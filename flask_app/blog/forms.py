from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, EmailField, PasswordField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from blog.models import get_model

class SignUpForm(FlaskForm):
    username = StringField('username', validators=[DataRequired('사용자 이름은 필수로 입력해야 합니다.'), Length(3,30, '사용자 이름이 너무 짧거나 깁니다.')])                                
    email = EmailField('email', validators=[DataRequired('사용자 이메일은 필수로 입력해야 합니다.'), Email('이메일 형식을 지켜주세요.')])                        
    password = PasswordField('password', validators=[DataRequired('비밀번호를 입력해주세요.'), 
                                                    Length(6, 30, '비밀번호 길이가 너무 짧거나 깁니다.'), 
                                                    EqualTo("password_check", message="비밀번호가 일치해야 합니다.")])
    password_check = PasswordField('password_check', validators=[DataRequired()])
    
class LoginForm(FlaskForm):
    email = EmailField('email', validators=[DataRequired('이메일을 입력해주세요'), Email('이메일 형식을 지켜주세요.')])
    password = PasswordField('password', validators=[DataRequired('비밀번호를 입력해주세요.'), Length(6, 30, '비밀번호 길이가 너무 짧거나 깁니다.')])

class PostForm(FlaskForm):
    title = StringField('title', validators=[DataRequired('제목을 작성해주세요.')])
    content = TextAreaField('content', validators=[DataRequired('본문을 작성해주세요.')])
    category_id = SelectField('category', coerce=int, validators=[DataRequired('카테고리를 지정해주세요.')])
    author = StringField('author', render_kw={'readonly': True})

    def __init__(self, *args, **kwargs): # 선택 항목 추가
        super(PostForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(category.id, category.name) for category in get_model('category').query.all()]
        self.author.data = current_user.username

class CommentForm(FlaskForm):
    content = TextAreaField('content', validators=[DataRequired('댓글을 작성해주세요.')])