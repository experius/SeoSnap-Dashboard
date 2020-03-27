#!make
.EXPORT_ALL_VARIABLES:
-include .env

up:
	docker-compose up --build

up_dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

serve: migrate create_admin
	echo 'Serving the backend'
	python manage.py runserver 0.0.0.0:80

install:
	echo 'Running installation'
	cp .env.example .env
	sh dev/commands/install.sh

migrate: 
	echo 'Migrating the backend'
	python manage.py makemigrations
	python manage.py migrate auth
	python manage.py migrate

create_admin:
	echo ${ADMIN_NAME}
	bash dev/commands/create_admin.sh

