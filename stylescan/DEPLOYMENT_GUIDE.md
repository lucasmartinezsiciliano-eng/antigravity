# VISAI Deployment Guide

**Status:** 🚀 Ready for production  
**Target Date:** May 18-19, 2026  
**Environments:** Staging → Production  

---

## Pre-Deployment Checklist

### Code & Configuration (May 18 Morning)

- [ ] All tests passing (`pytest tests/ --cov=app`)
- [ ] No console errors/warnings in logs
- [ ] TypeScript builds without errors (`npm run build` in web/)
- [ ] Environment variables configured (copy `.env.example` → `.env`)
- [ ] Git state clean (no untracked production secrets)
- [ ] Latest code committed and tagged

### Services & API Keys (May 18 Afternoon)

- [ ] **Cloudinary**
  - [ ] API key obtained from account
  - [ ] Unsigned upload preset created
  - [ ] Folder structure set up: `barber_references/`
  - [ ] CORS whitelist configured

- [ ] **Resend Email**
  - [ ] API key obtained
  - [ ] Sender email verified
  - [ ] Email template tested
  - [ ] Reply-to address configured

- [ ] **Telegram Bot**
  - [ ] Bot token obtained from @BotFather
  - [ ] Webhook URL configured
  - [ ] Commands registered (/start, /help, /status)
  - [ ] Bot invite link created

- [ ] **Stripe**
  - [ ] API keys obtained (public + secret)
  - [ ] Webhook endpoint created
  - [ ] Test mode verified first
  - [ ] Coupon setup for promo codes

---

## Deployment Steps

### Phase 1: Environment Setup (May 18, 2:00 PM UTC)

#### 1.1 Backend Environment

```bash
# Create .env from template
cp stylescan/backend/.env.example stylescan/backend/.env

# Fill in all credentials:
# - DATABASE_URL (PostgreSQL recommended for prod)
# - CLOUDINARY_* keys
# - RESEND_API_KEY
# - TELEGRAM_BOT_TOKEN
# - STRIPE_* keys
# - FRONTEND_URL
# - SECRET_KEY (generate: python -c "import secrets; print(secrets.token_hex(32))")

# Install dependencies
cd stylescan/backend
pip install -r requirements.txt

# Verify .env is loaded
python -c "from app.core.config import settings; print(settings.APP_NAME)"
# Should output: "VISAI API"
```

#### 1.2 Frontend Environment

```bash
# Create .env.local
cd stylescan/web
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=https://api.visai.es
NEXT_PUBLIC_APP_ENV=production
EOF

# Build Next.js app
npm run build

# Verify build completed
ls -la .next/
```

#### 1.3 Database Setup

```bash
# If using PostgreSQL:
# 1. Create database:
createdb visai_prod

# 2. Run migrations (if using Alembic):
# alembic upgrade head

# 3. If no migration tool, initialize via Python:
python -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
"

# 4. Verify tables created:
psql visai_prod -c "\dt"
# Should show: analyses, barber_partners, commissions, etc.
```

---

### Phase 2: Deployment to Staging (May 18, 3:00 PM UTC)

#### 2.1 Backend Deployment (Railway/AWS/Render)

**Option A: Railway (Recommended for MVP)**

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Create project
railway init

# Add environment variables
railway env --set DEBUG=False
railway env --set DATABASE_URL=postgresql://...
railway env --set CLOUDINARY_NAME=...
railway env --set RESEND_API_KEY=...
# ... (add all env vars from .env)

# Deploy
railway up

# Get URL
railway env
# Backend URL will be: https://visai-backend.railway.app
```

**Option B: AWS Lambda + RDS**

```bash
# Build Docker image
docker build -f stylescan/backend/Dockerfile -t visai-backend:latest .

# Push to ECR
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.eu-west-1.amazonaws.com
docker tag visai-backend:latest 123456789.dkr.ecr.eu-west-1.amazonaws.com/visai-backend:latest
docker push 123456789.dkr.ecr.eu-west-1.amazonaws.com/visai-backend:latest

# Create Lambda function from image
aws lambda create-function \
  --function-name visai-backend \
  --code ImageUri=123456789.dkr.ecr.eu-west-1.amazonaws.com/visai-backend:latest \
  --role arn:aws:iam::123456789:role/lambda-execution-role
```

#### 2.2 Frontend Deployment (Vercel)

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd stylescan/web
vercel --prod

# Set environment variables in dashboard
# - NEXT_PUBLIC_API_URL=https://visai-backend-staging.railway.app

# Preview URL will be: https://visai.vercel.app
```

#### 2.3 Database Backup

```bash
# If using PostgreSQL, backup before deployment
pg_dump visai_prod > visai_prod_backup_2026-05-18.sql

# Store backup securely (S3, Google Cloud Storage, etc.)
aws s3 cp visai_prod_backup_2026-05-18.sql s3://visai-backups/
```

---

### Phase 3: Staging Testing (May 18, 4:00 PM UTC)

#### 3.1 Health Checks

```bash
# Backend health
curl https://visai-backend-staging.railway.app/health
# Expected: {"status": "ok", "version": "1.0.0"}

# Frontend loads
curl https://visai-staging.vercel.app
# Expected: HTML response (check no errors in response)
```

#### 3.2 API Endpoint Tests

```bash
# Test leaderboard endpoint
curl -X GET https://visai-backend-staging.railway.app/api/v1/leaderboard?period=all_time

# Test health endpoint
curl https://visai-backend-staging.railway.app/health

# Test CORS
curl -H "Origin: https://visai-staging.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  https://visai-backend-staging.railway.app/api/v1/leaderboard
# Check CORS headers in response
```

#### 3.3 Manual E2E Testing (30 mins)

```
1. Barber Dashboard
   - Load /barber/dashboard?id=test-barber-001
   - Verify metrics display
   - Test reference photo upload
   - Check photo appears in gallery

2. Leaderboard
   - Load /barber/leaderboard
   - Filter by period (week/month/all-time)
   - Filter by city
   - Search by name

3. Parental Consent
   - Submit analysis as age 14
   - Receive consent email
   - Click authorization link
   - Verify consent confirmed
```

#### 3.4 Database Verification

```bash
# Connect to staging database
psql visai_staging

# Check tables exist
\dt

# Verify data integrity
SELECT COUNT(*) FROM barber_partners;
SELECT COUNT(*) FROM barber_leaderboard_stats;
SELECT COUNT(*) FROM barber_reference_photos;
```

---

### Phase 4: Production Deployment (May 19, 00:00 UTC)

#### 4.1 Production Database Migration

```bash
# 1. Final backup of staging database
pg_dump visai_staging > visai_backup_final_20260519.sql

# 2. Create production database
createdb visai_prod

# 3. Initialize tables (same as staging)
python -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
"

# 4. Verify
psql visai_prod -c "\dt"
```

#### 4.2 Production Backend Deployment

```bash
# Deploy to production (Railway)
railway environment production
railway up

# Or update Lambda function
aws lambda update-function-code \
  --function-name visai-backend \
  --image-uri 123456789.dkr.ecr.eu-west-1.amazonaws.com/visai-backend:v1.0.0

# Verify deployment
curl https://api.visai.es/health
# Expected: {"status": "ok", "version": "1.0.0"}
```

#### 4.3 Production Frontend Deployment

```bash
# Deploy to production (Vercel)
cd stylescan/web
vercel --prod

# Update environment variables
vercel env add NEXT_PUBLIC_API_URL "https://api.visai.es"
vercel --prod

# Verify
curl https://visai.es
```

#### 4.4 DNS Configuration

```bash
# Point domain to production:
# api.visai.es → Railway backend
# visai.es → Vercel frontend

# Update DNS records:
# A record: visai.es → Vercel IP
# CNAME: api.visai.es → Railway domain
```

---

### Phase 5: Post-Deployment Verification (May 19, 01:00 UTC)

#### 5.1 Production Health Checks

```bash
# Backend
curl https://api.visai.es/health

# Frontend
curl https://visai.es -L

# Check SSL certificates
openssl s_client -connect api.visai.es:443 -servername api.visai.es
```

#### 5.2 Monitoring Setup

```bash
# 1. Enable error tracking (Sentry)
SENTRY_DSN=https://xxx@sentry.io/project > .env

# 2. Set up log aggregation (CloudWatch / ELK)
# Configure in deployment dashboard

# 3. Set up alerts
# - API response time > 1s → alert
# - Error rate > 1% → alert
# - Database connection failures → alert
```

#### 5.3 Initial Barber Onboarding

```
1. Create 3 test barberos manually
2. Generate test promo codes
3. Verify dashboard loads for each
4. Test Telegram notifications
5. Verify email system working
```

---

## Monitoring & Support

### Daily Checks (First Week)

```bash
# Morning (8:00 AM UTC)
curl https://api.visai.es/health
curl https://visai.es

# Check error logs
tail -f logs/api.log | grep ERROR

# Check leaderboard updates
psql visai_prod -c "SELECT * FROM barber_leaderboard_stats ORDER BY last_updated DESC LIMIT 5;"

# Check email delivery
# (check Resend dashboard or email inbox)

# Check Telegram notifications
# (verify bot receives commands)
```

### Rollback Plan

If critical issues arise:

```bash
# 1. Revert backend to previous stable version
railway rollback

# 2. Revert frontend
vercel rollback

# 3. Restore database backup
psql visai_prod < visai_backup_final_20260519.sql

# 4. Verify rollback successful
curl https://api.visai.es/health
```

---

## Security Checklist

- [ ] HTTPS enabled (SSL/TLS certificates valid)
- [ ] CORS restricted (not "*", only visai.es)
- [ ] Rate limiting enabled
- [ ] SQL injection protection (SQLAlchemy parameterized)
- [ ] XSS protection (React escaping)
- [ ] API keys never logged
- [ ] Database backups automated (daily)
- [ ] Secrets in .env, never in git
- [ ] .gitignore excludes .env, credentials
- [ ] Security headers set:
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-Frame-Options: DENY
  - [ ] Referrer-Policy: strict-origin-when-cross-origin
  - [ ] Strict-Transport-Security

---

## Performance Baselines

Target metrics for May 19 launch:

| Metric | Target | Status |
|--------|--------|--------|
| API response time (P95) | < 200ms | ⏳ TBD |
| Dashboard load time | < 1s | ⏳ TBD |
| Leaderboard load time | < 2s | ⏳ TBD |
| Photo upload time | < 10s | ⏳ TBD |
| API uptime | 99.9% | ⏳ TBD |
| Database query time | < 100ms | ⏳ TBD |

---

## Troubleshooting

### Backend won't start

```bash
# Check environment variables
python -c "from app.core.config import settings; print(vars(settings))"

# Check database connection
psql visai_prod -c "SELECT version();"

# Check logs
tail -f uvicorn.log
```

### Frontend not loading

```bash
# Check environment variables in Vercel dashboard
vercel env ls

# Check build logs
vercel logs --tail

# Clear cache
vercel purge
```

### API not responding

```bash
# Check backend health
curl https://api.visai.es/health

# Check rate limits
curl -I https://api.visai.es/api/v1/leaderboard

# Check CORS headers
curl -H "Origin: https://visai.es" -I https://api.visai.es/api/v1/leaderboard
```

---

## Week 2 Post-Launch Tasks

- [ ] Automated database backups (daily to S3)
- [ ] Monitoring dashboard setup (Grafana/DataDog)
- [ ] Incident response playbook
- [ ] Scaling plan (if > 100 barberos)
- [ ] CDN configuration (CloudFlare)
- [ ] API versioning (v2 planning)
- [ ] Load testing (1000 concurrent users)

---

**Generated:** 2026-05-16  
**Status:** Ready to execute  
**Owner:** Lucas (lucas.martinez.siciliano@gmail.com)  
**Approval:** Pending
