FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the dataflow py file
COPY dataflow.py .

# Copy the train deploy
COPY train_deploy.py .

# Copy the credentials.json
COPY tensile-nebula-406509-8fd0cc70c363.json .

# Run the train_deploy script
CMD ["sh", "-c", "python dataflow.py && (python train_deploy.py || true)"]