

import re

import time

import html2text
from jinja2 import Template

import time
import tools

import shutil

import re

import requests
from pyquery import PyQuery as pq
from tools import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')

from .common import common_get


def fetch_v2ex_page(url):
  # html = re.sub(r'<img data-src="//i', '<img src="https://i', html)
  doc = pq(common_get(url))
  body_doc = doc('#Main > div:nth-child(2) > div.header')
  title = body_doc('h1').text().strip()
  tag = body_doc('a:nth-child(4)').text()
  author_name = body_doc('small > a').text()
  author_url = 'https://www.v2ex.com' + body_doc('small > a').attr('href')
  _, publish_date, view_count, *_ = doc("small").text().split('·')

  body = doc('div.cell > div.topic_content').html()
  body = tools.html2md(body)
  body += '\n\n\n'

  for subtle in doc.find('div.subtle'):
    body += tools.html2md(doc(subtle).html())
    body += '\n\n\n'


  reply_doc = doc('#Main > div:nth-child(4)')
  tags = reply_doc('a.tag').text().split(' ') + [tag]

  # 不登录时没有 fav count 放弃
  # favorite_count = reply_doc('.topic_stats').text().split(' ')

  
  if reply_doc('.page_current').text(): # has multiple pages
    pagenates1 = reply_doc('.page_current').text().split()[0]
    # pagenates2 = reply_doc('.page_normal').text().split()
    max_page = int(pagenates1)
  else:
    max_page = 1

  comments = []
  for page_index in range(1, max_page+1):
    if page_index < max_page:  
      current_page = f'{url}?p={page_index}'
    else:  # 默认打开的是 ?p=最大 的分页
      current_page = f'{url}'
    comments.extend(fetch_v2ex_comments(current_page))

  metadata = {
    'title': title, 
    'author_name': author_name,
    'author_url': author_url,
    'tags': tags,
    'url': url,
    'publish_date': publish_date.strip(),
    'fetch_date': tools.time_now_str(),
    'view_count': view_count.strip().split(' ')[0],

    # 'comment_count': comment_count,
    # 'favorite_count': favorite_count,

    'words': len(body),
  }
  return { 'metadata': metadata,
           'content': body.strip(),
           'comments': comments,
         }






def fetch_v2ex_comments(url):
  doc = pq(common_get(url))
  reply_doc = doc('#Main > div:nth-child(4)')

  results = []
  for cmt in reply_doc.find('.cell > table'):
    cmt = doc(cmt)
    if cmt('.page_current').text(): 
      continue

    results.append({
      'author': cmt('strong').text(), 
      'text': cmt('.reply_content').text(),
      'date': cmt('span.ago').text(),
      'no': cmt('span.no').text(),
      'likes': cmt('span.fade').text().split()[-1] if cmt('span.fade').text() else 0
    })
  return results




























