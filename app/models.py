from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role          = db.Column(db.String(20), default='student')
    full_name     = db.Column(db.String(120))
    points        = db.Column(db.Integer, default=0)
    level         = db.Column(db.Integer, default=1)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    is_active     = db.Column(db.Boolean, default=True)

    attempts  = db.relationship('QuizAttempt',   backref='student', lazy='dynamic')
    progress  = db.relationship('LessonProgress', backref='student', lazy='dynamic')
    badges    = db.relationship('UserBadge',      backref='student', lazy='dynamic')

    def set_password(self, p):   self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)
    def is_admin(self):          return self.role == 'admin'

    def get_level_title(self):
        return {1:'🌱 مبتدئ',2:'⭐ متقدم',3:'🚀 محترف',4:'🏆 خبير',5:'👑 بطل'}.get(self.level,'👑 بطل')


class Subject(db.Model):
    __tablename__ = 'subjects'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    name_ar     = db.Column(db.String(100))
    description = db.Column(db.Text)
    icon        = db.Column(db.String(10), default='📚')
    color       = db.Column(db.String(20), default='#4F46E5')
    bg_color    = db.Column(db.String(20), default='#EEF2FF')
    order       = db.Column(db.Integer, default=0)
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    lessons = db.relationship('Lesson', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz',   backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    videos  = db.relationship('Video',  backref='subject', lazy='dynamic', cascade='all, delete-orphan')

    def lesson_count(self): return self.lessons.filter_by(is_active=True).count()
    def quiz_count(self):   return self.quizzes.filter_by(is_active=True).count()
    def video_count(self):  return self.videos.filter_by(is_active=True).count()


class Lesson(db.Model):
    __tablename__ = 'lessons'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    content     = db.Column(db.Text, nullable=False)
    summary     = db.Column(db.Text)
    subject_id  = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    order       = db.Column(db.Integer, default=0)
    duration    = db.Column(db.Integer, default=15)
    difficulty  = db.Column(db.String(20), default='easy')
    image       = db.Column(db.String(200))
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    progress = db.relationship('LessonProgress', backref='lesson', lazy='dynamic', cascade='all, delete-orphan')

    def get_difficulty_label(self):
        return {'easy':('سهل','🟢'),'medium':('متوسط','🟡'),'hard':('صعب','🔴')}.get(self.difficulty,('سهل','🟢'))


class LessonProgress(db.Model):
    __tablename__ = 'lesson_progress'
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id     = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    completed     = db.Column(db.Boolean, default=False)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id'),)


class Video(db.Model):
    __tablename__ = 'videos'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    youtube_url = db.Column(db.String(300))
    youtube_id  = db.Column(db.String(50))
    subject_id  = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    duration    = db.Column(db.String(20))
    order       = db.Column(db.Integer, default=0)
    is_active   = db.Column(db.Boolean, default=True)
    views       = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def extract_youtube_id(self):
        import re
        if self.youtube_url:
            m = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', self.youtube_url)
            if m: return m.group(1)
        return None

    def get_embed_url(self):
        vid = self.youtube_id or self.extract_youtube_id()
        return f'https://www.youtube.com/embed/{vid}?rel=0&modestbranding=1' if vid else None

    def get_thumbnail_url(self):
        vid = self.youtube_id or self.extract_youtube_id()
        return f'https://img.youtube.com/vi/{vid}/mqdefault.jpg' if vid else None


class Quiz(db.Model):
    __tablename__ = 'quizzes'
    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(200), nullable=False)
    description      = db.Column(db.Text)
    subject_id       = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    time_limit       = db.Column(db.Integer, default=0)
    pass_score       = db.Column(db.Integer, default=60)
    order            = db.Column(db.Integer, default=0)
    is_active        = db.Column(db.Boolean, default=True)
    # ── New controls ──
    show_answers     = db.Column(db.Boolean, default=True)   # show correct answers after submit
    shuffle_questions= db.Column(db.Boolean, default=False)  # randomize question order
    max_attempts     = db.Column(db.Integer, default=0)      # 0 = unlimited
    quiz_type        = db.Column(db.String(20), default='exam')  # exam | practice | game
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question',    backref='quiz', lazy='dynamic',
                                cascade='all, delete-orphan', order_by='Question.order')
    attempts  = db.relationship('QuizAttempt', backref='quiz', lazy='dynamic',
                                cascade='all, delete-orphan')

    def question_count(self): return self.questions.count()
    def total_points(self):
        return db.session.query(db.func.sum(Question.points))\
                         .filter(Question.quiz_id == self.id).scalar() or 0

    def get_type_label(self):
        return {'exam':('امتحان','📝'),'practice':('تمرين','✏️'),'game':('لعبة','🎮')}.get(self.quiz_type,('امتحان','📝'))

    def user_attempts_count(self, user_id):
        return self.attempts.filter_by(user_id=user_id).count()

    def can_attempt(self, user_id):
        if self.max_attempts == 0: return True
        return self.user_attempts_count(user_id) < self.max_attempts


class Question(db.Model):
    __tablename__ = 'questions'
    id          = db.Column(db.Integer, primary_key=True)
    quiz_id     = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    text        = db.Column(db.Text, nullable=False)
    q_type      = db.Column(db.String(20), default='mcq')
    image       = db.Column(db.String(200))
    explanation = db.Column(db.Text)
    points      = db.Column(db.Integer, default=1)
    order       = db.Column(db.Integer, default=0)

    choices = db.relationship('Choice',     backref='question', lazy='dynamic', cascade='all, delete-orphan')
    answers = db.relationship('UserAnswer', backref='question', lazy='dynamic', cascade='all, delete-orphan')

    def get_correct_choice(self):
        return self.choices.filter_by(is_correct=True).first()


class Choice(db.Model):
    __tablename__ = 'choices'
    id          = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    text        = db.Column(db.String(500), nullable=False)
    is_correct  = db.Column(db.Boolean, default=False)
    order       = db.Column(db.Integer, default=0)


class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id       = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score         = db.Column(db.Float, default=0)
    total_points  = db.Column(db.Integer, default=0)
    earned_points = db.Column(db.Integer, default=0)
    passed        = db.Column(db.Boolean, default=False)
    started_at    = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at  = db.Column(db.DateTime)
    time_taken    = db.Column(db.Integer)

    answers = db.relationship('UserAnswer', backref='attempt', lazy='dynamic', cascade='all, delete-orphan')

    def get_percentage(self):
        if self.total_points == 0: return 0
        return round((self.earned_points / self.total_points) * 100, 1)


class UserAnswer(db.Model):
    __tablename__ = 'user_answers'
    id          = db.Column(db.Integer, primary_key=True)
    attempt_id  = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    choice_id   = db.Column(db.Integer, db.ForeignKey('choices.id'))
    is_correct  = db.Column(db.Boolean, default=False)
    choice      = db.relationship('Choice', foreign_keys=[choice_id])


class Badge(db.Model):
    __tablename__ = 'badges'
    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(100), nullable=False)
    description     = db.Column(db.Text)
    icon            = db.Column(db.String(10), default='🏅')
    color           = db.Column(db.String(20), default='#F59E0B')
    condition       = db.Column(db.String(50))
    points_required = db.Column(db.Integer, default=0)
    users = db.relationship('UserBadge', backref='badge', lazy='dynamic', cascade='all, delete-orphan')


class UserBadge(db.Model):
    __tablename__ = 'user_badges'
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_id  = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'badge_id'),)


# ═══════════════════════════════════════════════════════════
#  ADHD MODELS — Phase 1
# ═══════════════════════════════════════════════════════════

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    dark_mode      = db.Column(db.Boolean, default=False)
    font_size      = db.Column(db.String(10), default='medium')   # small|medium|large
    reduced_motion = db.Column(db.Boolean, default=False)
    sound_enabled  = db.Column(db.Boolean, default=True)
    dyslexia_font  = db.Column(db.Boolean, default=False)
    focus_duration = db.Column(db.Integer, default=25)            # minutes
    user           = db.relationship('User', backref=db.backref('settings', uselist=False))


class UserStreak(db.Model):
    __tablename__ = 'user_streaks'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    current_streak  = db.Column(db.Integer, default=0)
    longest_streak  = db.Column(db.Integer, default=0)
    last_activity   = db.Column(db.Date)
    total_days      = db.Column(db.Integer, default=0)
    user            = db.relationship('User', backref=db.backref('streak', uselist=False))

    def update(self):
        from datetime import date, timedelta
        today = date.today()
        if self.last_activity == today:
            return False   # already updated today
        if self.last_activity == today - timedelta(days=1):
            self.current_streak += 1
        else:
            self.current_streak = 1
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.last_activity = today
        self.total_days    += 1
        return True


class DailyMission(db.Model):
    __tablename__ = 'daily_missions'
    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    description  = db.Column(db.Text)
    mission_type = db.Column(db.String(20), default='lesson')  # lesson|quiz|video|streak|points
    target_count = db.Column(db.Integer, default=1)
    xp_reward    = db.Column(db.Integer, default=20)
    icon         = db.Column(db.String(10), default='🎯')
    is_active    = db.Column(db.Boolean, default=True)
    progress     = db.relationship('UserMissionProgress', backref='mission',
                                   lazy='dynamic', cascade='all, delete-orphan')


class UserMissionProgress(db.Model):
    __tablename__ = 'user_mission_progress'
    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mission_id    = db.Column(db.Integer, db.ForeignKey('daily_missions.id'), nullable=False)
    date          = db.Column(db.Date, nullable=False)
    current_count = db.Column(db.Integer, default=0)
    completed     = db.Column(db.Boolean, default=False)
    completed_at  = db.Column(db.DateTime)
    __table_args__ = (db.UniqueConstraint('user_id', 'mission_id', 'date'),)


class LearningChunk(db.Model):
    """Micro-learning: breaks a lesson into 2-3 min pieces"""
    __tablename__ = 'learning_chunks'
    id          = db.Column(db.Integer, primary_key=True)
    lesson_id   = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    title       = db.Column(db.String(200))
    content     = db.Column(db.Text, nullable=False)
    chunk_type  = db.Column(db.String(20), default='text')  # text|tip|example|summary
    order       = db.Column(db.Integer, default=0)
    emoji       = db.Column(db.String(10), default='📖')
    lesson      = db.relationship('Lesson', backref=db.backref('chunks', lazy='dynamic',
                                  order_by='LearningChunk.order'))


class FocusSession(db.Model):
    __tablename__ = 'focus_sessions'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id   = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    started_at  = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at    = db.Column(db.DateTime)
    duration    = db.Column(db.Integer, default=0)   # seconds
    completed   = db.Column(db.Boolean, default=False)
