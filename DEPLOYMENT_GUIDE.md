# 🚀 InstruNet AI - Deployment Guide

This guide provides instructions for deploying InstruNet AI in various environments.

## 📋 Table of Contents

1. [Local Development](#local-development)
2. [Production Deployment](#production-deployment)
3. [Security Best Practices](#security-best-practices)
4. [Performance Optimization](#performance-optimization)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)

## 🏠 Local Development

### Quick Start

```bash
# 1. Activate virtual environment
source instrunet_env/bin/activate  # Linux/Mac
# OR
instrunet_env\Scripts\activate     # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run development server
streamlit run app.py
```

### Development Configuration

Create a `.streamlit/config.toml` file:

```toml
[server]
port = 8501
headless = false
enableCORS = false

[browser]
gatherUsageStats = false
serverAddress = "localhost"

[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f9fafb"
textColor = "#1f2937"
font = "sans serif"
```

## 🌐 Production Deployment

### Option 1: Cloud Deployment (Streamlit Cloud)

1. **Push to GitHub**

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Select the main file: `app.py`
   - Add secrets in the dashboard:
     ```
     INSTRUNET_PASSWORD = "your_secure_password"
     ```

3. **Model File Handling**
   - Ensure `model/best_l2_regularized_model.h5` is in the repository
   - If too large, consider using Git LFS or cloud storage

### Option 2: Docker Deployment

1. **Create Dockerfile**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8501

# Set environment variables
ENV INSTRUNET_PASSWORD=change_me_in_production

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

2. **Build and Run**

   ```bash
   # Build image
   docker build -t instrunet-ai .

   # Run container
   docker run -d \
     -p 8501:8501 \
     -e INSTRUNET_PASSWORD=your_secure_password \
     --name instrunet-app \
     instrunet-ai
   ```

3. **Docker Compose** (recommended)

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  instrunet-ai:
    build: .
    ports:
      - "8501:8501"
    environment:
      - INSTRUNET_PASSWORD=${INSTRUNET_PASSWORD}
    volumes:
      - ./model:/app/model:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run with:

```bash
docker-compose up -d
```

### Option 3: Traditional Server Deployment

1. **Setup Server** (Ubuntu 20.04+)

   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Python
   sudo apt install python3.10 python3-pip python3-venv -y

   # Install dependencies
   sudo apt install libsndfile1 build-essential -y
   ```

2. **Deploy Application**

   ```bash
   # Create app directory
   sudo mkdir -p /opt/instrunet-ai
   cd /opt/instrunet-ai

   # Copy files or clone repository
   git clone <your-repo-url> .

   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install requirements
   pip install -r requirements.txt
   ```

3. **Create Systemd Service**

Create `/etc/systemd/system/instrunet-ai.service`:

```ini
[Unit]
Description=InstruNet AI Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/instrunet-ai
Environment="PATH=/opt/instrunet-ai/venv/bin"
Environment="INSTRUNET_PASSWORD=your_secure_password"
ExecStart=/opt/instrunet-ai/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
Restart=always

[Install]
WantedBy=multi-user.target
```

4. **Enable and Start Service**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable instrunet-ai
   sudo systemctl start instrunet-ai
   sudo systemctl status instrunet-ai
   ```

5. **Setup Nginx Reverse Proxy**

Create `/etc/nginx/sites-available/instrunet-ai`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
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

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/instrunet-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

6. **Setup SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx -y
   sudo certbot --nginx -d your-domain.com
   ```

## 🔒 Security Best Practices

### Password Management

1. **Never commit passwords to Git**

   ```bash
   # Add to .gitignore
   echo ".env" >> .gitignore
   echo "*.env" >> .gitignore
   ```

2. **Use Strong Passwords**

   ```bash
   # Generate secure password
   openssl rand -base64 32
   ```

3. **Environment Variables**
   ```bash
   # Set in production
   export INSTRUNET_PASSWORD="$(openssl rand -base64 32)"
   ```

### Application Security

1. **HTTPS Only**
   - Always use SSL/TLS in production
   - Redirect HTTP to HTTPS

2. **Rate Limiting**
   - Implement rate limiting to prevent abuse
   - Use Nginx or cloud provider features

3. **File Upload Restrictions**
   - Validate file types (WAV, MP3 only)
   - Limit file size (current: handled by Streamlit)
   - Sanitize filenames

4. **Session Management**
   - Sessions timeout after inactivity
   - Implement logout functionality

### Network Security

```nginx
# Nginx security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

## ⚡ Performance Optimization

### Model Loading

```python
# app.py - Cache model loading
@st.cache_resource
def load_model():
    return tf.keras.models.load_model("model/best_l2_regularized_model.h5")

model = load_model()
```

### Audio Processing

1. **Limit File Size**

   ```python
   # Add to app.py
   MAX_FILE_SIZE_MB = 50
   if len(audio_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
       st.error(f"File too large. Maximum size: {MAX_FILE_SIZE_MB}MB")
   ```

2. **Parallel Processing** (for large files)
   ```python
   # Consider using multiprocessing for segment analysis
   from multiprocessing import Pool
   ```

### Caching Strategy

```python
# Cache audio features
@st.cache_data
def extract_features(audio_bytes):
    # Feature extraction logic
    pass
```

### Resource Limits (Docker)

```yaml
# docker-compose.yml
services:
  instrunet-ai:
    # ... other config
    deploy:
      resources:
        limits:
          cpus: "2"
          memory: 4G
        reservations:
          cpus: "1"
          memory: 2G
```

## 📊 Monitoring and Maintenance

### Logging

1. **Application Logs**

   ```bash
   # View systemd service logs
   sudo journalctl -u instrunet-ai -f

   # Docker logs
   docker logs -f instrunet-app
   ```

2. **Nginx Access Logs**
   ```bash
   tail -f /var/log/nginx/access.log
   ```

### Health Checks

1. **Streamlit Health Endpoint**

   ```bash
   curl http://localhost:8501/_stcore/health
   ```

2. **Automated Monitoring**
   - Use tools like Uptime Robot, Pingdom
   - Set up email/SMS alerts

### Backup Strategy

1. **Model Files**

   ```bash
   # Backup model
   rsync -av model/ /backup/instrunet-ai/model/
   ```

2. **Configuration Files**
   ```bash
   # Backup configs
   tar -czf configs-$(date +%Y%m%d).tar.gz .streamlit/ .env
   ```

### Updates and Maintenance

1. **Update Dependencies**

   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Update Application**

   ```bash
   git pull origin main
   sudo systemctl restart instrunet-ai
   ```

3. **Database/Storage Cleanup**
   ```bash
   # Clean temp files
   find /tmp -name "tmp*" -mtime +7 -delete
   ```

## 🔍 Troubleshooting

### Common Issues

**Port Already in Use**

```bash
# Find process
sudo lsof -i :8501
# Kill process
sudo kill <PID>
```

**Memory Issues**

```bash
# Check memory usage
free -h
# Restart service
sudo systemctl restart instrunet-ai
```

**Model Loading Errors**

```bash
# Verify model file
ls -lh model/best_l2_regularized_model.h5
# Check permissions
sudo chmod 644 model/best_l2_regularized_model.h5
```

## 📞 Support

For deployment issues:

1. Check application logs
2. Verify environment variables
3. Ensure all dependencies are installed
4. Check file permissions
5. Review Streamlit documentation

## 🎯 Deployment Checklist

Before going live:

- [ ] Change default password
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerts
- [ ] Configure automated backups
- [ ] Test authentication flow
- [ ] Verify model file accessibility
- [ ] Test file upload functionality
- [ ] Check resource limits
- [ ] Review logs for errors
- [ ] Document deployment process
- [ ] Set up maintenance schedule

---

**🚀 Happy Deploying!**
