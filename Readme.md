# 프로젝트 목적
1. Flask 웹 어플리케이션 개발

2. 테스트 코드 작성 경험 쌓기

3. nginx + gunicorn + flask = docker-compose로 묶어서 배포하기 

4. CI/CD 적용

웹 개발에 대해 공부하면서, 지금까지 공부했던 내용들을 묶어서 하나의 과정으로 승화시키는 프로젝트가 필요하다고 느껴 이 프로젝트를 시작하게 되었습니다. 중간에 모르는 것은 채우고, 고민했던 부분은 공유하면서 진행하겠습니다.

웹 백엔드 개발에 필요한 부분을 정리하는 프로젝트이기 때문에, 프론트엔드는 부트스트랩의 clean-blog 템플릿 코드를 사용했습니다. - 출처: https://startbootstrap.com/theme/clean-blog

___

# 프로젝트 아키텍쳐

### 백엔드

- Flask 웹 어플리케이션: 엔드포인트 라우팅

- Flask-SQLAlchemy: ORM(Object Relational Mapping) 라이브러리 = 파이썬 클래스(object)와 DB(Relational) 매핑
    - models.py: DB 스키마 관리

- Flask-wtf: Form 데이터 validate 체크 등을 간편하게 할 수 있는 라이브러리
    - forms.py: 제출용 form 관리

- Flask-admin: 관리자 페이지를 간편하게 생성하고 관리할 수 있는 라이브러리
    - admin_models.py: 관리자 페이지 관리

- auth.py: auth 하위에 login, logout, sign-up 엔드포인트 관리

- views.py: views 하위에 about-me, category, contact, post_read, post_write, posts-list 엔드포인트 관리

### 프론트엔드
- Jinja2 템플릿 엔진 - 부트스트랩 템플릿 코드 활용

---
# 프로젝트 폴더 구조
MyBlog_project
* flask_app
    * blog - 주요 기능 개발
        * config - 각종 환경변수 관리(Secret key, db URI 관리 등)
        * static - assets, css, js 폴더 + 파일들
        * templates - html 템플릿
    * __init__.py - blog 패키징 파일
    * auth.py	- auth 엔드포인트 관리
    * views.py - views 엔드포인트 관리
    * forms.py - flask-wtf 폼 관리
    * models.py - flask-sqlalchemy 모델 관리(스키마 관리)
    * tests - 주요 테스트 개발
        * test_config.py - 테스트 환경변수 관리
        * test_base.py - TestBase 클래스 정의(setUpClass, tearDownClass 등)
        * test_auth.py - auth 엔드포인트 + 기능 테스트 (db기능, 회원가입, 로그인, 로그아웃)
        * test_post.py - post 관련 기능 테스트 (카테고리 생성, post 생성, 수정, 삭제)
        * test.py - 종합 테스트(기능 단위 or 통합 테스트)
    * .gitignore - git 추적 X 파일 관리
    * requirements.txt - 의존성 라이브러리 버전 관리
    * app.py - flask app entry point
    * Dockerfile - flask app DockerImage 생성을 위한 스크립트 파일
* nginx
    * nginx.conf - nginx 웹 서버의 기본 config 파일(worker_processes, http, log 설정 등)
    * default.conf - 가상 호스트 config 파일(listen 포트, server_name, proxy_pass 설정 등)
    * Dockerfile - nginx server DockerImage 생성을 위한 스크립트 파일
* docker-compose.yml - 
* run_docker.sh
* Readme.md - 프로젝트 소개