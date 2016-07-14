

import time
from pylon import puts
from pylon import datalines

import os
import shutil
import html2text
from pylon import enumrange
# import time
import datetime

from zhihu_oauth import ZhihuClient
from zhihu_oauth.zhcls.utils import remove_invalid_char



from jinja2 import Template
import re
from pyquery import PyQuery
import requests

import urllib.request

from pylon import create_logger

log = create_logger(__file__)
class ZhihuParseError(Exception):
  pass




TOKEN_FILE = 'token.pkl'
client = ZhihuClient()
client.load_token(TOKEN_FILE)














# OldZhihuClient 用于 zhihu-py3 cookie 模拟登录
# 到 http://www.zhihu.com/node/AnswerCommentBoxV2?params= 取得评论对象
# 比 API 方式快很多
# 如果不登录获取 cookie, 则在返回结果中看不到具体的作者名字
from zhihu import ZhihuClient as OldZhihuClient
old_client = OldZhihuClient('cookies.json')

def comment_list_id(url):
  """返回 aid 用于拼接 url get 该回答的评论
  <div tabindex="-1" class="zm-item-answer" itemscope="" itemtype="http://schema.org/Answer" data-aid="14852408" data-atoken="48635152" data-collapsed="0" data-created="1432285826" data-deleted="0" data-helpful="1" data-isowner="0" data-score="34.1227812032">
  """
  headers = {
    'User-agent': 'Mozilla/5.0',
  }
  r = old_client._session.get(url)
  return PyQuery(r.content).find('div.zm-item-answer').attr('data-aid')


class OldFashionAuthor:
  """配合 OldFashionComment 使用的 author"""
  def __init__(self, name):
    self.name = name
  def __str__(self):
    return '<OldFashionAuthor {}>'.format(self.name)


class OldFashionComment:
  """
  使用 http://www.zhihu.com/node/AnswerCommentBoxV2?params= 取得的评论对象
  速度比较快
  comment.author.name, reply_to_author, content, vote_count
  """
  def __init__(self, cid, vote_count, author, content, reply_to):
    self.cid = cid
    self.vote_count = vote_count
    self.content = content
    self.author = author
    self.reply_to = reply_to
  def __str__(self):
    s = '<OldFashionComment cid={} vote_count={}\n  author="{}" reply_to="{}">\n  {}'
    return s.format(self.cid, self.vote_count, self.author, self.reply_to, self.content)


def get_old_fashion_comments(answer_url):

  aid = comment_list_id(answer_url)
  comment_box_link = 'http://www.zhihu.com/node/AnswerCommentBoxV2?params=%7B%22answer_id%22%3A%22{}%22%2C%22load_all%22%3Atrue%7D'.format(aid) | log
  r = old_client._session.get(comment_box_link)
  doc = PyQuery(str(r.content, encoding='utf-8'))
  comments = []
  for div in doc.find('div.zm-item-comment'):
    div = PyQuery(div)
    cid = div.attr('data-id')
    vote_count = int(div.find('span.like-num').find('em').text())
    content = div.find('div.zm-comment-content').html()
    author_text = div.find('div.zm-comment-hd').text().replace('\n', ' ')
    if ' 回复 ' in author_text:
      author, reply_to = author_text.split(' 回复 ')
    else:
      author, reply_to = author_text, None

    comment = OldFashionComment(cid=cid,
                                vote_count=vote_count,
                                content=content,
                                author=OldFashionAuthor(author),
                                reply_to=OldFashionAuthor(reply_to) if reply_to else None)
    comments.append(comment)
  return comments













def zhihu_content_html2md(html):
  h2t = html2text.HTML2Text()
  h2t.body_width = 0
  r = h2t.handle(html).strip()
  r = '\n'.join(p.rstrip() for p in r.split('\n'))
  return re.sub('\n{4,}', '\n\n\n', r)


def parse_json_date(n):
  return str(datetime.datetime.fromtimestamp(n))




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
  author = answer.author
  question = answer.question

  try:
    content = answer.content
  except AttributeError:
    msg = 'cannot parse answer.content: {} {}'
    raise ZhihuParseError(msg.format(answer.question.title, answer._build_url()))


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
  question_details = zhihu_content_html2md(question.detail).strip()
  title = question.title + ' - ' + author.name + '的回答'
  topics = ', '.join(t.name for t in question.topics)
  question_id = question.id
  answer_id = answer.id
  count = len(answer_body)
  voteup_count = answer.voteup_count
  thanks_count = answer.thanks_count
  create_date = parse_json_date(answer.created_time)
  edit_date = parse_json_date(answer.updated_time)
  fetch_date = time.strftime('%Y-%m-%d')

  # conversations = get_valuable_conversations(answer.comments, limit=10)

  url = 'https://www.zhihu.com/question/{}/answer/{}'.format(question_id, answer_id)
  conversations = get_valuable_conversations(get_old_fashion_comments(url), limit=10)

  metadata_tmpl = '''
    author: {{author.name}} {{motto}}
    voteup: {{voteup_count}} 赞同
    thanks: {{thanks_count}} 感谢
    create: {{create_date}}
    edit:   {{edit_date}}
    fetch:  {{fetch_date}}
    count:  {{count}} 字
    url:    {{url}}
'''
  metadata = Template(metadata_tmpl).render(**locals())


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

  return {'title': title,
          'content': zhihu_fix_markdown(answer_body).strip(),
          'comments': zhihu_fix_markdown(comments).strip(),
          'author': author.name,
          'topic': topics,
          'question': zhihu_fix_markdown(question_details).strip(),
          'metadata': metadata,
          'url': url,
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


def save_answer(answer, folder='test'):
  answer = parse_answer(answer)

  data = fetch_zhihu_answer(answer=answer)
  save_path = folder + '/' + remove_invalid_char(data['title']) + '.md'


  tmpl = '''
# {{data.title}}

话题: {{data.topic}}

问题描述:

{{data.question}}

{{data.metadata}}


{{data.content}}



　　

评论:

{{data.comments}}

------------------

from: [{{data.url}}]()

'''
  rendered = Template(tmpl).render(**locals())

  with open(save_path, 'w', encoding='utf-8') as f:
    f.write(rendered)
    puts('write save_path done')

  fetch_images_for_markdown(save_path)  # get images in markdown
  return save_path



def fetch_image(url, ext, markdown_file, image_counter):
  '''
  需要区分 全路径 和 相对引用
  需要转换每个 md 的附件名
  需要附件名编号'''
  if '.zhimg.com' not in url:
    print('  exotic url: ', url)
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
    print('  existed: ', url)
    return image_name

  print('    fetching', url)
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
    print('parsing md file done:  ' + markdown_file.split('/')[-1])
  else:
    print('no pictures downloaded:' + markdown_file.split('/')[-1])


from urllib.parse import unquote



def zhihu_fix_markdown(text):
  # 去除 html2text 转换出来的 strong 和 link 的多余空格
  # drop extra space in link syntax
  # eg. [ wikipage ](http://.....) => [wikipage](http://.....)
  # eg2 [http://www.  businessanalysis.cn/por  tal.php ](http://www.businessanalysis.cn/portal.php)
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

  # line = pattern_hyperlink.sub(r'[\1]', line)
  text = pattern_hyperlink.sub(hyperlink_replacer, text)
  text = pattern_strong.sub(replace_strong, text)
  text = pattern_redirect_link.sub(replace_redirect_link, text)
  text = pattern_tex_link.sub('](http://www.zhihu.com/equation?tex=', text)
  return text















def save_from_author(url, folder='test', min_voteup=500, overwrite=False):
  # url = 'http://www.zhihu.com/people/nordenbox'
  # TODO: thread
  author = client.from_url(url)
  # 获取用户名称
  print(author.name, ' - ', author.headline)
  # 获取用户答题数
  print(author.answer_count)      # 227
  for i, answer in enumerate(author.answers):
    if answer.voteup_count < min_voteup:
      continue
    try:
      print(answer._build_url())
      save_answer(answer._build_url(), folder=folder)
    except ZhihuParseError as e:
      print(e)
    except RuntimeError as e:
      print(e, answer.question.title)
    except AttributeError as e:
      print(answer.question.title, answer._build_url(), e)
      raise





def save_from_collections(url, limit=10):
  collection = client.Collection(url)
  print(collection.name)
  print(collection.followers_num)
  for i, answer in enumerate(collection.answers):
    # print(answer._url)
    if i >= limit:
      break

    save_answer(answer._url, folder='test')




def save_from_question(url):
  question = client.Question(url)
  print(question.title)
  # 获取排名前十的十个回答
  for answer in question.top_i_answers(10):
    if answer.upvote > 1000:
      save_answer(answer)





def topic_best_answers(topic_id, limit=100, min_voteup=300):
  # id = 19641972 # '政治'
  topic = client.topic(topic_id)
  # print(topic.name)
  for answer, i in zip(topic.best_answers, range(limit)):
    # print(answer.question.title, answer.author.name, answer.voteup_count)
    if answer.voteup_count >= min_voteup:
      yield answer








def save_from_topic(url, limit=200,
                    min_voteup=1000, max_upvote=100000000,
                    folder='test',
                    overwrite=True):

  if not os.path.exists(folder):
    os.makedirs(folder)

  # topic = client.Topic(url)
  topic = client.from_url(url)

  for i, answer in enumrange(topic.best_answers, limit):
    print('fetching', answer.question.title, ' - ', answer.voteup_count)

    if answer.voteup_count < min_voteup:
      break
    if answer.voteup_count > max_upvote:
      continue

    try:
      save_answer(answer, folder=folder)
    except RuntimeError as e:
      print(e, answer.question.title)
    except TypeError as e:
      print('question_link["href"]', e, answer.question.title)
    # except AttributeError as e:
    #   print('time to long? ', e, question_title)





















####### ##   ## ####### ######
##       ## ##  ##     ###
######    ###   ###### ##
##       ## ##  ##     ###
####### ##   ## ####### ######


def exec_save_from_collections():
  # 采铜 的收藏 我心中的知乎TOP100
  url = 'http://www.zhihu.com/collection/19845840'
  save_from_collections(url, limit=10)



def exec_save_from_authors():
  # url = 'https://www.zhihu.com/people/xbjf/'  # 玄不救非氪不改命
  # save_from_author(url, folder='test', min_voteup=500)
  # url = 'https://www.zhihu.com/people/zhao-hao-yang-1991'  # 赵皓阳
  # save_from_author(url, folder='authors', min_voteup=300)
  url = 'https://www.zhihu.com/people/mandelbrot-11'  # Mandelbrot
  save_from_author(url, folder='test', min_voteup=500)

# exec_save_from_authors()


def exec_save_answers():
  urls = '''
    https://www.zhihu.com/question/40305228/answer/86179116
    https://www.zhihu.com/question/36466762/answer/85475145
    https://www.zhihu.com/question/33246348/answer/86919689
    https://www.zhihu.com/question/39906815/answer/88534869

    https://www.zhihu.com/question/40700155/answer/89002644
    https://www.zhihu.com/question/36380091/answer/84690117
    https://www.zhihu.com/question/33246348/answer/86919689
    https://www.zhihu.com/question/35254746/answer/90252213
    https://www.zhihu.com/question/23618517/answer/89823915

    https://www.zhihu.com/question/40677000/answer/87886574

    https://www.zhihu.com/question/41373242/answer/91417985
    https://www.zhihu.com/question/47275087/answer/106335325
    https://www.zhihu.com/question/47275087/answer/106335325 买不起房是房价太高还是工资太低？
    https://www.zhihu.com/question/36129534/answer/91921682  印度经济会在本世纪追上中国吗？
    https://www.zhihu.com/question/22513722/answer/21967185  火车票涨价是否能解决春运问题？
    https://www.zhihu.com/question/32210508/answer/57701501  蒋兆和《流民图》为何受到批判？
    https://www.zhihu.com/question/27820755/answer/107267228 裸辞后怎样解释以获工作机会？
  '''
  for url in datalines(urls):
    save_answer(url.split(' ')[0], folder='test')




# def exec_save_from_question():
#   urls = '''
#     # graphic design
#     # http://www.zhihu.com/question/19577036
#     # http://www.zhihu.com/question/21578745
#     # http://www.zhihu.com/question/22332149
#     # http://www.zhihu.com/question/21274267
#     # http://www.zhihu.com/question/22332149
#     # http://www.zhihu.com/question/29594460
#     # http://www.zhihu.com/question/27914845
#     # http://www.zhihu.com/question/28529486
#     # http://www.zhihu.com/question/20603867
#     http://www.zhihu.com/question/23914832
#   '''
#   for url in datalines(urls):
#     save_from_question(url)




def exec_save_from_topic():

  urls_str = '''
    # https://www.zhihu.com/topic/19554091 math
    # https://www.zhihu.com/topic/19556950 physics
    # https://www.zhihu.com/topic/19574449 a song of ice and fire
    # https://www.zhihu.com/topic/19556231 interactive design 1000
    # https://www.zhihu.com/topic/19556382 2d design 1000
    # https://www.zhihu.com/topic/19561709 ux design 1000
    # https://www.zhihu.com/topic/19551016 fonts 200
    # https://www.zhihu.com/topic/19553684 layout 100
    # https://www.zhihu.com/topic/19647471 style 100
    # https://www.zhihu.com/topic/19551077 history
    # https://www.zhihu.com/topic/19615699 immanuel_kant
    # https://www.zhihu.com/topic/19551864 classical music
    # https://www.zhihu.com/topic/19552330 programmer
    # https://www.zhihu.com/topic/19554298 programming
    # https://www.zhihu.com/topic/19615699 immanuel_kant

    # https://www.zhihu.com/topic/19563625 astronomy 天文
    # https://www.zhihu.com/topic/19620787 universe 天文
    # https://www.zhihu.com/topic/19569034 philosophy_of_science 科学哲学
    # https://www.zhihu.com/topic/19558740 statistics 统计
    # https://www.zhihu.com/topic/19576422 statistics 统计
    https://www.zhihu.com/topic/19552981 economics 经济
    # https://www.zhihu.com/topic/19553550 paradox 悖论
    # https://www.zhihu.com/topic/19559450 machine_learning 机器学习
    # https://www.zhihu.com/topic/19551275 artificial_intelligence 人工智能
    # https://www.zhihu.com/topic/19553534 data_mining 数据挖掘
    # https://www.zhihu.com/topic/19815465 quantitative_trading 量化交易
    # https://www.zhihu.com/topic/19571159 freelancer 自由职业
  '''

  for line in datalines(urls_str):
    url, topic_name, topic_name_cn = line.split(' ')
    puts('start parsing topic_name url')
    save_from_topic(url, limit=10, min_voteup=1000, max_upvote=5000000, folder=topic_name_cn, overwrite=False)



def exec_massive_download():

  # save_author('http://www.zhihu.com/people/nordenbox')
  urls = '''
    # http://www.zhihu.com/people/leng-zhe
    # http://www.zhihu.com/people/ji-xuan-yi-9
    # http://www.zhihu.com/people/Ivony
    # http://www.zhihu.com/people/BlackCloak

    # http://www.zhihu.com/people/hecaitou
    # http://www.zhihu.com/people/ma-bo-yong

    # http://www.zhihu.com/people/hutianyi
    # http://www.zhihu.com/people/lawrencelry
    # http://www.zhihu.com/people/Metaphox

    # http://www.zhihu.com/people/calon
    # http://www.zhihu.com/people/yolfilm
    # http://www.zhihu.com/people/superwyh
    # http://www.zhihu.com/people/cai-tong
    # http://www.zhihu.com/people/xiepanda




    # http://www.zhihu.com/people/cogito
    # http://www.zhihu.com/people/talich
    # http://www.zhihu.com/people/commando
    # http://www.zhihu.com/people/fu-er

    # http://www.zhihu.com/people/tassandar
    # http://www.zhihu.com/people/fei-niao-bing-he
    # http://www.zhihu.com/people/zhou-xiao-nong
    # http://www.zhihu.com/people/wang-lu-43-95
    # http://www.zhihu.com/people/yinshoufu
    # http://www.zhihu.com/people/tangsyau
    # http://www.zhihu.com/people/lianghai
    # http://www.zhihu.com/people/zhang-jia-wei
    # http://www.zhihu.com/people/bo-cai-28-7

    # all done
  '''

  urls = '''
    http://www.zhihu.com/people/sa-miu-47-86
    http://www.zhihu.com/people/xubowen
  '''


  for url in datalines(urls):
    save_from_author(url, folder='authors_explore', min_voteup=1000)

















####### #######  ###### #######
   ##   ##      ##         ##
   ##   ######   #####     ##
   ##   ##           ##    ##
   ##   ####### ######     ##



def test_answer_banned():
  # 为什么会出现「只有专政才能救中国」的言论？
  # 玄不救非氪不改命，东欧政治与杨幂及王晓晨研究
  # 回答建议修改：不友善内容
  # 作者修改内容通过后，回答会重新显示。如果一周内未得到有效修改，回答会自动折叠。
  url = 'https://www.zhihu.com/question/33594085/answer/74817919/'
  save_answer(url)


def test_save_answer_common():
  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  save_answer('https://www.zhihu.com/question/30595784/answer/49194862')
  # 人们买不起房子是因为房子价格太高，还是因为我们的工资太低？
  save_answer('https://www.zhihu.com/question/47275087/answer/106335325')
  # 如何从头系统地听古典音乐？
  # save_answer('https://www.zhihu.com/question/30957313/answer/50266448')



def test_save_answer_comments():
  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  save_answer('https://www.zhihu.com/question/30595784/answer/49194862')





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
  save_answer('http://www.zhihu.com/question/20087838/answer/25073924')
  save_answer('http://www.zhihu.com/question/20087838/answer/25169641')


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



def test_yield_topic():
  id = 19641972 # '政治'
  topic = client.topic(id)
  print(topic.name)

  i = 0
  for answer in topic.top_answers:
    print(answer.question.title, answer.author.name, answer.voteup_count)
    i += 1
  print(i)



def get_api_json(url='https://api.zhihu.com/answers/94150403'):
  from pprint import pprint
  import json
  r = client.test_api('GET', url)
  # s = str(r.content, encoding='utf-8')
  j = json.loads(str(r.content, encoding='utf-8'))
  pprint(j)



def test_get_html_not_json():
  url='http://www.zhihu.com/node/AnswerCommentBoxV2?params=%7B%22answer_id%22%3A%2227109662%22%2C%22load_all%22%3Atrue%7D'
  client.test_api('GET', url)

  print()















def test_comments_old_fashion():
  # 大偏差技术是什么？
  url = 'https://www.zhihu.com/question/29400357/answer/82408466'
  # 人们买不起房子是因为房子价格太高，还是因为我们的工资太低？
  url = 'https://www.zhihu.com/question/47275087/answer/106335325'

  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  # url = 'https://www.zhihu.com/question/30595784/answer/49194862'
  for c in get_old_fashion_comments(answer_url=url):
    c | log

