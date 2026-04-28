FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY weatheros_backend.py .
COPY index-backend-proxy.html .

EXPOSE 8787

CMD ["python", "weatheros_backend.py"]
