.PHONY: build up up-detached down restart logs rebuild
CONFIG_FILE ?= ./configs/config.yaml
build:
	docker compose build
up:
	CONFIG_PATH=$(CONFIG_FILE) docker-compose up --build
up-detached:
	CONFIG_PATH=$(CONFIG_FILE) docker-compose up --build -d
logs:
	docker-compose logs -f
restart:
	docker-compose restart
down:
	docker-compose down
