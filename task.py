





import os
import random

from collections import OrderedDict
from collections import Counter

import tools
from fetcher import UrlType
from fetcher import parse_type
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



from fetcher import Fetcher








class Task:
  '''
  抓取任务, 分为两类
    Lister 任务 (从列表页发现新Page)
    Page 任务 (获得一个页面)
  都需要送到 Fetcher 里抓取

  Task 包含的属性
    url:                   http://xxxx  唯一标识
    type:                  目前是 lister 或 page 两者之一
    title:                 (default '') 该页面的描述, 用于辨识 url, 
                                PageTask 的 title也用于文件命名
    version:               (default 0) 未抓取时是 version0, 之后递增

    enabled                (default True) 启用/禁用 Task
    min_cycle max_cycle    最大最小的抓取间隔时间, 
                               每当抓取结果跟上次一样时, 就翻倍等待时间, 
                               但最多不超过 max_cycle
    weight                 (default 0.5)  优先级参数

    fetch_time:            { task_add: time1, 
                             last_watch: time2, 
                             last_change: time3, 
                             next_watch: time4} 
                           创建后必然会设置 task_add 和 next_watch 为当前时间, 
                           但可以没有设置 last_watch last_change

  Lister Task 特别的属性
    limit: 15              从列表中最多获取多少条目
    min_voteup: 1000

  例:
  lister_task:
    - url: https://www.zhihu.com/xxxxxx
      tip: author's all answer
      timestamp: { task_add: "2019-07-04 21:12:16", last_watch: "2019-07-04 21:45:11", last_change: "2019-07-04 21:31:55", next_watch: "2019-07-04 21:58:27" }
      version: 5
      limit: 200
  page_task:
    - url: https://www.zhihu.com/xxxxxxx
      tip: question? - author's answer
      timestamp: { task_add: "2019-07-04 21:31:55", last_watch: "2019-07-04 21:45:13", last_change: "2019-07-04 21:32:00", next_watch: "2019-07-04 21:58:26" }
      version: 2

  用于提供基础的列表, 当Task自身属性与默认属性一致时, 可以不再记录自身属性
  单独一个Task的属性可以覆盖掉公共属性

  Lister任务 可以自定义的属性
    title_contains: filter_keyword
    min_voteup: 500
    min_thanks: 100
    limit: 10, 从列表页最多返回10个页面就结束

  可能会有多个Lister任务发现同一个页面

  Page抓取任务 可以自定义的属性
    title
    filename

  '''

  @classmethod
  def create(cls, desc, env_option):
    '''从 json description 创建 Task'''
    if str(parse_type(desc['url'])).endswith('Page'):
      pass
    elif str(parse_type(desc['url'])).endswith('Lister'):
      pass
    else:
      raise NotImplementedError

    return Task(desc, env_option)


  def __init__(self, desc, env_option):
    self.url = desc['url']
    self.url_type = parse_type(self.url)
    self.tip = tools.remove_invalid_char(str(desc.get('tip') or 'default tip').replace('\n', ' '))
 
    # 任务添加时间
    self.task_add_time = self.parse_time(desc, 'task_add')
    # 上次抓取的时间
    self.last_watch_time = self.parse_time(desc, 'last_watch')
    # 上次内容变动的时间, 不同的页面有不同的判定标准, 比如评论和点赞数变化不算变动, 内容修改算变动
    self.last_change_time = self.parse_time(desc, 'last_change')
    # 安排的下次采集时间, 可以手动修改, 立即触发一次采集
    self.next_watch_time = self.parse_time(desc, 'next_watch') 

    self.version = int(desc.get('version') or 0)
    self.option = tools.dict_merge(env_option, desc) # option 合并了所有的设置项目, 并需要传入 fetcher 
                                                     # TODO 这里能否改成引用相同 dict
    self.last_page = None

  def update_option(self, new_option):
    self.option.update(new_option)



  # 只读属性
  @property
  def min_cycle(self): 
    if self.is_lister_type:
      return str(self.option.get('lister_min_cycle'))
    elif self.is_page_type:
      return str(self.option.get('page_min_cycle'))
  @property
  def max_cycle(self): 
    if self.is_lister_type:
      return str(self.option.get('lister_max_cycle'))
    elif self.is_page_type:
      return str(self.option.get('page_max_cycle'))
  @property
  def lazy_ratio(self): return int(self.option.get('lazy_ratio') or 1)
  @property
  def weight(self): return float(self.option.get('weight') or 0.5)
  @property
  def brief_tip(self): return tools.truncate(self.tip, limit=16, ellipsis='...')
  @property
  def enabled(self): 
    enabled = self.option.get('enabled')
    if enabled in ('false', 'False', 0, False):
      return False
    else:
      return True


  def __str__(self):
    s = '''<Task #{5}> {0.url} (ver. {0.version})
    {0.tip}
    taskadd: {1}, lastwatch: {2}, lastchange: {3}, nextwatch: {4}'''
    return s.format(self, 
                    time_to_humanize(self.task_add_time),
                    self.last_watch_time and time_to_humanize(self.last_watch_time),
                    self.last_change_time and time_to_humanize(self.last_change_time),
                    time_to_humanize(self.next_watch_time),
                    id(self)
                    )

  def __repr__(self): return str(self)

  def parse_time(self, desc, time_label):
    # log('prepare parse time: {desc} {time_label}'.format(**locals()))
    # 从 desc['timestamp'] 里读配置, 整理到 arrow.time 类型
    if time_label in ('task_add', 'next_watch'):
      # 这两个如果缺省, 设为当前时间
      if not desc.get('timestamp'): return time_now()
      else: return time_from_str(desc.get('timestamp').get(time_label, time_now_str()))
    else:
      # 这两个 last_watch_time last_change_time 如果缺省, 不做设置
      if not desc.get('timestamp'): return None
      timestr = desc.get('timestamp').get(time_label, None)
      if timestr in ('null', 'none', 'None'): return None
      elif timestr: return time_from_str(timestr)
      else: return None

  def to_id(self):
    return '<Task #{}>'.format(id(self))

  def to_yaml_text(self):
    ''' 将 task 存为 yaml 文本片段
        需要缩减行数, 因此自定义格式化方案, 把timestamp放在同一行
        依次是 url, tip, timestamp x4, version
        tip 需要转义特殊字符
        task 具有 custom option, 但它来自 project 目录的 .config.yaml
        每次都重新加载, 不存放
    '''
    result = []
    result.append('- url: ' + getattr(self, 'url'))
    result.append('  tip: "' + getattr(self, 'tip').replace('"', '') + '"')
    timestamp = '  timestamp: {{ task_add: "{}", last_watch: "{}", last_change: "{}", next_watch: "{}" }}'
    timestamp = timestamp.format(
        time_to_str(self.task_add_time), 
        time_to_str(self.last_watch_time) if self.last_watch_time else None, 
        time_to_str(self.last_change_time) if self.last_change_time else None, 
        time_to_str(self.next_watch_time))
    result.append(timestamp)
    result.append('  version: ' + str(getattr(self, 'version')))

    # 存放 option 中与 default option 不同的部分
    # for key, val in self.option.items():
    #   if key in ('folder', 'url', 'tip', 'version', 'timestamp') or key.endswith('_time'):
    #     continue
    #   elif key in self.env_option and self.env_option[key] == val:
    #     continue
    #   else:
    #     result.append('    {}: {}'.format(key, str(val)))

    return '\n'.join(result)


  @property
  def is_page_type(self): return str(self.url_type).endswith('Page')
  @property
  def is_lister_type(self): return str(self.url_type).endswith('Lister')

  def run(self):
    '''执行一次抓取'''
    if self.is_page_type:
      # log('Task.run page request: {}'.format(str(self)))
      fetcher = Fetcher.create(fetcher_option=self.option)
      data_json = fetcher.request()
      # log('Task.run fetch page done')
      return data_json
    elif self.is_lister_type:
      # 探测新的页面
      # log('Task.run lister request: {}'.format(str(self)))
      fetcher = Fetcher.create(fetcher_option=self.option)
      tasks_json = fetcher.request()
      log('Task.run detect new tasks done: {} tasks'.format(len(tasks_json)))
      return tasks_json
    else:
      raise ValueError('cannot parse {} {}'.format(self.to_id(), self.url))

  def schedule(self, is_modified):
    ''' 如果成功存储, 则更新 version, last_watch_time, next_watch_time, tip
        根据上次是否变化, 安排下一次的抓取日程

        lazy_ratio: 抓取后如果发现内容自从历史 `A` 时起就没变过, 
                    则将下次抓取时间设为 `(now-A) * lazy_ratio`
                    理想状态下, 文章内容不变, 每次抓取间隔就以指数增长
                    如果某次抓取后发现内容改变, 则恢复为 min_cycle 的时间
                    lazy_ratio 默认设为1, 意味着按照2的幂次延迟下一次的抓取时间
                    当认为内容不会总变化时, lazy_ratio 可以乐观设置为 10, 
                        每次采集将使下次采集延长至10倍时间之后, 更省资源
                    当认为内容总变时, 比如lister型的任务, lazy_ratio 可以悲观设置可以为 0, 
                        这样将永远用 min_cycle 做安排

        min_cycle 下次抓取至少需要间隔的时间 (3分钟)
        max_cycle 下次抓取最多可以间隔的时间 (60天)
        以lazy_ratio计算出的时间要限制到 {min_cycle, max_cycle} 范围内


    '''
    # 更新 last_change_time, next_watch_time
    # 首先检测这次跟上次相比, 抓取到的内容是否已经改变
    if not self.last_change_time or is_modified:  # 没有上次, 或者这次相比上次有改变
      self.last_change_time = time_now()
      shift_secs = duration_from_humanize(self.min_cycle)
      self.next_watch_time = time_now().shift(seconds=shift_secs)
    else: # 跟上次已有的抓取内容一样, 此时不更新 last_change_time, 只动 next_watch_time
      # 以此时到现在的时间间隔 * lazy_ratio 作为下次安排时间
      not_changed = time_now() - self.last_change_time
      shift_secs = not_changed.days * 24 * 3600 + not_changed.seconds  # 把 diff 时间转为秒
      shift_secs = shift_secs * self.lazy_ratio # 计算培增比率, 之后再约束到 min_cycle max_cycle 之间
      shift_secs = max(shift_secs, duration_from_humanize(self.min_cycle))
      shift_secs = min(shift_secs, duration_from_humanize(self.max_cycle))
      self.next_watch_time = time_now().shift(seconds=shift_secs)

    # 更新 last_watch_time, version
    self.last_watch_time = time_now()
    self.version += 1
    # log('reschedule {} done'.format(self.to_id()))






  @property
  def priority(self):
    ''' 优先级从 weight 和 task_add_time next_watch_time last_watch_time 综合得出
        优先级越大的 task 越先执行
        weight 数值应该 >= 0, next_watch_time 应该已经落后于当前时间, 差距秒数称为 delta
        weight > 1, 直接以 weight 作为优先级, 忽略 last_watch_time next_watch_time
                    优先级相同时, task_add_time 最晚的优先级高
                    (weight 设为 > 1 是特殊情况, 表示希望立即抓取最近添加的任务)
        weight <= 1, 以 weight 作为基础的优先级, 以其他条件做调整
                     - next_watch_time 越早先的, 优先级越大, 具体为在 weight 上减去 1/(next_watch_delta + 100)
                     - 已经有了 last_watch_time, 则将最终的优先级 *=0.8

    '''
    weight = max(self.weight, 0)
    if weight > 1:
      s = tools.time_delta_from_now(self.task_add_time)
      s = max(s, 0)
      return weight + 1/(s + 100)
    else:
      s = tools.time_delta_from_now(self.next_watch_time)
      s = max(s, 0)
      weight = max(weight - 1/(s + 100), 0)
      if self.last_watch_time:
        return weight * 0.8 
      else:
        return weight



  @property
  def should_fetch(self):
    return self.enabled and (self.next_watch_time <= time_now().shift(seconds=1))












# =========================================================
# =================== end of class Task ===================
# =========================================================



