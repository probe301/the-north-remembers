
from crawler.zhihu import fetch_zhihu_answer
from crawler.zhihu import parse_answer
from crawler.zhihu import parse_question

from pprint import pprint
from crawler.zhihu import parse_question
from crawler.zhihu import parse_answer
from crawler.zhihu import zhihu_detect_with_client
from crawler.zhihu import zhihu_detect
from crawler.zhihu import get_comments_api_v4
from crawler.zhihu import get_valuable_conversations_api_v4

from crawler.zhihu import fetch_zhihu_article

fetch_zhihu_article('https://zhuanlan.zhihu.com/p/37509962')