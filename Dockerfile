FROM python:3.11-slim

# Postavi radni direktorij
WORKDIR /app

# Kopiraj dependency file i instaliraj
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Kopiraj ostatak projekta
COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
