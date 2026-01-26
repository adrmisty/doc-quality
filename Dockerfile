FROM python:3.10.19-slim-buster

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    g++ \
    ffmpeg \
    libsm6 \
    libxext6 \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install torch --extra-index-url https://download.pytorch.org/whl/cpu

COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./doc_quality ./doc_quality

ENV PYTHONPATH=/

EXPOSE 30600

CMD ["uvicorn", "doc_quality.app.fastapi_app:app", "--host", "0.0.0.0", "--port", "30600"]