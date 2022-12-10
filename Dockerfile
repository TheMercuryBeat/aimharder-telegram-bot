FROM python:3.10-slim

RUN apt-get update  \
    && apt-get install -y build-essential libpq-dev  \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /code
WORKDIR /code

COPY requirements.txt .
RUN python3.10 -m pip install --no-cache-dir --upgrade pip setuptools wheel
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt
COPY main.py .
COPY src src

EXPOSE 5000

CMD ["python3.10", "main.py"]