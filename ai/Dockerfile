# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# torch는 크고 잘 안 바뀌어서 먼저 설치한다. (CPU 버전)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu "torch>=2.6,<3"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 학습된 모델, 회사 표, 서버 코드만 넣는다.
COPY models ./models
COPY src ./src

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
