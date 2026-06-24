from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.admin import admin
from app import db
from app.models import Game, GameItem, Subject
from app.admin.routes import admin_required


@admin.route('/games')
@admin_required
def games():
    sid   = request.args.get('subject_id', type=int)
    query = Game.query
    if sid:
        query = query.filter_by(subject_id=sid)
    all_games = query.order_by(Game.subject_id, Game.order).all()
    subjects  = Subject.query.filter_by(is_active=True).all()
    return render_template('admin/games.html', games=all_games,
                           subjects=subjects, selected_subject=sid)


@admin.route('/games/add', methods=['GET', 'POST'])
@admin_required
def add_game():
    subjects = Subject.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        g = Game(
            title=request.form['title'],
            description=request.form.get('description', ''),
            subject_id=int(request.form['subject_id']),
            game_type=request.form.get('game_type', 'match'),
            order=int(request.form.get('order', 0)),
            xp_reward=int(request.form.get('xp_reward', 15)),
        )
        db.session.add(g)
        db.session.commit()
        flash('تمت إضافة اللعبة ✅', 'success')
        return redirect(url_for('admin.game_items', gid=g.id))
    return render_template('admin/game_form.html', game=None, subjects=subjects)


@admin.route('/games/<int:gid>/edit', methods=['GET', 'POST'])
@admin_required
def edit_game(gid):
    g        = Game.query.get_or_404(gid)
    subjects = Subject.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        g.title       = request.form['title']
        g.description = request.form.get('description', '')
        g.subject_id  = int(request.form['subject_id'])
        g.game_type   = request.form.get('game_type', 'match')
        g.order       = int(request.form.get('order', 0))
        g.xp_reward   = int(request.form.get('xp_reward', 15))
        g.is_active   = 'is_active' in request.form
        db.session.commit()
        flash('تم تحديث اللعبة ✅', 'success')
        return redirect(url_for('admin.games'))
    return render_template('admin/game_form.html', game=g, subjects=subjects)


@admin.route('/games/<int:gid>/delete', methods=['POST'])
@admin_required
def delete_game(gid):
    g = Game.query.get_or_404(gid)
    db.session.delete(g)
    db.session.commit()
    flash('تم حذف اللعبة', 'warning')
    return redirect(url_for('admin.games'))


@admin.route('/games/<int:gid>/items')
@admin_required
def game_items(gid):
    g     = Game.query.get_or_404(gid)
    items = g.items.order_by(GameItem.order).all()
    return render_template('admin/game_items.html', game=g, items=items)


@admin.route('/games/<int:gid>/items/add', methods=['POST'])
@admin_required
def add_game_item(gid):
    g = Game.query.get_or_404(gid)
    item = GameItem(
        game_id=g.id,
        field1=request.form.get('field1', '').strip(),
        field2=request.form.get('field2', '').strip(),
        field3=request.form.get('field3', '').strip(),
        order=g.item_count(),
    )
    if not item.field1:
        flash('الحقل الأول مطلوب', 'danger')
        return redirect(url_for('admin.game_items', gid=gid))
    db.session.add(item)
    db.session.commit()
    flash('تمت الإضافة ✅', 'success')
    return redirect(url_for('admin.game_items', gid=gid))


@admin.route('/game-items/<int:iid>/delete', methods=['POST'])
@admin_required
def delete_game_item(iid):
    item = GameItem.query.get_or_404(iid)
    gid  = item.game_id
    db.session.delete(item)
    db.session.commit()
    flash('تم الحذف', 'warning')
    return redirect(url_for('admin.game_items', gid=gid))


@admin.route('/game-items/<int:iid>/edit', methods=['POST'])
@admin_required
def edit_game_item(iid):
    item        = GameItem.query.get_or_404(iid)
    item.field1 = request.form.get('field1', '').strip()
    item.field2 = request.form.get('field2', '').strip()
    item.field3 = request.form.get('field3', '').strip()
    db.session.commit()
    return jsonify({'ok': True})
