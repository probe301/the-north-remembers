
import time
from tools import datalines
from tools import remove_invalid_char
import os
import shutil

from urllib.parse import unquote

from jinja2 import Template
import re

from cleaner import fix_md_title
from cleaner import fix_svg_image
from cleaner import fix_video_link

import tools
from tools import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')

from markdown import markdown
from mdx_gfm import GithubFlavoredMarkdownExtension



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

    文本形式为 (参考 Jekyll markdown)

        ---
        title:  title
        url:  url
        metadatakey1: value1
        metadatakey2: value2
        metadatakey3: value3
        ---

        # 标题

        ## 内容分段1 (如问题 / 引文)

        ### 文章内部标题1
        ### 文章内部标题2
        ### 文章内部标题3
        ### 文章内部标题4

        ## 内容分段2 (如回答 / 正文)

        ### 文章内部标题5
        ### 文章内部标题6

        ## 评论

      抓取文章中自带标题尽量降级到 `三级 title (###)` 以下


  '''
  def __init__(self, data):
    self.url = data['url']
    self.folder = data['folder']
    # 仅把最重要的属性 watch_time, version 等放在 page.watch_time 里, 其他不重要的属性从 metadata 里取
    self.watch_time = data['watch_time']
    self.version = data['version']
    self.metadata = data['metadata']
    self.filename = remove_invalid_char(self.metadata['title']) + '.md'

    self.tmpl = ''  # should override
    self.data = {}  # should override

  def __str__(self):
    title = self.metadata['title']
    return '<Page #{1}> {2} (ver. {0.version}, {0.watch_time}) '.format(self, id(self), title)

  def to_id(self):
    return '<Page #{}>'.format(id(self))

  @property
  def full_text(self):
    ''' 完整的 md 文本, 
        从本地文件 load 回来的 Page 的 data 里面自带 full_text
        新生成的 Page 对象需要 render 得到 full_text'''
    return self.data.get('full_text') or self.render(type='localfile')


  @classmethod
  def create(cls, data):
    url = data['url']
    page_type = tools.parse_type(url)
    if page_type == tools.UrlType.ZhihuColumnPage:
      return ZhihuColumnPage(data)

    if page_type == tools.UrlType.ZhihuAnswerPage:
      return ZhihuAnswerPage(data)

    raise NotImplementedError('Page.request: cannot reg type {}'.format(url))


  @staticmethod
  def convert_dict(metadata_txt):
    d = {}
    for line in metadata_txt.splitlines():
      if line.strip():
        k, v = line.strip().split(':', 1)
        d[k.strip()] = v.strip()
    return d

  @classmethod
  def load(cls, path):
    ''' 从磁盘加载 Page
        用于比对页面是否有变化, 以及生成 RSS 等
        比对页面是否有变化时, 只需要加载 title content 等少数内容, 评论等可以不加载 '''
    if not os.path.exists(path):
      raise ValueError('{} not found'.format(path))
    txt = tools.load_txt(path)

    folder = os.path.dirname(path)
    filename = os.path.basename(path)
    metadata = Page.convert_dict(txt.split('---')[1].strip())
    sections = tools.sections(txt.splitlines(), is_title=lambda line: line.startswith('#'))

    data = {'folder': folder, 
            'filename': filename, 
            'metadata': metadata, 
            'url': metadata['url'], 
            'watch_time': metadata['fetch_date'],
            'version': metadata['version'],
            'full_text': txt,
            'sections': sections}  # 从txt加载得到Page必须包含sections
    return cls.create(data)


  def is_changed(self, other):
    ''' 比对一个page对象是否有变化 '''
    raise NotImplementedError
    # return self.metadata['title'] == other.metadata['title'] and self.data['content'] == other.data['content']


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
    else:
      raise NotImplementedError

  def to_html(self, cut=0):
    ''' 转换为 html 用于输出 RSS 等
        必须有 data['full_text'] 才能 to_html() '''
    full_text = self.full_text
    if cut and len(full_text) > cut:
      full_text = full_text[:cut] + f' ... (共 {len(full_text)} 字)'

    html = markdown(full_text, output_format='html5', extensions=[GithubFlavoredMarkdownExtension()])
    return html

  def postprocess(self, data):
    ''' 处理 # 标题降级, 
        LATEX, 
        图片视频链接修正,
        代码判断语言种类和染色
        等等'''

    raise NotImplementedError


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
      data = self.postprocess(data)
      self.data = data

  def is_changed(self, other):
    ''' 比对一个ZhihuColumnPage对象是否有变化 '''
    return self.metadata['title'] == other.metadata['title'] and self.data['content'] == other.data['content']

  def postprocess(self, data):
    content = fix_md_title(data['content'])
    content = fix_video_link(content)
    content = fix_svg_image(content)
    data['content'] = content
    return data



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

    if 'sections' in data:  # from local load text
      data = data # TODO
      self.data = data
    else:
      data = self.postprocess(data)
      self.data = data

  def is_changed(self, other):
    ''' 比对一个ZhihuAnswerPage对象是否有变化 '''
    return self.metadata['title'] == other.metadata['title'] and self.data['answer'] == other.data['answer']

  def postprocess(self, data):
    answer = fix_md_title(data['answer'])
    answer = fix_video_link(answer)
    answer = fix_svg_image(answer)
    data['answer'] = answer
    return data

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
