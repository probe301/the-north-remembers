



import time
import os
import shutil
import re
from pylon import puts
from pylon import datalines
from pylon import enumrange
from datetime import datetime
from datetime import timedelta

# from peewee import *
from peewee import SqliteDatabase
from peewee import CharField
# from peewee import DateField
from peewee import TextField
from peewee import IntegerField
from peewee import DateTimeField
from peewee import FloatField
from peewee import ForeignKeyField
from peewee import BooleanField
from peewee import Model
from peewee import fn
from peewee import JOIN
from datetime import date



db = SqliteDatabase('zhihu.sqlite')



def test_create_db():
  'regenate sqlite db' | puts()
  db.connect()
  db.create_tables([Task, Page])
  db.close()

'''
####### #####   ###### ##   ##
   ##  ##   ## ##      ##  ##
   ##  #######  #####  ######
   ##  ##   ##      ## ##   ##
   ##  ##   ## ######  ##   ##
'''
class Task(Model):
  '''
  抓取任务排程

  url - url处理干净可以作为 pk？
  status - init, changed, not modified, not found
  init_watch_date
  page_type - [知乎问答 知乎专栏 微信公众号文章]
  last_watch_date
  next_watch_date
  怎样排出下一次采集的日期？

  query all Task
  对于每个 Task
  next_watch_time = 2**not_modified * (1hour) + last_watch_time

  '''
  url = CharField(unique=True)
  status = CharField()
  page_type = CharField()
  last_watch = DateTimeField(null=True)
  next_watch = DateTimeField(null=True)
  weight = FloatField(default=1)
  not_modified = IntegerField(default=0)

  BASETIMEOUT = 3600 # 1hour
  class Meta:
    database = db

  def __str__(self):
    return '<Task url={0.url}\n      last_watch={0.last_watch}next_watch={0.next_watch}>'.format(self)


  @classmethod
  def add(cls, url):
    '''添加抓取任务
    如果已经添加过了, 也应该将 next_watch 归零触发一次抓取
    但不改变 not_modified'''
    url = cls.purge_url(url)
    page_type = cls.get_page_type(url)

    existed = cls.select().where(cls.url == url)
    if existed:
      task = existed.get()
      '{} has already existed'.format(task.url) | puts()
      task.status = 'again'
      task.next_watch = datetime.now()
      task.save()
      return task
    else:
      task = cls.create(url=url,
                        page_type=page_type,
                        status='init',
                        next_watch=datetime.now())
      return task



  @classmethod
  def watch_all(cls):
    pass


  def watch(self):
    from zhihu_answer import fetch_answer
    text, title = fetch_answer(self.url)
    page = self.remember(text, title)
    return page


  def remember(self, text, title):
    now = datetime.now()
    page = Page(task=self, title=title, content=text, watch_date=now)
    self.last_watch = now
    if (page.same_as_last()):
      self.not_modified = 0
    else:
      self.not_modified += 1
    seconds = 2 ** self.not_modified * self.BASETIMEOUT
    self.next_watch = now + timedelta(seconds=seconds)

    page.save()
    self.save()
    return page


  @classmethod
  def get_page_type(cls, url):
    return 'zhihu_answer'
  @classmethod
  def purge_url(cls, url):
    return url









'''
######   #####   ###### #######
##   ## ##   ## ##      ##
######  ####### ##  ### ######
##      ##   ## ##   ## ##
##      ##   ##  #####  #######
'''
class Page(Model):
  '''
  抓取的页面

  '''
  task = ForeignKeyField(Task, related_name='task')
  title = CharField(null=True)
  content = TextField() # 存<html> content... </html>带标签
  comments = TextField(null=True)
  watch_date = DateTimeField()
  version = IntegerField(null=True)

  class Meta:
    database = db



  def same_as_last(self):
    return True










'''
####### #######  ###### #######
   ##   ##      ##         ##
   ##   ######   #####     ##
   ##   ##           ##    ##
   ##   ####### ######     ##
'''

def test_new_task():
  url = 'http://www.zhihu.com/question/22513722/answer/21967185'
  # 火车票涨价是否能解决春运问题？
  url = 'https://www.zhihu.com/question/30595784/answer/49194862'
  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  task = Task.add(url=url)


def test_readd_task():
  url = 'http://www.zhihu.com/question/22513722/answer/21967185' # 火车票涨价
  task = Task.add(url=url)
  task = Task.add(url=url)


def test_one_watch():
  task = Task.select().get()
  task | puts()
  task.watch()


def diff(page):
  # query some version
  # collect diff
  return diffs_json

def test_query():
  q = Task.select().get()
  print(q)
  q = Task.select()
  print(q)

  # q =


def test_tools():
  import pylon
  pylon.generate_figlet('task', fonts=['space_op'])
  pylon.generate_figlet('page', fonts=['space_op'])
  pylon.generate_figlet('test', fonts=['space_op'])
  print('test_fetch')
  url = 'http:....'
  page = fetch(url)
  save(page)

