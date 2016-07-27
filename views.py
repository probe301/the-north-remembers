
import time
import os
import shutil
import re
from pylon import puts
from pylon import datalines
from pylon import enumrange
from pylon import yaml_load
from werkzeug.contrib.atom import AtomFeed
from flask import request
from flask import jsonify
from datetime import datetime
####### ##       #####   ###### ##   ##
##      ##      ##   ## ##      ##  ##
######  ##      #######  #####  ######
##      ##      ##   ##      ## ##   ##
##      ####### ##   ## ######  ##   ##


from flask import Flask
from flask import render_template
from flask import Response
app = Flask(__name__)

from pylon import create_logger
log = create_logger(__file__)




from models import Task, Page

from zhihu_answer import zhihu_answer_url



@app.route('/')
@app.route('/index')
def index():
  user = {'nickname': 'Miguel'}  # fake user
  return render_template("index.html",
                         title='Home',
                         user=user)


@app.route('/hello')
def hello():
  return 'Hello World'





@app.route('/answer/<answer_id>')
def watch_zhihu_answer(answer_id):
  # https://www.zhihu.com/question/33918585/answer/89678373
  # puts('fetching zhihu / question / answer')
  task = Task.add_by(answer_id=answer_id)
  page = task.watch()
  return Response(page.full_content(), mimetype='text/text')






@app.route('/author/<author_id>')
def list_zhihu_answers_by_author(author_id):
  from zhihu_answer import yield_author_answers
  ret = []
  for answer in yield_author_answers(author_id, limit=100, min_voteup=300):
    url = zhihu_answer_url(answer)
    ret.append({'url': url,
                'title': answer.question.title,
                'vote': answer.voteup_count,
               })
  return str(ret)
  # return jsonify(ret)



from pylon import form

@app.route('/topic/<int:topic_id>')
def list_zhihu_answers_by_topic(topic_id):
  from zhihu_answer import yield_topic_best_answers


  # mockup
  def yield_topic_best_answers(topic_id, limit=100, min_voteup=300):
    import json
    data = json.loads(open('mockup_topic_answers.json', encoding='utf-8').read())
    return (elem for elem in data)

  ret = list(yield_topic_best_answers(topic_id))
  return render_template("topics.html",
                         title='Topics', topic_answers=ret)

  # real
  ret = []
  for answer in yield_topic_best_answers(topic_id, limit=100, min_voteup=300):
    url = zhihu_answer_url(answer)
    ret.append({'url': url,
                'title': answer.question.title,
                'vote': answer.voteup_count,
                'topic': [t.name for t in answer.question.topics],
               })
  # return form(ret)
  # return jsonify(ret)

  return render_template("topics.html",
                         title='Topics', topic_answers=ret)



@app.route('/rss')
def recent_feed():
    feed = AtomFeed('Recent Articles',
                    feed_url=request.url, url=request.url_root)

    info = '''
      - title: title1
        rendered_text: rendered_text1
        author_name: author_name1
        url: http://11.22.com
        last_update: 2016-1-1
        published: 2016-1-1
      - title: title2
        rendered_text: rendered_text2
        author_name: author_name2
        url: http://22.22.com
        last_update: 2016-1-12
        published: 2016-1-12

    '''
    articles = yaml_load(info)
    for article in articles:
        feed.add(article.get('title'),
                 article.get('rendered_text'),
                 content_type='html',
                 author=article.get('author_name'),
                 url=article.get('url'),
                 updated=datetime.now(),
                 published=datetime.now()
                 )
    return feed.get_response()







@app.route('/user/<username>')
def show_user_profile(username):
  # show the user profile for that user
  return 'User %s' % username








@app.route('/post/<int:post_id>')
def show_post(post_id):
  # show the post with the given id, the id is an integer
  return 'Post %d' % post_id
  # return flask.jsonify(**f)
  # @app.route('/_get_current_user')
  # def get_current_user():
  #     return jsonify(username=g.user.username,
  #                    email=g.user.email,
  #                    id=g.user.id)
  # Returns:

    # {
    #     "username": "admin",
    #     "email": "admin@localhost",
    #     "id": 42
    # }







if __name__ == '__main__':
  app.run(debug=True)
