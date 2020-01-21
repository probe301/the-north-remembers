
import time
import os
import shutil
import re
import random
from datetime import datetime

from fetcher import Fetcher
from collections import OrderedDict as odict
from collections import Counter
from pprint import pprint
import tools

log = tools.create_logger(__file__)
log_error = tools.create_logger(__file__ + '.error')

from task import Task
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
from fetcher import Fetcher
from fetcher import FetcherOption
from page import Page
# from werkzeug.contrib.atom import AtomFeed
from feedgen.feed import FeedGenerator

import pydantic



class TaskEnvOption(pydantic.BaseModel):
  '''收集 .config.yaml 里和 task 环境有关的配置'''
  lister_max_cycle = '30days'
  lister_min_cycle = '12hours'
  weight = 0.5
  page_max_cycle = '180days'
  page_min_cycle = '45days'


class WatcherOption(pydantic.BaseModel):
  '''收集 .config.yaml 里和 watcher 自身有关的配置'''
  git_commit_path = ''
  git_commit_batch = 3
  rss_title : str = None
  rss_link : str = 'https://xxxx'
  rss_output_path = 'feed.xml'
  epub_output_path : str = None



class Watcher:
  '''
  Watcher 为目录下具有 .config.yaml 的目录, 负责调度和执行抓取

  .config.yaml 只读, 指定全局设置, 和 lister
  .tasks.yaml 系统自动覆写, 记录已经抓取过的页面

  当创建 Watcher() 时:
    加载该 folder 下的 .tasks.yaml, 里面是已记录的 lister_tasks 和 page_tasks
    加载该 folder 下的 .config.yaml, 里面可能有新建的 lister_tasks
    输出一个报告

  当 watcher.watch() 时:
    首先运行 lister_task 里的任务, 检测这些列表页是否新增了页面
      如果检测到新增页面, 创建新的 page_task
      如果检测到的是本地 page_task 中已存在的页面, 按照预定的抓取时间处理
    然后运行 page_task 里的任务, 挨个抓取

    每完成一个 batch (比如 10 个更新) 之后, 交给 git 提交记录
    并输出一个报告
  '''

  def __init__(self, path):
    '''
    1 加载该 folder 下的 .tasks.yaml, 里面是已记录的 lister_tasks 和 page_tasks
    2 加载该 folder 下的 .config.yaml, 里面可能有新建的 lister_tasks

    .tasks.yaml 中需要记录 url, tip, date x4, version
    而 lister_limit, page_max_cycle, lister_min_cycle ... 等记录在 .config.yaml 中
    '''
    self.watcher_path = path
    self.folder = os.path.basename(path)
    config = tools.yaml_load(path + '/.config.yaml')
    self.config = WatcherOption(**config)  # 过滤出和 watcher 自身有关的设置项
    self.task_env_option = TaskEnvOption(**config).dict()
    self.fetcher_option = FetcherOption(**config).dict()
    self.tasks = {}
    # load_local_tasks task_dict 预备以 url 作为 key
    # 1 从 task.json 中载入已有 task
    # 2 对于 page task, 加入该 watcher 的 env_option
    # 3 对于 lister task, 加入该 watcher 的 env_option, 以及 listers 里特定的属性
    if os.path.exists(path + '/.tasks.yaml'):
      local_tasks_json = tools.yaml_load(os.path.join(self.watcher_path, '.tasks.yaml')) or []
    else:
      local_tasks_json = []
    for item in local_tasks_json:
      task = Task.create(item, env_option=self.task_env_option, fetcher_option=self.fetcher_option)
      self.tasks[item['url']] = task
    self.lister_urls = config.get('urls', [])
    for item in self.lister_urls:
      if item['url'] not in self.tasks:  # 从 config.yaml 中的 urls 里新增 task
        task = Task.create(item, env_option=self.task_env_option, fetcher_option=self.fetcher_option)
        self.tasks[item['url']] = task

    # 更新 listers 中的 task, 用户可能修改了某些 lister 的 option
    for item in self.lister_urls:
      url = item['url']
      custom_option = item.get('option')  # lister 自定义设置
      if custom_option: 
        self.tasks[url].patch(custom_option)

    # TODO 更新 page_option 中的 task, 用户可能修改了单独某个 page 的 option




  @classmethod
  def write_demo_config(cls, path):
    config = '''
git_commit_path: ''       # 使用 git 提交记录, 可选上一层目录 '..', 当前目录 '.', 或默认 none
git_commit_batch: 3       # 每 3 个页面执行一个提交

# Task Option
lister_max_cycle: 30days  # 对 Watcher 目录里的所有 lister 起效, 会被具体设置覆盖
lister_min_cycle: 12hours
weight: 0.5
page_max_cycle: 180days   # 对 Watcher 目录里的所有 page 起效
page_min_cycle: 45days

save_attachments: false
limit: 300
min_voteup: 0
min_thanks: 0
text_include: None
text_exclude: None
# Export Option
rss_title: "zhuanlan-frontend"
rss_link: https://xxxx
rss_output_path: 'feed.xml'
epub_output_path: none
# Lister Task and Page Task
urls:
  - url: "https://wemp.app/posts/123"
    tip: "tip1"
    option: {limit: 2}
  - url: "https://wemp.app/posts/456"
    tip: "tip2"
    option: {limit: 3}

    '''
    tools.text_save(path, config)


  @classmethod
  def create(cls, path):
    '''创建新的 Wacther 项目'''
    if os.path.exists(path):
      raise FileExistsError(f'create_watcher `{path}` exists')
    os.makedirs(path, exist_ok=False)
    Watcher.write_demo_config(path + '/.config.yaml')
    return cls(path=path)

  @classmethod
  def open(cls, path):
    if not os.path.exists(path):
      raise FileNotFoundError(f'open_watcher `{path}` not exists')
    if not os.path.exists(path + '/.config.yaml'):
      raise FileNotFoundError(f'open_watcher `{path}/.config.yaml` not exists')
    return cls(path=path)

  @classmethod
  def is_watcher(cls, path):
    return os.path.exists(path) and os.path.exists(path + '/.config.yaml') and os.path.exists(path + '/.tasks.yaml')

  def __str__(self):
    s = '''<Watcher #{}> from `{}`, {} tasks {} pages'''
    return s.format(id(self), self.watcher_path, self.tasks_count, self.pages_count)

  @property
  def git_project_path(self):
    path = self.config.git_commit_path
    if path: return os.path.join(self.watcher_path, path)
    else: return None

  @property
  def pages(self):
    all_pages = tools.all_files(self.watcher_path, patterns='*.md', single_level=True)
    return list(all_pages)

  @property
  def pages_count(self):
    return len(self.pages)

  @property
  def tasks_count(self): return len(self.tasks.keys())

  def add_task(self, task_desc):
    ''' 添加一个 Task, 以 url 判断是否为已存在的 Task
        返回 task 属于四种情况的数量
          new        当前未知的新任务,
          seen       当前任务列表中已存在的任务 (url 已知)
          prepare    任务已到抓取时间, 等待抓取
          wait       任务不到抓取时间
    '''
    url = task_desc['url']
    seen_task = self.tasks.get(url)
    if seen_task:
      if seen_task.next_watch_time <= time_now(): return "seen tasks, prepare fetch"
      else: return "seen tasks, not on fetch time"
    else:
      new_task = Task.create(task_desc, self.task_env_option)
      self.tasks[url] = new_task
      return "new tasks"

  def add_tasks(self, tasks_desc):
    ''' 添加任务列表, 并输出报告
        在 watcher 加载 config yaml 时调用, 以及 lister 检测到 new page 时调用
        输出报告 task 属于四种情况的数量
          new        当前未知的新任务,
          seen       当前任务列表中已存在的任务 (url 已知)
          prepare    任务已到抓取时间, 等待抓取
          wait       任务不到抓取时间
    '''
    results = []
    for item in tasks_desc:
      add_task_result = self.add_task(item)
      results.append(add_task_result)
    log(f'watcher add {len(tasks_desc)} tasks: {dict(Counter(results))}')
    return Counter(results)


  def save_tasks_yaml(self):
    ''' 存盘 .tasks.yaml
        按照添加顺序存放
    '''
    tasks = sorted(self.tasks.values(), key=lambda t: t.task_add_time)
    temp = ''
    for task in tasks:
      temp += task.to_yaml_text()
      temp += '\n'
    tools.text_save(path=self.watcher_path + '/.tasks.yaml', data=temp)


  def get_lister_tasks(self):
    lister_tasks_queue = []
    for task in self.tasks.values():
      if task.is_lister_type:
        lister_tasks_queue.append(task)
    return lister_tasks_queue


  def get_lister_tasks_should_fetch(self):
    lister_tasks_queue = []
    for task in self.tasks.values():
      if task.should_fetch and task.is_lister_type:
        lister_tasks_queue.append(task)
    lister_tasks_queue.sort(key=lambda x: -x.priority)
    return lister_tasks_queue

  def get_page_tasks_should_fetch(self):
    page_tasks_queue = []
    for task in self.tasks.values():
      if task.should_fetch and task.is_page_type:
        page_tasks_queue.append(task)
    page_tasks_queue.sort(key=lambda x: -x.priority)
    return page_tasks_queue



  def run(self):
    ''' 爬取页面,
        首先列出所有的NewPost任务, 都抓取一遍
        然后列出普通页面任务, 都抓取一遍
    '''
    lister_tasks_queue = self.get_lister_tasks_should_fetch()
    log(f'watching listers... should fetch {len(lister_tasks_queue)} lister tasks\n')
    for i, task in enumerate(lister_tasks_queue, 1):
      # log('Watcher.watch lister task.run: {}'.format(task))
      new_tasks_json = task.run()
      counter = self.add_tasks(new_tasks_json)
      is_modified = counter["new tasks"] > 0   # is_modified = add_tasks 时出现了新的 task
      task.schedule(is_modified=is_modified) 
      log(f'detect lister done ({i}/{len(lister_tasks_queue)}): \n{task}\n\n')
      self.save_tasks_yaml()
      yield {'commit_log': f'check lister {i}/{len(lister_tasks_queue)}, {task.brief_tip}'}
      # self.remember(commit_log='checked lister {}'.format(i), watcher_path=self.watcher_path)
      tools.time_random_sleep(5, 10)

    page_tasks_queue = self.get_page_tasks_should_fetch()
    log(f'watching pages... should fetch {len(page_tasks_queue)} page tasks\n')
    for tasks_batch in tools.windows(enumerate(page_tasks_queue, 1), self.config.git_commit_batch, yield_tail=True):
      # log('Watcher.watch page task: {}'.format(task))
      for i, task in tasks_batch:
        page_json = task.run()
        page_json['metadata']['folder'] = self.watcher_path
        page_json['metadata']['version'] = task.version + 1
        page = Page.create(page_json)
        is_modified = page.is_changed(page.last_page_version)
        page.write()
        task.schedule(is_modified=is_modified)  # is_modified = 跟上次存储的页面有区别
        next_watch_time = tools.time_to_humanize(task.next_watch_time)
        log(f'  -> {page.filename} is_modified={is_modified}, next_watch_time={next_watch_time}')
        log(f'page task done ({i}/{len(page_tasks_queue)}): \n{task}\n\n')

      self.save_tasks_yaml()
      commit_tasks_log = ','.join(task.brief_tip for i, task in tasks_batch)
      yield {'commit_log': f'save {len(tasks_batch)} pages, {commit_tasks_log}'}
      # self.remember(commit_log='save pages {}'.format(i))

      tools.time_random_sleep(3, 6)


  def watch_once(self):
    log(f'\n  ↓ start watch_once for\n  {self}')
    for commit_log in self.run():
      self.remember(commit_log)
    log(f'\n  ↑ start watch_once done\n')


  def remember(self, commit_log, verbose=False):
    ''' 如果使用 git, 将 watcher 抓取到的内容存储到 project git 仓库 '''
    if isinstance(commit_log, dict):
      commit_log = commit_log.get('commit_log', 'missing commit log')
    if self.git_project_path:
      cmd = f'cd "{self.git_project_path}" && git add . && git commit -m "{commit_log}"'
      # log(cmd)
      tools.run_command(cmd, verbose=verbose, timeout=15)
      log(f'git committed: "{commit_log}"\n')
    else:
      log(commit_log)


  def report(self):
    ''' 输出 Watcher folder 的摘要 '''
    log(f'---------------------')
    folder = self.folder
    count = self.pages_count
    folder_md5 = tools.md5(self.folder, 10)
    log(f'  ├─── Watcher: "{folder}" ({folder_md5}) {count} pages)')
    log(f'  ├─── should fetch {len(self.get_lister_tasks_should_fetch())} lister tasks')
    log(f'  ├─── should fetch {len(self.get_page_tasks_should_fetch())} page tasks')
    if self.git_project_path:
      output = tools.run_command(f'cd "{self.git_project_path}" && git log --oneline -n 5')
      log('  ├─── git log: ')
      for line in output.splitlines():
        log(f'  ├─── {line.strip()}')
    log(f'---------------------')



# =========================================================
# =================== end of class Watcher ================
# =========================================================



