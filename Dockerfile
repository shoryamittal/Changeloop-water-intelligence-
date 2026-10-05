FROM python:3.12-slim
WORKDIR /app
COPY . .
EXPOSE 8000
# Standard library only - there is nothing to install.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["python", "backend/server.py"]
