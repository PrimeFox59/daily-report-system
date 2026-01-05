⚠️ **DEPLOYMENT WARNING** ⚠️

This application has been configured for Vercel deployment, but **WILL NOT WORK PROPERLY** on Vercel due to:

## Critical Issues:

### 1. ❌ SQLite Database
- Vercel uses **stateless serverless functions**
- Database will be **RESET on every deployment**
- All data will be **LOST**
- Solution: Use PostgreSQL (Supabase, Neon, PlanetScale)

### 2. ❌ File Uploads (`static/uploads/`)
- Vercel filesystem is **READ-ONLY** except `/tmp`
- Uploaded files will **DISAPPEAR**
- Solution: Use cloud storage (Cloudinary, AWS S3)

### 3. ❌ Server-Sent Events (Chat Feature)
- Vercel has **10-second timeout** (hobby plan)
- SSE connections need persistent connections
- Chat will **NOT WORK**
- Solution: Use WebSocket service or polling

### 4. ❌ Database Initialization
- `db.create_all()` runs on every request
- Will cause **performance issues**
- Solution: Use migrations or external database

## Recommended Platforms:

### ✅ Railway (BEST CHOICE)
- SQLite works out of the box
- Persistent storage included
- No code changes needed
- Free tier available

### ✅ Render
- Free PostgreSQL database
- Persistent disk available
- Easy deployment

### ✅ PythonAnywhere
- Python-focused platform
- SQLite supported
- Easy for beginners

## Files Created:

- [vercel.json](vercel.json) - Vercel configuration
- [app.py](app.py) - Modified to export `app` object
- Port 8000 removed from Vercel (only for local dev)

## Local Development:

Still works as before:
```bash
python app.py  # Runs on port 8000
```

## If You Proceed with Vercel:

Expect:
- Database resets on every deploy
- Lost uploaded files
- Broken chat feature
- Slow performance

**Consider Railway/Render instead for a better experience!**
