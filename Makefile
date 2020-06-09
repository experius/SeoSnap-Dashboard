#!make
.EXPORT_ALL_VARIABLES:
-include .env

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help: ## Shows list of commands
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

up:  ## Starts up all the services
	docker-compose up --build

up_dev: ## Starts up all the services in dev mode
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

serve: migrate create_admin ## Starts django server
	echo 'Serving the backend'
	python manage.py runserver 0.0.0.0:80

install: ## Sets up environment for local installation
	echo 'Running installation'
	cp .env.example .env
	sh dev/commands/install.sh

migrate:  ## Runs migration
	echo 'Migrating the backend'
	python manage.py makemigrations
	python manage.py migrate auth
	python manage.py migrate

create_admin: ## Creates admin user
	echo ${ADMIN_NAME}
	bash dev/commands/create_admin.sh

db: ## Starts up the datavase
	docker-compose up db

down: ## Stops all the services
	docker-compose down