# Use your base image
FROM mcr.microsoft.com/devcontainers/python:3.12-bullseye

# Install git if it isn’t already available
RUN apt-get update && apt-get install -y git

# Clone the TruffleHog repository into a directory in your container
RUN git clone https://github.com/trufflesecurity/trufflehog.git /opt/trufflehog

# Install TruffleHog in editable mode using pip
RUN pip install --upgrade pip \
    && pip install -e /opt/trufflehog

# (Optional) Any other setup steps for your environment
