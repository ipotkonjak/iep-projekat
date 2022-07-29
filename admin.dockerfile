FROM python:3

RUN mkdir -p /opt/src/store
WORKDIR /opt/src/store

COPY ./store/administrator/application.py ./application.py
COPY ./store/configuration.py ./configuration.py
COPY ./store/models.py ./models.py
COPY ./store/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

ENTRYPOINT ["python", "./application.py"]