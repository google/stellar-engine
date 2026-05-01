# Use a hardened base image (e.g., Iron Bank or Google Distroless)
FROM python:3.11-slim 

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port 8080 for Cloud Run
EXPOSE 8080

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]