import os
from app import create_app, db
from app.models import (User, Subject, Lesson, Video, Quiz,
                        Question, Choice, Badge)

app = create_app(os.environ.get('FLASK_CONFIG', 'default'))


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Subject=Subject, Lesson=Lesson,
                Video=Video, Quiz=Quiz, Question=Question,
                Choice=Choice, Badge=Badge)


@app.cli.command('init-db')
def init_db():
    """Create all tables."""
    db.create_all()
    print('✅ قاعدة البيانات جاهزة.')


@app.cli.command('seed')
def seed():
    """Seed the database with initial data."""
    from seed import seed_database
    seed_database()


@app.cli.command('create-admin')
def create_admin():
    """Create a default admin account."""
    if User.query.filter_by(username='admin').first():
        print('⚠️  المشرف موجود بالفعل.')
        return
    admin = User(
        username='admin',
        email='admin@platform.dz',
        full_name='مشرف النظام',
        role='admin'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print('✅ تم إنشاء حساب المشرف:')
    print('   اسم المستخدم : admin')
    print('   كلمة المرور  : admin123')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
