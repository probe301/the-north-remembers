





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
# from lister import Lister
from fetcher import Fetcher








class Task:
  '''
  任务, 分为Lister抓取任务 (发现新Page), 和 Page抓取任务

  一个 .task.yaml 下所有Task的默认属性

      default_option:
        lister:
          enabled: true
          max_cycle: 15day
          min_cycle: 10minutes
          zhihu_min_voteup: 1000
          weight: 0.5
          limit: 15
        page:
          enabled: true
          max_cycle: 1day
          min_cycle: 10minutes
          weight: 0.5

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

  Task 必须包含的属性
    folder                 隐式由 .task.yaml 所在位置决定
    enabled                (default True) 启用/禁用 Task
    min_cycle max_cycle    (default '3minutes' '1day')  间隔时间区间         
    weight                 (default 0.5)  优先级  

    url:                   http://xxxx  处理干净作为 pk
    tip:                   (default 'Tip') 对该页面的描述, 可以直接用网页 title, 不参与文件名
    version:               (default 0) 未 fetch 时是 version0, 之后递增
    time:                  { task_add: time1, 
                             last_watch: time2, 
                             last_change: time3, 
                             next_watch: time4} 
                           创建后必然会设置 task_add 和 next_watch为当前, 
                           但允许没有设置 last_watch last_change

  用于提供基础的列表, 当Task自身属性与默认属性一致时, 可以不再记录自身属性
  单独一个Task的属性可以覆盖掉公共属性

  Lister任务 可以自定义的属性
    title_contains: filter_keyword
    zhihu_min_voteup: 500
    zhihu_min_thanks: 100
    limit: 10, 从列表页最多返回10个页面就结束

  可能会有多个Lister任务发现同一个页面

  Page抓取任务 可以自定义的属性
    title
    filename

  '''

  @classmethod
  def create(cls, desc, default_option):
    '''从 json description 创建 Task'''
    folder = default_option['folder']
    if str(parse_type(desc['url'])).endswith('Page'):
      default_option = default_option['page']
      default_option['folder'] = folder
    elif str(parse_type(desc['url'])).endswith('Lister'):
      default_option = default_option['lister']
      default_option['folder'] = folder
    else:
      raise NotImplementedError

    return Task(desc, default_option)


  def __init__(self, desc, default_option):
    self.default_option = default_option
    self.url = desc['url']
    self.url_type = parse_type(self.url)
    self.tip = str(desc.get('tip') or 'default tip').replace('\n', ' ').replace(':', ' ')
 
    # 任务添加时间
    self.task_add_time = self.parse_time(desc, 'task_add')
    # 上次抓取的时间
    self.last_watch_time = self.parse_time(desc, 'last_watch')
    # 上次内容变动的时间, 不同的页面有不同的判定标准, 比如评论和点赞数变化不算变动, 内容修改算变动
    self.last_change_time = self.parse_time(desc, 'last_change')
    # 安排的下次采集时间, 可以手动修改, 立即触发一次采集
    self.next_watch_time = self.parse_time(desc, 'next_watch') 

    self.version = int(desc.get('version') or 0)
    option = self.default_option.copy()
    option.update(desc)
    self.option = option # option 合并了所有的设置项目, 并需要传入 fetcher
    self.last_page = None

  # 只读属性
  @property
  def min_cycle(self): return str(self.option.get('min_cycle') or '3minutes') 
  @property
  def max_cycle(self): return str(self.option.get('max_cycle') or '1day') 
  @property
  def lazy_ratio(self): return int(self.option.get('lazy_ratio') or 1)
  @property
  def weight(self): return float(self.option.get('weight') or 0.5)
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
        依次是 url, tip, timestamp x4, version, custom option
        custom option 用于存放与default option 有区别的部分
    '''
    result = []
    result.append('  - url: ' + getattr(self, 'url'))
    result.append('    tip: ' + getattr(self, 'tip'))
    timestamp = '    timestamp: {{ task_add: "{}", last_watch: "{}", last_change: "{}", next_watch: "{}" }}'
    timestamp = timestamp.format(
        time_to_str(self.task_add_time), 
        time_to_str(self.last_watch_time) if self.last_watch_time else None, 
        time_to_str(self.last_change_time) if self.last_change_time else None, 
        time_to_str(self.next_watch_time))
    result.append(timestamp)
    result.append('    version: ' + str(getattr(self, 'version')))

    # 存放 option 中与 default option 不同的部分

    for key, val in self.option.items():
      if key in ('folder', 'url', 'tip', 'version', 'timestamp') or key.endswith('_time'):
        continue
      elif key in self.default_option and self.default_option[key] == val:
        continue
      else:
        result.append('    {}: {}'.format(key, str(val)))

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




  def save(self, data_json=None, diff=None):
    # 存储Page页
    data_json['url'] = self.url
    data_json['folder'] = self.option['folder']
    data_json['watch_time'] = time_now()
    data_json['version'] = self.version + 1
    page = Page.create(data_json)
    page.write()

    if self.last_page:
      is_modified = page.is_changed(self.last_page)
    else:
      is_modified = True

    self.last_page = page
    # log('save {} done'.format(self.to_id()))
    return is_modified


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



  @property
  def content_is_changed(self):
    # TODO IMPL
    return random.random() > 0.8
    # return True


  # def report(cls):
  #   tasks = Task.select()
  #   now = datetime.now()
  #   tasks_todo = Task.select().where(Task.next_watch <= now)

  #   log('Task total={} todo={}'.format(tasks.count(), tasks_todo.count()))
  #   log('todo tasks:')
  #   for task in tasks_todo.order_by(Task.next_watch):
  #     log(task)
  #   log('Task total={} todo={}'.format(tasks.count(), tasks_todo.count()))
  #   return tasks_todo.count()






# =========================================================
# =================== end of class Task ===================
# =========================================================































































class Watcher:
  '''
  任务调度, 维护任务队列, 执行抓取任务
  每个 Watcher 实例加载一个 ".task.yaml"
  ".task.yaml" 分为 default_option, lister_task, page_task 三部分设置

  - default_option 存放任务的默认设置
  - lister_task 是获取新页面的任务, 以 url 做为标识, 可以覆盖 default_option 的设置
  - page_task 是逐个抓取页面的任务, 以 url 做为标识, 可以覆盖 default_option 的设置

  Watcher 运行时, 
    lister_task 里的任务首先运行, 获取这段时间新增的页面, 创建新的 page_task 
    然后 page_task 里的任务运行, 挨个抓取具体的页面

  当 watcher.init() 时:
    加载 task.yaml, 分析设置, 创建所有的 tasks
    输出一个报告

  当 watcher.watch() 时:
    找出需要执行的 tasks, 对这些 tasks 按照优先级排序
    逐个执行 task
      如果是 lister_task, 追加新的 tasks, 并添加到优先级列表的头部
      如果是 page_task, 按需抓取
    每完成一个 batch (比如 10 个更新) 之后, 记录到文件 task.yaml
    git commit 到上一层的仓库
    生成 RSS Feed
    输出一个报告
  '''

  def __init__(self, watcher_path):
    self.watcher_path = watcher_path
    # task_option 该文件夹下默认属性 只读取不修改
    config_data = self.load_config_yaml()
    self.default_option = config_data.get('default_option', {})
    self.default_option.update({'folder': self.watcher_path})  # 将项目 folder 也放在公共属性

    self.tasks = []
    self.url_set = set()
    self.add_tasks(tasks=config_data.get('lister_task') or []) # 从 .task.yaml 里载入 "tasks:" 的所有内容
    self.add_tasks(tasks=config_data.get('page_task') or []) # 从 .task.yaml 里载入 "tasks:" 的所有内容


  def __str__(self):
    s = '''<Watcher #{}> from {}
    have {} tasks
    '''
    return s.format(id(self), self.tasks_count, self.watcher_path)


  def load_config_yaml(self):
    config_yaml = self.watcher_path + '/.task.yaml'
    if not os.path.exists(config_yaml):
      raise ValueError('{config_yaml} not found'.format(**locals()))
    config_data = tools.yaml_load(config_yaml)
    log(f'config `{config_yaml}` loaded: ')
    lister_default_option = dict(config_data['default_option']['lister'])
    page_default_option = dict(config_data['default_option']['page'])
    log(f'  lister default option: {lister_default_option}')
    log(f'  page default option: {page_default_option}')

    lister_tasks = config_data.get('lister_task') or []
    page_tasks = config_data.get('page_task') or []
    log(f'  found {len(lister_tasks)} lister tasks in config:')
    for task in lister_tasks:
      tip = task['tip']
      log(f'    lister_task: {tip}')
    log(f'  found {len(page_tasks)} page tasks in config:')
    for i, task in enumerate(page_tasks):
      tip = task['tip']
      log(f'    page_task: {tip}')
      if i > 5:
        log(f'    ......')
        break
    log()
    return config_data



  def add_task(self, task):
    ''' 添加一个 Task, 以 url 判断是否为已存在的 Task
        返回 task 属于四种情况的数量
          new        当前未知的新任务, 
          seen       当前任务列表中已存在的任务 (url 已知)
          prepare    任务已到抓取时间, 等待抓取
          wait       任务不到抓取时间
        '''
    if isinstance(task, dict):
      # 将 dict 型转为 Task 实例
      # task_desc 单独一个 task 的配置, 只需要记录与公共属性不同的字段
      task_desc = task
      task = Task.create(task_desc, self.default_option)
    seen_task = self.find_task(task)
    if seen_task:
      if seen_task.next_watch_time <= time_now():
        return "seen+prepare"
      else:
        return "seen+wait"
    else:
      self.tasks.append(task)
      self.url_set.add(task.url)
      if task.next_watch_time <= time_now():
        return "new+prepare"
      else:
        return "new+wait"


  def add_tasks(self, tasks):
    ''' 添加任务列表, 并输出报告
        在 watcher 加载 config yaml 时调用, 以及 lister 检测到 new page 时调用

        输出报告 task 属于四种情况的数量
          new        当前未知的新任务, 
          seen       当前任务列表中已存在的任务 (url 已知)
          prepare    任务已到抓取时间, 等待抓取
          wait       任务不到抓取时间

    '''
    results = []
    for task in tasks:
      result = self.add_task(task)
      results.append(result)
    log(f'watcher add {len(tasks)} tasks: {dict(Counter(results))}')
    return Counter(results)

  def find_task(self, other_task):
    if other_task.url in self.url_set:
      for task in self.tasks:
        if other_task.url == task.url:
          return task
    return None

  @property
  def tasks_count(self):
    return len(self.tasks)

  def save_config_yaml(self):
    ''' 存盘 .task.yaml
        首先存公共 config
        其次存 NewPost 类 tasks
        最后存普通 tasks

    '''
    config_yaml = self.watcher_path + '/.task.yaml'
    # default_option 不会改变 只有 lister_task 和 page_task 被更新
    temp = tools.load_txt(config_yaml).split('lister_task:')[0]  # 取得 default 部分
    temp += 'lister_task:\n'
    for task in self.tasks:
      if task.is_lister_type:
        temp += task.to_yaml_text()
        temp += '\n'
    temp += '\n\n\npage_task:\n'
    for task in self.tasks:
      if task.is_page_type:
        temp += task.to_yaml_text()
        temp += '\n'
    tools.save_txt(path=config_yaml, data=temp)
    log('done, save_config_yaml "{config_yaml}" done'.format(**locals()))


  def status(self):
    log('Watcher: tasks {}'.format(len(self.tasks)))


  def watch(self):
    ''' 爬取页面, 
        首先列出所有的NewPost任务, 都抓取一遍
        然后列出普通页面任务, 都抓取一遍
        在成功抓取后更新 RSS
    '''
    lister_tasks_queue = []
    for task in self.tasks:
      if task.should_fetch and task.is_lister_type:
        lister_tasks_queue.append(task)
    lister_tasks_queue.sort(key=lambda x: -x.priority)
    log(f'start watching listers... \n should fetch {len(lister_tasks_queue)} lister tasks\n')
    for i, task in enumerate(lister_tasks_queue, 1):
      # log('Watcher.watch lister task.run: {}'.format(task))
      new_tasks_json = task.run()
      counter = self.add_tasks(new_tasks_json)
      is_modified = counter["new+prepare"] > 0 or counter["new+wait"] > 0
      task.schedule(is_modified=is_modified) # is_modified = add_tasks 时出现了新的 task
      log(f'lister task done ({i}/{len(lister_tasks_queue)}): \n{task}\n\n')
      self.save_config_yaml()
      yield {'commit_log': f'yield checked lister {i}'}
      # remember(commit_log='checked lister {}'.format(i), watcher_path=self.watcher_path)
      tools.time_random_sleep(5, 10)




    page_tasks_queue = []
    for task in self.tasks:
      if task.should_fetch and task.is_page_type:
        page_tasks_queue.append(task)
    page_tasks_queue.sort(key=lambda x: -x.priority)
    log('start watching pages... \n should fetch {} page tasks\n'.format(len(page_tasks_queue)))
    for i, task in enumerate(page_tasks_queue, 1):
      # log('Watcher.watch page task: {}'.format(task))
      page_json = task.run()
      is_modified = task.save(page_json)
      task.schedule(is_modified=is_modified)  # is_modified = 跟上次存储的页面有区别
      log(f'page task done ({i}/{len(page_tasks_queue)}): \n{task}\n\n')
      self.save_config_yaml()
      if i % 3 == 0:
        yield {'commit_log': f'yield save pages {i}'}
        # remember(commit_log='save pages {}'.format(i), watcher_path=self.watcher_path)
        # generate_feed(self.watcher_path, )
      tools.time_random_sleep(5, 10)
    else:
      self.save_config_yaml()
      yield {'commit_log': f'yield save pages remain'}
      # remember(commit_log='save pages {}'.format('remain'), watcher_path=self.watcher_path)
      # generate_feed(self.watcher_path, )
    
