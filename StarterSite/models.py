from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, current_user
from sqlalchemy.orm.attributes import flag_modified
from flask import request, redirect, flash, url_for, json
from flask_migrate import Migrate
from datetime import datetime
from flask_admin.contrib.sqla import ModelView


PAGE_TEMPLATE = '<h2 style="color:blue;">New Page</h2>'

db = SQLAlchemy()
backup = Migrate()


def LOAD_USER_SETTINGS():
    with open('static/user_settings.json', 'r') as S:
        return json.load(S)


session_user_association = db.Table('session_user_association', db.Model.metadata,
    db.Column('session_id', db.Integer, db.ForeignKey('session.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.String(32), default=datetime.now().strftime("%m/%d/%Y - %H:%M:%S"))
    uname = db.Column(db.String(16), nullable=False, unique=True)
    fname = db.Column(db.String(16), nullable=False)
    lname = db.Column(db.String(16), nullable=False)
    email = db.Column(db.String, nullable=False)
    sessions = db.relationship('Session', secondary=session_user_association, back_populates='users')
    passwd = db.Column(db.String, nullable=False)
    bio = db.Column(db.String(600), default='')
    is_admin = db.Column(db.Boolean(False))
    settings = db.Column(db.JSON, default=LOAD_USER_SETTINGS())
    pages = db.relationship('Page', back_populates='owner')

    def reset_settings(self):
        self.settings  = LOAD_USER_SETTINGS()
        db.session.commit()


class Page(db.Model):
    __tablename__ = 'page'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.String(32), default=datetime.now().strftime("%m/%d/%Y - %H:%M:%S"))
    title = db.Column(db.String(12))
    content = db.Column(db.String, default=PAGE_TEMPLATE)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', back_populates='pages')
    private = db.Column(db.Boolean(False))
    index = db.Column(db.Boolean(False))

    def update_content(self, content=None, pid=None):
        if content:
            self.content = content
            print(f'updated page ({self.title}) content')
        else:
            if pid is not None:
                try:
                    p = Page.query.filter_by(owner_id=current_user.id, id=pid).first()
                    self.content = p.content
                    print(f'copied content from page "{p.title}" to page "{self.title}')
                except Exception as e:
                    print(e)

            db.session.commit()


class Session(db.Model):
    __tablename__ = 'session'
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.String(32), default=datetime.now().strftime("%m/%d/%Y - %H:%M:%S"))
    users = db.relationship('User', secondary=session_user_association, back_populates='sessions')

    def remove(self, X, xid):
        options = {'user': self.users}

        sid = self.id

        to_remove = next((x for x in self.users if x.id == int(xid)), None)

        if to_remove is not None:
            options[X.lower()].remove(to_remove)

            db.session.commit()

        if len(self.users) < 1:
            db.session.delete(self)
            db.session.commit()

            print(f'session {sid} removed')


class UserView(ModelView):
    can_delete = True
    page_size = 50

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('restricted access. please login')
        return redirect(url_for('views.login', next=request.url))


class SessionView(ModelView):
    can_delete = True
    page_size = 50

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('restricted access. please login')
        return redirect(url_for('views.login', next=request.url))


class PageView(ModelView):
    can_delete = True
    page_size = 50

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('restricted access. please login')
        return redirect(url_for('views.login', next=request.url))