
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
import time
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


def test_4_task_to_yaml_text(): 
  desc = {
    'url': 'https://zhuanlan.zhihu.com/p/67815990', 
  }
  task = Task.create(desc, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  yaml_should = f'''- url: https://zhuanlan.zhihu.com/p/67815990
  tip: "Default Tip"
  timestamp: {{ task_add: "{tools.time_now_str()}", last_watch: "None", last_change: "None", next_watch: "{tools.time_now_str()}" }}
  version: 0'''
  task.to_yaml_text() | should.equal(yaml_should)


def test_5_task_priority(): 
  ''' 优先级受 weight task_add_time next_watch_time last_watch_time 影响
      weight 数值应该 >= 0, next_watch_time 应该已经落后于当前时间, 差距秒数称为 delta
      weight > 1, 直接以 weight 作为优先级, 忽略 last_watch_time next_watch_time
        优先级相同时, task_add_time 最晚的优先级高
        (weight 设为 > 1 是特殊情况, 表示希望立即抓取最近添加的任务)
      weight <= 1, 以 weight 作为基础的优先级, 以其他条件做调整
        - next_watch_time 越早先的, 优先级越大, 具体为在 weight 上减去 1/(next_watch_delta + 100)
        - 已经有了 last_watch_time, 则将最终的优先级 *=0.8
  '''
  desc1 = {'url': 'https://zhuanlan.zhihu.com/p/67815990'}
  task1 = Task.create(desc1, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  desc2 = {'url': 'https://zhuanlan.zhihu.com/frontEndInDepth'}
  task2 = Task.create(desc2, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  assert task1.priority == task2.priority
  
  desc1 = {'url': 'https://zhuanlan.zhihu.com/p/67815990', 'weight': 3}
  task1 = Task.create(desc1, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  desc2 = {'url': 'https://zhuanlan.zhihu.com/frontEndInDepth', 'weight': 2}
  task2 = Task.create(desc2, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  time.sleep(1)
  desc3 = {'url': 'https://zhuanlan.zhihu.com/frontEndInDepth', 'weight': 2}
  task3 = Task.create(desc3, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  desc4 = {'url': 'https://zhuanlan.zhihu.com/frontEndInDepth', 'weight': 3}
  task4 = Task.create(desc4, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  assert task4.priority > task1.priority > task3.priority > task2.priority



def test_6_task_fethcer_option(): 
  desc = { 'url': 'https://zhuanlan.zhihu.com/p/67815990', }
  task = Task.create(desc, env_option={}, fetcher_option={})
  task.fetcher_option.limit | should.equal(300)
  task = Task.create(desc, env_option={}, fetcher_option={'limit': 200})
  task.fetcher_option.limit | should.equal(200)
  task = Task.create(desc, env_option={'limit': 200}, fetcher_option={})
  task.fetcher_option.limit | should.equal(300)  # key limit should in fetcher_option

  task = Task.create(desc, env_option={'page_min_cycle': '31minutes', 'lister_min_cycle': '32minutes'}, fetcher_option={})
  task.min_cycle | should.equal('31minutes')


def test_7_task_dispatch():
  desc1 = {'url': 'https://zhuanlan.zhihu.com/p/67815990'}
  task1 = Task.create(desc1, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  desc2 = {'url': 'https://zhuanlan.zhihu.com/frontEndInDepth'}
  task2 = Task.create(desc2, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  from task import PageTask, ListerTask
  assert type(task1) == PageTask
  assert type(task2) == ListerTask


def test_8_task_run():
  pass