/**
 * edu_games.js — ألعاب تعليمية مرتبطة بمحتوى الدرس
 * مصممة لتلاميذ سن 12 — تفاعلية وتربوية
 */

// ══════════════════════════════════════════════════════════════
//  CONTENT EXTRACTOR — يستخرج المعلومات من محتوى الدرس
// ══════════════════════════════════════════════════════════════

class LessonContentExtractor {
  constructor(htmlContent) {
    this.tmp = document.createElement('div');
    this.tmp.innerHTML = htmlContent;
    this._terms      = null;
    this._sentences  = null;
    this._paragraphs = null;
  }

  // استخراج المصطلحات المهمة (النصوص الغامقة والعناوين)
  getKeyTerms() {
    if (this._terms) return this._terms;
    const terms = [];
    const seen  = new Set();

    // من العناوين
    this.tmp.querySelectorAll('h1,h2,h3,h4').forEach(el => {
      const t = el.textContent.trim();
      if (t.length >= 3 && t.length <= 50 && !seen.has(t)) {
        seen.add(t);
        terms.push({ term: t, type: 'heading', context: '' });
      }
    });

    // من النص الغامق
    this.tmp.querySelectorAll('strong, b').forEach(el => {
      const t = el.textContent.trim();
      if (t.length >= 2 && t.length <= 40 && !seen.has(t)) {
        // ابحث عن الجملة المحيطة كسياق
        const parent = el.closest('p,li,td') || el.parentElement;
        const ctx    = parent ? parent.textContent.trim().substring(0, 120) : '';
        seen.add(t);
        terms.push({ term: t, type: 'bold', context: ctx });
      }
    });

    // من خلايا الجداول
    this.tmp.querySelectorAll('table').forEach(table => {
      const rows = table.querySelectorAll('tr');
      rows.forEach(row => {
        const cells = row.querySelectorAll('td,th');
        if (cells.length >= 2) {
          const key = cells[0].textContent.trim();
          const val = cells[1].textContent.trim();
          if (key && val && key.length < 40 && !seen.has(key)) {
            seen.add(key);
            terms.push({ term: key, type: 'table', context: val });
          }
        }
      });
    });

    this._terms = terms.filter(t => t.term.length >= 2);
    return this._terms;
  }

  // استخراج الجمل المفيدة
  getSentences() {
    if (this._sentences) return this._sentences;
    const text  = this.tmp.textContent;
    const sents = text.split(/[.!؟\n]+/).map(s => s.trim()).filter(s => s.length > 20 && s.length < 200);
    this._sentences = [...new Set(sents)];
    return this._sentences;
  }

  // توليد أسئلة صح/خطأ من المحتوى
  generateTrueFalseQuestions() {
    const terms     = this.getKeyTerms();
    const sentences = this.getSentences();
    const questions = [];

    // أسئلة من الجمل الحقيقية
    sentences.slice(0, 6).forEach(s => {
      questions.push({ text: s, answer: true,
        feedback: '✅ هذه المعلومة صحيحة من الدرس!' });
    });

    // أسئلة خاطئة — نعكس مصطلحين
    if (terms.length >= 2) {
      for (let i = 0; i < Math.min(3, terms.length - 1); i++) {
        const t1 = terms[i].term;
        const t2 = terms[i + 1].term;
        const s  = sentences[i % sentences.length] || '';
        if (s.includes(t1)) {
          questions.push({
            text: s.replace(t1, t2),
            answer: false,
            feedback: `❌ الصحيح هو "${t1}" وليس "${t2}"`
          });
        }
      }
    }

    return questions.sort(() => Math.random() - 0.5).slice(0, 8);
  }

  // توليد أسئلة أكمل الفراغ
  generateFillBlanks() {
    const terms  = this.getKeyTerms().filter(t => t.context.includes(t.term));
    const blanks = [];

    terms.slice(0, 6).forEach(item => {
      const sentence = item.context;
      const word     = item.term;
      if (sentence && sentence.includes(word) && word.length >= 3) {
        const masked = sentence.replace(word, '___________');
        blanks.push({ sentence: masked, answer: word, hint: word[0] + '...' });
      }
    });

    return blanks;
  }

  // بطاقات المطابقة — مصطلح ↔ تعريف
  generateMatchPairs() {
    const terms = this.getKeyTerms().filter(t => t.context.length > 5);
    return terms.slice(0, 6).map(t => ({
      term:       t.term,
      definition: t.context.substring(0, 80) + (t.context.length > 80 ? '...' : ''),
    }));
  }
}


// ══════════════════════════════════════════════════════════════
//  GAME 1: صح أم خطأ — True/False Race
// ══════════════════════════════════════════════════════════════

class TrueFalseGame {
  constructor(container, questions, onScore) {
    this.container = container;
    this.questions = questions;
    this.onScore   = onScore;
    this.idx       = 0;
    this.score     = 0;
    this.streak    = 0;
    this.timer     = null;
    this.timeLeft  = 10;
  }

  start() {
    this.idx = 0; this.score = 0; this.streak = 0;
    this.showQuestion();
  }

  showQuestion() {
    clearInterval(this.timer);
    if (this.idx >= this.questions.length) {
      this.showResult(); return;
    }
    const q = this.questions[this.idx];
    this.timeLeft = 10;

    this.container.innerHTML = `
      <div class="eg-header">
        <span class="eg-progress">${this.idx + 1} / ${this.questions.length}</span>
        <span class="eg-score">⭐ ${this.score}</span>
        <span class="eg-streak" id="egStreak">${this.streak > 1 ? '🔥 × ' + this.streak : ''}</span>
      </div>
      <div class="eg-timer-bar"><div class="eg-timer-fill" id="egTimerFill" style="width:100%"></div></div>
      <div class="eg-timer-num" id="egTimerNum">⏱️ ${this.timeLeft}</div>
      <div class="eg-question">${q.text}</div>
      <div class="eg-tf-btns">
        <button class="eg-btn eg-true"  onclick="window._tfGame.answer(true)">✅ صحيح</button>
        <button class="eg-btn eg-false" onclick="window._tfGame.answer(false)">❌ خطأ</button>
      </div>
      <div class="eg-feedback" id="egFeedback"></div>`;

    this.timer = setInterval(() => {
      this.timeLeft--;
      const fill = document.getElementById('egTimerFill');
      const num  = document.getElementById('egTimerNum');
      if (fill) fill.style.width = (this.timeLeft / 10 * 100) + '%';
      if (num)  num.textContent = '⏱️ ' + this.timeLeft;
      if (fill) fill.style.background = this.timeLeft <= 3 ? '#EF4444' : '#6C63FF';
      if (this.timeLeft <= 0) { clearInterval(this.timer); this.answer(null); }
    }, 1000);

    window._tfGame = this;
  }

  answer(val) {
    clearInterval(this.timer);
    const q    = this.questions[this.idx];
    const fb   = document.getElementById('egFeedback');
    const btns = this.container.querySelectorAll('.eg-btn');
    btns.forEach(b => b.disabled = true);

    if (val === null) {
      if (fb) fb.innerHTML = `<span class="eg-wrong">⏰ انتهى الوقت! ${q.feedback}</span>`;
      this.streak = 0;
    } else if (val === q.answer) {
      const pts = this.streak >= 2 ? 15 : 10;
      this.score  += pts;
      this.streak += 1;
      if (fb) fb.innerHTML = `<span class="eg-correct">🎉 ممتاز! +${pts} نقطة${this.streak >= 2 ? ' 🔥' : ''}</span>`;
      if (window.showToast) window.showToast(`+${pts} نقاط!`, '⭐');
    } else {
      this.streak = 0;
      if (fb) fb.innerHTML = `<span class="eg-wrong">${q.feedback}</span>`;
    }

    this.idx++;
    setTimeout(() => this.showQuestion(), 1800);
  }

  showResult() {
    const pct = Math.round(this.score / (this.questions.length * 10) * 100);
    const msg = pct >= 80 ? '🏆 ممتاز!' : pct >= 60 ? '👍 جيد!' : '💪 حاول مرة أخرى!';
    this.container.innerHTML = `
      <div class="eg-result">
        <div class="eg-result-icon">${msg}</div>
        <div class="eg-result-score">${this.score} نقطة</div>
        <div class="eg-result-pct">${pct}%</div>
        <button class="eg-restart-btn" onclick="window._tfGame.start()">🔄 العب مجدداً</button>
      </div>`;
    if (this.onScore) this.onScore(this.score);
  }
}


// ══════════════════════════════════════════════════════════════
//  GAME 2: أكمل الفراغ — Fill in the Blank
// ══════════════════════════════════════════════════════════════

class FillBlankGame {
  constructor(container, blanks, onScore) {
    this.container = container;
    this.blanks    = blanks;
    this.onScore   = onScore;
    this.idx       = 0;
    this.score     = 0;
    this.lives     = 3;
  }

  start() {
    this.idx = 0; this.score = 0; this.lives = 3;
    this.showBlank();
  }

  showBlank() {
    if (this.idx >= this.blanks.length || this.lives <= 0) {
      this.showResult(); return;
    }
    const b = this.blanks[this.idx];
    const hearts = '❤️'.repeat(this.lives) + '🖤'.repeat(3 - this.lives);

    this.container.innerHTML = `
      <div class="eg-header">
        <span class="eg-progress">${this.idx + 1} / ${this.blanks.length}</span>
        <span class="eg-score">⭐ ${this.score}</span>
        <span>${hearts}</span>
      </div>
      <div class="eg-question" style="font-size:1.05rem;line-height:1.8;">${b.sentence}</div>
      <div class="eg-hint">💡 تلميح: الكلمة تبدأ بـ <strong>${b.hint}</strong></div>
      <div class="eg-input-row">
        <input type="text" id="fillInput" class="eg-input" placeholder="اكتب الكلمة الناقصة..."
               onkeyup="if(event.key==='Enter')window._fbGame.check()"
               autocomplete="off" autocorrect="off" spellcheck="false">
        <button class="eg-submit-btn" onclick="window._fbGame.check()">تحقق ✓</button>
      </div>
      <div class="eg-feedback" id="egFeedback"></div>`;

    document.getElementById('fillInput')?.focus();
    window._fbGame = this;
  }

  check() {
    const input = document.getElementById('fillInput');
    const val   = input ? input.value.trim() : '';
    const b     = this.blanks[this.idx];
    const fb    = document.getElementById('egFeedback');

    // مقارنة مرنة
    const normalize = s => s.replace(/[\u064B-\u065F]/g, '').toLowerCase().trim();
    const correct   = normalize(val) === normalize(b.answer);

    if (correct) {
      this.score += 15;
      if (fb) fb.innerHTML = `<span class="eg-correct">✅ أحسنت! الإجابة: <strong>${b.answer}</strong> (+15 نقطة)</span>`;
      if (window.showToast) window.showToast('+15 نقطة!', '✅');
      this.idx++;
      setTimeout(() => this.showBlank(), 1500);
    } else if (val) {
      this.lives--;
      if (fb) {
        if (this.lives <= 0) {
          fb.innerHTML = `<span class="eg-wrong">❌ الإجابة الصحيحة: <strong>${b.answer}</strong></span>`;
          setTimeout(() => { this.idx++; this.lives = 3; this.showBlank(); }, 2000);
        } else {
          fb.innerHTML = `<span class="eg-wrong">❌ حاول مرة أخرى (${this.lives} محاولات متبقية)</span>`;
        }
      }
    }
  }

  showResult() {
    this.container.innerHTML = `
      <div class="eg-result">
        <div class="eg-result-icon">${this.score >= this.blanks.length * 10 ? '🏆' : '📝'}</div>
        <div class="eg-result-score">${this.score} نقطة</div>
        <button class="eg-restart-btn" onclick="window._fbGame.start()">🔄 حاول مجدداً</button>
      </div>`;
    if (this.onScore) this.onScore(this.score);
  }
}


// ══════════════════════════════════════════════════════════════
//  GAME 3: بطاقات المطابقة — Match Cards
// ══════════════════════════════════════════════════════════════

class MatchGame {
  constructor(container, pairs, onScore) {
    this.container = container;
    this.pairs     = pairs.slice(0, 5);
    this.onScore   = onScore;
    this.selected  = null;
    this.matched   = 0;
    this.attempts  = 0;
    this.score     = 0;
  }

  start() {
    this.selected = null; this.matched = 0; this.attempts = 0; this.score = 0;
    this.render();
  }

  render() {
    // خلط البطاقتين بشكل منفصل
    const terms = this.pairs.map((p, i) => ({ id: i, text: p.term,       side: 'term' }));
    const defs  = this.pairs.map((p, i) => ({ id: i, text: p.definition, side: 'def'  }));
    const left  = [...terms].sort(() => Math.random() - 0.5);
    const right = [...defs ].sort(() => Math.random() - 0.5);

    this.container.innerHTML = `
      <div class="eg-header">
        <span>🎯 اربط المصطلح بتعريفه</span>
        <span class="eg-score">⭐ ${this.score}</span>
      </div>
      <div class="eg-match-grid">
        <div class="eg-match-col" id="colLeft">
          ${left.map(c => `<button class="eg-match-card term" data-id="${c.id}" data-side="term"
            onclick="window._matchGame.select(this)">${c.text}</button>`).join('')}
        </div>
        <div class="eg-match-col" id="colRight">
          ${right.map(c => `<button class="eg-match-card def" data-id="${c.id}" data-side="def"
            onclick="window._matchGame.select(this)">${c.text}</button>`).join('')}
        </div>
      </div>
      <div class="eg-feedback" id="egFeedback"></div>`;

    window._matchGame = this;
  }

  select(btn) {
    if (btn.disabled || btn.classList.contains('matched')) return;

    if (!this.selected) {
      btn.classList.add('active');
      this.selected = btn;
    } else {
      // نفس الجانب — ألغ الأول
      if (this.selected.dataset.side === btn.dataset.side) {
        this.selected.classList.remove('active');
        this.selected = btn;
        btn.classList.add('active');
        return;
      }

      this.attempts++;
      const id1 = this.selected.dataset.id;
      const id2 = btn.dataset.id;
      const fb  = document.getElementById('egFeedback');

      if (id1 === id2) {
        // صحيح!
        this.score += 20;
        this.matched++;
        [this.selected, btn].forEach(b => {
          b.classList.remove('active');
          b.classList.add('matched');
          b.disabled = true;
        });
        if (fb) fb.innerHTML = `<span class="eg-correct">✅ صحيح! +20 نقطة</span>`;
        if (window.showToast) window.showToast('+20 نقطة!', '🎯');

        if (this.matched === this.pairs.length) {
          setTimeout(() => this.showResult(), 800);
        }
      } else {
        // خطأ
        [this.selected, btn].forEach(b => b.classList.add('wrong'));
        if (fb) fb.innerHTML = `<span class="eg-wrong">❌ ليس هذا — حاول مجدداً</span>`;
        setTimeout(() => {
          [this.selected, btn].forEach(b => {
            b.classList.remove('active', 'wrong');
          });
        }, 900);
      }

      this.selected = null;
    }
  }

  showResult() {
    const acc = Math.round((this.pairs.length / this.attempts) * 100);
    this.container.innerHTML = `
      <div class="eg-result">
        <div class="eg-result-icon">🎯</div>
        <div class="eg-result-score">${this.score} نقطة</div>
        <div style="font-size:.9rem;color:var(--adhd-muted);">دقة ${acc}% — ${this.attempts} محاولة</div>
        <button class="eg-restart-btn" onclick="window._matchGame.start()">🔄 العب مجدداً</button>
      </div>`;
    if (this.onScore) this.onScore(this.score);
  }
}


// ══════════════════════════════════════════════════════════════
//  EXPORT
// ══════════════════════════════════════════════════════════════
window.LessonContentExtractor = LessonContentExtractor;
window.TrueFalseGame          = TrueFalseGame;
window.FillBlankGame          = FillBlankGame;
window.MatchGame              = MatchGame;
