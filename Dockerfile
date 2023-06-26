# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV . /app
WORKDIR /app
COPY . /app

# Install production dependencies.
RUN cd /app
RUN python -m venv env
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD . env/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8080 --reload