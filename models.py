




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
        # log('already watching {} {}'.format(t.title, existed_count))
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
        log('  already watching {} {}'.format(t.title, existed_count))
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
        # log('already watching {} {}'.format(t.title, existed_count))
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
      try:
        zhihu_article = fetch_zhihu_article(self.url)
        page = self.remember(zhihu_article)
        return page
      except ZhihuParseError as e:
        blank_article = e.value
        log_error('!! 文章已删除 {} {}'.format(self.url, blank_article['title']))
        page = self.remember(blank_article)
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
    # if self.topic != other.topic:
    #   return False
    # if self.question != other.question:
    #   return False
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
  url = 'https://www.zhihu.com/question/50763374/answer/122822226'
  url = 'https://www.zhihu.com/question/40910547/answer/123021503'
  url = 'https://zhuanlan.zhihu.com/p/21478575'
  url = 'https://www.zhihu.com/question/40103788/answer/124499334'
  task = Task.add(url=url)
  task.watch()


  task.last_page.to_local_file(folder='test', fetch_images=False)



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

def test_tools():
  import pylon
  pylon.generate_figlet('task', fonts=['space_op'])
  pylon.generate_figlet('page', fonts=['space_op'])
  pylon.generate_figlet('test', fonts=['space_op'])


def test_load_json():
  import json

  print(json.loads(open('mockup_topic_answers.json', encoding='utf-8').read()))


def test_banned_modes():
  url = 'https://www.zhihu.com/question/40679967/answer/88310495'
  # 政府推出开放小区政策的真正目的是什么？ 2201 孟德尔 回答建议修改：政治敏感
  pass


def test_query_task():
  s = 'https://www.zhihu.com/question/48737226/answer/113036453'
  s = 'https://www.zhihu.com/question/47220155/answer/118154455'
  s = 'https://www.zhihu.com/question/49545583/answer/116529877'

  t = Task.select().where(Task.url == s)
  t = t.get()
  log(t.title)
  log(t.id)






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

  s = '''
  # 美国是不是正在为瓦解中国做准备？ - 张俊麒的回答 : 16  task_id 46
  # 为什么很少看到患者砍莆田系医生的报道？ - 玄不救非氪不改命的回答 : 3  task_id 196
  # 为什么很难证伪马克思主义理论？ - 玄不救非氪不改命的回答 : 3  task_id 360
  # 为什么快速浏览一段内容的时候，很容易看到自己感兴趣的部分？ - 采铜的回答 : 3  task_id 742
  # 为什么拿广州恒大淘宝队与中国国家男子足球队做对比？ - 玄不救非氪不改命的回答 : 3  task_id 492
  # 如何看待里约奥运陈欣怡药检呈阳性反应？ - 玄不救非氪不改命的回答 : 3  task_id 2393
  # 为什么厌恶「国粉」的知乎用户远多于厌恶「毛粉」的？ - chenqin的 : 3  task_id 3313
  # 2016 年中国的经济状况很差吗？真实状况是怎样的？ - 垒起善城堡的积木 : 3 task_id 2387
  # 如何看待2016年7月人民币贷款增幅里9.8成为房贷？ - 匿名用户的回答 : 3 task_id 2386




  # 怎样评价「游戏不汉化就差评」的行为？ - cOMMANDO的回答 : 9  task_id 4471
  # 既然有报道说人类的基因片段只占DNA序列总长的不到10%，那么这几个问题怎么解答？ - Mandelbrot的回答 : 9  task_id 676
  # 智商低的人真的不适合玩需要动脑子的游戏么？ - 匿名用户的回答 : 9  task_id 3461
  # 暴雪，Valve，拳头，谁更厉害？ - cOMMANDO的回答 : 9  task_id 2597
  # 有一个稀有的姓是一种怎样的体验？ - 冷哲的回答 : 9  task_id 1041
  # 有什么影视作品是当时演员名气不大，现在看来是全明星阵容出演？ - 玄不救非氪不改命的回答 : 9  task_id 484
  # 有关白龙尾岛的历史，哪些是有据可查的？ - 书生的回答 : 9  task_id 712
  # 有哪些「智商税」？ - 谢熊猫君的回答 : 9  task_id 2406
  # 有哪些令人拍案叫绝的临场反应？ - 大盗贼霍老爷的回答 : 9  task_id 4107
  # 有哪些可怕的故事？ - 大盗贼霍老爷的回答 : 9  task_id 4137
  # 有哪些长得比较逆天的动物？ - Mandelbrot的回答 : 9  task_id 648
  # 有文化有多可怕？ - 寺主人的回答 : 9  task_id 5787
  # 机器人教育这种不考试、以娱乐为主的教育对于中小学生及幼儿的意义何在？ - 冷哲的回答 : 9  task_id 1015
  # 毛花三年打败蒋然后走三十年弯路的目的，都是为后三十年的改革开放走资、大国崛起做铺垫扫平道路的么？ - 书生的回答 : 9  task_id 99
  # 水旱蝗汤中的汤指的到底是谁？ - 书生的回答 : 9  task_id 104
  # 河南的地理位置那么好，为什么经济落后？ - 大盗贼霍老爷的回答 : 9  task_id 4105
  # 為什麼蒋介石被称为运输大队长？求详? - 书生的回答 : 9  task_id 701
  # 玩《狼人杀》时你有什么屡试不爽的秘技诀窍？ - 汪诩文的回答 : 9  task_id 3526

  现在网络上很多人黑一些伟人，比如说周半期，黑鲁迅。他们是什么心态？ - 书生的回答 : 9  task_id 97
  看美剧、英剧学英语有什么有效的方法吗？ - 采铜的回答 : 9  task_id 787
  章鱼的智商到底有多高，为什么有人说它们的智商可以统治世界? - Mandelbrot的回答 : 9  task_id 588
  类似 AlphaGo 的人工智能在游戏王、万智牌等卡牌游戏中胜率如何？ - 莫名的回答 : 9  task_id 3724
  给 59 分强行不给过的老师是一种怎么样的存在？ - chenqin的回答 : 9  task_id 3317
  网络上有哪些广为流传的「历史真相」其实是谣言？ - 马前卒的回答 : 9  task_id 5089
  美国南北战争的真正原因是什么？ - talich的回答 : 9  task_id 2571
  美国发动伊拉克战争的核心原因到底是什么？ - 冷哲的回答 : 9  task_id 1332
  美国最高法院大法官 Scalia 的去世将会带来怎样的影响？ - talich的回答 : 9  task_id 4423
  美国有人在开车在路上故意把川普的竞选宣传牌碾倒，如何评价这种因为不同政见而破坏对方财物的行为？ - talich的回答 : 9  task_id 4412
  装逼成功是怎样一种体验？ - 大盗贼霍老爷的回答 : 9  task_id 4048
  谁最应该被印在人民币上面？ - 蜂鸟的回答 : 9  task_id 2274
  豆瓣的核心用户都有什么特点？ - 十一点半的回答 : 9  task_id 84
  赌场有哪些看似不起眼，实则心机颇深的设计？ - 第一喵的回答 : 9  task_id 3158
  赌场有哪些看似不起眼，实则心机颇深的设计？ - 肥肥猫的回答 : 9  task_id 3151
  雷锋是个什么样的人，怎么客观评价雷锋？ - 书生的回答 : 9  task_id 96
  鲁迅和秋瑾的关系好吗？ - 书生的回答 : 9  task_id 91
  1927 年蒋介石为什么要清党？ - 冷哲的回答 : 8  task_id 1415
  1949年以后的中国本土设计的建筑中，哪些能称得上是有思想的好建筑？ - Chilly的回答 : 8  task_id 3104
  2015 年初，中国制造业形势有多严峻？ - 稻可道 稻子的稻的回答 : 8  task_id 2239
  2016 年，中国房地产泡沫是否会在一两年内破灭，从而引发金融危机？ - Bee Mad的回答 : 8  task_id 2104
  2016 年，中国房地产泡沫是否会在一两年内破灭，从而引发金融危机？ - 君临的回答 : 8  task_id 2205
  2016 年，中国房地产泡沫是否会在一两年内破灭，从而引发金融危机？ - 小马的回答 : 8  task_id 5752
  ISIS 是一个什么样的组织？它的资金是哪来的？ - 罗晓川的回答 : 8  task_id 39
  Lambda 表达式有何用处？如何使用？ - 涛吴的回答 : 8  task_id 2008
  Signal Weighting---基于因子IC的因子权重优化模型 - 陈颖的专栏 量化哥 : 8  task_id 6007
  Smart Beta 投资方法 - 陈颖的专栏 量化哥 : 8  task_id 6017
  ofo 获滴滴数千万美元C轮投资，然后呢？ - 曲凯的专栏 创投方法论 : 8  task_id 5656
  《文明 6 》中的背景音乐都有什么来历？ - PenguinKing的回答 : 8  task_id 6250
  《权力的游戏》你觉得最可怜的人是谁？ - 苏鲁的回答 : 8  task_id 4576
  《蒋介石日记》和《毛泽东选集》差距有多大？ - 马前卒的回答 : 8  task_id 5355
  「心灵鸡汤」式的文章错在哪？ - 赵皓阳的回答 : 8  task_id 584
  '''

  for line in datalines(s):
    task_id = int(line.split('task_id')[-1][1:])
    # log(task_id)
    task = Task.select().where(Task.id == task_id).get()
    log(task)
    # log(task.pages)
    # log(task.last_page)
    contents = [fix_in_compare(p.content) for p in task.pages]
    # questions = [fix_in_compare(p.question) for p in task.pages]
    titles = [p.title for p in task.pages]

    # metas = [p.metadata for p in task.pages]
    # for meta in metas:
    #   log(meta)
    # compare_text_sequence(titles, label='titles')
    # compare_text_sequence(questions, label='questions')
    compare_text_sequence(contents, label='contents')

    log('\n\n\n')



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


def compare_text(t1, t2, prefix=''):
  import difflib
  changes = [l for l in difflib.ndiff(t1.split('\n'), t2.split('\n')) if l.startswith(('+ ', '- '))]
  for change in changes:
    log(prefix + change)
  return changes


def compare_text_sequence(texts, label=''):
  from pylon import dedupe
  from pylon import windows

  texts = list(dedupe(texts))
  if len(texts) > 1:
    log('detect changed {}'.format(label))
    for t1, t2 in windows(texts, length=2, overlap=1):
      compare_text(t1, t2, prefix='  ')
  else:
    log('nothing changed {}'.format(label))



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
