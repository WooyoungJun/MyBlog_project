from blog import create_app
from blog.config import Config
from blog.models import db

app = create_app(config=Config)
with app.app_context():
    # db.Model 상속한 모든 클래스 추적해서 테이블 생성
    db.create_all()
if __name__ == '__main__':
    app.run()