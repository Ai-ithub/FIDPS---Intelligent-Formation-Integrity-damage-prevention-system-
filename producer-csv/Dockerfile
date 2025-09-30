FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install kafka-python pandas pyarrow numpy
CMD ["python", "real-tim.py"]

