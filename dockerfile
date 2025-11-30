# Use the official Python 3.13 image (slim — for minimal size)
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Set environment variables
# PYTHONUNBUFFERED=1: prevents Python from buffering stdout/stderr
# PYTHONDONTWRITEBYTECODE=1: prevents Python from writing .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy the dependencies file
COPY requirements.txt .

# Install dependencies
# --no-cache-dir: saves space by not caching packages
# --upgrade pip: ensures we have the latest pip version
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the bot files into the container
COPY bot.py .

# Create a volume for data storage (if files need to be persisted, e.g., lessons.json)
VOLUME ["/app/data"]

# Command to run the application when the container starts
CMD ["python", "bot.py"]