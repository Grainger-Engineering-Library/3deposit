#!/bin/bash

docker network create proxy
docker-compose -f init.yml up --build -d
docker-compose -f docker-compose.yml up --build

