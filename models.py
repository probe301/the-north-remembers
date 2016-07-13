



import time
import sys
import os
# import shutil
# import re
from pylon import puts
from pylon import form
from pylon import datalines
from pylon import create_logger
log = create_logger(__file__)
# from pylon import enumrange
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
# from peewee import BooleanField
from peewee import Model
# from peewee import fn
# from peewee import JOIN
import arrow
from zhihu_answer import topic_best_answers
from zhihu_answer import fetch_zhihu_answer


db = SqliteDatabase('zhihu.sqlite')



def convert_time(d, humanize=False):
  if not d:
    return None
  if humanize:
    return arrow.get(d.strftime('%Y-%m-%d %H:%M:%S') + '+08:00').humanize()
  else:
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
  title = CharField(null=True)
  # status = CharField()
  last_watch = DateTimeField(null=True)
  next_watch = DateTimeField(null=True)
  weight = FloatField(default=1)
  not_modified = IntegerField(default=0)

  BASETIMEOUT = 3600 # 0.1 hour
  class Meta:
    database = db


  def __str__(self):
    s = '<Task "{}"\n  "{}"\n  last_watch at {} ({})\n  next_watch should on {} ({})>'
    return s.format(self.title, self.url,
                    convert_time(self.last_watch),
                    convert_time(self.last_watch, humanize=True),
                    convert_time(self.next_watch),
                    convert_time(self.next_watch, humanize=True),
                    )

  @classmethod
  def add(cls, url, title=None):
    '''添加抓取任务
    如果已经添加过了, 也应该将 next_watch 归零
    使得今后触发一次抓取
    但不改变 not_modified'''
    url = cls.purge_url(url)
    page_type = cls.get_page_type(url)

    existed = cls.select().where(cls.url == url)
    if existed:
      task = existed.get()
      log('Task.add has already existed: {}'.format(task))
      task.next_watch = datetime.now()
      task.not_modified = 0
      task.save()
      return task
    else:
      task = cls.create(url=url,
                        page_type=page_type,
                        title=title or '(has not fetched)',
                        next_watch=datetime.now())
      return task


  def remember(self, data):
    now = datetime.now()
    page = Page(task=self,
                title=data['title'].strip(),
                author=data['author'].strip(),
                content=data['content'].strip(),
                comment=data['comments'].strip(),
                metadata=data['metadata'],
                topic=data['topic'].strip(),
                question=data['question'].strip(),
                watch_date=now)

    self.last_watch = now
    if page.same_as_last():
      self.not_modified += 1
    else:
      self.not_modified = 0

    page.save()
    seconds = 2 ** self.not_modified * self.BASETIMEOUT
    # 如果几次都是 not_modified, 则下次计划任务会安排的较晚
    self.next_watch = now + timedelta(seconds=seconds)
    self.title = data['title'].strip()
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
    if url.startswith('http://'):
      url = 'https' + url[4:]
    return url

  def watch(self):
    zhihu_answer = fetch_zhihu_answer(self.url)
    page = self.remember(zhihu_answer)
    return page


  @classmethod
  def multiple_watch(cls, sleep_seconds=10, limit=10):
    for i in range(1, limit+1):
      now = datetime.now()
      log('\n\n  loop {}/{} current_time={}'.format(i, limit, convert_time(now)))
      task = Task.select().order_by(Task.next_watch).get()
      if not task:
        log('can not find any task')
        continue
      elif task.next_watch <= now:
        log('start: {}'.format(task))
        page = task.watch()
        log('done! {}'.format(page))
        time.sleep(sleep_seconds)
      else:
        log('not today... {}'.format(task))

  @classmethod
  def report(cls):
    tasks = Task.select()
    now = datetime.now()
    tasks_todo = Task.select().where(Task.next_watch <= now)

    log('Task total={} todo={}'.format(tasks.count(), tasks_todo.count()))
    log('todo tasks:')
    for task in tasks_todo.order_by(Task.next_watch):
      log(task)













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
  watch_date = DateTimeField()
  title = CharField(null=True)
  author = CharField(null=True)
  content = TextField(null=True)
  metadata = TextField(null=True)
  topic = TextField(null=True)
  question = TextField(null=True)
  comment = TextField(null=True)

  class Meta:
    database = db

  def __str__(self):
    # if len(self.content) > 300:
    #   less_content = self.content[:250] + '  ...  ' + self.content[-50:]
    # else:
    #   less_content = self.content
    s = '<Page title="{}" (version {})\n  watch_date on {} ({})\n  {!r}>'
    return s.format(self.title, self.version,
                    convert_time(self.watch_date),
                    convert_time(self.watch_date, humanize=True),
                    form(self.content, text_maxlen=300))

  def same_as_last(self):
    '''此时 page self 应当尚未储存
    取最新的 version 的 content 与尚未储存的 page content 对比'''
    content = self.content
    title = self.title
    query = Page.select().where(Page.task == self.task)
    if query:
      last_page = query.order_by(-Page.watch_date).get()
      return self.same_as(last_page)
    else:
      return True

  def same_as(self, other):
    if self.title != other.title:
      return False
    if self.content != other.content:
      return False
    if self.topic != other.topic:
      return False
    if self.question != other.question:
      return False
    if self.author != other.author:
      return False
    return True

  @property
  def version(self):
    q = Page.select().where((Page.task == self.task) & (Page.watch_date < self.watch_date))
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
    https://www.zhihu.com/question/33246348/answer/86919689
    https://www.zhihu.com/question/39906815/answer/88534869

    https://www.zhihu.com/question/40700155/answer/89002644
    https://www.zhihu.com/question/36380091/answer/84690117
    https://www.zhihu.com/question/33246348/answer/86919689
    https://www.zhihu.com/question/35254746/answer/90252213
    https://www.zhihu.com/question/23618517/answer/89823915

    https://www.zhihu.com/question/40677000/answer/87886574

    https://www.zhihu.com/question/41373242/answer/91417985
    https://www.zhihu.com/question/47275087/answer/106335325
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


def test_hot_answer():
  url = 'http://www.zhihu.com/question/39288165/answer/110207560'
  task = Task.add(url=url)
  task.watch()



def test_watch_all():
  Task.multiple_watch(sleep_seconds=10, limit=4)


def test_report():
  Task.report()


def test_tools():
  import pylon
  pylon.generate_figlet('task', fonts=['space_op'])
  pylon.generate_figlet('page', fonts=['space_op'])
  pylon.generate_figlet('test', fonts=['space_op'])



def test_topic():
  topic_id = 19641972 # 货币政策
  for answer in topic_best_answers(topic_id=topic_id):
    log(answer.question.title, answer.author.name, answer.voteup_count)


def test_fetch_topic():
  topic_id = 19641972 # 货币政策
  topic_id = 19565985 # 中国经济
  # topic_id = 19551424 # 政治
  # topic_id = 19556950 # 物理学
  topic_id = 19612637 # 科学
  for answer in topic_best_answers(topic_id=topic_id, limit=10):
    log(answer.question.title, answer.author.name, answer.voteup_count)
    url = 'https://www.zhihu.com/question/{}/answer/{}'.format(answer.question.id, answer.id)

    Task.add(url=url, title=answer.question.title)


