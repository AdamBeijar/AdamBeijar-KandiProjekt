FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app", "--access-logfile", "/dev/null"]