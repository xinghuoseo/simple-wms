# ---------- 前端构建 ----------
FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ---------- 后端运行 ----------
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY main.py seed_admin.py ./
COPY --from=frontend /app/dist ./frontend/dist

EXPOSE 39800
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "39800"]
