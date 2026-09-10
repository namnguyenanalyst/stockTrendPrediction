FROM python:3.10-slim

WORKDIR /app

# Cài đặt uv để quản lý dependencies nhanh chóng
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy cấu hình pyproject.toml
COPY pyproject.toml .

# Cài đặt dependencies bằng uv
RUN uv pip install --system -r <(uv pip compile pyproject.toml) || uv pip install --system fastapi uvicorn pydantic pydantic-settings

# Copy mã nguồn API
COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
