from .user import User, UserAdmin
from .post import Post, PostAdmin
from .file import File, FileAdmin
from .category import Category, CategoryAdmin
from .comment import Comment, CommentAdmin
from .message import Message, MessageAdmin

def get_model(arg):
    models = {
        'user': User,
        'post': Post,
        'file': File,
        'category': Category,
        'comment': Comment,
        'message': Message,
    }
    return models[arg]

def get_admin_model(arg):
    models = {
        'user': UserAdmin,
        'post': PostAdmin,
        'file': FileAdmin,
        'category': CategoryAdmin,
        'comment': CommentAdmin,
        'message': MessageAdmin,
    }
    return models[arg]

def get_all_admin_models():
    arg_list = ['user', 'post', 'file', 'category', 'comment', 'message']
    return [[get_admin_model(arg), get_model(arg)] for arg in arg_list]