FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

WORKDIR /app/test1

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8088", "app:app", "--access-logfile", "/dev/null"]