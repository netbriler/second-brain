from decimal import Decimal

import pytest
from altcoin.collection import CollectionWorkflow
from altcoin.constants import AccountRole, InputRole
from altcoin.models import (
    Account,
    Coin,
    CollectionConfig,
    Input,
    InputFilter,
    Network,
    Transaction,
)
from altcoin.seeds import ensure_networks_and_coins
from django.db import transaction

from workflows.constants import JOB_FAILED, JOB_SUCCESS
from workflows.manager import manager
from workflows.models import Job, Process


class TestCollectionWorkflow(CollectionWorkflow):
    @transaction.atomic
    def collect_currency(self, process: Process, job: Job):
        """
        Creates ether transaction
        """
        data = job.data

        self.job_log(job, f'Collecting currency | Data: {data}')
        self.done_job(job)


@pytest.fixture
def defaults():
    ensure_networks_and_coins()

    coin = Coin.objects.first()
    network = Network.objects.first()
    workflow_class = manager.get_workflow_class_str(TestCollectionWorkflow)

    transaction, _ = Transaction.objects.get_or_create(
        hash='sdfsdfsdf',
        network=network,
    )

    account1 = Account.objects.create(
        address='account1',
        role=AccountRole.DEPOSIT,
    )
    account2 = Account.objects.create(
        address='account2',
        role=AccountRole.DEPOSIT,
    )
    account3 = Account.objects.create(
        address='account3',
        role=AccountRole.HOT,
    )

    input1, _ = Input.objects.get_or_create(
        coin=coin,
        account=account1,
        transaction=transaction,
        amount=1,
        vout=0,
        role=InputRole.QUARANTINE,
    )
    input2, _ = Input.objects.get_or_create(
        coin=coin,
        account=account1,
        transaction=transaction,
        amount=0.1,
        vout=1,
        role=InputRole.DEPOSIT,
    )
    input3, _ = Input.objects.get_or_create(
        coin=coin,
        account=account1,
        transaction=transaction,
        amount=50,
        vout=2,
        role=InputRole.DEPOSIT,
    )

    # Account 2
    input4, _ = Input.objects.get_or_create(
        coin=coin,
        account=account2,
        transaction=transaction,
        amount=1,
        vout=3,
        role=InputRole.DEPOSIT,
    )
    input5, _ = Input.objects.get_or_create(
        coin=coin,
        account=account2,
        transaction=transaction,
        amount=0.1,
        vout=4,
        role=InputRole.DEPOSIT,
    )
    input6, _ = Input.objects.get_or_create(
        coin=coin,
        account=account2,
        transaction=transaction,
        amount=51,
        vout=5,
        role=InputRole.DEPOSIT,
    )

    # Account 3
    input7, _ = Input.objects.get_or_create(
        coin=coin,
        account=account3,
        transaction=transaction,
        amount=1,
        vout=6,
        role=InputRole.HOT,
    )
    input8, _ = Input.objects.get_or_create(
        coin=coin,
        account=account3,
        transaction=transaction,
        amount=50,
        vout=7,
        role=InputRole.DEPOSIT,
    )

    return {
        'network': network,
        'transaction': transaction,
        'coin': coin,
        'accounts': [account1, account2, account3],
        'inputs': [
            # Account 1
            input1,
            input2,
            input3,
            # Account 2
            input4,
            input5,
            input6,
            # Account 3 Hot
            input7,
            input8,
        ],
        'workflow_class': workflow_class,
    }


@pytest.mark.django_db
def test_simple_collection_config(defaults):
    network = defaults['network']
    workflow_class = defaults['workflow_class']

    destination_address = 'tb1qd7c02rl8kgyfujnw74lzg9uf9axy5tnqcmmjf6'

    config = CollectionConfig.objects.create(
        workflow_class=workflow_class,
        name='Config 1: DEPOSIT Accounts',
        description='Collect from DEPOSIT role accounts with input roles DEPOSIT and min_amount filter',
        enable=True,
        network=network,
        accounts_roles=[AccountRole.DEPOSIT],
        input_roles=[InputRole.DEPOSIT],
        min_amount=0.5,
        destination_address_string=destination_address,
    )

    process, job = manager.create_process(
        config,
        TestCollectionWorkflow,
    )

    manager.run(None, stop_on_jobs_end=True)

    job.refresh_from_db()

    collect_currency_job = process.jobs.filter(stage='collect_currency').first()
    collect_currency_job.data['inputs'].sort()

    assert job.status == JOB_SUCCESS

    result_inputs = [
        defaults['inputs'][1].id,
        defaults['inputs'][2].id,
        defaults['inputs'][3].id,
        defaults['inputs'][4].id,
        defaults['inputs'][5].id,
    ]
    result_inputs.sort()

    assert collect_currency_job.data['inputs'] == result_inputs

    collect_currency_job.data['outputs'] = {k: Decimal(v) for k, v in collect_currency_job.data['outputs'].items()}
    assert collect_currency_job.data['outputs'] == {
        destination_address: Decimal('102.2'),
    }, 'The output dictionaries do not match.'

    assert Decimal(collect_currency_job.data['total_amount']) == Decimal(
        '102.2',
    ), 'The total amount is not correct.'


@pytest.mark.django_db
def test_input_filters(defaults):
    network = defaults['network']
    workflow_class = defaults['workflow_class']

    destination_address = 'tb1qd7c02rl8kgyfujnw74lzg9uf9axy5tnqcmmjf6'

    config = CollectionConfig.objects.create(
        workflow_class=workflow_class,
        name='Config 1: DEPOSIT Accounts',
        description='Collect from DEPOSIT role accounts with input roles DEPOSIT and min_amount filter',
        enable=True,
        network=network,
        accounts_roles=[AccountRole.DEPOSIT],
        input_roles=[InputRole.DEPOSIT],
        min_amount=0.5,
        destination_address_string=destination_address,
    )
    InputFilter.objects.create(
        collection_config=config,
        account_role=AccountRole.DEPOSIT,
        min_amount=0.5,
        max_amount=50,
    )

    process, job = manager.create_process(
        config,
        TestCollectionWorkflow,
    )

    manager.run(None, stop_on_jobs_end=True)

    job.refresh_from_db()

    collect_currency_job = process.jobs.filter(stage='collect_currency').first()
    collect_currency_job.data['inputs'].sort()

    assert job.status == JOB_SUCCESS

    result_inputs = [
        defaults['inputs'][2].id,
        defaults['inputs'][3].id,
    ]
    result_inputs.sort()

    assert collect_currency_job.data['inputs'] == result_inputs

    collect_currency_job.data['outputs'] = {k: Decimal(v) for k, v in collect_currency_job.data['outputs'].items()}
    assert collect_currency_job.data['outputs'] == {
        destination_address: Decimal('51'),
    }, 'The output dictionaries do not match.'

    assert Decimal(collect_currency_job.data['total_amount']) == Decimal('51'), 'The total amount is not correct.'


@pytest.mark.django_db
def test_min_count_input_filter(defaults):
    network = defaults['network']
    workflow_class = defaults['workflow_class']
    destination_address = 'tb1qd7c02rl8kgyfujnw74lzg9uf9axy5tnqcmmjf6'

    config = CollectionConfig.objects.create(
        workflow_class=workflow_class,
        name='Config Min Count',
        description='Collect with a minimum count of inputs',
        enable=True,
        network=network,
        accounts_roles=[AccountRole.DEPOSIT],
        input_roles=[InputRole.DEPOSIT],
        min_amount=0.5,
        destination_address_string=destination_address,
    )
    InputFilter.objects.create(
        collection_config=config,
        account_role=AccountRole.DEPOSIT,
        min_amount=0.5,
        min_count=2,
    )

    process, job = manager.create_process(
        config,
        TestCollectionWorkflow,
    )

    manager.run(None, stop_on_jobs_end=True)

    process.refresh_from_db()
    job.refresh_from_db()

    collect_currency_job = process.jobs.filter(stage='collect_currency').first()
    collect_currency_job.data['inputs'].sort()

    assert job.status == JOB_SUCCESS

    result_inputs = [
        defaults['inputs'][2].id,
        defaults['inputs'][3].id,
        defaults['inputs'][5].id,
    ]
    result_inputs.sort()

    assert collect_currency_job.data['inputs'] == result_inputs

    collect_currency_job.data['outputs'] = {k: Decimal(v) for k, v in collect_currency_job.data['outputs'].items()}
    assert collect_currency_job.data['outputs'] == {
        destination_address: Decimal('102'),
    }, 'The output dictionaries do not match.'

    assert Decimal(collect_currency_job.data['total_amount']) == Decimal(
        '102',
    ), 'The total amount is not correct.'


@pytest.mark.django_db
def test_min_count_input_filter_fail(defaults):
    network = defaults['network']
    workflow_class = defaults['workflow_class']
    destination_address = 'tb1qd7c02rl8kgyfujnw74lzg9uf9axy5tnqcmmjf6'

    config = CollectionConfig.objects.create(
        workflow_class=workflow_class,
        name='Config Min Count',
        description='Collect with a minimum count of inputs',
        enable=True,
        network=network,
        accounts_roles=[AccountRole.DEPOSIT],
        input_roles=[InputRole.DEPOSIT],
        min_amount=0.5,
        destination_address_string=destination_address,
    )
    InputFilter.objects.create(
        collection_config=config,
        account_role=AccountRole.DEPOSIT,
        min_amount=0.5,
        min_count=20,
    )

    process, job = manager.create_process(
        config,
        TestCollectionWorkflow,
    )

    manager.run(None, stop_on_jobs_end=True)

    process.refresh_from_db()
    job.refresh_from_db()

    assert job.status == JOB_FAILED

    for log in process.logs.all():
        if 'Not enough inputs for role deposit' in log.message:
            return

    raise Exception('Process has not failed')


@pytest.mark.django_db
def test_max_count_input_filter(defaults):
    network = defaults['network']
    workflow_class = defaults['workflow_class']
    destination_address = 'tb1qd7c02rl8kgyfujnw74lzg9uf9axy5tnqcmmjf6'

    config = CollectionConfig.objects.create(
        workflow_class=workflow_class,
        name='Config Min Count',
        description='Collect with a maximum count of inputs',
        enable=True,
        network=network,
        accounts_roles=[AccountRole.DEPOSIT],
        input_roles=[InputRole.DEPOSIT],
        min_amount=0.5,
        destination_address_string=destination_address,
    )
    InputFilter.objects.create(
        collection_config=config,
        account_role=AccountRole.DEPOSIT,
        min_amount=0.5,
        max_count=40,
    )

    process, job = manager.create_process(
        config,
        TestCollectionWorkflow,
    )

    manager.run(None, stop_on_jobs_end=True)

    process.refresh_from_db()
    job.refresh_from_db()

    collect_currency_job = process.jobs.filter(stage='collect_currency').first()
    collect_currency_job.data['inputs'].sort()

    assert job.status == JOB_SUCCESS

    result_inputs = [
        defaults['inputs'][2].id,
        defaults['inputs'][3].id,
        defaults['inputs'][5].id,
    ]
    result_inputs.sort()

    assert collect_currency_job.data['inputs'] == result_inputs

    collect_currency_job.data['outputs'] = {k: Decimal(v) for k, v in collect_currency_job.data['outputs'].items()}
    assert collect_currency_job.data['outputs'] == {
        destination_address: Decimal('102'),
    }, 'The output dictionaries do not match.'

    assert Decimal(collect_currency_job.data['total_amount']) == Decimal(
        '102',
    ), 'The total amount is not correct.'


@pytest.mark.django_db
def test_max_count_input_filter_fail(defaults):
    network = defaults['network']
    workflow_class = defaults['workflow_class']
    destination_address = 'tb1qd7c02rl8kgyfujnw74lzg9uf9axy5tnqcmmjf6'

    config = CollectionConfig.objects.create(
        workflow_class=workflow_class,
        name='Config Min Count',
        description='Collect with a maximum count of inputs',
        enable=True,
        network=network,
        accounts_roles=[AccountRole.DEPOSIT, AccountRole.HOT],
        input_roles=[InputRole.DEPOSIT, InputRole.HOT],
        min_amount=0.5,
        destination_address_string=destination_address,
    )
    InputFilter.objects.create(
        collection_config=config,
        account_role=AccountRole.DEPOSIT,
        min_amount=0.5,
        max_count=1,
    )
    InputFilter.objects.create(
        collection_config=config,
        account_role=AccountRole.HOT,
        min_amount=0.5,
        max_count=2,
    )
    InputFilter.objects.create(
        collection_config=config,
        account_role='__all__',
        max_count=2,
    )

    process, job = manager.create_process(
        config,
        TestCollectionWorkflow,
    )

    manager.run(None, stop_on_jobs_end=True)

    process.refresh_from_db()
    job.refresh_from_db()

    collect_currency_job = process.jobs.filter(stage='collect_currency').first()
    collect_currency_job.data['inputs'].sort()

    assert job.status == JOB_SUCCESS

    result_inputs = [
        defaults['inputs'][2].id,
        defaults['inputs'][6].id,
    ]
    result_inputs.sort()

    assert collect_currency_job.data['inputs'] == result_inputs

    collect_currency_job.data['outputs'] = {k: Decimal(v) for k, v in collect_currency_job.data['outputs'].items()}
    assert collect_currency_job.data['outputs'] == {
        destination_address: Decimal('51'),
    }, 'The output dictionaries do not match.'

    assert Decimal(collect_currency_job.data['total_amount']) == Decimal(
        '51',
    ), 'The total amount is not correct.'


@pytest.mark.django_db
def test_min_amount(defaults):
    network = defaults['network']
    workflow_class = defaults['workflow_class']
    destination_address = 'tb1qd7c02rl8kgyfujnw74lzg9uf9axy5tnqcmmjf6'

    config = CollectionConfig.objects.create(
        workflow_class=workflow_class,
        name='Config Min Amount',
        description='Collect with a minimum amount of inputs',
        enable=True,
        network=network,
        accounts_roles=[AccountRole.DEPOSIT],
        input_roles=[InputRole.DEPOSIT],
        min_amount=10,
        destination_address_string=destination_address,
    )

    process, job = manager.create_process(
        config,
        TestCollectionWorkflow,
    )

    manager.run(None, stop_on_jobs_end=True)

    process.refresh_from_db()
    job.refresh_from_db()

    assert job.status == JOB_SUCCESS

    collect_currency_job = process.jobs.filter(stage='collect_currency').first()
    collect_currency_job.data['inputs'].sort()

    result_inputs = [
        defaults['inputs'][1].id,
        defaults['inputs'][2].id,
        defaults['inputs'][3].id,
        defaults['inputs'][4].id,
        defaults['inputs'][5].id,
    ]
    result_inputs.sort()

    assert collect_currency_job.data['inputs'] == result_inputs

    collect_currency_job.data['outputs'] = {k: Decimal(v) for k, v in collect_currency_job.data['outputs'].items()}
    assert collect_currency_job.data['outputs'] == {
        destination_address: Decimal('102.2'),
    }, 'The output dictionaries do not match.'

    assert Decimal(collect_currency_job.data['total_amount']) == Decimal(
        '102.2',
    ), 'The total amount is not correct.'


@pytest.mark.django_db
def test_min_amount_fail(defaults):
    network = defaults['network']
    workflow_class = defaults['workflow_class']
    destination_address = 'tb1qd7c02rl8kgyfujnw74lzg9uf9axy5tnqcmmjf6'

    config = CollectionConfig.objects.create(
        workflow_class=workflow_class,
        name='Config Min Amount',
        description='Collect with a minimum amount of inputs',
        enable=True,
        network=network,
        accounts_roles=[AccountRole.DEPOSIT],
        input_roles=[InputRole.DEPOSIT],
        min_amount=9999,
        destination_address_string=destination_address,
    )

    process, job = manager.create_process(
        config,
        TestCollectionWorkflow,
    )

    manager.run(None, stop_on_jobs_end=True)

    process.refresh_from_db()
    job.refresh_from_db()

    assert job.status == JOB_FAILED

    for log in process.logs.all():
        if 'Total amount is too low' in log.message:
            return

    raise Exception('Process has not failed')


@pytest.mark.django_db
def test_max_amount(defaults):
    network = defaults['network']
    workflow_class = defaults['workflow_class']
    destination_address = 'tb1qd7c02rl8kgyfujnw74lzg9uf9axy5tnqcmmjf6'

    config = CollectionConfig.objects.create(
        workflow_class=workflow_class,
        name='Config Max Amount',
        description='Collect with a maximum amount of inputs',
        enable=True,
        network=network,
        accounts_roles=[AccountRole.DEPOSIT],
        input_roles=[InputRole.DEPOSIT],
        max_amount=10,
        destination_address_string=destination_address,
    )

    process, job = manager.create_process(
        config,
        TestCollectionWorkflow,
    )

    manager.run(None, stop_on_jobs_end=True)

    process.refresh_from_db()
    job.refresh_from_db()

    assert job.status == JOB_SUCCESS

    collect_currency_job = process.jobs.filter(stage='collect_currency').first()
    collect_currency_job.data['inputs'].sort()

    result_inputs = [
        defaults['inputs'][1].id,
        defaults['inputs'][2].id,
    ]
    result_inputs.sort()

    assert collect_currency_job.data['inputs'] == result_inputs

    collect_currency_job.data['outputs'] = {k: Decimal(v) for k, v in collect_currency_job.data['outputs'].items()}
    assert collect_currency_job.data['outputs'] == {
        destination_address: Decimal('10'),
        defaults['accounts'][0].address: Decimal('40.1'),
    }, 'The output dictionaries do not match.'

    assert Decimal(collect_currency_job.data['total_amount']) == Decimal('50.1'), 'The total amount is not correct.'


@pytest.mark.django_db
def test_tail_amount_with_max_amount(defaults):
    network = defaults['network']
    workflow_class = defaults['workflow_class']
    destination_address = 'tb1qd7c02rl8kgyfujnw74lzg9uf9axy5tnqcmmjf6'

    config = CollectionConfig.objects.create(
        workflow_class=workflow_class,
        name='Config Max Amount',
        description='Collect with a maximum amount of inputs',
        enable=True,
        network=network,
        accounts_roles=[AccountRole.DEPOSIT],
        input_roles=[InputRole.DEPOSIT],
        max_amount=64,
        tail_amount=Decimal('0.1'),
        destination_address_string=destination_address,
    )

    process, job = manager.create_process(
        config,
        TestCollectionWorkflow,
    )

    manager.run(None, stop_on_jobs_end=True)

    process.refresh_from_db()
    job.refresh_from_db()

    assert job.status == JOB_SUCCESS

    collect_currency_job = process.jobs.filter(stage='collect_currency').first()
    collect_currency_job.data['inputs'].sort()

    result_inputs = [
        defaults['inputs'][1].id,
        defaults['inputs'][2].id,
        defaults['inputs'][3].id,
        defaults['inputs'][4].id,
        defaults['inputs'][5].id,
    ]
    result_inputs.sort()

    assert collect_currency_job.data['inputs'] == result_inputs

    collect_currency_job.data['outputs'] = {k: Decimal(v) for k, v in collect_currency_job.data['outputs'].items()}
    assert collect_currency_job.data['outputs'] == {
        destination_address: Decimal('64'),
        defaults['accounts'][0].address: Decimal('38.1'),  # return with change because of max amount
        defaults['accounts'][1].address: Decimal('0.1'),  # return with change because of tail amount
    }, 'The output dictionaries do not match.'

    assert Decimal(collect_currency_job.data['total_amount']) == Decimal('102.2'), 'The total amount is not correct.'


@pytest.mark.django_db
def test_tail_amount(defaults):
    network = defaults['network']
    workflow_class = defaults['workflow_class']
    destination_address = 'tb1qd7c02rl8kgyfujnw74lzg9uf9axy5tnqcmmjf6'

    config = CollectionConfig.objects.create(
        workflow_class=workflow_class,
        name='Config Max Amount',
        description='Collect with a maximum amount of inputs',
        enable=True,
        network=network,
        accounts_roles=[AccountRole.DEPOSIT, AccountRole.HOT],
        input_roles=[InputRole.DEPOSIT, InputRole.HOT, InputRole.QUARANTINE],
        tail_amount=Decimal('51.1'),
        destination_address_string=destination_address,
    )

    process, job = manager.create_process(
        config,
        TestCollectionWorkflow,
    )

    manager.run(None, stop_on_jobs_end=True)

    process.refresh_from_db()
    job.refresh_from_db()

    assert job.status == JOB_SUCCESS

    collect_currency_job = process.jobs.filter(stage='collect_currency').first()
    collect_currency_job.data['inputs'].sort()

    result_inputs = [
        defaults['inputs'][0].id,
        defaults['inputs'][1].id,
        defaults['inputs'][2].id,
        defaults['inputs'][3].id,
        defaults['inputs'][4].id,
        defaults['inputs'][5].id,
        defaults['inputs'][6].id,
        defaults['inputs'][7].id,
    ]
    result_inputs.sort()

    assert collect_currency_job.data['inputs'] == result_inputs

    collect_currency_job.data['outputs'] = {k: Decimal(v) for k, v in collect_currency_job.data['outputs'].items()}
    assert collect_currency_job.data['outputs'] == {
        destination_address: Decimal('52'),
        defaults['accounts'][0].address: Decimal('51.1'),  # return with change because of tail amount
        defaults['accounts'][1].address: Decimal('51.1'),  # return with change because of tail amount
        # accounts[2] should not be included because it has less coins than tail amount
    }, 'The output dictionaries do not match.'

    assert Decimal(collect_currency_job.data['total_amount']) == Decimal('154.2'), 'The total amount is not correct.'
