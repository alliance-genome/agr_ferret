REG := 100225593120.dkr.ecr.us-east-1.amazonaws.com
DOCKER_PULL_TAG=latest
DOCKER_BUILD_TAG=latest
AWS_DEFAULT_REGION := us-east-1


registry-docker-login:
ifneq ($(shell echo ${REG} | egrep "ecr\..+\.amazonaws\.com"),)
	@$(eval DOCKER_LOGIN_CMD=docker run --rm -it -v ~/.aws:/root/.aws amazon/aws-cli)
ifneq (${AWS_PROFILE},)
	@$(eval DOCKER_LOGIN_CMD=${DOCKER_LOGIN_CMD} --profile ${AWS_PROFILE})
endif
	@$(eval DOCKER_LOGIN_CMD=${DOCKER_LOGIN_CMD} ecr get-login-password --region=${AWS_DEFAULT_REGION} | docker login -u AWS --password-stdin https://${REG})
	${DOCKER_LOGIN_CMD}
endif

password:
	install -m 600 /dev/null .password
	./password-client.sh > .password

build: registry-docker-login password pull
	docker build -t ${REG}/agr_ferret_run:${DOCKER_BUILD_TAG} --build-arg DOCKER_PULL_TAG=${DOCKER_PULL_TAG} .

buildenv: registry-docker-login password build

pull:
	docker pull ${REG}/agr_base_linux_env:${DOCKER_PULL_TAG}

run: build
	REG=${REG} docker-compose up agr_ferret
