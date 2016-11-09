


# import time
# import os

from pylon import datalines
from pylon import grep_before
from pylon import create_logger

log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')

from peewee import fn

from models import Task
from models import Page



import sys

if len(sys.argv) == 2 and sys.argv[1].isdigit:
  # cmd> python loop_watch.py 100
  limit = int(sys.argv[1])
  Task.multiple_watch(sleep_seconds=11, limit=limit)
  Task.report()

else:
  print('not enter loop watch', sys.argv)




def test_to_local_file():
  # page = Page.select().order_by(-Page.id).get()

  # page = Page.select(Page.topic).distinct().where(Page.topic.contains('房')).limit(5)
  # q = Page.select(Page.id).distinct()
  # for p in q:
  #   print(p)
  query = (Page.select(Page, Task)
           .join(Task)
           .where(Page.author == '十年寒霜')  # .where(Page.topic.contains('建筑'))
           .group_by(Page.task)
           .having(Page.watch_date == fn.MAX(Page.watch_date))
           .limit(8800))
  for page in query:
    log(page.title)
    # log(page.metadata)
    page.to_local_file(folder='test', fetch_images=False)
# test_to_local_file()

def test_to_local_file__2():

  query = (Page.select(Page, Task)
           .join(Task)
           .where((Task.page_type == 'zhihu_article') & (Page.title.contains('最前沿')))
           .group_by(Page.task)
           .having(Page.watch_date == fn.MAX(Page.watch_date))
           .limit(9999))
  for page in query:
    log(page.title)
    log(page.task)
    page.to_local_file(folder='zhi3', fetch_images=False)








def test_fetch_topic():
  topic_id = 19551424 # 政治
  # topic_id = 19556950 # 物理学
  # topic_id = 19612637 # 科学
  # topic_id = 19569034 # philosophy_of_science 科学哲学
  # topic_id = 19555355 # 房地产
  # topic_id = 19641972 # 货币政策
  # topic_id = 19565985 # 中国经济
  # topic_id = 19644231 # 古建筑
  # topic_id = 19582176 # 建筑设计
  # topic_id = 19573393 # 建筑史
  topic_id = 19568972 # 建筑学
  # topic_id = 19574449 # 冰与火之歌（小说）
  # topic_id = 19551864 # 古典音乐
  Task.add_by_topic_best_answers(topic_id, limit=3000, min_voteup=600,
                                 stop_at_existed=100, force_start=False)
# test_fetch_topic()



def test_add_task_by_author():

  ids = '''
  shi-yidian-ban-98
  xbjf
  zhao-hao-yang-1991
  mandelbrot-11
  chenqin
  leng-zhe
  spto
  xiepanda
  cogito
  xu-zhe-42
  huo-zhen-bu-lu-zi-lao-ye

  cai-tong
  shu-sheng-4-25
  BlackCloak
  ma-bo-yong
  hutianyi
  Metaphox
  calon

  ma-qian-zu
  skiptomylou

  sinsirius 费寒冬
  shinianhanshuang 十年寒霜
  youhuiwu 程步一
  xie-wei-54-24


  # talich
  # commando
  # fu-er
  # tassandar
  # zhou-xiao-nong
  # yinshoufu
  # tangsyau
  # lianghai
  '''
  for author_id in datalines(ids):
    # for answer in yield_author_answers(id, limit=3000, min_voteup=100):
    #   url = zhihu_answer_url(answer)
    #   count += 1
    #   log('<{}> {}'.format(count, url))
    #   Task.add(url=url)
    if ' ' in author_id:
      author_id = author_id | grep_before(' ')
    log(author_id)
    Task.add_by_author(author_id, limit=2000, min_voteup=1,
                       stop_at_existed=5,
                       force_start=False)

# test_add_task_by_author()



def test_add_articles():
  author_id = 'chenqin'
  author_id = 'du-ke'
  author_id = 'flood-sung'
  author_id = 'hmonkey'
  Task.add_articles(author_id=author_id, limit=3000, min_voteup=1,
                    stop_at_existed=300)



def test_add_articles_by_zhuanlan_title():
  column_ids = '''
    wontfallinyourlap
    necromanov
    smartdesigner
    plant
    jingjixue
    # 天淡银河垂地
    Mrfox
    laodaoxx
    startup
    intelligentunit
    musicgossip


    pianofanie
    c-sharp-minor
    # uqer2015
  '''
  for column_id in datalines(column_ids):
    Task.add_articles(column_id=column_id, limit=3000, min_voteup=1,
                      stop_at_existed=5)





def test_fetch_history():
  url = 'https://www.zhihu.com/question/40103788/answer/124499334'
  # query = (Page.select(Page, Task)
  #          .join(Task)
  #          .where((Task.page_type == 'zhihu_article') & (Page.title.contains('最前沿')))
  #          .group_by(Page.task)
  #          .having(Page.watch_date == fn.MAX(Page.watch_date))
  #          .limit(9999))
  t = Task.select().where(Task.url == url).get()
  for page in t.pages:

    log(page.version)
    log(page.title)
    log(page.content)
