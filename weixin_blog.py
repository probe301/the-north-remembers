

import re
import json
import sys
import random
import time
from pyquery import PyQuery
import requests
import html2text
from jinja2 import Template



def weixin_blog_html2md(html):
  h2t = html2text.HTML2Text()
  h2t.body_width = 0
  html = patch_weixin_blog_images(html)

  ret = h2t.handle(html).strip()
  ret = '\n'.join(p.rstrip() for p in ret.split('\n'))
  ret = re.sub('\n{4,}', '\n\n\n', ret)
  return ret

def patch_weixin_blog_images(html):
  # <img data-s="300,640" data-type="jpeg" data-src="http://mmbiz.qpic.cn/mmbiz/ia241nPa7bNwribnXiazWBO2xYmosVEu5bXoLqyIoibqVk4zVANaC1oSviawIrJrCsYic4ic6ILY2qtbibbPfiaPFN99sKA/0?wx_fmt=jpeg" data-ratio="2.197802197802198" data-w="364"/>
  p = r'<img data.+? data-src="(.+?)".+?/>'
  html = re.sub(p, r'<img src="\1" />', html)
  return html


def fill_template(url=None, title=None, post_date=None,
                  content=None, author=None):
  tmpl_string = '''
# {{title}}

    author: {{author}}
    post_date: {{post_date}}
    url: {{url}}


{{content}}



------------------

from: [{{url}}]()


'''
  template = Template(tmpl_string)
  return template.render(**locals())



def test_fetch():

  url = 'http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=403189023&idx=1&sn=8f5774a37f965d3e33901172d191ac91&scene=0#rd'  #
  url = 'http://mp.weixin.qq.com/s?__biz=MzI3MDE0NzI0MA==&mid=2650991368&idx=2&sn=efc68055efff53061cedb8eba58bf5fd&scene=0#rd' # 伦敦

  url = 'http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690132&idx=1&sn=0e16066155bdccc005717909ef28c7f3&scene=0#rd' # 地王

  # t = d('div#js_article')
  # md = html2md(t.text())
  # print(md)
  doc = PyQuery(url=url)('div#js_article')

  content = doc('#js_content')
  # print(content.html(), file=open('test_wx.html', 'w', encoding='utf-8'))
  title = doc('#activity-name')
  author = doc('#post-user')
  post_date = doc('#post-date')


  # TODO: 加上 header bg 图
  page = fill_template(title=title.text(),
                       post_date=post_date.text(),
                       content=weixin_blog_html2md(content.html()),
                       author=author.text(),
                       url=url)
  print(page)
  print(page, file=open('test_wx.md', 'w', encoding='utf-8'))
