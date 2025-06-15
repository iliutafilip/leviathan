#!/bin/bash

set -e

CONFIG_PATH="${1:-./configs/config.yaml}"

if ! command -v docker &> /dev/null; then
    echo "Docker not installed."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose not installed."
    exit 1
fi

docker run --rm --entrypoint htpasswd httpd:alpine -Bbn leviathan leviathan > htpasswd

export CONFIG_PATH

docker-compose up -d --build

sleep 2
if ! docker ps --filter "name=leviathan" --filter "status=running" | grep -q leviathan; then
    echo "Leviathan container exited (invalid config?)."
    docker logs leviathan
    exit 1
fi


echo "Waiting for Kibana..."
until curl -s http://localhost:5601/api/status | grep -q '"level":"available"'; do
    printf "."
    sleep 5
done
echo -e "Kibana online!"

if [[ -f dashboard.ndjson ]]; then
    echo "Importing dashboard.ndjson in Kibana..."
    curl -X POST "http://leviathan:leviathan@localhost:8080/api/saved_objects/_import?overwrite=true" \
        -H "kbn-xsrf: true" \
        --form file=@dashboard.ndjson
    echo "Dashboard successfully imported"
else
    echo "No dashboard.ndjson found. Skipping import..."
fi

echo "Kibana is ready!"
echo "Access Kibana: http://localhost:8080"
echo "User: leviathan"
echo "Password: leviathan"
echo "Streaming Leviathan logs. Pres Ctrl-C to exit."

docker-compose logs -f leviathan
