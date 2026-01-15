# Deployment Guide – Google Maps Lead Scraper

This guide covers how to deploy your app to different platforms.

---

## 🚀 Quick Deploy (Choose One)

### Option 1: Render (Recommended – Free tier available)

**Advantages:**
- Free tier available
- Easy GitHub integration
- Auto-deploys on git push
- Good performance

**Steps:**

1. Push your code to GitHub (public or private repo)
2. Go to https://render.com
3. Click "New +" → "Web Service"
4. Select your GitHub repo
5. Configure:
   - **Name:** `google-maps-scraper`
   - **Runtime:** `Python`
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
   - **Free plan:** Select if you want free tier
6. Click "Deploy"
7. Your app is live at: `https://google-maps-scraper.onrender.com`

**Environment variables:**
Go to Settings → Environment → Add environment variables:

```
FLASK_ENV=production
FLASK_DEBUG=False
```

---

### Option 2: Heroku (Classic but slightly more expensive)

**Advantages:**
- Very popular
- Great documentation
- Add-ons for databases, logging

**Steps:**

1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
2. Login:
   ```bash
   heroku login
   ```
3. Create app:
   ```bash
   heroku create google-maps-scraper
   ```
4. Deploy:
   ```bash
   git push heroku main
   ```
5. Open app:
   ```bash
   heroku open
   ```

**View logs:**
```bash
heroku logs --tail
```

**Set environment variables:**
```bash
heroku config:set FLASK_ENV=production
heroku config:set FLASK_DEBUG=False
```

---

### Option 3: DigitalOcean App Platform

**Advantages:**
- Good value ($5-12/month)
- Simple interface
- GitHub integration

**Steps:**

1. Go to https://www.digitalocean.com/products/app-platform
2. Click "Create App"
3. Select GitHub repo
4. Configure:
   - **Resource:** Basic plan ($5/month)
   - **HTTP Port:** 5000
   - **Buildpack:** Python
5. Click "Deploy"

---

### Option 4: Deploy to Your Own Server (VPS)

**Best for:** Full control, custom domain, production workloads

**Steps:**

1. Rent a VPS (Linode, AWS EC2, DigitalOcean Droplet, etc.)
2. SSH into server:
   ```bash
   ssh root@your_server_ip
   ```
3. Install dependencies:
   ```bash
   apt update && apt install python3 python3-pip python3-venv nginx
   ```
4. Clone repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/google-maps-scraper.git
   cd google-maps-scraper
   ```
5. Create virtual env:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
6. Create systemd service (`/etc/systemd/system/scraper.service`):
   ```ini
   [Unit]
   Description=Google Maps Scraper
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/home/user/google-maps-scraper
   Environment="PATH=/home/user/google-maps-scraper/venv/bin"
   ExecStart=/home/user/google-maps-scraper/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:5000 app:app

   [Install]
   WantedBy=multi-user.target
   ```
7. Start service:
   ```bash
   systemctl enable scraper
   systemctl start scraper
   ```
8. Configure Nginx as reverse proxy
9. Enable HTTPS with Let's Encrypt

---

## 📋 Pre-deployment Checklist

Before deploying to production, verify:

- [ ] `FLASK_ENV=production`
- [ ] `FLASK_DEBUG=False`
- [ ] `.env` file is NOT committed to git
- [ ] All secrets (API keys) are in environment variables
- [ ] `requirements.txt` is up-to-date
- [ ] Tests pass locally
- [ ] No hardcoded paths or IPs
- [ ] Logging is configured
- [ ] Error handling is robust
- [ ] Rate limiting is implemented
- [ ] HTTPS/SSL is enabled
- [ ] Database (if any) is backed up regularly

---

## 🔐 Security Checklist

- [ ] Set strong `SECRET_KEY` for Flask sessions
- [ ] Never commit `.env` file
- [ ] Use environment variables for all secrets
- [ ] Validate user input (sanitize query strings)
- [ ] Rate limit API endpoints
- [ ] Use HTTPS only (redirect HTTP → HTTPS)
- [ ] Set security headers (CSP, X-Frame-Options, etc.)
- [ ] Keep dependencies updated
- [ ] Monitor error logs for suspicious activity
- [ ] Use API authentication if exposed publicly

---

## 📊 Monitoring

### Render
- Built-in logs: Settings → Logs
- Memory & CPU usage: Metrics tab

### Heroku
- View logs:
  ```bash
  heroku logs -t
  ```
- Monitor dyno usage: Dashboard → Resources

### DigitalOcean
- Metrics: App dashboard
- Logs: Logs tab

### Your own server
- Check status:
  ```bash
  systemctl status scraper
  ```
- View logs:
  ```bash
  journalctl -u scraper -f
  ```

---

## 🚨 Troubleshooting

### App not starting

**Check logs first:**

**Render:**
```
Settings → Logs
```

**Heroku:**
```bash
heroku logs -t
```

**Common errors:**

1. **Module not found** → Check `requirements.txt`
2. **Port already in use** → Change port in config
3. **Out of memory** → Upgrade plan
4. **Timeout** → Increase timeout limits

### High latency

- Check server region
- Monitor CPU/memory usage
- Optimize API calls (add caching)
- Use CDN for static assets

### Database connection errors

- Verify DATABASE_URL environment variable
- Check database credentials
- Ensure database is running
- Check firewall rules

---

## 📈 Scaling

### When your single instance isn't enough

1. **Render:** Upgrade from Free → Standard plan
2. **Heroku:** Add more dynos or upgrade dyno type
3. **DigitalOcean:** Upgrade VM or add load balancer
4. **Custom server:** Add database replication, cache layer (Redis), load balancer

### Optimization tips

- Use database indexing
- Implement response caching (Redis)
- Add CDN for static files
- Optimize scraping (parallel requests)
- Monitor slow queries

---

## 💰 Cost Breakdown (Monthly)

| Platform | Free Tier | Paid Entry |
|----------|-----------|------------|
| **Render** | Yes (~free) | $5–20 |
| **Heroku** | No | $7–50 |
| **DigitalOcean** | No | $5–12 |
| **Your VPS** | No | $5–30 |

For a hobby project or MVP → Use **Render free tier**  
For production → Use **Render Standard** or **DigitalOcean**

---

## 📚 Additional Resources

- [Flask Deployment](https://flask.palletsprojects.com/en/stable/deploying/)
- [Gunicorn Documentation](https://gunicorn.org/)
- [Render Docs](https://render.com/docs)
- [Heroku Docs](https://devcenter.heroku.com/)
- [DigitalOcean Tutorials](https://www.digitalocean.com/community/tutorials)

---

**Deployed successfully? Update your README with the live URL!** 🎉
