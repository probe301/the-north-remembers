

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

  # print(content.html(), file=open(title + '.debug.html', 'w', encoding='utf-8'))
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
  log(feed)
  # r = requests.get(feed)
  # log(r.content)
  # doc = PyQuery(r.content)
  doc = PyQuery(open('knowleage_rss.xml', 'rb').read())
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
  if 'iwgc.cn' in url:
    text = str(text).split('window.location.href = \\\'')[1]
    return text.split('\\\'')[0]
  elif 'www.vccoo.com' in url:
    # 境外server
    # http://www.vccoo.com/v/899e61?source=rss
    text = str(text).split('var s = "')[1]
    return text.split('";')[0]
  else:
    raise ValueError()





def test_rss():
  feed = 'http://www.vccoo.com/a/vzr62/rss.xml'
  feed = 'http://www.vccoo.com/v/f5b94c'
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    # 'Referer': 'http://www.vccoo.com',
    # 'Accept-Encoding': 'gzip, deflate, sdch',
  }

  # cookies = {'ASP.NET_SessionId': 'kbnrrb45ovcumwfy25xooxec'}
  s = requests.Session()
  r = s.get(feed, headers=headers)
  log(r.content[:400])
  # r = s.get(feed, headers=headers, stream=True)
  # log(r)


def test_extract_from_feed():
  feed = 'http://rss.iwgc.cn/rss/3615-43519defd654b27f8f3b5205e678b9bb1799'
  feed = 'http://www.vccoo.com/a/vzr62/rss.xml'
  data = extract_weixin_articles_from_feed(feed)
  i = 0
  for a in data:
    log(a)
    i += 1
    if i > 9999:
      break










def test_knewleagewealth():
  s = '''
    http://www.vccoo.com/v/b9c80e
    http://www.vccoo.com/v/281ebb
    http://www.vccoo.com/v/cc1c1c
    http://www.vccoo.com/v/b2ed93
    http://www.vccoo.com/v/899e61
    http://www.vccoo.com/v/b62073
    http://www.vccoo.com/v/4a8b83
    http://www.vccoo.com/v/67dfde
    http://www.vccoo.com/v/2d11aa
    http://www.vccoo.com/v/dfbbd4
    http://www.vccoo.com/v/f5b94c
    http://www.vccoo.com/v/456a41
    http://www.vccoo.com/v/f68c61
    http://www.vccoo.com/v/36ead5
    http://www.vccoo.com/v/10fead
    http://www.vccoo.com/v/6cf373
    http://www.vccoo.com/v/2c7531
    http://www.vccoo.com/v/471418
    http://www.vccoo.com/v/bc650c
    http://www.vccoo.com/v/6c9518
    http://www.vccoo.com/v/5a3234
    http://www.vccoo.com/v/356f01
    http://www.vccoo.com/v/35b3b7
    http://www.vccoo.com/v/61b98a
    http://www.vccoo.com/v/7ee861
  '''
  for line in datalines(s):
    log(line)
    # log(follow_iwgc_redirect(line))

  s_finish = '''
    # zhaohaoyang
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672803&idx=1&sn=032a476cef35b974ed5f39e9b07fefa9#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672799&idx=1&sn=27453994634bb0245e9b4aaea0942b2b#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672791&idx=1&sn=c72f74615feb49c29d2d039bd20d8c09#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672788&idx=1&sn=4851efd729fa6b28c6335b9ba911393b#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672773&idx=1&sn=c06f03b9f0d72a33281e4ff71a09b2ee#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672765&idx=1&sn=d7472177530167c4031e8bfda8e74ef1#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672749&idx=1&sn=f0fbfcf12ae9f691e7ec61730613b0fb#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672739&idx=1&sn=e72ac99a37b0076dcd28446814aaa702#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672734&idx=1&sn=bbb6f4805603e04917cf1a7c99f328f6#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672727&idx=1&sn=102ab61d5d2299bffe26087f3f190b23#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672721&idx=1&sn=736094e9955e5bead81524fecf90bc7f#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672712&idx=1&sn=5f0ec02b5191a0cfea1067e25b8a844d#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672708&idx=1&sn=4b1f7d3e02a52c50217d8d274c10e325#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672687&idx=1&sn=03e8a22e114f6de57865a5a26e32f640#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672679&idx=1&sn=aa72c26e937580b45df811e0efc957ee#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=403189023&idx=1&sn=8f5774a37f965d3e33901172d191ac91#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402667616&idx=1&sn=bff275d46d168f9844d1ebacc5d70ec6#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402419132&idx=1&sn=3d4c50c89f487cd2de18e381d339f0e8#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402782125&idx=1&sn=8ffaad2bc1e94f2f550f02eb01759d69#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402997622&idx=1&sn=f9eaa33a7d8894cc754b84949d89d096#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402265925&idx=1&sn=5de1f01d0c586185a06f71b0818e3568#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402904215&idx=1&sn=c2c52de290010b9af4b0361b3e3290ce#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=403020365&idx=1&sn=0937c509bf719c7735ea0c834a82b602#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402345108&idx=1&sn=b41b60214c36cfb20e9a05e9d2a35704#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402149805&idx=1&sn=76473bc0189c5b70bb438ef0dfd326a1#rd
  '''

  for url in datalines(s_finish):
    page = fetch_weixin_blog(url)
    path = format_weixin_filename(page['title'] + '.md')
    print(page['content'], file=open('knew/' + path, 'w', encoding='utf-8'))









def test_follow_iwgc_redirect():
  url = 'http://www.iwgc.cn/link/2655245'
  url = 'http://www.vccoo.com/v/f5b94c'
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







