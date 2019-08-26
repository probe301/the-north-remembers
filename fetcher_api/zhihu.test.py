import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from tools import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')



from zhihu import *


'''
####### #######  ###### #######
   ##   ##      ##         ##
   ##   ######   #####     ##
   ##   ##           ##    ##
   ##   ####### ######     ##
'''



def test_answer_normal():
  # 为什么大部分中国人没学过繁体字却能看懂？ - Rian Zakaron的回答
  url = 'https://www.zhihu.com/question/296904119/answer/510160579'       
  fetch_zhihu_answer(url)

def test_question_deleted():
  # https://www.zhihu.com/question/44069719
  url = 'https://www.zhihu.com/question/44069719/answer/97020803' # 可能有404问题和404回答两类    
  # 404 你似乎来到了没有知识存在的荒原
  fetch_zhihu_answer(url)


def test_answer_deleted():
  # 中国传统建筑中的宫、殿、堂、楼各有什么特点？
  url = 'https://www.zhihu.com/question/32237946/answer/734344973'       
  # 该回答已被删除
  fetch_zhihu_answer(url)


def test_answer_suggest_edit():
  # 为什么会出现「只有专政才能救中国」的言论？
  url = 'https://www.zhihu.com/question/33594085/answer/74817919/'
  # 回答建议修改：不友善内容 作者修改内容通过后，回答会重新显示
  fetch_zhihu_answer(url) # 不报错, 返回正常的 json_data











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
