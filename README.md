# ActForIran - Iranian Advocacy Email Campaign Platform

🇮🇷 **پلتفرم کمپین ایمیل حمایتی برای ایران**

A comprehensive web platform for generating personalized advocacy emails to politicians worldwide regarding human rights violations in Iran. Built with FastAPI backend and modern Persian-supported frontend.

## ✨ Features

### 🎯 Core Functionality
- **5-Step Stepper Form**: Guided process for email generation
- **Persian RTL Interface**: Complete Persian language support with Vazirmatn font
- **Smart Email Generation**: AI-powered personalized emails based on selected topics
- **Political Recipients Database**: Comprehensive database of political figures
- **Country-based Filtering**: Target specific countries and their representatives
- **Admin Panel**: Full administrative control with Persian interface

### 🛠️ Technical Features
- **FastAPI Backend**: High-performance async Python API
- **SQLAlchemy ORM**: Robust database operations with PostgreSQL/SQLite support
- **JWT Authentication**: Secure admin authentication
- **Rate Limiting**: Protection against abuse
- **CORS Support**: Frontend-backend connectivity
- **Data Seeding**: Automatic database population with sample data
- **Comprehensive Testing**: Full test suite for all functionality

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Modern web browser
- (Optional) PostgreSQL for production

### 1. Start the Backend Server
```bash
# Make startup script executable
chmod +x start.sh

# Start the full platform
./start.sh
```

This will:
- Install Python dependencies
- Initialize and seed the database
- Start the backend server on http://localhost:8000

### 2. Open the Frontend
- Open `frontend/index.html` in your browser
- Or serve with a local web server for better CORS support

### 3. Admin Access
- Admin Panel: `frontend/admin.html`
- Username: `admin@actforiran.org`
- Password: `admin123`

## 📁 Project Structure

```
actforiran/
├── README.md                 # Project documentation
├── start.sh                 # Quick start script
├── test_system.py           # Database and API testing
├── backend/                 # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── database.py         # Database config and seeding
│   ├── models.py           # SQLAlchemy models
│   ├── schemas.py          # Pydantic schemas
│   ├── limiter.py          # Rate limiting
│   ├── requirements.txt    # Python dependencies
│   ├── data/               # Static data
│   │   ├── countries.py    # Country definitions
│   │   └── roles.py        # Political roles
│   ├── routes/             # API endpoints
│   │   ├── admin.py        # Admin routes
│   │   ├── public.py       # Public API routes
│   │   └── test.py         # Testing endpoints
│   └── services/           # Business logic
│       ├── ai_service.py   # Email generation service
│       └── auth.py         # Authentication service
└── frontend/               # Modern Persian interface
    ├── index.html          # Main stepper form
    ├── admin.html          # Administrative panel
    ├── css/
    │   └── style.css       # Persian RTL styling
    └── js/
        ├── app.js          # Main application logic
        └── admin.js        # Admin panel logic
```

## 🎨 Design System

### Color Palette
- **Primary**: Deep red (#DC2626) - Iranian flag inspired
- **Background**: Rich black (#0F0F0F) - News station aesthetic
- **Surfaces**: Dark gray (#1A1A1A) - Modern contrast
- **Text**: Pure white (#FFFFFF) - Maximum readability
- **Accent**: Bright red (#EF4444) - Interactive elements

### Typography
- **Font**: Vazirmatn - Modern Persian typeface
- **Direction**: RTL (Right-to-Left) support
- **Weights**: 300, 400, 600, 700

## 🛠️ Development

### Backend Development
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Database Management
```bash
# Test database and seeding
python test_system.py

# Initialize database manually
python -c "from database import init_db; init_db()"
```

### Environment Variables
```bash
export ENVIRONMENT=development
export DATABASE_URL=sqlite:///./actforiran.db
export JWT_SECRET=your-jwt-secret
export OPENAI_API_KEY=your-openai-key
export OPENAI_MODEL=gpt-4o-mini
export FRONTEND_URL=http://localhost:3000
```

## 📊 API Endpoints

### Public API (`/api/v1/`)
- `GET /countries` - List all active countries
- `GET /recipients` - List political recipients (filterable by country)
- `GET /topics` - List advocacy topics
- `POST /generate-email` - Generate personalized email content

### Admin API (`/api/v1/admin/`)
- `POST /auth/login` - Admin authentication
- `GET /auth/me` - Get current admin info
- `GET /recipients` - Manage recipients
- `POST /recipients` - Add new recipient
- `PUT /recipients/{id}` - Update recipient
- `DELETE /recipients/{id}` - Delete recipient
- `GET /topics` - Manage topics
- `POST /topics` - Add new topic
- `PUT /topics/{id}` - Update topic

### Testing API (`/api/test/`)
- `GET /connectivity` - Test database connectivity
- `GET /sample-data` - Verify sample data
- `GET /admin-auth` - Test admin authentication

## 🗄️ Database Schema

### Core Models
- **Administrator**: Admin users with roles (admin, super_admin)
- **Country**: Country definitions with ISO codes
- **RecipientRole**: Political roles (Prime Minister, President, etc.)
- **PoliticalRecipient**: Individual political figures
- **AdvocacyTopic**: Campaign topics (Human Rights, Women's Rights, etc.)
- **EmailGenerationLog**: Usage tracking and analytics

### Sample Data Included
- 🌍 **15 Countries**: USA, UK, Canada, Germany, France, Australia, etc.
- 👥 **25+ Recipients**: Presidents, Prime Ministers, Foreign Ministers
- 📝 **8 Topics**: Human Rights, Women's Rights, Freedom of Expression, etc.
- 🔐 **Admin User**: admin@actforiran.org / admin123

## 🧪 Testing

### Run All Tests
```bash
# Test database and core functionality
python test_system.py

# Test API endpoints (requires running server)
python test_system.py --api-only
```

### Manual Testing Workflow
1. Start backend: `./start.sh`
2. Open `frontend/index.html`
3. Test 5-step form workflow:
   - Step 1: Select country
   - Step 2: Choose recipients
   - Step 3: Specify residency status
   - Step 4: Select advocacy topics
   - Step 5: Generate and review email
4. Test admin panel at `frontend/admin.html`

## 🌐 Deployment

### Production Configuration
```bash
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@host:port/db
export JWT_SECRET=your-secure-jwt-secret
export OPENAI_API_KEY=your-openai-key
export FRONTEND_URL=https://your-domain.com
```

### Recommended Deployment
- **Backend**: Railway, Heroku, or DigitalOcean App Platform
- **Frontend**: Cloudflare Pages, Netlify, or Vercel
- **Database**: PostgreSQL on Railway, Supabase, or AWS RDS

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting on API endpoints
- Input validation and sanitization
- CORS configuration for production

## 📄 License

This project is developed for advocacy purposes supporting human rights in Iran.

## 🆘 Support

If you encounter issues:

1. Check the console for error messages
2. Verify backend server is running on port 8000
3. Ensure all dependencies are installed
4. Run the test script: `python test_system.py`

### Common Issues
- **CORS Errors**: Make sure backend is running and FRONTEND_URL is correct
- **Database Issues**: Run `python test_system.py` to verify seeding
- **API Errors**: Check backend logs for detailed error messages

## 🎯 Next Steps

1. **AI Integration**: Add OpenAI API key for email generation
2. **Email Analytics**: Track email open/click rates
3. **Multi-language**: Support for more languages
4. **Mobile App**: React Native or Flutter implementation
5. **Social Sharing**: Share campaigns on social media

---

**🇮🇷 Made with ❤️ for Iranian human rights advocacy**
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
