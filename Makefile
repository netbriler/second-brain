RUN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(RUN_ARGS):;@:)

BACKUPS_PATH := ./data/backups/postgres

run:
	docker-compose up -d --force-recreate

build:
	docker-compose build --no-cache

exec_userbot:
	docker-compose exec -it userbot /bin/bash

exec_backend:
	docker-compose exec -it backend /bin/bash

exec_nginx:
	docker-compose exec -it nginx /bin/sh

down:
	docker-compose down

psql:
	docker-compose exec postgres psql -U postgres postgres

pg_dump:
	mkdir -p ./data/backups/postgres && docker-compose exec -T postgres pg_dump -U postgres postgres --no-owner \
	| gzip -9 > ./data/backups/postgres/backup-$(shell date +%Y-%m-%d_%H-%M-%S).sql.gz

pg_restore:
	mkdir -p ./data/backups/postgres && bash ./bin/pg_restore.sh ${BACKUPS_PATH}

restart:
	docker-compose restart userbot && docker-compose restart backend

stop:
	docker-compose stop

migrate:
	python manage.py makemigrations && python manage.py migrate

run-dev:
	python manage.py runserver 0.0.0.0:8000
