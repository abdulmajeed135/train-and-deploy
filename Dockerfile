FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY train_deploy.py .

# Run the train_deploy script
CMD ["python", "train_deploy.py"]
