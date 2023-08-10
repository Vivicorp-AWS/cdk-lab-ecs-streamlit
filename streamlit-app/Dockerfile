FROM --platform=linux/arm64 python:3.10.12-slim-bookworm

EXPOSE 8501

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN ["python", "-m", "pip", "install", "-r", "requirements.txt"]

COPY . .

ENTRYPOINT ["streamlit"]

CMD ["run", "Home.py", \
     "--server.headless", "true", \
     "--browser.serverAddress=0.0.0.0", \
     "--server.enableCORS", "false", \
     "--browser.gatherUsageStats", "false"]