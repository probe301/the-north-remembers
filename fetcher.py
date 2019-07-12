





from fetcher_api.zhihu import fetch_zhihu_article
from fetcher_api.zhihu import zhihu_article_url
from fetcher_api.zhihu import yield_column_articles



from fetcher_api.zhihu import fetch_zhihu_answer
from fetcher_api.zhihu import zhihu_answer_url
from fetcher_api.zhihu import yield_author_answers
from fetcher_api.zhihu import zhihu_answer_title


from fetcher_api.zhihu import yield_topic_best_answers
from fetcher_api.zhihu import yield_author_articles
from fetcher_api.zhihu import yield_collection_answers
from fetcher_api.zhihu import yield_question_answers



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

    log('request_ZhihuColumnLister column_id', column_id)
    for article in yield_column_articles(column_id, limit=self.option['limit'], min_voteup=20):
      desc = {'url': zhihu_article_url(article),
              'tip': article.title + ' - ' + article.author.name, 
              }
      log('extract new task {}'.format(desc))
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
    min_voteup = self.option.get('min_voteup', 0)
    if '/question/' in self.url:
      question_id = int(self.url.split('/')[-1])
      log('request_ZhihuAnswerLister question_id', question_id)
      iter_answers = yield_question_answers(question_id, limit=limit, min_voteup=min_voteup)
    elif '/people/' in self.url:
      author_id = self.url.split('/')[-2]
      log('request_ZhihuAnswerLister author_id', author_id)
      iter_answers = yield_author_answers(author_id, limit=limit, min_voteup=min_voteup)
    elif '/topic/' in self.url:
      topic_id = int(self.url.split('/')[-2])
      log('request_ZhihuAnswerLister topic_id', topic_id)
      iter_answers = yield_topic_best_answers(topic_id, limit=limit, min_voteup=min_voteup)
    elif '/collection/' in self.url:
      collection_id = int(self.url.split('/')[-1])
      log('request_ZhihuAnswerLister collection_id', collection_id)
      iter_answers = yield_collection_answers(collection_id, limit=limit, min_voteup=min_voteup)
    else:
      raise NotImplementedError

    for answer in iter_answers:
      desc = {'url': zhihu_answer_url(answer),
              'tip': zhihu_answer_title(answer), }
      log('detect new task: {}\n                 {}'.format(desc['url'], desc['tip']))
      tasks_desc.append(desc)

    return tasks_desc





  def request_ZhihuAnswerPage(self):
    data = fetch_zhihu_answer(self.url)
    return data




