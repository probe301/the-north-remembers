

import re

import time
from pyquery import PyQuery

import html2text
from jinja2 import Template

import time
from pylon import datalines

import shutil

from urllib.parse import unquote
from jinja2 import Template
import re
from pyquery import PyQuery
import requests
from pylon import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')



def format_weixin_url(url):
  '''需要url中的4个参数
     __biz=MzI3MDE0NzI0MA==
   & mid=2650991378
   & idx=1
   & sn=7fb39f8f5b8d2b98751fd5515a7a4623
  '''
  # 'http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690955&idx=2&sn=9f8a8c23ca60ac68d1b8647f8d80dd8f&scene=0#rd'

  if 'mp.weixin.qq.com' not in url:
    raise ValueError('cannot parse WeiXin url {}'.format(url))

  url = url.split('#')[0]
  if 'scene=' in url:
    url = re.sub(r'\&scene=\d+', '', url)
  return url


def weixin_blog_html2md(html):

  if html is None:
    raise ValueError('html is none')
  def replace_section_to_p(html):
    p = r'(</?)section'
    html = re.sub(p, r'\1p', html)
    return html
  def patch_weixin_blog_images(html):
    # <img data-s="300,640" data-type="jpeg" data-src="http://mmbiz.qpic.cn/mmbiz/ia241nPa7bNwribnX...KA/0?wx_fmt=jpeg" data-ratio="2.197802197802198" data-w="364"/>
    p = r'<img.+?data-src="(.+?)".+?/>'
    html = re.sub(p, r'<img src="\1" />', html)
    return html

  html = patch_weixin_blog_images(html)
  html = replace_section_to_p(html)

  h2t = html2text.HTML2Text()
  h2t.body_width = 0
  ret = h2t.handle(html).strip()
  ret = '\n'.join(p.rstrip() for p in ret.split('\n'))
  return ret




def weixin_fix_markdown(text):
  # 去除 html2text 转换出来的 strong 和 link 的多余空格
  # ![](http://mmbiz.qpic.cn/mmbiz_jpg/52ChNWeJui...EwrkQ/0?wx_fmt=jpeg)
  pattern_img_start_inline = re.compile(r'\n*(\!\[\]\(http://mmbiz\.qpic\.cn.+?\))\n*')
  # def replace_img_start_inline(mat):
  #   # 保证生成的 *.md 图片在新的一行
  #   s = mat.group(0)
  #   while not s.startswith('\n\n'):
  #     s = '\n' + s
  #   while not s.endswith('\n\n'):
  #     s = s + '\n'
  #   return s
  pattern_multiple_newline = re.compile(r'\n{4,}') # 连续4+换行的都压缩到3个

  text = pattern_img_start_inline.sub(r'\n\n\1\n\n', text)
  text = pattern_multiple_newline.sub('\n\n\n', text)
  text = re.sub(r'\*\*\n{0,1}\*\*', '', text)
  text = re.sub(r'\*\*\n{2,4}\*\*', ' ', text)
  return text








def fill_template(url=None, title=None, post_date=None, fetch_date=None,
                  content=None, author=None):

  # 需要 header image
  tmpl_string = '''
### {{title}}

    author: {{author}}
    post_date: {{post_date}}
    fetch: {{fetch_date}}
    url: {{url}}


{{content}}






'''
  template = Template(tmpl_string)
  return template.render(**locals())




def fetch_weixin_blog(url):
  # t = d('div#js_article')
  # md = html2md(t.text())
  # print(md)
  url = format_weixin_url(url)
  doc = PyQuery(url=url)('div#js_article')

  content = doc('#js_content')
  # print(content.html(), file=open('test_wx.html', 'w', encoding='utf-8'))
  title = doc('#activity-name').text().strip()
  author = doc('#post-user').text().strip()
  post_date = doc('#post-date').text().strip()


  # TODO: 加上 header bg 图

  print(content.html(), file=open(title + '.debug.html', 'w', encoding='utf-8'))
  page = fill_template(title=title,
                       post_date=post_date,
                       fetch_date=time.strftime('%Y-%m-%d'),
                       content=weixin_fix_markdown(weixin_blog_html2md(content.html())),
                       author=author,
                       url=url)

  return {'title': title + ' - ' + author, 'content': page}


def format_weixin_filename(title):
  invalid_chars = list('|?"\'')
  invalid_chars.append('\xa0')
  return ''.join(' ' if c in invalid_chars else c for c in title)








def extract_weixin_articles_from_feed(feed):
  # <title>做商业地产，也许可以听听这段异类的观点</title>
  # <link>http://www.iwgc.cn/link/2646045</link>
  # <description>...</description>
  # <pubDate>Sun, 11 Sep 2016 09:31:10 +0800</pubDate>
  r = requests.get(feed)
  doc = PyQuery(r.content)
  for item in doc.find('item'):
    article = PyQuery(item)
    yield {'title': article.find('title').text(),
           'link': article.find('link').text(),
           'description': article.find('description').text(),
           'pubDate': article.find('pubDate').text()}


def follow_iwgc_redirect(url):
  response = requests.get(url)
  text = response.content
  # log(type(text))
  text = str(text).split('window.location.href = \\\'')[1]
  return text.split('\\\'')[0]






def test_extract_from_feed():
  feed = 'http://rss.iwgc.cn/rss/3615-43519defd654b27f8f3b5205e678b9bb1799'
  data = extract_weixin_articles_from_feed(feed)
  for a in data:
    log(a)




















def test_follow_iwgc_redirect():
  url = 'http://www.iwgc.cn/link/2655245'
  new_url = follow_iwgc_redirect(url)
  log(new_url)
  # => http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691331&idx=1&sn=8c0756fa629940953ac8e353d662bf8d&chksm=84147ab0b363f3a6460df0e4581c0853f31b68a0bb0d729a52374af38414cd44fb9596e56205&scene=0#rd














def test_fetch():

  url = 'http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=403189023&idx=1&sn=8f5774a37f965d3e33901172d191ac91'  #
  url = 'http://mp.weixin.qq.com/s?__biz=MzI3MDE0NzI0MA==&mid=2650991368&idx=2&sn=efc68055efff53061cedb8eba58bf5fd' # 伦敦

  url = 'http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690164&idx=1&sn=29d2b67be37d2bbda10b981a8b9ef420' # 地王
  url = 'http://mp.weixin.qq.com/s?__biz=MzI3MDE0NzI0MA==&mid=2650991378&idx=1&sn=7fb39f8f5b8d2b98751fd5515a7a4623' # 劳工运动会毁于精英主义吗

  url = 'http://mp.weixin.qq.com/s?timestamp=1473058983&src=3&ver=1&signature=2gTbvfvRieZfUb99JUzpk8n1cqpTxqaTB4IdjkedT1N7AOtwiswxp84*DOJJ6r5s*ffnXW2O6Z45OmzBUtyMA4XDnQbg2dPHB7b6Q1SUel8Lt8Z5KL5pNpQHaMYwiRdcFju9n8l5kG6wbU-dA-OaJSfneBj4g7V3GkAGiJghmIg=' # 新海诚《你的名字》

  url = 'http://mp.weixin.qq.com/s?timestamp=1473128685&src=3&ver=1&signature=twQkNHc5vMmsmjOsxmUnSuJkGEZrtosWQptMdO7hGdT4UTfiTPnSiK88LO9FQXlqTSXf9dl64oFAV8sYjQyNTK2Weev-Z0dEWaK772DIVNBpX4EZjQpcRAwGku2*YQG32*QhJxbl-SHVMZYByGV5GQm5Dku2N*eN2WQhBvYA8KU=' # 新海诚《你的名字》on other timestamp
  url = 'http://mp.weixin.qq.com/s?__biz=MzAxMjcyODExMA==&mid=2652273018&idx=1&sn=984cb5e9daea270f91a536a69330d670' # 新海诚《你的名字》 permalink

  url = 'http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690955&idx=2&sn=9f8a8c23ca60ac68d1b8647f8d80dd8f' # 高低配让开发商赚了钱

  url = 'http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672791&idx=1&sn=c72f74615feb49c29d2d039bd20d8c09'  # 马克思主义经济观

  url = 'http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691115&idx=1&sn=bace23bc811274b0b420c9a481a21a69&chksm=84147b98b363f28ea4262d28a1a9bf91d4da9a04b15c58bfb4a395b1d48a9884381fce16591e&scene=0#wechat_redirect'

  # url = 'http://mp.weixin.qq.com/s?src=3&timestamp=1473128750&ver=1&signature=P9LX1wt*2XYCHzwdy16NomH3-DFE80OK3aBvpnQuW6a0uWedkoFoqcpAb0mSw9Mo5UAfmbjkNEwcGdOU4s1Et2tojz4nyq8tELr-mbPKZ1Lyb1Kb5pbp6M60SA2Ldg2EF21K8iMDNIScALKdLllw-QrOYtJyBo5N0yhm3mvyX-g=' # 马克思主义经济观 utl type 2 # 这种url里有评论但是timestamp会过期
  page = fetch_weixin_blog(url)

  path = format_weixin_filename(page['title'] + '.md')
  print(page['content'], file=open(path, 'w', encoding='utf-8'))







