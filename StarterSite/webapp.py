from flask import Flask
from os import getcwd
from os.path import join, dirname, realpath, exists
from flask_login import LoginManager
from flask_ckeditor import CKEditor
from flask_admin import Admin as fAdmin


CWD = getcwd()
print(CWD)

db_name = 'DATABASE.db'
UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'static/uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
IMAGE_PATH = 'static/uploads/images/'
FILE_PATH = 'static/uploads/files/'


if __name__ == '__main__':
    def create_app():
        from models import(db, backup, User, UserView, Session, SessionView, Page, PageView)
        app = Flask(__name__)

        app.config['SECRET_KEY'] = 'thisisatest'

        app.config['MAX_CONTENT_LENGTH'] = 25 * 1000 * 1000
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        app.config['CKEDITOR_SERVE_LOCAL'] = True
        app.config['CKEDITOR_ENABLE_CODESNIPPET'] = True
        app.config['CKEDITOR_EXTRA_PLUGINS'] = ['autogrow', 'widget', 'widgetselection', 'clipboard', 'lineutils',
                                                'html5audio']
        ckeditor = CKEditor()
        ckeditor.init_app(app)

        app.config['FLASK_ADMIN_SWATCH'] = 'cyborg'

        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{CWD}/{db_name}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)

        Admin = fAdmin(app, name='Admin', template_mode='bootstrap3')
        Admin.add_view(UserView(User, db.session))
        Admin.add_view(PageView(Page, db.session))
        Admin.add_view(SessionView(Session, db.session))

        from views import views
        from auth import auth

        app.register_blueprint(views, url_prefix='/')
        app.register_blueprint(auth, url_prefix='/')


        print('creating backup..')
        with app.app_context():
            if not exists(f'{CWD}/{db_name}'):
                print('creating database..')
                db.create_all()

            backup.init_app(app, db, render_as_batch=True)
            if not User.query.get(1):
                admin = User(uname='D-Net', fname='D', lname='Net', passwd='password', email='d.w.clay94@gmail.com', is_admin=True)
                db.session.add(admin)
                db.session.commit()
                page = Page(owner=admin, title='D-Net Live', content='<div class="pure-u-1"><h2>This Is A Test..</h2></div>', index=True)
                db.session.add(page)
                db.session.commit()

        login_manager = LoginManager()
        login_manager.login_view = 'views.login'
        login_manager.init_app(app)

        @login_manager.user_loader
        def load_user(ID):
            return User.query.get(int(ID))

        return app

    app = create_app()
    app.run('0.0.0.0', debug=True)
