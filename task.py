
import time
import os
import shutil
import re
from pylon import puts
from pylon import datalines
from pylon import enumrange
# from pylon import yaml_ordered_load
from datetime import datetime



'''
puts('fetching zhihu / question / answer')
mdfile = fetch_answer('https://www.zhihu.com/question/{}/answer/{}'.format(qid, aid))
'''
import sqlite3


# from mark import fetch_answer



def trace_url(url):
  # build page record
  # set kind
  # set first delay
  fetch_page(url)
  save(page_version)
  return Page


def get_page_type(url):
  return 'zhihuwenda'


def fetch(url):
  # scrawl

  return PageVersion.new


def save(page_version):

  # update page
  # insert version
  return PageVersion


def diff(page):
  # query some version
  # collect diff
  return diffs_json




def test_fetch():
  print(1)


'''
DB

TABLE PAGE

url - url处理干净可以作为 pk？
status - changed, not modified, not found
first_fetch_date
kind - [知乎问答 知乎专栏 微信公众号文章]
last_fetch_date
delay





怎样排出下一次采集的日期？

query all PAGE
对于每个 PAGE
如果 status 是 (not modified, not found) 则 last_fetch_date + delay*2
如果 changed 则恢复默认的 delay








TABLE PAGE_VERSION

version 1, 2, 3
fetch_date
comments
title 可以取页面标题
content 存html带标签












'''
