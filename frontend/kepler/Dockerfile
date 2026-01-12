
FROM python:3.11-slim

WORKDIR /app

RUN pip install --upgrade pip 

COPY pyproject.toml .

COPY src/ src/

RUN pip install -e .

COPY frontend/ frontend/

CMD ["uvicorn", "frontend.kepler.server:app", "--host", "0.0.0.0", "--port", "8501"]
