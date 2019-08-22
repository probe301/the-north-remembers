
import os
import random

from collections import OrderedDict
from collections import Counter

import tools
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

log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')


from page import Page
from werkzeug.contrib.atom import AtomFeed


def remember(commit_log, watcher_path):
  ''' 将 watcher 抓取到的内容存储到 git 仓库
      git 仓库通常位于 watcher folder 的上一层
  '''
  git_path = os.path.dirname(watcher_path) # watcher folder 上一层
  cmd = 'cd {} && git add . && git commit -m "{}"'.format(git_path, commit_log)
  # log(cmd)
  os.system(cmd)
  log('Watcher.remember added + committed {} {}'.format(watcher_path, commit_log))



def generate_feed(watcher_path, save_xml=False):
  ''' 生成 RSS, 内容为全部 page_task, 
      按照添加任务的顺序倒序排列 (按照更新时间排列? TODO)
      RSS Feed 文件名为 Watcher 文件夹名称
      '''
  feed_name = os.path.basename(watcher_path)
  feed = AtomFeed(feed_name,
                  feed_url="feed_url--request.url", 
                  url="url--request.url_root")
  # info = '''
  #   - title: title1
  #     rendered_text: rendered_text1
  #     author_name: author_name1
  #     url: http://11.22.com
  #     last_update: 2016-1-1
  #     published: 2016-1-1
  #   - title: title2
  #     rendered_text: rendered_text2
  #     author_name: author_name2
  #     url: http://22.22.com
  #     last_update: 2016-1-12
  #     published: 2016-1-12
  # '''
  pages = []
  count = 10
  for path in tools.all_files(watcher_path, patterns='*.md'):
    if not count: break
    count -= 1
    try:
      page = Page.load(path)
      pages.append(page)
    except:
      log(f'error Page.load({path})')
      raise
    

  for page in pages:
    log(page)

  for page in sorted(pages, key=lambda page: page.watch_time):
    feed.add(page.metadata['title'],
             page.to_html(cut=500),
             content_type='html',
             author="article.get('author_name')",
             url=page.metadata['url'],
             updated=tools.time_from_str(page.watch_time),
             published=tools.time_from_str(page.watch_time)
            )
  return feed.get_response()



