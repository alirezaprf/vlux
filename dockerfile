# Use an official Python runtime as a base image
FROM python:3.10-slim

# Install git
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean

# Clone the repository
RUN git clone https://github.com/alirezaprf/vlux /app

# Set the working directory to the cloned repository
WORKDIR /app

# Install the required Python packages
RUN pip install -r requirements.txt

# Run slave.py
CMD ["python", "slave.py"]
