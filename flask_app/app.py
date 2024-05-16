from blog.factory import create_app
from blog.config import Config

app = create_app(config=Config(), mode='DEVELOPMENT')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)
