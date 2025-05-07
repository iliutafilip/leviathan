.PHONY: build up up-detached down restart logs rebuild
CONFIG_FILE ?= ./configs/config.yaml
start:
	docker compose build
	CONFIG_PATH=$(CONFIG_FILE) docker-compose up --build
logs:
	docker-compose logs -f
stop:
	docker-compose down
tests:
	python3 -m unittest discover -s tests
