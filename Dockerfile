# ChangeLoop - container image.
#
# Standard library only, so there is no dependency layer and nothing to
# cache. The image is essentially the Python base plus this repository.
FROM python:3.12.4-slim

# PYTHONUNBUFFERED: platform log collectors read stdout, and a
#   block-buffered pipe holds output until the process exits - which is
#   exactly when nobody needs it.
# PORT/HOST: defaults only. Both are read at runtime, so a platform that
#   injects its own PORT is honoured without rebuilding the image.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Copied and installed separately from the rest of the tree so the build
# fails loudly if the file is ever lost, and so the zero-dependency claim
# is exercised rather than asserted. pip accepts a comment-only
# requirements file and installs nothing.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user. The service writes only its ledger; it should
# not be able to write anything else.
RUN useradd --create-home --uid 10001 changeloop \
    && mkdir -p /app/data \
    && chown -R changeloop:changeloop /app
USER changeloop

# Informational only - the platform decides the published port.
EXPOSE 8000

# The health check must use the port the server was actually told to use.
# Hardcoding 8000 means that the moment a platform injects its own PORT the
# container is marked unhealthy while serving perfectly - a failure that
# reads as "the app is broken" and is entirely the health check's fault.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os,sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/api/health', timeout=4).status==200 else 1)"

CMD ["python", "backend/server.py"]
