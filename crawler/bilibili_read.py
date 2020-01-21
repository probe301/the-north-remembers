

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



def fetch_bilibili_read_page(html, stats):
  html = re.sub(r'<img data-src="//i', '<img src="https://i', html)
  doc = pq(html)
  title = doc('h1.title').text().strip()
  author_name = doc.find('a.up-name').text().strip()
  author_url = 'https:' + doc.find('a.up-name').attr('href')
  publish_date = doc("meta[itemprop='uploadDate']").attr("content")

  # view_count = doc('div.title-container div.article-data span:nth-child(1)').text().strip()
  # like_count = doc('div.title-container div.article-data span:nth-child(2)').text().strip()
  # comment_count = doc('div.title-container div.article-data span:nth-child(3)').text().strip()
  # coin_count = doc('span.coin-btn').text().strip()
  # favorite_count = doc('span.fav-btn').text().strip()
  stats = stats['data']['stats']
  # stats: {view: 482, favorite: 19, like: 32, dislike: 0, reply: 12, share: 2, coin: 17, dynamic: 0}
  view_count = stats['view']
  like_count = stats['like']
  comment_count = stats['reply']
  coin_count = stats['coin']
  favorite_count = stats['favorite']

  body = doc('div.article-holder').html()
  body = tools.html2md(body)

  metadata = {
    'title': title, 
    'author_name': author_name,
    'author_url': author_url,

    'publish_date': publish_date,
    'fetch_date': tools.time_now_str(),
    'view_count': view_count,
    'like_count': like_count,
    'comment_count': comment_count,
    'coin_count': coin_count,
    'favorite_count': favorite_count,

    'words': len(body),
  }
  return { 'metadata': metadata,
           'content': body.strip(),
         }






































