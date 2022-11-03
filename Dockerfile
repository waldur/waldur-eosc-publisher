FROM python:3.9.6-buster

RUN apt-get update -y && \
    pip install pipenv --no-cache-dir

COPY . /src

WORKDIR /src

RUN pip install -r requirements/requirements.txt --no-cache-dir

ENTRYPOINT [ "python3" ]

CMD [ "-m", "eosc_publisher.app" ]
