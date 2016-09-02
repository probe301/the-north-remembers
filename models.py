




import time
# import sys
import os
# import shutil
# import re
from pylon import puts
from pylon import form
from pylon import datalines
from pylon import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')

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
from peewee import fn
# from peewee import BooleanField
from peewee import Model
# from peewee import fn
# from peewee import JOIN
import arrow
from zhihu_answer import yield_topic_best_answers
from zhihu_answer import yield_author_answers
from zhihu_answer import yield_author_articles
from zhihu_answer import yield_column_articles
from zhihu_answer import fetch_zhihu_answer
from zhihu_answer import fetch_zhihu_article
from zhihu_answer import fill_full_content
from zhihu_answer import zhihu_answer_url
from zhihu_answer import zhihu_article_url
from zhihu_answer import fetch_images_for_markdown
from zhihu_answer import ZhihuParseError
# import requests
from zhihu_oauth.zhcls.utils import remove_invalid_char


# from jinja2 import Template
db = SqliteDatabase('zhihu.sqlite')



def convert_time(d, humanize=False):
  if not d:
    return None
  if isinstance(d, int):
    d = datetime.utcfromtimestamp(d)
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

  BASETIMEOUT = 3600 * 24 * 7 # 7 days
  class Meta:
    database = db


  def __str__(self):
    s = '<Task "{}"\n      {} last_watch: {}, next_watch should: {}>'
    return s.format(self.title, self.url,
                    convert_time(self.last_watch, humanize=True),
                    convert_time(self.next_watch, humanize=True),
                    )


  @classmethod
  def report(cls):
    tasks = Task.select()
    now = datetime.now()
    tasks_todo = Task.select().where(Task.next_watch <= now)

    log('Task total={} todo={}'.format(tasks.count(), tasks_todo.count()))
    log('todo tasks:')
    for task in tasks_todo.order_by(Task.next_watch):
      log(task)
    log('Task total={} todo={}'.format(tasks.count(), tasks_todo.count()))
    return tasks_todo.count()

  @classmethod
  def is_watching(cls, url):
    existed = cls.select().where(cls.url == url)
    if existed:
      return existed.get()
    else:
      return False


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
      # task.not_modified = 0
      task.save()
    else:
      task = cls.create(url=url,
                        page_type=page_type,
                        title=title or '(has not fetched)',
                        next_watch=datetime.now())
      log('new Task added: {}'.format(task))
    return task


  @classmethod
  def add_by_answer(cls, answer_id, title=None, force_start=False):
    # log('add by answer')
    url = zhihu_answer_url(answer_id)
    # log('add by answer {}'.format(url))
    task = cls.add(url, title=title)
    # log('add by answer {} {}'.format(url, task))
    if force_start:
      task.watch()
    return task


  @classmethod
  def add_by_author(cls, author_id, limit=3000, min_voteup=100,
                    stop_at_existed=10, force_start=False):
    existed_count = 0
    added_count = 0
    for answer in yield_author_answers(author_id, limit=limit, min_voteup=min_voteup):
      url = zhihu_answer_url(answer)

      t = Task.is_watching(url)
      if t:
        existed_count += 1
        log('already watching {} {}'.format(t, existed_count))
        if stop_at_existed and stop_at_existed <= existed_count:
          break
      else:
        task = Task.add(url, title=answer.question.title)
        added_count += 1
        log('add_by_author <{}>\n'.format(added_count))
        if force_start:
          task.watch()
    log('add_by_author done, total added {} skipped {}'.format(added_count, existed_count))

  @classmethod
  def add_by_topic_best_answers(cls, topic_id, limit=3000, min_voteup=100,
                                stop_at_existed=10, force_start=False):
    existed_count = 0
    added_count = 0
    log(topic_id)
    for answer in yield_topic_best_answers(topic_id, limit=limit, min_voteup=min_voteup):
      url = zhihu_answer_url(answer)

      t = Task.is_watching(url)
      if t:
        existed_count += 1
        log('already watching {} {}'.format(t, existed_count))
        if stop_at_existed and stop_at_existed <= existed_count:
          break
      else:
        task = Task.add(url, title=answer.question.title)
        added_count += 1
        log('add_by_topic_best_answers <{}>\n'.format(added_count))
        if force_start:
          task.watch()
    log('add_by_topic_best_answers done, total added {} skipped {}'.format(added_count, existed_count))


  @classmethod
  def add_articles(cls, author_id=None, column_id=None,
                   limit=3000, min_voteup=10,
                   stop_at_existed=10, force_start=False):

    if not author_id and not column_id:
      raise ValueError('no author_id, no column_id')
    if author_id:
      yield_articles = yield_author_articles(author_id, limit=limit, min_voteup=min_voteup)
    else:
      yield_articles = yield_column_articles(column_id, limit=limit, min_voteup=min_voteup)

    existed_count = 0
    added_count = 0
    for article in yield_articles:
      url = zhihu_article_url(article)

      t = Task.is_watching(url)
      if t:
        existed_count += 1
        log('already watching {} {}'.format(t, existed_count))
        if stop_at_existed and stop_at_existed <= existed_count:
          break
      else:
        task = Task.add(url, title=article.title)
        added_count += 1
        log('add_articles <{}>\n'.format(added_count))
        if force_start:
          task.watch()
    log('add_articles done, total added {} skipped {}'.format(added_count, existed_count))












  @classmethod
  def get_page_type(cls, url):
    if 'zhihu.com' in url:
      if 'answer' in url:
        return 'zhihu_answer'
      elif 'zhuanlan' in url:
        return 'zhihu_article'
    else:
      raise

  @classmethod
  def purge_url(cls, url):
    if url.startswith('http://'):
      url = 'https' + url[4:]
    return url


  def watch(self):
    if self.page_type == 'zhihu_answer':
      try:
        zhihu_answer = fetch_zhihu_answer(self.url)
        page = self.remember(zhihu_answer)
        return page
      except ZhihuParseError as e:
        blank_answer = e.value
        log_error('!! 问题已删除 {} {}'.format(self.url, blank_answer['title']))
        page = self.remember(blank_answer)
        return page
      except RuntimeError as e:
        log_error(e)
        raise
    elif self.page_type == 'zhihu_article':
      zhihu_article = fetch_zhihu_article(self.url)
      page = self.remember(zhihu_article)
      return page
    else:
      raise

  @classmethod
  def multiple_watch(cls, sleep_seconds=10, limit=10):
    count = Task.report()
    if count == 0:
      log('current no tasks')
      return

    limit = min(limit, count)
    for i in range(1, limit+1):
      now = datetime.now()
      log('\nloop {}/{} current_time={}'.format(i, limit, convert_time(now)))
      task = Task.select().order_by(Task.next_watch).get()
      if not task:
        log('can not find any task')
        continue
      elif task.next_watch <= now:
        log('start: {}'.format(task))
        page = task.watch()
        next_time = convert_time(task.next_watch, humanize=True)
        log('done!  {} (next watch: {})'.format(page, next_time))
        time.sleep(sleep_seconds)
      else:
        log('not today... {}'.format(task))





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
    # 推迟时间算法有问题, 如果几分钟内反复fetch,
    # 基本不会有内容变化, 将导致下一次获取时间极大的延后
    self.next_watch = now + timedelta(seconds=seconds)
    self.title = data['title'].strip()
    self.save()
    return page








  @property
  def last_page(self):
    query = Page.select().where(Page.task == self)
    if query:
      last_page = query.order_by(-Page.watch_date).get()
      return last_page
    else:
      raise ValueError('cannot find any page on {}'.format(self))


  @property
  def pages(self):
    query = Page.select().where(Page.task == self)
    if query:
      return list(query.order_by(Page.watch_date))
    else:
      return []






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
    s = '<Page title="{}" (version {})\n  watch_date on {} ({}) |{}|\n  {!r}>'
    return s.format(self.title, self.version,
                    convert_time(self.watch_date),
                    convert_time(self.watch_date, humanize=True),
                    self.topic,
                    form(self.content, text_maxlen=300))

  def same_as_last(self):
    '''此时 page self 应当尚未储存
    取最新的 version 的 content 与尚未储存的 page content 对比'''
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


  def to_dict(self):
    return {'title': self.title,
            'full_content': self.full_content,
            'author': self.author,
            'watch_date': self.watch_date,
            'url': self.url,
            }


  def to_local_file(self, folder, file_name=None,
                    fetch_images=True, overwrite=False):
    if not file_name:
      file_name = self.title
    if not os.path.exists(folder):
      os.makedirs(folder)

    save_path = folder + '/' + remove_invalid_char(file_name) + '.md'
    if not overwrite:
      if os.path.exists(save_path):
        log('already exist {}'.format(save_path))
        return save_path

    rendered = self.full_content

    with open(save_path, 'w', encoding='utf-8') as f:
      f.write(rendered)
      log('write {} done'.format(save_path))

    if fetch_images:
      # 本地存储, 需要抓取所有附图
      fetch_images_for_markdown(save_path)
    return save_path






  @property
  def full_content(self):
    data = self
    rendered = fill_full_content(data)
    return rendered


  @property
  def comments(self):
    return self.comment


  @property
  def url(self):
    return self.task.url
















'''
####### #######  ###### #######
   ##   ##      ##         ##
   ##   ######   #####     ##
   ##   ##           ##    ##
   ##   ####### ######     ##
'''

def test_new_task():
  # url = 'https://www.zhihu.com/question/30595784/answer/49194862'
  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  url = 'https://www.zhihu.com/question/22316395/answer/100909780'
  url = 'https://www.zhihu.com/question/47220155/answer/118154455'
  url = 'https://www.zhihu.com/question/49962599/answer/118716273'
  url = 'https://zhuanlan.zhihu.com/p/19837940'
  url = 'https://zhuanlan.zhihu.com/p/20639779'
  url = 'https://zhuanlan.zhihu.com/p/20153329'
  url = 'https://zhuanlan.zhihu.com/p/21281864'
  url = 'https://zhuanlan.zhihu.com/p/19964142'
  task = Task.add(url=url)
  print(task)
  # task.watch()


def test_readd_task():
  url = 'http://www.zhihu.com/question/22513722/answer/21967185' # 火车票涨价
  task = Task.add(url=url)
  task = Task.add(url=url)
  url = 'https://www.zhihu.com/question/30957313/answer/50266448' # 古典音乐
  task = Task.add(url=url)
  url = 'https://www.zhihu.com/question/40056948/answer/110794550' # 四万亿
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


def test_to_local_file():
  # page = Page.select().order_by(-Page.id).get()

  # page = Page.select(Page.topic).distinct().where(Page.topic.contains('房')).limit(5)
  # q = Page.select(Page.id).distinct()
  # for p in q:
  #   print(p)
  query = (Page.select(Page, Task)
           .join(Task)
           .where(Page.author == 'chenqin')  # .where(Page.topic.contains('建筑'))
           .group_by(Page.task)
           .having(Page.watch_date == fn.MAX(Page.watch_date))
           .limit(8800))
  for page in query:
    log(page.title)
    # log(page.metadata)
    # page.to_local_file(folder='chen', fetch_images=False)
# test_to_local_file()

def test_to_local_file__2():

  query = (Page.select(Page, Task)
           .join(Task)
           .where((Task.page_type == 'zhihu_article') & (Page.author == 'More'))
           .group_by(Page.task)
           .having(Page.watch_date == fn.MAX(Page.watch_date))
           .limit(8800))
  for page in query:
    log(page.title)
    page.to_local_file(folder='more', fetch_images=True)






def test_tools():
  import pylon
  pylon.generate_figlet('task', fonts=['space_op'])
  pylon.generate_figlet('page', fonts=['space_op'])
  pylon.generate_figlet('test', fonts=['space_op'])




def test_fetch_topic():
  # topic_id = 19551424 # 政治
  # topic_id = 19556950 # 物理学
  # topic_id = 19612637 # 科学
  # topic_id = 19569034 # philosophy_of_science 科学哲学
  # topic_id = 19555355 # 房地产
  # topic_id = 19641972 # 货币政策
  # topic_id = 19565985 # 中国经济
  topic_id = 19644231 # 古建筑
  topic_id = 19582176 # 建筑设计
  topic_id = 19573393 # 建筑史
  topic_id = 19568972 # 建筑学
  # topic_id = 19551864 # 古典音乐
  Task.add_by_topic_best_answers(topic_id, limit=3000, min_voteup=50,
                                 stop_at_existed=200, force_start=False)
# test_fetch_topic()



def test_add_task_by_author():

  ids = '''
  shi-yidian-ban-98
  xbjf
  zhao-hao-yang-1991
  mandelbrot-11
  chenqin
  leng-zhe


  # cai-tog
  # shu-sheng-4-25
  # done BlackCloak
  # done ma-bo-yong
  # done hutianyi
  # done lawrencelry
  # done Metaphox
  # done calon


  # done xiepanda
  # done cogito
  # done talich
  # done commando
  # done fu-er

  # done spto



  # done xu-zhe-42


  # tassandar
  # zhou-xiao-nong
  # yinshoufu
  # huo-zhen-bu-lu-zi-lao-ye
  # tangsyau
  # lianghai
  '''
  for author_id in datalines(ids):
    # for answer in yield_author_answers(id, limit=3000, min_voteup=100):
    #   url = zhihu_answer_url(answer)
    #   count += 1
    #   log('<{}> {}'.format(count, url))
    #   Task.add(url=url)
    log(author_id)
    Task.add_by_author(author_id, limit=3000, min_voteup=50,
                       stop_at_existed=5,
                       force_start=False)

# test_add_task_by_author()



def test_add_articles():
  author_id = 'chenqin'
  author_id = 'chenqin'
  Task.add_articles(author_id=author_id, limit=3000, min_voteup=10,
                    stop_at_existed=30)

def test_add_articles__2():
  column_id = 'wontfallinyourlap'
  column_id = 'necromanov'
  column_id = 'smartdesigner'
  Task.add_articles(column_id=column_id, limit=3000, min_voteup=500,
                    stop_at_existed=30)



def test_load_json():
  import json

  print(json.loads(open('mockup_topic_answers.json', encoding='utf-8').read()))




def test_banned_modes():
  url = 'https://www.zhihu.com/question/40679967/answer/88310495'
  # 政府推出开放小区政策的真正目的是什么？ 2201 孟德尔 回答建议修改：政治敏感
  pass

def test_explore():
  # Tweet.select(fn.COUNT(Tweet.id)).where(Tweet.user == User.id)
  query = (Task
           .select(Task, fn.COUNT(Page.id).alias('fetched_count'))
           .join(Page)
           .group_by(Task.title)
           .limit(50)
           .offset(200)
           .order_by(fn.COUNT(Page.id).desc()))

  for task in query:
    log(task.title + ' : ' + str(task.fetched_count) + '  task_id ' + str(task.id))

def test_explore_watching_results_diff():

  import difflib

  # 美国是不是正在为瓦解中国做准备？ - 张俊麒的回答 : 16  task_id 46

  s = '''
为什么很少看到患者砍莆田系医生的报道？ - 玄不救非氪不改命的回答 : 3  task_id 196
为什么很难证伪马克思主义理论？ - 玄不救非氪不改命的回答 : 3  task_id 360
为什么快速浏览一段内容的时候，很容易看到自己感兴趣的部分？ - 采铜的回答 : 3  task_id 742
为什么拿广州恒大淘宝队与中国国家男子足球队做对比？ - 玄不救非氪不改命的回答 : 3  task_id 492
为什么教育部门至今没有实现高考在省际的公平化？ - 玄不救非氪不改命的回答 : 3  task_id 368
为什么文革时期故宫没有被砸？ - 书生的回答 : 3  task_id 690
为什么斯大林作为一个格鲁吉亚人却会成为一个大俄罗斯主义者而执著地服务于俄民族利益而不是相反呢？ - 玄不救非氪不改命的回答 : 3  task_id 396
为什么时间箭头是单向的，即为什么时间的流动是单向的呢？ - Mandelbrot的回答 : 3  task_id 612
为什么明显矛盾的《国际歌》与《东方红》会共存？ - 玄不救非氪不改命的回答 : 3  task_id 225
为什么星球都是球形的？ - Mandelbrot的回答 : 3  task_id 599
为什么有了县长还要县委书记？ - 玄不救非氪不改命的回答 : 3  task_id 440
为什么有些人说马克思是人渣？ - 玄不救非氪不改命的回答 : 3  task_id 485
为什么有些人连街头小偷都不敢呵斥，却发誓跟美国兵血战到底？ - 玄不救非氪不改命的回答 : 3  task_id 125
为什么有些异地考生觉得北京学生 400~500 就能上北大清华呢？ - 玄不救非氪不改命的回答 : 3  task_id 154
为什么有人支持黑龙江延寿县高玉伦越狱？ - 赵皓阳的回答 : 3  task_id 571
为什么有关北大清华在京录取比例的讨论中，往往忽视了各大高校对本地招生均有偏向性的事实？ - 玄不救非氪不改命的回答 : 3  task_id 152
为什么有关部门不治理莆田系医院？ - 玄不救非氪不改命的回答 : 3  task_id 205
为什么有的人喜欢吃五仁月饼？ - 赵皓阳的回答 : 3  task_id 573
为什么朱元璋用重刑解决不了贪腐问题？ - 玄不救非氪不改命的回答 : 3  task_id 406
为什么每年招那么多公务员，基层还是很缺人？ - 玄不救非氪不改命的回答 : 3  task_id 167
为什么满族没有省级自治区？ - 玄不救非氪不改命的回答 : 3  task_id 123
为什么生命起源一定要有水，不能存在一种外星文明是以液态乙醇什么的为生命之源的吗？ - Mandelbrot的回答 : 3  task_id 585
为什么科学家要假设存在暗物质？ - Mandelbrot的回答 : 3  task_id 689
为什么第三次长沙会战日军伤亡的统计中日之间如此悬殊？ - 书生的回答 : 3  task_id 709
为什么网上对朱镕基的评价两极非常明显？ - 书生的回答 : 3  task_id 691
为什么网友对警察扫黄这么不满？他们不满的到底是什么？ - 玄不救非氪不改命的回答 : 3  task_id 191
为什么舟山发展这么慢？ - 玄不救非氪不改命的回答 : 3  task_id 175
为什么蔡振华能当足协主席？ - 玄不救非氪不改命的回答 : 3  task_id 424
为什么街区制在之前被很多知友认为是解决堵车的良方，非常支持。但当国家出台街区制之后知友们又大多反对呢？ - 玄不救非氪不改命的回答 : 3  task_id 348
为什么要感谢日本侵略？ - 书生的回答 : 3  task_id 693
为什么许多人不愿意相信现在乌克兰、伊拉克、阿富汗、利比亚处于民主的阵痛期呢？ - 玄不救非氪不改命的回答 : 3  task_id 478
为什么贾静雯晒娃评论一片赞美甚至网友提出多晒，而范玮琪当初就被骂很惨？ - 玄不救非氪不改命的回答 : 3  task_id 256
为什么那么多人喷朋友圈？ - 赵皓阳的回答 : 3  task_id 541
为什么部分历史书说国民党消极抗日？ - 书生的回答 : 3  task_id 698
为什么部分西方人认为西藏是一个国家？ - 玄不救非氪不改命的回答 : 3  task_id 216
为什么雷锋精神没成为普世价值？ - 玄不救非氪不改命的回答 : 3  task_id 309
为何 33 万人口的冰岛足球水平可观？ - 玄不救非氪不改命的回答 : 3  task_id 141
为何东欧国家基本都走过了社会主义道路，而西欧国家却基本没有？ - 玄不救非氪不改命的回答 : 3  task_id 300
为何殷素素在临死之前对张无忌说「越好看的女人越会骗人」 这句遗言在整部书里有何意义？ - 玄不救非氪不改命的回答 : 3  task_id 264
乌克兰、塞尔维亚、格鲁吉亚这些欧洲国家老龄化严重，且人均GDP很低，是未富先老典型。他们怎么办？ - 玄不救非氪不改命的回答 : 3  task_id 409
九一八事变，张学良为什么下不抵抗命令而丧权辱国？ - 书生的回答 : 3  task_id 699
二战后德国怎么被西方国家重新接受的？ - 玄不救非氪不改命的回答 : 3  task_id 466
二战没有国军的正面战场，中国单靠游击战能坚持到二战胜利吗？ - 玄不救非氪不改命的回答 : 3  task_id 163
二维世界的的物理定律是怎样的? - Mandelbrot的回答 : 3  task_id 616
于正又要拍《倚天屠龙记》，大陆港台演员，谁能胜任张无忌，赵敏，周芷若？这几个角色历代谁演的最好呢？ - 玄不救非氪不改命的回答 : 3  task_id 260
互联网领域的「用户研究」有哪些有趣的发现？ - 采铜的回答 : 3  task_id 718
人有翅膀能飞吗？ - Mandelbrot的回答 : 3  task_id 622
人民币汇率是如何形成的？中国能算「汇率操纵国」吗？ - 冷哲的回答 : 3  task_id 1213
人类将来的技术水平有可能延长太阳的「寿命」吗? - Mandelbrot的回答 : 3  task_id 657
人类是否生活在电脑模拟出来的宇宙之中？ - Mandelbrot的回答 : 3  task_id 686
  '''

  for line in datalines(s):
    task_id = int(line.split('task_id')[-1][1:])
    # log(task_id)
    task = Task.select().where(Task.id == task_id).get()
    log(task)
    # log(task.pages)

    contents = [fix_in_compare(p.content) for p in task.pages]
    metas = [p.metadata for p in task.pages]

    # for meta in metas:
    #   log(meta)


    c0 = contents[0].split('\n')
    c_1 = contents[-1].split('\n')
    # diff = difflib.ndiff(c0, c_1)
    # for line in diff:
    #   log(line)
    changes = [l for l in difflib.ndiff(c0, c_1) if l.startswith('+ ') or l.startswith('- ')]
    for c in changes:
      log(c)

    log('------------------------\n\n')

def fix_in_compare(text):
  import re
  img_reg = r'\n*\!\[\]\((https?://pic[^()]+?(\.jpg|\.png|\.gif))\)\n*'
  pattern_img_start_inline = re.compile(img_reg)
  def replace_img_start_inline(mat):
    # 保证生成的 *.md 图片在新的一行
    s = mat.group(0)
    while not s.startswith('\n\n'):
      s = '\n' + s
    while not s.endswith('\n\n'):
      s = s + '\n'
    return s

  text = pattern_img_start_inline.sub(replace_img_start_inline, text)

  pattern_img_https = re.compile(r'http://pic(\d)\.zhimg\.com')
  text = pattern_img_https.sub(r'https://pic\1.zhimg.com', text)
  return text


def test_explore_voteup_thanks():
  '''感谢赞同比跟文章质量没啥关系'''
  query = (Page.select(Page, Task)
           .join(Task)
           .where((Task.page_type == 'zhihu_answer'))
           .group_by(Page.task)
           .having(Page.watch_date == fn.MAX(Page.watch_date))
           .limit(50)
           .order_by(fn.Random())
           )

  def thanks_voteup_ratio(page):
    thanks = int(page.metadata.split('thanks: ')[1].split(' ')[0])
    voteup = int(page.metadata.split('voteup: ')[1].split(' ')[0])
    return round(thanks / voteup, 3)

  # for page in query:
  #   log(page.title)

  pages = sorted(query, key=thanks_voteup_ratio)
  for page in pages:
    log(page.title)
    log(repr(page.content[:500]))
    log(thanks_voteup_ratio(page))
    log('-----------------\n\n\n')
