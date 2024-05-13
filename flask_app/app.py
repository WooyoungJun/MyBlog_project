from blog.factory import create_app
from blog.config import Config

app = create_app(config=Config(), mode='PRODUCTION')
if __name__ == '__main__':
    app.run(port=8888, debug=True)
