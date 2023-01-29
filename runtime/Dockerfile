FROM python:3.9.16-slim

WORKDIR /app

COPY requirements.txt .
COPY runtime.py .

RUN apt-get update -y && apt-get install -y gcc

RUN pip3 install -r requirements.txt

CMD ["python", "runtime.py"]