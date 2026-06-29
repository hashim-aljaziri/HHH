FROM node:24-bookworm AS frontend

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY static ./static
COPY templates ./templates
COPY postcss.config.js tailwind.config.js webpack.config.js .babelrc ./
RUN npm run build

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend /app/static/dist ./static/dist

EXPOSE 8000

CMD ["gunicorn", "wsgi:app", "--bind", "0.0.0.0:8000", "--workers", "3"]
