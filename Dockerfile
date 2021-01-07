ARG ALLIANCE_RELEASE=latest
ARG REG=100225593120.dkr.ecr.us-east-1.amazonaws.com
FROM ${REG}/agr_base_linux_env:${ALLIANCE_RELEASE}

WORKDIR /usr/src/app

ADD requirements.txt .

RUN pip3 install -r requirements.txt

RUN mkdir tmp

RUN mkdir coverage_output

ADD . .

CMD ["python3", "-u", "src/app.py"]
