FROM node:22-alpine AS frontend
WORKDIR /web
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
RUN npm run build

FROM python:3.12-slim AS python-builder
WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
RUN python -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir .

FROM python:3.12-slim AS api
COPY --from=python-builder /opt/venv /opt/venv
COPY --from=frontend /web/dist /app/static
ENV PATH="/opt/venv/bin:$PATH" LABELLINT_STATIC_DIR=/app/static
WORKDIR /app
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["uvicorn", "labellint.api:app", "--host", "0.0.0.0", "--port", "8000"]

FROM nginx:1.27-alpine AS dashboard
COPY --from=frontend /web/dist /usr/share/nginx/html
COPY dashboard/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
