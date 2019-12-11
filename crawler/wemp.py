

import re

import time

import html2text
from jinja2 import Template

import time
import tools


import shutil

from urllib.parse import unquote
from jinja2 import Template
import re

import requests
from pyquery import PyQuery as pq
from tools import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')




# def weixin_blog_html2md(html):
#   def replace_section_to_p(html):
#     p = r'(</?)section'
#     html = re.sub(p, r'\1p', html)
#     return html
#   def patch_weixin_blog_images(html):
#     # <img data-s="300,640" data-type="jpeg" data-src="http://mmbiz.qpic.cn/mmbiz/ia241nPa7bNwribnX...KA/0?wx_fmt=jpeg" data-ratio="2.197802197802198" data-w="364"/>
#     p = r'<img.+?data-src="(.+?)".+?/>'
#     html = re.sub(p, r'<img src="\1" />', html)
#     return html

#   html = patch_weixin_blog_images(html)
#   html = replace_section_to_p(html)

#   h2t = html2text.HTML2Text()
#   h2t.body_width = 0
#   ret = h2t.handle(html).strip()
#   ret = '\n'.join(p.rstrip() for p in ret.split('\n'))
#   return ret




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




def fetch_wemp_lister(html):
  doc = pq(html)
  result = []
  for item in doc.find('div.post-item'):
    item = pq(item)
    date = item.find('div.post-item__date').text()
    title = item.find('a.post-item__title').text()
    url = item.find('a.post-item__title').attr('href')
    result.append({ 'url': 'https://wemp.app'+url, 
                    'tip': title, 
                    'pubdate': date })
  return result


def fetch_wemp_page(html):
  doc = pq(html)
  title = doc('h1.post__title').text().strip()
  author_name = doc.find('h3.mp-info__title').text().split('\n')[0].strip()
  author_id = doc.find('h3.mp-info__title>a').attr('href').split('/')[-1]
  publish_date = doc('.post__date').text().strip()
  body = doc('#content').html()
  body = tools.html2md(body)

  metadata = {
    'title': title, 
    'author_name': author_name,
    'author_id': author_id,
    'publish_date': publish_date,
    'fetch_date': tools.time_now_str(),
    'count': len(body),
  }
  return { 'metadata': metadata,
           'content': body.strip(),
         }











def fetch_weixin_article_page(url):
  content = requests.get(url).content
  doc = pq(content)
  msg = doc('.page_msg').text()
  if msg:
    return { 'metadata': {
                          'title': '-1', 
                          'author_name': '-1',
                          'author_id': '-1',
                          'publish_date': '',
                          'fetch_date': tools.time_now_str(),
                          'count': 0,
                          'url': url,
                        },
            'content': msg,
          }

  title = doc('#activity-name').text().strip()
  author_name, author_id, _ = doc.find('#js_profile_qrcode').text().strip().split('\n')
  author_id = author_id.split(' ')[-1]
  publish_date = doc('#publish_time').text().strip()
  body = doc('#js_content').html()
  body = weixin_fix_markdown(weixin_blog_html2md(body))

  # publish_date = parse_json_date(article.updated_time)
  fetch_date = tools.time_now_str()

  # TODO: 加上 header bg 图

  metadata = {
    'title': title, 
    'author_name': author_name,
    'author_id': author_id,
    'publish_date': publish_date,
    'fetch_date': fetch_date,
    'count': len(body),
    'url': url,
  }
  return { 'metadata': metadata,
           'content': body.strip(),
         }




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


































