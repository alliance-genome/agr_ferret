build: pull
	docker build -t agrdocker/agr_ferret_run:latest .

buildenv: build

pull:
	docker pull agrdocker/agr_base_linux_env:latest

run: build
	docker-compose up agr_ferret
