# 🇮🇷 Iranian Advocacy Email Campaign Platform

A secure web platform that enables global citizens to easily send personalized, AI-generated advocacy emails to international politicians regarding human rights violations in Iran.

## 🏗️ Architecture

- **Frontend**: Cloudflare Pages (Static HTML/CSS/JS)
- **Backend**: Railway (Python FastAPI)
- **Database**: Railway PostgreSQL
- **AI**: OpenAI API (o4-mini)

## 📋 Sprint 0 - Deployment Test

This repository is currently at Sprint 0 with minimal working code to test deployments.

### Current Files:
- ✅ `backend/main.py` - Basic FastAPI app with health check
- ✅ `backend/requirements.txt` - Python dependencies
- ✅ `backend/.env.example` - Environment variables template
- ✅ `frontend/index.html` - Test page for Cloudflare
- ✅ `.gitignore` - Git ignore patterns

---

## 🚀 Deployment Instructions

### **Step 1: Push to GitHub**

```bash
git add .
git commit -m "Sprint 0: Basic deployment setup"
git push origin main
```

### **Step 2: Deploy Backend to Railway**

1. **Create Railway Account**: Go to [Railway.app](https://railway.app)

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose this repository
   - Select "Deploy from /backend folder"

3. **Add PostgreSQL**:
   - In your project, click "New"
   - Select "Database" → "PostgreSQL"
   - Railway will auto-generate `DATABASE_URL`

4. **Set Environment Variables**:
   Go to your backend service → Variables tab → Add:
   ```
   OPENAI_API_KEY=your-api-key-here
   OPENAI_MODEL=o4-mini
   JWT_SECRET=random-32-character-string-here
   FRONTEND_URL=https://yourdomain.org
   ENVIRONMENT=production
   ```

5. **Configure Build Settings**:
   - Root Directory: `/backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

6. **Deploy**: Railway will auto-deploy. You'll get a URL like:
   ```
   https://your-app-name.up.railway.app
   ```

7. **Test Backend**:
   ```bash
   curl https://your-app-name.up.railway.app/api/health
   ```

### **Step 3: Deploy Frontend to Cloudflare Pages**

1. **Create Cloudflare Account**: Go to [Cloudflare Pages](https://pages.cloudflare.com)

2. **Create New Project**:
   - Click "Create a project"
   - Connect to GitHub
   - Select this repository

3. **Configure Build Settings**:
   - Project name: `iranian-advocacy-platform`
   - Production branch: `main`
   - Build command: (leave empty)
   - Build output directory: `/frontend`

4. **Deploy**: Cloudflare will deploy. You'll get a URL like:
   ```
   https://iranian-advocacy-platform.pages.dev
   ```

5. **Add Custom Domain** (Optional):
   - Go to Custom domains
   - Add your domain: `yourdomain.org`
   - Update DNS records as instructed

6. **Update Backend URL in Frontend**:
   - Edit `frontend/index.html`
   - Line 142: Replace `YOUR-RAILWAY-APP` with your actual Railway URL
   - Commit and push changes

7. **Update CORS in Railway**:
   - Go to Railway → Backend service → Variables
   - Update `FRONTEND_URL` to your Cloudflare Pages URL

### **Step 4: Test Everything**

1. Visit your Cloudflare Pages URL
2. Click "Test Backend API" button
3. Should see green "✅ Backend Connected!" message

---

## 🔐 Security Setup

### Generate JWT Secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Get OpenAI API Key:
1. Go to OpenAI API settings
2. Create or copy an API key
3. Add it to Railway environment variables as `OPENAI_API_KEY`

---

## 📁 Project Structure

```
actforiran/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment template
│   ├── database.py             # Database setup + seeding
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── routes/
│   │   ├── public.py           # Public endpoints
│   │   └── admin.py            # (Coming in Sprint 2)
│   └── services/
│       ├── ai_service.py       # OpenAI integration
│       └── auth.py             # (Coming in Sprint 2)
│
└── frontend/
    ├── index.html              # Public interface
    ├── admin.html              # (Coming in Sprint 2)
    ├── css/
    │   └── style.css           # Public styles
    └── js/
        ├── app.js              # Public UI logic
        └── admin.js            # (Coming in Sprint 2)
```

---

## 🐛 Troubleshooting

### Backend not starting on Railway:
- Check logs in Railway dashboard
- Verify all environment variables are set
- Ensure `DATABASE_URL` is auto-set from PostgreSQL service

### Frontend can't connect to backend:
- Check CORS: `FRONTEND_URL` must match your Cloudflare domain
- Update API URL in `frontend/index.html`
- Check Railway backend is running (visit `/api/health`)

### CORS errors:
- Railway: Update `FRONTEND_URL` to exact Cloudflare URL
- Don't include trailing slash

---

## 📞 Support

If you encounter issues:
1. Check Railway logs
2. Check Cloudflare Pages deployment logs
3. Verify all environment variables are set correctly

---

## 🗺️ Roadmap

- ✅ **Sprint 0**: Basic deployment (CURRENT)
- 🔄 **Sprint 1**: Public email generation flow
- 🔄 **Sprint 2**: Admin authentication
- 🔄 **Sprint 3**: Admin CRUD (recipients/topics)
- 🔄 **Sprint 4**: Analytics & visualization

---

## 📄 License

This project is dedicated to supporting human rights advocacy in Iran.
