# Use an official Python runtime as a base image
FROM python:3.10-slim

# Install git
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean

# Set the working directory to the cloned repository
WORKDIR /app

# Copy docker entrypoint
COPY docker-entrypoint.sh .

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]

# Run slave.py
CMD ["python", "slave.py"]
