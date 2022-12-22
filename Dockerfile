FROM python:3.9-slim

RUN pip install --upgrade pip

# Install libraries
COPY ./requirements.txt ./

RUN pip install -r requirements.txt && \
    rm ./requirements.txt

# Setup container directories
RUN mkdir /app

# Copy local code to the container
COPY . /app

# launch server with gunicorn
WORKDIR /app

EXPOSE 8080

CMD gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind=0.0.0.0:8080 --threads 4 --timeout 0 
