# Deployment Guide

## GitHub Pages / Static Hosting

Since this is a Flask application, you'll need a platform that supports Python backend hosting.

### Recommended Platforms:

1. **Heroku** (Easy deployment)
2. **Railway** (Modern alternative to Heroku)
3. **Render** (Free tier available)
4. **PythonAnywhere** (Python-focused hosting)

### Environment Variables for Production:

Set these in your hosting platform's environment variables section:

- `REPLICATE_API_TOKEN`: Your Replicate API key
- `FLASK_ENV`: Set to `production` for production deployment
- `PORT`: Usually set automatically by the hosting platform

### Heroku Deployment (Example):

1. Create a Heroku app:
   ```bash
   heroku create your-app-name
   ```

2. Set environment variables:
   ```bash
   heroku config:set REPLICATE_API_TOKEN=your_api_key_here
   heroku config:set FLASK_ENV=production
   ```

3. Deploy:
   ```bash
   git push heroku main
   ```

### Security Notes:

- Never commit your `.env` file to git
- The `.gitignore` file is already configured to exclude sensitive files
- Always use environment variables for API keys in production

### Local Development:

```bash
# Set development environment
export FLASK_ENV=development

# Run locally
./run.py
```
