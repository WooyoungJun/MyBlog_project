from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
db = SQLAlchemy()
migrate = Migrate()

def db_migrate_setup(app):
    db.init_app(app)
    migrate.init_app(app, db)
    with app.app_context():
        # db.Model 상속한 모든 클래스 추적해서 테이블 생성
        db.create_all()

def get_session():
    return db.session

def get_db():
    return db