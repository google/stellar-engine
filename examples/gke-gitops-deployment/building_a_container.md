## A Simple Guide To Build An Example Containerized App

This walks through the steps to create a containerized app and save in Artifact Registry

1. Create requirements.txt
```
fastapi==0.111.0
uvicorn==0.30.1
```

1. Create main.py
```
from fastapi import FastAPI
import os

app = FastAPI()
POD_NAME = os.getenv("POD_NAME")


@app.get("/")
async def read_root():
    return {"message": "Hello there, from {POD_NAME}!"}
```

1. Create Dockerfile
```
FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

1. Create docker-push.sh
```
PROJECT_ID="[Your Target Project]"
REGION="[YOUR REGION]"
REPO_NAME="applications"
IMAGE_NAME="[APP NAME ex: flash-app]"
IMAGE_TAG="latest"

# Full path for the image in Artifact Registry
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"
docker build -t ${IMAGE_URI} .
docker push ${IMAGE_URI}
```

1. Run the docker-push.sh script to build the image and push to Artifact Registry
```
sudo chmod +x docker-push.sh
./docker-push.sh
```
When GKE has a deployment configured, it can pull this image from Artifact Registry.