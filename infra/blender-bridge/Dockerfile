FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn Pillow

COPY bridge.py .

ENV BLENDER_HOST=host.docker.internal
ENV BLENDER_PORT=9876
ENV SOCKET_TIMEOUT=120

EXPOSE 9877

CMD ["uvicorn", "bridge:app", "--host", "0.0.0.0", "--port", "9877"]
