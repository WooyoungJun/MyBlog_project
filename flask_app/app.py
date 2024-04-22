from blog import create_app
from blog.config import Config

app = create_app(config=Config)
if __name__ == '__main__':
    app.run(debug=True)