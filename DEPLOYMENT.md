# PayrollHQ Railway Deployment Guide

## 🚀 Quick Deploy to Railway

### Prerequisites
1. GitHub account with this repository
2. Railway account (https://railway.app)
3. Basic understanding of environment variables

### Backend Deployment Steps

1. **Connect Repository to Railway**
   - Go to Railway dashboard
   - Click "New Project"  
   - Select "Deploy from GitHub repo"
   - Choose `capollo254/payrolhq` repository

2. **Configure Environment Variables**
   Add these in Railway dashboard under Variables:
   ```
   DJANGO_SECRET_KEY=your-very-long-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=your-backend-url.railway.app
   ```

3. **Database Setup**
   - Railway will automatically provide PostgreSQL
   - DATABASE_URL will be set automatically
   - No manual database configuration needed

4. **Deploy**
   - Railway will automatically detect Django project (manage.py in root)
   - Uses Python 3.11 (specified in runtime.txt)
   - Uses `Procfile` for deployment commands
   - Runs migrations and collects static files automatically

### Frontend Deployment (Optional Separate Service)

1. **Create New Railway Service**
   - In same project, add new service
   - Select same GitHub repo
   - Set root directory to `payrollhq-frontend`

2. **Configure Build Settings**
   ```
   Build Command: npm install && npm run build
   Start Command: npx serve -s build -l $PORT
   ```

3. **Environment Variables**
   ```
   REACT_APP_API_URL=https://your-backend-url.railway.app/api
   ```

### Alternative: Serve Frontend from Django

The Django backend can serve the React frontend in production:

1. **Build Frontend Locally**
   ```bash
   cd payrollhq-frontend
   npm run build
   ```

2. **Copy Build to Django Static**
   ```bash
   cp -r build/* ../payrollhq/static/
   ```

3. **Configure Django URLs**
   Add catch-all route in main urls.py:
   ```python
   from django.views.generic import TemplateView
   
   urlpatterns = [
       # ... existing patterns
       path('', TemplateView.as_view(template_name='index.html')),
   ]
   ```

## 🔧 Environment Variables Reference

### Required Variables
- `DJANGO_SECRET_KEY`: Django secret key (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `DEBUG`: Set to `False` for production
- `ALLOWED_HOSTS`: Your Railway app domain

### Optional Variables
- `CORS_ALLOWED_ORIGINS`: Frontend domain for CORS
- `EMAIL_*`: Email configuration for notifications
- `SENTRY_DSN`: Error tracking with Sentry

## 📋 Post-Deployment Steps

1. **Create Superuser**
   ```bash
   railway run python manage.py createsuperuser
   ```

2. **Load Sample Data** (Optional)
   ```bash
   railway run python manage.py shell -c "
   from master_data.sample_data import create_sample_compliance_data
   create_sample_compliance_data()
   "
   ```

3. **Test API Endpoints**
   - Visit `https://your-app.railway.app/admin/` for Django admin
   - Test `https://your-app.railway.app/api/master-data/compliance-settings/`

## 🐛 Troubleshooting

### Common Issues

1. **Build Fails - Python Dependencies**
   - Check `requirements.txt` is in correct location
   - Ensure all required packages are listed

2. **Database Connection Issues**
   - Railway provides DATABASE_URL automatically
   - Check if migrations ran successfully in logs

3. **Static Files Not Loading**
   - Ensure `collectstatic` runs in build process
   - Check `STATIC_URL` and `STATIC_ROOT` settings

4. **CORS Errors**
   - Add frontend domain to `CORS_ALLOWED_ORIGINS`
   - Check `django-cors-headers` is installed

### Checking Logs
```bash
railway logs
```

### Running Commands
```bash
railway run python manage.py shell
railway run python manage.py migrate
```

## 🔐 Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `DJANGO_SECRET_KEY`
- [ ] Proper `ALLOWED_HOSTS` configuration
- [ ] CORS settings configured correctly
- [ ] Database credentials secure (handled by Railway)
- [ ] Sensitive data in environment variables only

## 📊 Monitoring

### Built-in Django Admin
- Access admin panel at `/admin/`
- Monitor user activity, payroll batches, compliance settings

### Railway Dashboard
- View deployment logs
- Monitor resource usage
- Check environment variables

### Health Check
- Endpoint: `/admin/` (configured in railway.json)
- Railway will monitor application health

## 🔄 Continuous Deployment

Railway automatically deploys when you push to the main branch:

1. **Make Changes**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin master
   ```

2. **Railway Auto-Deploys**
   - Watches for GitHub pushes
   - Automatically builds and deploys
   - Zero-downtime deployments

## 📞 Support

If you encounter issues:
1. Check Railway logs first
2. Review this deployment guide
3. Check Django/React documentation
4. Create issue in GitHub repository

---

**Happy Deploying! 🚀**