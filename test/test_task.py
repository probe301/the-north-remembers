
import os, sys 
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
sys.path.insert(0, parentdir)
import shutil
import tools
import arrow
from pyshould import should
from datetime import datetime
from pydantic import (HttpUrl, DirectoryPath, FilePath,)
import dictdiffer
import pytest
from task import Task

DESC = {
  'url': 'https://zhuanlan.zhihu.com/p/67815990', 
  'tip': 'test task', 
  'task_add_time': "2019-12-01 18:59:09", 
  'last_watch_time': "2019-12-01 19:05:06", 
  'last_change_time': "2019-12-01 19:05:06", 
  'next_watch_time': "2019-12-02 19:05:06" ,
  'version': 1
}
ENV_OPTION = {
  'page_min_cycle': '15days', 
  'page_max_cycle': '25days', 
  'lister_min_cycle': '1days', 
  'lister_max_cycle': '3days', 
  'weight': 0.8,
  'enabled': True,
}
FETCHER_OPTION = {
  'save_attachments': True,
  'limit': 300,
  'min_voteup': 300,
  'min_thanks': 300,
  'title_contains': 'filter,keyword',
}


@pytest.fixture(scope='function')
def setup_function(request):
    def teardown_function():
        print("teardown_function called.")
    request.addfinalizer(teardown_function)  # 此内嵌函数做teardown工作
    print('setup_function called.')

@pytest.fixture(scope='module')
def setup_module(request):
    def teardown_module():
        print("teardown_module called.")
    request.addfinalizer(teardown_module)
    print('setup_module called.')









def test_1_task_create_usage():
  task = Task.create(DESC, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  should_result = {
    'url': 'https://zhuanlan.zhihu.com/p/67815990', 
    'tip': 'test task', 
    'task_add_time': tools.time_from_str("2019-12-01 18:59:09"), 
    'last_watch_time': tools.time_from_str("2019-12-01 19:05:06"), 
    'last_change_time': tools.time_from_str("2019-12-01 19:05:06"), 
    'next_watch_time': tools.time_from_str("2019-12-02 19:05:06"),
    'version': 1,
    'min_cycle': '15days', 
    'max_cycle': '25days',
    'lazy_ratio': 1,
    'weight': 0.8,
    'enabled': True,
    'fetcher_option': {
      'text_include': None, 
      'text_exclude': None, 
      'save_attachments': True, 
      'limit': 300, 
      'min_voteup': 300, 
      'min_thanks': 300
    }, 
  }
  list(dictdiffer.diff(task.dict(), should_result)) | should.equal([])


@pytest.mark.date
def test_2_task_parse_date():
  desc = {
    'url': 'https://zhuanlan.zhihu.com/p/67815990', 
    'tip': 'test task', 
  }
  task = Task.create(desc, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  task.dict()['task_add_time'].timestamp    | should.equal(tools.time_now().timestamp)
  task.dict()['last_watch_time']            | should.equal(None)
  task.dict()['last_change_time']           | should.equal(None)
  task.dict()['next_watch_time'].timestamp  | should.equal(tools.time_now().timestamp)

  desc = {
    'url': 'https://zhuanlan.zhihu.com/p/67815990', 
    'tip': 'test task', 
    'task_add_time': None, 
    'last_watch_time': None, 
    'last_change_time': None, 
    'next_watch_time': None,
  }
  task = Task.create(desc, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  task.task_add_time.timestamp    | should.equal(tools.time_now().timestamp)
  task.last_watch_time            | should.equal(None)
  task.last_change_time           | should.equal(None)
  task.next_watch_time.timestamp  | should.equal(tools.time_now().timestamp)


  desc = {
    'url': 'https://zhuanlan.zhihu.com/p/67815990', 
    'tip': 'test task', 
    'task_add_time': "2019-12-01 18:59:09", 
    'last_watch_time': None, 
    'last_change_time': None, 
    'next_watch_time': "2019-12-01 18:59:09",
  }
  task = Task.create(desc, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  task.dict()['task_add_time']    | should.equal(tools.time_from_str("2019-12-01 18:59:09"))
  task.dict()['last_watch_time']  | should.equal(None)
  task.dict()['last_change_time'] | should.equal(None)
  task.dict()['next_watch_time']  | should.equal(tools.time_from_str("2019-12-01 18:59:09"))



def test_3_task_default_params():
  desc = {
    'url': 'https://zhuanlan.zhihu.com/p/67815990', 
  }
  env_option = {
  }
  task = Task.create(desc, env_option=env_option, fetcher_option=FETCHER_OPTION)
  task.tip     | should.equal('Default Tip')
  task.version | should.equal(0)
  task.min_cycle | should.equal('5days')
  task.max_cycle | should.equal('15days')
  task.weight | should.equal(0.5)
  task.enabled | should.equal(True)
  desc = {
    'url': 'https://zhuanlan.zhihu.com/frontEndInDepth', 
  }
  task = Task.create(desc, env_option=env_option, fetcher_option=FETCHER_OPTION)
  task.min_cycle | should.equal('1day')
  task.max_cycle | should.equal('3days')


def test_4_task_to_yaml_text(): pass
def test_5_task_priority():  pass
def test_6_task_fethcer_option(): 
  desc = {
    'url': 'https://zhuanlan.zhihu.com/p/67815990', 
  }
  task = Task.create(desc, env_option={}, fetcher_option={})
  task.fetcher_option.limit | should.equal(300)