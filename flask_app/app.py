from blog import create_app
from blog.config import Config

app = create_app(config=Config(), mode='DEVELOPMENT')
if __name__ == '__main__':
    app.run(port=8888, debug=True)
