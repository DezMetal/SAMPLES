from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_user
from models import *


views = Blueprint('views', __name__)


@views.route('/')
def index():
    try:
        admin = User.query.filter_by(id=1, is_admin=True).first()
        p = Page.query.filter_by(index=True, owner=admin).first()
        page_data = {
            'title': None,
            'style': 'default',
            'content': None
        }
        return render_template('index.html', page=p, page_data=page_data)

    except Exception as e:
        return f'<h2 style="color:red;">an error has occurred..\n\n{e}\n</h2>'


@views.route('/login/', methods=['GET', 'POST'])
def login():
    user = User.query.filter_by(uname='D-Net').first()
    style = user.settings['style']

    if request.method == 'GET':
        page_data = {
            'title': 'Login',
            'block_names': [],
            'blocks': [],
            'style': style
        }

        return render_template('login.html', page_data=page_data, page=None)

    else:
        uname = request.form['uname']
        passwd = generate_password_hash(request.form['passwd'])
        user = User.query.filter_by(uname=uname).first()

        if not user or not check_password_hash(passwd, user.passwd):
            flash('Incorrect Login Info')
            return redirect('/login')

        login_user(user, remember=True)

        if user.is_authenticated:
            if len(current_user.sessions) == 0:
                s = Session()
                s.users.append(user)
                db.session.commit()

        page_data = {
            'title': 'Logged In',
            'block_names': [],
            'blocks': [],
            'style': 'default'
        }

        return redirect(url_for('views.index'))


@views.route('/register/', methods=['POST', 'GET'])
def register():
    user = User.query.filter_by(uname='D-Net').first()
    style = user.settings['style']

    page_data = {
        'title': 'Register',
        'block_names': [],
        'blocks': [],
        'style': style
    }

    if request.method == 'POST':
        email = request.form.get('email')
        uname = request.form.get('uname')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        pass0 = request.form.get('pass0')
        pass1 = request.form.get('pass1')

        email_exists = True if User.query.filter_by(email=email).first() is not None else False
        uname_exists = True if User.query.filter_by(uname=uname).first() is not None else False

        if email_exists:
            r = url_for('views.register')
            flash(f'someone using {email} already exists', category='error')

        elif uname_exists:
            r = url_for('views.register')
            flash(f'{uname} already exists', category='error')

        elif pass0 != pass1:
            r = url_for('views.register')
            flash('passwords must match', category='error')

        elif not 16 > len(pass0) > 7:
            r = url_for('views.register')
            flash('password must be 8 - 16 characters', category='error')

        elif not 16 > len(uname) > 4:
            r = url_for('views.register')
            flash('username must be 5 - 16 characters', category='error')

        elif len(email) > 50:
            r = url_for('views.register')
            flash('email must be less than 50 characters', category='error')

        else:
            user = User(uname=uname, fname=fname, lname=lname, passwd=pass1, email=email)
            db.session.add(user)
            user.reset_settings()
            r = url_for('views.login')
            p = Page(title=user.uname, owner=user, index=True)
            db.session.add(p)
            db.session.commit()
            flash('- your account has been created -')

        return redirect(r)

    return render_template('register.html', page_data=page_data, page=None)

