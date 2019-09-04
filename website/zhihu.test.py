import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from tools import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')



from zhihu import *

def save_answer(answer, folder='test', overwrite=True):
  answer = parse_answer(answer)
  author = answer.author
  if author is None:
    # 如果匿名, 现在返回 None, 需要 fix 为一个 AuthorObject
    author = FakeAuthor()
  title = answer.question.title + ' - ' + author.name + '的回答'
  save_path = folder + '/' + tools.remove_invalid_char(title) + '.md'
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


































### 原 models test exec



'''
####### #######  ###### #######
   ##   ##      ##         ##
   ##   ######   #####     ##
   ##   ##           ##    ##
   ##   ####### ######     ##
'''

def test_new_task():
  # url = 'https://www.zhihu.com/question/30595784/answer/49194862'
  # 如何看待许知远在青年领袖颁奖典礼上愤怒「砸场」？
  url = 'https://www.zhihu.com/question/22316395/answer/100909780'
  url = 'https://www.zhihu.com/question/47220155/answer/118154455'
  url = 'https://www.zhihu.com/question/49962599/answer/118716273'
  url = 'https://zhuanlan.zhihu.com/p/19837940'
  url = 'https://zhuanlan.zhihu.com/p/20639779'
  url = 'https://zhuanlan.zhihu.com/p/20153329'
  url = 'https://zhuanlan.zhihu.com/p/21281864'
  url = 'https://zhuanlan.zhihu.com/p/19964142'
  task = Task.add(url=url)
  print(task)
  # task.watch()


def test_readd_task():
  url = 'http://www.zhihu.com/question/22513722/answer/21967185' # 火车票涨价
  task = Task.add(url=url)
  task = Task.add(url=url)
  url = 'https://www.zhihu.com/question/30957313/answer/50266448' # 古典音乐
  task = Task.add(url=url)
  url = 'https://www.zhihu.com/question/40056948/answer/110794550' # 四万亿
  task = Task.add(url=url)

def test_seed_add_tasks():
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
    https://www.zhihu.com/question/27820755/answer/107267228 裸辞后怎样解释以获工作机会？
  '''
  for url in datalines(urls):
    url = url.split(' ')[0]
    task = Task.add(url=url)
    task | puts()



def test_one_watch():
  task = Task.select().order_by(-Task.id).get()
  task | puts()
  task.watch()

def test_another_watch():
  url = 'http://www.zhihu.com/question/22513722/answer/21967185' # 火车票涨价
  task = Task.select().where(Task.url == url).get()
  task | puts()
  task.watch()


def test_hot_answer():
  url = 'http://www.zhihu.com/question/39288165/answer/110207560'
  url = 'https://www.zhihu.com/question/50763374/answer/122822226'
  url = 'https://www.zhihu.com/question/40910547/answer/123021503'
  url = 'https://zhuanlan.zhihu.com/p/21478575'
  url = 'https://www.zhihu.com/question/40103788/answer/124499334'
  task = Task.add(url=url)
  task.watch()


  task.last_page.to_local_file(folder='test', fetch_images=False)



def test_watch_all():
  Task.multiple_watch(sleep_seconds=10, limit=4)


def test_report():
  Task.report()



def test_to_local_file():
  # page = Page.select().order_by(-Page.id).get()

  # page = Page.select(Page.topic).distinct().where(Page.topic.contains('房')).limit(5)
  # q = Page.select(Page.id).distinct()
  # for p in q:
  #   print(p)
  query = (Page.select(Page, Task)
           .join(Task)
           .where(Page.author == 'chenqin')  # .where(Page.topic.contains('建筑'))
           .group_by(Page.task)
           .having(Page.watch_date == fn.MAX(Page.watch_date))
           .limit(8800))
  for page in query:
    log(page.title)
    # log(page.metadata)
    # page.to_local_file(folder='chen', fetch_images=False)
# test_to_local_file()

def test_tools():
  import pylon
  pylon.generate_figlet('task', fonts=['space_op'])
  pylon.generate_figlet('page', fonts=['space_op'])
  pylon.generate_figlet('test', fonts=['space_op'])


def test_load_json():
  import json

  print(json.loads(open('mockup_topic_answers.json', encoding='utf-8').read()))


def test_banned_modes():
  url = 'https://www.zhihu.com/question/40679967/answer/88310495'
  # 政府推出开放小区政策的真正目的是什么？ 2201 孟德尔 回答建议修改：政治敏感
  pass


def test_query_task():
  s = 'https://www.zhihu.com/question/48737226/answer/113036453'
  s = 'https://www.zhihu.com/question/47220155/answer/118154455'
  s = 'https://www.zhihu.com/question/49545583/answer/116529877'

  t = Task.select().where(Task.url == s)
  t = t.get()
  log(t.title)
  log(t.id)






def test_explore():
  # Tweet.select(fn.COUNT(Tweet.id)).where(Tweet.user == User.id)
  query = (Task
           .select(Task, fn.COUNT(Page.id).alias('fetched_count'))
           .join(Page)
           .group_by(Task.title)
           .limit(50)
           .offset(200)
           .order_by(fn.COUNT(Page.id).desc()))

  for task in query:
    log(task.title + ' : ' + str(task.fetched_count) + '  task_id ' + str(task.id))




def test_explore_watching_results_diff():

  s = '''
  # 美国是不是正在为瓦解中国做准备？ - 张俊麒的回答 : 16  task_id 46
  # 为什么很少看到患者砍莆田系医生的报道？ - 玄不救非氪不改命的回答 : 3  task_id 196
  # 为什么很难证伪马克思主义理论？ - 玄不救非氪不改命的回答 : 3  task_id 360
  # 为什么快速浏览一段内容的时候，很容易看到自己感兴趣的部分？ - 采铜的回答 : 3  task_id 742
  # 为什么拿广州恒大淘宝队与中国国家男子足球队做对比？ - 玄不救非氪不改命的回答 : 3  task_id 492
  # 如何看待里约奥运陈欣怡药检呈阳性反应？ - 玄不救非氪不改命的回答 : 3  task_id 2393
  # 为什么厌恶「国粉」的知乎用户远多于厌恶「毛粉」的？ - chenqin的 : 3  task_id 3313
  # 2016 年中国的经济状况很差吗？真实状况是怎样的？ - 垒起善城堡的积木 : 3 task_id 2387
  # 如何看待2016年7月人民币贷款增幅里9.8成为房贷？ - 匿名用户的回答 : 3 task_id 2386




  # 怎样评价「游戏不汉化就差评」的行为？ - cOMMANDO的回答 : 9  task_id 4471
  # 既然有报道说人类的基因片段只占DNA序列总长的不到10%，那么这几个问题怎么解答？ - Mandelbrot的回答 : 9  task_id 676
  # 智商低的人真的不适合玩需要动脑子的游戏么？ - 匿名用户的回答 : 9  task_id 3461
  # 暴雪，Valve，拳头，谁更厉害？ - cOMMANDO的回答 : 9  task_id 2597
  # 有一个稀有的姓是一种怎样的体验？ - 冷哲的回答 : 9  task_id 1041
  # 有什么影视作品是当时演员名气不大，现在看来是全明星阵容出演？ - 玄不救非氪不改命的回答 : 9  task_id 484
  # 有关白龙尾岛的历史，哪些是有据可查的？ - 书生的回答 : 9  task_id 712
  # 有哪些「智商税」？ - 谢熊猫君的回答 : 9  task_id 2406
  # 有哪些令人拍案叫绝的临场反应？ - 大盗贼霍老爷的回答 : 9  task_id 4107
  # 有哪些可怕的故事？ - 大盗贼霍老爷的回答 : 9  task_id 4137
  # 有哪些长得比较逆天的动物？ - Mandelbrot的回答 : 9  task_id 648
  # 有文化有多可怕？ - 寺主人的回答 : 9  task_id 5787
  # 机器人教育这种不考试、以娱乐为主的教育对于中小学生及幼儿的意义何在？ - 冷哲的回答 : 9  task_id 1015
  # 毛花三年打败蒋然后走三十年弯路的目的，都是为后三十年的改革开放走资、大国崛起做铺垫扫平道路的么？ - 书生的回答 : 9  task_id 99
  # 水旱蝗汤中的汤指的到底是谁？ - 书生的回答 : 9  task_id 104
  # 河南的地理位置那么好，为什么经济落后？ - 大盗贼霍老爷的回答 : 9  task_id 4105
  # 為什麼蒋介石被称为运输大队长？求详? - 书生的回答 : 9  task_id 701
  # 玩《狼人杀》时你有什么屡试不爽的秘技诀窍？ - 汪诩文的回答 : 9  task_id 3526

  现在网络上很多人黑一些伟人，比如说周半期，黑鲁迅。他们是什么心态？ - 书生的回答 : 9  task_id 97
  看美剧、英剧学英语有什么有效的方法吗？ - 采铜的回答 : 9  task_id 787
  章鱼的智商到底有多高，为什么有人说它们的智商可以统治世界? - Mandelbrot的回答 : 9  task_id 588
  类似 AlphaGo 的人工智能在游戏王、万智牌等卡牌游戏中胜率如何？ - 莫名的回答 : 9  task_id 3724
  给 59 分强行不给过的老师是一种怎么样的存在？ - chenqin的回答 : 9  task_id 3317
  网络上有哪些广为流传的「历史真相」其实是谣言？ - 马前卒的回答 : 9  task_id 5089
  美国南北战争的真正原因是什么？ - talich的回答 : 9  task_id 2571
  美国发动伊拉克战争的核心原因到底是什么？ - 冷哲的回答 : 9  task_id 1332
  美国最高法院大法官 Scalia 的去世将会带来怎样的影响？ - talich的回答 : 9  task_id 4423
  美国有人在开车在路上故意把川普的竞选宣传牌碾倒，如何评价这种因为不同政见而破坏对方财物的行为？ - talich的回答 : 9  task_id 4412
  装逼成功是怎样一种体验？ - 大盗贼霍老爷的回答 : 9  task_id 4048
  谁最应该被印在人民币上面？ - 蜂鸟的回答 : 9  task_id 2274
  豆瓣的核心用户都有什么特点？ - 十一点半的回答 : 9  task_id 84
  赌场有哪些看似不起眼，实则心机颇深的设计？ - 第一喵的回答 : 9  task_id 3158
  赌场有哪些看似不起眼，实则心机颇深的设计？ - 肥肥猫的回答 : 9  task_id 3151
  雷锋是个什么样的人，怎么客观评价雷锋？ - 书生的回答 : 9  task_id 96
  鲁迅和秋瑾的关系好吗？ - 书生的回答 : 9  task_id 91
  1927 年蒋介石为什么要清党？ - 冷哲的回答 : 8  task_id 1415
  1949年以后的中国本土设计的建筑中，哪些能称得上是有思想的好建筑？ - Chilly的回答 : 8  task_id 3104
  2015 年初，中国制造业形势有多严峻？ - 稻可道 稻子的稻的回答 : 8  task_id 2239
  2016 年，中国房地产泡沫是否会在一两年内破灭，从而引发金融危机？ - Bee Mad的回答 : 8  task_id 2104
  2016 年，中国房地产泡沫是否会在一两年内破灭，从而引发金融危机？ - 君临的回答 : 8  task_id 2205
  2016 年，中国房地产泡沫是否会在一两年内破灭，从而引发金融危机？ - 小马的回答 : 8  task_id 5752
  ISIS 是一个什么样的组织？它的资金是哪来的？ - 罗晓川的回答 : 8  task_id 39
  Lambda 表达式有何用处？如何使用？ - 涛吴的回答 : 8  task_id 2008
  Signal Weighting---基于因子IC的因子权重优化模型 - 陈颖的专栏 量化哥 : 8  task_id 6007
  Smart Beta 投资方法 - 陈颖的专栏 量化哥 : 8  task_id 6017
  ofo 获滴滴数千万美元C轮投资，然后呢？ - 曲凯的专栏 创投方法论 : 8  task_id 5656
  《文明 6 》中的背景音乐都有什么来历？ - PenguinKing的回答 : 8  task_id 6250
  《权力的游戏》你觉得最可怜的人是谁？ - 苏鲁的回答 : 8  task_id 4576
  《蒋介石日记》和《毛泽东选集》差距有多大？ - 马前卒的回答 : 8  task_id 5355
  「心灵鸡汤」式的文章错在哪？ - 赵皓阳的回答 : 8  task_id 584
  '''

  for line in datalines(s):
    task_id = int(line.split('task_id')[-1][1:])
    # log(task_id)
    task = Task.select().where(Task.id == task_id).get()
    log(task)
    # log(task.pages)
    # log(task.last_page)
    contents = [fix_in_compare(p.content) for p in task.pages]
    # questions = [fix_in_compare(p.question) for p in task.pages]
    titles = [p.title for p in task.pages]

    # metas = [p.metadata for p in task.pages]
    # for meta in metas:
    #   log(meta)
    # compare_text_sequence(titles, label='titles')
    # compare_text_sequence(questions, label='questions')
    compare_text_sequence(contents, label='contents')

    log('\n\n\n')



def fix_in_compare(text):
  import re
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

  text = pattern_img_start_inline.sub(replace_img_start_inline, text)

  pattern_img_https = re.compile(r'http://pic(\d)\.zhimg\.com')
  text = pattern_img_https.sub(r'https://pic\1.zhimg.com', text)
  return text


def compare_text(t1, t2, prefix=''):
  import difflib
  changes = [l for l in difflib.ndiff(t1.split('\n'), t2.split('\n')) if l.startswith(('+ ', '- '))]
  for change in changes:
    log(prefix + change)
  return changes


def compare_text_sequence(texts, label=''):
  from pylon import dedupe
  from pylon import windows

  texts = list(dedupe(texts))
  if len(texts) > 1:
    log('detect changed {}'.format(label))
    for t1, t2 in windows(texts, length=2, overlap=1):
      compare_text(t1, t2, prefix='  ')
  else:
    log('nothing changed {}'.format(label))



def test_explore_voteup_thanks():
  '''感谢赞同比跟文章质量没啥关系'''
  query = (Page.select(Page, Task)
           .join(Task)
           .where((Task.page_type == 'zhihu_answer'))
           .group_by(Page.task)
           .having(Page.watch_date == fn.MAX(Page.watch_date))
           .limit(50)
           .order_by(fn.Random())
           )

  def thanks_voteup_ratio(page):
    thanks = int(page.metadata.split('thanks: ')[1].split(' ')[0])
    voteup = int(page.metadata.split('voteup: ')[1].split(' ')[0])
    return round(thanks / voteup, 3)

  # for page in query:
  #   log(page.title)

  pages = sorted(query, key=thanks_voteup_ratio)
  for page in pages:
    log(page.title)
    log(repr(page.content[:500]))
    log(thanks_voteup_ratio(page))
    log('-----------------\n\n\n')















