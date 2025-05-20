# Deployment Guide for DigitalOcean Droplet

## 1. Create a DigitalOcean Droplet
- Choose Ubuntu 20.04 or 22.04 LTS.
- Select appropriate size and region.
- Add your SSH key for access.

## 2. SSH into the Droplet
```bash
ssh root@your_droplet_ip
```

## 3. Install Docker and Docker Compose
```bash
apt update
apt install -y docker.io docker-compose
systemctl start docker
systemctl enable docker
```

## 4. Clone your project
```bash
cd /opt
git clone your_repo_url project
cd project
```

## 5. Create a `.env` file in the project directory with the following content:
```
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DB_NAME=store_audit
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=3600
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.your-email-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
```

## 6. Start the app with Docker Compose
```bash
docker-compose up -d --build
```

## 7. Collect static files
```bash
docker exec -it $(docker ps -qf "name=project_web") python manage.py collectstatic --noinput
```

## 8. Configure your domain DNS
- Point your domain's A record to your Droplet's IP address.

## 9. Install Certbot and obtain SSL certificate
```bash
apt install -y certbot
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

## 10. Configure SSL termination
- You can configure a reverse proxy like Nginx to handle SSL and forward requests to your Docker container.
- Alternatively, configure Gunicorn to use SSL certificates directly (less common).

## 11. Update Django settings if needed
- Ensure `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, and `CSRF_COOKIE_SECURE` are set to True (already set in deployment_settings.py).

## 12. Restart Docker containers if any changes made
```bash
docker-compose down
docker-compose up -d --build
```

## 13. Verify your app is running
- Visit https://yourdomain.com in your browser.

---

This guide assumes you have basic knowledge of Linux command line and DNS management.

For DigitalOcean App Platform deployment, the process is simpler and involves connecting your GitHub repo and configuring environment variables via the DigitalOcean dashboard.
