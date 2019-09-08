
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
from pprint import pprint
import tools

log = tools.create_logger(__file__)
log_error = tools.create_logger(__file__ + '.error')


from fetcher import UrlType
from fetcher import parse_type
from fetcher import purge_url
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
  max_cycle='30days',
  min_cycle='12hours',
  weight=0.5,
  limit=200,
)
PAGE_DEFAULT_OPTION = odict(
  enabled=True,
  max_cycle='180days',
  min_cycle='45days',
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
  collector.find_watcher_path(xxx)                      返回 Watcher
  TODO collector.rename_watcher(a, b)                   返回 Watcher

  collector.create_watcher(url)              通过 url 创建 Watcher
  collector.create_watcher(url1, url2 ...)

  collector.explore # 探查 url 的标题, 专栏文章数, 最近更新时间等
  collector.create_from_config(config)  # 通过 config dict 创建多个 watcher folder, 



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
                |-- watcher_path2
                |     |-- .task.yaml
                |-- watcher_path3
                | ..........
    '''
    if not os.path.exists(project_path):
      raise FileNotFoundError(f'project `{project_path}` does not exists')
    tools.run_command(f'cd "{project_path}" && git status') # check git repo
    self.project_path = project_path
    

  def __str__(self):
    return f'<Collector #{id(self)} path=`{self.project_path}`>'


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
      cmd = f'cd "{path}" && git init'
      tools.run_command(cmd)
      cmd = f'cd "{path}" && git config user.name TNR && git config user.email tnr@email.com'
      tools.run_command(cmd)
      cmd = f'cd "{path}" && git add . && git commit -m "init TNR project"'
      tools.run_command(cmd)
      log(f'create new project {path} and committed')
    return cls(project_path=path)

  def report(self):
    ''' 输出每个 Watcher folder 的摘要 '''
    log(f'report {self} \n---------------------')
    for directory in self.iter_watcher_paths():
      folder = os.path.basename(directory)
      folder_md5 = tools.md5(folder)
      all_pages = tools.all_files(directory, patterns='*.md', single_level=True)
      count = len(list(all_pages))
      log(f'    Watcher: "{folder}" (or "{folder_md5}") ({count} pages)')
    output = tools.run_command(f'cd "{self.project_path}" && git log --oneline -n 5')
    log('git log: ')
    for line in output.splitlines():
      log(f'    {line.strip()}')
    log(f'---------------------')


  def iter_watcher_paths(self):
    for directory in tools.all_subdirs(self.project_path):
      task_yaml = os.path.join(directory, '.task.yaml')
      if os.path.exists(task_yaml):
        yield directory


  def create_watcher(self, urls, tips=None, folder=None, parent_folder='.', lister_option=None, page_option=None):
    ''' 添加一个 Watcher, 根据 urls 创建 folder, 
        urls: 一个或多个网址, 多个需属于同种类型, 目前未检测 
        tips: 与 urls 配套的描述字符串
        folder: 指定 Watcher 文件夹名, 不指定就自动生成
    '''
    if isinstance(urls, str): urls = [urls, ]
    if isinstance(tips, str): tips = [tips, ]
    urls = [purge_url(u) for u in urls]
    if tips is None: tips = [Fetcher.generate_tip(u) for u in urls]
    if len(urls) != len(tips):
      raise ValueError(f'count of {urls} should equal to count {tips}')


    if folder is None:
      folder = Fetcher.generate_folder_name(urls)
      folder = tools.remove_invalid_char(folder)  # 只有自动生成 folder 需要处理 invalid_char
    watcher_path = os.path.join(self.project_path, parent_folder, folder)
    if os.path.exists(watcher_path):
      raise FileExistsError(f'creating watcher, already exists: `{watcher_path}`')

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

    os.makedirs(watcher_path)
    tools.yaml_save(d, watcher_path + '/' + '.task.yaml')
    log(f'Watcher path {watcher_path} created')
    folder_name = os.path.basename(watcher_path)
    self.remember(f'create Watcher folder {folder_name}')


  def create_multiple_watchers(self, config):
    ''' 依据 config 创建多个 watcher folder
    config 样例 (format as yaml): 
    
        global_default_option: 
          lister: 
            max_cycle: 30days
            min_cycle: 12hours
            limit: 200
          page: 
            weight: 0.5

        watcher_config:
          "folder/subfolder":
            default_option:
              lister:
                min_cycle: 18hours
                limit: 300
              page:
                min_cycle: 45days
                weight: 0.8
            lister_task:
                - 'https://zhuanlan.zhihu.com/xxxx #注释'
                - 'https://zhuanlan.zhihu.com/yyyy #注释'
                - url: https://zhuanlan.zhihu.com/zzzz
                  tip: "知乎专栏 - zzzz"
                  zhihu_min_voteup: 100
          "folder/subfolder2":
              lister_task:
                - 'https://url   #注释'
                - 'https://url   #注释'
                - 'https://url   #注释'

    对 config 任务的说明:
      都要位于 watcher_config 之下的 "folder/subfolder" 中
      该 "folder/subfolder" 将自动创建, 
      "folder/subfolder" 内部的配置与 Watcher 的 '.task.yaml' 一致, 
      特殊的, 如果 lister_task 列表中的条目是字符串 (正常应该是 {'url': xxx, 'tip': yyy})
      视为 {'url': 从该字符串中提取 url 部分}
    对 config 参数配置的说明:
      参数优先级从低到高依次是:
      1 "global_default_option:" 中的 lister: page:
      2 "watcher_config:" 中, 对每个 folder 独立配置的 "default_option:"
      3 每个 lister task 独立配置的选项
      更具体的选项配置将覆盖全局的选项配置
    '''

    log(f'create_multiple_watchers... ')
    # pprint(config)
    global_default_option = config.get('global_default_option', {'lister': {}, 'page': {}})
    global_default_lister_option = global_default_option.get('lister', {})
    global_default_page_option = global_default_option.get('page', {})

    for path, task_config in config.get('watcher_config', []).items():
      # pprint(path)
      # pprint(task_config)
      folder = os.path.basename(path)
      parent_folder = os.path.dirname(path)
      folder_default_option = task_config.get('default_option', {})
      lister_option = tools.dict_merge(global_default_lister_option, folder_default_option.get('lister', {}))
      page_option = tools.dict_merge(global_default_page_option, folder_default_option.get('page', {}))
      urls = [url.split(' ')[0] for url in task_config.get('lister_task', [])]

      # print('urls', urls, 'folder', folder, 'parent_folder', repr(parent_folder), )
      # print('lister_option:' ), pprint(lister_option, )
      # print('page_option:'), pprint(page_option, )

      self.create_watcher(urls, tips=None, 
                          folder=folder, parent_folder=parent_folder, 
                          lister_option=lister_option, page_option=page_option)
    log(f'create_multiple_watchers... done')



  def find_watcher_path(self, folder_name, strict=True):
    ''' strict=False 时, 查找 folder_name 近似, 或者 md5 吻合的 watcher_path'''
    if strict:
      for directory in self.iter_watcher_paths():
        if folder_name == os.path.basename(directory):
          return directory
      return None
    else:  # strict False 时
      clean = lambda text: tools.remove_invalid_char(text).replace(' ', '')
      for directory in self.iter_watcher_paths():
        if clean(folder_name) == clean(os.path.basename(directory)):
          return directory
        if folder_name == tools.md5(os.path.basename(directory)):
          return directory
      return None

  @classmethod
  def explore(cls, urls):
    '''分析多个页面的摘要特征'''
    for url in urls:
      url = purge_url(url.split(' ')[0])
      desc = Fetcher.create({'url': url}).detect()
      log(desc)


  def watching(self, folder_name):
    watcher_path = self.find_watcher_path(folder_name, strict=True)
    watcher = Watcher(watcher_path)
    log(f'\n  ↓ start_watching_once for\n  {watcher}')
    for commit_log in watcher.watch():
      self.remember(commit_log)
    log(f'  ↑ start_watching_once done\n')

  def start_watching_loop(self, folder_name):
    pass


  def remember(self, commit_log, verbose=False):
    ''' 将 watcher 抓取到的内容存储到 git 仓库
        git 仓库通常位于 watcher folder 的上一层
    '''
    # git_path = os.path.dirname(watcher_path) # watcher folder 上一层
    if isinstance(commit_log, dict):
      commit_log = commit_log.get('commit_log', 'missing commit log')
    cmd = f'cd "{self.project_path}" && git add . && git commit -m "{commit_log}"'
    # log(cmd)
    tools.run_command(cmd, verbose=verbose)
    log(f'Watcher.remember committed: "{commit_log}"\n')



  def generate_feed(self, path, limit, site='http://xxx.com/'):
    ''' 生成 RSS, 内容为全部 page_task, 
        按照添加任务的顺序倒序排列 (按照更新时间排列? TODO)
        TODO path 如果是父级文件夹, 视为合并子文件夹里所有 page 生成 rss feed
        RSS Feed 文件名为 path, alias? TODO

        limit=-1 时迭代所有Page
        '''
    watcher_path = self.find_watcher_path(path, strict=False)
    if not watcher_path: 
      log(f'WARN: generate_feed path {path} not found')
      return None
    feed_name = os.path.basename(watcher_path)  # TODO 如果是父级文件夹, 合并
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

    fg = FeedGenerator()
    fg.id(site + feed_name)
    fg.title(feed_name)
    # <link>https://xxx.com/thread.php?fid=1</link>
    fg.link(href=site + feed_name, rel='alternate')
    # fg.logo('http://ex.com/logo.jpg')
    fg.subtitle('generated by The North Remembers')
    # <atom:link href="http://rsshub.app/xxx" rel="self" type="application/rss+xml"/>
    fg.link(href=site + feed_name + '/feed', rel='self')
    fg.language('zh-cn')
    for page in sorted(pages, key=lambda page: page.edit_date):  # 这里不需要 reverse=True
      # log(f'prepare feed entry {page}')
      fe = fg.add_entry()
      fe.id(page.metadata['url'])
      fe.title(tools.clean_xml(page.metadata['title']))
      fe.link(href=page.metadata['url'])
      fe.published(page.edit_date+'+08:00')  
      # fe.updated(page.edit_date+'+08:00')  # 在这种 RSS 似乎不起作用
      fe.description(tools.clean_xml(page.to_html(cut=0)))
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
from flask import make_response
from flask import abort
from flask import after_this_request
app = Flask(__name__)


import gzip, functools
from io import BytesIO

def gzipped(f):
  @functools.wraps(f)
  def view_func(*args, **kwargs):
    @after_this_request
    def zipper(response):
      accept_encoding = request.headers.get('Accept-Encoding', '')
      if 'gzip' not in accept_encoding.lower(): return response

      response.direct_passthrough = False
      if (response.status_code < 200 or
          response.status_code >= 300 or
          'Content-Encoding' in response.headers):
          return response
      gzip_buffer = BytesIO()
      gzip_file = gzip.GzipFile(mode='wb', fileobj=gzip_buffer)
      gzip_file.write(response.data)
      gzip_file.close()
      response.data = gzip_buffer.getvalue()
      response.headers['Content-Encoding'] = 'gzip'
      response.headers['Vary'] = 'Accept-Encoding'
      response.headers['Content-Length'] = len(response.data)
      return response
    return f(*args, **kwargs)
  return view_func





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
@gzipped
def get_feed(folder_name):
  log(f'getting feed {folder_name} for {request.url}')
  limit = int(request.args.get('limit', 120))
  feed_path = col.generate_feed(folder_name, limit=limit, site=request.url_root)
  log(f'generate_feed done {feed_path}')
  if feed_path:
    return Response(open(feed_path, encoding='utf-8').read(), mimetype='application/xml')
  else:
    abort(404)
    # raise RuntimeError(f'cannot generate_feed {folder_name}')






if __name__ == '__main__':
  if tools.is_windows():
    project_path = 'D:/DataStore/Test Collector2' 
    col = Collector(project_path=project_path)
    app.run(debug=True, host='0.0.0.0', port=80)
  elif tools.is_linux():
    project_path = '/project'
    col = Collector(project_path=project_path)
    app.run(debug=True, host='0.0.0.0', port=443,
            ssl_context=('cert.pem', 'key.pem'))
  else:
    raise 