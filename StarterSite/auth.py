from flask import Blueprint, redirect, render_template, flash, url_for
from flask_login import current_user, logout_user, login_required

auth = Blueprint('auth', __name__)
from models import db


@auth.route('/logout')
@login_required
def logout():
    page_data = {
        'title': 'Logout',
        'block_names': [],
        'blocks': [],
        'msg': [],
        'style': current_user.settings['style']
    }
    uname = current_user.uname
    try:
        for s in current_user.sessions[1:]:
            s.remove('user', current_user.id)

        if len(current_user.sessions[0].users) < 1:
            db.session.delete(current_user.sessions[0])
            db.session.commit()
    except IndexError:
        pass

    logout_user()

    flash(f'Have a nice day, {uname}')

    return redirect(url_for('views.index'))


