import os, uuid
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.student import student
from app import db
from werkzeug.utils import secure_filename

ALLOWED_IMG = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
THEME_COLORS = [
    ('#6C63FF', 'بنفسجي'),  ('#10B981', 'أخضر'),
    ('#3B82F6', 'أزرق'),    ('#F59E0B', 'ذهبي'),
    ('#EF4444', 'أحمر'),    ('#EC4899', 'وردي'),
    ('#8B5CF6', 'بنفسجي غامق'), ('#14B8A6', 'فيروزي'),
]


@student.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        action = request.form.get('action', 'profile')

        if action == 'profile':
            current_user.full_name = request.form.get('full_name', '').strip()
            # Avatar upload
            if 'avatar' in request.files:
                f = request.files['avatar']
                if f and f.filename and '.' in f.filename:
                    ext = f.filename.rsplit('.', 1)[1].lower()
                    if ext in ALLOWED_IMG:
                        fname = f'{uuid.uuid4().hex}.{ext}'
                        folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
                        os.makedirs(folder, exist_ok=True)
                        f.save(os.path.join(folder, fname))
                        current_user.avatar = f'avatars/{fname}'
            db.session.commit()
            flash('تم تحديث الملف الشخصي ✅', 'success')

        elif action == 'password':
            from werkzeug.security import check_password_hash
            current_pw = request.form.get('current_password', '')
            new_pw     = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')
            if not current_user.check_password(current_pw):
                flash('كلمة المرور الحالية غير صحيحة', 'danger')
            elif len(new_pw) < 6:
                flash('كلمة المرور الجديدة قصيرة جداً (6 أحرف على الأقل)', 'danger')
            elif new_pw != confirm_pw:
                flash('كلمتا المرور غير متطابقتين', 'danger')
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash('تم تغيير كلمة المرور ✅', 'success')

        elif action == 'email':
            from app.models import User
            new_email = request.form.get('email', '').strip()
            if not new_email:
                flash('البريد الإلكتروني مطلوب', 'danger')
            elif User.query.filter(User.email == new_email, User.id != current_user.id).first():
                flash('هذا البريد مستخدم من حساب آخر', 'danger')
            else:
                current_user.email = new_email
                db.session.commit()
                flash('تم تحديث البريد الإلكتروني ✅', 'success')

        elif action == 'theme':
            theme = request.form.get('theme_color', '#6C63FF')
            from app.student.routes import get_or_create_settings
            s = get_or_create_settings(current_user)
            # Store theme in settings extra field
            if not hasattr(s, 'theme_color'):
                pass  # handled via CSS variable
            # Save to session for now
            from flask import session
            session['theme_color'] = theme
            db.session.commit()
            flash('تم تغيير لون الواجهة ✅', 'success')

        return redirect(url_for('student.edit_profile'))

    from app.student.routes import get_or_create_settings
    settings = get_or_create_settings(current_user)
    return render_template('student/edit_profile.html',
                           settings=settings, theme_colors=THEME_COLORS)
