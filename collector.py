
import time
import os
import shutil
import re
from datetime import datetime


from watcher import Watcher
from collections import OrderedDict as odict
import tools

log = tools.create_logger(__file__)
log_error = tools.create_logger(__file__ + '.error')


class Collector:
  '''
  与用户对接提交抓取任务, 接受用户输入的条件和附加参数
  提交一个页面, 直接安排抓取, 不记录
  提交页面集合 (用户的所有回答, 专栏, 收藏夹),
    首先解析任务列表, 取出所涉及页面, 都安排一次抓取
    如果要求记录任务自身, 则额外记录 Collector 配置, 供之后定期rescan增加页面

  collector = Collector(project_path=xxx)
  collector.add(url1)
  collector.add(weixin_page_url)
  collector.add(zhihu_column_url)
  collector.add(zhihu_anwser_id=xxx)
  collector.add(zhihu_author_id=xxx)
  collector.add(column_id=xxx)

  yaml_tmpl like:
                  default_option:
                    lister:
                      enabled: true
                      max_cycle: 15day
                      min_cycle: 1hour
                      zhihu_min_voteup: 1
                      weight: 0.5
                      limit: 200
                    page:
                      enabled: true
                      max_cycle: 1day
                      min_cycle: 1hour
                      weight: 0.5

                  lister_task:
                    - url: xxxxx
                      tip: xxx

  '''


  def __init__(self, project_path):
    ''' 创建 Collector 
        需要固定的项目路径, 
        同时检测项目路径是否为 git 仓库
    '''
    self.project_path = project_path
    # TODO check git repo


  def __str__(self):
    return f'<Collector #{id(self)} path={self.project_path}>'



  def add(self, url, tip, lister_option=None, page_option=None):
    ''' 添加一个 Watcher, 根据 url 决定何种类型 '''

    lister_default_option = odict(
      enabled=True,
      max_cycle='15day',
      min_cycle='1hour',
      weight=0.5,
      limit=200,
    )
    page_default_option = odict(
      enabled=True,
      max_cycle='1day',
      min_cycle='1hour',
      weight=0.5,
    )

    if lister_option:
      lister_default_option.update(lister_option)
    if page_option:
      page_default_option.update(page_option)

    url = tools.purge_url(url)
    # page_type = tools.parse_type(url)
    folder = self.project_path + '/' + tools.remove_invalid_char(tip)

    d = odict(
      default_option=odict(
        lister=lister_default_option,
        page=page_default_option,
      ), 
      lister_task=[odict(url=url, tip=tip), odict(url=url, tip=tip),]
    )
    # 这样会让 lister_task[] 的缩进不正确
    # 应该是 lister_task:
    #          - url: xxx
    #            tip: xxx
    # 实际是 lister_task:
    #        - url: xxx
    #          tip: xxx 但是不影响识别


    if os.path.exists(folder):
      raise ValueError(f'folder already exists: {folder}')
    else:
      os.mkdir(folder)
      tools.yaml_save(d, folder + '/' + '.task.yaml')
      log(f'Watcher folder {folder} created')


  # def add_by_answer(self, answer_id, title=None, force_start=False):
  #   # log('add by answer')
  #   url = zhihu_answer_url(answer_id)
  #   # log('add by answer {}'.format(url))
  #   task = self.add(url, title=title)
  #   # log('add by answer {} {}'.format(url, task))
  #   if force_start:
  #     task.watch()
  #   return task


  # def add_by_author(self, author_id, limit=3000, min_voteup=100,
  #                   stop_at_existed=10, force_start=False):
  #   existed_count = 0
  #   added_count = 0
  #   for answer in yield_author_answers(author_id, limit=limit, min_voteup=min_voteup):
  #     url = zhihu_answer_url(answer)

  #     t = Task.is_watching(url)
  #     if t:
  #       existed_count += 1
  #       # log('already watching {} {}'.format(t.title, existed_count))
  #       if stop_at_existed and stop_at_existed <= existed_count:
  #         break
  #     else:
  #       task = Task.add(url, title=answer.question.title)
  #       added_count += 1
  #       log('add_by_author <{}>\n'.format(added_count))
  #       if force_start:
  #         task.watch()
  #   log('add_by_author done, total added {} skipped {}'.format(added_count, existed_count))


  # def add_by_topic_best_answers(cls, topic_id, limit=3000, min_voteup=100,
  #                               stop_at_existed=10, force_start=False):
  #   existed_count = 0
  #   added_count = 0
  #   log(topic_id)
  #   for answer in yield_topic_best_answers(topic_id, limit=limit, min_voteup=min_voteup):
  #     url = zhihu_answer_url(answer)

  #     t = Task.is_watching(url)
  #     if t:
  #       existed_count += 1
  #       log('  already watching {} {}'.format(t.title, existed_count))
  #       if stop_at_existed and stop_at_existed <= existed_count:
  #         break
  #     else:
  #       task = Task.add(url, title=answer.question.title)
  #       added_count += 1
  #       log('add_by_topic_best_answers <{}>\n'.format(added_count))
  #       if force_start:
  #         task.watch()
  #   log('add_by_topic_best_answers done, total added {} skipped {}'.format(added_count, existed_count))



  # def add_articles(cls, author_id=None, column_id=None,
  #                  limit=3000, min_voteup=10,
  #                  stop_at_existed=10, force_start=False):

  #   if not author_id and not column_id:
  #     raise ValueError('no author_id, no column_id')
  #   if author_id:
  #     yield_articles = yield_author_articles(author_id, limit=limit, min_voteup=min_voteup)
  #   else:
  #     yield_articles = yield_column_articles(column_id, limit=limit, min_voteup=min_voteup)

  #   existed_count = 0
  #   added_count = 0
  #   for article in yield_articles:
  #     url = zhihu_article_url(article)

  #     t = Task.is_watching(url)
  #     if t:
  #       existed_count += 1
  #       # log('already watching {} {}'.format(t.title, existed_count))
  #       if stop_at_existed and stop_at_existed <= existed_count:
  #         break
  #     else:
  #       task = Task.add(url, title=article.title)
  #       added_count += 1
  #       log('add_articles <{}>\n'.format(added_count))
  #       if force_start:
  #         task.watch()
  #   log('add_articles done, total added {} skipped {}'.format(added_count, existed_count))






















# @app.route('/answer/<answer_id>')
# def watch_zhihu_answer(answer_id):
#   # https://www.zhihu.com/question/33918585/answer/89678373
#   log('get /answer/<answer_id>' + str(answer_id))
#   task = Task.add_by_answer(answer_id=int(answer_id), force_start=True)
#   return jsonify(task.last_page.to_dict())






# @app.route('/author/<author_id>')
# def list_zhihu_answers_by_author(author_id):
#   from zhihu_answer import yield_author_answers
#   ret = []
#   limit = int(request.args.get('limit', 10))
#   min_voteup = int(request.args.get('min_voteup', 300))
#   for answer in yield_author_answers(author_id, limit=limit, min_voteup=min_voteup):
#     url = zhihu_answer_url(answer)
#     ret.append({'url': url,
#                 'title': answer.question.title,
#                 'voteup_count': answer.voteup_count,
#                 'created_time': convert_time(answer.created_time),
#                 'updated_time': convert_time(answer.updated_time),
#                 'author_name': answer.author.name,
#                })
#   return jsonify(ret)


# @app.route('/topic/<int:topic_id>')
# def list_zhihu_answers_by_topic(topic_id):
#   from zhihu_answer import yield_topic_best_answers


#   # mockup
#   def yield_topic_best_answers(topic_id, limit=100, min_voteup=300):
#     import json
#     data = json.loads(open('mockup_topic_answers.json', encoding='utf-8').read())
#     return (elem for elem in data)

#   ret = list(yield_topic_best_answers(topic_id))
#   return render_template("topics.html",
#                          title='Topics', topic_answers=ret)

#   # real
#   ret = []
#   for answer in yield_topic_best_answers(topic_id, limit=100, min_voteup=300):
#     url = zhihu_answer_url(answer)
#     ret.append({'url': url,
#                 'title': answer.question.title,
#                 'vote': answer.voteup_count,
#                 'topic': [t.name for t in answer.question.topics],
#                })
#   # return form(ret)
#   # return jsonify(ret)

#   return render_template("topics.html",
#                          title='Topics', topic_answers=ret)



# @app.route('/rss')
# def recent_feed():
#     feed = AtomFeed('Recent Articles',
#                     feed_url=request.url, url=request.url_root)

#     info = '''
#       - title: title1
#         rendered_text: rendered_text1
#         author_name: author_name1
#         url: http://11.22.com
#         last_update: 2016-1-1
#         published: 2016-1-1
#       - title: title2
#         rendered_text: rendered_text2
#         author_name: author_name2
#         url: http://22.22.com
#         last_update: 2016-1-12
#         published: 2016-1-12

#     '''
#     articles = yaml_load(info)
#     for article in articles:
#         feed.add(article.get('title'),
#                  article.get('rendered_text'),
#                  content_type='html',
#                  author=article.get('author_name'),
#                  url=article.get('url'),
#                  updated=datetime.now(),
#                  published=datetime.now()
#                  )
#     return feed.get_response()







# @app.route('/user/<username>')
# def show_user_profile(username):
#   # show the user profile for that user
#   return 'User %s' % username








# @app.route('/post/<int:post_id>')
# def show_post(post_id):
#   # show the post with the given id, the id is an integer
#   return 'Post %d' % post_id
#   # return flask.jsonify(**f)
#   # @app.route('/_get_current_user')
#   # def get_current_user():
#   #     return jsonify(username=g.user.username,
#   #                    email=g.user.email,
#   #                    id=g.user.id)
#   # Returns:

#     # {
#     #     "username": "admin",
#     #     "email": "admin@localhost",
#     #     "id": 42
#     # }








  # def yield_topic_best_answers(topic_id, limit=100, min_voteup=300):
  # def save_answer(answer, folder='test', overwrite=True):
  # def save_article(article, folder='test', overwrite=True):
  # def fetch_images_for_markdown(markdown_file):


# def smart_save(url, folder=None, limit=1000,
#                min_voteup=500, max_voteup=500000000,
#                overwrite=False):
#   '''根据 url 推断 话题 或者 作者, 自动抓取此类回答'''
#   if 'www.zhihu.com/topic/' in url:
#     topic = client.from_url(url)
#     log([topic.name, topic.id])
#     folder = folder or topic.name
#     answers = list(yield_topic_best_answers(int(topic.id), limit=limit, min_voteup=min_voteup))

#   elif 'www.zhihu.com/people/' in url:
#     author = client.from_url(url)
#     log([author.name, author.headline, 'answers', author.answer_count])
#     folder = folder or author.name
#     answers = list(yield_author_answers(author.id, limit=limit, min_voteup=min_voteup))
#   elif 'www.zhihu.com/collection/' in url:
#     collection = client.from_url(url)
#     log([collection.title, collection.creator.name, collection.description, collection.answer_count])
#     folder = folder or collection.title
#     answers = list(yield_collection_answers(collection.id, limit=limit, min_voteup=min_voteup))


#   log('detected {} answers'.format(len(answers)))
#   if not os.path.exists(folder):
#     os.makedirs(folder)

#   for i, answer in enumerate(answers, 1):
#     url = zhihu_answer_url(answer)
#     try:
#       log('start fetching answer {}/{}'.format(i, len(answers)))
#       log('{}'.format(zhihu_answer_format(answer)))
#       save_answer(url, folder=folder, overwrite=overwrite)
#       log('save done\n')
#     except ZhihuParseError as e:
#       log_error(e)
#     except RuntimeError as e:
#       log_error(e, answer.question.title)
#     except requests.exceptions.RetryError as e:
#       log_error([e, 'on {}'.format(url)])
#     except AttributeError as e:
#       print(answer.question.title, url, e)
#       raise

#   log('all done!')

