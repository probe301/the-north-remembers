





import os
import random
import re
import arrow

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
from fetcher import FetcherOption
from datetime import date, datetime
import pydantic 





class ArrowDate(str):
  '''基于 arrow 的 datetime 字段验证器'''
  @classmethod
  def __get_validators__(cls):
    yield cls.validate
  @classmethod
  def validate(cls, v):
    if isinstance(v, arrow.Arrow):
      return v
    if isinstance(v, (int, float)):
      return tools.time_from_stamp(v)
    if isinstance(v, str):
      try:
        return tools.time_from_str(v)
      except arrow.parser.ParserError:
        raise ValueError(f'cannot parse date {v}')
    raise ValueError(f'invalid date {v}')    

class Task(pydantic.BaseModel):
  '''
  抓取任务, 分为两类继承
    class ListerTask(Task) 任务 (检测列表页, 发现新页面)
    class PageTask(Task) 任务 (获得该页面)
  都需要送到 Fetcher 里抓取
  task 的属性分为三部分

  1 跟 task 自身有关, 
    如 url tip time(x4) version
    需要存到 tasks.json
  2 由用户在 config.yaml 里配置, 每次创建 task 时都重新加载当前的 config.yaml 配置, 
    如 page_min_cycle lister_max_cycle weight enabled
    不需要存到 tasks.json
  3 其余未识别的, 都将传给 fetcher 处理, 这些也是由用户在 config.yaml 里配置, 每次重新加载
    如 save_attachments limit min_voteup title_contains
  '''
  # 来自task自身参数
  url : str                 # url 唯一标识
  tip = 'Default Tip'       # 该页面的描述, 用于辨识 url

  task_add_time : ArrowDate = None    # 任务添加时间
  last_watch_time : ArrowDate = None  # 上次抓取的时间
  last_change_time : ArrowDate = None # 上次内容变动的时间, 不同的页面有不同的判定标准
  next_watch_time : ArrowDate = None  # 安排的下次采集时间, 手动修改就立即触发一次采集
  # 创建后会设置 task_add 和 next_watch 为当前时间,
  # 但可以没有设置 last_watch last_change

  version = 0                # 未抓取时是 version0, 之后递增
  weight = 0.5               # 权重参数, 用于计算优先级
  enabled = True             # 启用/禁用 Task
  lazy_ratio = 1


  min_cycle : str = None       # 由继承类处理
  max_cycle : str = None       # 由继承类处理
  # page_min_cycle = '5days'   # 最大最小的抓取间隔时间,
  # page_max_cycle = '15days'  # 每当抓取结果跟上次一样时, 就翻倍等待时间,
  # lister_min_cycle = '1days' # 但最多不超过 max_cycle
  # lister_max_cycle = '2days'

  # 来自Fetcher参数
  fetcher_option : FetcherOption
  @pydantic.validator('url')
  def url_should_valid(cls, v):
    v = v.strip()
    if v.strip().startswith(('http://', 'https://')): return v
    else: raise ValueError(f'invalid url {v}')

  @pydantic.validator('tip')
  def tip_should_remove_invalid_char(cls, v):
    return tools.remove_invalid_char(str(v).replace('\n', ' '))

  # task 内部使用 arrow.time 类型,
  # task 序列化时, 使用 2019-12-03 18:35:35 风格
  # TODO 应该改为 2019-12-03T18:35:35.590582+08:00 风格
  @pydantic.validator('task_add_time', always=True, pre=True)
  def task_add_time_set_now(cls, v):   # 这两个如果缺省, 设为当前时间
    # log(f'task_add_time_set_now v={v}')
    return v or time_now()
  @pydantic.validator('next_watch_time', always=True, pre=True)
  def next_watch_time_set_now(cls, v): # 这两个如果缺省, 设为当前时间
    return v or time_now()
  @pydantic.validator('last_watch_time', pre=True)
  def last_watch_time_setting(cls, v): # 如果缺省, 不做设置
    # log(f'last_watch_time_setting v={v}')
    if v in ('null', 'none', 'None', None): return None
    else: return v
  @pydantic.validator('last_change_time', pre=True)
  def last_change_time_setting(cls, v): # 如果缺省, 不做设置
    if v in ('null', 'none', 'None', None): return None
    else: return v

  def __str__(self):
    s = '''<Task url="{0.url}">
    ├─── "{0.tip}" ver.{0.version}
    └─── add: {1}, watch: {2}, change: {3}, next: {4}'''
    return s.format(self,
                    time_to_humanize(self.task_add_time),
                    self.last_watch_time and time_to_humanize(self.last_watch_time),
                    self.last_change_time and time_to_humanize(self.last_change_time),
                    time_to_humanize(self.next_watch_time),
                    )

  @classmethod
  def create(cls, desc, env_option={}, fetcher_option={}):
    '''从 json description 创建 Task'''
    option = tools.dict_merge(env_option, desc)
    if 'timestamp' in option:
      option['task_add_time'] = option['timestamp'].get('task_add')
      option['next_watch_time'] = option['timestamp'].get('next_watch')
      option['last_watch_time'] = option['timestamp'].get('last_watch')
      option['last_change_time'] = option['timestamp'].get('last_change')
    t = parse_type(option['url'])
    if str(t).endswith('Lister'):
      return ListerTask(**option, fetcher_option=fetcher_option)
    if str(t).endswith('Page'):
      return PageTask(**option, fetcher_option=fetcher_option)
    raise ValueError(f'cannot create Task for {option["url"]}')


  # 只读属性
  @property
  def brief_tip(self): return tools.truncate(self.tip, limit=16, ellipsis='...')

  def patch(self, data):
    new_fetcher_option = FetcherOption(**data)
    self.fetcher_option.patch(new_fetcher_option.dict())

    for k, v in data.items():
      if (k in self.__fields__) and (k not in ('fetcher_option', 'url')):
        setattr(self, k, v)


  def to_yaml_text(self):
    ''' 将 task 存为 yaml 文本片段
        需要缩减行数, 因此自定义格式化方案, 把timestamp放在同一行
        依次是 url, tip, timestamp x4, version
        tip 需要转义特殊字符
        task 具有 custom option, 但它来自 project 目录的 .config.yaml
        每次都重新加载, 不存放
    '''
    result = []
    result.append('- url: ' + self.url)
    result.append('  tip: "' + self.tip + '"')
    timestamp = '  timestamp: {{ task_add: "{}", last_watch: "{}", last_change: "{}", next_watch: "{}" }}'
    timestamp = timestamp.format(
        time_to_str(self.task_add_time),
        time_to_str(self.last_watch_time) if self.last_watch_time else None,
        time_to_str(self.last_change_time) if self.last_change_time else None,
        time_to_str(self.next_watch_time))
    result.append(timestamp)
    result.append('  version: ' + str(getattr(self, 'version')))
    return '\n'.join(result)

  @property
  def url_type(self): return parse_type(self.url)
  @property
  def is_page_type(self): return str(self.url_type).endswith('Page')
  @property
  def is_lister_type(self): return str(self.url_type).endswith('Lister')
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


  def run(self):
    '''执行一次抓取'''
    raise NotImplementedError

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



# =========================================================
# =================== end of class Task ===================
# =========================================================


class ListerTask(Task):
  # 最大最小的抓取间隔时间, 每当抓取结果跟上次一样时, 
  # 就翻倍等待时间, 但最多不超过 max_cycle
  min_cycle : str      # 1day
  max_cycle : str      # 3days

  @pydantic.root_validator(pre=True)
  def check_root(cls, values):
    # print(f'check_root {values}')
    min_cycle = values.get('lister_min_cycle') or values.get('min_cycle') or '1day'
    max_cycle = values.get('lister_max_cycle') or values.get('max_cycle') or '3days'
    try: 
      tools.duration_from_humanize(min_cycle)
      tools.duration_from_humanize(max_cycle)
    except ValueError: 
      raise ValueError(f'ListerTask min_cycle or max_cycle invalid: {min_cycle} {max_cycle}')
    if tools.duration_from_humanize(max_cycle) < tools.duration_from_humanize(min_cycle):
      # max_cycle 必须 >= min_cycle
      raise ValueError(f'max_cycle {max_cycle} should >= min_cycle {min_cycle}')
    values['min_cycle'] = min_cycle 
    values['max_cycle'] = max_cycle 
    return values

  def run(self):
    '''执行一次抓取'''
    # 探测新的页面
    # log('Task.run lister request: {}'.format(str(self)))
    fetcher = Fetcher.create(url=self.url, fetcher_option=self.fetcher_option.dict())
    tasks_json = fetcher.request()
    log('Task.run detect new tasks done: {} tasks'.format(len(tasks_json)))
    return tasks_json









class PageTask(Task):
  # 最大最小的抓取间隔时间, 每当抓取结果跟上次一样时, 
  # 就翻倍等待时间, 但最多不超过 max_cycle
  min_cycle : str # = '5days'
  max_cycle : str # = '15days'

  @pydantic.root_validator(pre=True)
  def check_root(cls, values):
    # print(f'check_root {values}')
    min_cycle = values.get('page_min_cycle') or values.get('min_cycle') or '5days'
    max_cycle = values.get('page_max_cycle') or values.get('max_cycle') or '15days'
    try: 
      tools.duration_from_humanize(min_cycle)
      tools.duration_from_humanize(max_cycle)
    except ValueError: 
      raise ValueError(f'PageTask min_cycle or max_cycle invalid: {min_cycle} {max_cycle}')
    if tools.duration_from_humanize(max_cycle) < tools.duration_from_humanize(min_cycle):
      # max_cycle 必须 >= min_cycle
      raise ValueError(f'max_cycle {max_cycle} should >= min_cycle {min_cycle}')
    values['min_cycle'] = min_cycle 
    values['max_cycle'] = max_cycle 
    return values



  def run(self):
    '''执行一次抓取'''
    # log('Task.run page request: {}'.format(str(self)))
    fetcher = Fetcher.create(url=self.url, fetcher_option=self.fetcher_option)
    data_json = fetcher.request()
    # log('Task.run fetch page done')
    return data_json
