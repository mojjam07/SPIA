# Deployment Guide for Render

This guide explains how to deploy your Django project on Render, a cloud platform that supports easy deployment of web services and databases.

---

## 1. Prepare Your Project Repository

- Ensure your project has a `requirements.txt` file listing all dependencies.
- Create a `Dockerfile` in the root of your project if you don't have one. Example Dockerfile:

```Dockerfile
 
```

---

## 2. Create a New Web Service on Render

- Log in to your Render account.
- Click **New** > **Web Service**.
- Connect your GitHub repository containing the project.
- Set the following:
  - **Environment**: Docker
  - **Build Command**: (leave empty, Dockerfile handles build)
  - **Start Command**: (leave empty, Dockerfile handles start)
  - **Port**: 10000

---

## 3. Provision a Managed PostgreSQL Database on Render

- Click **New** > **PostgreSQL Database**.
- Choose your plan and create the database.
- Once created, note the database connection details (host, port, user, password, database name).

---

## 4. Configure Environment Variables for the Web Service

In your Render Web Service settings, add the following environment variables:

- `DEBUG` = `False`
- `ALLOWED_HOSTS` = your Render service URL (e.g., `your-service.onrender.com`) or your custom domain
- `DB_NAME` = your Render Postgres database name
- `DB_USER` = your Render Postgres user
- `DB_PASSWORD` = your Render Postgres password
- `DB_HOST` = your Render Postgres host
- `DB_PORT` = your Render Postgres port
- `SESSION_COOKIE_SECURE` = `True`
- `CSRF_COOKIE_SECURE` = `True`
- `SECURE_SSL_REDIRECT` = `True`
- `SECURE_HSTS_SECONDS` = `3600`
- `SECURE_HSTS_INCLUDE_SUBDOMAINS` = `True`
- `SECURE_HSTS_PRELOAD` = `True`
- Email settings as per your configuration:
  - `EMAIL_BACKEND`
  - `EMAIL_HOST`
  - `EMAIL_PORT`
  - `EMAIL_USE_TLS`
  - `EMAIL_HOST_USER`
  - `EMAIL_HOST_PASSWORD`

---

## 5. Static Files Handling

- The Dockerfile runs `collectstatic` during build to gather static files into the `staticfiles` directory.
- Render provides ephemeral filesystem, so for persistent static/media files, consider using external storage like AWS S3.
- Alternatively, you can configure Render's persistent disks and update your Django settings accordingly.

---

## 6. Custom Domain and SSL

- Add your custom domain in Render dashboard under your Web Service settings.
- Update your DNS provider to point your domain to Render.
- Render automatically provisions SSL certificates for your domain.

---

## 7. Deploy and Verify

- Push your code to GitHub.
- Render will automatically build and deploy your service.
- Visit your Render URL or custom domain to verify the app is running.

---

## Additional Notes

- If you use migrations, you can run them on Render via the Render shell or by adding a deploy hook.
- Monitor logs in Render dashboard for any errors.
- Adjust settings and environment variables as needed.

---

This guide should help you deploy your Django project on Render smoothly. If you need assistance with any step, feel free to ask.
