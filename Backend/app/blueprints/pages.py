from flask import Blueprint, render_template, redirect, url_for, session
from auth import login_required_web, admin_required_web

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/')
def home():
    """Redirect to the viewer page."""
    if 'username' not in session:
        return redirect(url_for('pages.login'))
    return render_template('viewer.html')

@pages_bp.route('/login')
def login():
    """Render the login page."""
    if 'username' in session:
        return redirect(url_for('pages.home'))
    return render_template('login.html')

@pages_bp.route('/signup')
def signup():
    """Render the signup page."""
    if 'username' in session:
        return redirect(url_for('pages.home'))
    return render_template('signup.html')

@pages_bp.route('/logout')
def logout():
    """Logout the user."""
    session.clear()
    return redirect(url_for('pages.login'))

@pages_bp.route('/viewer')
@login_required_web
def viewer():
    """Render the knowledge base viewer page."""
    return render_template('viewer.html')

@pages_bp.route('/settings')
@login_required_web
def settings():
    """Render the settings page."""
    return render_template('settings.html')

@pages_bp.route('/balance')
@login_required_web
def balance():
    """Render the balance page."""
    return render_template('balance.html')

@pages_bp.route('/contact')
@login_required_web
def contact():
    """Render the contact page."""
    return render_template('contact.html')

@pages_bp.route('/analytics')
@login_required_web
def analytics():
    """Render the analytics page."""
    return render_template('analytics.html')

@pages_bp.route('/about')
@login_required_web
def about():
    """Render the about page."""
    return render_template('about.html')

@pages_bp.route('/chatbot')
@login_required_web
def chatbot():
    """Render the chatbot page."""
    return render_template('chatbot.html')

@pages_bp.route('/admin')
@admin_required_web
def admin_panel():
    """Render the admin panel page."""
    return render_template('admin.html')
