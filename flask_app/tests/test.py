import unittest

if __name__ == '__main__':
    
    # 회원가입, 로그인, 로그아웃 기능 확인
    from test_1_auth import AuthTest
    # auth_test = unittest.TestLoader().loadTestsFromTestCase(AuthTest)
    # unittest.TextTestRunner(verbosity=2).run(auth_test)

    # 포스트 생성, 수정, 삭제 기능 확인
    from test_2_post import PostTest
    # post_test = unittest.TestLoader().loadTestsFromTestCase(PostTest)
    # unittest.TextTestRunner(verbosity=2).run(post_test)
    
    # 댓글 생성, 수정, 삭제 기능 확인
    from test_3_comment import CommentTest
    # comment_test = unittest.TestLoader().loadTestsFromTestCase(CommentTest)
    # unittest.TextTestRunner(verbosity=2).run(comment_test)

    unittest.main(argv=[''], verbosity=2, exit=False) # 전체 테스트 실행