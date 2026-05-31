import os, re
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.admin import admin
from app import db
from app.models import (User, Subject, Lesson, Video, Quiz,
                        Question, Choice, QuizAttempt, Badge, UserBadge)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('ليس لديك صلاحية الوصول', 'danger')
            return redirect(url_for('student.dashboard'))
        return f(*args, **kwargs)
    return login_required(decorated)

def save_upload(file, subfolder=''):
    from werkzeug.utils import secure_filename
    import uuid
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join('app', 'static', 'uploads', subfolder)
    os.makedirs(folder, exist_ok=True)
    file.save(os.path.join(folder, filename))
    return os.path.join(subfolder, filename).replace('\\', '/')

# ═══ DASHBOARD ════════════════════════════════════════════════
@admin.route('/dashboard')
@admin_required
def dashboard():
    stats = {
        'subjects': Subject.query.count(),
        'lessons':  Lesson.query.count(),
        'videos':   Video.query.count(),
        'quizzes':  Quiz.query.count(),
        'students': User.query.filter_by(role='student').count(),
        'attempts': QuizAttempt.query.count(),
    }
    recent_students = User.query.filter_by(role='student').order_by(User.created_at.desc()).limit(5).all()
    recent_attempts = QuizAttempt.query.order_by(QuizAttempt.completed_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_students=recent_students, recent_attempts=recent_attempts)

# ═══ SUBJECTS ═════════════════════════════════════════════════
@admin.route('/subjects')
@admin_required
def subjects():
    return render_template('admin/subjects.html', subjects=Subject.query.order_by(Subject.order).all())

@admin.route('/subjects/add', methods=['GET','POST'])
@admin_required
def add_subject():
    if request.method == 'POST':
        s = Subject(name=request.form['name'], name_ar=request.form.get('name_ar',''),
                    description=request.form.get('description',''),
                    icon=request.form.get('icon','📚'), color=request.form.get('color','#4F46E5'),
                    bg_color=request.form.get('bg_color','#EEF2FF'),
                    order=int(request.form.get('order',0)))
        db.session.add(s); db.session.commit()
        flash('تمت إضافة المادة ✅','success')
        return redirect(url_for('admin.subjects'))
    return render_template('admin/subject_form.html', subject=None)

@admin.route('/subjects/<int:sid>/edit', methods=['GET','POST'])
@admin_required
def edit_subject(sid):
    s = Subject.query.get_or_404(sid)
    if request.method == 'POST':
        s.name=request.form['name']; s.name_ar=request.form.get('name_ar','')
        s.description=request.form.get('description',''); s.icon=request.form.get('icon','📚')
        s.color=request.form.get('color','#4F46E5'); s.bg_color=request.form.get('bg_color','#EEF2FF')
        s.order=int(request.form.get('order',0)); s.is_active='is_active' in request.form
        db.session.commit(); flash('تم تحديث المادة ✅','success')
        return redirect(url_for('admin.subjects'))
    return render_template('admin/subject_form.html', subject=s)

@admin.route('/subjects/<int:sid>/delete', methods=['POST'])
@admin_required
def delete_subject(sid):
    s = Subject.query.get_or_404(sid); db.session.delete(s); db.session.commit()
    flash('تم حذف المادة','warning'); return redirect(url_for('admin.subjects'))

# ═══ LESSONS ══════════════════════════════════════════════════
@admin.route('/lessons')
@admin_required
def lessons():
    sid = request.args.get('subject_id', type=int)
    q = Lesson.query
    if sid: q = q.filter_by(subject_id=sid)
    return render_template('admin/lessons.html', lessons=q.order_by(Lesson.subject_id,Lesson.order).all(),
                           subjects=Subject.query.filter_by(is_active=True).all(), selected_subject=sid)

@admin.route('/lessons/add', methods=['GET','POST'])
@admin_required
def add_lesson():
    subjects = Subject.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        lesson = Lesson(title=request.form['title'], content=request.form['content'],
                        summary=request.form.get('summary',''),
                        subject_id=int(request.form['subject_id']),
                        order=int(request.form.get('order',0)),
                        duration=int(request.form.get('duration',15)),
                        difficulty=request.form.get('difficulty','easy'))
        db.session.add(lesson); db.session.commit()
        flash('تمت إضافة الدرس ✅','success')
        return redirect(url_for('admin.lessons'))
    return render_template('admin/lesson_form.html', lesson=None, subjects=subjects)

@admin.route('/lessons/<int:lid>/edit', methods=['GET','POST'])
@admin_required
def edit_lesson(lid):
    lesson = Lesson.query.get_or_404(lid)
    subjects = Subject.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        lesson.title=request.form['title']; lesson.content=request.form['content']
        lesson.summary=request.form.get('summary','')
        lesson.subject_id=int(request.form['subject_id'])
        lesson.order=int(request.form.get('order',0))
        lesson.duration=int(request.form.get('duration',15))
        lesson.difficulty=request.form.get('difficulty','easy')
        lesson.is_active='is_active' in request.form
        db.session.commit(); flash('تم تحديث الدرس ✅','success')
        return redirect(url_for('admin.lessons'))
    return render_template('admin/lesson_form.html', lesson=lesson, subjects=subjects)

@admin.route('/lessons/<int:lid>/delete', methods=['POST'])
@admin_required
def delete_lesson(lid):
    l = Lesson.query.get_or_404(lid); db.session.delete(l); db.session.commit()
    flash('تم حذف الدرس','warning'); return redirect(url_for('admin.lessons'))

# ═══ VIDEOS ═══════════════════════════════════════════════════
@admin.route('/videos')
@admin_required
def videos():
    sid = request.args.get('subject_id', type=int)
    q = Video.query
    if sid: q = q.filter_by(subject_id=sid)
    return render_template('admin/videos.html',
                           videos=q.order_by(Video.subject_id,Video.order).all(),
                           subjects=Subject.query.filter_by(is_active=True).all(), selected_subject=sid)

@admin.route('/videos/add', methods=['GET','POST'])
@admin_required
def add_video():
    subjects = Subject.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url','')
        youtube_id = None
        if youtube_url:
            m = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', youtube_url)
            if m: youtube_id = m.group(1)
        v = Video(title=request.form['title'], description=request.form.get('description',''),
                  youtube_url=youtube_url, youtube_id=youtube_id,
                  subject_id=int(request.form['subject_id']),
                  duration=request.form.get('duration',''), order=int(request.form.get('order',0)))
        db.session.add(v); db.session.commit()
        flash('تمت إضافة الفيديو ✅','success')
        return redirect(url_for('admin.videos'))
    return render_template('admin/video_form.html', video=None, subjects=subjects)

@admin.route('/videos/<int:vid>/edit', methods=['GET','POST'])
@admin_required
def edit_video(vid):
    video = Video.query.get_or_404(vid)
    subjects = Subject.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        youtube_url = request.form.get('youtube_url','')
        youtube_id = None
        if youtube_url:
            m = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', youtube_url)
            if m: youtube_id = m.group(1)
        video.title=request.form['title']; video.description=request.form.get('description','')
        video.youtube_url=youtube_url; video.youtube_id=youtube_id
        video.subject_id=int(request.form['subject_id'])
        video.duration=request.form.get('duration',''); video.order=int(request.form.get('order',0))
        video.is_active='is_active' in request.form
        db.session.commit(); flash('تم تحديث الفيديو ✅','success')
        return redirect(url_for('admin.videos'))
    return render_template('admin/video_form.html', video=video, subjects=subjects)

@admin.route('/videos/<int:vid>/delete', methods=['POST'])
@admin_required
def delete_video(vid):
    v = Video.query.get_or_404(vid); db.session.delete(v); db.session.commit()
    flash('تم حذف الفيديو','warning'); return redirect(url_for('admin.videos'))

# ═══ QUIZZES ══════════════════════════════════════════════════
@admin.route('/quizzes')
@admin_required
def quizzes():
    sid = request.args.get('subject_id', type=int)
    q = Quiz.query
    if sid: q = q.filter_by(subject_id=sid)
    return render_template('admin/quizzes.html',
                           quizzes=q.order_by(Quiz.subject_id,Quiz.order).all(),
                           subjects=Subject.query.filter_by(is_active=True).all(), selected_subject=sid)

@admin.route('/quizzes/add', methods=['GET','POST'])
@admin_required
def add_quiz():
    subjects = Subject.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        q = Quiz(
            title=request.form['title'],
            description=request.form.get('description',''),
            subject_id=int(request.form['subject_id']),
            time_limit=int(request.form.get('time_limit',0)),
            pass_score=int(request.form.get('pass_score',60)),
            order=int(request.form.get('order',0)),
            quiz_type=request.form.get('quiz_type','exam'),
            show_answers='show_answers' in request.form,
            shuffle_questions='shuffle_questions' in request.form,
            max_attempts=int(request.form.get('max_attempts',0)),
        )
        db.session.add(q); db.session.commit()
        flash('تمت إضافة الامتحان ✅','success')
        return redirect(url_for('admin.quiz_questions', qid=q.id))
    return render_template('admin/quiz_form.html', quiz=None, subjects=subjects)

@admin.route('/quizzes/<int:qid>/edit', methods=['GET','POST'])
@admin_required
def edit_quiz(qid):
    quiz = Quiz.query.get_or_404(qid)
    subjects = Subject.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        quiz.title=request.form['title']; quiz.description=request.form.get('description','')
        quiz.subject_id=int(request.form['subject_id'])
        quiz.time_limit=int(request.form.get('time_limit',0))
        quiz.pass_score=int(request.form.get('pass_score',60))
        quiz.order=int(request.form.get('order',0))
        quiz.is_active='is_active' in request.form
        quiz.quiz_type=request.form.get('quiz_type','exam')
        quiz.show_answers='show_answers' in request.form
        quiz.shuffle_questions='shuffle_questions' in request.form
        quiz.max_attempts=int(request.form.get('max_attempts',0))
        db.session.commit(); flash('تم تحديث الامتحان ✅','success')
        return redirect(url_for('admin.quizzes'))
    return render_template('admin/quiz_form.html', quiz=quiz, subjects=subjects)

@admin.route('/quizzes/<int:qid>/delete', methods=['POST'])
@admin_required
def delete_quiz(qid):
    q = Quiz.query.get_or_404(qid); db.session.delete(q); db.session.commit()
    flash('تم حذف الامتحان','warning'); return redirect(url_for('admin.quizzes'))

@admin.route('/quizzes/<int:qid>/questions')
@admin_required
def quiz_questions(qid):
    quiz = Quiz.query.get_or_404(qid)
    return render_template('admin/quiz_questions.html', quiz=quiz,
                           questions=quiz.questions.order_by(Question.order).all())

@admin.route('/quizzes/<int:qid>/questions/add', methods=['GET','POST'])
@admin_required
def add_question(qid):
    quiz = Quiz.query.get_or_404(qid)
    if request.method == 'POST':
        question = Question(quiz_id=quiz.id, text=request.form['text'],
                            q_type=request.form.get('q_type','mcq'),
                            explanation=request.form.get('explanation',''),
                            points=int(request.form.get('points',1)),
                            order=int(request.form.get('order',0)))
        db.session.add(question); db.session.flush()
        if question.q_type == 'true_false':
            correct = request.form.get('correct_tf','true')
            db.session.add(Choice(question_id=question.id, text='صحيح', is_correct=(correct=='true'), order=0))
            db.session.add(Choice(question_id=question.id, text='خطأ',  is_correct=(correct=='false'), order=1))
        else:
            choices = request.form.getlist('choice_text')
            correct_idx = int(request.form.get('correct_choice',0))
            for i, text in enumerate(choices):
                if text.strip():
                    db.session.add(Choice(question_id=question.id, text=text.strip(),
                                          is_correct=(i==correct_idx), order=i))
        db.session.commit(); flash('تمت إضافة السؤال ✅','success')
        return redirect(url_for('admin.quiz_questions', qid=qid))
    return render_template('admin/question_form.html', quiz=quiz, question=None)

@admin.route('/questions/<int:qid>/edit', methods=['GET','POST'])
@admin_required
def edit_question(qid):
    question = Question.query.get_or_404(qid); quiz = question.quiz
    if request.method == 'POST':
        question.text=request.form['text']; question.q_type=request.form.get('q_type','mcq')
        question.explanation=request.form.get('explanation','')
        question.points=int(request.form.get('points',1)); question.order=int(request.form.get('order',0))
        for c in question.choices.all(): db.session.delete(c)
        db.session.flush()
        if question.q_type == 'true_false':
            correct = request.form.get('correct_tf','true')
            db.session.add(Choice(question_id=question.id, text='صحيح', is_correct=(correct=='true'), order=0))
            db.session.add(Choice(question_id=question.id, text='خطأ',  is_correct=(correct=='false'), order=1))
        else:
            choices = request.form.getlist('choice_text')
            correct_idx = int(request.form.get('correct_choice',0))
            for i, text in enumerate(choices):
                if text.strip():
                    db.session.add(Choice(question_id=question.id, text=text.strip(),
                                          is_correct=(i==correct_idx), order=i))
        db.session.commit(); flash('تم تحديث السؤال ✅','success')
        return redirect(url_for('admin.quiz_questions', qid=quiz.id))
    return render_template('admin/question_form.html', quiz=quiz, question=question)

@admin.route('/questions/<int:qid>/delete', methods=['POST'])
@admin_required
def delete_question(qid):
    question = Question.query.get_or_404(qid); quiz_id = question.quiz_id
    db.session.delete(question); db.session.commit()
    flash('تم حذف السؤال','warning')
    return redirect(url_for('admin.quiz_questions', qid=quiz_id))

# ═══ STUDENTS ═════════════════════════════════════════════════
@admin.route('/students')
@admin_required
def students():
    return render_template('admin/students.html',
                           students=User.query.filter_by(role='student').order_by(User.created_at.desc()).all())

@admin.route('/students/<int:uid>/toggle', methods=['POST'])
@admin_required
def toggle_student(uid):
    user = User.query.get_or_404(uid); user.is_active = not user.is_active
    db.session.commit(); flash(f'تم {"تفعيل" if user.is_active else "تعطيل"} الحساب','info')
    return redirect(url_for('admin.students'))

@admin.route('/students/<int:uid>/delete', methods=['POST'])
@admin_required
def delete_student(uid):
    user = User.query.get_or_404(uid); db.session.delete(user); db.session.commit()
    flash('تم حذف الطالب','warning'); return redirect(url_for('admin.students'))

# ═══ BADGES ═══════════════════════════════════════════════════
@admin.route('/badges')
@admin_required
def badges():
    return render_template('admin/badges.html', badges=Badge.query.all())

@admin.route('/badges/add', methods=['GET','POST'])
@admin_required
def add_badge():
    if request.method == 'POST':
        b = Badge(name=request.form['name'], description=request.form.get('description',''),
                  icon=request.form.get('icon','🏅'), color=request.form.get('color','#F59E0B'),
                  condition=request.form.get('condition',''),
                  points_required=int(request.form.get('points_required',0)))
        db.session.add(b); db.session.commit()
        flash('تمت إضافة الشارة ✅','success')
        return redirect(url_for('admin.badges'))
    return render_template('admin/badge_form.html', badge=None)

@admin.route('/badges/<int:bid>/delete', methods=['POST'])
@admin_required
def delete_badge(bid):
    b = Badge.query.get_or_404(bid); db.session.delete(b); db.session.commit()
    flash('تم حذف الشارة','warning'); return redirect(url_for('admin.badges'))

# ═══ QUIZ RESULTS (admin view) ════════════════════════════════
@admin.route('/results')
@admin_required
def results():
    attempts = QuizAttempt.query.filter(QuizAttempt.completed_at.isnot(None))\
                                .order_by(QuizAttempt.completed_at.desc()).limit(50).all()
    return render_template('admin/results.html', attempts=attempts)
