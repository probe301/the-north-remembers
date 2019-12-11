
import time
import os
import shutil
import re
from datetime import datetime
import time
import arrow
import json
import random
import html2text

import sys

# 2019-12-03T18:35:35.590582+08:00
# 1575369335
# 2019-12-03 18:35:35


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
  ''' 按照有序字典载入yaml 支持 !include'''
  with open(path, encoding='utf-8') as f:
    result = yaml.load(f, loader)
  return result


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



import json
def json_load(path):
  with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)
  return data
def json_loads(s):
  return json.loads(s)

def json_save(data, path):
  with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f)
def json_saves(data):
  return json.dumps(data)


def text_load(path, encoding=None):
  ''' 读取文本, 尝试不同的解码 '''
  if not os.path.exists(path):
    raise ValueError("path `{}` not exist".format(path))
  if encoding is None:  # 猜测 encoding
    try:
      open(path, 'r', encoding='utf-8').read()
      encoding = 'utf-8'
    except UnicodeDecodeError:
      encoding = 'gbk'
  with open(path, 'r', encoding=encoding) as f:
    ret = f.read()
  return ret
def text_save(path, data, encoding='utf-8'):
  with open(path, 'w', encoding=encoding) as f:
    f.write(data)
  return True


def sections(text, is_title=lambda line: line.startswith('#')):
  ''' 通过小节的标题和之后文字生成 {标题: 内容} 的 order dict
  '''
  result = OrderedDict()
  title_index = 0
  title = (title_index, 'DEFAULT HEADER')
  result.setdefault(title, [])
  for line in text.splitlines():
    if is_title(line):
      title_index += 1
      title = (title_index, line)
      result.setdefault(title, [])
    else:
      result[title].append(line)
  for key in result:
    result[key] = '\n'.join(result[key])
  return result



def encode_len(text, encode=None):
  return len(text.encode(encode) if encode else text)

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
    dest_length =  limit - encode_len(ellipsis)
    current_index = len(text)
    while encode_len(text[:current_index]) > dest_length:
      current_index -= 1
    return text[:current_index] + ellipsis




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





def clean_xml(text):
  ''' 清理用于 xml 的有效字符
      曾遇到标题里有字符 backspace \x08, 在 CentOS 中无法生成 xml feed
      用于文本内容, 
      一般不用于路径或 yaml csv 中 '''
  def valid_xml_char_ordinal(c):
    # conditions ordered by presumed frequency
    codepoint = ord(c)
    return (0x20 <= codepoint <= 0xD7FF or
            codepoint in (0x9, 0xA, 0xD) or
            0xE000 <= codepoint <= 0xFFFD or
            0x10000 <= codepoint <= 0x10FFFF)
  return ''.join(c for c in text if valid_xml_char_ordinal(c))


DEFAULT_INVALID_CHARS = {':', '*', '?', '"', "'", '<', '>', '|', '\r', '\n', '\t'}
EXTRA_CHAR_FOR_FILENAME = {'/', '\\'}

def remove_invalid_char(dirty, invalid_chars=None, for_path=False, combine_whitespaces=True):
  ''' 清理无效字符, 用于文件路径, 配置字段, 或 yaml csv 等 '''
  text = clean_xml(dirty)
  if invalid_chars is None:
    invalid_chars = set(DEFAULT_INVALID_CHARS)
  else:
    invalid_chars = set(invalid_chars)
    invalid_chars.update(DEFAULT_INVALID_CHARS)
  if not for_path:
    invalid_chars.update(EXTRA_CHAR_FOR_FILENAME)
  text = ''.join([c for c in text if c not in invalid_chars]).strip()
  if combine_whitespaces:
    text = re.sub(r'\s+', ' ', text).strip()
  return text



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
def is_linux():
  import sys
  return sys.platform == 'linux'


import subprocess
def run_command(cmd, verbose=False, timeout=3):
  if verbose: print('> running: ', cmd)
  try:
    output = subprocess.check_output(
        cmd, stderr=subprocess.STDOUT, shell=True, timeout=timeout,
        universal_newlines=True)
  except subprocess.CalledProcessError as exc:
    if verbose: print("status: FAIL", exc.returncode, exc.output)
    raise RuntimeError(f'status: FAIL, {exc.returncode}, {exc.output}')
  else:
    if verbose: print("output: \n{}\n".format(output))
    return output


def easy_average(lister, key=lambda x: x):
  l = len(lister)
  if l == 0: return 0
  return int(sum(key(item) for item in lister) / len(lister) * 100) / 100


import hashlib
def md5(text, limit=32):
  return hashlib.md5(text.encode('utf-8')).hexdigest()[:limit]





# def cdata(text, inline=False):
#   if inline:
#     return f'<![CDATA[{text}]]>'
#   else:
#     return f'<![CDATA[\n{text}\n]]>'


def windows(iterable, length, overlap=0, yield_tail=False):
  '''按照固定窗口大小切片list, 可以重叠
  滑动array窗口,
  每次提供length数目的元素,如果有overlap则重复之前的元素
  yield_tail: 最后不足 length 的那部分元素是否也要 yield'''
  import itertools
  if length <= overlap:
    raise AttributeError(
        'overlap {} cannot larger than length {}'.format(overlap, length))
  it = iter(iterable)
  results = list(itertools.islice(it, length))
  while len(results) == length:
    yield results
    results = results[length-overlap:]
    results.extend(itertools.islice(it, length-overlap))
  if results and yield_tail:
    yield results




def fix_md_title(mdtxt, header_level=3):
  ''' 将正文出现内的 <h1> <h2> 标题降级 '''
  top_level = 100
  for line in mdtxt.splitlines():
    if line.startswith('#'):
      tag = line.split(' ')[0]
      if tag == '#': 
        top_level = min(top_level, 1)
        break
      elif tag == '##': top_level = min(top_level, 2)
      elif tag == '###': top_level = min(top_level, 3)
      elif tag == '####': top_level = min(top_level, 4)
      elif tag == '#####': top_level = min(top_level, 5)
  
  offset = header_level - top_level
  if (top_level == 100) or (offset <= 0):
    return mdtxt
  else:
    pad = '#' * offset
    result = []
    for line in mdtxt.splitlines():
      tag = line.split(' ')[0]
      if tag in ('#', '##', '###', '####', '#####'):
        line = pad + line
      result.append(line)
  return '\n'.join(result)












def fix_svg_image(mdtxt):
  ''' 删除每个图片后面附加的 svg 图片链接 '''
  # 这里通常是图片的label, 需要改成浅灰色
  mdtxt += '\n'
  pat = r'\!\[\]\(data:image\/svg\+xml;utf8,<svg.+?<\/svg>\)(.+?)\n'
  mdtxt = re.sub(pat, r'<center style="color:gray;">\1</center>\n', mdtxt)
  pat2 = r'\!\[\]\(data:image\/svg\+xml;utf8,<svg.+?<\/svg>\)\n'  # 没有 label
  mdtxt = re.sub(pat2, r'\n', mdtxt)
  return mdtxt.strip()






def fix_video_link(mdtxt):
  ''' 视频链接形如
[
![](https://pic1.zhimg.com/v2-6a815464926a29329b5e0e68f0a2a375.png)
动物有语言吗 | 混乱博物馆https://www.zhihu.com/video/1125529815624884224](https://www.zhihu.com/video/1125529815624884224)

修正为

![](https://pic1.zhimg.com/v2-6a815464926a29329b5e0e68f0a2a375.png)
[视频: 动物有语言吗 | 混乱博物馆](https://www.zhihu.com/video/1125529815624884224)'''
  pat = r'\[\n\n(\!\[\]\(https?://pic.+?\))\n\n(.*?)(https://www.zhihu.com/video/\d+|http://www.iqiyi.com.+?.html|http://v.youku.com.+?.html)\]\(\3\)'
  mdtxt = re.sub(pat, r'\1  \n[视频: \2](\3)', mdtxt)

  pat2 = r'\[\!\[\]\(\)(.+?)(http://v.youku.com.+?.html)\]\(\2\)'
  mdtxt = re.sub(pat2, r'[视频: \1](\2)', mdtxt)
  return mdtxt







# pygments lexers 非常不准
from pygments.lexers import guess_lexer
def guess_lang_pygments(code):
  lang = guess_lexer(code).name.lower()  
  if lang == 'text only': lang = 'text'
  return lang

# guesslang 好一些
from guesslang import Guess
def guess_lang(code):
  name = Guess().language_name(code)
  return name.lower()

def fix_code_lang(mdtxt):
  ''' 检测代码语言, 标记在 markdown 代码语法 ```<lang> 位置中 '''
  code_starts = []
  code_ends = []
  in_code = False
  result = mdtxt.splitlines()
  for i, line in enumerate(mdtxt.splitlines()):
    if in_code:
      if line.startswith('    '): 
        continue
      elif line == '':
        continue
      else: 
        in_code = False
        code_ends.append(i)
        # code_ends 记录了不再是代码的行
    else:
      in_code = line.startswith('    ')
      if in_code:
        code_starts.append(i)

  if len(code_ends) < len(code_starts):  # 到结束时仍为代码
    code_ends.append(len(result))
  for start, end in zip(code_starts, code_ends):
    code_body = '\n'.join(result[start:end])
    code_body = trim_leading_spaces(code_body)
    lang = guess_lang(code_body)
    trans_dict = {'javascript': 'js', 'markdown': 'md'}
    if lang in trans_dict: lang = trans_dict[lang]
    # end 表示不再是代码的行, end 之前可能有空行
    # 需要从 end 向前找到第一个有内容的行, 此为代码真正结束位置
    # end 有可能等于 start (对于单行代码时)
    while end:
      end -= 1
      if result[end].startswith('    '): break
    result[start] = f'```{lang}\n' + result[start]
    result[end] = result[end] + '\n```'

  return '\n'.join(result)





def fix_image_alt(mdtxt):
  '''为 image 增加 alt 属性'''
  mdtxt += '\n'
  pat = r'\n\!\[\]\((http.+?\.(png|gif|jpg|jpeg))\)\n'
  mdtxt = re.sub(pat, r'\n![image](\1)\n', mdtxt)
  return mdtxt.strip()





def trim_leading_spaces(text):
  ''' 移除文本行首的空白字符
      首先去掉位于文本中完全为空的行
      然后查看每行的开始空格数, 记录开始空格的最小值
      对每一行都去掉该最小值的空格数
  如: (下面以 `_` 表示空格, `^` 表示行首)
          ^__
          ^____headerline
          ^________contentline1
          ^________contentline2
          ^__
          ^________contentline3
          ^____footerline

  将返回:
          ^headerline
          ^____contentline1
          ^____contentline2
          ^____contentline3
          ^footerline

  '''
  pat = re.compile(r'^( *).+$')
  array = [line for line in text.splitlines() if line.strip()]
  min_leading_space_count = min(len(pat.match(line).group(1)) for line in array)
  # print(min_leading_space_count)
  return '\n'.join(line[min_leading_space_count:] for line in array)


def html2md(html_str):
  h2t = html2text.HTML2Text()
  h2t.body_width = 0
  r = h2t.handle(html_str).strip()
  r = '\n'.join(p.rstrip() for p in r.split('\n'))
  return re.sub('\n{4,}', '\n\n\n', r)

