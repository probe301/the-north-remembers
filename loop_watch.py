import sys
import tools
from fetcher import parse_type
from fetcher import UrlType
from tools import create_logger

log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')




def test_to_local_file():
  # page = Page.select().order_by(-Page.id).get()

  # page = Page.select(Page.topic).distinct().where(Page.topic.contains('房')).limit(5)
  # q = Page.select(Page.id).distinct()
  # for p in q:
  #   print(p)
  query = (Page.select(Page, Task)
           .join(Task)
           .where(Page.author == '地平线机器人技术')  # .where(Page.topic.contains('建筑'))
           .group_by(Page.task)
           .having(Page.watch_date == fn.MAX(Page.watch_date))
           .limit(8800))
  for page in query:
    log(page.title)
    # log(page.metadata)
    page.to_local_file(folder='deep3', fetch_images=False)
# test_to_local_file()




def test_to_local_file__2():

  query = (Page.select(Page, Task)
           .join(Task)
           .where((Task.page_type == 'zhihu_article') & (Page.title.contains('深度学习大讲堂')))
           .group_by(Page.task)
           .having(Page.watch_date == fn.MAX(Page.watch_date))
           .limit(9999))
  for page in query:
    log(page.title)
    log(page.task)
    page.to_local_file(folder='deep3', fetch_images=False)


def test_to_local_file_3():

  query = (Page.select(Page, Task)
           .join(Task)
           .where(Page.topic.contains('矩阵'))
           .group_by(Page.task)
           .having(Page.watch_date == fn.MAX(Page.watch_date))
           .limit(8800))
  for page in query:
    log(page.title)
    # log(page.metadata)
    page.to_local_file(folder='deep', fetch_images=False)
# test_to_local_file()




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
  # topic_id = 19568972 # 建筑学
  # topic_id = 19574449 # 冰与火之歌（小说）
  # topic_id = 19551864 # 古典音乐
  topic_id = 19577698 # 线性代数
  topic_id = 19650614 # 矩阵
  Task.add_by_topic_best_answers(topic_id, limit=3000, min_voteup=50,
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

  # huo-zhen-bu-lu-zi-lao-ye  用户没了 404 需要处理异常

  cai-tong
  shu-sheng-4-25
  BlackCloak
  ma-bo-yong
  hutianyi
  Metaphox
  calon

  ma-qian-zu
  skiptomylou

  di-ping-xian-ji-qi-ren-ji-shu

  sinsirius 费寒冬
  shinianhanshuang 十年寒霜
  youhuiwu 程步一
  xie-wei-54-24
  lianghai


  # talich
  # commando
  # fu-er
  # tassandar
  # zhou-xiao-nong
  # yinshoufu
  # tangsyau
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
                       stop_at_existed=5, force_start=False)
    Task.add_articles(author_id, limit=3000, min_voteup=1,
                      stop_at_existed=5, force_start=False)
# test_add_task_by_author()



def test_add_articles():
  author_id = 'chenqin'
  author_id = 'du-ke'
  author_id = 'flood-sung'
  author_id = 'hmonkey'
  Task.add_articles(author_id=author_id, limit=3000, min_voteup=1,
                    stop_at_existed=300)



def test_yield_colum():
  Task.add_articles(column_id='wontfallinyourlap', limit=3000, min_voteup=1,
                    stop_at_existed=5)


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
    wx-math
    # 那些年那些有趣的数学
    symmetry
    # 在物质世界的角落

    pianofanie
    c-sharp-minor
    xiaoleimlnote
    hsmyy
    dlclass
    # 深度学习大讲堂

    uqer2015
    # c_29122335
    # 混沌巡洋舰
    learningtheory
    c_78213311
    # 彩虹尽头
  '''
  for column_id in datalines(column_ids):
    # 2017.04.18 现在 yield_articles 不能认出 voteup_count 了, 全是 0
    Task.add_articles(column_id=column_id, limit=3000, min_voteup=0,
                      stop_at_existed=5)


def test_add_articles_by_author():
  # 大牛讲堂 | 第一期：深度学习 之 Sequence Learning
  Task.add_articles(author_id='di-ping-xian-ji-qi-ren-ji-shu',
                    limit=3000, min_voteup=1,
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


def test_add_new_task():

  url = 'https://www.zhihu.com/question/51936651/answer/130915660'
  # url = 'https://zhuanlan.zhihu.com/p/23149710'
  # url = 'http://www.zhihu.com/question/51331837/answer/130295341'
  task = Task.add(url=url)
  print(task)
  print(task.title)


def test_save_zhuanlan():
  query = (Page.select(Page, Task)
           .join(Task)
           .where((Task.page_type == 'zhihu_article') & (Page.title.contains('战略航空军元帅的旗舰')))
           .group_by(Page.task)
           .having(Page.watch_date == fn.MAX(Page.watch_date))
           .limit(9999))
  for page in query:
    log(page.title)
    log(page.task)
    page.to_local_file(folder='test', fetch_images=False)


def test_get_comment_list_id():
  # 似乎是改成 react 了, 然后有时无法获取 aid
  # find('div.zm-item-answer').attr('data-aid')
  from zhihu_answer import get_old_fashion_comments
  url = 'https://www.zhihu.com/question/52284957/answer/130185745'
  d = get_old_fashion_comments(url)
  print(d)
  for i in d:
    print(i.content)












'''
####### ##   ## ####### ######
##       ## ##  ##     ###
######    ###   ###### ##
##       ## ##  ##     ###
####### ##   ## ####### ######
'''

def exec_save_from_collections():
  # 采铜 的收藏 我心中的知乎TOP100
  url = 'http://www.zhihu.com/collection/19845840'
  smart_save(url, limit=3000,
             min_voteup=100, max_voteup=500000000,
             overwrite=False)

# exec_save_from_collections()

def exec_save_from_authors():
  # url = 'https://www.zhihu.com/people/xbjf/'  # 玄不救非氪不改命
  # url = 'https://www.zhihu.com/people/zhao-hao-yang-1991'  # 赵皓阳
  # url = 'https://www.zhihu.com/people/mandelbrot-11'  # Mandelbrot
  # url = 'https://www.zhihu.com/people/shi-yidian-ban-98'  # shiyidianban
  # url = 'https://www.zhihu.com/people/heismail' # 卡夫卡斯
  # url = 'https://www.zhihu.com/people/shu-sheng-4-25' # 书生
  # url = 'https://www.zhihu.com/people/cai-tong' # 采铜
  url = 'https://www.zhihu.com/people/chenqin'
  url = 'https://www.zhihu.com/people/Huang-Lei-970106'
  smart_save(url, folder=None, limit=4000, min_voteup=1, overwrite=False)
# exec_save_from_authors()


def exec_save_answers():
  urls = '''
    # https://www.zhihu.com/question/40305228/answer/86179116
    # https://www.zhihu.com/question/36466762/answer/85475145
    # https://www.zhihu.com/question/33246348/answer/86919689

    https://www.zhihu.com/question/31073228/answer/66187805
    # https://www.zhihu.com/question/39906815/answer/88534869

    # https://www.zhihu.com/question/40700155/answer/89002644
    # https://www.zhihu.com/question/36380091/answer/84690117
    # https://www.zhihu.com/question/33246348/answer/86919689
    # https://www.zhihu.com/question/35254746/answer/90252213
    # https://www.zhihu.com/question/23618517/answer/89823915

    # https://www.zhihu.com/question/40677000/answer/87886574

    # https://www.zhihu.com/question/41373242/answer/91417985
    # https://www.zhihu.com/question/47275087/answer/106335325
    # https://www.zhihu.com/question/47275087/answer/106335325 买不起房是房价太高还是工资太低？
    # https://www.zhihu.com/question/36129534/answer/91921682  印度经济会在本世纪追上中国吗？
    # https://www.zhihu.com/question/22513722/answer/21967185  火车票涨价是否能解决春运问题？
    # https://www.zhihu.com/question/32210508/answer/57701501  蒋兆和《流民图》为何受到批判？
    # https://www.zhihu.com/question/27820755/answer/107267228 裸辞后怎样解释以获工作机会？
  '''
  for url in ss(urls).datalines():
    save_answer(url.split(' ')[0], folder='test')




# def exec_save_from_question():
#   urls = '''
#     # graphic design
#     # http://www.zhihu.com/question/19577036
#     # http://www.zhihu.com/question/21578745
#     # http://www.zhihu.com/question/22332149
#     # http://www.zhihu.com/question/21274267
#     # http://www.zhihu.com/question/22332149
#     # http://www.zhihu.com/question/29594460
#     # http://www.zhihu.com/question/27914845
#     # http://www.zhihu.com/question/28529486
#     # http://www.zhihu.com/question/20603867
#     http://www.zhihu.com/question/23914832
#   '''
#   for url in datalines(urls):
#     save_from_question(url)




def exec_save_from_topic():

  urls_str = '''
    # https://www.zhihu.com/topic/19554091 math
    # https://www.zhihu.com/topic/19556950 physics
    # https://www.zhihu.com/topic/19574449 a song of ice and fire
    # https://www.zhihu.com/topic/19556231 interactive design 1000
    # https://www.zhihu.com/topic/19556382 2d design 1000
    # https://www.zhihu.com/topic/19561709 ux design 1000
    # https://www.zhihu.com/topic/19551016 fonts 200
    # https://www.zhihu.com/topic/19553684 layout 100
    # https://www.zhihu.com/topic/19647471 style 100
    # https://www.zhihu.com/topic/19551077 history
    # https://www.zhihu.com/topic/19615699 immanuel_kant
    # https://www.zhihu.com/topic/19551864 classical music
    # https://www.zhihu.com/topic/19552330 programmer
    # https://www.zhihu.com/topic/19554298 programming
    # https://www.zhihu.com/topic/19615699 immanuel_kant

    # https://www.zhihu.com/topic/19563625 astronomy 天文
    # https://www.zhihu.com/topic/19620787 universe 天文
    # https://www.zhihu.com/topic/19569034 philosophy_of_science 科学哲学
    # https://www.zhihu.com/topic/19558740 statistics 统计学 answer 更多
    # https://www.zhihu.com/topic/19576422 statistics 统计
    # https://www.zhihu.com/topic/19552981 economics 经济
    # https://www.zhihu.com/topic/19553550 paradox 悖论
    # https://www.zhihu.com/topic/19559450 machine_learning 机器学习
    # https://www.zhihu.com/topic/19551275 artificial_intelligence 人工智能
    # https://www.zhihu.com/topic/19553534 data_mining 数据挖掘
    # https://www.zhihu.com/topic/19815465 quantitative_trading 量化交易
    # https://www.zhihu.com/topic/19571159 freelancer 自由职业
    # https://www.zhihu.com/topic/19555355 房地产
    # https://www.zhihu.com/topic/19555407 桌面游戏
  '''

  url = 'https://www.zhihu.com/topic/19555407'
  smart_save(url, folder=None, limit=3000, min_voteup=300, overwrite=False)
# exec_save_from_topic()

def exec_massive_download():

  # save_author('http://www.zhihu.com/people/nordenbox')
  urls = '''
    # http://www.zhihu.com/people/leng-zhe
    # http://www.zhihu.com/people/ji-xuan-yi-9
    # http://www.zhihu.com/people/Ivony
    # http://www.zhihu.com/people/BlackCloak

    # http://www.zhihu.com/people/hecaitou
    # http://www.zhihu.com/people/ma-bo-yong

    # http://www.zhihu.com/people/hutianyi
    # http://www.zhihu.com/people/lawrencelry
    # http://www.zhihu.com/people/Metaphox

    # http://www.zhihu.com/people/calon
    # http://www.zhihu.com/people/yolfilm
    # http://www.zhihu.com/people/superwyh
    # http://www.zhihu.com/people/cai-tong
    # http://www.zhihu.com/people/xiepanda




    # http://www.zhihu.com/people/cogito
    # http://www.zhihu.com/people/talich
    # http://www.zhihu.com/people/commando
    # http://www.zhihu.com/people/fu-er

    # http://www.zhihu.com/people/tassandar
    # http://www.zhihu.com/people/fei-niao-bing-he
    # http://www.zhihu.com/people/zhou-xiao-nong
    # http://www.zhihu.com/people/wang-lu-43-95
    # http://www.zhihu.com/people/yinshoufu
    # http://www.zhihu.com/people/tangsyau
    # http://www.zhihu.com/people/lianghai
    # http://www.zhihu.com/people/zhang-jia-wei
    # http://www.zhihu.com/people/bo-cai-28-7

    # all done
  '''

  urls = '''
    # http://www.zhihu.com/people/sa-miu-47-86
    # http://www.zhihu.com/people/xubowen
    http://www.zhihu.com/people/Huang-Lei-970106
  '''


  for url in ss(urls).datalines():
    save_from_author(url, folder='authors_explore', min_voteup=30)



def exec_download_zhuanlan():
  url = 'https://zhuanlan.zhihu.com/chicken-life'
  url = 'https://zhuanlan.zhihu.com/tonnie'

  column = client.from_url(url)
  for a in column.articles:
    print(a)
    save_article(a)



def exec_save_sinple_answer():
    url = 'https://www.zhihu.com/question/51936651/answer/130915660'
    save_answer(url)
























from watcher import Watcher



def test_run_watcher():
  w = Watcher(r'D:\Coding\TheNorthRemembers\test\旗舰评论——战略航空军元帅的旗舰')
  # w = Watcher(r'D:\Coding\TheNorthRemembers\test\知乎 - 温酒的回答')
  # w = Watcher(r'D:\Coding\TheNorthRemembers\test\经济')
  # w = Watcher(r'D:\Coding\TheNorthRemembers\test\HelloFlask')
  w.watch()


if __name__ == "__main__":
    test_run_watcher()