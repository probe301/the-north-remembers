
import time
import os
import shutil
import re
import random
from datetime import datetime

from watcher import Watcher
from fetcher import Fetcher
from collections import OrderedDict as odict
from collections import Counter
import tools

log = tools.create_logger(__file__)
log_error = tools.create_logger(__file__ + '.error')


from tools import UrlType
from tools import parse_type
from tools import create_logger
from tools import time_to_str
from tools import duration_from_humanize
from tools import time_now
from tools import time_now_str
from tools import time_from_str
from tools import time_to_humanize
from tools import remove_invalid_char

from page import Page
# from werkzeug.contrib.atom import AtomFeed
from feedgen.feed import FeedGenerator






class Collector:
  '''
  与用户对接提交抓取任务, 接受用户输入的条件和附加参数
  提交一个页面, 直接安排抓取, 不记录
  提交页面集合 (用户的所有回答, 专栏, 收藏夹),
    首先解析任务列表, 取出所涉及页面, 都安排一次抓取
    如果要求记录任务自身, 则额外记录 Collector 配置, 供之后定期rescan增加页面

  Collector.create(project_path=xxx) 创建项目, 将该目录设为 git 仓库
  collector = Collector(project_path=xxx)

  Collector.watchers 返回项目中所有的 Watcher 目录
  Collector.report 返回所有的 Watcher 状态, 带有多少 task 等等
  Collector.find_watcher(folder=xxx) 返回 Watcher

  Collector

  collector.add(url1)
  collector.add(weixin_page_url)
  collector.add(zhihu_column_url)
  collector.add(zhihu_anwser_id=xxx)
  collector.add(zhihu_author_id=xxx)
  collector.add(column_id=xxx)



  '''


  def __init__(self, project_path):
    ''' 创建 Collector 
        需要固定的项目路径, 
        同时检测项目路径是否为 git 仓库 TODO

        结构是 project_path (git repo)
                |
                |-- watcher_path1
                |     |-- .task.yaml
                |     |-- lister_task (xN)
                |     |-- page_task (xN)
                |-- watcher_path2
                |     |-- .task.yaml
                |     |-- lister_task (xN)
                |     |-- page_task (xN)
                |-- watcher_path3
                | ..........
    '''
    self.project_path = project_path
    # TODO check git repo


  def __str__(self):
    return f'<Collector #{id(self)} path={self.project_path}>'


  def add(self, url, tip=None, lister_option=None, page_option=None):
    ''' 添加一个 Watcher, 根据 url 决定何种类型 '''

    lister_default_option = odict(
      enabled=True,
      max_cycle='15day',
      min_cycle='1hour',
      weight=0.5,
      limit=200,
    )
    page_default_option = odict(
      enabled=True,
      max_cycle='1day',
      min_cycle='1hour',
      weight=0.5,
    )

    if lister_option:
      lister_default_option.update(lister_option)
    if page_option:
      page_default_option.update(page_option)

    url = tools.purge_url(url)
    if tip is None:
      tip = Fetcher.generate_tip(url)
    # page_type = tools.parse_type(url)
    folder = self.project_path + '/' + tools.remove_invalid_char(tip)

    d = odict(
      default_option=odict(
        lister=lister_default_option,
        page=page_default_option,
      ), 
      lister_task=[odict(url=url, tip=tip), ]
    )
    # 这样会让 lister_task[] 的缩进不正确
    # 应该是 lister_task:
    #          - url: xxx
    #            tip: xxx
    # 实际是 lister_task:
    #        - url: xxx
    #          tip: xxx 但是不影响识别


    if os.path.exists(folder):
      raise ValueError(f'folder already exists: {folder}')
    else:
      os.mkdir(folder)
      tools.yaml_save(d, folder + '/' + '.task.yaml')
      log(f'Watcher folder {folder} created')



  def add_multiple(self, urls, tips=None, folder=None, lister_option=None, page_option=None):
    ''' 添加一个 Watcher, 根据 urls 创建 folder, 
        urls 需要属于同种类型, 目前未检测 '''

    lister_default_option = odict(
      enabled=True,
      max_cycle='15day',
      min_cycle='1hour',
      weight=0.5,
      limit=200,
    )
    page_default_option = odict(
      enabled=True,
      max_cycle='1day',
      min_cycle='1hour',
      weight=0.5,
    )

    if lister_option:
      lister_default_option.update(lister_option)
    if page_option:
      page_default_option.update(page_option)
    
    urls = [tools.purge_url(u) for u in urls]

    if tips is None:
      tips = [Fetcher.generate_tip(u) for u in urls]
    else:
      if len(urls) != len(tips):
        raise ValueError(f'count of {urls} should equal to count {tips}')

    if folder is None:
      folder = Fetcher.generate_folder(urls)
    folder = self.project_path + '/' + tools.remove_invalid_char(folder)

    d = odict(
      default_option=odict(
        lister=lister_default_option,
        page=page_default_option,
      ), 
      lister_task=[odict(url=url, tip=tip) for url, tip in zip(urls, tips)]
    )

    if os.path.exists(folder):
      raise ValueError(f'folder already exists: {folder}')
    else:
      os.mkdir(folder)
      tools.yaml_save(d, folder + '/' + '.task.yaml')
      log(f'Watcher folder {folder} created')







  def remember(self, commit_log, watcher_path):
    ''' 将 watcher 抓取到的内容存储到 git 仓库
        git 仓库通常位于 watcher folder 的上一层
    '''
    git_path = os.path.dirname(watcher_path) # watcher folder 上一层
    cmd = 'cd {} && git add . && git commit -m "{}"'.format(git_path, commit_log)
    # log(cmd)
    os.system(cmd)
    log('Watcher.remember added + committed {} {}'.format(watcher_path, commit_log))



  def generate_feed(watcher_path, limit=10, ):
    ''' 生成 RSS, 内容为全部 page_task, 
        按照添加任务的顺序倒序排列 (按照更新时间排列? TODO)
        RSS Feed 文件名为 Watcher 文件夹名称

        limit=-1 时迭代所有Page
        '''
    feed_name = os.path.basename(watcher_path)
    pages = []

    for path in tools.all_files(watcher_path, patterns='*.md'):
      if limit == 0: break
      limit -= 1
      try:
        page = Page.load(path)
        pages.append(page)
      except:
        log(f'error Page.load({path})')
        raise

    # for page in pages:
    #   log(page)

    fg = FeedGenerator()
    fg.id('xxxurl/' + feed_name)
    fg.title(feed_name)
    fg.link(href='xxxurl/' + feed_name, rel='alternate')
    # fg.logo('http://ex.com/logo.jpg')
    fg.subtitle('generated by The North Remembers')
    fg.link(href='xxxurl/' + feed_name + 'atom', rel='self')
    fg.language('zh-cn')

    for page in sorted(pages, key=lambda page: page.watch_time):
      fe = fg.add_entry()
      fe.id(page.metadata['url'])
      fe.title(page.metadata['title'])
      fe.link(href=page.metadata['url'])
      fe.description('\n\n' + page.to_html(cut=0) + '\n')
    feed_path = os.path.join(watcher_path, 'feed.xml')
    fg.rss_file(feed_path, pretty=True)
    # log(f'generate_feed `{feed_path}` done')
    return feed_path






















































'''

route:



常用的单页面 
example: http://host/question/<123>/answer/<123>
         (替换 https://www.zhihu.com => http://host)

返回格式化后的页面, 初步只有 txt 即可

RSS Feed
  http://host/<folder>/feed/
返回 project 下属这个 folder 里的 feed

folder 是 rss feed 的基本单位, 
如果需要过滤 folder 内的条目, 或者聚合多个 folder, 先用别的 feed 工具



'''


from flask import request
from flask import jsonify
from flask import Flask
from flask import render_template
from flask import Response
app = Flask(__name__)








@app.route('/')
@app.route('/index')
def index():
  user = {'nickname': 'test'}  # fake user
  return render_template("index.html", title='Home', user=user)


@app.route('/hello')
def hello():
  return 'Hello World'



@app.route('/question/<int:question_id>/answer/<int:answer_id>')
def fetch_zhihu_answer(question_id, answer_id):
  log(f'get /question/{question_id}/answer/{answer_id}')
  text = col.fetch_zhihu_answer(question_id, answer_id)
  return text # return jsonify(ret)


# @app.route('/topic/<int:topic_id>')
# def list_zhihu_answers_by_topic(topic_id):
#   from zhihu_answer import yield_topic_best_answers
#   # mockup
#   def yield_topic_best_answers(topic_id, limit=100, min_voteup=300):
#     import json
#     data = json.loads(open('mockup_topic_answers.json', encoding='utf-8').read())
#     return (elem for elem in data)

#   ret = list(yield_topic_best_answers(topic_id))
#   return render_template("topics.html",
#                          title='Topics', topic_answers=ret)

#   # real
#   ret = []
#   for answer in yield_topic_best_answers(topic_id, limit=100, min_voteup=300):
#     url = zhihu_answer_url(answer)
#     ret.append({'url': url,
#                 'title': answer.question.title,
#                 'vote': answer.voteup_count,
#                 'topic': [t.name for t in answer.question.topics],
#                })
#   # return form(ret)
#   # return jsonify(ret)

#   return render_template("topics.html",
#                          title='Topics', topic_answers=ret)







  # def yield_topic_best_answers(topic_id, limit=100, min_voteup=300):
  # def save_answer(answer, folder='test', overwrite=True):
  # def save_article(article, folder='test', overwrite=True):
  # def fetch_images_for_markdown(markdown_file):


@app.route('/author/<author_id>')
def list_zhihu_answers_by_author(author_id):
  from zhihu_answer import yield_author_answers
  ret = []
  limit = int(request.args.get('limit', 10))
  min_voteup = int(request.args.get('min_voteup', 300))
  for answer in yield_author_answers(author_id, limit=limit, min_voteup=min_voteup):
    url = zhihu_answer_url(answer)
    ret.append({'url': url,
                'title': answer.question.title,
                'voteup_count': answer.voteup_count,
                'created_time': convert_time(answer.created_time),
                'updated_time': convert_time(answer.updated_time),
                'author_name': answer.author.name,
               })
  return jsonify(ret)



@app.route('/topic/<int:topic_id>')
def list_zhihu_answers_by_topic(topic_id):
  # mockup
  def yield_topic_best_answers(topic_id, limit=100, min_voteup=300):
    import json
    data = json.loads(open('mockup_topic_answers.json', encoding='utf-8').read())
    return (elem for elem in data)

  ret = list(yield_topic_best_answers(topic_id))
  return render_template("topics.html",
                         title='Topics', topic_answers=ret)

  # real
  ret = []
  for answer in yield_topic_best_answers(topic_id, limit=100, min_voteup=300):
    url = zhihu_answer_url(answer)
    ret.append({'url': url,
                'title': answer.question.title,
                'vote': answer.voteup_count,
                'topic': [t.name for t in answer.question.topics],
               })
  # return form(ret)
  # return jsonify(ret)

  return render_template("topics.html",
                         title='Topics', topic_answers=ret)




from recorder import generate_feed
@app.route('/<folder_name>/feed')
def get_feed(folder_name):
  log(f'getting feed {folder_name}')
  project_path = r'./project'
  watcher_path = os.path.join(project_path, folder_name)
  feed_path = generate_feed(watcher_path, limit=100)
  if feed_path:
    return tools.load_txt(feed_path)
  else:
    raise RuntimeError(f'cannot generate_feed {folder_name}')





# if __name__ == '__main__':
#   col = Collector(project_path='/project')

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0', port=80)
