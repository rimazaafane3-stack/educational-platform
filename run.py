import os
from app import create_app, db
from app.models import (User, Subject, Lesson, Video, Quiz,
                        Question, Choice, Badge)

config_name = os.environ.get('FLASK_CONFIG', 'default')
app = create_app(config_name)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Subject=Subject,
                Lesson=Lesson, Video=Video, Quiz=Quiz)

# Auto-create tables on startup (safe for production)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0',
            port=int(os.environ.get('PORT', 5000)))
