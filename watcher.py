

import os
import tools
from tools import PageType
from tools import parse_type
from tools import create_logger
from tools import time_to_str
from tools import duration_from_humanize
from tools import time_now
from tools import time_now_str
from tools import time_from_str
from tools import time_to_humanize


log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')


from fetcher.zhihu_answer import fetch_zhihu_answer
from fetcher.zhihu_answer import zhihu_article_url
from fetcher.zhihu_answer import yield_column_articles
from fetcher.zhihu_answer import save_article

from collections import OrderedDict
from collections import Counter







class Task:
  '''
  任务, 分为发现新Page, 和抓取Page变化两种


  一个 .task.yaml 下所有Task的公共属性
    folder
    enabled
    min_cycle
    max_cycle
    weight

  单独一个Task的属性 (可以覆盖掉公共属性)
    url: http://xxxx
    tip: xxxx
    version: 12
    watch_time: {task_add_time: xx, last_watch_time: xx, next_watch_time: xx}
    filename: xxxx

  发现新Page任务可以自定义的属性
    title_contains: filter_keyword
    zhihu_upvote: '>=500'


  抓取Page可以自定义的属性
    pass


  url - url处理干净作为 pk

  '''

  fields = ['url', 'folder', 'tip', 'enabled', 
            'task_add_time', 'last_watch_time', 'last_change_time', 'next_watch_time',
            'weight', 'version', 
            'min_cycle', 'max_cycle']


  @classmethod
  def create(cls, desc, option):
    '''从 json description 创建 Task'''
    page_type = parse_type(desc['url'])
    if page_type == PageType.ZhihuColumnPage:
      return ZhihuColumnPageTask(desc, option)
    elif page_type == PageType.ZhihuColumnIndex:
      return ZhihuColumnIndexTask(desc, option)
    else:
      log(page_type, '?')
      raise ValueError(
          'Task.create: cannot reg task type {}'.format(desc['url']))
  
  def __init__(self, desc, option):
    self.option = option
    # TODO merge desc + option
    self.url = desc['url']
    self.enabled = bool(desc.get('enabled') or True)
    self.tip = str(desc.get('tip') or 'TIP')

    # 任务添加时间
    self.task_add_time = self.parse_time(desc, 'task_add')
    # 上次抓取的时间
    self.last_watch_time = self.parse_time(desc, 'last_watch')
    # 上次内容变动的时间, 不同的页面有不同的判定标准, 比如评论和点赞数不算变动, 内容修改肯定算变动
    self.last_change_time = self.parse_time(desc, 'last_change')
    # 安排的下次采集时间, 可以手动修改, 立即触发一次采集
    self.next_watch_time = self.parse_time(desc, 'next_watch') 

    self.weight = float(desc.get('weight') or 0.5)
    self.once = bool(desc.get('once') or False)
    self.version = int(desc.get('version') or 0)
    self.min_cycle = str(desc.get('min_cycle') or self.option.get('min_cycle') or '3minutes')  # TODO parse cycle time
    self.max_cycle = str(desc.get('max_cycle') or self.option.get('max_cycle') or '1day')
    self.lazy_ratio = int(desc.get('lazy_ratio') or self.option.get('lazy_ratio') or 1)

  def parse_time(self, desc, time_label):
    # log('prepare parse time: {desc} {time_label}'.format(**locals()))
    # 从 desc['timestamp'] 里读配置, 整理到 arrow.time 类型
    if time_label in ('task_add', 'next_watch'):
      # 这两个如果缺省, 设为当前时间
      if not desc.get('timestamp'): 
        return time_now()
      else: 
        return time_from_str(desc.get('timestamp').get(time_label, time_now_str()))
    else:
      # 这两个 last_watch_time last_change_time 如果缺省, 不做设置
      if not desc.get('timestamp'): 
        return None
      timestr = desc.get('timestamp').get(time_label, None)
      if timestr:
        return time_from_str(timestr)
      else:
        return None
#

  def __str__(self):
    s = '''<Task url={0.url}> (version {0.version})
    {0.tip}
    task add: ({1}) last watch: ({2}) last change ({3}) next watch: ({4}) '''
    return s.format(self, 
                    time_to_humanize(self.task_add_time),
                    self.last_watch_time and time_to_humanize(self.last_watch_time),
                    self.last_change_time and time_to_humanize(self.last_change_time),
                    time_to_humanize(self.next_watch_time),
                    )


  def to_yaml_text(self):
    ''' 将 task 存为 yaml 文本片段
        因为需要节省行数, 自定义格式化方案'''
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

    for field in Task.fields:
      if field in ('folder', 'url', 'tip'):
        continue
      if field in self.option and getattr(self, field) == self.option.get(field):
        continue
      if field.endswith('_time'):
        continue
      result.append('    {}: {}'.format(field, str(getattr(self, field))))

    return '\n'.join(result)

  def update_timestamp(self, other):
    self.next_watch_time = time_now()


  def fetch(self):
    log('will fetch: {}'.format(str(self)))


  def save(self, data=None, diff=None):
    ''' 如果成功存储, 则更新 version, last_watch_time, next_watch_time, tip
        根据上次是否变化, 安排下一次的抓取日程

        lazy_ratio: 抓取后如果发现内容自从历史 `A` 时起就没变过, 
                    则将下次抓取时间设为 `(now-A) * lazy_ratio`
                    理想状态下, 文章内容不变, 每次抓取间隔就以指数增长
                    如果某次抓取后发现内容改变, 则恢复为 min_cycle 的时间
                    lazy_ratio 默认设为1, 意味着按照2的幂次延迟下一次的抓取时间
                    当认为内容不会总变化时, lazy_ratio 可以乐观设置为 10, 每次延长10倍的时间, 更省资源
                    当认为内容总变时, 比如Index型的任务, lazy_ratio 可以悲观设置可以为 0, 这样将采用 min_cycle

        min_cycle 下次抓取至少需要间隔的时间 (3分钟)
        max_cycle 下次抓取最多可以间隔的时间 (60天)
        以lazy_ratio计算出的时间要限制到 {min_cycle, max_cycle} 范围内
        
    '''
    # 更新 last_change_time, next_watch_time
    # 首先检测这次跟上次相比, 抓取到的内容是否已经改变
    if not self.last_change_time or self.content_is_changed:  # 没有上次, 或者这次相比上次有改变
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
    log('save task: {}'.format(str(self)))




  @property
  def priority(self):
    ''' 优先级从 weight 和 task_add_time next_watch_time last_watch_time 综合得出
        如果 weight == 1, task_add_time 最靠后的排在前面
        如果 weight < 1, last_watch_time 为 None 的排在前面, 然后是
        如果 weight < 1, 且已经有了 last_watch_time, 按照 next_watch_time 排列
    '''
    if self.weight >= 1:
      pass
    return 1

  @property
  def is_index_type(self):
    return str(parse_type(self.url)).endswith('Index')

  @property
  def is_page_type(self):
    return str(parse_type(self.url)).endswith('Page')

  @property
  def should_fetch(self):
    return self.enabled and self.next_watch_time <= time_now().shift(seconds=1)



  @property
  def content_is_changed(self):
    # TODO IMPL
    return True


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

  def remember(self):
    # save to git
    pass



  # def to_local_file(self, folder, file_name=None,
  #                   fetch_images=True, overwrite=False):
  #   if not file_name:
  #     file_name = self.title
  #   if not os.path.exists(folder):
  #     os.makedirs(folder)

  #   save_path = folder + '/' + remove_invalid_char(file_name) + '.md'
  #   if not overwrite:
  #     if os.path.exists(save_path):
  #       log('already exist {}'.format(save_path))
  #       return save_path

  #   rendered = self.full_content

  #   with open(save_path, 'w', encoding='utf-8') as f:
  #     f.write(rendered)
  #     log('write {} done'.format(save_path))

  #   if fetch_images:
  #     # 本地存储, 需要抓取所有附图
  #     fetch_images_for_markdown(save_path)
  #   return save_path


# ================= end of class Task =================







class ZhihuAnswerTask(Task):
  pass





class ZhihuColumnPageTask(Task):
  '''抓取Zhihu专栏的一篇文章
  自有属性:
  '''
  def fetch(self):
    log('ZhihuColumnPageTask fetching...')
    save_article(self.url, folder=self.option['folder'])
  # def save(self):
  #   super()

  # def watch(self):
  #   if self.page_type == 'zhihu_answer':
  #     try:
  #       zhihu_answer = fetch_zhihu_answer(self.url)
  #       page = self.remember(zhihu_answer)
  #       return page
  #     except ZhihuParseError as e:
  #       blank_answer = e.value
  #       log_error('!! 问题已删除 {} {}'.format(self.url, blank_answer['title']))
  #       page = self.remember(blank_answer)
  #       return page
  #     except RuntimeError as e:
  #       log_error(e)
  #       raise
  #   elif self.page_type == 'zhihu_article':
  #     try:
  #       zhihu_article = fetch_zhihu_article(self.url)
  #       page = self.remember(zhihu_article)
  #       return page
  #     except ZhihuParseError as e:
  #       blank_article = e.value
  #       log_error('!! 文章已删除 {} {}'.format(self.url, blank_article['title']))
  #       page = self.remember(blank_article)
  #       return page
  #   else:
  #     raise



class ZhihuColumnIndexTask(Task):
  ''' 以Zhihu专栏ID获取所有文章
      option 继承自该 task 自身属性
      
      过滤属性
      
      limit: 最多返回 n 个 task
      min_voteup: 赞同数超过 n'''
  def fetch(self):
    tasks = []
    column_id = self.url.split('/')[-1]

    # TODO reg limit
    for article in yield_column_articles(column_id, limit=5, min_voteup=20):
      desc = {'url': zhihu_article_url(article),
              'tip': article.title + ' - ' + article.author.name, 
              }
      log('extract new task {}'.format(desc))
      task = Task.create(desc, self.option)
      tasks.append(task)
    return tasks

  # def save(self):
  #   super()





# class ZhihuDetectNewAnswerTask(Task):
#   pass

























class Watcher:
  '''
  任务调度, 维护任务队列, 执行抓取任务
  每个 Watcher 实例加载一个 ".task.yaml"
  ".task.yaml" 分为 default_option 和 tasks 两部分设置
  default_option 存放公用设置
  tasks 部分是具体任务属性, 可以覆盖 default_option 的设置
  tasks 里的任务按照优先度排序, 依次执行
    如果是 FetchNewPost 任务, 会添加新的页面到 tasks 里
    如果是普通任务, 会更新一次页面

  执行条件包括:
      手动触发
      达到特定时间

  当 watcher.init() 时做这些:
      加载 task.yaml, 分析设置, 创建所有的 tasks
      输出一个报告

  当 watcher.watch() 时做这些:
      找出需要执行的 tasks, 对这些 tasks 按照优先级排序
      逐个执行 task
        如果是 IndexTask, 追加新的 tasks, 并添加到优先级列表的头部
        如果是 PageTask, 按需抓取
      每完成一个 batch (比如10个更新) 之后, 记录到文件 task.yaml
      git commit
      输出一个报告
  '''

  def __init__(self, project_path):
    self.project_path = project_path
    # task_option 该文件夹下公共属性
    config_data = self.load_config_yaml()
    self.task_option = config_data.get('default_option', {})
    self.task_option.update({'folder': self.project_path})  # 将项目 folder 也放在公共属性

    self.tasks = []
    self.url_set = set()
    self.add_tasks(tasks=config_data.get('tasks', [])) # 从 .task.yaml 里载入 "tasks:" 的所有内容




  def load_config_yaml(self):
    config_yaml = self.project_path + '/.task.yaml'
    if not os.path.exists(config_yaml):
      raise ValueError('{config_yaml} not found'.format(**locals()))
    config_data = tools.yaml_load(config_yaml)
    log('loaded config_data option: ')
    log(dict(config_data.get('default_option')), pretty=True)
    log('loaded config_data tasks {}'.format(len(config_data.get('tasks', []))))
    return config_data



  def add_task(self, task):
    if isinstance(task, dict):
      # 将 dict 型转为 Task 实例
      # task_desc 单独一个 task 的配置, 只需要记录与公共属性不同的字段
      task_desc = task
      task = Task.create(task_desc, self.task_option)
    seen_task = self.find_task(task)
    if seen_task:
      # TODO 需要处理时间顺序, nextwatch < now() 时, 应该保留不动, 提高权重, 不应该把时间更新到 now()
      seen_task.update_timestamp(task)
      return "updated"
      # return "dropped"
    else:
      self.tasks.append(task)
      self.url_set.add(task.url)
      return "added"
    return

  def add_tasks(self, tasks):
    '''添加任务列表, 并输出报告'''
    results = []
    for task in tasks:
      result = self.add_task(task)
      results.append(result)
    log('Watcher.add_tasks result: ', Counter(results))

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
        最后存普通 tasks'''
    config_yaml = self.project_path + '/.task.yaml'
    data = tools.yaml_load(config_yaml)
    # data.option 不会改变
    # 只有 data.tasks 被更新
    temp = tools.yaml_saves({'default_option': dict(data['default_option'])})
    temp += '\n\n\n'
    temp += 'tasks:\n'
    for task in self.tasks:
      temp += task.to_yaml_text()
      temp += '\n'
    tools.save_txt(path=config_yaml, data=temp)
    log('save_config_yaml "{config_yaml}" done'.format(**locals()))


  def status(self):
    log('Watcher: tasks {}'.format(len(self.tasks)))


  def watch(self):
    ''' 爬取页面, 
        首先列出所有的NewPost任务, 都抓取一遍
        然后列出普通页面任务, 都抓取一遍
    '''
    temp_queue = []
    for task in self.tasks:
      if task.should_fetch and task.is_index_type:
        temp_queue.append(task)
    temp_queue.sort(key=lambda x: -x.priority)
    for task in temp_queue:
      log('Watcher.watch index task: {}'.format(task))
      new_tasks = task.fetch()
      self.add_tasks(new_tasks)
      task.save()
      log('Watcher.watch index task done: {}\n\n'.format(task))

    temp_queue = []
    for task in self.tasks:
      if task.should_fetch and task.is_page_type:
        temp_queue.append(task)
    temp_queue.sort(key=lambda x: -x.priority)
    for task in temp_queue:
      log('Watcher.watch page task: {}'.format(task))
      task.fetch()
      task.save()
      tools.time_random_sleep(1, 5)
      log('Watcher.watch page task done: {}\n\n'.format(task))

    self.save_config_yaml()


    






  # TODO remix
  # 
  # def fetch(self):
  #   existed = self.select().where(self.url == url)
  #   if existed:
  #     task = existed.get()
  #     log('Task.add has already existed: {}'.format(task))
  #     task.next_watch = datetime.now()
  #     # task.not_modified = 0
  #     task.save()
  #   else:
  #     task = self.create(url=url,
  #                        page_type=page_type,
  #                        title=title or '(has not fetched)',
  #                        next_watch=datetime.now())
  #     log('new Task added: {}'.format(task))


  # @classmethod
  # def multiple_watch(cls, sleep_seconds=10, limit=10):
  #   count = Task.report()
  #   if count == 0:
  #     log('current no tasks')
  #     return

  #   limit = min(limit, count)
  #   for i in range(1, limit+1):
  #     now = datetime.now()
  #     log('\nloop {}/{} current_time={}'.format(i, limit, convert_time(now)))
  #     task = Task.select().order_by(Task.next_watch).get()
  #     if not task:
  #       log('can not find any task')
  #       continue
  #     elif task.next_watch <= now:
  #       log('start: {}'.format(task))
  #       page = task.watch()
  #       next_time = convert_time(task.next_watch, humanize=True)
  #       log('done!  {} (next watch: {})'.format(page, next_time))
  #       time.sleep(sleep_seconds)
  #     else:
  #       log('not today... {}'.format(task))

