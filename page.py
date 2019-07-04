
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
  Watcher -> Task -> Page 
                  -> FetcherAPI
  页面内容分为 元数据 + 文章主体 + 评论, 评论先放放
  Page.load(filepath)   返回一个读盘的页面
  Page.create(data) 返回一个新建 (从 fetcher 后的 data json) 的页面
  page.write()  存储页面
  page.render() 转为为其他格式, rss, pdf 等, 用于 Exporter

  以md文件为单位
      ZhihuColumnPage
          .load(path)
          .write(path)
          .compare()
  Page dat json struct:
    
    title
    folder
    watch_time
    version

    metadata
      author
      topic
      question
      voteup
      thanks

    content

    comment

  '''
  def __init__(self, data):
    self.url = data['url']
    self.folder = data['folder']
    self.filename = remove_invalid_char(data.get('title')) + '.md'
    self.watch_time = data.get('watch_time')
    self.version = data.get('version')
    self.title = data.get('title')

    self.tmpl = None
    self.data = None

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


  @classmethod
  def load(cls, filepath):
    '''从磁盘加载 Page'''
    if not os.path.exists(filepath):
      raise ValueError('{} not found'.format(filepath))
    txt = tools.load_txt(filepath)
    # TODO refine
    return {'body': txt}

  def write(self):
    '''存盘'''
    if not os.path.exists(self.folder):
      raise ValueError('can not open folder {}'.format(self.folder))
    save_path = self.folder + '/' + self.filename
    if os.path.exists(save_path):
      log('warning! already exist {}'.format(save_path))
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
  自有属性:
  ZhihuColumnPage data json struct:
    
    title
    folder
    watch_time
    version

    metadata
      author
      topic
      voteup
      columnname

    bgimage

    content

    comment

  '''

  def __init__(self, data):
    super().__init__(data)
    self.data = data
    # self.content = data.get('content')
    # self.metadata = data.get('metadata')
    # self.comment = data.get('comment')
    # return {'title': title,
    #         'content': zhihu_fix_markdown(article_body).strip(),
    #         'comments': zhihu_fix_markdown(comments).strip(),
    #         'author': author.name,
    #         'topic': topics,
    #         'question': '',
    #         'metadata': metadata,
    #         'url': url,
    #         }

    # try:
    #   zhihu_article = fetch_zhihu_article(self.url)
    #   page = self.remember(zhihu_article)
    #   return page
    # except ZhihuParseError as e:
    #   blank_article = e.value
    #   log_error('!! 文章已删除 {} {}'.format(self.url, blank_article['title']))
    #   page = self.remember(blank_article)
    #   return page
    self.tmpl = 'fetcher_api/zhihu_column_page.tmpl'






  # def last_page(self):
  #   ''' 上次的抓取结果 dict, 
  #       分为 metadata content comments 三个部分
  #       TODO 需要考虑文件名变化的情况 以 url 作为 pk?'''
  #   d = {}
  #   d['metadata'] = ''
  #   d['content'] = ''
  #   d['comments'] = ''
  #   return d





class ZhihuAnswerPage(Page):
  '''抓取Zhihu一篇回答

  ZhihuAnswerPage data json struct:

    title
    folder
    watch_time
    version

    metadata
      author
      topic
      voteup
      columnname

    question desc

    content

    comment

  '''

  def __init__(self, data):
    super().__init__(data)
    self.data = data
    # self.content = data.get('content')
    # self.metadata = data.get('metadata')
    # self.comment = data.get('comment')
    # self.question = data.get('question')
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
    self.tmpl = 'fetcher_api/zhihu_answer_page.tmpl'