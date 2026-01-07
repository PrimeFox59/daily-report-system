from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, RegisterForm, ReportForm, SettingsForm, AdminEditUserForm
from models import db, User, Report, ReportTemplate, Category, AuditLog, ItemLibrary
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import time
import json
from sqlalchemy import text
import openpyxl


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-for-production')
    
    # Check if DATABASE_URL is set (for Neon PostgreSQL)
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Use PostgreSQL from environment variable (Neon)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Detect if running on Vercel (serverless) - use /tmp for writable storage
        is_vercel = os.getenv('VERCEL') or os.getenv('VERCEL_ENV')
        
        if is_vercel:
            # Vercel: use /tmp (temporary, will reset on cold start)
            db_path = '/tmp/app.db'
        else:
            # Local: use instance folder
            db_path = 'sqlite:///app.db'
        
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}' if is_vercel else db_path
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 20,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 30
    }

    db.init_app(app)
    
    # Initialize database tables and create default data
    try:
        with app.app_context():
            db.create_all()
            
            # Auto-create default users if database is empty (important for Vercel /tmp)
            if User.query.count() == 0:
                app.logger.info("Empty database detected, creating default users...")
                
                # Create default categories
                default_categories = [
                    Category(name='Produksi', color='primary', icon='bi-gear-fill', is_active=True),
                    Category(name='Quality Check', color='success', icon='bi-check-circle-fill', is_active=True),
                    Category(name='Maintenance', color='warning', icon='bi-tools', is_active=True),
                    Category(name='Meeting', color='info', icon='bi-people-fill', is_active=True),
                    Category(name='Training', color='secondary', icon='bi-book-fill', is_active=True),
                    Category(name='Problem', color='danger', icon='bi-exclamation-triangle-fill', is_active=True),
                ]
                for cat in default_categories:
                    db.session.add(cat)
                
                # Create admin user
                admin = User(
                    name='Administrator',
                    employee_id='admin',
                    department='IT',
                    section='System',
                    job='Admin',
                    shift='Day',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                
                # Create demo users
                demo_users = [
                    {'name': 'John Doe', 'id': '344', 'dept': 'Production', 'section': 'Assembly', 'job': 'Operator', 'shift': 'Morning'},
                    {'name': 'Jane Smith', 'id': '368', 'dept': 'Quality', 'section': 'QC', 'job': 'Inspector', 'shift': 'Afternoon'},
                ]
                for u in demo_users:
                    user = User(
                        name=u['name'],
                        employee_id=u['id'],
                        department=u['dept'],
                        section=u['section'],
                        job=u['job'],
                        shift=u['shift']
                    )
                    user.set_password('zzz')
                    db.session.add(user)
                
                db.session.commit()
                app.logger.info("Default users and categories created successfully!")
    except Exception as e:
        app.logger.error(f"Database initialization error: {e}")
        # Continue anyway - will fail on first database access but at least app loads

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    def log_action(user_id, action, detail='', actor_id=None):
        """Persist audit log without blocking main flow."""
        try:
            entry = AuditLog(
                user_id=user_id,
                actor_id=actor_id if actor_id is not None else user_id,
                action=action,
                detail=detail
            )
            db.session.add(entry)
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            app.logger.error(f"Failed to log action {action}: {exc}")

    # Jinja2 filter for GMT+7 timezone conversion
    @app.template_filter('gmt7')
    def gmt7_filter(utc_datetime):
        if utc_datetime:
            return utc_datetime + timedelta(hours=7)
        return utc_datetime
    
    # Jinja2 filter for strftime
    @app.template_filter('strftime')
    def strftime_filter(date, fmt):
        if date:
            return date.strftime(fmt)
        return ''

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegisterForm()
        if form.validate_on_submit():
            if User.query.filter_by(employee_id=form.employee_id.data).first():
                flash('ID already registered', 'warning')
                return redirect(url_for('register'))
            user = User(
                name=form.name.data,
                employee_id=form.employee_id.data,
                department=form.department.data,
                section=form.section.data,
                job=form.job.data,
                shift=form.shift.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please login.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(employee_id=form.employee_id.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                log_action(user.id, 'login', detail=f"IP {request.remote_addr or '-'}")
                flash('Logged in successfully.', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            flash('Invalid credentials', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get all reports (no date filter - frontend will handle filtering by selected date)
        reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.time.desc()).all()
        
        templates = ReportTemplate.query.filter_by(user_id=current_user.id).order_by(ReportTemplate.created_at.desc()).all()
        categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
        category_colors = {c.name: c.color for c in categories}
        form = ReportForm()  # Create form for CSRF token
        
        # Get last report for auto-filling optional details
        last_report = reports[0] if reports else None
        
        # Calculate category counts
        category_counts = {}
        for category in categories:
            count = Report.query.filter_by(user_id=current_user.id, category=category.name).count()
            category_counts[category.name] = count
        
        # Convert reports to JSON-serializable format for calendar (with GMT+7)
        reports_json = [{
            'id': r.id,
            'created_at': (r.created_at + timedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S'),
            'category': r.category,
            'title': r.title
        } for r in reports]
        
        return render_template(
            'dashboard.html',
            reports=reports,
            templates=templates,
            categories=categories,
            category_counts=category_counts,
            category_colors=category_colors,
            form=form,
            now=datetime.utcnow(),
            last_report=last_report,
            reports_json=reports_json,
        )

    @app.route('/report/new', methods=['GET', 'POST'])
    @login_required
    def new_report():
        if request.method == 'POST':
            # Handle AJAX submission
            try:
                time = request.form.get('time')
                category = request.form.get('category')
                title = request.form.get('title')
                notes = request.form.get('notes', '')
                item_name = request.form.get('item_name', '').strip() or None
                part_number = request.form.get('part_number', '').strip() or None
                customer = request.form.get('customer', '').strip() or None
                
                if not time or not category or not title:
                    return {'success': False, 'message': 'Time, category, and title are required'}, 400
                
                # Auto-save to ItemLibrary if item_name is provided
                # Check for unique combination of item_name + part_number + customer
                if item_name:
                    existing_item = ItemLibrary.query.filter_by(
                        item_name=item_name,
                        part_number=part_number,
                        customer=customer
                    ).first()
                    
                    if not existing_item:
                        new_item = ItemLibrary(
                            item_name=item_name,
                            part_number=part_number,
                            customer=customer
                        )
                        db.session.add(new_item)
                        # Commit immediately to make it available for next autocomplete
                        db.session.flush()
                
                r = Report(
                    user_id=current_user.id,
                    time=time,
                    category=category,
                    title=title,
                    notes=notes,
                    item_name=item_name,
                    part_number=part_number,
                    customer=customer,
                )
                db.session.add(r)
                db.session.commit()
                log_action(current_user.id, 'report_created', detail=f"Report #{r.id}: {title}")
                
                # Get category color
                cat = Category.query.filter_by(name=category).first()
                category_color = cat.color if cat else 'secondary'
                
                return {
                    'success': True,
                    'message': 'Report saved successfully',
                    'report_id': r.id,
                    'time': time,
                    'category': category,
                    'category_color': category_color,
                    'title': title,
                    'notes': notes,
                    'item_name': item_name or '',
                    'part_number': part_number or '',
                    'customer': customer or ''
                }
            except Exception as e:
                db.session.rollback()
                return {'success': False, 'message': str(e)}, 500

    @app.route('/report/edit/<int:report_id>', methods=['GET', 'POST'])
    @login_required
    def edit_report(report_id):
        from datetime import datetime, timedelta
        report = Report.query.get_or_404(report_id)
        
        # Check ownership
        if report.user_id != current_user.id:
            if request.is_json:
                return {'success': False, 'message': 'Unauthorized'}, 403
            flash('Unauthorized access', 'danger')
            return redirect(url_for('dashboard'))
        
        # Check if report is within 2 days
        days_old = (datetime.utcnow() - report.created_at).days
        if days_old >= 2:
            if request.is_json:
                return {'success': False, 'message': 'Report older than 2 days cannot be edited'}, 403
            flash('Report older than 2 days cannot be edited', 'warning')
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            if request.is_json or 'application/json' in request.accept_mimetypes:
                try:
                    report.time = request.form.get('time', report.time)
                    report.category = request.form.get('category', report.category)
                    report.title = request.form.get('title', report.title)
                    report.notes = request.form.get('notes', report.notes)
                    report.item_name = request.form.get('item_name') or None
                    report.part_number = request.form.get('part_number') or None
                    report.customer = request.form.get('customer') or None
                    db.session.commit()
                    log_action(report.user_id, 'report_edited', detail=f"Report #{report.id}", actor_id=current_user.id)
                    return {'success': True, 'message': 'Report updated successfully'}
                except Exception as e:
                    return {'success': False, 'message': str(e)}, 500
        
        return {'success': False, 'message': 'Invalid request'}, 400

    @app.route('/api/report/<int:report_id>')
    @login_required
    def get_report_detail(report_id):
        """Get detailed information about a specific report."""
        report = Report.query.get_or_404(report_id)
        
        # Calculate if report is editable (within 2 days and owned by current user)
        from datetime import datetime
        days_old = (datetime.utcnow() - report.created_at).days
        is_editable = (days_old < 2 and report.user_id == current_user.id)
        
        return jsonify({
            'success': True,
            'report': {
                'id': report.id,
                'time': report.time,
                'category': report.category,
                'title': report.title,
                'notes': report.notes,
                'item_name': report.item_name,
                'part_number': report.part_number,
                'customer': report.customer,
                'user_name': report.user.name,
                'user_employee_id': report.user.employee_id,
                'created_at': report.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_editable': is_editable
            }
        })

    @app.route('/api/items/search')
    @login_required
    def search_items():
        """Return item suggestions from ItemLibrary with part/customer for auto-fill."""
        query = request.args.get('q', '').strip()
        if not query:
            # Return all items if no query (for dropdown)
            items = ItemLibrary.query.order_by(ItemLibrary.item_name).limit(50).all()
            return jsonify([{
                'item_name': item.item_name,
                'part_number': item.part_number or '',
                'customer': item.customer or '',
                'display': f"{item.item_name} | {item.part_number or 'No Part#'} | {item.customer or 'No Customer'}"
            } for item in items])

        # Search items matching the query (from ItemLibrary table)
        # Return ALL combinations even if item_name is the same
        items = ItemLibrary.query.filter(
            ItemLibrary.item_name.ilike(f"%{query}%")
        ).order_by(ItemLibrary.item_name, ItemLibrary.part_number, ItemLibrary.customer).limit(50).all()

        suggestions = [{
            'item_name': item.item_name,
            'part_number': item.part_number or '',
            'customer': item.customer or '',
            'display': f"{item.item_name} | {item.part_number or 'No Part#'} | {item.customer or 'No Customer'}"
        } for item in items]
        
        return jsonify(suggestions)
    
    @app.route('/report/delete/<int:report_id>', methods=['POST', 'DELETE'])
    @login_required
    def delete_report(report_id):
        from datetime import datetime, timedelta
        report = Report.query.get_or_404(report_id)
        
        # Check ownership
        if report.user_id != current_user.id:
            return {'success': False, 'message': 'Unauthorized'}, 403
        
        # Check if report is within 2 days
        days_old = (datetime.utcnow() - report.created_at).days
        if days_old >= 2:
            return {'success': False, 'message': 'Report older than 2 days cannot be deleted'}, 403
        
        try:
            category = report.category
            db.session.delete(report)
            db.session.commit()
            log_action(report.user_id, 'report_deleted', detail=f"Report #{report.id}", actor_id=current_user.id)
            return {'success': True, 'message': 'Report deleted successfully', 'category': category}
        except Exception as e:
            return {'success': False, 'message': str(e)}, 500

    @app.route('/monitoring')
    @app.route('/monitoring/<int:user_id>')
    @login_required
    def monitoring(user_id=None):
        # Check if user is admin
        if not current_user.is_admin:
            flash('Access denied. Admin only.', 'danger')
            return redirect(url_for('dashboard'))
        
        from datetime import datetime, timedelta
        from sqlalchemy import func
        from collections import defaultdict
        
        # Get all users (including admin), favorites first, then by name
        all_users = User.query.order_by(User.is_favorite.desc(), User.name).all()
        
        # Get all active categories
        categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
        
        # Get all items worked on (for filter)
        all_items = db.session.query(Report.item_name).filter(
            Report.item_name.isnot(None),
            Report.item_name != ''
        ).distinct().order_by(Report.item_name).all()
        all_items_list = [item[0] for item in all_items]
        
        selected_user = None
        user_stats = None
        
        # If specific user is selected
        if user_id:
            selected_user = User.query.get_or_404(user_id)
            
            # Get filter parameter
            item_filter = request.args.get('item')
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            now_gmt7 = datetime.utcnow() + timedelta(hours=7)
            end_date_local = now_gmt7.date()
            if end_date_str:
                try:
                    end_date_local = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            start_date_local = end_date_local - timedelta(days=29)
            if start_date_str:
                try:
                    start_date_local = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
            if start_date_local > end_date_local:
                start_date_local = end_date_local
            start_utc = datetime.combine(start_date_local, datetime.min.time()) - timedelta(hours=7)
            end_utc = datetime.combine(end_date_local + timedelta(days=1), datetime.min.time()) - timedelta(hours=7)
            
            # Base query
            query = Report.query.filter_by(user_id=selected_user.id)
            if item_filter:
                query = query.filter_by(item_name=item_filter)
            query = query.filter(Report.created_at >= start_utc, Report.created_at < end_utc)
            
            # Get total reports
            total_reports = query.count()
            
            # Get category counts (dynamic)
            category_counts = {}
            category_pcts = {}
            for category in categories:
                count = query.filter_by(category=category.name).count()
                category_counts[category.name] = count
                category_pcts[category.name] = round((count / total_reports * 100) if total_reports > 0 else 0, 1)
            
            # Get timeline data (last 30 days) - using GMT+7
            timeline_reports = query.all()
            
            # Group by date and category (convert to GMT+7)
            timeline_data = defaultdict(lambda: defaultdict(int))
            for report in timeline_reports:
                gmt7_date = (report.created_at + timedelta(hours=7)).strftime('%Y-%m-%d')
                timeline_data[gmt7_date][report.category] += 1
            
            # Prepare timeline arrays for chart
            timeline_dates = []
            timeline_series = {cat.name: [] for cat in categories}
            
            current_date = start_date_local
            while current_date <= end_date_local:
                date_str = current_date.strftime('%Y-%m-%d')
                timeline_dates.append(date_str)
                for category in categories:
                    timeline_series[category.name].append(timeline_data[date_str].get(category.name, 0))
                current_date += timedelta(days=1)
            
            # Get recent items worked on
            recent_items = db.session.query(Report.item_name).filter(
                Report.user_id == selected_user.id,
                Report.item_name.isnot(None),
                Report.item_name != ''
            ).distinct().limit(10).all()

            # Item contribution counts (for donut chart)
            item_count_rows = db.session.query(Report.item_name, func.count(Report.id)).filter(
                Report.user_id == selected_user.id,
                Report.item_name.isnot(None),
                Report.item_name != ''
            ).group_by(Report.item_name).all()
            item_labels = [row[0] for row in item_count_rows]
            item_counts = [row[1] for row in item_count_rows]
            
            # Get all reports for detailed view
            all_reports = query.order_by(Report.created_at.desc()).all()
            
            user_stats = {
                'user': selected_user,
                'total_reports': total_reports,
                'category_counts': category_counts,
                'category_pcts': category_pcts,
                'recent_items': [item[0] for item in recent_items],
                'all_reports': all_reports,
                'timeline_dates': timeline_dates,
                'timeline_series': timeline_series,
                'item_labels': item_labels,
                'item_counts': item_counts,
                'date_range_label': f"{start_date_local.strftime('%d/%m/%y')} - {end_date_local.strftime('%d/%m/%y')}",
                'start_date_local': start_date_local.strftime('%Y-%m-%d'),
                'end_date_local': end_date_local.strftime('%Y-%m-%d')
            }
        

        # --- SUMMARY ALL USERS DATA ---
        # Get filter parameters for all users summary
        filter_item = request.args.get('filter_item')
        all_start_date_str = request.args.get('all_start_date')
        all_end_date_str = request.args.get('all_end_date')
        
        # Calculate date range for all users (default: last 30 days)
        now_gmt7 = datetime.utcnow() + timedelta(hours=7)
        all_end_date = now_gmt7.date()
        if all_end_date_str:
            try:
                all_end_date = datetime.strptime(all_end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        all_start_date = all_end_date - timedelta(days=29)
        if all_start_date_str:
            try:
                all_start_date = datetime.strptime(all_start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        if all_start_date > all_end_date:
            all_start_date = all_end_date
        
        # Convert to UTC for database query
        all_start_utc = datetime.combine(all_start_date, datetime.min.time()) - timedelta(hours=7)
        all_end_utc = datetime.combine(all_end_date + timedelta(days=1), datetime.min.time()) - timedelta(hours=7)
        
        # 1. Category distribution (all reports, optionally filtered by item and date range)
        all_users_category_counts = {cat.name: 0 for cat in categories}
        for user in all_users:
            for report in user.reports:
                # Apply date range filter
                if not (all_start_utc <= report.created_at < all_end_utc):
                    continue
                # Apply item filter if specified
                if filter_item and report.item_name != filter_item:
                    continue
                if report.category in all_users_category_counts:
                    all_users_category_counts[report.category] += 1

        # 2. Report count per user (for bar chart, optionally filtered by item and date range)
        all_users_report_counts = []
        for user in all_users:
            count = 0
            for r in user.reports:
                # Apply date range filter
                if not (all_start_utc <= r.created_at < all_end_utc):
                    continue
                # Apply item filter
                if filter_item and r.item_name != filter_item:
                    continue
                count += 1
            all_users_report_counts.append((user.name, count))

        # 3. Item name distribution (top items worked on, optionally filtered by date range)
        all_items_counts = defaultdict(int)
        for user in all_users:
            for report in user.reports:
                # Apply date range filter
                if not (all_start_utc <= report.created_at < all_end_utc):
                    continue
                if not report.item_name or not report.item_name.strip():
                    continue
                if filter_item and report.item_name != filter_item:
                    continue
                all_items_counts[report.item_name] += 1
        
        # Get top 10 items sorted by count
        if all_items_counts:
            top_items = sorted(all_items_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            all_users_item_names = [item[0] for item in top_items]
            all_users_item_counts = [item[1] for item in top_items]
        else:
            all_users_item_names = []
            all_users_item_counts = []

        # 4. Timeline stacked chart (all users, filtered by date range and item)
        all_timeline_dates = []
        all_timeline_series = {cat.name: [] for cat in categories}
        all_timeline_data = defaultdict(lambda: defaultdict(int))
        
        for user in all_users:
            for report in user.reports:
                # Apply date range filter
                if not (all_start_utc <= report.created_at < all_end_utc):
                    continue
                # Apply item filter if specified
                if filter_item and report.item_name != filter_item:
                    continue
                gmt7_date = (report.created_at + timedelta(hours=7)).strftime('%Y-%m-%d')
                all_timeline_data[gmt7_date][report.category] += 1
        
        current_date_all = all_start_date
        while current_date_all <= all_end_date:
            date_str = current_date_all.strftime('%Y-%m-%d')
            all_timeline_dates.append(date_str)
            for category in categories:
                all_timeline_series[category.name].append(all_timeline_data[date_str].get(category.name, 0))
            current_date_all += timedelta(days=1)

        total_users = len(all_users)
        total_reports_all = Report.query.count()

        return render_template('monitoring.html',
            all_users=all_users,
            selected_user=selected_user,
            user_stats=user_stats,
            categories=categories,
            all_items=all_items_list,
            total_users=total_users,
            total_reports_all=total_reports_all,
            all_users_category_counts=all_users_category_counts,
            all_users_report_counts=all_users_report_counts,
            all_users_item_names=all_users_item_names,
            all_users_item_counts=all_users_item_counts,
            all_users_timeline_dates=all_timeline_dates,
            all_users_timeline_series=all_timeline_series,
            all_start_date=all_start_date.strftime('%Y-%m-%d'),
            all_end_date=all_end_date.strftime('%Y-%m-%d')
        )

    @app.route('/audit-log')
    @login_required
    def audit_log():
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        filter_user_id = request.args.get('user_id', type=int)

        now_gmt7 = datetime.utcnow() + timedelta(hours=7)
        end_date_local = now_gmt7.date()
        if end_date_str:
            try:
                end_date_local = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        start_date_local = end_date_local - timedelta(days=29)
        if start_date_str:
            try:
                start_date_local = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        if start_date_local > end_date_local:
            start_date_local = end_date_local

        start_utc = datetime.combine(start_date_local, datetime.min.time()) - timedelta(hours=7)
        end_utc = datetime.combine(end_date_local + timedelta(days=1), datetime.min.time()) - timedelta(hours=7)

        query = AuditLog.query.filter(AuditLog.created_at >= start_utc, AuditLog.created_at < end_utc)

        if current_user.is_admin:
            if filter_user_id:
                query = query.filter(AuditLog.user_id == filter_user_id)
            available_users = User.query.order_by(User.name).all()
        else:
            filter_user_id = current_user.id
            query = query.filter(AuditLog.user_id == current_user.id)
            available_users = [current_user]

        logs = query.order_by(AuditLog.created_at.desc()).all()
        date_range_label = f"{start_date_local.strftime('%d/%m/%y')} - {end_date_local.strftime('%d/%m/%y')}"

        return render_template(
            'audit_log.html',
            logs=logs,
            users=available_users,
            filter_user_id=filter_user_id,
            start_date=start_date_local.strftime('%Y-%m-%d'),
            end_date=end_date_local.strftime('%Y-%m-%d'),
            date_range_label=date_range_label,
            is_admin=current_user.is_admin
        )

    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        form = SettingsForm(obj=current_user)
        if form.validate_on_submit():
            # Update profile information
            current_user.name = form.name.data
            current_user.department = form.department.data
            current_user.section = form.section.data
            current_user.job = form.job.data
            current_user.shift = form.shift.data
            
            # Handle password change if provided
            if form.new_password.data:
                if not form.current_password.data:
                    flash('Please enter your current password to change password.', 'danger')
                    return render_template('settings.html', form=form)
                
                # Verify current password
                if not check_password_hash(current_user.password, form.current_password.data):
                    flash('Current password is incorrect.', 'danger')
                    return render_template('settings.html', form=form)
                
                # Update password
                current_user.password = generate_password_hash(form.new_password.data)
                flash('Password updated successfully!', 'success')
                log_action(current_user.id, 'password_changed', detail='User changed password')
            
            db.session.commit()
            log_action(current_user.id, 'profile_updated', detail='Updated profile settings')
            flash('Settings updated.', 'success')
            return redirect(url_for('settings'))
        return render_template('settings.html', form=form)

    @app.route('/admin/users')
    @login_required
    def admin_users():
        if not current_user.is_admin:
            flash('Access denied. Admin only.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Get search query
        search = request.args.get('search', '')
        
        # Query users
        if search:
            users = User.query.filter(
                (User.name.ilike(f'%{search}%')) |
                (User.employee_id.ilike(f'%{search}%')) |
                (User.department.ilike(f'%{search}%'))
            ).order_by(User.name).all()
        else:
            users = User.query.order_by(User.name).all()
        
        return render_template('admin_users.html', users=users, search=search)

    @app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @login_required
    def admin_edit_user(user_id):
        if not current_user.is_admin:
            flash('Access denied. Admin only.', 'danger')
            return redirect(url_for('dashboard'))
        
        user = User.query.get_or_404(user_id)
        form = AdminEditUserForm(obj=user)
        prev_is_admin = user.is_admin
        
        # Set the current is_admin value
        if request.method == 'GET':
            form.is_admin.data = '1' if user.is_admin else '0'
        
        if form.validate_on_submit():
            # Check if employee_id is being changed and if it already exists
            if form.employee_id.data != user.employee_id:
                existing = User.query.filter_by(employee_id=form.employee_id.data).first()
                if existing:
                    flash('Employee ID already exists!', 'danger')
                    return render_template('admin_edit_user.html', form=form, user=user)
            
            user.name = form.name.data
            user.employee_id = form.employee_id.data
            user.department = form.department.data
            user.section = form.section.data
            user.job = form.job.data
            user.shift = form.shift.data
            user.is_admin = (form.is_admin.data == '1')
            changed_password = False
            
            # Update password if provided
            if form.new_password.data:
                user.set_password(form.new_password.data)
                changed_password = True
            
            db.session.commit()
            changes = []
            if changed_password:
                changes.append('password')
            if prev_is_admin != user.is_admin:
                changes.append('role')
            change_label = ', '.join(changes) if changes else 'profile'
            log_action(user.id, 'user_updated', detail=f"Updated {change_label} for {user.name}", actor_id=current_user.id)
            flash(f'User {user.name} updated successfully!', 'success')
            return redirect(url_for('admin_users'))
        
        return render_template('admin_edit_user.html', form=form, user=user)

    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    def admin_delete_user(user_id):
        if not current_user.is_admin:
            return {'success': False, 'message': 'Access denied'}, 403
        
        user = User.query.get_or_404(user_id)
        
        # Prevent deleting yourself
        if user.id == current_user.id:
            return {'success': False, 'message': 'Cannot delete your own account!'}, 400
        
        try:
            # Delete all user's reports first
            Report.query.filter_by(user_id=user.id).delete()
            
            # Delete user
            username = user.name
            target_id = user.id
            db.session.delete(user)
            db.session.commit()
            log_action(None, 'user_deleted', detail=f"Deleted user {username} (ID {target_id})", actor_id=current_user.id)
            
            return {'success': True, 'message': f'User {username} deleted successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}, 500

    @app.route('/template/create', methods=['POST'])
    @login_required
    def create_template():
        try:
            name = request.form.get('name')
            category = request.form.get('category')
            title = request.form.get('title')
            notes = request.form.get('notes', '')
            item_name = request.form.get('item_name', '')
            part_number = request.form.get('part_number', '')
            customer = request.form.get('customer', '')
            color = request.form.get('color', 'yellow')
            
            if not name:
                return {'success': False, 'message': 'Template name is required'}, 400
            
            template = ReportTemplate(
                user_id=current_user.id,
                name=name,
                category=category,
                title=title,
                notes=notes,
                item_name=item_name,
                part_number=part_number,
                customer=customer,
                color=color
            )
            db.session.add(template)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Template created successfully',
                'template': {
                    'id': template.id,
                    'name': template.name,
                    'category': template.category,
                    'title': template.title,
                    'notes': template.notes,
                    'item_name': template.item_name,
                    'part_number': template.part_number,
                    'customer': template.customer,
                    'color': template.color
                }
            }
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}, 500

    @app.route('/template/<int:template_id>/delete', methods=['POST', 'DELETE'])
    @login_required
    def delete_template(template_id):
        template = ReportTemplate.query.get_or_404(template_id)
        
        # Check ownership
        if template.user_id != current_user.id:
            return {'success': False, 'message': 'Unauthorized'}, 403
        
        try:
            template_name = template.name
            db.session.delete(template)
            db.session.commit()
            return {'success': True, 'message': f'Template "{template_name}" deleted successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}, 500

    # Admin Category Management Routes
    @app.route('/admin/categories')
    @login_required
    def admin_categories():
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        
        categories = Category.query.order_by(Category.name).all()
        
        # Get all users for user management tab
        search = request.args.get('search', '').strip()
        if search:
            users = User.query.filter(
                (User.name.ilike(f'%{search}%')) |
                (User.employee_id.ilike(f'%{search}%')) |
                (User.department.ilike(f'%{search}%'))
            ).order_by(User.name).all()
        else:
            users = User.query.order_by(User.name).all()
        
        # Get all items for item library tab
        items = ItemLibrary.query.order_by(ItemLibrary.item_name).all()
        
        return render_template('admin_categories.html', categories=categories, users=users, items=items, search=search)

    @app.route('/admin/category/add', methods=['POST'])
    @login_required
    def add_category():
        if not current_user.is_admin:
            return {'success': False, 'message': 'Unauthorized'}, 403
        
        try:
            name = request.form.get('name')
            color = request.form.get('color', 'primary')
            icon = request.form.get('icon', 'bi-tag')
            
            if not name:
                return {'success': False, 'message': 'Category name is required'}
            
            # Check if category already exists
            existing = Category.query.filter_by(name=name).first()
            if existing:
                return {'success': False, 'message': 'Category already exists'}
            
            category = Category(name=name, color=color, icon=icon)
            db.session.add(category)
            db.session.commit()
            
            return {'success': True, 'message': 'Category added successfully', 
                   'category': {'id': category.id, 'name': category.name, 'color': category.color, 'icon': category.icon}}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}, 500

    @app.route('/admin/category/<int:category_id>/edit', methods=['POST'])
    @login_required
    def edit_category(category_id):
        if not current_user.is_admin:
            return {'success': False, 'message': 'Unauthorized'}, 403
        
        category = Category.query.get_or_404(category_id)
        
        try:
            name = request.form.get('name')
            color = request.form.get('color')
            icon = request.form.get('icon')
            
            if name:
                category.name = name
            if color:
                category.color = color
            if icon:
                category.icon = icon
            
            db.session.commit()
            return {'success': True, 'message': 'Category updated successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}, 500

    @app.route('/admin/category/<int:category_id>/delete', methods=['POST'])
    @login_required
    def delete_category(category_id):
        if not current_user.is_admin:
            return {'success': False, 'message': 'Unauthorized'}, 403
        
        category = Category.query.get_or_404(category_id)
        
        try:
            category_name = category.name
            db.session.delete(category)
            db.session.commit()
            return {'success': True, 'message': f'Category "{category_name}" deleted successfully'}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}, 500

    @app.route('/admin/category/<int:category_id>/toggle', methods=['POST'])
    @login_required
    def toggle_category(category_id):
        if not current_user.is_admin:
            return {'success': False, 'message': 'Unauthorized'}, 403
        
        category = Category.query.get_or_404(category_id)
        
        try:
            category.is_active = not category.is_active
            db.session.commit()
            return {'success': True, 'message': f'Category {"activated" if category.is_active else "deactivated"}', 'is_active': category.is_active}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': str(e)}, 500

    @app.route('/api/users/<int:user_id>/toggle-favorite', methods=['POST'])
    @login_required
    def toggle_favorite(user_id):
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        user = User.query.get_or_404(user_id)
        
        try:
            user.is_favorite = not user.is_favorite
            db.session.commit()
            return jsonify({
                'success': True, 
                'message': f'User {"added to" if user.is_favorite else "removed from"} favorites', 
                'is_favorite': user.is_favorite
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

    # ===== ITEM LIBRARY ROUTES =====
    
    @app.route('/admin/items/upload', methods=['POST'])
    @login_required
    def upload_items():
        """Upload items from Excel file"""
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file uploaded'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        if not file.filename.endswith('.xlsx'):
            return jsonify({'success': False, 'message': 'Only .xlsx files are allowed'})
        
        try:
            # Read Excel file
            workbook = openpyxl.load_workbook(file)
            sheet = workbook.active
            
            count = 0
            for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip header
                if not row[0]:  # Skip if item_name is empty
                    continue
                
                item_name = str(row[0]).strip()
                part_number = str(row[1]).strip() if len(row) > 1 and row[1] else None
                customer = str(row[2]).strip() if len(row) > 2 and row[2] else None
                
                # Check if exact combination already exists (item_name + part_number + customer)
                existing = ItemLibrary.query.filter_by(
                    item_name=item_name,
                    part_number=part_number,
                    customer=customer
                ).first()
                
                if not existing:
                    item = ItemLibrary(
                        item_name=item_name,
                        part_number=part_number,
                        customer=customer
                    )
                    db.session.add(item)
                    count += 1
            
            db.session.commit()
            return jsonify({'success': True, 'message': f'{count} items uploaded successfully', 'count': count})
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error reading Excel file: {str(e)}'})
    
    @app.route('/admin/items/add', methods=['POST'])
    @login_required
    def add_item():
        """Add item manually"""
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        try:
            item_name = request.form.get('item_name', '').strip()
            part_number = request.form.get('part_number', '').strip() or None
            customer = request.form.get('customer', '').strip() or None
            
            if not item_name:
                return jsonify({'success': False, 'message': 'Item name is required'})
            
            # Check if exact combination already exists (item_name + part_number + customer)
            existing = ItemLibrary.query.filter_by(
                item_name=item_name,
                part_number=part_number,
                customer=customer
            ).first()
            
            if existing:
                return jsonify({'success': False, 'message': 'This exact combination already exists in library'})
            
            item = ItemLibrary(
                item_name=item_name,
                part_number=part_number,
                customer=customer
            )
            db.session.add(item)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Item added successfully'})
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/admin/items/<int:item_id>/edit', methods=['POST'])
    @login_required
    def edit_item(item_id):
        """Edit item"""
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        try:
            item = ItemLibrary.query.get_or_404(item_id)
            
            item.item_name = request.form.get('item_name', '').strip()
            item.part_number = request.form.get('part_number', '').strip() or None
            item.customer = request.form.get('customer', '').strip() or None
            
            if not item.item_name:
                return jsonify({'success': False, 'message': 'Item name is required'})
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Item updated successfully'})
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/admin/items/<int:item_id>/delete', methods=['POST'])
    @login_required
    def delete_item(item_id):
        """Delete item"""
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        try:
            item = ItemLibrary.query.get_or_404(item_id)
            db.session.delete(item)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Item deleted successfully'})
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})
    
    @app.route('/admin/items/clear-all', methods=['POST'])
    @login_required
    def clear_all_items():
        """Clear all items from library"""
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        try:
            ItemLibrary.query.delete()
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'All items cleared successfully'})
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})

    return app


# Create app instance at module level for Vercel/WSGI servers
app = create_app()

if __name__ == '__main__':
    # Local development only
    # Port 8000 is only for local dev, not used in Vercel
    debug_mode = os.getenv('FLASK_DEBUG') == '1'
    app.run(debug=debug_mode, host=os.getenv('HOST', '0.0.0.0'), port=int(os.getenv('PORT', '8000')))

