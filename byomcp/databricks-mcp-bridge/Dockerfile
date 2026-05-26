FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --index-url https://pypi.org/simple

COPY . .

EXPOSE 8080

CMD ["uvicorn", "bridge:app", "--host", "0.0.0.0", "--port", "8080"]
