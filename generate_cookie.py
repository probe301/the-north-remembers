# oauth

# from zhihu_oauth import ZhihuClient
# from zhihu_oauth.exception import NeedCaptchaException

# client = ZhihuClient()

# # name = 'p....1@g'
# # pw = 'p...'
# name = input('name:')
# pw = input('pw:')
# try:
#     client.login(name, pw)
# except NeedCaptchaException:
#     # 保存验证码并提示输入，重新登录
#     with open('a.gif', 'wb') as f:
#         f.write(client.get_captcha())
#     captcha = input('please input captcha:')
#     # captcha = ''
#     client.login(name, pw, captcha)

# print(client)
# client.save_token('token.pkl')


# cookie

# from zhihu import ZhihuClient
# client = ZhihuClient()
# # client.login_in_terminal()
# client.create_cookies('cookies.json')

