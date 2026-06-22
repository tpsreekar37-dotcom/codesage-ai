# Deployment Guide

This guide covers deploying CodeSage AI to a production environment.

## Docker Swarm / Kubernetes
The project is containerized. For a scalable deployment, you can deploy the `docker-compose.yml` to a Docker Swarm or use tools like Kompose to migrate it to Kubernetes.

### Production Environment Variables
Ensure the following variables are securely injected into the environment (e.g., using Kubernetes Secrets or Docker Secrets):

- `POSTGRES_PASSWORD`: Must be a strong generated string.
- `SECRET_KEY`: Use a randomly generated 256-bit key for JWT signing.
- `GEMINI_API_KEY`: The production API key for Google Gemini.

### Scaling the Background Workers
To handle a large influx of repository uploads and code analysis requests, scale the FastAPI background worker instances independently of the main API server.

## Reverse Proxy & TLS
Place the application behind a reverse proxy such as Nginx or Traefik, and ensure you terminate TLS/SSL. The `frontend/nginx.conf` is provided as a starting point for the React application.
