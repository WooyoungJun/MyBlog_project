from flask import Blueprint, abort, flash, jsonify, url_for, redirect, render_template, request
from flask_login import current_user, login_required
from blog.forms import CommentForm, ContactForm, PostForm
from blog.models import db, get_model
from sqlalchemy.orm import selectinload, load_only

views = Blueprint('views', __name__)
BASE_VIEWS_DIR = 'views/'

# post = get_model('post').query.get(id) 대신 아래처럼 사용(deprecated)
# post = db.session.get(get_model('post'), id)

@views.route("/")
@views.route("/home")
def home():
    posts = db.session.query(get_model('post')).options(selectinload(get_model('post').user), selectinload(get_model('post').category)).all() 
    return render_template(BASE_VIEWS_DIR + "posts_list.html", 
        user=current_user, 
        posts=posts, 
        type = 'home',
        category_name='all',
    )

@views.route("/posts-list/<int:category_id>")
def posts_list(category_id):
    category_posts = db.session.query(get_model('post')).filter_by(category_id=category_id).options(selectinload(get_model('post').user)).all() 
    if category_posts is None:
        flash('해당 카테고리는 존재하지 않습니다.', category="error")
        return redirect(url_for('views.category'))
    
    return render_template(BASE_VIEWS_DIR + "posts_list.html", 
        user=current_user, 
        posts=category_posts, 
        type = 'category_posts',
        category_name=category_posts[0].category.name,
    )

@views.route("/user_posts/<int:user_id>")
def user_posts(user_id):
    user_posts = db.session.query(get_model('post')).filter_by(author_id=user_id).options(selectinload(get_model('post').category), selectinload(get_model('post').user)).all() 
    if user_posts is None:
        flash('해당 유저가 작성한 글이 존재하지 않습니다.', category="error")
        return redirect(url_for('views.home'))
    
    return render_template(BASE_VIEWS_DIR + "posts_list.html", 
        user=current_user, 
        selected_user=user_posts[0].user,
        posts=user_posts, 
        type = 'user_posts',
    )

@views.route("/about-me")
def about_me():
    return render_template(BASE_VIEWS_DIR + "about_me.html", user=current_user)
    
@views.route("/contact", methods=['GET', 'POST'])
def contact():
    form = ContactForm()

    if request.method == 'POST' and form.validate_on_submit():
        message = get_model('message')(
            content=form.content.data,
            user_id=current_user.id,
        )
        db.session.add(message)
        db.session.commit()
        flash('메세지 전송이 완료되었습니다.', category="success")
        form.content.data = ''  # 폼 초기화

    return render_template(BASE_VIEWS_DIR + "contact.html", 
        user=current_user,
        form=form,
    )

@views.route('/mypage')
def mypage():
    return render_template(BASE_VIEWS_DIR + "mypage.html", user=current_user)
    
@views.route('/category')
def category():
    categories = db.session.query(get_model('category')).all()
    return render_template(BASE_VIEWS_DIR + "category.html", user=current_user, categories=categories)

# 해당하는 id의 포스트를 보여줌
@views.route('/post/<int:post_id>')
def post(post_id):
    form = CommentForm()

    post = db.session.get(get_model('post'), post_id)
    if post is None:
        flash('해당 포스트는 존재하지 않습니다.', category="error")
        return redirect(url_for('views.home'))
    
    post_comments = db.session.query(get_model('comment')).filter_by(post_id=post_id).options(selectinload(get_model('comment').user)).all()
    
    return render_template(BASE_VIEWS_DIR + "post_read.html", 
        user=current_user, 
        post=post,
        form=form,
        comments=post_comments,
    )

@views.route('/post-create', methods=['GET', 'POST'])
@login_required
def post_create():
    # 글 작성 권한 없으면 abort
    if current_user.post_create_permission == False: return abort(403)

    form = PostForm()
    if request.method == 'POST' and form.validate_on_submit():
        post = get_model('post')(
            title=form.title.data,
            content=form.content.data,
            category_id=form.category_id.data,
            author_id=current_user.id,
        )
        db.session.add(post)
        db.session.commit()
        flash('Post 작성 완료!', category="success")
        return redirect(url_for('views.home'))
    else: # GET 요청 or form invalidated
        return render_template(BASE_VIEWS_DIR + "post_write.html", 
            user=current_user, 
            form=form, 
            type='Create',
        )

@views.route('/post-edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def post_edit(post_id):
    # edit 요청 post 가져오기
    post = db.session.get(get_model('post'), post_id)
    if post is None:
        flash('게시물을 찾을 수 없습니다.', 'error')
        return redirect(url_for('views.home'))
    
    # 작성자가 아니면 abort
    if current_user.id != post.author_id: return abort(403)

    form = PostForm()

    if request.method == 'GET':
        # 기존 post 데이터 채우기
        form.title.data = post.title
        form.content.data = post.content
        form.category_id.data = post.category_id
        return render_template(BASE_VIEWS_DIR + "post_write.html", 
            user=current_user, 
            form=form, 
            type="Edit",
            post_id=post_id,
        )
    
    if request.method == 'POST' and form.validate_on_submit():
        # 새로운 post 데이터 업데이트
        post.title = form.title.data
        post.content = form.content.data
        post.category_id = form.category_id.data
        db.session.commit() # 바로 commit = update
        flash('Post 수정 완료!', category="success")
        return redirect(url_for('views.post', post_id=post_id))
    else:
        flash('Post 수정 실패!', category="error")
        return render_template(BASE_VIEWS_DIR + "post_write.html", 
            user=current_user, 
            form=form, 
            type="Edit",
            post_id=post_id,
        )

@views.route('/post-delete/<int:post_id>')
@login_required
def post_delete(post_id):
    # delete 요청 post 가져오기
    post = db.session.get(get_model('post'), post_id)
    if post is None:
        flash('게시물을 찾을 수 없습니다.', 'error')
        return redirect(url_for('views.home'))
    
    # 작성자가 아니면 abort
    if current_user.id != post.author_id: return abort(403)

    db.session.delete(post)
    db.session.commit()
    flash('게시물이 성공적으로 삭제되었습니다.', 'success')
    return jsonify(message='success'), 200

@views.route('/comment-create/<int:post_id>', methods=['POST'])
@login_required
def comment_create(post_id):
    form = CommentForm()

    if request.method == 'GET':
        flash('잘못된 요청입니다.', category="error")
        return redirect(url_for('views.post', post_id=post_id))
    
    if form.validate_on_submit():
        comment = get_model('comment')(
            content=form.content.data,
            author_id=current_user.id,
            post_id=post_id
        )
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('views.post', post_id=post_id))
    else:
        flash('댓글 작성 실패!', category="error")
        return redirect(url_for('views.post', post_id=post_id))

@views.route('/comment-edit/<int:post_id>-<int:comment_id>', methods=['POST'])
@login_required
def comment_edit(post_id, comment_id):
    form = CommentForm()

    post = db.session.get(get_model('post'), post_id)
    if post is None:
        flash('해당 포스트는 존재하지 않습니다.', category="error")
        return redirect(url_for('views.home'))
    
    if request.method == 'GET':
        flash('잘못된 요청입니다.', category="error")
        return redirect(url_for('views.post', post_id=post_id))
    
    comment = db.session.get(get_model('comment'), comment_id)
    if comment is None:
        flash('해당 댓글은 존재하지 않습니다.', category="error")
        return redirect(url_for('views.post', post_id=post_id))
    
    if current_user.id != comment.author_id: return abort(403)

    if form.validate_on_submit():
        comment.content = form.content.data
        db.session.commit()
        flash('댓글 수정 완료!', category="success")
        return redirect(url_for('views.post', post_id=post_id))
    else:
        flash('댓글 수정 실패!', category="error")
        return redirect(url_for('views.post', post_id=post_id))
    

@views.route('/comment-delete/<int:comment_id>')
@login_required
def comment_delete(comment_id):
    # delete 요청 comment 가져오기
    comment = db.session.get(get_model('comment'), comment_id)
    if comment is None:
        flash('해당 댓글은 존재하지 않습니다.', 'error')
        return jsonify(message='error'), 400
    
    # 작성자가 아니면 abort
    if current_user.id != comment.author_id: return abort(403)

    db.session.delete(comment)
    db.session.commit()
    flash('댓글이 성공적으로 삭제되었습니다.', 'success')
    return jsonify(message='success'), 200