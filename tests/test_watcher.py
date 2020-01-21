
import os, sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import shutil
import tools
from watcher import Watcher
from pyshould import should
import arrow
from datetime import datetime
from time import sleep
import dictdiffer
import pytest
from task import Task

'''
#### Watcher
任务调度, 监视文件夹, 
.config.yaml 抓取页面
.tasks.yaml 记录历史

task_type: page, lister, 

通过扫描已有的待抓取任务, 在手动触发或者达到特定时间后, 分派抓取任务

'''

ROOTPATH = r'D:/DataStore'
PROJECTPATH = r'D:/DataStore/Test Watcher'
PROJECTPATHOPEN = r'D:/DataStore/Test Watcher Open'
PROJECTPATHNEW = r'D:/DataStore/Test Watcher New'
CONFIGDATA = r'''
# Watcher Option
git_commit_path: ''       # 使用 git 提交记录, 可选上一层目录 '..', 当前目录 '.', 或默认 none
git_commit_batch: 3       # 每 3 个页面执行一个提交
# Task Option
lister_max_cycle: 30days  # 对 Watcher 目录里的所有 lister 起效, 会被具体设置覆盖
lister_min_cycle: 12hours
weight: 0.5
page_max_cycle: 180days   # 对 Watcher 目录里的所有 page 起效
page_min_cycle: 45days
# Fetcher Option
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
  - url: https://zhuanlan.zhihu.com/frontEndInDepth
    tip: "专栏 TryFEInDepth"
    option: {limit: 4}
  - url: https://zhuanlan.zhihu.com/learn-vue-source-code
    tip: "专栏 Vue源码研究会"
    option:  # 专属这个 lister url 的 option, 覆盖全局设置
      min_voteup_count: 100
      limit: 3
      text_exclude: '有哪些,如何看待'  # 标题/话题中有这些关键词, 就不抓取limit: 10
'''

PROJECTPATHWITHGIT = PROJECTPATH + ' withgit'
CONFIGDATAWITHGIT = CONFIGDATA.replace("git_commit_path: ''", "git_commit_path: '.'")


@pytest.fixture()  # default scope='function'
def setup_git_project(request):
  def teardown_function():
    print("teardown_git_project...")
    # tools.run_command(f'cd "{ROOTPATH}"')
    # sleep(3)
    # shutil.rmtree(PROJECTPATHWITHGIT, ignore_errors=False)
  request.addfinalizer(teardown_function)

  print('setup_git_project...')
  shutil.rmtree(PROJECTPATHWITHGIT, ignore_errors=True)
  os.makedirs(PROJECTPATHWITHGIT, exist_ok=True)
  tools.text_save(PROJECTPATHWITHGIT + '/.config.yaml', CONFIGDATAWITHGIT)
  cmd = f'cd "{PROJECTPATHWITHGIT}" && git init'
  tools.run_command(cmd)
  cmd = f'cd "{PROJECTPATHWITHGIT}" && git config user.name TNR && git config user.email tnr@email.com'
  tools.run_command(cmd)
  cmd = f'cd "{PROJECTPATHWITHGIT}" && git add . && git commit -m "init TNR project"'
  tools.run_command(cmd)


def test_1_watcher_open():
  os.makedirs(PROJECTPATHOPEN, exist_ok=True)
  tools.text_save(PROJECTPATHOPEN + '/.config.yaml', CONFIGDATA)
  w = Watcher.open(PROJECTPATHOPEN)
  w.report()
  shutil.rmtree(PROJECTPATHOPEN, ignore_errors=False)


def test_2_watcher_create():
  shutil.rmtree(PROJECTPATHNEW, ignore_errors=True)
  Watcher.create(PROJECTPATHNEW)
  w = Watcher.open(PROJECTPATHNEW)
  w.report()
  shutil.rmtree(PROJECTPATHNEW, ignore_errors=False)

def test_3_git_report(setup_git_project):
  w = Watcher.open(PROJECTPATHWITHGIT)
  w.folder | should.equal('Test Watcher withgit')
  lister_urls = [t.url for t in w.get_lister_tasks()]
  lister_urls | should.equal(['https://zhuanlan.zhihu.com/frontEndInDepth', 'https://zhuanlan.zhihu.com/learn-vue-source-code'])
  w.report()

def test_4_watch_once(setup_git_project):
  w = Watcher.open(PROJECTPATHWITHGIT)
  w.report()
  w.watch_once()
  for path in tools.all_files(w.watcher_path, '*.md', ):
    print(path)


def test_5_watcher_add_lister():
  url = 'https://zhuanlan.zhihu.com/prodesire'
  w = Watcher.create(r'D:\DataStore\prodesire')
  w.listers 
  w.add_lister(url)
  w.report()

def test_6_watcher_generate_feed():
  col.generate_feed('旗舰评论——战略航空军元帅的旗舰', 
                    limit=150, site='http://tnr-feed.netlify.com/')
