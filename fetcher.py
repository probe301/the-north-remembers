

import os
import re
from enum import Enum
from pyquery import PyQuery
import requests

from crawler.zhihu import fetch_zhihu_article
from crawler.zhihu import zhihu_article_url
from crawler.zhihu import yield_column_articles



from crawler.zhihu import fetch_zhihu_answer
from crawler.zhihu import zhihu_answer_url
from crawler.zhihu import yield_author_answers
from crawler.zhihu import zhihu_answer_title


from crawler.zhihu import yield_topic_best_answers
from crawler.zhihu import yield_author_articles
from crawler.zhihu import yield_collection_answers
from crawler.zhihu import yield_question_answers


from crawler.zhihu import parse_topic
from crawler.zhihu import parse_author
from crawler.zhihu import parse_column
from crawler.zhihu import parse_answer
from crawler.zhihu import parse_article

# from crawler.weixin import fetch_weixin_article_lister
from crawler.weixin import fetch_weixin_article_page
from crawler.wemp import fetch_wemp_page
from crawler.wemp import fetch_wemp_lister


from crawler.zhihu import ZhihuFetchError

from pydantic import (BaseModel, ValidationError, validator, root_validator, 
                      HttpUrl, DirectoryPath, FilePath,)






import tools
from tools import create_logger

log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')



class FetcherError(Exception):
  pass

class FetcherOption(BaseModel):
  save_attachments = True
  limit = 300
  min_voteup = 0
  min_thanks = 0
  text_include: str = None
  text_exclude: str = None

  def patch(self, data):
    for k, v in data.items():
      if k in self.__fields__:
        setattr(self, k, v)




UA = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.13 Safari/537.36"
session = requests.Session()

def common_get(url, cache=True, referer=None):
  '''# requests with UA, referer, cache'''
  md5 = tools.md5(url, 6)
  file_url = tools.remove_invalid_char(','.join(url.split('/')[2:]))
  cache_file = f'temp/{file_url}-{md5}'
  
  if cache and os.path.exists(cache_file):
    modify_time = tools.time_now_stamp() - os.path.getmtime(cache_file)
    if modify_time < 3600: # 在60分钟以内修改
      log(f'using cached `{url}`\n    `{cache_file}`')
      return tools.text_load(cache_file)

  # 没有 cache, 需要抓取
  if referer is None: referer = '/'.join(url.split('/')[:3])
  log(f'referer {referer}')
  headers = { "User-Agent" : UA, "Referer": referer}
  resp = session.get(url, headers=headers)
  log(f'resp.status_code { resp.status_code }')
  if resp.status_code != 200:
    raise FetcherError(f'can not get url {url}, resp.status_code={resp.status_code}')

  data = bytes.decode(resp.content, encoding='utf-8')
  if cache: tools.text_save(data=data, path=cache_file)
  return data



def extract_items_from_feed(content):
  ''' 从 RSS Feed 中取出条目 '''
  # <title>xxx</title>
  # <link>xxx</link>
  # <description>...</description>
  # <pubDate>xxx</pubDate>
  if 'xml version' in content.splitlines()[0]: 
    # 去掉第一行 xml 声明 <?xml version="1.0" encoding="UTF-8"?>
    content = '\n'.join(content.splitlines()[1:])
  for item in PyQuery(content).find('item'):
    article = PyQuery(item)
    yield {'title': article.find('title').text().strip(),
           'tip': article.find('title').text().strip(),
           'url': article.find('link').text().strip(),
           'description': article.find('description').text().strip(),
           # TODO pq cannot parse camelCase tag pubDate
           'pubDate': article.find('pubDate').text().strip()  
           }




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



UrlType = Enum('UrlType', 
                ('ZhihuAnswerPage', 
                 'ZhihuAnswerLister',   
                 'ZhihuColumnPage',     # 用于抓取专栏文章
                 'ZhihuColumnLister',   # 用于监视专栏新文章
                 'ZhihuAuthor', 
                 'ZhihuQuestionPage',   # 用于抓取问题描述
                 'ZhihuQuestionLister', # 问题页, 用于监视新增回答
                 'WeixinArticlePage', 'WeixinArticleLister',
                 'WempPage', 'WempLister',
                 )
               )





def parse_type(url):
  ''' TODO 改成同时返回 Type 和提取信息的方式
      结合 parse_column, xxx 等
      detail=False  返回基本信息 id, 
      detail=True   也返回 title, info, followingcount 等
  '''

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
  if re.search(r'https://rsshub.app/wechat/ershicimi/\d+', url):
    return UrlType.WeixinArticleLister 
  if re.search(r'https://wemp.app/posts/.+?', url):
    return UrlType.WempPage
  if re.search(r'https://wemp.app/accounts/.+?', url):
    return UrlType.WempLister
  if re.search(r'http://mp.weixin.qq.com/s\?__biz=.+?', url):
    return UrlType.WeixinArticlePage



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


def format_weixin_url(url):
  '''需要url中的4个参数 __biz mid idx sn
  '''
  if 'mp.weixin.qq.com' not in url:
    raise ValueError('cannot parse WeiXin url {}'.format(url))

  url, params = url.split('#')[0].split('/s?')
  keys = ('__biz=', 'mid=', 'idx=', 'sn=')
  params = '&'.join(part for part in params.split('&') if part.startswith(keys))
  return f'{url}/s?{params}'

















class Fetcher(BaseModel):

  url : str
  option : FetcherOption

  @classmethod
  def create(cls, url, fetcher_option):
    if isinstance(fetcher_option, dict):
      fetcher_option = FetcherOption(**fetcher_option)
    return cls(url=url, option=fetcher_option)

  @classmethod
  def generate_tip(cls, url):
    ''' 从 url 生成 tip '''
    if parse_type(url) == UrlType.ZhihuAnswerLister:
      if '/topic/' in url:
        topic = parse_topic(url)
        log(f'generate_tip get {topic.name}')
        return '知乎话题 - ' + topic.name
      else:
        raise NotImplementedError()
    elif parse_type(url) == UrlType.ZhihuColumnLister:
      column = parse_column(url)
      log(f'generate_tip get {column.title}')
      return '知乎专栏 - ' + column.title
    else:
      raise ValueError(f'cannot parse url type except Lister {url}')

  @classmethod
  def generate_folder_name(cls, urls):
    ''' 要求所有 urls 属于同一类
        现在未检查 '''
    if not urls:
      raise ValueError('urls is not specified')

    if parse_type(urls[0]) == UrlType.ZhihuAnswerLister:
      if '/topic/' in urls[0]:
        topic_names = []
        for url in urls:
          topic = parse_topic(url)
          # log(f'generate_tip get {topic.name}')
          topic_names.append(topic.name)
        
        return '知乎话题 - ' + ', '.join(topic_names)
      else:
        raise NotImplementedError('generate_folder_name')
    elif parse_type(urls[0]) == UrlType.ZhihuColumnLister:
      column_names = []
      for url in urls:
        column = parse_column(url)
        # log(f'generate_tip get {column.title}')
        column_names.append(column.title)
      return '知乎专栏 - ' + ', '.join(column_names)
    else:
      raise ValueError(f'cannot parse url type {urls}')






  def request(self):
    ''' 抓取页面的详细内容 '''
    url_type = parse_type(self.url)
    method = getattr(self, 'request_' + str(url_type).split('.')[-1])
    result = method()
    return result

  def detect(self):
    ''' 获取主要参数, 如页面标题, 点赞数等, 尽量不抓取详细页面 '''
    url_type = parse_type(self.url)
    method = getattr(self, 'detect_' + str(url_type).split('.')[-1])
    return method()

  def request_ZhihuColumnLister(self):
    ''' 以Zhihu专栏ID获取所有文章
        option 继承自该 task 自身属性
        过滤属性
        limit: 最多返回 n 个 task
        min_voteup: 赞同数超过 n'''
    tasks_desc = []
    column_id = self.url.split('/')[-1]
    limit = self.option['limit']
    min_voteup = self.option.get('min_voteup', 0)
    # 专栏没有感谢 min_thanks = self.option.get('min_thanks', 0)
    log('request_ZhihuColumnLister column_id', column_id)
    for article in yield_column_articles(column_id, limit=limit, min_voteup=min_voteup):
      desc = {'url': zhihu_article_url(article),
              'tip': article.title + ' - ' + article.author.name, 
              }
      log('detect {} {}'.format(desc['url'], desc['tip']))
      tasks_desc.append(desc)
    return tasks_desc



  def detect_ZhihuColumnLister(self):
    c = parse_column(self.url)
    description = c.description.replace('\n', ' ').strip()
    # 这个不准确 updated_time = tools.time_to_humanize(tools.time_from_stamp(c.updated_time))

    # 近一年内更新文章数量
    column_id = self.url.split('/')[-1]
    a_month_ago = tools.time_now().shift(days=-30)
    a_year_ago = tools.time_now().shift(days=-365)
    articles = []
    for article in yield_column_articles(column_id, limit=999, min_voteup=0):
      updated_time = tools.time_from_stamp(article.updated_time)
      articles.append({'title': article.title, 'date': updated_time, 'voteup_count': article.voteup_count})
      if updated_time < a_year_ago and len(articles) > 3: break

    last_update = tools.time_to_humanize(articles[0]['date'])
    count_in_month = len([a for a in articles if a['date'] > a_month_ago])
    count_in_year = len([a for a in articles if a['date'] > a_year_ago])
    average_voteup_count = tools.easy_average(articles, key=lambda a: a['voteup_count'])
    return f'''
    {self.url} 知乎专栏 {c.title} - {description}
    文章数 {c.articles_count}, 关注数 {c.follower_count}, 平均赞数 {average_voteup_count}
    最近更新时间 {last_update}, 近一月内更新 {count_in_month}, 近一年内更新 {count_in_year}
    最新文章 {[a['title'] for a in articles[:3]]}'''



  def request_ZhihuColumnPage(self):
    data = fetch_zhihu_article(self.url)
    return data


  def detect_ZhihuColumnPage(self):
    article = parse_article(self.url)
    return f'''知乎专栏文章 {article.title} {article.author.name} {article.column.title} {article.voteup_count}'''



  def request_ZhihuAnswerLister(self):
    ''' 从 question author topic collection 获取回答列表
        过滤属性包括
          limit: 最多返回 n 个 task
          min_voteup: 赞同数超过 n
    '''
    tasks_desc = []
    limit = self.option['limit']
    min_voteup = self.option.get('min_voteup', 0)
    min_thanks = self.option.get('min_thanks', 0)
    banned_keywords = self.option.get('banned_keywords', '')
    if '/question/' in self.url:
      question_id = int(self.url.split('/')[-1])
      log('request_ZhihuAnswerLister question_id', question_id)
      iter_answers = yield_question_answers(question_id, limit=limit, min_voteup=min_voteup, min_thanks=min_thanks)
    elif '/people/' in self.url:
      author_id = self.url.split('/')[-2]
      log('request_ZhihuAnswerLister author_id', author_id)
      iter_answers = yield_author_answers(author_id, limit=limit, min_voteup=min_voteup, min_thanks=min_thanks)
    elif '/topic/' in self.url:
      topic_id = int(self.url.split('/')[-2])
      log('request_ZhihuAnswerLister topic_id', topic_id)
      iter_answers = yield_topic_best_answers(topic_id, limit=limit, min_voteup=min_voteup, min_thanks=min_thanks, 
                                              banned_keywords=banned_keywords)
    elif '/collection/' in self.url:
      collection_id = int(self.url.split('/')[-1])
      log('request_ZhihuAnswerLister collection_id', collection_id)
      iter_answers = yield_collection_answers(collection_id, limit=limit, min_voteup=min_voteup, min_thanks=min_thanks)
    else:
      raise NotImplementedError

    for answer in iter_answers:
      desc = {'url': zhihu_answer_url(answer),
              'tip': zhihu_answer_title(answer), }
      log('detect {} {}'.format(desc['url'], desc['tip']))
      tasks_desc.append(desc)

    return tasks_desc


  def detect_ZhihuAnswerLister(self):
    # for i, answer in tools.enumer(topic.best_answers, first=30):
    # topics = ' '.join(t.name for t in answer.question.topics)
    # ratio = answer.voteup_count / answer.thanks_count
    # result = f'''
    # {answer.question.title} 赞{answer.voteup_count} 谢{answer.thanks_count} ({ratio:.2f})
    # {topics}'''
    # print(result)
    pass


  def request_ZhihuAnswerPage(self):
    try:
      data = fetch_zhihu_answer(self.url)
    except ZhihuFetchError as e:
      data = e.fake_data
    return data


  def detect_ZhihuAnswerPage(self):
    answer = parse_answer(self.url)
    topics = ', '.join(t.name for t in answer.question.topics)
    return f'''知乎回答 {answer.question.title} {topics}
    by {answer.author.name} {answer.voteup_count}赞 {answer.thanks_count}谢
    '''


  def request_WeixinArticleLister(self):
    # self.url 为任何 RSSHub 微信公众号 feed 来源
    # feed 中 每个 item 的 link 为微信公众号页面永久链接

    content = request_with_ua(self.url)
    result = list(extract_items_from_feed(content))
    for item in result:
      item['url'] = format_weixin_url(item['url'])
    return result

  def request_WeixinArticlePage(self):
    url = format_weixin_url(self.url)
    data = fetch_weixin_article_page(url)
    return data


  def request_WempPage(self):
    html = common_get(self.url)
    data = fetch_wemp_page(html)
    return data

  def request_WempLister(self):
    def gen_wemp_item(url):
      cur_page = 1
      while True:
        html = common_get(url + f'?page={cur_page}')
        items = fetch_wemp_lister(html)
        for item in items:
          yield item
        if len(items) < 10:
          return
        cur_page += 1

    data = []
    url = self.url
    for item, _ in zip(gen_wemp_item(url), range(self.option.limit)):
      data.append(item)
    return data

