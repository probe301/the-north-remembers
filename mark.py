

import time
from pylon import puts
from pylon import datalines

import os
import shutil

from pylon import enumrange
# import time


from zhihu import ZhihuClient
from zhihu.common import remove_invalid_char

import re

import urllib.request


class ZhihuParseError(Exception):
  pass



def generate_cookie():
  # pob....@gmail.com p...
  ZhihuClient().create_cookies('cookies.json')
# generate_cookie()



client = ZhihuClient('cookies.json')



def h2t_handle_html(html):
  import html2text
  h2t = html2text.HTML2Text()
  h2t.body_width = 0
  return '\n'.join(p.rstrip() for p in h2t.handle(html).strip().split('\n'))





def fetch_answer(answer, question=None, author=None):
  time.sleep(1)
  if isinstance(answer, str):
    answer = client.Answer(answer)
  author = author or answer.author
  question = question or answer.question
  # 'http://zhuanlan.zhihu.com/xiepanda'
  # url = 'http://www.zhihu.com/question/30595784/answer/49194862'
  # url = 'http://www.zhihu.com/question/19622414/answer/19798844'
  # url = 'http://www.zhihu.com/question/24413365/answer/27857112'
  # url = 'http://www.zhihu.com/question/23039503/answer/48635152'
  try:
    content = answer.content
  except AttributeError:
    raise ZhihuParseError('cannot parse answer.content: {} {}'.format(answer.question.title, answer.url))

  answer_body = h2t_handle_html(content)

  text = '# {}\n\n'.format(question.title)

  text += '**话题**: {}\n\n'.format(', '.join(question.topics))


  details = h2t_handle_html(question.details).strip()
  if details:
    text += '**补充描述**: \n\n'
    text += details
    text += '\n\n'

  motto = ' ({})'.format(author.motto) if author.motto else ''
  create_date, edit_date = answer.date_pair

  text += '    author:      {}{}\n'.format(author.name, motto)
  text += '    upvote:      {} 赞同\n'.format(answer.upvote_num)
  text += '    count:       {} 字\n'.format(len(answer_body))
  text += '    create_date: {}\n'.format(create_date)
  if edit_date:
    text += '    edit_date:   {}\n'.format(edit_date)
  text += '    fetch_date:  {}\n'.format(time.strftime('%Y-%m-%d'))
  text += '    link:        {}\n\n'.format(answer.url)


  text += answer_body

  conversations = answer.valuable_conversations(limit=10)
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
        # puts(content)
        text += '**{}**{}: {}{}\n\n'.format(comment.author, reply_to_author, content, likes)


  text += '\n\n　　\n\n--------------\n'
  text += 'from: [{}]()\n'.format(answer.url)
  return text



def save_answer(answer, folder='test', overwrite=True):
  if isinstance(answer, str):
    answer = client.Answer(answer)
  author = answer.author
  question = answer.question
  save_path = folder + '/' + remove_invalid_char(question.title + ' - ' + author.name + '的回答.md')
  if not overwrite and os.path.exists(save_path):
    puts('answer_md_file exist! save_path')
    return

  text = fetch_answer(answer, question, author)

  with open(save_path, 'w') as f:
    f.write(text)
    puts('write save_path done')

  markdown_prettify(save_path)  # 去除 html2text 转换出来的 strong 和 link 的多余空格
  fetch_images_for_markdown_file(save_path)  # get images in markdown
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




def fetch_images_for_markdown_file(markdown_file):
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

def markdown_prettify(path, prefix=''):

  with open(path, encoding='utf-8') as f:
    lines = f.readlines()

  # drop extra space in link syntax
  # eg. [ wikipage ](http://.....) => [wikipage](http://.....)
  # eg2 [http://www.  businessanalysis.cn/por  tal.php ](http://www.businessanalysis.cn/portal.php)
  pattern_hyperlink = re.compile(r'\[ (.+?) \](?=\(.+?\))')

  def hyperlink_replacer(mat):
    r = mat.group(1).replace('http://www.', '').replace('http://', '').replace(' ', '')
    if r.endswith('/'):
      r = r[:-1]
    if r.endswith('__'):
      r = r[:-2] + '...'
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
  pattern_redirect_link = re.compile(r'\]\(\/\/link\.zhihu\.com\/\?target=(.+?)\)')
  replace_redirect_link = lambda m: '](' + unquote(m.group(1)) + ')'


  for i, line in enumerate(lines):
    if not ('[' in line or '**' in line):
      continue
    # line = pattern_hyperlink.sub(r'[\1]', line)
    line = pattern_hyperlink.sub(hyperlink_replacer, line)
    line = pattern_strong.sub(replace_strong, line)
    line = pattern_redirect_link.sub(replace_redirect_link, line)
    line = pattern_tex_link.sub('](http://www.zhihu.com/equation?tex=', line)
    lines[i] = line





  with open(prefix + path, 'w', encoding='utf-8') as f2:
    f2.writelines(lines)













def save_from_author(url, folder='test', min_upvote=500, overwrite=False):
  # url = 'http://www.zhihu.com/people/nordenbox'
  author = client.Author(url)
  # 获取用户名称
  print(author.name, ' - ', author.motto)
  # 获取用户答题数
  print(author.answer_num)      # 227
  for i, answer in enumerate(author.answers):
    # if i > 20:
    #   break
    if answer.upvote_num < min_upvote:
      continue

    try:
      save_answer(answer, folder=folder, overwrite=overwrite)
    except ZhihuParseError as e:
      print(e)
    except RuntimeError as e:
      print(e, answer.question.title)
    except AttributeError as e:
      print(answer.question.title, answer.url, e)
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





def save_from_topic(url, limit=200,
                    min_upvote=1000, max_upvote=100000000,
                    folder='test',
                    overwrite=True):

  if not os.path.exists(folder):
    os.makedirs(folder)

  topic = client.Topic(url)

  for i, answer in enumrange(topic.top_answers, limit):
    print('fetching', answer.question.title, ' - ', answer.upvote_num)

    if answer.upvote_num < min_upvote:
      break
    if answer.upvote_num > max_upvote:
      continue

    try:
      save_answer(answer, folder=folder, overwrite=overwrite)
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
  url = 'https://www.zhihu.com/people/xbjf/'  # 玄不救非氪不改命
  save_from_author(url, folder='authors', min_upvote=500)
  url = 'https://www.zhihu.com/people/lu-pi-xiong/'  # 陆坏熊
  save_from_author(url, folder='authors', min_upvote=300)
  url = 'https://www.zhihu.com/people/zhao-hao-yang-1991'  # 赵皓阳
  save_from_author(url, folder='authors', min_upvote=300)
# exec_save_from_authors()


def exec_save_answers():
  urls = '''
    # https://www.zhihu.com/question/40305228/answer/86179116
    # https://www.zhihu.com/question/36466762/answer/85475145
    # https://www.zhihu.com/question/33246348/answer/86919689
    # https://www.zhihu.com/question/39906815/answer/88534869

    # https://www.zhihu.com/question/40700155/answer/89002644
    # https://www.zhihu.com/question/36380091/answer/84690117
    # https://www.zhihu.com/question/33246348/answer/86919689
    # https://www.zhihu.com/question/35254746/answer/90252213
    # https://www.zhihu.com/question/23618517/answer/89823915
    https://www.zhihu.com/question/40677000/answer/87886574
  '''
  for url in datalines(urls):
    save_answer(url, folder='test')




def exec_save_from_question():
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
    # https://www.zhihu.com/topic/19552981 economics 经济
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
    save_from_topic(url, limit=300, min_upvote=1000, max_upvote=5000000, folder=topic_name_cn, overwrite=False)




# exec_save_from_topic()

















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
  # 如何从头系统地听古典音乐？
  save_answer('https://www.zhihu.com/question/30957313/answer/50266448')
  # 你会带哪三本书穿越回到北宋熙宁二年？
  save_answer('http://www.zhihu.com/question/25569054/answer/31213671')



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
  save_answer('https://www.zhihu.com/question/34961425/answer/74576898', overwrite=False)


def test_save_answer_drop_redirect_links():
  # 大偏差技术是什么？
  save_answer('https://www.zhihu.com/question/29400357/answer/82408466')





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



def test_save_whitedot_bug():
  # QQ 的登录封面（QQ印象）是怎么设计的？
  url = 'http://www.zhihu.com/question/22497026/answer/21551914/'
  # answer = zhihu.Answer(url)
  # print(answer)
  # print(answer.content)
  save_answer(url)




def test_generate_ascii_art():
  from pyfiglet import Figlet

  print(Figlet(font='space_op').renderText('flask'))





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






def test_time():
  print(time.strftime('%Y-%m-%d'))


def test_new_zhihu():
  url = 'https://www.zhihu.com/question/30957313/answer/50266448'
  answer = client.answer(url) | puts()
  answer.author | puts()
  answer.collect_num | puts()
  answer.upvote_num | puts()
  answer.content | puts()
  for c in list(answer.comments):
    (c.author.name, c.content) | puts()




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







