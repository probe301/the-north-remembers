
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
  Page.load(filepath)   从本地文件返回页面
  Page.create(data) 返回一个新建 (data json) 页面
  page.write()  存储页面
  page.render() 转为其他格式
  page.compare() 比对两个页面的区别?

  文本形式为 (参考 Jekyll markdown)
  ---
  title:  title
  url:  url
  metadatakey1: value1
  metadatakey2: value2
  metadatakey3: value3
  ---

  # 标题

  ## 内容分段1 (如问题 / 引文)

  ### 文章内部标题1
  ### 文章内部标题2
  ### 文章内部标题3
  ### 文章内部标题4

  ## 内容分段2 (如回答 / 正文)

  ### 文章内部标题5
  ### 文章内部标题6


  抓取文章中自带标题尽量降级到 `三级 title (###)` 以下

'''


# @pytest.fixture()  # default scope='function'
# def setup_git_project(request):
#   def teardown_function():
#     print("teardown_git_project...")
#     # tools.run_command(f'cd "{ROOTPATH}"')
#     # sleep(3)
#     # shutil.rmtree(PROJECTPATHWITHGIT, ignore_errors=False)
#   request.addfinalizer(teardown_function)

#   print('setup_git_project...')
#   shutil.rmtree(PROJECTPATHWITHGIT, ignore_errors=True)
#   os.makedirs(PROJECTPATHWITHGIT, exist_ok=True)
#   tools.text_save(PROJECTPATHWITHGIT + '/.config.yaml', CONFIGDATAWITHGIT)
#   cmd = f'cd "{PROJECTPATHWITHGIT}" && git init'
#   tools.run_command(cmd)
#   cmd = f'cd "{PROJECTPATHWITHGIT}" && git config user.name TNR && git config user.email tnr@email.com'
#   tools.run_command(cmd)
#   cmd = f'cd "{PROJECTPATHWITHGIT}" && git add . && git commit -m "init TNR project"'
#   tools.run_command(cmd)


PAGETESTFOLDER = r'D:\DataStore\Test Watcher pages'

def test_1_page_open():
  page1 = Page.create(data)
  page2 = Page.load(path)

  assert page1.full_text == page2.full_text
  assert page1.title == page2.title
  assert page1.url == page2.url
  assert page1.version == page2.version
  assert page1.create_date == page2.create_date

  assert page1.from_disk == False
  assert page2.from_disk == True





def test_2_page_is_changed():
  pass

def test_3_page_write():
  pass

def test_4_page_render():
  pass


def test_5_page_to_html():
  pass