PROCESS_ACTIVE = 'active'
PROCESS_DONE = 'done'
PROCESS_FAILED = 'failed'

PROCESS_STATUSES = (
    (PROCESS_ACTIVE, 'Active'),
    (PROCESS_DONE, 'Done'),
    (PROCESS_FAILED, 'Failed'),
)

JOB_PLANNED = 'planed'
JOB_ACTIVE = 'active'
JOB_SUCCESS = 'success'
JOB_FAILED = 'failed'
JOB_CANCELED = 'canceled'

JOB_STATUSES = (
    (JOB_PLANNED, 'Planned'),
    (JOB_ACTIVE, 'Active'),
    (JOB_SUCCESS, 'Done'),
    (JOB_FAILED, 'Failed'),
    (JOB_CANCELED, 'Canceled'),
)

WORKFLOW_CLASSES = (('altcoin.collection.CollectionWorkflow', 'altcoin.collection.CollectionWorkflow'),)
