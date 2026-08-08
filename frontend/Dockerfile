# Frontend Dockerfile
# Uses Python slim image to serve static files
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy frontend files
COPY . .

# Expose port
EXPOSE 3000

# Run the frontend server
CMD ["python", "serve.py"]
