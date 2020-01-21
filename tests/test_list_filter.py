
import os, sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parentdir)
import shutil
import tools
from fetcher import FetcherFilter
from pyshould import should
import arrow
from datetime import datetime
from time import sleep
import dictdiffer
import pytest
from task import Task

'''
#### Lister
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




def test_1_lister_filter():

  item1 = {'title': 'title1 a', 'voteup': 100, 'thanks': 100}
  item2 = {'title': 'title2 a', 'voteup': 2300, 'thanks': 200}
  item3 = {'title': 'title3 a', 'voteup': 3000, 'thanks': 300}
  item4 = {'title': 'title4 b', 'voteup': 3000, 'thanks': 100}
  item5 = {'title': 'title5 b', 'voteup': 2000, 'thanks': 200}
  feed = [item1, item2, item3, item4, item5]

  option = {}
  f = FetcherFilter(iter(feed), option)
  result = f.title_contain('b').min_voteup(3000).limit(100)
  list(result) | should.eq([item4])

  f = FetcherFilter(iter(feed), option)
  result = f.title_contain('a').min_voteup(200).limit(1)
  list(result) | should.eq([item2])

  f = FetcherFilter(iter(feed), option)
  result = f.min_thanks(200)
  list(result) | should.eq([item2, item3, item5])

  f = FetcherFilter(iter(feed), option)
  result = f.title_before('title3 a')
  list(result) | should.eq([item1, item2])
  f = FetcherFilter(iter(feed), option)
  result = f.title_before('title3 a', include=True)
  list(result) | should.eq([item1, item2, item3])
