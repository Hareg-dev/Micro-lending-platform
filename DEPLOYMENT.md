# Production Deployment Guide

## Server Requirements

### Minimum Specifications
```
CPU: 4 cores (2.4GHz+)
RAM: 8GB
Storage: 100GB SSD
Network: 100Mbps
OS: Ubuntu 22.04 LTS
```

### Recommended for Scale
```
CPU: 8+ cores
RAM: 16GB+
Storage: 500GB+ SSD
Network: 1Gbps
Load Balancer: Nginx/HAProxy
```

## Installation Steps

### 1. System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.11 python3.11-venv python3-pip postgresql postgresql-contrib redis-server nginx supervisor git -y

# Create application user
sudo useradd -m -s /bin/bash microlending
sudo usermod -aG sudo microlending
```

### 2. Database Setup
```bash
# Configure PostgreSQL
sudo -u postgres createuser --interactive microlending
sudo -u postgres createdb microlending_db -O microlending

# Set password
sudo -u postgres psql -c "ALTER USER microlending PASSWORD 'secure_password';"
```

### 3. Application Deployment
```bash
# Switch to app user
sudo su - microlending

# Clone repository
git clone <repository_url> /home/microlending/app
cd /home/microlending/app

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Configure environment
cp .env.example .env
# Edit .env with production settings
```

### 4. Environment Configuration
```bash
# /home/microlending/app/.env
DEBUG=False
SECRET_KEY=your_super_secure_secret_key_here
DATABASE_URL=postgresql://microlending:secure_password@localhost/microlending_db
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
TELEBIRR_APP_ID=your_telebirr_app_id
TELEBIRR_APP_KEY=your_telebirr_app_key
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=noreply@yourdomain.com
EMAIL_HOST_PASSWORD=your_email_password
```

### 5. Database Migration
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

## Service Configuration

### 1. Gunicorn Service
```bash
# /etc/systemd/system/microlending.service
[Unit]
Description=Micro-Lending Platform
After=network.target

[Service]
User=microlending
Group=microlending
WorkingDirectory=/home/microlending/app
Environment=PATH=/home/microlending/app/venv/bin
ExecStart=/home/microlending/app/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 core.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

### 2. Celery Worker Service
```bash
# /etc/systemd/system/celery.service
[Unit]
Description=Celery Worker
After=network.target

[Service]
User=microlending
Group=microlending
WorkingDirectory=/home/microlending/app
Environment=PATH=/home/microlending/app/venv/bin
ExecStart=/home/microlending/app/venv/bin/celery -A core worker -l info
Restart=always

[Install]
WantedBy=multi-user.target
```

### 3. Celery Beat Service
```bash
# /etc/systemd/system/celerybeat.service
[Unit]
Description=Celery Beat Scheduler
After=network.target

[Service]
User=microlending
Group=microlending
WorkingDirectory=/home/microlending/app
Environment=PATH=/home/microlending/app/venv/bin
ExecStart=/home/microlending/app/venv/bin/celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4. Nginx Configuration
```bash
# /etc/nginx/sites-available/microlending
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /static/ {
        alias /home/microlending/app/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /home/microlending/app/media/;
        expires 30d;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## SSL/HTTPS Setup

### Using Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring & Logging

### 1. Log Configuration
```bash
# Create log directories
sudo mkdir -p /var/log/microlending
sudo chown microlending:microlending /var/log/microlending

# Configure Django logging in settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/microlending/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### 2. System Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Monitor services
sudo systemctl status microlending celery celerybeat nginx postgresql redis
```

## Backup Strategy

### 1. Database Backup
```bash
# Create backup script
#!/bin/bash
# /home/microlending/backup_db.sh
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U microlending -h localhost microlending_db > /home/microlending/backups/db_$DATE.sql
find /home/microlending/backups -name "db_*.sql" -mtime +7 -delete

# Make executable and add to cron
chmod +x /home/microlending/backup_db.sh
crontab -e
# Add: 0 2 * * * /home/microlending/backup_db.sh
```

### 2. Application Backup
```bash
# Backup application files
tar -czf /home/microlending/backups/app_$(date +%Y%m%d).tar.gz /home/microlending/app --exclude=venv --exclude=__pycache__
```

## Security Hardening

### 1. Firewall Configuration
```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Fail2Ban Setup
```bash
# Install and configure Fail2Ban
sudo apt install fail2ban -y

# Create jail configuration
sudo tee /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
EOF

sudo systemctl restart fail2ban
```

## Performance Optimization

### 1. Database Optimization
```sql
-- PostgreSQL performance tuning
-- /etc/postgresql/14/main/postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### 2. Redis Optimization
```bash
# /etc/redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## Maintenance Tasks

### Daily Operations
```bash
# Check system health
sudo systemctl status microlending celery celerybeat
df -h
free -m

# Apply late fees
cd /home/microlending/app
source venv/bin/activate
python manage.py apply_late_fees
```

### Weekly Tasks
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Restart services
sudo systemctl restart microlending celery celerybeat

# Check logs
tail -f /var/log/microlending/django.log
```

### Monthly Tasks
```bash
# Database maintenance
sudo -u postgres vacuumdb -d microlending_db -z

# Clean old logs
find /var/log/microlending -name "*.log.*" -mtime +30 -delete

# Security updates
sudo unattended-upgrades
```

## Troubleshooting

### Common Issues
1. **Service won't start**: Check logs with `journalctl -u servicename`
2. **Database connection**: Verify PostgreSQL is running and credentials
3. **Static files**: Run `python manage.py collectstatic`
4. **Celery tasks**: Check Redis connection and worker status

### Emergency Procedures
```bash
# Stop all services
sudo systemctl stop microlending celery celerybeat

# Restore from backup
pg_dump -U microlending -h localhost microlending_db < backup_file.sql

# Restart services
sudo systemctl start microlending celery celerybeat
```