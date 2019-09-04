import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import time
import tools
from tools import datalines

import os
import shutil
import json
import html2text

from pprint import pprint
import datetime
from zhihu_oauth import ZhihuClient

from zhihu_oauth.exception import GetDataErrorException
from urllib.parse import unquote

from jinja2 import Template
import re
import requests

import urllib.request

from tools import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')


class ZhihuFetchError(Exception):
  def __init__(self, msg, url):
    self.msg = msg
    self.url = url

  def __str__(self):
    return f'{self.__class__.__name__} {self.msg} {self.url}'



# class AnswerStatusError(ZhihuFetchError):
#   ''' 例如
#       https://www.zhihu.com/question/33594085/answer/74817919 
#       回答建议修改：不友善内容
#       这里可以返回一致的 json_data
#   '''
#   def __init__(self, msg, fake_data):
#     self.msg = msg
#     self.fake_data = fake_data


class AnswerDeleteError(ZhihuFetchError):
  ''' 例如
      中国传统建筑中的宫、殿、堂、楼各有什么特点？
      https://www.zhihu.com/question/32237946/answer/734344973
      该回答已被删除 '''
  def __init__(self, msg, url, question):
    self.msg = msg
    self.url = url
    blank_answer = {
      'metadata': {
          'title': question.title + ' - ' + '(本回答已删除)', 
          'topics': ', '.join(t.name for t in question.topics), 
          'author_name': '回答被删除',
          'author_id': '-1',
          'voteup_count': 0,
          'thanks_count': 0,
          'create_date': None,
          'edit_date':   None,
          'fetch_date':  tools.time_now_str(),
          'count': 0,
          'url': url,
      },
      'question_detail': zhihu_fix_markdown(zhihu_content_html2md(question.detail)).strip(),
      'answer': '(回答被删除)',
      'comments': '',
    }
    self.fake_data = blank_answer






class QuestionDeleteError(ZhihuFetchError):
  ''' 例如
      https://www.zhihu.com/question/44069719
      https://www.zhihu.com/question/44069719/answer/97020803
      404 你似乎来到了没有知识存在的荒原 '''
  def __init__(self, msg, url):
    self.msg = msg
    self.url = url
    blank_answer = {
      'metadata': {
          'title': '404 问题被删除', 
          'topics': '', 
          'author_name': '404 问题被删除',
          'author_id': '-1',
          'voteup_count': -1,
          'thanks_count': -1,
          'create_date': None,
          'edit_date':   None,
          'fetch_date':  tools.time_now_str(),
          'count':  -1,
          'url': url,
      },
      'question_detail': '',
      'answer': '(问题被删除)',
      'comments': '',
    }
    self.fake_data = blank_answer




class AnswerNoCommentError(ZhihuFetchError):
  ''' TODO '''
  def __init__(self, msg, url, fake_data):
    self.msg = msg
    self.url = url
    self.fake_data = fake_data



class ArticleDeleteError(ZhihuFetchError):
  ''' 专栏文章被删除 TODO'''
  def __init__(self, msg, url):
    self.msg = msg
    self.url = url
    blank_article = {
      'metadata': {
          'title': '404 专栏文章被删除', 
          'topics': '', 
          'author_name': '404 专栏文章被删除',
          'author_id': '-1',
          'voteup_count': -1,
          'thanks_count': -1,
          'create_date': None,
          'edit_date':   None,
          'fetch_date':  tools.time_now_str(),
          'count':  -1,
          'url': url,
      },
      'answer': '(专栏文章被删除)',
      'comments': '',
    }
    self.fake_data = blank_article


# "　　"
COMMENTS_TMPL = '''
{% if conversations %}
{% for root_comment in conversations %}
{{root_comment.author_info}}:  
{{root_comment.content}} {{root_comment.vote_info}}  
　　{% for child in root_comment.child_comments %}
　　{{child.author_info}}:  
　　{{child.content_indent}} {{child.vote_info}}  
　　{% endfor %}
  
{% endfor %}
{% endif %}
'''




TOKEN_FILE = 'token.pkl'
client = ZhihuClient()
client.load_token(TOKEN_FILE)

# from zhihu_oauth import ZhihuClient
# from zhihu_oauth import Article
# from zhihu_oauth import Answer
# article = client.article(123)
# answer = client.answer(123)
# answer.__class__ == Answer


def zhihu_detect(url):
  '''用来检测页面是否可用'''
  UA = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.13 Safari/537.36"
  headers = { "User-Agent" : UA,
              "Referer": "https://zhuanlan.zhihu.com/"}

  session = requests.Session()
  return session.get(url, headers=headers)

  # t = sess.get(url, headers=headers).text
  # data = json.loads(bytes.decode(t, encoding='utf-8'))

  # json = sess.get(url, headers=headers).json()

def zhihu_detect_with_client(url):
  '''带有登录后的 session'''
  return client.test_api('GET', url)





def zhihu_answer_url(answer):
  '''以 answer 对象拼接 url, 貌似答案被删也不报错'''
  # log('zhihu_answer_url answer' + str(answer))
  if isinstance(answer, int):
    answer = client.answer(answer)
  return 'https://www.zhihu.com/question/{}/answer/{}'.format(answer.question.id, answer.id)



def zhihu_answer_format(answer):
  if isinstance(answer, int):
    answer = client.answer(answer)
  url = zhihu_answer_url(answer)
  title = answer.question.title
  author = answer.author.name
  vote = answer.voteup_count
  topic = '|'.join([t.name for t in answer.question.topics])
  return f'<ZhihuAnswer {title} by {author} ({vote}赞) {topic}>\n{url}'

def zhihu_answer_title(answer):
  '''TODO 需要处理多个匿名用户回答同一个问题的情况'''
  return answer.question.title + ' - ' + answer.author.name + '的回答'




def parse_question(question):
  ''' 以 url, (str or int) id 转换为 question 对象
      url 可能是 www.zhihu.com 或 api.zhihu.com
  '''
  if isinstance(question, str):
    if '/answer' in question: question = question.split('/answer')[0]
    if 'api.zhihu.com' in question: # https://api.zhihu.com/question/12345
      question = client.question(int(question.split('/')[-1]))
    elif question.isdigit():
      question = client.question(int(question))
    else:
      question = client.from_url(question)
  elif isinstance(question, int):
    question = client.question(question)
  return question


def parse_answer(answer):
  ''' 以 url, (str or int) id 转换为 answer 对象
      url 可能是 www.zhihu.com 或 api.zhihu.com
  '''
  if isinstance(answer, str):
    if 'api.zhihu.com' in answer: # https://api.zhihu.com/answers/71917800
      answer = client.answer(int(answer.split('/')[-1]))
    elif answer.isdigit():
      answer = client.answer(int(answer))
    else:
      answer = client.from_url(answer)
  elif isinstance(answer, int):
    answer = client.answer(answer)
  return answer


def parse_column(column):
  column = client.from_url(column)
  return column


def parse_article(article):
  if isinstance(article, str):
    if 'api.zhihu.com' in article:
      article = client.article(int(article.split('/')[-1]))
    elif article.isdigit():
      article = client.article(int(article))
    else:
      article = client.from_url(article)
  elif isinstance(article, int):
    article = client.article(article)
  return article

def parse_topic(topic):
      # https://www.zhihu.com/topic/19568972/questions
      # https://www.zhihu.com/topic/19568972/hot
      # https://www.zhihu.com/topic/19568972/top-answers
      # https://api.zhihu.com/topic/19568972/top-answers

  if isinstance(topic, str):
    if topic.isdigit():
      topic = client.topic(int(topic))
    else:
      for part in topic.split('/'):
        if part.isdigit():
          topic = client.topic(int(part))
          break
  elif isinstance(topic, int):
    topic = client.topic(topic)
  return topic


def parse_author(url):
  pass


class FakeAuthor:
  def __init__(self):
    self.name = '[匿名用户]'
    self.headline = ''



































'''
 ###### #####  ##   ## ##   ## ####### ##   ## #######
###    ##   ## ### ### ### ### ##      ###  ##    ##
##     ##   ## ## # ## ## # ## ######  ## # ##    ##
###    ##   ## ##   ## ##   ## ##      ##  ###    ##
 ###### #####  ##   ## ##   ## ####### ##   ##    ##
'''

class CommentAuthor:
  """ 配合 CommentText 使用的 author """
  def __init__(self, aid, name, url_token, role):
    self.aid = aid  # bdf090...
    self.name = name
    self.url_token = url_token # alphanum id with dash
    self.role = role
  def __equal__(self, other):
    return self.aid == other.aid
  def __str__(self):
    return '<CommentAuthor {}>'.format(self.name)
  @classmethod
  def create(cls, author_json):
    aid = author_json['member']['id']
    name = author_json['member']['name']
    url_token = author_json['member'].get('url_token')
    role = author_json['role']
    return cls(aid, name, url_token, role)


class CommentBody:
  """
  从 get_comments_api_v4() 得到的评论对象, 构造成和 zhihu_oauth 获得的评论对象属性一致
  comment.author.name, reply_to_author, content, vote_count
  """
  def __init__(self, cid, vote_count, author, content, reply_to):
    self.cid = cid
    self.vote_count = vote_count
    self.content = content
    self.author = author
    self.reply_to = reply_to
    self.child_comments = None
  def __str__(self):
    if self.reply_to:
      s = '<Comment #{} vote {} "{}"=>"{}"> {}'
      return s.format(self.cid, self.vote_count, self.author.name, self.reply_to.name, self.content[:20])
    else:
      s = '<Comment #{} vote {} "{}"> {}'
      return s.format(self.cid, self.vote_count, self.author.name, tools.truncate(self.content, 40))
  @property
  def author_info(self):
    if self.reply_to:
      return f'{self.author.name} 回复 {self.reply_to.name}'
    else:
      return f'{self.author.name}'
  @property
  def vote_info(self):
    return f'({self.vote_count} 赞)' if self.vote_count > 0 else ''
  @property
  def content_indent(self):
    lines = (line.strip() + '  ' for line in self.content.splitlines() if line.strip())
    return '\n'.join('　　' + line for line in lines)[2:]  # [2:] 略过第一段开头的 '　　'

  @classmethod
  def create(cls, comment_json):
    cid = comment_json['id']
    vote_count = comment_json['vote_count']
    content = zhihu_content_html2md(comment_json['content'])
    author = CommentAuthor.create(comment_json['author'])
    if comment_json.get('reply_to_author'):
      reply_to = CommentAuthor.create(comment_json['reply_to_author'])
    else:
      reply_to = None
    return cls(cid, vote_count, author, content, reply_to)




def get_comments_api_v4(answer_article_object, limit=2000):
  ''' 获取评论, zhihu oauth 方式太慢, 换个直接拿到 api v4 json 的方式
      使用 (for root_comments)
      https://www.zhihu.com/api/v4/answers/<id>/root_comments?order=normal&limit=20&offset=20
      https://www.zhihu.com/api/v4/articles/<id>/root_comments?order=normal&limit=20&offset=20
      和 (for child_comments)
      https://www.zhihu.com/api/v4/comments/<id>/child_comments?limit=20&offset=20
      取得评论对象, 速度比较快
      
      结构是双层的, (root_comments 和 child_comments)
      即评论可以有子级评论, 子级评论可以相互回复,
      回复的对象是用户, 不是评论
      最开始还有5条精选评论, 但是脱离上下文了, 不管它
      root_comments 取得结果中, 
      每个 root_comment 带有最多两条 child_comments 预览, 
      仍然要对每个 root_comment 追踪 get 才能得到全部 child_comments

      例如
        {'collapsed_counts': 0,
        'common_counts': 38,
        'data': [{'author': 'e4686e...',
                  'child_comment_count': 3,
                  'child_comments': [
                                      {'author': '1e3553...',
                                      'content': '已更新'},
                                      {'author': 'd0090a...',
                                      'content': '你好 可以转载吗 我会标明作者和出处'}
                                    ],
                  {'author': '16c1e1...',
                  'child_comment_count': 0,
                  'child_comments': [],
                  'content': '非常棒的解答'},
                  {
                    ...
                  },
                  {
                    ...
                  },   
        'featured_counts': 0,
        'paging': { 'is_end': False,
                    'is_start': True,
                    'next': 'xxx',
                    'previous': 'xxx',
                    'totals': 30},
        'reviewing_counts': 0
        }
  '''
  page_id = answer_article_object.id
  page_klass = answer_article_object.__class__.__name__
  if page_klass == 'Answer':
    tmpl = 'https://www.zhihu.com/api/v4/answers/{page_id}/root_comments?order=normal&limit=20&offset={offset}'
  elif page_klass == 'Article':
    tmpl = 'https://www.zhihu.com/api/v4/articles/{page_id}/root_comments?order=normal&limit=20&offset={offset}'
  else:
    raise ValueError(f'get_comments_api_v4 cannot parse page_klass for {answer_article_object} {page_id}')

  comment_list = []

  for offset in range(0, limit, 20):
    comment_link = tmpl.format(page_id=page_id, offset=offset)
    if offset == 0:
      # log(f'start fetching comment {comment_link} ...')
      pass

    comment_data = zhihu_detect_with_client(comment_link).json()
    # comment_data = json.loads(text, encoding='utf-8')
    comment_list.extend(comment_data['data'])
    if comment_data.get('paging'):
      if comment_data['paging']['is_end']:
        break
    tools.time_random_sleep(0.2)
  # log(f'fetch {len(comment_list)} top level comments')
  return comment_list



def get_child_comments_api_v4(root_comment_id, limit=2000):
  '''从 root comment id 获取 child comment'''
  tmpl = 'https://www.zhihu.com/api/v4/comments/{root_comment_id}/child_comments?limit=20&offset={offset}'

  child_comment_list = []

  for offset in range(0, limit, 20):
    comment_link = tmpl.format(root_comment_id=root_comment_id, offset=offset)
    # log(f'start fetching child comments {comment_link} ...')
    comment_data = zhihu_detect_with_client(comment_link).json()
    # comment_data = json.loads(text, encoding='utf-8')
    child_comment_list.extend(comment_data['data'])
    if comment_data.get('paging'):
      if comment_data['paging']['is_end']:
        break
    tools.time_random_sleep(0.2)
  # log(f'fetch {len(child_comment_list)} child level comments')
  return child_comment_list


def get_valuable_conversations_api_v4(comment_list, root_limit=10, child_limit=8):
  '''
  使用 url api v4
  conversation 会话组, 是父级评论和下属子级评论的对话集合
  在 url api v4 时已经用 json data 标记好了对话组
  但是 root comment get 的结果, 只能得到不超过两条 child comment, 仍然需要追踪

  root_limit : 选取会话组的上限
  child_limit : 会话组中内部相互回复的上限

  会话组选取规则是
    0 去掉 featured 属性的内容 (这些评论之后会重复一遍)
    1 计算每会话组的 score = rootcomment.voteup + len(childcomments), 选最大 10 个会话组
    2 也保留答主参与了回复的会话组 TODO

  在选中的会话组内, 评论的选取规则是
    1 保留会话组的父级评论 (仅一条)
    3 在该会话组的子级评论中, 选取 8 个最高 vote 的评论
    4 在子级评论中保留答主的评论 TODO
    5 保留这些评论的上文 TODO
  '''

  conversations = []
  for root_comment in comment_list:  # comment_list 的元素可能带有子级评论
                                  # root_comment = toplevel_comment
    if root_comment.get('featured'):
      continue # 略过 featured 属性
    root_comment['score'] = root_comment['vote_count'] + root_comment['child_comment_count']
    # TODO root_comment['contain_page_author'] 
    conversations.append(root_comment)
  conversations = sorted(conversations, key=lambda c: -c['score'])[:root_limit]
  # conversations = sorted(conversations, key=lambda c: -c['created_time']) # 不需要调整时间顺序
  result = []
  for root_comment in conversations:
    if root_comment['child_comment_count'] > len(root_comment['child_comments']):
      child_comments = get_child_comments_api_v4(root_comment['id'])
    else:
      child_comments = root_comment['child_comments']
    child_comments = sorted(child_comments, key=lambda c: -c['vote_count'])[:child_limit]
    child_comments = sorted(child_comments, key=lambda c: c['created_time'])  # 调整为时间先后顺序
    child_comments = [CommentBody.create(c) for c in child_comments]
    father = CommentBody.create(root_comment)
    father.child_comments = child_comments
    result.append(father)
  return result




  
def preview_comment_data(comment_data):
  '''预览 comment 结构'''
  from copy import deepcopy

  def short_author(author):
    name = author['member']['name']
    id = author['member']['id']
    url_token = author['member']['url_token']
    role = author['role']
    return role + ', ' + name + ', ' + id[:6] +  '..., ' + url_token

  def short_comment(comment):
    comment['author'] = short_author(comment['author'])

    if comment.get('reply_to_author'):
      comment['reply_to_author'] = short_author(comment['reply_to_author'])

    delete_key_tmpl = {
                      'allow_delete': False,
                      'allow_like': True,
                      'allow_reply': True,
                      'allow_vote': True,
                      'can_collapse': False,
                      'can_recommend': False,
                      'censor_status': 0,
                      # 'child_comment_count': 0,
                      # 'child_comments': [],
                      'collapsed': False,
                      # 'content': '非常棒的解答',
                      # 'created_time': 1437720487,
                      'disliked': False,
                      # 'featured': False,
                      # 'id': 123,
                      # 'is_author': False,
                      'is_delete': False,
                      'resource_type': 'answer',
                      'reviewing': False,
                      'type': 'comment',
                      'url': 'https://www.zhihu.com/comments/123',
                      # 'vote_count': 6,
                      # 'voting': False
                      }

    for key in delete_key_tmpl.keys():
      del comment[key]

  data = deepcopy(comment_data)
  sum_parent = 0
  sum_child = 0
  for comment in data['data']:
    sum_parent += 1
    short_comment(comment)
    for child in comment['child_comments']:
      short_comment(child)
      sum_child += 1
  pprint(data)
  print(sum_parent, sum_child)







def get_valuable_conversations(comments, limit=10):
  '''
  limit: 有效的会话组里的likes总和最大的 n 个对话

  2016.07.05 试图大量使用 zhihu-oauth comment.conversation 来获取评论会话,
  但是 zhihuapi 发送了大量get请求, 总是超时 comments/xxxxx/conversation 非常慢
  还是采用老办法

  zhihuapi: replies12 = list(c12.replies) # 所有回复本评论的评论, 第一条为本评论
  [print(r.author.name, r.content) for r in replies12]
  # 玄不救非氪不改命 可以用马列主义指导炒房嘛，郁闷啥呢？
  # Razor Liu 你觉得能问出这话的会是有钱炒房的阶级么...
  # 暗黑的傀儡师 思路很新颖，就是把劳动力市场看的太简...

  zhihuapi: g12 = list(c12.conversation)  # 包含该评论的对话, 从最开始到结束
  [print(r.author.name, r.content) for r in g12]
  # Razor Liu 看不到武装革命可能性的情况下,读马列是不是会越读越郁闷?
  # 玄不救非氪不改命 可以用马列主义指导炒房嘛，郁闷啥呢？
  # Razor Liu 你觉得能问出这话的会是有钱炒房的阶级么...
  '''

  # all_comments = list(answer.comments)
  # selected_ids = set()
  # while group_limit:
  #   selecting = (c for c in all_comments if c.id not in selected_ids)
  #   top_voteup_comment = max(selecting, key=lambda x: x.vote_count)
  #   conversation = list(top_voteup_comment.conversation)
  #   yield [comment_to_string(comment) for comment in conversation]
  #   time.sleep(1)
  #   group_limit -= 1
  #   for c in conversation:
  #     selected_ids.add(c.id)

  conversations = get_all_conversations(comments)
  sum_vote_count = lambda conversation: sum(comment.vote_count for comment in conversation)
  valuable_conversations = sorted(conversations, key=sum_vote_count, reverse=True)[:limit]
  return [[comment_to_string(c) for c in v] for v in valuable_conversations]


def get_all_conversations(comments):
  '''
  会话, 评论区的所有评论的分组

  2016.07.05 试图大量使用 zhihu-oauth comment.conversation 来获取评论会话,
  但是 zhihuapi 发送了大量get请求, 总是超时 comments/xxxxx/conversation 非常慢
  还是采用老办法

  规则:
  0. comment 分为直接评论和回复别人两种
  1. 从第一个评论开始, 将每一个评论归入合适的分组, 否则建新分组
  2. 直接评论视为开启新的会话
  3. B回复A, 放入B回复的A的评论的会话,
      如果A已经出现在n个会话里, 寻找A之前是否回复过B,
          A回复过B: 放在这一组会话里,
          A没有回复过B: 放在A最晚说话的那一条评论的会话里 second_choice
  '''
  result = []
  for comment in comments:
    if not comment.reply_to:  # 直接评论, 开启新的会话
      result.append([comment])
    else:                     # 回复别人
      second_choice = None  # A最晚说话的那一条评论的会话
      for conversation in reversed(result):  # 反着查找, 获取时间最近的匹配
        if comment.reply_to.name in [c.author.name for c in conversation]:
          second_choice = second_choice or conversation
          if comment.author.name in [c.reply_to.name for c in conversation if c.reply_to]:
            # B回复A之前 A也回复过B
            conversation.append(comment)
            break
      else:  # B回复A, 但是A没有回复过B, 或者A被删了评论
        if second_choice:  # A没有回复过B 放在A最晚说话的那一条评论的会话里
          second_choice.append(comment)
        else:  # A被删了评论, 只好加入新的会话分组
          result.append([comment])

  return result




def comment_to_string(comment):
  reply_to_author = ' 回复 **{}**'.format(comment.reply_to.name) if comment.reply_to else ''
  vote_count = '  ({} 赞)'.format(comment.vote_count) if comment.vote_count else ''
  content = zhihu_content_html2md(comment.content).strip()
  if '\n' in content:
    content = '\n\n' + content
  text = '**{}**{}: {}{}'.format(comment.author.name, reply_to_author, content, vote_count)
  return text
















'''
 #####  ##   ##  ###### ##   ## ####### ######
##   ## ###  ## ##      ##   ## ##      ##   ##
####### ## # ##  #####  ## # ## ######  ######
##   ## ##  ###      ## ### ### ##      ##  ##
##   ## ##   ## ######  ##   ## ####### ##   ##
'''


def fetch_zhihu_answer(url):
  question = parse_question(url)
  answer = parse_answer(url)
  try:
    title = question.title
    detail = question.detail
  except GetDataErrorException:
    # zhihu_oauth.exception.GetDataErrorException:
    # A error happened when get data: 问题不存在
    raise QuestionDeleteError(msg='问题已删除', url=url)

  try:
    author = answer.author
    if author is None:
      # 如果匿名, 现在返回 None, 需要 fix 为一个 AuthorObject
      author = FakeAuthor()
  except (requests.exceptions.RetryError, GetDataErrorException):
    # 回答已被删除
    raise AnswerDeleteError('本回答已删除', url=url, question=question)


  try:
    content = answer.content
  except requests.exceptions.RetryError:
    # TODO 找不到 answer.content, 一般是问题已被删除? 
    # blank_answer = blank_zhihu_answer()
    # blank_answer['title'] = '(找不到 answer.content)' + answer.question.title
    # blank_answer['url'] = url
    raise ZhihuFetchError(msg='找不到 answer.content', url=url)

  answer_body = zhihu_content_html2md(content).strip()

  # suggest_edit 答案是否处于「被建议修改」状态，常见返回值为：
  # { 'status': True,
  #   'title': '为什么回答会被建议修改',
  #   'tip': '作者修改内容通过后，回答会重新显示。如果一周内未得到有效修改，回答会自动折叠',
  #   'reason': '回答被建议修改：\n不宜公开讨论的政治内容',
  #   'url': 'zhihu://questions/24752645' }
  if answer.suggest_edit.status:
    answer_body += '\n' + answer.suggest_edit.reason + '\n' + answer.suggest_edit.tip

  motto = '({})'.format(author.headline) if author.headline else ''
  motto = motto.replace('\n', ' ')
  question_details = zhihu_content_html2md(detail).strip()

  title = question.title + ' - ' + author.name + '的回答'
  topics = ', '.join(t.name for t in question.topics)
  question_id = question.id
  count = len(answer_body)
  voteup_count = answer.voteup_count
  thanks_count = answer.thanks_count
  create_date = parse_json_date(answer.created_time)
  edit_date = parse_json_date(answer.updated_time)
  fetch_date = tools.time_now_str()




  try:
    comments = get_comments_api_v4(answer, limit=2000)
    conversations = get_valuable_conversations_api_v4(comments, root_limit=10, child_limit=8)
    # conversations = get_valuable_conversations(get_old_fashion_comments(url), limit=10)
  except (requests.exceptions.RetryError):
    resp_json = zhihu_detect(answer.comments._url).json()
    if 'error' in resp_json:
      conversations = [ [
        '错误: {name} - {code} - {message}'.format(**resp_json['error'])
      ], ]
    raise 


  metadata = {
    'title': title, 
    'topics': topics, 
    'author_name': author.name,
    'author_id': author.__dict__['_cache']['url_token'] if author.name != '匿名用户' else '-1',
    'voteup_count': voteup_count,
    'thanks_count': thanks_count,
    'create_date': create_date,
    'edit_date':   edit_date,
    'fetch_date':  fetch_date,
    'count':  count,
    'url': url,
  }




  comments = Template(COMMENTS_TMPL).render(conversations=conversations)

  return { 'metadata': metadata,
           'question_detail': zhihu_fix_markdown(question_details).strip(),
           'answer': zhihu_fix_markdown(answer_body).strip(),
           'comments': comments.strip(),
          }





































'''
 #####  ###### ####### ###### ###### ##      #######
##   ## ##   ##   ##     ##  ###     ##      ##
####### ######    ##     ##  ##      ##      ######
##   ## ##  ##    ##     ##  ###     ##      ##
##   ## ##   ##   ##   ###### ###### ####### #######
'''

def zhihu_article_format(article):
  if isinstance(article, int):
    article = client.article(article)
  url = zhihu_article_url(article)
  title = article.title
  author_name = article.author.name # 应该没有专栏匿名作者 if article.author else FakeAuthor().name
  vote = article.voteup_count
  column = article.column.title if article.column else '无专栏'
  return f'<ZhihuArticle {title} ({column}) by {author_name} ({vote}赞)>\n{url}'


def zhihu_article_url(article):
  # https://zhuanlan.zhihu.com/p/22197924
  if isinstance(article, int):
    return 'https://zhuanlan.zhihu.com/p/{}'.format(article)
  else:
    return 'https://zhuanlan.zhihu.com/p/{}'.format(article.id)


def zhihu_article_title(article):
  title = article.title
  author_name = article.author.name # 应该没有专栏匿名作者 if article.author else FakeAuthor().name
  column = article.column.title if article.column else ''
  return f'{title} - {author_name}的专栏 {column}'.strip()


def fetch_zhihu_article(url):
  article = parse_article(url)
  try:
    author = article.author
  except (requests.exceptions.RetryError, GetDataErrorException):
    # 文章已被删除
    raise ArticleDeleteError(msg='本文章已删除', url=url)

  content = article.content

  article_body = zhihu_content_html2md(content).strip()
  if article.suggest_edit.status:
    article_body += '\n' + article.suggest_edit.reason + '\n' + article.suggest_edit.tip

  if article.image_url:
    # https://pic4.zhimg.com/50/d58be60ea916b5c231e72e790dc71b33_hd.jpg
    # 需要fix为
    # https://pic4.zhimg.com/d58be60ea916b5c231e72e790dc71b33_hd.jpg
    # 否则白色背景会显示为黑色背景
    bg_img_url = article.image_url.replace('.zhimg.com/50/', '.zhimg.com/')
    article_body = '![]({})\n\n'.format(bg_img_url) + article_body

  motto = '({})'.format(author.headline) if author.headline else ''
  motto = motto.replace('\n', ' ')

  title = zhihu_article_title(article)

  count = len(article_body)
  voteup_count = article.voteup_count
  edit_date = parse_json_date(article.updated_time)
  fetch_date = tools.time_now_str()
  # log(list(article.comments))

  try:
    comments = get_comments_api_v4(article, limit=2000)
    conversations = get_valuable_conversations_api_v4(comments, root_limit=10, child_limit=8)
  except (requests.exceptions.RetryError):
    resp_json = zhihu_detect(article.comments._url).json()
    if 'error' in resp_json:
      conversations = [ [
        '错误: {name} - {code} - {message}'.format(**resp_json['error'])
      ], ]
    raise

  topics = article._data['topics']   # zhihu_oauth API 没有这个属性, 通过 _data 取出

  metadata = {
    'title': title, 
    'author_name': author.name,
    'author_id': author.__dict__['_cache']['url_token'],
    'column_name': article.column.title if article.column else '无专栏',
    'column_id': article.column._id if article.column else '',
    'voteup_count': voteup_count,
    'edit_date':   edit_date,
    'fetch_date':  fetch_date,
    'count':  count,
    'url': url,
    'topics': ', '.join(t['name'] for t in topics),
  }


  comments = Template(COMMENTS_TMPL).render(conversations=conversations)

  return { 'metadata': metadata,
           'content': zhihu_fix_markdown(article_body).strip(),
           'comments': comments.strip()
         }
































'''
####### ###### ##   ##        ##   ## ######
##        ##    ## ##         ### ### ##   ##
######    ##     ###          ## # ## ##   ##
##        ##    ## ##         ##   ## ##   ##
##      ###### ##   ##        ##   ## ######
'''

def zhihu_content_html2md(html):
  h2t = html2text.HTML2Text()
  h2t.body_width = 0
  r = h2t.handle(html).strip()
  r = '\n'.join(p.rstrip() for p in r.split('\n'))
  return re.sub('\n{4,}', '\n\n\n', r)


def parse_json_date(n):
  return str(datetime.datetime.fromtimestamp(n))


def fetch_image(url, ext, markdown_file, image_counter):
  '''
  需要区分 全路径 和 相对引用
  需要转换每个 md 的附件名
  需要附件名编号'''
  if '.zhimg.com' not in url:
    log_error('  exotic url: ', url)
    return url
  # name = url.split('/')[-1]
  # nonlocal image_counter
  image_counter.append(1)
  image_index = str(len(image_counter))
  if len(image_index) == 1:
    image_index = '0' + image_index

  folder = os.path.dirname(markdown_file)
  basename = os.path.basename(markdown_file)[:-3]
  image_fullname = folder + '/' + basename + image_index + ext
  image_name = basename + image_index + ext

  if os.path.exists(image_fullname):
    log('  existed: ' + url)
    return image_name

  log('    fetching ' + url)
  data = urllib.request.urlopen(url).read()
  with open(image_fullname, "wb") as f:
    f.write(data)
  return image_name



def fetch_images_for_markdown(markdown_file):
  with open(markdown_file, 'r', encoding='utf-8') as f:
    text = f.read()

  if 'whitedot.jpg' in text:
    print("'whitedot.jpg' in text")
    if not markdown_file.endswith('whitedot'):
      shutil.move(markdown_file, markdown_file + '.whitedot')
    return False

  # print('start parsing md file: ' + markdown_file.split('/')[-1])
  image_counter = []
  replacer = lambda m: fetch_image(url=m.group(0),
                                   ext=m.group(2),
                                   markdown_file=markdown_file,
                                   image_counter=image_counter)

  text2, n = re.subn(r'(https?://pic[^()]+(\.jpg|\.png|\.gif))', replacer, text)
  if n > 0:
    with open(markdown_file, 'w', encoding='utf-8') as f:
      f.write(text2)
    log('parsing md file done:  ' + markdown_file.split('/')[-1])
  else:
    log('no pictures downloaded: ' + markdown_file.split('/')[-1])





def zhihu_fix_markdown(text):
  # 去除 html2text 转换出来的 strong 和 link 的多余空格
  # drop extra space in link syntax
  # eg. [ wikipage ](http://.....) => [wikipage](http://.....)
  # eg2 [http://www.  businessanalysis.cn/por  tal.php ](http://www.businessanalysis.cn/portal.php)
  # TODO fix vedio link in markdown
  # in https://zhuanlan.zhihu.com/p/22604627
  pattern_hyperlink = re.compile(r'\[(.+?)\](?=\(.+?\))')

  def hyperlink_replacer(mat):
    r = mat.group(1).strip()
    if r.startswith('http'):
      r = re.sub(r'^https?:\/\/(www\.)?  ', '', r)
      r = r.replace(' ', '')
      # r = mat.group(1).replace('http://www.  ', '').replace('http://  ', '').replace(' ', '')
    if r.endswith('/'):
      r = r[:-1]
    if r.endswith(' _ _'):
      r = r[:-4] + '...'
    if r.endswith('__'):
      r = r[:-2]
    return '[{}]'.format(r)

  # drop extra space around strong tag
  pattern_strong = re.compile(r'\*\* (.+?) \*\*')
  replace_strong = lambda m: '** 回复 **' if m.group(1) == '回复' else '**'+m.group(1)+'**'

  # fix tex syntax use zhihu.com/equation
  pattern_tex_link = re.compile(r'\]\(\/\/zhihu\.com\/equation\?tex=')

  # fix zhihu redirection
  # [Law of large numbers](//link.zhihu.com/?target=https%3A//en.wikipedia.org/wiki/Law_of_large_numbers)
  # =>
  # [Law of large numbers](https://en.wikipedia.org/wiki/Law_of_large_numbers)
  pattern_redirect_link = re.compile(r'\]\((https?:)?\/\/link\.zhihu\.com\/\?target=(.+?)\)')
  replace_redirect_link = lambda m: '](' + unquote(m.group(2)) + ')'

  # ![](互联网领域的「用户研究」有哪些有趣的发现？ - 采铜的回答02.png)
  img_reg = r'\n*\!\[\]\((https?://pic[^()]+?(\.jpg|\.png|\.gif))\)\n*'
  pattern_img_start_inline = re.compile(img_reg)
  def replace_img_start_inline(mat):
    # 保证生成的 *.md 图片在新的一行
    s = mat.group(0)
    while not s.startswith('\n\n'):
      s = '\n' + s
    while not s.endswith('\n\n'):
      s = s + '\n'
    return s
  pattern_multiple_newline = re.compile(r'\n{3,}') # 连续3+换行的都压缩到3个

  text = pattern_hyperlink.sub(hyperlink_replacer, text)
  text = pattern_strong.sub(replace_strong, text)
  text = pattern_redirect_link.sub(replace_redirect_link, text)
  text = pattern_tex_link.sub('](http://www.zhihu.com/equation?tex=', text)
  text = pattern_img_start_inline.sub(replace_img_start_inline, text)
  text = pattern_multiple_newline.sub('\n\n\n', text)

  text = zhihu_fix_mistake_headerline_splitter(text)

  return text



def zhihu_fix_mistake_headerline_splitter(text):
  ''' html to markdown 之后,
  知乎回答内容中可能有分割线紧跟着上一节文本, 如
  text1111
  \--------------
  text22222

  此时 markdown 会将 text1111 解释为标题, 需修正'''
  pattern = re.compile(r'(?<!\n)(\n\\\-{10,})')
  text = pattern.sub(r'\n\1', text)

  pattern = re.compile(r'(?<!\n)(\n={10,})')
  text = pattern.sub(r'\n\1', text)
  return text



def test_zhihu_fix_mistake_headerline_splitter():

  root = 'D:/ZhihuEpub/统计学/'
  for md in tools.all_files(root, '*.md'):
    # print(md)
    text = open(md, encoding='utf8').read()

    text_new = zhihu_fix_mistake_headerline_splitter(text)

    if text_new != text:
      with open(md, 'w', encoding='utf8') as f:
        f.write(text_new)

      print('write on ' + md)











'''
##      ######  ###### ####### ####### ######
##        ##   ##         ##   ##      ##   ##
##        ##    #####     ##   ######  ######
##        ##        ##    ##   ##      ##  ##
####### ###### ######     ##   ####### ##   ##
'''

def yield_topic_best_answers(topic_id, limit=100, min_voteup=300, min_thanks=50, 
                             banned_keywords=''):
  ''' banned_keywords: 忽略问题 topic 中具有该关键词的情况, 如 情感, 调查类问题
                       忽略问题 title 中具有该关键词的情况, 如 有哪些, 文艺表达, 文艺的表达, 前女友
  '''
  topic = client.topic(topic_id)
  log(topic.name + str(topic_id))
  count = 0
  if banned_keywords.strip():
    banned_keywords = set(key.strip() for key in banned_keywords.split(','))
  else:
    banned_keywords = set()
  for answer in topic.best_answers:
    # log('yield_topic_best {} {} {}'.format(answer.question.title, answer.author.name, answer.voteup_count))
    if answer.voteup_count >= min_voteup and answer.thanks_count >= min_thanks:
      if set(t.name for t in answer.question.topics) & banned_keywords: 
        log(f'  -- drop {answer.question.title} question.topics in banned_keywords ')
        continue
      if any((key in answer.question.title) for key in banned_keywords): 
        log(f'  -- drop {answer.question.title} question.title in banned_keywords ')
        continue
      count += 1
      yield answer
    if count >= limit:
      break


def yield_old_fashion_topic_answers(topic_id, mode=('all', 'best')[0],
                                    limit=100, min_voteup=300):
  # id = 19641972 # '政治'
  topic = old_client.topic('https://www.zhihu.com/topic/{}'.format(topic_id))
  # top_answers(self): 获取话题下的精华答案 返回生成器
  # answers(self): 获取话题下所有答案（按时间降序排列）返回生成器
  if mode == 'all':
    answers = topic.answers
  elif mode == 'best':
    answers = topic.top_answers
  else:
    raise
  count = 0
  for old_answer in answers:
    answer = client.answer(int(old_answer.id))
    # print(answer.question.title, answer.author.name, answer.id, answer.question.id)
    if answer.voteup_count >= min_voteup:
      count += 1
      yield answer
    if count >= limit:
      break

def yield_author_answers(author_id, limit=100, min_voteup=300, min_thanks=50):
  # url = 'https://www.zhihu.com/people/shi-yidian-ban-98'
  author = client.people(author_id)
  count = 0
  for answer in author.answers:
    if answer.voteup_count >= min_voteup and answer.thanks_count >= min_thanks:
      count += 1
      yield answer
    if count >= limit:
      break


def yield_question_answers(question_id, limit=100, min_voteup=300, min_thanks=50):
  # url = 'https://www.zhihu.com/people/shi-yidian-ban-98'
  question = client.question(question_id)
  count = 0
  for answer in question.answers:
    if answer.voteup_count >= min_voteup and answer.thanks_count >= min_thanks:
      count += 1
      yield answer
    if count >= limit:
      break


def yield_column_articles(column_id, limit=100, min_voteup=20):
  column = client.column(column_id)
  count = 0
  for article in column.articles:
    # print(article.voteup_count)
    if article.voteup_count >= min_voteup:
      count += 1
      yield article
    if count >= limit:
      break


def yield_author_articles(author_id, limit=100, min_voteup=20):
  author = client.people(author_id)
  count = 0
  for article in author.articles:
    if article.voteup_count >= min_voteup :
      count += 1
      yield article
    if count >= limit:
      break


def test_yield_org_articles():
  # author_id = 'di-ping-xian-ji-qi-ren-ji-shu'
  url = 'https://www.zhihu.com/org/di-ping-xian-ji-qi-ren-ji-shu'
  author = client.from_url(url)
  print(author)
  print(author.name)
  ats = list(author.articles)
  print(ats)


def yield_collection_answers(collection_id, limit=100, min_voteup=300, min_thanks=50):
  # 'http://www.zhihu.com/collection/19845840' 我心中的知乎TOP100
  collection = client.collection(collection_id)
  count = 0
  for answer in collection.answers:
    if answer.voteup_count >= min_voteup and answer.thanks_count >= min_thanks:
      count += 1
      yield answer
    if count >= limit:
      break

# def save_from_question(url):
#   question = client.Question(url)
#   print(question.title)
#   # 获取排名前十的十个回答
#   for answer in question.top_i_answers(10):
#     if answer.upvote > 1000:
#       save_answer(answer)









