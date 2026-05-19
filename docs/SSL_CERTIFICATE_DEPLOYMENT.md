# ADRION 369 v4.0 - SSL/TLS CERTIFICATE DEPLOYMENT GUIDE

**Date:** 2026-04-08
**Phase:** ETAP 4 (Production Deployment)
**Duration:** ~30-45 minutes setup + 5 minute certificate updates
**Author:** MASTER ORCHESTRATOR (ADRION 369)

---

## TABLE OF CONTENTS

1. [Prerequisites](#prerequisites)
2. [Option A: Let's Encrypt (Free)](#option-a-lets-encrypt-free)
3. [Option B: Commercial Certificate](#option-b-commercial-certificate)
4. [Nginx Configuration](#nginx-configuration)
5. [Certificate Renewal Automation](#certificate-renewal-automation)
6. [Verification Checklist](#verification-checklist)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- Linux server with public domain (not localhost)
- Port 80 and 443 accessible from internet
- Root or sudo access
- Nginx web server installed: `nginx --version`

### Environment Variables (from .env)

```bash
# Required in .env:
SSL_ENABLED=true
SSL_CERT_PATH=/etc/letsencrypt/live/your-domain.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/your-domain.com/privkey.pem
SSL_VERIFY=true
DOMAIN=your-domain.com           # Your production domain
EMAIL_ADMIN=admin@your-domain.com # For certificate expiry notices
```

---

## OPTION A: Let's Encrypt (Free) ✅ RECOMMENDED

### Step 1: Install Certbot

Let's Encrypt's official tool for automatic certificate management.

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install -y certbot python3-certbot-nginx

# Check installation
certbot --version
```

### Step 2: Obtain Certificate (Interactive)

```bash
# Stop Nginx temporarily
sudo systemctl stop nginx

# Generate certificate (interactive)
sudo certbot certonly --standalone \
    --email admin@your-domain.com \
    --agree-tos \
    --non-interactive \
    -d your-domain.com \
    -d www.your-domain.com

# Output will be:
# Congratulations! Your certificate and chain have been saved at:
#   /etc/letsencrypt/live/your-domain.com/fullchain.pem
#   /etc/letsencrypt/live/your-domain.com/privkey.pem
```

**Important Fields:**

- `--email`: Renewal reminders sent here
- `-d`: Domain names (can use multiple -d for subdomains)
- `--standalone`: Certbot uses its own web server (not tied to Nginx)

### Step 3: Non-Interactive Certificate (Automated)

```bash
# For CI/CD environments without interactive prompts
sudo certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email $EMAIL_ADMIN \
    --no-eff-email \
    -d $DOMAIN

# Or using Docker (if running in container)
docker run -it --rm --name certbot \
    -v "/etc/letsencrypt:/etc/letsencrypt" \
    certbot/certbot certonly \
    --standalone \
    -d your-domain.com \
    --email admin@your-domain.com \
    --agree-tos
```

### Step 4: Verify Certificate Installation

```bash
# Check certificate details
sudo openssl x509 -in /etc/letsencrypt/live/your-domain.com/fullchain.pem -text -noout

# Expected output includes:
#   Subject: CN = your-domain.com
#   Issuer: CN = R3, O = Let's Encrypt
#   Not Before: Apr  8 12:34:56 2026
#   Not After : Jul  7 12:34:56 2026

# Check certificate validity
sudo certbot certificates

# Output:
# Found the following certs:
#   Certificate Name: your-domain.com
#     Domains: your-domain.com, www.your-domain.com
#     Expiry Date: 2026-07-07
#     Certificate Path: /etc/letsencrypt/live/your-domain.com/fullchain.pem
```

---

## OPTION B: Commercial Certificate

### Step 1: Generate CSR (Certificate Signing Request)

```bash
# Create private key
openssl genrsa -out /etc/ssl/private/domain.key 2048

# Generate CSR
openssl req -new \
    -key /etc/ssl/private/domain.key \
    -out /etc/ssl/certs/domain.csr \
    -subj "/C=US/ST=CA/L=SF/O=YourCompany/CN=your-domain.com"

# Verify CSR
openssl req -in /etc/ssl/certs/domain.csr -text -noout
```

### Step 2: Submit to Certificate Authority

1. Go to CA provider (Sectigo, DigiCert, etc.)
2. Upload CSR from `domain.csr`
3. Complete domain validation (CNAME/TXT record)
4. Receive certificate + chain

### Step 3: Install Commercial Certificate

```bash
# Save certificate files from CA
sudo cp /path/to/domain.crt /etc/ssl/certs/domain.crt
sudo cp /path/to/chain.crt /etc/ssl/certs/chain.crt

# Combine certificate + chain (some CAs require)
sudo cat /etc/ssl/certs/domain.crt /etc/ssl/certs/chain.crt > /etc/ssl/certs/fullchain.pem

# Verify
sudo openssl x509 -in /etc/ssl/certs/domain.crt -text -noout
```

---

## Nginx Configuration

### Step 5: Update Nginx SSL Configuration

**File:** `/etc/nginx/nginx.conf` or `/etc/nginx/sites-available/adrion.conf`

```nginx
# ============================================================================
# ADRION 369 v4.0 - NGINX SSL CONFIGURATION
# ============================================================================

# Redirect HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;

    # Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # All other traffic → HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # ========== SSL CERTIFICATES ==========
    # For Let's Encrypt:
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # For commercial certificates:
    # ssl_certificate /etc/ssl/certs/fullchain.pem;
    # ssl_certificate_key /etc/ssl/private/domain.key;

    # ========== SSL PROTOCOL & CIPHERS ==========
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # ========== SECURITY HEADERS ==========
    # Strict Transport Security (HSTS)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Content Security Policy
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'" always;

    # X-Frame-Options (prevent clickjacking)
    add_header X-Frame-Options "DENY" always;

    # X-Content-Type-Options
    add_header X-Content-Type-Options "nosniff" always;

    # X-XSS-Protection
    add_header X-XSS-Protection "1; mode=block" always;

    # Referrer-Policy
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # ========== PROXY CONFIGURATION ==========
    location / {
        proxy_pass http://localhost:8000;  # Flask/ADRION backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # ========== MCP SERVER PROXY ==========
    # Genesis-MCP
    location /mcp/genesis/ {
        proxy_pass http://localhost:9004/;
        proxy_set_header X-Forwarded-Proto https;
    }

    # Router-MCP
    location /mcp/router/ {
        proxy_pass http://localhost:9001/;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /mcp/guardian/ {
        proxy_pass http://localhost:9002/;
        proxy_set_header X-Forwarded-Proto https;
    }

    # ========== SECURITY LOCATIONS ==========
    # Prevent access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Prevent access to .env files
    location ~ \.env {
        deny all;
    }

    # ========== LOGGING ==========
    access_log /var/log/nginx/adrion_access.log combined;
    error_log /var/log/nginx/adrion_error.log warn;
}
```

### Step 6: Test Nginx Configuration

```bash
# Syntax check
sudo nginx -t

# Expected: "nginx: the configuration file /etc/nginx/nginx.conf syntax is ok"

# Reload Nginx
sudo systemctl reload nginx

# Check status
sudo systemctl status nginx
```

---

## Certificate Renewal Automation

### Step 7: Set Up Automatic Renewal

**For Let's Encrypt:**

```bash
# Test renewal process (dry run)
sudo certbot renew --dry-run

# Check renewal is scheduled
sudo systemctl list-timers | grep certbot

# Manual renewal (if needed)
sudo certbot renew

# Set crontab for daily renewal checks (Let's Encrypt)
sudo crontab -e

# Add line:
0 12 * * * certbot renew --quiet && systemctl reload nginx

# Verify crontab
sudo crontab -l
```

### Step 8: Renewal Monitoring

```bash
# Check certificate expiry (reminder 30 days before)
sudo certbot certificates

# Manual check for expiry dates:
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | \
  openssl x509 -noout -dates
```

---

## Verification Checklist

### Step 9: Verify SSL Configuration

```bash
# 9.1: Test HTTPS connectivity
curl -I https://your-domain.com/
# Expected: HTTP/2 200

# 9.2: Check certificate chain
openssl s_client -connect your-domain.com:443 -showcerts

# 9.3: Verify HSTS header
curl -I https://your-domain.com/ | grep Strict-Transport-Security
# Expected: "Strict-Transport-Security: max-age=31536000..."

# 9.4: Test TLS version
openssl s_client -connect your-domain.com:443 -tls1_1
# Expected: "SSL_ERROR_PROTOCOL_ERROR" (TLS 1.1 disabled) ✅

# 9.5: Test SSL rating (Mozilla Observatory)
# Go to: https://observatory.mozilla.org/
# Rate your domain for security headers

# 9.6: SSLLabs test (comprehensive SSL check)
# Go to: https://www.ssllabs.com/ssltest/
# Scan your domain (usually gets A+ grade)
```

### SSL Configuration Test Results

| Test              | Command                    | Expected Result             | Status   |
| ----------------- | -------------------------- | --------------------------- | -------- |
| HTTPS Access      | `curl -I https://...`      | 200 OK                      | [ ] Pass |
| Certificate Valid | `certbot certificates`     | Not expired                 | [ ] Pass |
| HSTS Header       | `curl -I https://...`      | "Strict-Transport-Security" | [ ] Pass |
| TLS 1.2+ Only     | `openssl s_client -tls1_1` | Protocol error              | [ ] Pass |
| HTTP Redirect     | `curl -I http://...`       | 301 redirect                | [ ] Pass |
| Certificate Chain | openssl s_client           | Full chain shown            | [ ] Pass |
| Security Headers  | Response headers           | All 5 headers present       | [ ] Pass |

---

## Troubleshooting

### Issue: Certificate Not Found After Installation

```bash
# Verify Let's Encrypt directory exists
ls -la /etc/letsencrypt/live/your-domain.com/

# If not found, regenerate:
sudo certbot certonly --standalone -d your-domain.com

# Check file permissions
sudo ls -la /etc/letsencrypt/live/your-domain.com/
# Should show: root readable
```

### Issue: Nginx: "SSL certificate problem"

```bash
# Verify path in nginx.conf matches actual certificate path
sudo certbot certificates | grep "Certificate Name"

# Update nginx.conf with correct path
# Reload Nginx
sudo nginx -t && sudo systemctl reload nginx
```

### Issue: Let's Encrypt Rate Limiting Error

```bash
# Error: "too many certificates already issued"
# Solution: Use staging server for testing
sudo certbot certonly --staging --standalone -d your-domain.com

# Or delete certificate and retry (after waiting 1 hour)
sudo certbot delete --cert-name your-domain.com
```

### Issue: Certificate Renewal Failed

```bash
# Check logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# Manual renewal with verbose output
sudo certbot renew -v

# Check if port 80 is accessible
sudo ss -tulpn | grep :80

# Restart certbot service
sudo systemctl restart nginx
```

### Issue: Mixed Content Warning in Browser

```nginx
# Add X-Forwarded-Proto header in all proxy configurations
proxy_set_header X-Forwarded-Proto $scheme;

# And configure Flask app to use HTTPS:
# In app.py: app.config['PREFERRED_URL_SCHEME'] = 'https'

# Reload Nginx
sudo systemctl reload nginx
```

---

## Production Checklist

### Pre-Deployment

- [ ] Certificate obtained from Let's Encrypt or CA
- [ ] Nginx configuration tested (`nginx -t`)
- [ ] All 5 security headers configured in `server {}` block
- [ ] HSTS preload ready (if desired)
- [ ] Renewal automation set up (crontab or certbot systemd)
- [ ] Monitoring alerts configured for certificate expiry

### Post-Deployment (24 hours)

- [ ] HTTPS working on all domains (test: `curl -I https://...`)
- [ ] HTTP → HTTPS redirect working
- [ ] Certificate chain valid (test: SSLLabs)
- [ ] Security headers present (test: `curl -I https://...`)
- [ ] No mixed content warnings
- [ ] Performance acceptable (<100ms additional latency)

### Ongoing Monitoring

- [ ] Certificate expiry notifications received
- [ ] Automatic renewal logs monitored
- [ ] Monthly SSL Labs test performed
- [ ] Guardian Law compliance maintained (G5 transparency of TLS)

---

## Performance Notes

### SSL/TLS Optimization

- **Session resumption:** `ssl_session_cache` enabled (10m cache)
- **HTTP/2:** Enabled for multiplexing (faster load)
- **OCSP Stapling:** Can be added for real-time revocation checks:
  ```nginx
  ssl_stapling on;
  ssl_stapling_verify on;
  resolver 8.8.8.8;
  ```

### Expected Overhead

- **Initial TLS handshake:** +50-100ms (first request only)
- **Subsequent requests:** <5ms overhead (TLS session cached)
- **HSTS preload:** <1ms (browser cached)

---

## Security Best Practices

### 1. Key Rotation

```bash
# Rotate private key annually (Let's Encrypt does automatically)
# Manual rotation: Delete cert + renew
sudo certbot delete --cert-name your-domain.com
sudo certbot certonly --standalone -d your-domain.com
```

### 2. Certificate Pinning (Advanced)

```nginx
# HPKP header (use with caution - can lock users out)
# Not recommended unless you have backup public key
add_header Public-Key-Pins "pin-sha256=\"base64encodedkey\"; max-age=2592000; includeSubDomains" always;
```

### 3. Monitoring & Alerts

```bash
# Set up monitoring for certificate expiry
# Add to monitoring system (Prometheus, Datadog, etc.):
echo $(date -d "$(openssl x509 -in /etc/letsencrypt/live/your-domain.com/cert.pem -noout -enddate | cut -d= -f 2)" +%s)
```

---

## Implementation Timeline

| Step               | Duration    | Notes                                |
| ------------------ | ----------- | ------------------------------------ |
| 1. Install Certbot | 2 min       | `apt install -y certbot`             |
| 2. Get Certificate | 5 min       | `certbot certonly --standalone`      |
| 3. Configure Nginx | 10 min      | Copy SSL configuration               |
| 4. Test & Reload   | 5 min       | `nginx -t && systemctl reload nginx` |
| 5. Verify HTTPS    | 5 min       | Test via curl + browser              |
| 6. Set Up Renewal  | 5 min       | Add to crontab                       |
| **Total**          | **~30 min** | All steps                            |

---

## References

- **Let's Encrypt Docs:** https://letsencrypt.org/docs/
- **Certbot Manual:** https://certbot.eff.org/docs/
- **Mozilla SSL Configuration Generator:** https://ssl-config.mozilla.org/
- **OWASP TLS Guidelines:** https://owasp.org/www-community/controls/Transport_Layer_Protection_Cheat_Sheet
- **Guardian Law G5 (Transparency):** SSL logs recorded to audit trail

---

**Created:** 2026-04-08
**ETAP 4 - Production Deployment**
**ADRION 369 v4.0 - MASTER ORCHESTRATOR**
