

import time
from pylon import puts
from pylon import datalines

import os
import shutil

from pylon import enumrange
# import time
import datetime

from zhihu_oauth import ZhihuClient
from zhihu_oauth.zhcls.utils import remove_invalid_char

import re

import urllib.request


class WeixinParseError(Exception):
  pass


from newspaper import Article
url = 'http://mp.weixin.qq.com/s?__biz=MzIyNDA2NTI4Mg==&mid=2655408046&idx=3&sn=1e6017387b5eea9dd51c3bd04f057c79&scene=0#rd'
# 时空的观念：艺术学与物理学
article = Article(url, language='zh')

article.download()
article.parse()

print(article.text[:1000], '......')
print(article.title)
print(article.top_image)
print(article.authors)
