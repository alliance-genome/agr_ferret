REG := 100225593120.dkr.ecr.us-east-1.amazonaws.com
DOCKER_IMAGE_TAG := latest

registry-docker-login:
ifneq ($(shell echo ${REG} | egrep "ecr\..+\.amazonaws\.com"),)
	@$(eval DOCKER_LOGIN_CMD=aws)
ifneq (${AWS_PROFILE},)
	@$(eval DOCKER_LOGIN_CMD=${DOCKER_LOGIN_CMD} --profile ${AWS_PROFILE})
endif
	@$(eval DOCKER_LOGIN_CMD=${DOCKER_LOGIN_CMD} ecr get-login-password | docker login -u AWS --password-stdin https://${REG})
	${DOCKER_LOGIN_CMD}
endif

build: pull
	docker build -t ${REG}/agr_ferret_run:${DOCKER_IMAGE_TAG} --build-arg DOCKER_IMAGE_TAG=${DOCKER_IMAGE_TAG} .

buildenv: build

pull:
	docker pull ${REG}/agr_base_linux_env:${DOCKER_IMAGE_TAG}

run: build
	REG=${REG} docker-compose up agr_ferret
