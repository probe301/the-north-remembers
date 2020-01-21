
import os, sys 
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
sys.path.insert(0, parentdir)
import shutil
import tools
import arrow
from pyshould import should
from datetime import datetime
import dictdiffer
import pytest
from task import Task
from page import Page
import time

import fetcher

def test_1_faker():
  import time
  from faker import Faker
  fake = Faker(['zh_CN'])
  for _ in range(3):
    print(fake.name())
    time.sleep(2)


def test_2_add_task():
  url = 'https://zhuanlan.zhihu.com/prodesire'
  from watcher import Watcher
  w = Watcher.create(r'D:\DataStore\prodesire')
  # w.add_lister(url)
  # w.report()
  # w.watch_once()


def test_3_run_task():
  from watcher import Watcher
  w = Watcher.open(r'D:\DataStore\prodesire')
  w.report()
  w.watch_once()




def test_4_fetch_page():
  url = 'https://www.zhihu.com/question/295758159/answer/581105694'
  #url = 'https://www.zhihu.com/question/54353637/answer/207166302'
  task = Task.create({'url': url, 'desc': 'tip'})
  data = task.run()
  data['metadata']['folder'] = './'
  page = Page.create(data)
  page.write()




def test_5_fetch_bilibili_read_fetch():

  #'tip': '专栏文章 泰拉瑞亚多模组：模组流程解析'
  # data = fetcher.common_get('https://api.bilibili.com/x/space/article?mid=23096000&jsonp=jsonp&callback=__jp13')
  # print(data)

  




