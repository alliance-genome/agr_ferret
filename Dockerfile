FROM agrdocker/agr_base_linux_env:latest

WORKDIR /usr/src/

ADD requirements.txt .

RUN pip3 install -r requirements.txt

ADD . .

CMD ["python3", "-u", "src/app.py"]