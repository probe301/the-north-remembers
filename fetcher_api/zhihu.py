import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import time
import tools
from tools import datalines

import os
import shutil
import html2text


import datetime
from zhihu_oauth import ZhihuClient
from zhihu_oauth.zhcls.utils import remove_invalid_char
from zhihu_oauth.exception import GetDataErrorException
from urllib.parse import unquote



from jinja2 import Template
import re
from pyquery import PyQuery
import requests

import urllib.request

from tools import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')


class ZhihuParseError(Exception):
  def __init__(self, msg=None, value=None):
    self.value = value
    self.msg = msg



TOKEN_FILE = 'token.pkl'
client = ZhihuClient()
client.load_token(TOKEN_FILE)




def zhihu_detect(url):
  UA = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.13 Safari/537.36"
  headers = { "User-Agent" : UA,
              "Referer": "https://zhuanlan.zhihu.com/"}

  session = requests.Session()
  return session.get(url, headers=headers)



def zhihu_answer_url(answer):
  '''貌似答案被删也不报错'''
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
  return '<ZhihuAnswer {title} by {author} ({vote}赞) {topic}>\n{url}'.format(**locals())

def zhihu_answer_title(answer):
  return answer.question.title + ' - ' + answer.author.name + '的回答'











# '''
#  #####  ##      ######
# ##   ## ##      ##   ##
# ##   ## ##      ##   ##
# ##   ## ##      ##   ##
#  #####  ####### ######

#  ###### #####  ##   ## ##   ## ####### ##   ## #######
# ###    ##   ## ### ### ### ### ##      ###  ##    ##
# ##     ##   ## ## # ## ## # ## ######  ## # ##    ##
# ###    ##   ## ##   ## ##   ## ##      ##  ###    ##
#  ###### #####  ##   ## ##   ## ####### ##   ##    ##
# '''
# # OldZhihuClient 用于 zhihu-py3 cookie 模拟登录
# # 到 http://www.zhihu.com/node/AnswerCommentBoxV2?params= 取得评论对象
# # 比 API 方式快很多
# # 如果不登录获取 cookie, 则在返回结果中看不到具体的作者名字
# # from zhihu import ZhihuClient as OldZhihuClient
# # old_client = OldZhihuClient('cookies.json')

# def comment_list_id(url):
#   """返回 aid 用于拼接 url get 该回答的评论
#   <div tabindex="-1" class="zm-item-answer" itemscope="" itemtype="http://schema.org/Answer" data-aid="14852408" data-atoken="48635152" data-collapsed="0" data-created="1432285826" data-deleted="0" data-helpful="1" data-isowner="0" data-score="34.1227812032">

#   某些页面仅在登录后 才能取得 comment_list_id, 否则会进入 login 页面找不到该 id
#   可能跟答主允许站外分享有关
#   # client = ZhihuClient()
#   # client.create_cookies('cookies.json')
#   """

#   headers = {
#     'User-agent': 'Mozilla/5.0',
#   }
#   # print(url)
#   r = old_client._session.get(url, headers=headers)
#   aid = PyQuery(r.content).find('div.zm-item-answer').attr('data-aid')
#   if aid:
#     return aid
#   else:
#     log_error(url + ' can not find aid in\n')
#     log_error(r.content)
#     raise ValueError

# class OldFashionAuthor:
#   """配合 OldFashionComment 使用的 author"""
#   def __init__(self, name):
#     self.name = name
#   def __str__(self):
#     return '<OldFashionAuthor {}>'.format(self.name)


# class OldFashionComment:
#   """
#   使用 http://www.zhihu.com/node/AnswerCommentBoxV2?params= 取得的评论对象
#   速度比较快
#   comment.author.name, reply_to_author, content, vote_count
#   """
#   def __init__(self, cid, vote_count, author, content, reply_to):
#     self.cid = cid
#     self.vote_count = vote_count
#     self.content = content
#     self.author = author
#     self.reply_to = reply_to
#   def __str__(self):
#     s = '<OldFashionComment cid={} vote_count={}\n  author="{}" reply_to="{}">\n  {}'
#     return s.format(self.cid, self.vote_count, self.author, self.reply_to, self.content)


# def get_old_fashion_comments(answer_url):
#   aid = comment_list_id(answer_url)
#   comment_box_link = 'http://www.zhihu.com/node/AnswerCommentBoxV2?params=%7B%22answer_id%22%3A%22{}%22%2C%22load_all%22%3Atrue%7D'.format(aid)  # | log
#   # log('comments: ' + comment_box_link)
#   r = old_client._session.get(comment_box_link)
#   # print(str(r.content))
#   doc = PyQuery(str(r.content, encoding='utf-8'))
#   comments = []
#   for div in doc.find('div.zm-item-comment'):
#     div = PyQuery(div)
#     cid = div.attr('data-id')
#     vote_count = int(div.find('span.like-num').find('em').text())
#     content = div.find('div.zm-comment-content').html()
#     author_text = div.find('div.zm-comment-hd').text().replace('\n', ' ')
#     if ' 回复 ' in author_text:
#       author, reply_to = author_text.split(' 回复 ')
#     else:
#       author, reply_to = author_text, None

#     comment = OldFashionComment(cid=cid,
#                                 vote_count=vote_count,
#                                 content=content,
#                                 author=OldFashionAuthor(author),
#                                 reply_to=OldFashionAuthor(reply_to) if reply_to else None)
#     comments.append(comment)
#   return comments


class FakeAuthor:
  def __init__(self):
    self.name = '[匿名用户]'
    self.headline = ''


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






















def fetch_zhihu_answer(answer):
  answer = parse_answer(answer)

  try:
    author = answer.author
    if author is None:
      # 如果匿名, 现在返回 None, 需要 fix 为一个 AuthorObject
      author = FakeAuthor()
  except (requests.exceptions.RetryError, GetDataErrorException) as e:
    # 回答已被删除? 目前分不清怎么判断 回答or问题 被删
    blank_answer = blank_zhihu_answer()
    blank_answer['title'] = '(本回答已删除)' # + answer.question.title
    # blank_answer['url'] = zhihu_answer_url(answer)
    raise ZhihuParseError(msg='本回答已删除', value=blank_answer)

  try:
    question = answer.question
    detail = question.detail
  except GetDataErrorException as e:
    # zhihu_oauth.exception.GetDataErrorException:
    # A error happened when get data: 问题不存在
    blank_answer = blank_zhihu_answer()
    blank_answer['title'] = '(问题已删除)' + answer.question.title
    blank_answer['url'] = zhihu_answer_url(answer)
    raise ZhihuParseError(msg='问题已删除', value=blank_answer)
  try:
    content = answer.content
  except requests.exceptions.RetryError as e:
    # 一般是问题已被删除
    blank_answer = blank_zhihu_answer()
    blank_answer['title'] = '(问题已删除)' + answer.question.title
    blank_answer['url'] = zhihu_answer_url(answer)
    raise ZhihuParseError(msg='问题已删除', value=blank_answer)


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
  answer_id = answer.id
  count = len(answer_body)
  voteup_count = answer.voteup_count
  thanks_count = answer.thanks_count
  create_date = parse_json_date(answer.created_time)
  edit_date = parse_json_date(answer.updated_time)
  fetch_date = tools.time_now_str()


  url = 'https://www.zhihu.com/question/{}/answer/{}'.format(question_id, answer_id)
  # TODO redo comments 

  try:
    conversations = get_valuable_conversations(answer.comments, limit=10)
    # conversations = get_valuable_conversations(get_old_fashion_comments(url), limit=10)
  except (requests.exceptions.RetryError) as e:
    resp_json = zhihu_detect(answer.comments._url).json()
    if 'error' in resp_json:
      conversations = [ [
        '错误: {name} - {code} - {message}'.format(**resp_json['error'])
      ], ]


  metadata = {
    'title': title, 
    'topics': topics, 
    'author_name': author.name,
    'author_id': author.__dict__['_cache']['url_token'],
    'voteup_count': voteup_count,
    'thanks_count': thanks_count,
    'create_date': create_date,
    'edit_date':   edit_date,
    'fetch_date':  fetch_date,
    'count':  count,
    'url': url,
  }


  comments_tmpl = '''
{% if conversations %}
{% for conversation in conversations %}
{%- for comment in conversation %}
{{comment}}
{% endfor %}
　　
{% endfor %}
{% endif %}
'''
  comments = Template(comments_tmpl).render(**locals())

  return { 'metadata': metadata,
           'question': zhihu_fix_markdown(question_details).strip(),
           'answer': zhihu_fix_markdown(answer_body).strip(),
           'comments': zhihu_fix_markdown(comments).strip(),
          }


def blank_zhihu_answer():
  return {'title': '',
          'content': '',
          'comments': '',
          'author': '',
          'topic': '',
          'question': '',
          'metadata': '',
          'url': '',
          }






def parse_answer(answer):
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



def save_answer(answer, folder='test', overwrite=True):
  answer = parse_answer(answer)
  author = answer.author
  if author is None:
    # 如果匿名, 现在返回 None, 需要 fix 为一个 AuthorObject
    author = FakeAuthor()
  title = answer.question.title + ' - ' + author.name + '的回答'
  save_path = folder + '/' + remove_invalid_char(title) + '.md'
  if not overwrite:
    if os.path.exists(save_path):
      log('already exist {}'.format(save_path))
      return save_path

  data = fetch_zhihu_answer(answer=answer)
  rendered = fill_full_content(data)

  with open(save_path, 'w', encoding='utf-8') as f:
    f.write(rendered)
    log('write {} done'.format(save_path))

  # 本地存储, 需要抓取所有附图
  # TODO fetch_images_for_markdown(save_path)
  return save_path










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
  author_name = article.author.name if article.author else FakeAuthor().name
  vote = article.voteup_count
  column = article.column.title if article.column else '无专栏'
  return '<ZhihuArticle {title} ({column}) by {author_name} ({vote}赞)>\n{url}'.format(**locals())

def zhihu_article_url(article):
  # https://zhuanlan.zhihu.com/p/22197924
  if isinstance(article, int):
    return 'https://zhuanlan.zhihu.com/p/{}'.format(article)
  return 'https://zhuanlan.zhihu.com/p/{}'.format(article.id)

def zhihu_article_title(article):
  title = article.title
  author_name = article.author.name if article.author else FakeAuthor().name
  column = article.column.title if article.column else ''
  return '{title} - {author_name}的专栏 {column}'.format(**locals()).strip()

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

def fetch_zhihu_article(article):
  article = parse_article(article)

  try:
    author = article.author
  except (requests.exceptions.RetryError, GetDataErrorException) as e:
    # 文章已被删除
    blank_article = blank_zhihu_answer()
    blank_article['title'] = '(本文章已删除)'
    raise ZhihuParseError(msg='本文章已删除', value=blank_article)

  content = article.content

  # try:  # 未观察到文章被删的情况, 暂时不适用 try except
  #   author = article.author
  # except requests.exceptions.RetryError as e:
  #   blank_article = blank_zhihu_article()
  #   blank_article['title'] = '(本文章已删除)' # + article.question.title
  #   raise ZhihuParseError(msg='本文章已删除', value=blank_article)
  # try:
  #   question = article.question
  #   content = article.content
  #   detail = question.detail
  # except requests.exceptions.RetryError as e:
  #   blank_article = blank_zhihu_answer() # reuse blank answer
  #   blank_article['title'] = '(文章已删除)' + article.question.title
  #   blank_article['url'] = zhihu_article_url(article)
  #   raise ZhihuParseError(msg='文章已删除', value=blank_article)

  article_body = zhihu_content_html2md(content).strip()
  if article.suggest_edit.status:
    article_body += '\n' + article.suggest_edit.reason + '\n' + article.suggest_edit.tip

  if article.image_url:
    # https://pic4.zhimg.com/50/d58be60ea916b5c231e72e790dc71b33_hd.jpg
    # 需要fix为
    # https://pic4.zhimg.com/d58be60ea916b5c231e72e790dc71b33_hd.jpg
    # 否则白色背景会显示为黑色背景
    img_url = article.image_url.replace('.zhimg.com/50/', '.zhimg.com/')
    article_body = '![]({})\n\n'.format(img_url) + article_body

  motto = '({})'.format(author.headline) if author.headline else ''
  motto = motto.replace('\n', ' ')

  title = zhihu_article_title(article)


  count = len(article_body)
  voteup_count = article.voteup_count
  edit_date = parse_json_date(article.updated_time)
  fetch_date = tools.time_now_str()
  url = zhihu_article_url(article)
  # log(list(article.comments))

  try:
    conversations = get_valuable_conversations(article.comments, limit=10)
    # conversations = get_valuable_conversations(get_old_fashion_comments(url), limit=10)
  except (requests.exceptions.RetryError) as e:
    resp_json = zhihu_detect(article.comments._url).json()
    if 'error' in resp_json:
      conversations = [ [
        '错误: {name} - {code} - {message}'.format(**resp_json['error'])
      ], ]

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


  comments_tmpl = '''
{% if conversations %}
{% for conversation in conversations %}
{%- for comment in conversation %}
{{comment}}
{% endfor %}
　　
{% endfor %}
{% endif %}
'''
  comments = Template(comments_tmpl).render(**locals())

  return { 'metadata': metadata,
           'content': zhihu_fix_markdown(article_body).strip(),
           'comments': zhihu_fix_markdown(comments).strip(),
         }



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
  from pylon import all_files

  root = 'D:/ZhihuEpub/统计学/'
  for md in all_files(root, '*.md'):
    # print(md)
    text = open(md, encoding='utf8').read()

    text_new = zhihu_fix_mistake_headerline_splitter(text)

    if text_new != text:
      with open(md, 'w', encoding='utf8') as f:
        f.write(text_new)

      print('write on ' + md)











'''
##   ## ###### ####### ##      ######
##   ##   ##   ##      ##      ##   ##
 #####    ##   ######  ##      ##   ##
   ##     ##   ##      ##      ##   ##
   ##   ###### ####### ####### ######
'''

def yield_topic_best_answers(topic_id, limit=100, min_voteup=300, min_thanks=50):
  # id = 19641972 # '政治'
  topic = client.topic(topic_id)
  log(topic.name + str(topic_id))
  count = 0
  for answer in topic.best_answers:
    # log('yield_topic_best {} {} {}'.format(answer.question.title, answer.author.name, answer.voteup_count))
    if answer.voteup_count >= min_voteup and answer.thanks_count >= min_thanks:
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


























































'''
####### #######  ###### #######
   ##   ##      ##         ##
   ##   ######   #####     ##
   ##   ##           ##    ##
   ##   ####### ######     ##
'''


def test_answer_banned():
  # 为什么会出现「只有专政才能救中国」的言论？
  # 玄不救非氪不改命，东欧政治与杨幂及王晓晨研究
  # 回答建议修改：不友善内容
  # 作者修改内容通过后，回答会重新显示。如果一周内未得到有效修改，回答会自动折叠。
  url = 'https://www.zhihu.com/question/33594085/answer/74817919/'
  save_answer(url)


def test_comments_dispaired():
  # 近日河北邢台水淹村庄事件到底是天灾还是人祸？不做键盘侠，谁能给个真实的新闻？ - 玄不救非氪不改命
  # old_fashion_comments url 返回 b''
  url = 'https://www.zhihu.com/question/48793565/answer/112968110'
  answer = parse_answer(url)
  print(answer)
  # print(answer.question.title)
  # print(answer.content)
  # print(answer.comments)
  # print(list(answer.comments))
  c = get_old_fashion_comments(url)

def untest_404():
  url = 'https://www.zhihu.com/question/44069719/answer/97020803' # ???


def test_save_answer_image_url_should_on_newline():
  # 互联网领域的「用户研究」有哪些有趣的发现？ - 采铜的回答
  url = 'https://www.zhihu.com/question/42201108/answer/94323448'
  save_answer(url)

def test_save_answer_common():
  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  # save_answer('https://www.zhihu.com/question/30595784/answer/49194862')
  # 人们买不起房子是因为房子价格太高，还是因为我们的工资太低？
  save_answer('https://www.zhihu.com/question/47275087/answer/106335325')
  # 如何从头系统地听古典音乐？
  # save_answer('https://www.zhihu.com/question/30957313/answer/50266448')



def test_save_answer_comments():
  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  save_answer('https://www.zhihu.com/question/30595784/answer/49194862')


def test_save_answer_comments():
  save_answer('https://www.zhihu.com/question/30276520/answer/314587618')





def test_save_answer_save_jpg_png_images():
  # 人类是否能想象出多维空间的形态？
  save_answer('https://www.zhihu.com/question/29324865/answer/45647794')


def test_save_answer_latex():
  # 大偏差技术是什么？
  save_answer('https://www.zhihu.com/question/29400357/answer/82408466')
  # save_answer('https://www.zhihu.com/question/34961425/answer/80970102')
  save_answer('https://www.zhihu.com/question/34961425/answer/74576898')


def test_save_answer_drop_redirect_links():
  # 大偏差技术是什么？
  # save_answer('https://www.zhihu.com/question/29400357/answer/82408466')
  # 人们买不起房子是因为房子价格太高，还是因为我们的工资太低？
  save_answer('https://www.zhihu.com/question/47275087/answer/106335325')
  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  # save_answer('https://www.zhihu.com/question/30595784/answer/49194862')



def test_save_anonymous():
  # 辜鸿铭的英语学习方法有效吗？为什么？
  # save_answer('http://www.zhihu.com/question/20087838/answer/25073924')
  save_answer('http://www.zhihu.com/question/20087838/answer/25169641')
  # url = 'https://www.zhihu.com/question/21082351/answer/126177114'
  # url = 'https://www.zhihu.com/question/46343014/answer/101244285'
  # save_answer(url)




def test_save_should_trim_link_url_whitespace():
  # 如何追回参与高利贷而造成的损失？
  save_answer('http://www.zhihu.com/question/30787121/answer/49480841')
  # 热门的数据挖掘的论坛、社区有哪些？
  save_answer('https://www.zhihu.com/question/20142515/answer/15215875')
  # 金融专业学生应该学编程语言吗，学什么语言好呢？
  save_answer('https://www.zhihu.com/question/33554217/answer/57561928')
  # 如果太阳系是一个双恒星的星系，那地球应该是什么样的运转轨道，地球人的生活会是什么样的？
  save_answer('https://www.zhihu.com/question/38860589/answer/79205923')



def test_save_whitedot_bug():
  # QQ 的登录封面（QQ印象）是怎么设计的？
  url = 'http://www.zhihu.com/question/22497026/answer/21551914/'
  # answer = zhihu.Answer(url)
  # print(answer)
  # print(answer.content)
  save_answer(url)






def test_yield_answers_by_author():
  url = 'https://www.zhihu.com/people/shi-yidian-ban-98'
  author = client.from_url(url)
  author = client.people('shi-yidian-ban-98')

  log(author.name)
  i = 0
  for answer in author.answers:
    print(answer.question.title, answer.author.name, answer.voteup_count)
    i += 1
  print(i)




def test_get_api_json():
  url = 'https://api.zhihu.com/answers/94150403'
  url = 'https://api.zhihu.com/answers/101244285'
  from pprint import pprint
  import json
  r = client.test_api('GET', url)
  # s = str(r.content, encoding='utf-8')
  j = json.loads(str(r.content, encoding='utf-8'))
  pprint(j)




def load_json_file(path):
  from pprint import pprint
  import json
  j = json.loads(open(path, encoding='utf-8').read())
  pprint(j)



def test_load_json_file():
  path = 'test_book/book.json'

  load_json_file(path)









def test_comments_old_fashion():
  # 大偏差技术是什么？
  url = 'https://www.zhihu.com/question/29400357/answer/82408466'
  # 人们买不起房子是因为房子价格太高，还是因为我们的工资太低？
  url = 'https://www.zhihu.com/question/47275087/answer/106335325'

  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  # url = 'https://www.zhihu.com/question/30595784/answer/49194862'
  for c in get_old_fashion_comments(answer_url=url):
    c | log



def test_yield_old_topic():
  id = 19641972 # 货币政策
  id = 19576422 # 统计
  id = 19558740 # 统计学
  answers = yield_old_fashion_topic_answers(topic_id=id, mode='best', limit=300, min_voteup=500)
  for answer in answers:
    log(zhihu_answer_format(answer))





def test_fetch_articles_by_column():
  column_id = 'learningtheory'
  column_id = 'qbitai'
  column_id = 'leanreact'
  column = client.column(column_id)
  for a in column.articles:
    log(a.title + ' - ' + a.column.title)
    save_article(a)




def test_fetch_articles():
  # url = 'https://www.zhihu.com/people/chenqin'
  author_id = 'chenqin'
  author_id = 'liang-zi-wei-48'
  author_id = 'qbitai'

  author = client.people(author_id)
  log(author.name)

  for a in author.articles:
    if a.column:
      log(a.title + ' - ' + a.column.title)
    else:
      log(a.title + ' - ' + 'None')
    save_article(a)

  # log('------------')
  # for c in author.columns:
  #   log(c.title)
  # smart_save(url, folder=None, limit=4000, min_voteup=500, overwrite=False)



def test_fetch_one_article():
  # url = 'https://zhuanlan.zhihu.com/p/19598346'
  # https://zhuanlan.zhihu.com/p/22197924
  # article = client.article(19598346) # 设计一只蘑菇 - 傅渥成 生命的设计原则
  # article = client.article(19610634) # 穿过黑箱的数据
  # article = client.article(19950456) # 警惕人工智能
  # article = client.article(19837940) # 二十四条逻辑谬误
  # article = client.article(20684541) # 俄罗斯 | 没人扎堆的博物馆
  # article = client.article(21586417) # 不同的调有什么区别？
  article = client.article(29435406) # 浅析 Hinton 最近提出的 Capsule 计划
  article = client.article(31809930) # 浅述：从 Minimax 到 AlphaZero，完全信息博弈之路（1）
  # article = client.article(20361844) # 对位法入门

  # article = client.article(19950456)
  # article = client.article(22197924) # 明天究竟有多远——怎么加总贴现率
  log(article.image_url)
  # print(zhihu_article_format(article))


  save_article(article)
  # log(fetch_zhihu_article(article))
  # log(article.title)
  # log(article.author.name)
  # # log(article.topics)
  # log(article.column.title)
  # log(article.voteup_count)
  # log(zhihu_content_html2md(article.content))
  # for comment in article.comments:
  #   log(comment.author.name + ': ' + comment.content)
  #   log('\n')




def test_article_howto_fetch_quick_comments():
  # article = client.article(19598346) # 设计一只蘑菇 - 傅渥成 生命的设计原则
  # article = client.article(19610634) # 穿过黑箱的数据
  # article = client.article(19950456) # 警惕人工智能

  # print(zhihu_article_format(article))
  # DEBUG: "GET /articles/19950456/comments?limit=20&offset=120
  from pprint import pprint
  import json
  url = 'https://api.zhihu.com/articles/19950456/comments?limit=40'
  r = client.test_api('GET', url)
  # s = str(r.content, encoding='utf-8')
  j = json.loads(str(r.content, encoding='utf-8'))
  pprint(j)


def test_yield_column_by_id():
  cid = 'wontfallinyourlap'
  for article in yield_column_articles(cid):
    log(article.title)



def test_genenate_figlet():
  from pylon import generate_figlet
  generate_figlet('yield', fonts=['space_op'])
  generate_figlet('save', fonts=['space_op'])
  generate_figlet('fix md', fonts=['space_op'])
  generate_figlet('article', fonts=['space_op'])



def test_file_fetch_images_zhuanlan():
  file = 'D:/TheNorthRemembers/more/我们在地球这颗小小的蓝星上都留下过怎样的痕迹 - More的专栏 Voicer.md'
  # file = 'D:/TheNorthRemembers/more/国家版戴维斯双杀 - 许哲的专栏 天上不会掉馅饼.md'
  # TODO fetch_images_for_markdown(file)


def test_https_image():
  path = 'https://pic4.zhimg.com/fd40c5cc4e662895b57f5c4132fa54b7_b.jpg'
  r = requests.get(path)
  log(r.content)


def test_https_image_tls():
  pass


def test_fetch_articles():
  # url = 'https://www.zhihu.com/people/chenqin'
  author_id = 'chenqin'
  # author_id = 'liang-zi-wei-48'
  # author_id = 'qbitai'

  author = client.people(author_id)
  log(author.name)

  for a in author.articles:
    if a.column:
      log(a.title + ' - ' + a.column.title)
    else:
      log(a.title + ' - ' + 'None')
    save_article(a)

  # log('------------')
  # for c in author.columns:
  #   log(c.title)
  # smart_save(url, folder=None, limit=4000, min_voteup=500, overwrite=False)
