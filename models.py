



import time
import os
import shutil
import re
from pylon import puts
from pylon import datalines
from pylon import enumrange
from datetime import datetime

from datetime import timedelta

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


def convert_time(d):
  if d is None:
    return None
  return d.strftime('%Y-%m-%d %H:%M:%S')


def exec_create_db():
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

  init_watch_date
  page_type - [知乎问答 知乎专栏 微信公众号文章]
  last_watch_date
  next_watch_date
  怎样排出下一次采集的日期？

  query all Task
  对于每个 Task
  next_watch_time = 2**not_modified * (1hour) + last_watch_time

  '''
  page_type = CharField()
  url = CharField(unique=True)
  title = CharField(default='(has not fetched)')
  # status = CharField()
  last_watch = DateTimeField(null=True)
  next_watch = DateTimeField(null=True)
  weight = FloatField(default=1)
  not_modified = IntegerField(default=0)

  BASETIMEOUT = 360 # 0.1 hour
  class Meta:
    database = db


  def __str__(self):
    query = Page.select().where(Page.task == self)
    if query:
      title = query.get().title
    else:
      title = '(page has not fetched)'

    s = '<Task title="{}"\n      url="{}"\n      last_watch={}\n      next_watch={}>'
    return s.format(title, self.url, convert_time(self.last_watch), convert_time(self.next_watch))

  @classmethod
  def add(cls, url):
    '''添加抓取任务
    如果已经添加过了, 也应该将 next_watch 归零
    使得今后触发一次抓取
    但不改变 not_modified'''
    url = cls.purge_url(url)
    page_type = cls.get_page_type(url)

    existed = cls.select().where(cls.url == url)
    if existed:
      task = existed.get()
      print('has already existed: {}'.format(task))
      task.next_watch = datetime.now()
      task.not_modified = 0
      task.save()
      return task
    else:
      task = cls.create(url=url,
                        page_type=page_type,
                        next_watch=datetime.now())
      return task


  def remember(self, data):
    now = datetime.now()
    page = Page(task=self, title=data['title'],
                content=data['content'].strip(), watch_date=now)
    self.last_watch = now
    if page.same_as_last():
      self.not_modified += 1
    else:
      self.not_modified = 0

    page.save()
    seconds = 2 ** self.not_modified * self.BASETIMEOUT
    self.next_watch = now + timedelta(seconds=seconds)
    self.title = data['title']
    self.save()
    return page

  @classmethod
  def get_page_type(cls, url):
    if 'zhihu.com' in url:
      return 'zhihu_answer'
    else:
      raise

  @classmethod
  def purge_url(cls, url):
    return url

  def watch(self):
    from zhihu_answer import fetch_zhihu_answer
    zhihu_answer = fetch_zhihu_answer(self.url)
    page = self.remember(zhihu_answer)
    return page


  @classmethod
  def loop_watch(cls, sleep_seconds=1, times=10):
    for i in range(1, times+1):
      task = Task.select().order_by(Task.next_watch).get()
      if not task:
        print('can not find any task')
        continue
      now = datetime.now()
      if task.next_watch <= now:
        print('{} loop watch start: now: {}\n{}'.format(i, now, task))
        page = task.watch()
        print('{} loop watch done:\n{}'.format(i, page))
        time.sleep(sleep_seconds)
      else:
        print('{} not today...\nnext_watch at: {} but now: {}\n{}'.format(i, task.next_watch, now, task))

  @classmethod
  def report(cls):
    tasks = Task.select()
    now = datetime.now()
    tasks_expired = Task.select().where(Task.next_watch <= now)

    print('Task total={} expired={}'.format(tasks.count(), tasks_expired.count()))
    print('expired tasks:')
    for task in tasks_expired.order_by(Task.next_watch):
      print(task)

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
  content = TextField()
  comments = TextField(null=True)
  watch_date = DateTimeField()


  class Meta:
    database = db

  def __str__(self):
    if len(self.content) > 300:
      description = self.content[:250] + '...' + self.content[-50:]
    else:
      description = self.content
    s = '<Page title="{}"\n      version={} watch_date={}\n      content="{!r}">'
    return s.format(self.title, self.version, convert_time(self.watch_date), description)

  def same_as_last(self):
    '''此时 page self 应当尚未储存
    取最新的 version 的 content 与尚未储存的 page content 对比'''
    content = self.content
    title = self.title
    query = Page.select().where(Page.task == self.task)
    if query:
      last_page = query.order_by(-Page.watch_date).get()
      return last_page.content == content and last_page.title == title
    else:
      return True

  @property
  def version(self):
    q = Page.select().where(Page.task == self.task and Page.watch_date < self.watch_date)
    if q:
      return q.count() + 1
    else:
      return 1

  def diff(self, other=None):
    pass







'''
####### #######  ###### #######
   ##   ##      ##         ##
   ##   ######   #####     ##
   ##   ##           ##    ##
   ##   ####### ######     ##
'''

def test_new_task():
  url = 'https://www.zhihu.com/question/30595784/answer/49194862'
  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  task = Task.add(url=url)


def test_readd_task():
  url = 'http://www.zhihu.com/question/22513722/answer/21967185' # 火车票涨价
  task = Task.add(url=url)
  task = Task.add(url=url)
  url = 'https://www.zhihu.com/question/30957313/answer/50266448' # 古典音乐
  task = Task.add(url=url)


def test_seed_add_tasks():
  urls = '''
    https://www.zhihu.com/question/40305228/answer/86179116
    https://www.zhihu.com/question/36466762/answer/85475145
    # https://www.zhihu.com/question/33246348/answer/86919689
    # https://www.zhihu.com/question/39906815/answer/88534869

    # https://www.zhihu.com/question/40700155/answer/89002644
    # https://www.zhihu.com/question/36380091/answer/84690117
    # https://www.zhihu.com/question/33246348/answer/86919689
    # https://www.zhihu.com/question/35254746/answer/90252213
    # https://www.zhihu.com/question/23618517/answer/89823915

    # https://www.zhihu.com/question/40677000/answer/87886574

    # https://www.zhihu.com/question/41373242/answer/91417985
    # https://www.zhihu.com/question/47275087/answer/106335325
    https://www.zhihu.com/question/47275087/answer/106335325 买不起房是房价太高还是工资太低？
    https://www.zhihu.com/question/36129534/answer/91921682  印度经济会在本世纪追上中国吗？
    https://www.zhihu.com/question/22513722/answer/21967185  火车票涨价是否能解决春运问题？
    https://www.zhihu.com/question/27820755/answer/107267228 裸辞后怎样解释以获工作机会？
  '''
  for url in datalines(urls):
    url = url.split(' ')[0]
    task = Task.add(url=url)
    task | puts()



def test_one_watch():
  task = Task.select().order_by(-Task.id).get()
  task | puts()
  task.watch()

def test_another_watch():
  url = 'http://www.zhihu.com/question/22513722/answer/21967185' # 火车票涨价
  task = Task.select().where(Task.url == url).get()
  task | puts()
  task.watch()


def test_watch_all():
  Task.loop_watch(sleep_seconds=10, times=4)


def test_report():
  Task.report()


def test_tools():
  import pylon
  pylon.generate_figlet('task', fonts=['space_op'])
  pylon.generate_figlet('page', fonts=['space_op'])
  pylon.generate_figlet('test', fonts=['space_op'])









