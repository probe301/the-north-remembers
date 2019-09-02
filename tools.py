
import time
import os
import shutil
import re
from enum import Enum
from datetime import datetime
import time
import arrow
import json
import random
# data = json.loads(open('mockup_topic_answers.json', encoding='utf-8').read())

import sys

UrlType = Enum('UrlType', 
                ('ZhihuAnswerPage', 
                 'ZhihuAnswerLister',   
                 'ZhihuColumnPage',     # 用于抓取专栏文章
                 'ZhihuColumnLister',   # 用于监视专栏新文章
                 'ZhihuAuthor', 
                 'ZhihuQuestionPage',   # 用于抓取问题描述
                 'ZhihuQuestionLister', # 问题页, 用于监视新增回答
                 'WeixinAricle',
                 'WeixinAricleLister')
               )





def parse_type(url):
  if re.search(r'https://zhuanlan.zhihu.com/p/\d+?', url):
    return UrlType.ZhihuColumnPage
  if re.search(r'https://zhuanlan.zhihu.com/\w+?', url):
    return UrlType.ZhihuColumnLister

  if re.search(r'https://www.zhihu.com/question/\d+?/answer/\d+?', url):
    return UrlType.ZhihuAnswerPage
  if re.search(r'https://www.zhihu.com/people/(\w|\-)+?/answers', url):
    return UrlType.ZhihuAnswerLister  # from author's answers
  if re.search(r'https://www.zhihu.com/topic/\d+/(top\-answers|hot|intro)?/?', url):
    return UrlType.ZhihuAnswerLister  # from topic's answers 1
  if re.search(r'https://www.zhihu.com/collection/\d+', url):
    return UrlType.ZhihuAnswerLister  # from collection's answers
  if re.search(r'https://www.zhihu.com/question/\d+', url):
    return UrlType.ZhihuAnswerLister  # from question's answers

  if 'weixin' in url:
    return UrlType.WeixinAricle

  raise ValueError('cannot reg tasktype of url {}'.format(url))



def purge_url(url):
  url = url.strip()
  if url.endswith('/'):
    url = url[:-1]
  url = url.replace('//zhihu.com/', '//www.zhihu.com/')

  if 'www.zhihu.com' in url:
    url = url.split('?')[0]  # 不需要 query=? 参数
    url = url.replace('http://', 'https://')

  return url


def generate_zhihu_token():
  import os
  from zhihu_oauth import ZhihuClient

  # 'p.....@' '42'

  TOKEN_FILE = 'token.pkl'
  client = ZhihuClient()
  if os.path.isfile(TOKEN_FILE):
      client.load_token(TOKEN_FILE)
  else:
      client.login_in_terminal(use_getpass=False)
      client.save_token(TOKEN_FILE)



def time_from_stamp(s):
  return arrow.get(s) # s in (float, str)
def time_from_str(s, zone='+08:00'):
  return arrow.get(s+zone, "YYYY-MM-DD HH:mm:ssZZ")
def time_now():
  return arrow.now()
def time_now_stamp():
  return arrow.now().timestamp
def time_now_str():
  return arrow.now().format("YYYY-MM-DD HH:mm:ss")
def time_to_stamp(t):
  return t.timestamp
def time_to_str(t):
  return t.format("YYYY-MM-DD HH:mm:ss")
def time_to_humanize(t):
  return t.humanize()

def time_delta_from_now(t):
  ''' t 落后于当前时间时, 返回秒数为正数 '''
  delta = time_now() - t
  seconds = delta.days * 24 * 3600 + delta.seconds
  return seconds


def time_shift_from_humanize(t, shift_expr):
  ''' 返回 t 变动了 shift_expr 后的时刻
      shift_expr 只接受 秒 分 时 和 天
      like: 3days, -3day, 20min, +20mins, 1seconds'''
  pat = r'^(\+?\-?\d+) ?(second|seconds|minute|minutes|hour|hours|day|days)$'
  m = re.match(pat , shift_expr)
  if not m:
    raise ValueError('time_shift cannot parse shift_expr: {shift_expr}'.format(**locals()))
  kargs = dict()
  unit = m.group(2) if m.group(2)[-1] == 's' else m.group(2)+'s' # 必须是 days=1, 不是 day=1
  kargs[unit] = int(m.group(1))
  return t.shift(**kargs)
  # t.shift(weeks=-1)
  # t.shift(months=-2)
  # t.shift(years=1)


def duration_from_humanize(expr):
  ''' 返回 expr 语义中的 diff 秒数
      expr 只接受 秒 分 时 和 天'''
  pat = r'^(\+?\-?\d+) ?(second|seconds|minute|minutes|hour|hours|day|days)$'
  m = re.match(pat, expr)
  if not m:
    raise ValueError(
        'duration_from_humanize cannot parse duration expr: {expr}'.format(**locals()))
  kargs = dict()
  unit = m.group(2) if m.group(2)[-1] == 's' else m.group(2)+'s'
  kargs[unit] = int(m.group(1))
  diff = arrow.now().shift(**kargs) - arrow.now()
  return diff.days * 24 * 3600 + diff.seconds





def time_random_sleep(min, max=None):
  '''休眠指定的时间,或范围内的随机值'''
  if max is None:
    return time.sleep(float(min))
  else:
    t = random.uniform(float(min), float(max))
    return time.sleep(t)



def convert_time(d, humanize=False):
  if not d:
    return None
  if isinstance(d, int):
    d = datetime.utcfromtimestamp(d)
  if humanize:
    return arrow.get(d.strftime('%Y-%m-%d %H:%M:%S') + '+08:00').humanize()
  else:
    return d.strftime('%Y-%m-%d %H:%M:%S')


import fnmatch
def all_files(root, patterns='*', 
              blacklist=('.git', '__pycache__', '.ipynb_checkpoints'), 
              single_level=False, yield_folders=False):
  ''' 取得文件夹下所有文件
  single_level 仅处理 root 中的文件(文件夹) 不处理下层文件夹
  yield_folders 也遍历文件夹'''

  patterns = patterns.split(';')
  for path, subdirs, files in os.walk(root, topdown=True):
    subdirs[:] = [d for d in subdirs if d not in blacklist]
    subdirs.sort()
    if yield_folders:
      files.extend(subdirs)
    files.sort()
    for name in files:
      for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
          yield os.path.join(path, name)
          break
    if single_level:
      break

import fnmatch
def all_subdirs(root, patterns='*', 
                blacklist=('.git', '__pycache__', '.ipynb_checkpoints'), 
                single_level=False):
  ''' 取得文件夹下所有文件夹 '''

  patterns = patterns.split(';')
  for path, subdirs, __ in os.walk(root, topdown=True):
    subdirs[:] = [d for d in subdirs if d not in blacklist]
    subdirs.sort()
    for name in subdirs:
      for pattern in patterns:
        if fnmatch.fnmatch(name, pattern):
          yield os.path.join(path, name)
          break
    if single_level:
      break

# When `topdown` is true, the caller can modify the dirnames 
# list in-place and walk will only recurse into the subdirectories 
# whose names remain in dirnames; can be used to prune the search...
# `dirs[:] = value` modifies dirs in-place. It changes the contents 
# of the list dirs without changing the container. 





def datalines(data, sample=None):
  '''返回一段文字中有效的行(非空行, 且不以注释符号开头)'''
  ret = []
  for l in data.splitlines():
    line = l.strip()
    if line and not line.startswith('#'):
      ret.append(line)
  if sample:
    return ret[:sample]
  else:
    return ret




def encode_open(filename):
  '''读取文本, 依次尝试不同的解码'''
  try:
    open(filename, 'r', encoding='utf-8').read()
    encoding = 'utf-8'
  except UnicodeDecodeError:
    encoding = 'gbk'
  return open(filename, 'r', encoding=encoding)



import yaml
from collections import OrderedDict

class IncludeOrderedLoader(yaml.Loader):
  ''' yaml loader
      以有序 dict 替代默认 dict
      值为 !include 开头时, 嵌套另一个 yaml
      !include 可以是绝对路径或相对路径
      如果嵌套太深, 可能遇到相对路径错乱的问题
  '''

  def __init__(self, stream):
    super(IncludeOrderedLoader, self).__init__(stream)
    self.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                         self._construct_mapping)
    self.add_constructor('!include', self._include)
    self._root = os.path.split(stream.name)[0]

  def _include(self, loader, node):
    filename = os.path.join(self._root, self.construct_scalar(node))
    return yaml.load(encode_open(filename), IncludeOrderedLoader)

  def _construct_mapping(self, loader, node):
    loader.flatten_mapping(node)
    return OrderedDict(loader.construct_pairs(node))


def yaml_load(path, loader=IncludeOrderedLoader):
  ''' 按照有序字典载入yaml 支持 !include
  '''
  return yaml.load(open(path, encoding='utf-8'), loader)



def yaml_save(data, path):
  '''支持中文, 可以识别 OrderedDict'''
  class OrderedDumper(yaml.SafeDumper):
    pass
  def _dict_representer(dumper, data):
    return dumper.represent_mapping(
              yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
              data.items()
            )
  with open(path, 'w', encoding='utf-8') as file:
    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    yaml.dump(data, file, OrderedDumper, allow_unicode=True)
  return True

def yaml_loads(text, loader=IncludeOrderedLoader):
  try:
    from StringIO import StringIO
  except ImportError:
    from io import StringIO
  fd = StringIO(text)
  fd.name = 'tempyamltext'
  return yaml.load(fd, loader)

def yaml_saves(data):
  return yaml.safe_dump(data, allow_unicode=True)



def load_txt(path, encoding='utf-8'):
  with open(path, 'r', encoding=encoding) as f:
    ret = f.read()
  return ret


def save_txt(path, data, encoding='utf-8'):
  with open(path, 'w', encoding=encoding) as f:
    f.write(data)
  return True


def sections(iterable, is_title=lambda line: line.startswith('#')):
  ''' 通过小节的标题和之后文字生成 {标题: 内容} 的 order dict
  '''
  result = OrderedDict()
  title_index = 0
  title = (title_index, 'DEFAULT HEADER')
  result.setdefault(title, [])
  for line in iterable:
    if is_title(line):
      title_index += 1
      title = (title_index, line)
      result.setdefault(title, [])
    else:
      result[title].append(line)
  return result



def truncate(text, limit=20, with_end=False, ellipsis='... ', encode=None):
  ''' 截断字符串尾部, 保留指定长度
      encode='gbk' 计算长度时, 中文字符视为长度2, 这样方便对齐
      encode='utf8' 计算长度时, 中文字符视为长度3
      encode=None 使用普通的 len(text) 计算长度
      with_end=True 保留开头和结束, 省略中间的字符 TODO
  '''
  encode_len = lambda t: len(t.encode(encode) if encode else t)
  limit = max(limit, encode_len(ellipsis))
  len_text = encode_len(text)
  if len_text <= limit:
    return text
  else:
    while encode_len(text[:len_text]) > limit - encode_len(ellipsis):
      len_text -= 1
    return text[:len_text] + ellipsis




from pprint import pprint
from datetime import datetime
# import inspect
class create_logger:
  def __init__(self, file_path):
    self.filepath = file_path + '.log'

  def custom_print(self, data, prefix='', filepath=None, pretty=False):
    out = open(filepath, 'a', encoding='utf-8') if filepath else sys.stdout
    if filepath:  # 在输出到文件时增加记录时间戳, 输出到 stdout 不记录时间戳
      prefix = '[' + datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + ']' + prefix

    if prefix:
      print(prefix, file=out, end=' ')
    if pretty:
      pprint(data, stream=out, width=80, compact=True, depth=2)
    else:
      print(data, file=out)
    # if filepath:
    #   out.close()


  def output(self, values, pretty=False):

    if len(values) == 1:
      s = values[0]
    else:
      s = ', '.join(str(v) for v in values)
    try:
      self.custom_print(s, filepath=None, pretty=pretty)
    except UnicodeEncodeError as e:
      self.custom_print(str(e), prefix='logger output error: ')
    try:
      self.custom_print(s, filepath=self.filepath, pretty=pretty)
    except UnicodeEncodeError as e:
      self.custom_print(str(e), filepath=self.filepath, prefix='logger output error: ')

  def __ror__(self, *other):
    self.output(other, pretty=True)
    return other

  def __call__(self, *other, pretty=False):
    self.output(other, pretty=pretty)





DEFAULT_INVALID_CHARS = {':', '*', '?', '"', "'", '<', '>', '|', '\r', '\n', '\t'}
EXTRA_CHAR_FOR_FILENAME = {'/', '\\'}

def remove_invalid_char(dirty, invalid_chars=None, for_path=False):
    if invalid_chars is None:
        invalid_chars = set(DEFAULT_INVALID_CHARS)
    else:
        invalid_chars = set(invalid_chars)
        invalid_chars.update(DEFAULT_INVALID_CHARS)
    if not for_path:
        invalid_chars.update(EXTRA_CHAR_FOR_FILENAME)

    return ''.join([c for c in dirty if c not in invalid_chars]).strip()


class Null:
  def __init__(self, *args, **kwargs):
    "忽略参数"
    return None
  def __call__(self, *args, **kwargs):
    "忽略实例调用"
    return self
  def __getattr__(self, mname):
    "忽略属性获得"
    return self
  def __setattr__(self, name, value):
    "忽略设置属性操作"
    return self
  def __delattr__(self, name):
    '''忽略删除属性操作'''
    return self
  def __repr__(self):
    return "<Null>"
  def __str__(self):
    return "Null"


from difflib import unified_diff
def compare_text(t1, t2, prefix=''):
  changes = [l for l in unified_diff(t1.split('\n'), t2.split('\n'))]
  for change in changes:
    print(prefix + change)
  return changes

def split_text(text):
  col = []
  for sent in re.findall('.*?[！|，|。|？|\n|；|~|～|：|\)|\]]', text):
    col.append(sent)
  return col

def display_compare_text(contents):
  for i, (a, b) in enumerate(zip(contents[:-1], contents[1:])):
    # if i == 0: continue
    if (a!=b):
      print('a!=b on', i, i+1)
      for d in unified_diff(split_text(a), split_text(b), n=2, lineterm=''):
        print(d)
    print('\n\n\n\n\n\n')
  #   if i >= 5:
  #     break


def generate_ascii_title(text):
  from pyfiglet import Figlet
  f = Figlet()
  fonts = ['ogre', '6x10', 'space_op', 'o8',]
  for font in fonts:
    f.setFont(font=font)
    print(f.renderText(text=text.strip()))
# generate_ascii_title('common import')


def enumer(iterable, first=None, skip=0):
  ''' 迭代开头的 n 个元素, 顺便 yield 元素的索引
      enumfirst('abcdefg')            => 0a 1b 2c 3d 4e 5f 6g
      enumfirst('abcdefg', first=4)   => 0a 1b 2c 3d
      enumfirst('abcdefg', skip=2)    => 2c 3d 4e 5f 6g
      enumfirst('abcdefg', first=3, skip=2) => 2c 3d 4e
  '''
  for i, item in enumerate(iterable):
    if skip != 0 and i < skip:
      continue
    if first is not None and i >= first+skip:
      break
    else:
      yield i, item


from copy import deepcopy
def dict_merge(a, b=None):
  a = deepcopy(a)
  if b is None:
    b = {}
  a.update(b)
  return a



def is_windows():
  import sys
  return sys.platform == 'win32'


import subprocess
def run_command(cmd, verbose=False):
  if verbose: print('> running: ', cmd)
  try:
    output = subprocess.check_output(
        cmd, stderr=subprocess.STDOUT, shell=True, timeout=3,
        universal_newlines=True)
  except subprocess.CalledProcessError as exc:
    if verbose: print("status: FAIL", exc.returncode, exc.output)
    raise RuntimeError(f'status: FAIL, {exc.returncode}, {exc.output}')
  else:
    if verbose: print("output: \n{}\n".format(output))
    return output


# import time
# # import sys
# import os
# # import shutil
# # import re
# from pylon import puts
# from pylon import form
# from pylon import datalines
# from pylon import create_logger
# log = create_logger(__file__)
# log_error = create_logger(__file__ + '.error')

# # from pylon import enumrange

# from zhihu_answer import yield_topic_best_answers
# from zhihu_answer import yield_author_answers
# from zhihu_answer import yield_author_articles
# from zhihu_answer import yield_column_articles
# from zhihu_answer import fetch_zhihu_answer
# from zhihu_answer import fetch_zhihu_article
# from zhihu_answer import fill_full_content
# from zhihu_answer import zhihu_answer_url
# from zhihu_answer import zhihu_article_url
# from zhihu_answer import fetch_images_for_markdown
# from zhihu_answer import ZhihuParseError
# # import requests
# from zhihu_oauth.zhcls.utils import remove_invalid_char


# # from jinja2 import Template
# db = SqliteDatabase('zhihu.sqlite')

# from tools import *

# # def exec_create_db():
# #   'regenate sqlite db' | puts()
# #   db.connect()
# #   db.create_tables([Task, Page])
# #   db.close()
