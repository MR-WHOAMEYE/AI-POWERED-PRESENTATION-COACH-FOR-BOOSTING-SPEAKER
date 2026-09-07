# ==========================================
# Stage 1: Build React Frontend
# ==========================================
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Serve Frontend with Nginx
# ==========================================
FROM nginx:alpine AS frontend
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

# ==========================================
# Stage 3: Python Backend Base
# ==========================================
FROM python:3.12-slim AS backend-base

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY backend/ ./backend
WORKDIR /app/backend

# ==========================================
# Stage 4: Backend Development Target
# ==========================================
FROM backend-base AS backend-dev
ENV FLASK_ENV=development
EXPOSE 5000
CMD ["python", "app.py"]

# ==========================================
# Stage 5: Backend Production Target
# ==========================================
FROM backend-base AS backend-prod
ENV FLASK_ENV=production
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "wsgi.py"]
