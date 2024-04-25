from flask import Flask, redirect, url_for, flash
from flask_login import LoginManager
from flask_admin import Admin
from blog.admin_models import get_all_admin_models
from .models import get_model, db, migrate

def create_app(config, mode):
    '''
    플라스크의 팩토리 지정함수(app 객체 생성 함수)
    app 객체를 생성할 때 전역으로 접근하지 못하게 함 
    즉, 순환 참조 방지
    '''
    app = Flask(__name__)
    app.config.from_object(config) # 환경변수 설정 코드
    app.secret_key = config.SECRET_KEYS[f'{mode}_SECRET_KEY']
    app.config['mode'] = mode.lower()
    db.init_app(app)
    migrate.init_app(app, db)
    with app.app_context():
        # db.Model 상속한 모든 클래스 추적해서 테이블 생성
        db.create_all()

    # admin 페이지에 모델뷰 추가
    add_admin_view(app)

    # blueprint 등록 코드, url_prefix를 기본으로 함
    add_blueprint(app)

    # jinja2 필터 등록
    app.jinja_env.filters['datetime'] = lambda x: x.strftime('%y.%m.%d %H:%M')

    # login_manager 설정 코드
    set_login_manager(app)
    
    # 403, 404, favicon error handler
    set_app_error(app)

    # create_user, update_all_model_instances 명령어 추가
    add_cli(app)

    # sqlalchemy 쿼리 로깅 확인용 
    # import logging
    # logging.basicConfig()
    # logging.getLogger('sqlalchemy.engine').setLevel(logging.DEBUG)
        
    return app

def add_admin_view(app):
    # admin 페이지에 모델뷰 추가
    admin = Admin(app, name='MyBlog', template_mode='bootstrap3')
    for admin_model, model in get_all_admin_models():
        admin.add_view(admin_model(model, db.session))

def add_blueprint(app):
    from .views import views
    app.register_blueprint(views)
    from .auth import auth
    app.register_blueprint(auth, url_prefix='/auth')

def set_login_manager(app):
    login_manager = LoginManager()
    login_manager.init_app(app) # app 연결
    login_manager.login_view = 'auth.login' # 로그인을 꼭 해야하는 페이지 접근 시 auth.login으로 리다이렉트 설정 

    # login_required 실행 전 사용자 정보 조회 메소드
    @login_manager.user_loader
    def user_loader(user_id):
        return db.session.get(get_model('user'), int(user_id))
    
def set_app_error(app):
    # 403(Forbidden) 오류 발생 시 로그인 페이지로 리디렉션
    @app.errorhandler(403)
    def handle_forbidden_error(e):
        flash('권한이 없습니다', category="error")
        return redirect(url_for('auth.login'))
    
    # 404(Not Found) 오류 발생 시 홈페이지로 리디렉션
    @app.errorhandler(404)
    def handle_not_found_error(e):
        flash('잘못된 경로입니다.', category="error")
        return redirect(url_for('views.home'))
    
    @app.route('/favicon.ico') 
    def favicon(): 
        return url_for('static', filename='assets/favicon.ico')
    
def add_cli(app):
    from click import command               # 커맨드 라인 인터페이스 작성
    from flask.cli import with_appcontext   # Flask 애플리케이션 컨텍스트
    from sqlite3 import IntegrityError      # unique 제약조건 위배
    @command(name="create_user")
    @with_appcontext
    def create_user():
        username = input("Enter username : ")
        email = input("Enter email : ")
        password = input("Enter password : ")
        post_create_permission = input("Do you want post create permission? (y/n): ")
        admin_check = input("Do you want admin check? (y/n): ")

        post_create_permission = post_create_permission.lower() == "y"
        admin_check = admin_check.lower() == "y"

        try:
            admin_user = get_model('user')(
                username = username,
                email = email,
                password = password,
                post_create_permission = post_create_permission,
                admin_check = admin_check
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"User created!\n{admin_user.id}: {admin_user.username}")
        except IntegrityError:
            # 빨간색으로 표시
            print('\033[31m' + "Error : username or email already exists.")

    @command(name="update_all_model_instances")
    @with_appcontext
    def update_all_model_instances():
        for _, model in get_all_admin_models():
            instances = db.session.query(model).all()
            for instance in instances:
                instance.update_instance()
            print(f"Model {model.__name__} update finished!")

    # app에 등록
    app.cli.add_command(create_user)
    app.cli.add_command(update_all_model_instances)