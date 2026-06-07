# Deployment Guide - Resume Screening & ATS Scoring Platform

This document provides complete, end-to-end instructions for deploying this Gradio-based application using three different hosting models.

---

## 🚀 Option 1: Hugging Face Spaces (Easiest & Free)

Hugging Face Spaces natively supports Gradio. It is the fastest way to get your app online.

### Step 1: Create a Space
1. Log in to [Hugging Face](https://huggingface.co/).
2. Click on **Spaces** -> **Create new Space**.
3. Configure the Space:
   * **Space Name**: `resume-ats-screener` (or similar)
   * **License**: `mit` (or open-source choice)
   * **SDK**: `Gradio`
   * **Gradio Template**: `Blank`
   * **Space Hardware**: `CPU Basic` (Free)
   * **Visibility**: `Public` or `Private`

### Step 2: Configure Environment Secrets
1. In your newly created Space, click on the **Settings** tab.
2. Scroll to the **Variables and secrets** section.
3. Click **New secret** and add your LLM API keys:
   * Name: `OPENAI_API_KEY`, Value: `your-actual-api-key`
   * Name: `GEMINI_API_KEY`, Value: `your-actual-api-key`
   * Name: `GROQ_API_KEY`, Value: `your-actual-api-key`
4. Set default provider configurations (as Variables):
   * Name: `DEFAULT_LLM_PROVIDER`, Value: `openai` (or `gemini`)
   * Name: `DEFAULT_MODEL_NAME`, Value: `gpt-4o` (or `gemini-2.5-flash`)
   * Name: `EMBEDDING_PROVIDER`, Value: `huggingface`
   * Name: `EMBEDDING_MODEL_NAME`, Value: `sentence-transformers/all-MiniLM-L6-v2`

### Step 3: Push Your Code
1. Clone the Space's repository locally:
   ```bash
   git clone https://huggingface.co/spaces/your-username/resume-ats-screener
   cd resume-ats-screener
   ```
2. Copy all your workspace files (excluding `venv/`, `.env`, and local `.log`/`.faiss` files) into the cloned directory.
3. Commit and push the code:
   ```bash
   git add .
   git commit -m "Initial Gradio Deployment"
   git push
   ```
Hugging Face will automatically read the `requirements.txt` file, install dependencies, and launch your server at `https://huggingface.co/spaces/your-username/resume-ats-screener`.

---

## 🐳 Option 2: Docker Containerization (AWS ECS / GCP Cloud Run)

For production-grade, isolated cloud deployments, build a Docker container.

### Step 1: Create the Configuration Files
Create a [Dockerfile](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/Dockerfile) in your root folder:
```dockerfile
FROM python:3.10-slim

# Set environment paths and configurations
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GRADIO_SERVER_NAME=0.0.0.0 \
    GRADIO_SERVER_PORT=7860

WORKDIR /app

# Install build dependencies (for FAISS/wheel compilation if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose server port
EXPOSE 7860

# Run entrypoint
CMD ["python", "main.py"]
```

Create a [.dockerignore](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/.dockerignore) file:
```text
venv/
.git/
.env
logs/
data/
TestScripts/
__pycache__/
*.log
*.faiss
*.pkl
```

### Step 2: Build and Test the Image Locally
1. Build the Docker image:
   ```bash
   docker build -t resume-ats-app:latest .
   ```
2. Run it locally using your environment variables:
   ```bash
   docker run -p 7860:7860 --env-file .env resume-ats-app:latest
   ```
3. Test by opening `http://localhost:7860` in your browser.

### Step 3: Deploy to Cloud Provider
#### Deployment to Google Cloud Run (Serverless)
1. Authenticate with gcloud:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
2. Submit the build to GCP Container Registry:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/resume-ats-app:latest
   ```
3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy resume-ats-service \
     --image gcr.io/YOUR_PROJECT_ID/resume-ats-app:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 7860 \
     --set-env-vars="DEFAULT_LLM_PROVIDER=openai,DEFAULT_MODEL_NAME=gpt-4o,EMBEDDING_PROVIDER=huggingface,EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2"
   ```
   *(Be sure to pass your `OPENAI_API_KEY` or `GEMINI_API_KEY` via the `--set-env-vars` flag or configure them securely in the GCP Console under Secrets).*

---

## 🖥️ Option 3: VPS / VM (Ubuntu Server + Nginx + SSL)

If you are hosting on a dedicated VM instance (like an AWS EC2, DigitalOcean Droplet, or Linode) running Ubuntu Server.

### Step 1: System Package Update & Installation
Connect to your server via SSH and install the system prerequisites:
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git nginx certbot python3-certbot-nginx
```

### Step 2: Clone Code & Configure virtualenv
1. Clone your project repository:
   ```bash
   sudo mkdir -p /var/www/resume-ats-app
   sudo chown -R ubuntu:ubuntu /var/www/resume-ats-app
   git clone https://github.com/your-username/ResumeScreening-ATSScoring.git /var/www/resume-ats-app
   cd /var/www/resume-ats-app
   ```
2. Setup virtual environment and install packages:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
3. Create your `.env` configuration file:
   ```bash
   nano .env
   ```
   Paste your configuration variables (keys and default models) and save (Ctrl+O, Enter, Ctrl+X).

### Step 3: Set up Systemd Daemon Service
Create a system service file so the Gradio app runs continuously in the background and restarts on system reboots:
```bash
sudo nano /etc/systemd/system/resume-ats.service
```

Paste the following configurations:
```ini
[Unit]
Description=Gradio Resume ATS Application Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/resume-ats-app
ExecStart=/var/www/resume-ats-app/venv/bin/python main.py
Restart=always
RestartSec=5
Environment=PATH=/var/www/resume-ats-app/venv/bin:/usr/bin:/usr/local/bin

[Install]
WantedBy=multi-user.target
```

Enable and start the system service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable resume-ats.service
sudo systemctl start resume-ats.service
```

Verify it is running correctly:
```bash
sudo systemctl status resume-ats.service
```

### Step 4: Configure Nginx Reverse Proxy
To bind Gradio (running internally on port 7860) to HTTP Port 80 (and later HTTPS SSL):
```bash
sudo nano /etc/nginx/sites-available/default
```

Replace the contents of the `server { ... }` block with this reverse proxy definition:
```nginx
server {
    listen 80;
    server_name yourdomain.com; # Replace with your actual domain or VPS IP

    location / {
        proxy_pass http://127.0.0.1:7860;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Test the configuration and reload Nginx:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

### Step 5: Install SSL Certificates (HTTPS)
Use Let's Encrypt Certbot to automatically configure secure SSL certificates for your domain:
```bash
sudo certbot --nginx -d yourdomain.com
```
Certbot will ask for your email address and prompt you to automatically redirect HTTP traffic to HTTPS. Agree and complete the setup. Nginx will reload and your app will be served securely over HTTPS!
