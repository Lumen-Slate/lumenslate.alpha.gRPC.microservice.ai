# Makefile for ai-microservice

.PHONY: build up down logs restart

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose down
	docker-compose up -d
 
proto:
	python3 -m grpc_tools.protoc -I ./app/protos --python_out=./app/protos --grpc_python_out=./app/protos ./app/protos/ai_service.proto
