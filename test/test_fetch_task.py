
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
  'limit': 5,
  'title_contains': 'filter,keyword',
}

def test_1_fetch_wemp_page():
  desc = { 'url': 'https://wemp.app/posts/b25d6561-8e09-44c6-93e4-3fbfffcd1261',  
           'tip': 'Vue 组件库实践和设计', }
  task = Task.create(desc, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
  data = task.run()
  # print(data)
  data['metadata']['title']       | should.equal('Vue 组件库实践和设计')
  data['metadata']['author_name'] | should.equal('Vue中文社区')
  data['metadata']['author_id']   | should.equal('18173241-bb5e-4841-8e96-236efc512aaa')
  # tools.text_save('t2.md', data['content'])
  content = data['content']
  assert content.startswith('## 原文链接：https://juejin.im/post/598965')
  assert content.endswith('XziaH3pOQ/0)\n\n\n强者怒时向更强者挑衅\n\n弱者怒时向更弱者挑衅')



def test_2_fetch_wemp_lister():
  desc = { 'url': 'https://wemp.app/accounts/18173241-bb5e-4841-8e96-236efc512aaa',  
           'tip': '微信公众号 Vue中文社区', }
  task = Task.create(desc, env_option=ENV_OPTION, fetcher_option={'limit': 3})
  data = task.run()
  print(data)
  len(data) | should.equal(3)
  data[0]['url']  | should.eq('https://wemp.app/posts/e8c57dfb-3b81-4229-9742-da4890cd9688')
  data[0]['tip']  | should.eq('8道有意思的JavaScript面试题，附解答')


def test_3_fetch_wemp_lister_in_multiple_listers():
  desc = { 'url': 'https://wemp.app/accounts/18173241-bb5e-4841-8e96-236efc512aaa',  
           'tip': '微信公众号 Vue中文社区', }
  task = Task.create(desc, env_option=ENV_OPTION, fetcher_option={'limit': 23})
  data = task.run()
  print(data)
  len(data) | should.equal(23)
  data[0]['url']  | should.eq('https://wemp.app/posts/e8c57dfb-3b81-4229-9742-da4890cd9688')
  data[0]['tip']  | should.eq('8道有意思的JavaScript面试题，附解答')


def test_4_fetch_wemp_lister_all_fetch():
  desc = { 'url': 'https://wemp.app/accounts/18173241-bb5e-4841-8e96-236efc512aaa',  
           'tip': '微信公众号 Vue中文社区', }
  task = Task.create(desc, env_option=ENV_OPTION, fetcher_option={'limit': 500})
  data = task.run()
  print(data)
  len(data) | should.equal(37)






# def test_3_task_default_params():
#   desc = {
#     'url': 'https://zhuanlan.zhihu.com/p/67815990', 
#   }
#   env_option = {
#   }
#   task = Task.create(desc, env_option=env_option, fetcher_option=FETCHER_OPTION)
#   task.tip     | should.equal('Default Tip')
#   task.version | should.equal(0)
#   task.min_cycle | should.equal('5days')
#   task.max_cycle | should.equal('15days')
#   task.weight | should.equal(0.5)
#   task.enabled | should.equal(True)
#   desc = {
#     'url': 'https://zhuanlan.zhihu.com/frontEndInDepth', 
#   }
#   task = Task.create(desc, env_option=env_option, fetcher_option=FETCHER_OPTION)
#   task.min_cycle | should.equal('1day')
#   task.max_cycle | should.equal('3days')


# def test_4_task_to_yaml_text(): 
#   desc = {
#     'url': 'https://zhuanlan.zhihu.com/p/67815990', 
#   }
#   task = Task.create(desc, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
#   yaml_should = f'''- url: https://zhuanlan.zhihu.com/p/67815990
#   tip: "Default Tip"
#   timestamp: {{ task_add: "{tools.time_now_str()}", last_watch: "None", last_change: "None", next_watch: "{tools.time_now_str()}" }}
#   version: 0'''
#   task.to_yaml_text() | should.equal(yaml_should)


# def test_5_task_priority(): 
#   ''' 优先级受 weight task_add_time next_watch_time last_watch_time 影响
#       weight 数值应该 >= 0, next_watch_time 应该已经落后于当前时间, 差距秒数称为 delta
#       weight > 1, 直接以 weight 作为优先级, 忽略 last_watch_time next_watch_time
#         优先级相同时, task_add_time 最晚的优先级高
#         (weight 设为 > 1 是特殊情况, 表示希望立即抓取最近添加的任务)
#       weight <= 1, 以 weight 作为基础的优先级, 以其他条件做调整
#         - next_watch_time 越早先的, 优先级越大, 具体为在 weight 上减去 1/(next_watch_delta + 100)
#         - 已经有了 last_watch_time, 则将最终的优先级 *=0.8
#   '''
#   desc1 = {'url': 'https://zhuanlan.zhihu.com/p/67815990'}
#   task1 = Task.create(desc1, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
#   desc2 = {'url': 'https://zhuanlan.zhihu.com/frontEndInDepth'}
#   task2 = Task.create(desc2, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
#   assert task1.priority == task2.priority
  
#   desc1 = {'url': 'https://zhuanlan.zhihu.com/p/67815990', 'weight': 3}
#   task1 = Task.create(desc1, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
#   desc2 = {'url': 'https://zhuanlan.zhihu.com/frontEndInDepth', 'weight': 2}
#   task2 = Task.create(desc2, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
#   time.sleep(1)
#   desc3 = {'url': 'https://zhuanlan.zhihu.com/frontEndInDepth', 'weight': 2}
#   task3 = Task.create(desc3, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
#   desc4 = {'url': 'https://zhuanlan.zhihu.com/frontEndInDepth', 'weight': 3}
#   task4 = Task.create(desc4, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
#   assert task4.priority > task1.priority > task3.priority > task2.priority



# def test_6_task_fethcer_option(): 
#   desc = { 'url': 'https://zhuanlan.zhihu.com/p/67815990', }
#   task = Task.create(desc, env_option={}, fetcher_option={})
#   task.fetcher_option.limit | should.equal(300)
#   task = Task.create(desc, env_option={}, fetcher_option={'limit': 200})
#   task.fetcher_option.limit | should.equal(200)
#   task = Task.create(desc, env_option={'limit': 200}, fetcher_option={})
#   task.fetcher_option.limit | should.equal(300)  # key limit should in fetcher_option

#   task = Task.create(desc, env_option={'page_min_cycle': '31minutes', 'lister_min_cycle': '32minutes'}, fetcher_option={})
#   task.min_cycle | should.equal('31minutes')


# def test_7_task_dispatch():
#   desc1 = {'url': 'https://zhuanlan.zhihu.com/p/67815990'}
#   task1 = Task.create(desc1, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
#   desc2 = {'url': 'https://zhuanlan.zhihu.com/frontEndInDepth'}
#   task2 = Task.create(desc2, env_option=ENV_OPTION, fetcher_option=FETCHER_OPTION)
#   from task import PageTask, ListerTask
#   assert type(task1) == PageTask
#   assert type(task2) == ListerTask


# def test_8_task_run():
#   pass