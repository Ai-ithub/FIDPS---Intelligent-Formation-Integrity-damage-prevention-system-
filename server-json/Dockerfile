FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install kafka-python requests zeep
CMD ["python", "json-witsml.py"]



#docker build -t witsml-connector .
#docker run -it witsml-connector

#docker exec mehr3-kafka-1 kafka-topics.sh --list --bootstrap-server KAFKA:29092



#FROM python:3.10-slim
#WORKDIR /app
#COPY . .
#RUN pip install kafka-python requests
#CMD ["python", "producer.py"]
