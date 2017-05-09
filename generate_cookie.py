# -*- coding: utf-8 -*-

# # name = 'p....1@g'
# # pw = 'p...'


import os
from zhihu_oauth import ZhihuClient
TOKEN_FILE = 'token.pkl'
client = ZhihuClient()
if os.path.isfile(TOKEN_FILE):
    client.load_token(TOKEN_FILE)
else:
    client.login_in_terminal(use_getpass=False)
    client.save_token(TOKEN_FILE)



