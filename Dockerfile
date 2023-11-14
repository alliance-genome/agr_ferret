ARG DOCKER_PULL_TAG=latest
ARG REG=100225593120.dkr.ecr.us-east-1.amazonaws.com

FROM ${REG}/agr_base_linux_env:${DOCKER_PULL_TAG}

WORKDIR /usr/src/app

ADD requirements.txt .

RUN . /root/venv/bin/activate

RUN pip install -r requirements.txt

RUN mkdir tmp

RUN mkdir coverage_output

ADD . .

CMD ["python", "-u", "src/app.py"]
