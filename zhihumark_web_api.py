

from flask import Flask
from flask import render_template
app = Flask(__name__)



# 知乎马克 ZhihuMark


@app.route('/')
@app.route('/index')
def index():
    user = {'nickname': 'Miguel'}  # fake user
    return render_template("index.html",
                          title = 'Home',
                          user = user)


@app.route('/hello')
def hello():
    return 'Hello World'


@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username


@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id



if __name__ == '__main__':
    app.run(debug=True)