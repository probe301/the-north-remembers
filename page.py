
import time
from tools import datalines
from tools import remove_invalid_char
import os
import shutil

from urllib.parse import unquote

from jinja2 import Template
import re


import tools
from tools import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')






class Page:
  '''
  表达一个抓取后的页面, 不管抓取过程
                    -> Page 
  Watcher -> Task -|
                    -> FetcherAPI
  页面内容分为 元数据 + 文章主体 + 评论, 评论先放放
  Page.load(filepath)   返回一个读盘的页面
  Page.create(data) 返回一个新建 (从 fetcher 后的 data json) 的页面
  page.write()  存储页面
  page.render() 转为其他格式, rss, pdf 等, 用于 Exporter
  page.compare() 比对两个页面的区别

  以md文件为单位 Page 对应一个 json data
  Page data json struct:

    title
    folder
    watch_time
    version

    metadata 依据不同类型 Page 而定
      author
      topic
      question
      voteup
      thanks

    sections 如果包含 sections, 说明是从本地 md 加载得来, 需要还原内容和评论等
  '''
  def __init__(self, data):
    self.url = data['url']
    self.folder = data['folder']
    self.filename = remove_invalid_char(data.get('title')) + '.md'
    self.watch_time = data.get('watch_time')
    self.version = data.get('version')
    self.title = data.get('title')

    self.tmpl = ''
    self.data = {}

  def __str__(self):
    return '<Page #{1}> {0.title} (ver. {0.version}, {0.watch_time}) '.format(self, id(self))

  def to_id(self):
    return '<Page #{}>'.format(id(self))


  @classmethod
  def create(cls, data):
    url = data.get('url')
    page_type = tools.parse_type(url)
    if page_type == tools.UrlType.ZhihuColumnPage:
      return ZhihuColumnPage(data)

    if page_type == tools.UrlType.ZhihuAnswerPage:
      return ZhihuAnswerPage(data)

    raise NotImplementedError('Page.request: cannot reg type {}'.format(url))


  @staticmethod
  def convert_dict(metadata_txt):
    d = {}
    for line in metadata_txt.readlines():
      if line.strip():
        k, v = line.strip().split(':')
        d[k.strip()] = v.strip()
    return d

  @classmethod
  def load(cls, path):
    ''' 从磁盘加载 Page
        用于比对页面是否有变化
        只需要加载 title content 等少数内容, 评论等可以不加载 '''
    if not os.path.exists(path):
      raise ValueError('{} not found'.format(path))
    txt = tools.load_txt(path)

    title = txt.split('---')[0].strip().lstrip('#').strip()
    folder = os.path.dirname(path)
    filename = os.path.basename(path)

    metadata = Page.convert_dict(txt.split('---')[1].strip())
    watch_time = metadata.get('watch_time')
    version = metadata.get('version')
    url = metadata.get('url')
    sections = tools.sections(txt.readlines(), is_title=lambda line: line.startswith('#'))

    data = {'title': title, 'folder': folder, 'filename': filename, 
            'metadata': metadata, 
            'watch_time': watch_time, 
            'version': version, 
            'url': url, 
            'sections': sections}  # 从txt加载得到Page必须包含sections
    return cls.create(data)

  def is_changed(self, other):
    ''' 比对一个page对象是否有变化 '''
    return self.data['title'] == other.data['title'] and self.data['content'] == other.data['content']


  def write(self):
    '''存盘'''
    if not os.path.exists(self.folder):
      raise ValueError('can not open folder {}'.format(self.folder))
    save_path = self.folder + '/' + self.filename
    if os.path.exists(save_path):
      log('warning! already exist')
    with open(save_path, 'w', encoding='utf-8') as f:
      f.write(self.render(type='localfile'))
      log('write {} done'.format(save_path))

    # if fetch_images:
    #   # 本地存储, 需要抓取所有附图
    #   fetch_images_for_markdown(save_path)
    # return save_path

  def render(self, type='localfile'):
    if type == 'localfile':
        tmpl = tools.load_txt(self.tmpl)
        rendered = Template(tmpl).render(data=self.data)
        return rendered




# =========================================================
# =================== end of class Page ===================
# =========================================================





class ZhihuColumnPage(Page):
  '''抓取Zhihu专栏的一篇文章
  专栏文章 added 属性:
    metadata
      author
      topic
      voteup
      thanks
      columnname
    content: 正文:
    comment:
  '''

  def __init__(self, data, from_local_file=False):

    super().__init__(data)
    self.tmpl = 'fetcher_api/zhihu_column_page.tmpl'
    if 'sections' in data:
      data = data # TODO
      self.data = data
    else:
      self.data = data






class ZhihuAnswerPage(Page):
  '''抓取Zhihu一篇回答

  回答 added 属性:
    metadata
      author
      voteup
      thanks

    question desc: 问题和描述:
    topic: 话题:
    answer: 回答:
    comment:

  '''

  def __init__(self, data, from_local_file=False):
    super().__init__(data)
    self.tmpl = 'fetcher_api/zhihu_answer_page.tmpl'

    if 'sections' in data:
      data = data # TODO
      self.data = data
    else:
      self.data = data




    # if self.page_type == 'zhihu_answer':
    #   try:
    #     zhihu_answer = fetch_zhihu_answer(self.url)
    #     page = self.remember(zhihu_answer)
    #     return page
    #   except ZhihuParseError as e:
    #     blank_answer = e.value
    #     log_error('!! 问题已删除 {} {}'.format(self.url, blank_answer['title']))
    #     page = self.remember(blank_answer)
    #     return page
    #   except RuntimeError as e:
    #     log_error(e)
    #     raise

    # try:
    #   zhihu_article = fetch_zhihu_article(self.url)
    #   page = self.remember(zhihu_article)
    #   return page
    # except ZhihuParseError as e:
    #   blank_article = e.value
    #   log_error('!! 文章已删除 {} {}'.format(self.url, blank_article['title']))
    #   page = self.remember(blank_article)
    #   return page
