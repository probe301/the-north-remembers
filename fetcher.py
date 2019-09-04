





from website.zhihu import fetch_zhihu_article
from website.zhihu import zhihu_article_url
from website.zhihu import yield_column_articles



from website.zhihu import fetch_zhihu_answer
from website.zhihu import zhihu_answer_url
from website.zhihu import yield_author_answers
from website.zhihu import zhihu_answer_title


from website.zhihu import yield_topic_best_answers
from website.zhihu import yield_author_articles
from website.zhihu import yield_collection_answers
from website.zhihu import yield_question_answers


from website.zhihu import parse_topic
from website.zhihu import parse_author
from website.zhihu import parse_column


from website.zhihu import ZhihuFetchError



import tools
from tools import parse_type
from tools import UrlType
from tools import create_logger

log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')



class Fetcher:
  @classmethod
  def create(cls, fetcher_option={}):
    return cls(fetcher_option)

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





  def __init__(self, option):
    self.url = option['url']
    self.option = option

  def request(self):
    url_type = parse_type(self.url)
    method = getattr(self, 'request_' + str(url_type).split('.')[-1])
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
    min_voteup = self.option.get('zhihu_min_voteup', 0)
    # 专栏没有感谢 min_thanks = self.option.get('zhihu_min_thanks', 0)
    log('request_ZhihuColumnLister column_id', column_id)
    for article in yield_column_articles(column_id, limit=limit, min_voteup=min_voteup):
      desc = {'url': zhihu_article_url(article),
              'tip': article.title + ' - ' + article.author.name, 
              }
      log('detect {} {}'.format(desc['url'], desc['tip']))
      tasks_desc.append(desc)
    return tasks_desc


  def request_ZhihuColumnPage(self):
    data = fetch_zhihu_article(self.url)
    return data





  def request_ZhihuAnswerLister(self):
    ''' 从 question author topic collection 获取回答列表
        过滤属性包括
          limit: 最多返回 n 个 task
          min_voteup: 赞同数超过 n
    '''
    tasks_desc = []
    limit = self.option['limit']
    min_voteup = self.option.get('zhihu_min_voteup', 0)
    min_thanks = self.option.get('zhihu_min_thanks', 0)
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





  def request_ZhihuAnswerPage(self):
    try:
      data = fetch_zhihu_answer(self.url)
    except ZhihuFetchError as e:
      data = e.fake_data
    return data




