FROM alirezasharifi/lighthouse-python:latest

RUN pip install pip --upgrade

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

CMD celery -A main.celery_app worker --loglevel=info -c ${WORKER_COUNT} & uvicorn main:app --host 0.0.0.0 --port 8080

