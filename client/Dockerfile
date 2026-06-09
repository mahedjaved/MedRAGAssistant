FROM python:3.13-slim
RUN apt-get update && apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY client /.
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
# running streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]