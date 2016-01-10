

import time
from pylon import puts
from pylon import datalines
from pylon import all_files
import os
import shutil
from datetime import datetime




from zhihu import ZhihuClient, ActType


import re

import urllib.request





def generate_cookie():
  # po....@gmail.com p...
  ZhihuClient().create_cookies('cookies.json')
# generate_cookie()



def test_time():
  print(time.strftime('%Y-%m-%d'))



COOKIES_FILE = 'cookies.json'
client = ZhihuClient(COOKIES_FILE)



def test_new_zhihu():
  url = 'https://www.zhihu.com/question/30957313/answer/50266448'
  answer = client.answer(url) | puts()
  answer.author | puts()
  answer.collect_num | puts()
  answer.upvote_num | puts()
  answer.content | puts()
  for c in list(answer.comments):
    (c.author.name, c.content) | puts()











def test_html2text():
  import html2text
  h = html2text.HTML2Text()
  # h.ignore_links = True
  print(h.handle("<p>Hello, <a href='http://earth.google.com/'>world</a>!"))

  import html2text
  h2t = html2text.HTML2Text()
  h2t.body_width = 0

  html = '11111111<br>222222<br><br><br><br>3333333'
  a = h2t.handle(html)
  puts('a=')
  b = h2t_handle_html(html)
  puts('b=')
  # print(html.split('\n'))
  # print('\n'.join(p for p in html.split('\n')))
  # print('\n'.join(p.rstrip() for p in html.split('\n')))
  # print(h2t_handle_html(html))




def done_test_fix_img():
  import html2text
  h2t = html2text.HTML2Text()
  h2t.body_width = 0
  # 'http://zhuanlan.zhihu.com/xiepanda'
  # url = 'http://www.zhihu.com/question/30595784/answer/49194862'
  # url = 'http://www.zhihu.com/question/19622414/answer/19798844'
  # url = 'http://www.zhihu.com/question/24413365/answer/27857112'
  url = 'http://www.zhihu.com/question/23039503/answer/48635152'
  answer = zhihu.Answer(url)
  content = answer.content
  answer_body = h2t.handle(content)
  puts('answer content= answer_body=')



def h2t_handle_html(html):
  import html2text
  h2t = html2text.HTML2Text()
  h2t.body_width = 0
  return '\n'.join(p.rstrip() for p in h2t.handle(html).strip().split('\n'))



def markdown_prettify(path, prefix=''):
  import re
  with open(path, encoding='utf-8') as f:
    lines = f.readlines()

  pattern_hyperlink = re.compile(r'\[ (.+?) \](?=\(.+?\))')
  pattern_strong = re.compile(r'\*\* (.+?) \*\*')
  replace = lambda m: '** 回复 **' if m.group(1) == '回复' else '**'+m.group(1)+'**'

  for i, line in enumerate(lines):
    if not ('[' in line or '**' in line):
      continue
    line = pattern_hyperlink.sub(r'[\1]', line)
    line = pattern_strong.sub(replace, line)
    lines[i] = line

  with open(prefix + path, 'w', encoding='utf-8') as f2:
    f2.writelines(lines)



def save_answer(answer, folder='test'):

  # 'http://zhuanlan.zhihu.com/xiepanda'
  # url = 'http://www.zhihu.com/question/30595784/answer/49194862'
  # url = 'http://www.zhihu.com/question/19622414/answer/19798844'
  # url = 'http://www.zhihu.com/question/24413365/answer/27857112'
  # url = 'http://www.zhihu.com/question/23039503/answer/48635152'
  if isinstance(answer, str):
    answer = client.Answer(answer)
  author = answer.author
  question = answer.question
  # print(answer.content)
  # raise
  answer_body = h2t_handle_html(answer.content)
  # print(answer_body)
  text = '# {}\n\n'.format(question.title)

  text += '**话题**: {}\n\n'.format(', '.join(question.topics))


  details = h2t_handle_html(question.details).strip()
  if details:
    text += '**补充描述**: \n\n'
    text += details
    text += '\n\n'

  motto = ' ({})'.format(author.motto) if author.motto else ''
  # create_date, edit_date = answer.creation_time
  create_date = answer.creation_time
  text += '    author:      {}{}\n'.format(author.name, motto)
  text += '    upvote:      {} 赞同\n'.format(answer.upvote_num)
  text += '    count:       {} 字\n'.format(len(answer_body))
  text += '    create_date: {}\n'.format(create_date)
  # if edit_date:
  #   text += '    edit_date:   {}\n'.format(edit_date)
  text += '    fetch_date:  {}\n'.format(time.strftime('%Y-%m-%d'))
  text += '    link:        {}\n\n'.format(answer.url)


  text += answer_body

  # conversations = answer.valuable_conversations(min_likes=20)
  conversations = None
  if conversations:
    text += '\n\n　　\n\n### 评论\n\n'
    for i, conversation in enumerate(conversations):
      if i > 0:
        text += '　　\n\n'
      for comment in conversation:
        reply_to_author = ' 回复 **{}**'.format(comment.reply_to) if comment.reply_to else ''
        likes = '  ({} 赞)'.format(comment.likes) if comment.likes else ''
        content = h2t_handle_html(comment.content)
        if '\n' in content:
          content = '\n\n' + content
        # print(content)
        text += '**{}**{}: {} {}\n\n'.format(comment.author, reply_to_author, content, likes)


  text += '\n\n　　\n\n--------------\n'
  text += 'from: [{}]()\n'.format(answer.url)
  from zhihu.common import remove_invalid_char
  path = folder + '/' + remove_invalid_char(question.title + ' - ' + author.name + '的回答.md')
  with open(path, 'w') as f:
    f.write(text)
    puts('write path done')

  markdown_prettify(path)  # 去除 html2text 转换出来的 strong 和 link 的多余空格
  return path








def test_save_answer():
  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  save_answer('https://www.zhihu.com/question/30595784/answer/49194862')
  # 如何从头系统地听古典音乐？
  save_answer('https://www.zhihu.com/question/30957313/answer/50266448')

  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  # save_answer('http://www.zhihu.com/question/19598964/answer/49293435')

  # # 你会带哪三本书穿越回到北宋熙宁二年？
  # save_answer('http://www.zhihu.com/question/25569054/answer/31213671')


def test_save_anonymous():
  # 辜鸿铭的英语学习方法有效吗？为什么？
  save_answer('http://www.zhihu.com/question/20087838/answer/25073924')
  save_answer('http://www.zhihu.com/question/20087838/answer/25169641')


def test_save_href_bug():
  # 如何追回参与高利贷而造成的损失？
  save_answer('http://www.zhihu.com/question/30787121/answer/49480841')


def test_save_whitedot_bug():
  # QQ 的登录封面（QQ印象）是怎么设计的？
  url = 'http://www.zhihu.com/question/22497026/answer/21551914/'
  # answer = zhihu.Answer(url)
  # print(answer)
  # print(answer.content)
  save_answer(url)



def test_hehe1():
  print(111)












def fetch_image(url, markdown_file, image_counter):
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
  image_fullname = folder + '/' + basename + image_index + '.jpg'
  image_name = basename + image_index + '.jpg'

  # print('image_fullname', image_fullname)
  # print('image_name', image_name)

  if os.path.exists(image_fullname):
    print('  existed: ', url)
    return image_name

  print('    fetching', url)
  data = urllib.request.urlopen(url).read()
  with open(image_fullname, "wb") as f:
    f.write(data)
  return image_name


def fetch_images_for_markdown_file(markdown_file):
  with open(markdown_file, 'r', encoding='utf-8') as f:
    text = f.read()

  if 'whitedot.jpg' in text:
    print("'whitedot.jpg' in text")
    if not markdown_file.endswith('whitedot'):
      shutil.move(markdown_file, markdown_file + '.whitedot')
    return False

  print('start parsing md file: ' + markdown_file.split('/')[-1])
  image_counter = []
  replacer = lambda m: fetch_image(url=m.group(0), markdown_file=markdown_file, image_counter=image_counter)
  text2, n = re.subn(r'(http://pic[^()]+\.jpg)', replacer, text)
  if n > 0:
    with open(markdown_file, 'w', encoding='utf-8') as f:
      f.write(text2)
    print('parsing md file done:  ' + markdown_file.split('/')[-1])
  else:
    print('no pictures downloaded:' + markdown_file.split('/')[-1])


def test_fetch_images_for_markdown_file():
  # QQ 的登录封面（QQ印象）是怎么设计的？
  url = 'http://www.zhihu.com/question/22497026/answer/21551914/'
  save_answer(url)
  markdown_file = '/Users/probe/git/zhihumark/test/QQ 的登录封面（QQ印象）是怎么设计的？ - 傅仲的回答.md'
  fetch_images_for_markdown_file(markdown_file)

  # path = '/Users/probe/git/zhihumark/test'
  # # i = 0
  # for markdown_file in all_files(path, patterns='*.md'):
  #   # i += 1
  #   # if i > 5:
  #   #   break

  #   print(markdown_file)
  #   fetch_images_for_markdown_file(markdown_file)

















def save_from_author(url, folder='test', min_upvote=500):
  # url = 'http://www.zhihu.com/people/nordenbox'
  author = zhihu.Author(url)
  # 获取用户名称
  print(author.name)
  # 获取用户介绍
  print(author.motto)
  # 获取用户答题数
  print(author.answers_num)      # 227
  for i, answer in enumerate(author.answers):
    # if i > 20:
    #   break
    if answer.upvote < min_upvote:
      break

    try:
      save_answer(answer, folder=folder)
    except RuntimeError as e:
      print(e, answer.question.title)


def test_download():

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
    save_from_author(url, folder='authors_explore', min_upvote=1000)


# test_download()


def test_comment():
  import html2text
  h2t = html2text.HTML2Text()
  h2t.body_width = 0

  url = 'http://www.zhihu.com/question/30557155/answer/49730622'
  url = 'http://www.zhihu.com/question/27794207/answer/46866751'

  answer = zhihu.Answer(url)
  # content = answer.content
  # puts(content)
  aid = answer.comment_list_id
  puts(aid)
  for comment in answer.comments:
    print(comment)

  puts('valuable_comments-------')
  for comment in answer.valuable_comments():
    print(comment)

  # answer_body = h2t.handle(content)
  # puts('answer answer_body=')











def save_from_collections(url, limit=10):
  collection = zhihu.Collection(url)
  print(collection.name)
  print(collection.followers_num)
  for i, answer in enumerate(collection.answers):
    # print(answer._url)
    if i >= limit:
      break

    save_answer(answer._url, folder='test')


def test_do_save_from_collections():
  #  采铜 的收藏 我心中的知乎TOP100
  url = 'http://www.zhihu.com/collection/19845840'
  save_from_collections(url, limit=10)



def save_from_question(url):
  question = zhihu.Question(url)
  print(question.title)
  # 获取排名前十的十个回答
  for answer in question.top_i_answers(10):
    if answer.upvote > 1000:
      save_answer(answer)



def test_do_save_from_question():
  urls = '''
    # graphic design
    # http://www.zhihu.com/question/19577036
    # http://www.zhihu.com/question/21578745
    # http://www.zhihu.com/question/22332149
    # http://www.zhihu.com/question/21274267
    # http://www.zhihu.com/question/22332149

    # http://www.zhihu.com/question/29594460
    # http://www.zhihu.com/question/27914845
    # http://www.zhihu.com/question/28529486
    # http://www.zhihu.com/question/20603867

    http://www.zhihu.com/question/23914832
  '''
  for url in datalines(urls):
    save_from_question(url)




def save_from_topic(url, min_upvote=1000, max_upvote=100000000, folder='test'):
  topic = zhihu.Topic(url)
  print('name', topic.name, 'pages', topic.page_number)

  for answer, upvote, question_title, from_sub_topic in topic.top_answers:
    if upvote < min_upvote:
      break
    if upvote > max_upvote:
      continue

    print(question_title, ' - ', upvote, from_sub_topic)
    try:
      md_file = save_answer(answer, folder=folder)
      fetch_images_for_markdown_file(md_file)
    except RuntimeError as e:
      print(e, question_title)
    except TypeError as e:
      print('question_link["href"]', e, question_title)
    # except AttributeError as e:
    #   print('time to long? ', e, question_title)



def test_do_save_from_topic():

  # url = 'http://www.zhihu.com/topic/19554091/top-answers'  # math
  # url = 'http://www.zhihu.com/topic/19556950/top-answers'  # Physics
  # url = 'http://www.zhihu.com/topic/19574449/top-answers'  # a song of ice and fire
  # url = 'http://www.zhihu.com/topic/19556231/top-answers'  # interactive design 1000
  # url = 'http://www.zhihu.com/topic/19556382/top-answers'  # 2d design 1000
  # url_1 = 'http://www.zhihu.com/topic/19561709/top-answers'  # ux design 1000
  # url_2 = 'http://www.zhihu.com/topic/19551016/top-answers'  # fonts 200
  # url_3 = 'http://www.zhihu.com/topic/19553684/top-answers'  # layout 100
  # url_4 = 'http://www.zhihu.com/topic/19647471/top-answers'  # style 100



  # url = 'http://www.zhihu.com/topic/19551077/top-answers'  # history
  # url = 'http://www.zhihu.com/topic/19615699/top-answers'  # immanuel_kant
  # url = 'http://www.zhihu.com/topic/19558740/top-answers'  # statistics
  # url = 'http://www.zhihu.com/topic/19576422/top-answers'  # statistics
  # url = 'http://www.zhihu.com/topic/19552981/top-answers'  # economics
  # url = 'http://www.zhihu.com/topic/19551864/top-answers' # classical music

  url = 'http://www.zhihu.com/topic/19563625/top-answers'  # astronomy
  save_from_topic(url, min_upvote=2000, max_upvote=5000, folder='history')


# test_do_save_from_topic()







def test_collection():
    url = 'http://www.zhihu.com/collection/19845840'
    collection = zhihu.Collection(url)
    # 获取收藏夹名字
    print(collection.name)
    # 获取收藏夹关注人数
    print(collection.followers_num)

    # 获取收藏夹创建者
    # print(collection.owner)
    # <zhihu.Author object at 0x03EFDB70>

    # 获取收藏夹内所有答案
    # print(collection.answers)

    # <generator object answers at 0x03F00620>

    # 获取收藏夹内所有问题
    # print(collection.questions)
    # <generator object questions at 0x03F00620>

    # Author 对象 和 questions generator 用法见前文




def test_topic(url):

  topic = zhihu.Topic(url)
  # 获取话题名称
  print('name', topic.name)  # 树莓派 (Raspberry Pi)
  print('pages', topic.page_number)  # 5

  # 获取精华回答
  for answer, upvote, question_title, from_sub_topic in topic.top_answers:
    print(question_title, )
    print('    ', answer, upvote, from_sub_topic)
  # generator (answers, upvotes, is_sub_topic)
  # <zhihu.Book object at 0x0600AF90>


def test_test_topic():
  # test_topic('http://www.zhihu.com/topic/20016006/top-answers')  # page 1 ACMDIY
  # test_topic('http://www.zhihu.com/topic/19554298/top-answers')  # page 50 Programming
  # test_topic('http://www.zhihu.com/topic/19737690/top-answers')  # page 2 Raspberry PI
  test_topic('http://www.zhihu.com/topic/19569910/top-answers')  # page 11 OOP
  # test_topic('http://www.zhihu.com/topic/19569910/top-answers')  # page 11 OOP




def test_md_prettify():
  path = '苏州？ - 王維鈞的回答.md'
  markdown_prettify(path, )




def test_md_line_replace():
  text = '感谢 [ @Jim Liu ](http://www.zhihu.com/744db) 乱入的 ** 湖北白河村 ** 与 ** 邯郸玉佛寺 ** ） **王維鈞（作者）** 回复 **Jade Shan**: 他作了一首诗：“床前明月光， ** 脱光光。'
  pattern_hyperlink = re.compile(r'\[ (.+?) \](?=\(.+?\))')
  pattern_strong = re.compile(r'\*\* (.+?) \*\*')
  replace = lambda m: '** 回复 **' if m.group(1) == '回复' else '**'+m.group(1)+'**'
  text2 = pattern_hyperlink.sub(r'[\1]', text)
  text3 = pattern_strong.sub(replace, text2)
  puts()
  print(text3)
  # print(text3)

