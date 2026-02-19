# 🚀 GitHub Setup & Deployment Guide — EcoPackAI

Complete step-by-step instructions to push to GitHub and deploy live.

---

## STEP 1: Create GitHub Repository

1. Go to **https://github.com/new**
2. Fill in:
   - **Repository name:** `ecopackai`
   - **Description:** `AI-Powered Sustainable Packaging Recommendation System`
   - **Visibility:** Public (for free Render deployment)
   - ✅ Do NOT initialise with README (you already have one)
3. Click **Create repository**

---

## STEP 2: Push Your Code to GitHub

Open your terminal in the project folder and run:

```bash
# 1. Initialise git
git init

# 2. Add all files
git add .

# 3. First commit
git commit -m "🌿 Initial commit — EcoPackAI complete project"

# 4. Set main branch
git branch -M main

# 5. Connect to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/ecopackai.git

# 6. Push
git push -u origin main
```

> ✅ Your code is now on GitHub!

---

## STEP 3: Handle Large Files (.pkl models)

The trained `.pkl` model files are ~10–50MB. Use Git LFS:

```bash
# Install Git LFS (first time only)
git lfs install

# Track .pkl files
git lfs track "*.pkl"

# Add the tracking config
git add .gitattributes

# Add and commit models
git add models/
git commit -m "Add trained ML models via Git LFS"
git push
```

Or **skip committing models** — Render will retrain them during build (setup in `render.yaml`).

---

## STEP 4: Deploy to Render (FREE — Recommended)

### 4a. Sign up
Go to **https://render.com** → Sign up with GitHub

### 4b. New Web Service
1. Click **New +** → **Web Service**
2. Connect your GitHub account
3. Select the `ecopackai` repository
4. Click **Connect**

### 4c. Configure the service

| Setting | Value |
|---|---|
| **Name** | `ecopackai` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python scripts/module1_data_collection.py && python scripts/module2_feature_engineering.py && python scripts/module3_ml_training.py && python scripts/module7_bi_dashboard.py` |
| **Start Command** | `gunicorn --chdir app app:app --workers 2 --timeout 120` |
| **Instance Type** | `Free` |

### 4d. Add Environment Variables
Click **Environment** tab and add:

```
FLASK_ENV       = production
FLASK_SECRET_KEY = (click "Generate" for random key)
```

### 4e. Deploy
Click **Create Web Service** → Render builds and deploys automatically.

Your app is live at: `https://ecopackai.onrender.com`

> ⚠️ Free tier spins down after 15 min inactivity. First request after idle takes ~30 seconds.

---

## STEP 5: Add PostgreSQL on Render (Optional)

1. In Render dashboard → **New +** → **PostgreSQL**
2. Name: `ecopackai-db`, Plan: **Free**
3. After creation, go to your Web Service → **Environment**
4. Add these variables (from the DB dashboard):

```
DB_HOST     = (from Render DB info)
DB_PORT     = 5432
DB_NAME     = ecopackai
DB_USER     = (from Render DB info)
DB_PASSWORD = (from Render DB info)
```

5. Update Build Command to include schema setup:
```
pip install -r requirements.txt &&
psql $DATABASE_URL -f database/schema.sql &&
python scripts/module1_data_collection.py &&
python scripts/module2_feature_engineering.py &&
python scripts/module3_ml_training.py
```

---

## STEP 6: Deploy to Heroku (Alternative)

```bash
# Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
heroku login

# Create app
heroku create ecopackai-yourname

# Add Postgres addon
heroku addons:create heroku-postgresql:mini

# Set env vars
heroku config:set FLASK_ENV=production
heroku config:set FLASK_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Deploy
git push heroku main

# Run pipeline on Heroku
heroku run python scripts/module1_data_collection.py
heroku run python scripts/module2_feature_engineering.py
heroku run python scripts/module3_ml_training.py

# Open app
heroku open
```

---

## STEP 7: Set Up Auto-Deploy (CI/CD)

Every `git push main` → auto-deploys to Render:

1. In Render Web Service → **Settings** → **Deploy Hook**
2. Copy the deploy hook URL
3. In GitHub repo → **Settings** → **Secrets and variables** → **Actions**
4. Add secret: `RENDER_DEPLOY_HOOK` = (paste URL)

Now the GitHub Actions workflow (`.github/workflows/ci.yml`) will:
- ✅ Run tests on every push
- ✅ Auto-deploy to Render on `main` branch pushes

---

## STEP 8: Verify Deployment

After deployment, test these URLs:

```bash
# Replace with your actual URL
BASE=https://ecopackai.onrender.com

# Health check
curl $BASE/api/stats

# Get top materials
curl $BASE/api/top_materials?n=5

# Test recommendation
curl -X POST $BASE/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"category":"Electronics","shipping_mode":"Air","weight_kg":1.5,"distance_km":800,"length_cm":30,"width_cm":20,"height_cm":15,"fragility":7,"moisture_sensitive":0}'
```

---

## STEP 9: Future Updates

```bash
# Make changes locally, then:
git add .
git commit -m "feat: describe your changes"
git push origin main
# → GitHub Actions runs tests
# → Render auto-deploys
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Build fails on Render | Check Build Command has no typos; check logs in Render dashboard |
| `ModuleNotFoundError` | Ensure `requirements.txt` is complete |
| App loads but no data | Models not trained — run pipeline scripts in build command |
| Slow first load | Normal for Render free tier — app wakes from sleep |
| DB connection refused | Check env vars match your DB credentials exactly |
| `.pkl` files too large | Use Git LFS (`git lfs track "*.pkl"`) or exclude from git |

---

## Quick Reference

```
📁 Repository:    https://github.com/YOUR_USERNAME/ecopackai
🌐 Live App:      https://ecopackai.onrender.com
📊 Dashboard:     https://ecopackai.onrender.com/dashboard
🔌 API Base:      https://ecopackai.onrender.com/api/
```
