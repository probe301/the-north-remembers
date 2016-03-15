
import time
import os
import shutil
import re
from pylon import puts
from pylon import datalines
from pylon import enumrange





####### ##       #####   ###### ##   ##
##      ##      ##   ## ##      ##  ##
######  ##      #######  #####  ######
##      ##      ##   ##      ## ##   ##
##      ####### ##   ## ######  ##   ##


from flask import Flask
from flask import render_template
from flask import Response
app = Flask(__name__)




# 知乎马克 ZhihuMark


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


@app.route('/question/<qid>/answer/<aid>')
def zhihu_question_answer(qid, aid):
  # https://www.zhihu.com/question/33918585/answer/89678373
  from mark import fetch_answer
  puts('fetching zhihu / question / answer')
  mdfile = fetch_answer('https://www.zhihu.com/question/{}/answer/{}'.format(qid, aid))
  return Response(mdfile, mimetype='text/text')
  # return 'zhihu qid {} aid {}'.format(qid, aid)


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
