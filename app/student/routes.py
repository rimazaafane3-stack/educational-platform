from datetime import datetime, date, timedelta
from flask import (render_template, redirect, url_for, flash,
                   request, jsonify, session)
from flask_login import login_required, current_user
from app.student import student
from app import db
from app.models import (Subject, Lesson, Video, Quiz, Question,
                        Choice, QuizAttempt, UserAnswer, LessonProgress,
                        Badge, UserBadge, UserStreak, UserSettings,
                        DailyMission, UserMissionProgress, LearningChunk,
                        FocusSession)

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_or_create_streak(user):
    s = UserStreak.query.filter_by(user_id=user.id).first()
    if not s:
        s = UserStreak(user_id=user.id)
        db.session.add(s)
        db.session.commit()
    return s

def get_or_create_settings(user):
    s = UserSettings.query.filter_by(user_id=user.id).first()
    if not s:
        s = UserSettings(user_id=user.id)
        db.session.add(s)
        db.session.commit()
    return s

def touch_streak(user):
    streak = get_or_create_streak(user)
    updated = streak.update()
    if updated:
        db.session.commit()
    return streak

def award_badge(user, condition):
    badge = Badge.query.filter_by(condition=condition).first()
    if badge and not UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first():
        ub = UserBadge(user_id=user.id, badge_id=badge.id)
        db.session.add(ub)
        db.session.commit()
        return badge
    return None

def update_user_level(user):
    for pts, lvl in reversed([(0,1),(100,2),(300,3),(600,4),(1000,5)]):
        if user.points >= pts:
            user.level = lvl
            break
    db.session.commit()

def get_today_missions(user):
    today   = date.today()
    missions = DailyMission.query.filter_by(is_active=True).all()
    result   = []
    for m in missions:
        prog = UserMissionProgress.query.filter_by(
            user_id=user.id, mission_id=m.id, date=today).first()
        if not prog:
            prog = UserMissionProgress(user_id=user.id, mission_id=m.id,
                                       date=today, current_count=0)
            db.session.add(prog)
        result.append({'mission': m, 'progress': prog})
    db.session.commit()
    return result

def advance_mission(user, mission_type, count=1):
    today    = date.today()
    missions = DailyMission.query.filter_by(is_active=True, mission_type=mission_type).all()
    for m in missions:
        prog = UserMissionProgress.query.filter_by(
            user_id=user.id, mission_id=m.id, date=today).first()
        if not prog:
            prog = UserMissionProgress(user_id=user.id, mission_id=m.id, date=today)
            db.session.add(prog)
        if not prog.completed:
            prog.current_count += count
            if prog.current_count >= m.target_count:
                prog.completed    = True
                prog.completed_at = datetime.utcnow()
                user.points      += m.xp_reward
                update_user_level(user)
    db.session.commit()

# ═══ HOME ════════════════════════════════════════════════════════════════════
@student.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))

# ═══ DASHBOARD ═══════════════════════════════════════════════════════════════
@student.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    # Touch streak
    streak   = touch_streak(current_user)
    settings = get_or_create_settings(current_user)

    subjects  = Subject.query.filter_by(is_active=True).order_by(Subject.order).all()
    missions  = get_today_missions(current_user)
    badges    = current_user.badges.order_by(UserBadge.earned_at.desc()).limit(4).all()
    attempts  = current_user.attempts.filter(
        QuizAttempt.completed_at.isnot(None)).order_by(
        QuizAttempt.completed_at.desc()).limit(3).all()

    # Last accessed lesson
    last_progress = LessonProgress.query.filter_by(
        user_id=current_user.id, completed=False).order_by(
        LessonProgress.last_accessed.desc()).first()
    last_lesson   = last_progress.lesson if last_progress else None

    # Progress per subject
    progress_map = {}
    for s in subjects:
        total    = s.lessons.filter_by(is_active=True).count()
        done_ids = [lp.lesson_id for lp in
                    current_user.progress.filter_by(completed=True).all()]
        done     = s.lessons.filter(Lesson.id.in_(done_ids),
                                    Lesson.is_active == True).count()
        progress_map[s.id] = {
            'total': total, 'done': done,
            'pct':   int(done/total*100) if total else 0
        }

    # Missions done count
    missions_done = sum(1 for m in missions if m['progress'].completed)

    return render_template('student/dashboard.html',
        subjects=subjects, progress_map=progress_map,
        streak=streak, settings=settings,
        missions=missions, missions_done=missions_done,
        badges=badges, attempts=attempts, last_lesson=last_lesson)

# ═══ SUBJECT ═════════════════════════════════════════════════════════════════
@student.route('/subject/<int:sid>')
@login_required
def subject(sid):
    s        = Subject.query.get_or_404(sid)
    lessons  = s.lessons.filter_by(is_active=True).order_by(Lesson.order).all()
    videos   = s.videos.filter_by(is_active=True).order_by(Video.order).all()
    quizzes  = s.quizzes.filter_by(is_active=True).order_by(Quiz.order).all()
    done_ids = {lp.lesson_id for lp in
                current_user.progress.filter_by(completed=True).all()}
    best_scores = {}
    for q in quizzes:
        best = current_user.attempts.filter_by(quiz_id=q.id)\
                           .order_by(QuizAttempt.score.desc()).first()
        best_scores[q.id] = best
    return render_template('student/subject.html', subject=s,
                           lessons=lessons, videos=videos, quizzes=quizzes,
                           done_ids=done_ids, best_scores=best_scores)

# ═══ LESSON — Focus Mode ══════════════════════════════════════════════════════
@student.route('/lesson/<int:lid>')
@login_required
def lesson(lid):
    l = Lesson.query.get_or_404(lid)
    if not l.is_active:
        flash('هذا الدرس غير متاح', 'warning')
        return redirect(url_for('student.subject', sid=l.subject_id))

    # Progress tracking
    prog = LessonProgress.query.filter_by(
        user_id=current_user.id, lesson_id=l.id).first()
    if not prog:
        prog = LessonProgress(user_id=current_user.id, lesson_id=l.id)
        db.session.add(prog)
    prog.last_accessed = datetime.utcnow()

    # Focus session
    fs = FocusSession(user_id=current_user.id, lesson_id=l.id)
    db.session.add(fs)
    db.session.commit()

    # Get chunks
    chunks = l.chunks.order_by(LearningChunk.order).all()

    # Adjacent lessons
    prev_l = Lesson.query.filter_by(subject_id=l.subject_id, is_active=True)\
                         .filter(Lesson.order < l.order)\
                         .order_by(Lesson.order.desc()).first()
    next_l = Lesson.query.filter_by(subject_id=l.subject_id, is_active=True)\
                         .filter(Lesson.order > l.order)\
                         .order_by(Lesson.order.asc()).first()

    settings = get_or_create_settings(current_user)

    return render_template('student/lesson.html', lesson=l,
                           progress=prog, prev_lesson=prev_l, next_lesson=next_l,
                           chunks=chunks, focus_session_id=fs.id,
                           settings=settings)

@student.route('/lesson/<int:lid>/complete', methods=['POST'])
@login_required
def complete_lesson(lid):
    lesson = Lesson.query.get_or_404(lid)
    prog   = LessonProgress.query.filter_by(
        user_id=current_user.id, lesson_id=lid).first()
    if not prog:
        prog = LessonProgress(user_id=current_user.id, lesson_id=lid)
        db.session.add(prog)
    new_complete = not prog.completed
    if not prog.completed:
        prog.completed       = True
        current_user.points += 10
        update_user_level(current_user)
        award_badge(current_user, 'first_lesson')
        advance_mission(current_user, 'lesson')
        touch_streak(current_user)
    db.session.commit()
    return jsonify({
        'success':   True,
        'points':    current_user.points,
        'level':     current_user.level,
        'new':       new_complete,
        'message':   'أحسنت! حصلت على 10 نقاط 🌟'
    })

# End focus session
@student.route('/focus/<int:fid>/end', methods=['POST'])
@login_required
def end_focus(fid):
    fs = FocusSession.query.get_or_404(fid)
    if fs.user_id == current_user.id:
        fs.ended_at = datetime.utcnow()
        fs.duration = int((fs.ended_at - fs.started_at).total_seconds())
        fs.completed = request.json.get('completed', False)
        db.session.commit()
    return jsonify({'ok': True})

# ═══ VIDEOS ══════════════════════════════════════════════════════════════════
@student.route('/videos')
@login_required
def videos_list():
    sid  = request.args.get('subject_id', type=int)
    q    = Video.query.filter_by(is_active=True)
    if sid: q = q.filter_by(subject_id=sid)
    vids = q.order_by(Video.subject_id, Video.order).all()
    subjects = Subject.query.filter_by(is_active=True).all()
    return render_template('student/videos.html', videos=vids,
                           subjects=subjects, selected_subject=sid)

@student.route('/video/<int:vid>')
@login_required
def video(vid):
    v = Video.query.get_or_404(vid)
    if not v.is_active:
        flash('هذا الفيديو غير متاح', 'warning')
        return redirect(url_for('student.videos_list'))
    v.views += 1
    db.session.commit()
    advance_mission(current_user, 'video')
    related = Video.query.filter_by(subject_id=v.subject_id, is_active=True)\
                         .filter(Video.id != v.id).limit(4).all()
    return render_template('student/video.html', video=v, related=related)

# ═══ QUIZZES ═════════════════════════════════════════════════════════════════
@student.route('/quiz/<int:qid>/start')
@login_required
def quiz_start(qid):
    quiz = Quiz.query.get_or_404(qid)
    if not quiz.is_active:
        flash('هذا الامتحان غير متاح', 'warning')
        return redirect(url_for('student.subject', sid=quiz.subject_id))
    if not quiz.can_attempt(current_user.id):
        flash('وصلت للحد الأقصى من المحاولات', 'warning')
        return redirect(url_for('student.subject', sid=quiz.subject_id))

    questions = quiz.questions.order_by(Question.order).all()
    if not questions:
        flash('لا توجد أسئلة بعد', 'warning')
        return redirect(url_for('student.subject', sid=quiz.subject_id))

    import random as _r
    if quiz.shuffle_questions:
        questions = list(questions)
        _r.shuffle(questions)

    attempt = QuizAttempt(user_id=current_user.id, quiz_id=quiz.id,
                          total_points=quiz.total_points())
    db.session.add(attempt)
    db.session.commit()
    session[f'attempt_{attempt.id}_start'] = datetime.utcnow().isoformat()

    return render_template('student/quiz.html', quiz=quiz,
                           questions=questions, attempt=attempt)

@student.route('/quiz/submit/<int:attempt_id>', methods=['POST'])
@login_required
def quiz_submit(attempt_id):
    attempt   = QuizAttempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id:
        flash('خطأ في الصلاحية', 'danger')
        return redirect(url_for('student.dashboard'))

    quiz      = attempt.quiz
    questions = quiz.questions.all()
    earned    = 0

    for q in questions:
        choice_id  = request.form.get(f'q_{q.id}')
        is_correct = False
        if choice_id:
            choice = Choice.query.get(int(choice_id))
            if choice and choice.question_id == q.id:
                is_correct = choice.is_correct
                if is_correct: earned += q.points
                db.session.add(UserAnswer(attempt_id=attempt.id,
                                          question_id=q.id,
                                          choice_id=choice.id,
                                          is_correct=is_correct))

    attempt.earned_points = earned
    attempt.total_points  = quiz.total_points()
    attempt.score         = attempt.get_percentage()
    attempt.passed        = attempt.score >= quiz.pass_score
    attempt.completed_at  = datetime.utcnow()

    start_key = f'attempt_{attempt.id}_start'
    if start_key in session:
        start = datetime.fromisoformat(session.pop(start_key))
        attempt.time_taken = int((datetime.utcnow() - start).total_seconds())

    pts = earned * 5 + (20 if attempt.score == 100 else 0)
    current_user.points += pts
    update_user_level(current_user)
    touch_streak(current_user)
    advance_mission(current_user, 'quiz')
    db.session.commit()

    new_badge = None
    if QuizAttempt.query.filter_by(user_id=current_user.id).count() == 1:
        new_badge = award_badge(current_user, 'first_quiz')
    if attempt.score == 100:
        new_badge = award_badge(current_user, 'perfect_score')

    return redirect(url_for('student.quiz_result', attempt_id=attempt.id,
                             new_badge=new_badge.id if new_badge else ''))

@student.route('/quiz/result/<int:attempt_id>')
@login_required
def quiz_result(attempt_id):
    attempt   = QuizAttempt.query.get_or_404(attempt_id)
    if attempt.user_id != current_user.id and not current_user.is_admin():
        flash('ليس لديك صلاحية', 'danger')
        return redirect(url_for('student.dashboard'))
    questions    = attempt.quiz.questions.order_by(Question.order).all()
    answers      = {a.question_id: a for a in attempt.answers.all()}
    new_badge_id = request.args.get('new_badge', type=int)
    new_badge    = Badge.query.get(new_badge_id) if new_badge_id else None
    return render_template('student/quiz_result.html',
                           attempt=attempt, questions=questions,
                           answers=answers, new_badge=new_badge)

# ═══ SETTINGS ════════════════════════════════════════════════════════════════
@student.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    s = get_or_create_settings(current_user)
    if request.method == 'POST':
        s.dark_mode      = 'dark_mode'      in request.form
        s.reduced_motion = 'reduced_motion' in request.form
        s.sound_enabled  = 'sound_enabled'  in request.form
        s.dyslexia_font  = 'dyslexia_font'  in request.form
        s.font_size      = request.form.get('font_size', 'medium')
        s.focus_duration = int(request.form.get('focus_duration', 25))
        db.session.commit()
        flash('تم حفظ الإعدادات ✅', 'success')
        return redirect(url_for('student.settings'))
    return render_template('student/settings.html', settings=s)

# ═══ PROFILE ═════════════════════════════════════════════════════════════════
@student.route('/profile')
@login_required
def profile():
    attempts         = current_user.attempts.filter(
        QuizAttempt.completed_at.isnot(None)).order_by(
        QuizAttempt.completed_at.desc()).all()
    badges           = current_user.badges.all()
    completed_lessons = current_user.progress.filter_by(completed=True).count()
    streak           = get_or_create_streak(current_user)
    return render_template('student/profile.html',
                           attempts=attempts, badges=badges,
                           completed_lessons=completed_lessons, streak=streak)

# ═══ LEADERBOARD — replaced with personal journey ═════════════════════════
@student.route('/journey')
@login_required
def journey():
    streak   = get_or_create_streak(current_user)
    missions = get_today_missions(current_user)
    sessions = FocusSession.query.filter_by(
        user_id=current_user.id, completed=True).order_by(
        FocusSession.started_at.desc()).limit(10).all()
    total_focus = sum(s.duration for s in
                      FocusSession.query.filter_by(
                          user_id=current_user.id, completed=True).all())
    completed_l  = current_user.progress.filter_by(completed=True).count()
    return render_template('student/journey.html',
                           streak=streak, missions=missions,
                           total_focus=total_focus//60,
                           completed_lessons=completed_l,
                           sessions=sessions)

# API: settings quick-toggle (dark mode etc.)
@student.route('/api/settings', methods=['POST'])
@login_required
def api_settings():
    s   = get_or_create_settings(current_user)
    key = request.json.get('key')
    val = request.json.get('value')
    if key in ('dark_mode','reduced_motion','sound_enabled','dyslexia_font'):
        setattr(s, key, bool(val))
        db.session.commit()
    return jsonify({'ok': True, key: val})
