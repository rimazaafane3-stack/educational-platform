"""
seed.py — تعبئة قاعدة البيانات ببيانات تجريبية لسنة أولى متوسط
Run: python run.py seed  OR  python seed.py
"""

from app import create_app, db
from app.models import (User, Subject, Lesson, Video,
                        Quiz, Question, Choice, Badge, UserBadge)


def seed_database():
    app = create_app()
    with app.app_context():
        db.create_all()

        # ── 1. Admin ────────────────────────────────────────────
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin', email='admin@platform.dz',
                full_name='مشرف النظام', role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print('✅ تم إنشاء حساب المشرف: admin / admin123')

        # ── 2. Demo Student ─────────────────────────────────────
        if not User.query.filter_by(username='طالب').first():
            student = User(
                username='طالب', email='student@platform.dz',
                full_name='طالب تجريبي', role='student', points=45
            )
            student.set_password('123456')
            db.session.add(student)
            print('✅ تم إنشاء حساب الطالب: طالب / 123456')

        db.session.commit()

        # ── 3. Badges ───────────────────────────────────────────
        badges_data = [
            ('مرحباً بك!',       'شارة الترحيب للأعضاء الجدد',         '👋', '#6C63FF', 'welcome',       0),
            ('أول خطوة',         'أكملت درسك الأول',                    '📖', '#10B981', 'first_lesson',  0),
            ('المتحدي',          'أجريت أول امتحان',                    '🎯', '#3B82F6', 'first_quiz',    0),
            ('نجم الكمال',        'حصلت على 100% في امتحان',             '🌟', '#F59E0B', 'perfect_score', 0),
            ('جامع النقاط',      'جمعت 100 نقطة',                       '💎', '#8B5CF6', '',              100),
            ('المثابر',          'جمعت 300 نقطة',                       '🚀', '#EF4444', '',              300),
        ]
        for name, desc, icon, color, cond, pts in badges_data:
            if not Badge.query.filter_by(name=name).first():
                db.session.add(Badge(name=name, description=desc, icon=icon,
                                     color=color, condition=cond, points_required=pts))
        db.session.commit()
        print('✅ تم إضافة الشارات')

        # ── 4. Subjects ─────────────────────────────────────────
        subjects_data = [
            ('الرياضيات',    'Mathématiques', 'تعلم الأعداد والعمليات الحسابية بطريقة ممتعة',   '🔢', '#6C63FF', '#EEF2FF', 1),
            ('العلوم',        'Sciences',      'اكتشف أسرار الطبيعة والعلوم',                    '🔬', '#10B981', '#ECFDF5', 2),
            ('اللغة العربية','Langue Arabe',  'تعلم قواعد اللغة العربية الجميلة',               '📝', '#F59E0B', '#FFFBEB', 3),
            ('التاريخ',      'Histoire',      'رحلة في عالم التاريخ والحضارات',                 '🏛️', '#EF4444', '#FEF2F2', 4),
            ('الجغرافيا',    'Géographie',    'استكشف العالم والخرائط',                         '🌍', '#3B82F6', '#EFF6FF', 5),
            ('التربية الإسلامية', 'Éducation Islamique', 'قيم ومبادئ الإسلام الحنيف',          '☪️', '#8B5CF6', '#F5F3FF', 6),
        ]
        subjects = {}
        for name_ar, name, desc, icon, color, bg, order in subjects_data:
            if not Subject.query.filter_by(name=name).first():
                s = Subject(name=name, name_ar=name_ar, description=desc,
                            icon=icon, color=color, bg_color=bg, order=order)
                db.session.add(s)
                db.session.flush()
                subjects[name] = s
            else:
                subjects[name] = Subject.query.filter_by(name=name).first()
        db.session.commit()
        print('✅ تم إضافة المواد الدراسية')

        # ── 5. Lessons ──────────────────────────────────────────
        math = subjects.get('Mathématiques')
        sci  = subjects.get('Sciences')
        ar   = subjects.get('Langue Arabe')

        if math and not Lesson.query.filter_by(subject_id=math.id).first():
            lessons_math = [
                ('الأعداد الطبيعية',
                 '''<h2>🔢 الأعداد الطبيعية</h2>
<p>الأعداد الطبيعية هي الأعداد التي نستخدمها في العد اليومي: <strong>0، 1، 2، 3، 4، 5، ...</strong></p>
<blockquote>الأعداد الطبيعية تبدأ من الصفر ولا تنتهي أبداً!</blockquote>
<h3>📌 خصائص الأعداد الطبيعية</h3>
<ul>
  <li>أصغر عدد طبيعي هو <strong>الصفر (0)</strong></li>
  <li>لا يوجد أكبر عدد طبيعي</li>
  <li>كل عدد طبيعي يأتي بعده عدد أكبر منه بـ 1</li>
</ul>
<h3>🎯 أمثلة من الحياة</h3>
<table>
  <tr><th>الموقف</th><th>العدد الطبيعي</th></tr>
  <tr><td>عدد الكتب في حقيبتك</td><td>5</td></tr>
  <tr><td>عدد أصابع يدك</td><td>10</td></tr>
  <tr><td>عدد أيام الأسبوع</td><td>7</td></tr>
</table>''',
                 'تعرف على الأعداد الطبيعية وخصائصها الأساسية', 1, 'easy', 15),

                ('الجمع والطرح',
                 '''<h2>➕ الجمع والطرح</h2>
<p>الجمع هو إضافة عددين للحصول على مجموعهما، والطرح هو إيجاد الفرق بين عددين.</p>
<h3>🎯 قاعدة الجمع</h3>
<blockquote>العدد الأول + العدد الثاني = المجموع</blockquote>
<p>مثال: <strong>35 + 47 = 82</strong></p>
<h3>🎯 قاعدة الطرح</h3>
<blockquote>العدد الكبير - العدد الصغير = الفرق</blockquote>
<p>مثال: <strong>93 - 28 = 65</strong></p>
<h3>💡 خدعة ذكية للجمع السريع</h3>
<ul>
  <li>جمع الآحاد أولاً، ثم العشرات</li>
  <li>إذا تجاوز مجموع الآحاد 9، نحمل 1 إلى العشرات</li>
</ul>''',
                 'تعلم عمليتي الجمع والطرح مع أمثلة تطبيقية', 2, 'easy', 20),

                ('الضرب والقسمة',
                 '''<h2>✖️ الضرب والقسمة</h2>
<p>الضرب هو جمع متكرر، والقسمة هي التوزيع المتساوي.</p>
<h3>جدول الضرب — أساس الحساب</h3>
<table>
  <tr><th>×</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th></tr>
  <tr><th>2</th><td>2</td><td>4</td><td>6</td><td>8</td><td>10</td></tr>
  <tr><th>3</th><td>3</td><td>6</td><td>9</td><td>12</td><td>15</td></tr>
  <tr><th>4</th><td>4</td><td>8</td><td>12</td><td>16</td><td>20</td></tr>
  <tr><th>5</th><td>5</td><td>10</td><td>15</td><td>20</td><td>25</td></tr>
</table>
<h3>💡 القسمة</h3>
<blockquote>القسمة هي عكس الضرب: 20 ÷ 4 = 5 لأن 4 × 5 = 20</blockquote>''',
                 'احفظ جدول الضرب وتعلم القسمة بسهولة', 3, 'medium', 25),
            ]
            for title, content, summary, order, diff, dur in lessons_math:
                db.session.add(Lesson(subject_id=math.id, title=title,
                                      content=content, summary=summary,
                                      order=order, difficulty=diff, duration=dur))
            print('✅ تم إضافة دروس الرياضيات')

        if sci and not Lesson.query.filter_by(subject_id=sci.id).first():
            db.session.add(Lesson(
                subject_id=sci.id,
                title='المادة وخصائصها',
                content='''<h2>🔬 المادة وخصائصها</h2>
<p>المادة هي كل شيء يشغل حيزاً من الفضاء وله كتلة.</p>
<h3>حالات المادة الثلاث</h3>
<ul>
  <li>🧊 <strong>الصلبة</strong> — شكل وحجم ثابتان (مثال: الجليد، الخشب)</li>
  <li>💧 <strong>السائلة</strong> — حجم ثابت لكن الشكل يتغير (مثال: الماء، العصير)</li>
  <li>💨 <strong>الغازية</strong> — الشكل والحجم يتغيران (مثال: الهواء، البخار)</li>
</ul>
<h3>🌡️ التحولات بين الحالات</h3>
<table>
  <tr><th>التحول</th><th>السبب</th><th>مثال</th></tr>
  <tr><td>الانصهار</td><td>تسخين الصلب</td><td>ذوبان الجليد</td></tr>
  <tr><td>التجمد</td><td>تبريد السائل</td><td>تجمد الماء</td></tr>
  <tr><td>التبخر</td><td>تسخين السائل</td><td>غليان الماء</td></tr>
</table>''',
                summary='تعرف على المادة وحالاتها الثلاث',
                order=1, difficulty='easy', duration=20
            ))
            print('✅ تم إضافة دروس العلوم')

        if ar and not Lesson.query.filter_by(subject_id=ar.id).first():
            db.session.add(Lesson(
                subject_id=ar.id,
                title='أقسام الكلام',
                content='''<h2>📝 أقسام الكلام في اللغة العربية</h2>
<p>الكلام في اللغة العربية ثلاثة أقسام:</p>
<h3>1️⃣ الاسم</h3>
<blockquote>الاسم هو كل كلمة تدل على إنسان أو حيوان أو نبات أو جماد أو مكان أو زمان.</blockquote>
<p>أمثلة: <strong>محمد، كتاب، مدرسة، يوم</strong></p>
<h3>2️⃣ الفعل</h3>
<blockquote>الفعل هو كل كلمة تدل على حدث في زمن معين.</blockquote>
<p>أمثلة: <strong>كتب، يدرس، سيذهب</strong></p>
<h3>3️⃣ الحرف</h3>
<blockquote>الحرف هو كل كلمة لا معنى لها إلا مع غيرها.</blockquote>
<p>أمثلة: <strong>في، على، من، إلى، و، ف</strong></p>
<h3>📊 جدول المقارنة</h3>
<table>
  <tr><th>القسم</th><th>السؤال</th><th>أمثلة</th></tr>
  <tr><td>اسم</td><td>من؟ ما؟</td><td>طالب، قلم، مدينة</td></tr>
  <tr><td>فعل</td><td>ماذا فعل؟</td><td>قرأ، يكتب، سيلعب</td></tr>
  <tr><td>حرف</td><td>—</td><td>في، على، من</td></tr>
</table>''',
                summary='تعلم أقسام الكلام: الاسم والفعل والحرف',
                order=1, difficulty='easy', duration=20
            ))
            print('✅ تم إضافة دروس اللغة العربية')

        db.session.commit()

        # ── 6. Videos ───────────────────────────────────────────
        if math and not Video.query.filter_by(subject_id=math.id).first():
            videos = [
                (math.id, 'شرح الأعداد الطبيعية كاملاً',
                 'شرح مبسط للأعداد الطبيعية مع أمثلة',
                 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'dQw4w9WgXcQ', '12:30', 1),
                (math.id, 'جدول الضرب بطريقة ممتعة',
                 'تعلم جدول الضرب مع أغنية ممتعة',
                 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'dQw4w9WgXcQ', '8:45', 2),
                (sci.id if sci else math.id, 'تجربة المادة وحالاتها',
                 'تجربة علمية رائعة لحالات المادة',
                 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'dQw4w9WgXcQ', '15:20', 1),
            ]
            for sid, title, desc, url, vid_id, dur, order in videos:
                db.session.add(Video(subject_id=sid, title=title,
                                     description=desc, youtube_url=url,
                                     youtube_id=vid_id, duration=dur, order=order))
            db.session.commit()
            print('✅ تم إضافة الفيديوهات')

        # ── 7. Quizzes + Questions ──────────────────────────────
        if math and not Quiz.query.filter_by(subject_id=math.id).first():
            quiz = Quiz(
                subject_id=math.id,
                title='امتحان الأعداد الطبيعية',
                description='اختبر معلوماتك في الأعداد الطبيعية والعمليات الحسابية',
                time_limit=15,
                pass_score=60,
                order=1
            )
            db.session.add(quiz)
            db.session.flush()

            questions_data = [
                ('ما هو أصغر عدد طبيعي؟', 'mcq',
                 [('الصفر 0', True), ('الواحد 1', False), ('المئة 100', False), ('لا يوجد', False)],
                 'الصفر هو أصغر عدد طبيعي', 1),

                ('ما ناتج: 35 + 47 ؟', 'mcq',
                 [('72', False), ('82', True), ('92', False), ('62', False)],
                 '35 + 47 = 82 نجمع الآحاد: 5+7=12 نكتب 2 ونحمل 1، ثم العشرات: 3+4+1=8', 1),

                ('ما ناتج: 8 × 7 ؟', 'mcq',
                 [('54', False), ('48', False), ('56', True), ('63', False)],
                 '8 × 7 = 56', 1),

                ('الأعداد الطبيعية لها نهاية؟', 'true_false',
                 [('صحيح', False), ('خطأ', True)],
                 'الأعداد الطبيعية لا تنتهي، يمكن الزيادة عليها إلى ما لا نهاية', 1),

                ('ما ناتج: 120 ÷ 4 ؟', 'mcq',
                 [('30', True), ('40', False), ('24', False), ('34', False)],
                 '120 ÷ 4 = 30 لأن 4 × 30 = 120', 2),
            ]

            for i, (text, qtype, choices, expl, pts) in enumerate(questions_data):
                q = Question(quiz_id=quiz.id, text=text, q_type=qtype,
                             explanation=expl, points=pts, order=i+1)
                db.session.add(q)
                db.session.flush()
                for j, (ctext, is_correct) in enumerate(choices):
                    db.session.add(Choice(question_id=q.id, text=ctext,
                                          is_correct=is_correct, order=j))

            db.session.commit()
            print('✅ تم إضافة امتحان الرياضيات مع الأسئلة')

        if sci and not Quiz.query.filter_by(subject_id=sci.id).first():
            quiz2 = Quiz(
                subject_id=sci.id,
                title='امتحان المادة وخصائصها',
                description='اختبر فهمك لحالات المادة',
                time_limit=10,
                pass_score=60,
                order=1
            )
            db.session.add(quiz2)
            db.session.flush()

            sci_questions = [
                ('كم عدد حالات المادة؟', 'mcq',
                 [('2', False), ('3', True), ('4', False), ('5', False)],
                 'للمادة ثلاث حالات: صلبة وسائلة وغازية', 1),

                ('الماء في درجة حرارة الغليان يتحول إلى؟', 'mcq',
                 [('جليد', False), ('بخار', True), ('هواء', False), ('دخان', False)],
                 'الماء المغلي يتحول إلى بخار ماء (حالة غازية)', 1),

                ('الجليد يملك شكلاً ثابتاً؟', 'true_false',
                 [('صحيح', True), ('خطأ', False)],
                 'الجليد مادة صلبة لذلك له شكل ثابت', 1),
            ]

            for i, (text, qtype, choices, expl, pts) in enumerate(sci_questions):
                q = Question(quiz_id=quiz2.id, text=text, q_type=qtype,
                             explanation=expl, points=pts, order=i+1)
                db.session.add(q)
                db.session.flush()
                for j, (ctext, is_correct) in enumerate(choices):
                    db.session.add(Choice(question_id=q.id, text=ctext,
                                          is_correct=is_correct, order=j))

            db.session.commit()
            print('✅ تم إضافة امتحان العلوم مع الأسئلة')

        print('\n🎉 تمت تعبئة قاعدة البيانات بنجاح!')
        print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
        print('👤 المشرف : admin  /  admin123')
        print('👤 الطالب : طالب  /  123456')
        print('🌐 ابدأ التشغيل: python run.py')
        print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')


if __name__ == '__main__':
    seed_database()


def seed_adhd():
    """Seed ADHD-specific data: daily missions + learning chunks"""
    from app import create_app, db
    from app.models import DailyMission, LearningChunk, Lesson

    app = create_app()
    with app.app_context():

        # ── Daily Missions ────────────────────────────────────
        missions_data = [
            ('أكمل درساً واحداً',   'ادخل لأي درس وأكمله',         'lesson',  1, 20, '📖'),
            ('شاهد فيديو تعليمي',   'شاهد أي فيديو من المنصة',     'video',   1, 15, '🎥'),
            ('أجب على 3 أسئلة',     'أجب في أي امتحان',            'quiz',    1, 25, '🧠'),
            ('تعلّم 3 أيام متواصلة','حافظ على سلسلتك',             'streak',  1, 30, '🔥'),
        ]
        for title, desc, mtype, target, xp, icon in missions_data:
            if not DailyMission.query.filter_by(title=title).first():
                db.session.add(DailyMission(
                    title=title, description=desc, mission_type=mtype,
                    target_count=target, xp_reward=xp, icon=icon
                ))
        db.session.commit()
        print('✅ Daily missions added')

        # ── Learning Chunks for first lesson ─────────────────
        lesson = Lesson.query.first()
        if lesson and lesson.chunks.count() == 0:
            chunks = [
                ('مقدمة 👋',       lesson.content[:200] + '...' if len(lesson.content) > 200 else lesson.content,
                 'text', '📖', 0),
                ('النقطة الأساسية 🎯', '<p>الفكرة الرئيسية في هذا الدرس: <strong>' + lesson.title + '</strong></p><p>ركّز على هذه الفكرة وستفهم الباقي بسهولة.</p>',
                 'tip', '💡', 1),
                ('ملخص ⚡',         '<p>في هذا الدرس تعلمنا:</p><ul><li>' + lesson.title + '</li><li>المفاهيم الأساسية</li><li>التطبيق العملي</li></ul>',
                 'summary', '⚡', 2),
            ]
            for title, content, ctype, emoji, order in chunks:
                db.session.add(LearningChunk(
                    lesson_id=lesson.id, title=title, content=content,
                    chunk_type=ctype, emoji=emoji, order=order
                ))
            db.session.commit()
            print('✅ Learning chunks added to first lesson')


if __name__ == '__main__':
    seed_database()
    seed_adhd()
