
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



# 创建 Watcher 目录时的默认 lister task 和 page task 设置
LISTER_DEFAULT_OPTION = odict(
  enabled=True,
  max_cycle='15days',
  min_cycle='12hours',
  weight=0.5,
  limit=200,
)
PAGE_DEFAULT_OPTION = odict(
  enabled=True,
  max_cycle='90day',
  min_cycle='18hours',
  weight=0.5,
)

class Collector:
  '''
  与用户对接提交抓取任务, 接受用户输入的条件和附加参数
  提交一个页面, 直接安排抓取, 不记录
  提交页面集合 (用户的所有回答, 专栏, 收藏夹),
    首先解析任务列表, 取出所涉及页面, 都安排一次抓取
    如果要求记录任务自身, 则额外记录 Collector 配置, 供之后定期rescan增加页面

  Collector.create_project(path=xxx) 创建项目, 将该目录设为 git 仓库
  collector = Collector(project_path=xxx) 打开项目
  collector.report 返回所有的 Watcher 状态, 带有多少 task 等等

  collector.list_watchers 
  collector.find_watcher(xxx)                      返回 Watcher
  TODO collector.rename_watcher(a, b)                   返回 Watcher

  collector.create_watcher(url)              通过 url 创建 Watcher
  collector.create_watcher(url1, url2 ...)

  # 向已有的 Watcher 更新条目
  TODO collector.append_to_watcher(use watcher.add_task(task_dict))




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


  @classmethod
  def create_project(cls, path):
    ''' 创建项目或打开已存在项目
        新建时附带生成 git 仓库'''
    if os.path.exists(path):
      log(f'WARN: create_project `{path}` exists')
    else:
      os.mkdir(path)
      ignore = "# project\n.ipynb_checkpoints\n__pycache__/\n*.py[cod]\ntodo.txt\n**/feed.xml"
      tools.save_txt(os.path.join(path, '.gitignore'), ignore)
      cmd = f'cd "{path}" && git init && git add . && git commit -m "init TNR project"'
      # log(cmd)
      tools.run_command(cmd)
      log(f'create new project {path} and committed')
    return cls(project_path=path)

  def report(self):
    ''' 输出每个 Watcher folder 的摘要 '''
    log(f'report {self} \n---------------------')
    for directory in tools.all_subdirs(self.project_path):
      # if directory == '.git':
      task_yaml = os.path.join(directory, '.task.yaml')
      if os.path.exists(task_yaml):
        folder = os.path.basename(directory)
        all_pages = tools.all_files(directory, patterns='*.md', single_level=True)
        count = len(list(all_pages))
        log(f'    Watcher: `{folder}` ({count} pages)')
    output = tools.run_command(f'cd "{self.project_path}" && git log --oneline -n 5')
    log('git log: ')
    for line in output.splitlines():
      log(f'    {line.strip()}')
    log(f'---------------------')






  def create_watcher(self, urls, tips=None, folder=None, lister_option=None, page_option=None):
    ''' 添加一个 Watcher, 根据 urls 创建 folder, 
        urls: 一个或多个网址, 多个需属于同种类型, 目前未检测 
        tips: 与 urls 配套的描述字符串
        folder: 指定 Watcher 文件夹名, 不指定就自动生成
    '''
    if isinstance(urls, str): urls = [urls, ]
    if isinstance(tips, str): tips = [tips, ]
    urls = [tools.purge_url(u) for u in urls]
    if tips is None: tips = [Fetcher.generate_tip(u) for u in urls]
    if len(urls) != len(tips):
      raise ValueError(f'count of {urls} should equal to count {tips}')

    if folder is None:
      folder = Fetcher.generate_folder_name(urls)
    folder = os.path.join(self.project_path, tools.remove_invalid_char(folder))
    if os.path.exists(folder):
      raise ValueError(f'folder already exists: {folder}')

    d = odict(
        default_option=odict(
            lister=tools.dict_merge(LISTER_DEFAULT_OPTION, lister_option),
            page=tools.dict_merge(PAGE_DEFAULT_OPTION, page_option),
        ), 
        lister_task=[odict(url=url, tip=tip) for url, tip in zip(urls, tips)]
    )
    # 这样会让 lister_task[] 的缩进不正确
    # 应该是 lister_task:
    #          - url: xxx
    #            tip: xxx
    # 实际是 lister_task:
    #        - url: xxx
    #          tip: xxx 但是不影响识别

    os.mkdir(folder)
    tools.yaml_save(d, folder + '/' + '.task.yaml')
    log(f'Watcher folder {folder} created')
    folder_name = os.path.basename(folder)
    self.remember(f'create Watcher folder `{folder_name}`')






  def remember(self, commit_log, verbose=False):
    ''' 将 watcher 抓取到的内容存储到 git 仓库
        git 仓库通常位于 watcher folder 的上一层
    '''
    # git_path = os.path.dirname(watcher_path) # watcher folder 上一层
    cmd = f'cd "{self.project_path}" && git add . && git commit -m "{commit_log}"'
    # log(cmd)
    tools.run_command(cmd, verbose=verbose)
    log(f'Watcher.remember added + committed {commit_log}')



  def generate_feed(self, watcher_path, limit=10, ):
    ''' 生成 RSS, 内容为全部 page_task, 
        按照添加任务的顺序倒序排列 (按照更新时间排列? TODO)
        watcher_path 如果是父级文件夹, 视为合并子文件夹里所有 page 生成 rss feed
        RSS Feed 文件名为 watcher_path, alias? TODO

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






if __name__ == '__main__':
  project_path = 'D:/DataStore/test' if tools.is_windows() else '/project'
  col = Collector(project_path=project_path)
  app.run(debug=True, host='0.0.0.0', port=80)
