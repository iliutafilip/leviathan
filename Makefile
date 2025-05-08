.PHONY: build up up-detached down restart logs rebuild start start-detached stop tests

CONFIG_FILE ?= ./configs/config.yaml

start:
	docker-compose build
	CONFIG_PATH=$(CONFIG_FILE) docker-compose up --build

start-detached:
	docker-compose build
	CONFIG_PATH=$(CONFIG_FILE) docker-compose up -d --build

logs:
	docker-compose logs -f

stop:
	docker-compose down

tests:
	python3 -m unittest discover -s tests
