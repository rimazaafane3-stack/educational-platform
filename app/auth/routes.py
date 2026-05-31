from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth
from app import db
from app.models import User, Badge, UserBadge


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=bool(remember))
            next_page = request.args.get('next')
            if user.is_admin():
                return redirect(next_page or url_for('admin.dashboard'))
            return redirect(next_page or url_for('student.dashboard'))
        flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
    return render_template('auth/login.html')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))
    if request.method == 'POST':
        username  = request.form.get('username', '').strip()
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        if not all([username, email, password]):
            flash('يرجى ملء جميع الحقول المطلوبة', 'danger')
            return render_template('auth/register.html')
        if password != confirm:
            flash('كلمتا المرور غير متطابقتين', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم مستخدم بالفعل', 'danger')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني مستخدم بالفعل', 'danger')
            return render_template('auth/register.html')

        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Award welcome badge
        welcome_badge = Badge.query.filter_by(condition='welcome').first()
        if welcome_badge:
            ub = UserBadge(user_id=user.id, badge_id=welcome_badge.id)
            db.session.add(ub)
            db.session.commit()

        login_user(user)
        flash(f'أهلاً {username}! تم إنشاء حسابك بنجاح 🎉', 'success')
        return redirect(url_for('student.dashboard'))
    return render_template('auth/register.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('auth.login'))
