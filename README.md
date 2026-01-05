# Daily Report System (Flask + SQLite)

Professional daily report web application built with Flask, SQLite, and Bootstrap 5.

## Features:
- ✅ **Modern UI/UX** - Bootstrap 5 with professional design, icons, and animations
- ✅ **User Authentication** - Secure registration and login system
- ✅ **Dashboard** - Statistics cards showing report counts by category with real-time updates
- ✅ **Report Management** - Create, view, and track daily reports with dynamic categories
- ✅ **Admin-Configurable Categories** - Admin can create, edit, activate/deactivate categories with custom colors
- ✅ **Advanced Monitoring** - Comprehensive analytics with Chart.js (pie, bar, timeline charts)
  - **Enhanced Summary Dashboard** - Modern gradient cards with interactive hover effects
  - **Multi-Filter System** - Filter by date range (start/end date) and item name
  - Real-time data visualization across all users
  - Summary charts for all users
  - Per-user analytics with filtering
  - **Favorite/Bookmark Users** - Mark users as favorites for quick access (always on top)
- ✅ **Item Library System** - Centralized management of items with Excel import/export
  - Upload items via Excel (.xlsx)
  - Manual add/edit/delete operations
  - Auto-save new items from report forms
  - Autocomplete suggestions when creating reports
- ✅ **Team Chat** - Real-time messaging with Server-Sent Events (SSE)
  - Direct messages and group chat
  - File and image attachments
  - Recent chats with remove functionality
  - Message retraction (within 1 hour of sending)
  - Unread message badges
  - Collapsible sections for better organization
- ✅ **User Profile** - Customizable settings (name, department, section, job, shift)
- ✅ **Responsive Design** - Works on desktop, tablet, and mobile
- ✅ **Timezone Support** - GMT+7 display throughout the application
- ✅ **Demo Data** - Pre-loaded dummy users and sample reports

## Installation:

1. **Clone the repository:**
```bash
git clone <your-repository-url>
cd <repository-folder>
```

2. **Create and activate virtual environment:**

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and set your SECRET_KEY
# For production, use a strong random key
```

5. **Initialize the database:**
```bash
python init_db.py
```

6. **Run the application:**
```bash
python app.py
```

Then open http://127.0.0.1:8000 in your browser.

## Demo Accounts:

Login credentials created by `init_db.py`:
- **Admin:** admin@example.com / password
- **User:** user1@example.com / password

## UI/UX Features:

- 📊 **Statistics Dashboard** - Visual cards showing report counts
- 🎨 **Professional Design** - Bootstrap 5 with custom styling
- 🔔 **Smart Alerts** - Color-coded notifications
- 📱 **Responsive Layout** - Mobile-friendly design
- ⚡ **Smooth Animations** - Hover effects and transitions
- 🎯 **Icon System** - Bootstrap Icons throughout

## Technology Stack:

- **Backend:** Flask (Python)
- **Database:** SQLAlchemy + SQLite
- **Frontend:** Bootstrap 5, Chart.js
- **Authentication:** Flask-Login
- **Real-time:** Server-Sent Events (SSE)

## Project Structure:

```
trial 2 php/
├── app.py              # Main Flask application
├── models.py           # Database models
├── forms.py            # WTForms definitions
├── requirements.txt    # Python dependencies
├── init_db.py          # Database initialization script
├── templates/          # HTML templates
├── static/             # CSS, JS, and uploaded files
└── instance/           # Database files (not in git)
```

## Security Notes:

⚠️ **Important for Production:**
- Change `SECRET_KEY` in your `.env` file to a strong random value
- Use a production-grade database (PostgreSQL, MySQL) instead of SQLite
- Enable HTTPS
- Set `FLASK_ENV=production` in `.env`
- Review and configure CORS settings if needed
- Implement rate limiting for API endpoints

## Contributing:

Contributions are welcome! Please feel free to submit a Pull Request.

## License:

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support:

If you encounter any issues or have questions, please open an issue on GitHub.
