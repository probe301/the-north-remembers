

import re
# import json
# import sys
# import random
import time
from pyquery import PyQuery
# import requests
import html2text
from jinja2 import Template



def format_weixin_url(url):
  '''需要url中的4个参数
     __biz=MzI3MDE0NzI0MA==
   & mid=2650991378
   & idx=1
   & sn=7fb39f8f5b8d2b98751fd5515a7a4623
  '''
  # 'http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690955&idx=2&sn=9f8a8c23ca60ac68d1b8647f8d80dd8f&scene=0#rd'

  if 'mp.weixin.qq.com' not in url:
    raise ValueError('cannot parse WeiXin url {}'.format(url))

  url = url.split('#')[0]
  if 'scene=' in url:
    url = re.sub(r'\&scene=\d+', '', url)
  return url


def weixin_blog_html2md(html):

  if html is None:
    raise ValueError('html is none')
  def replace_section_to_p(html):
    p = r'(</?)section'
    html = re.sub(p, r'\1p', html)
    return html
  def patch_weixin_blog_images(html):
    # <img data-s="300,640" data-type="jpeg" data-src="http://mmbiz.qpic.cn/mmbiz/ia241nPa7bNwribnX...KA/0?wx_fmt=jpeg" data-ratio="2.197802197802198" data-w="364"/>
    p = r'<img.+?data-src="(.+?)".+?/>'
    html = re.sub(p, r'<img src="\1" />', html)
    return html

  html = patch_weixin_blog_images(html)
  html = replace_section_to_p(html)

  h2t = html2text.HTML2Text()
  h2t.body_width = 0
  ret = h2t.handle(html).strip()
  ret = '\n'.join(p.rstrip() for p in ret.split('\n'))
  return ret




def weixin_fix_markdown(text):
  # 去除 html2text 转换出来的 strong 和 link 的多余空格
  # ![](http://mmbiz.qpic.cn/mmbiz_jpg/52ChNWeJui...EwrkQ/0?wx_fmt=jpeg)
  pattern_img_start_inline = re.compile(r'\n*(\!\[\]\(http://mmbiz\.qpic\.cn.+?\))\n*')
  # def replace_img_start_inline(mat):
  #   # 保证生成的 *.md 图片在新的一行
  #   s = mat.group(0)
  #   while not s.startswith('\n\n'):
  #     s = '\n' + s
  #   while not s.endswith('\n\n'):
  #     s = s + '\n'
  #   return s
  pattern_multiple_newline = re.compile(r'\n{4,}') # 连续4+换行的都压缩到3个

  text = pattern_img_start_inline.sub(r'\n\n\1\n\n', text)
  text = pattern_multiple_newline.sub('\n\n\n', text)
  text = re.sub(r'\*\*\n{0,1}\*\*', '', text)
  text = re.sub(r'\*\*\n{2,4}\*\*', ' ', text)
  return text








def fill_template(url=None, title=None, post_date=None, fetch_date=None,
                  content=None, author=None):

  # 需要 header image
  tmpl_string = '''
### {{title}}

    author: {{author}}
    post_date: {{post_date}}
    fetch: {{fetch_date}}
    url: {{url}}


{{content}}






'''
  template = Template(tmpl_string)
  return template.render(**locals())




def fetch_weixin_blog(url):
  # t = d('div#js_article')
  # md = html2md(t.text())
  # print(md)
  url = format_weixin_url(url)
  doc = PyQuery(url=url)('div#js_article')

  content = doc('#js_content')
  # print(content.html(), file=open('test_wx.html', 'w', encoding='utf-8'))
  title = doc('#activity-name').text().strip()
  author = doc('#post-user').text().strip()
  post_date = doc('#post-date').text().strip()


  # TODO: 加上 header bg 图

  print(content.html(), file=open(title + '.debug.html', 'w', encoding='utf-8'))
  page = fill_template(title=title,
                       post_date=post_date,
                       fetch_date=time.strftime('%Y-%m-%d'),
                       content=weixin_fix_markdown(weixin_blog_html2md(content.html())),
                       author=author,
                       url=url)

  return {'title': title + ' - ' + author, 'content': page}


def format_weixin_filename(title):
  invalid_chars = list('|?"\'')
  invalid_chars.append('\xa0')
  return ''.join(' ' if c in invalid_chars else c for c in title)

def test_fetch():

  url = 'http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=403189023&idx=1&sn=8f5774a37f965d3e33901172d191ac91'  #
  url = 'http://mp.weixin.qq.com/s?__biz=MzI3MDE0NzI0MA==&mid=2650991368&idx=2&sn=efc68055efff53061cedb8eba58bf5fd' # 伦敦

  url = 'http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690164&idx=1&sn=29d2b67be37d2bbda10b981a8b9ef420' # 地王
  url = 'http://mp.weixin.qq.com/s?__biz=MzI3MDE0NzI0MA==&mid=2650991378&idx=1&sn=7fb39f8f5b8d2b98751fd5515a7a4623' # 劳工运动会毁于精英主义吗

  url = 'http://mp.weixin.qq.com/s?timestamp=1473058983&src=3&ver=1&signature=2gTbvfvRieZfUb99JUzpk8n1cqpTxqaTB4IdjkedT1N7AOtwiswxp84*DOJJ6r5s*ffnXW2O6Z45OmzBUtyMA4XDnQbg2dPHB7b6Q1SUel8Lt8Z5KL5pNpQHaMYwiRdcFju9n8l5kG6wbU-dA-OaJSfneBj4g7V3GkAGiJghmIg=' # 新海诚《你的名字》

  url = 'http://mp.weixin.qq.com/s?timestamp=1473128685&src=3&ver=1&signature=twQkNHc5vMmsmjOsxmUnSuJkGEZrtosWQptMdO7hGdT4UTfiTPnSiK88LO9FQXlqTSXf9dl64oFAV8sYjQyNTK2Weev-Z0dEWaK772DIVNBpX4EZjQpcRAwGku2*YQG32*QhJxbl-SHVMZYByGV5GQm5Dku2N*eN2WQhBvYA8KU=' # 新海诚《你的名字》on other timestamp
  url = 'http://mp.weixin.qq.com/s?__biz=MzAxMjcyODExMA==&mid=2652273018&idx=1&sn=984cb5e9daea270f91a536a69330d670' # 新海诚《你的名字》 permalink

  url = 'http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690955&idx=2&sn=9f8a8c23ca60ac68d1b8647f8d80dd8f' # 高低配让开发商赚了钱

  url = 'http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672791&idx=1&sn=c72f74615feb49c29d2d039bd20d8c09'  # 马克思主义经济观

  # url = 'http://mp.weixin.qq.com/s?src=3&timestamp=1473128750&ver=1&signature=P9LX1wt*2XYCHzwdy16NomH3-DFE80OK3aBvpnQuW6a0uWedkoFoqcpAb0mSw9Mo5UAfmbjkNEwcGdOU4s1Et2tojz4nyq8tELr-mbPKZ1Lyb1Kb5pbp6M60SA2Ldg2EF21K8iMDNIScALKdLllw-QrOYtJyBo5N0yhm3mvyX-g=' # 马克思主义经济观 utl type 2 # 这种url里有评论但是timestamp会过期
  page = fetch_weixin_blog(url)

  path = format_weixin_filename(page['title'] + '.md')
  print(page['content'], file=open(path, 'w', encoding='utf-8'))




def test_decode_base64():


  import base64
  a = 'MjM5NzE2NTY0Ng=='  # => 2397165646
  b = '2gTbvfvRieZfUb99JUzpk8n1cqpTxqaTB4IdjkedT1N7AOtwiswxp84*DOJJ6r5s*ffnXW2O6Z45OmzBUtyMA4XDnQbg2dPHB7b6Q1SUel8Lt8Z5KL5pNpQHaMYwiRdcFju9n8l5kG6wbU-dA-OaJSfneBj4g7V3GkAGiJghmIg='


  print(base64.b64decode(a))
  print(base64.b64decode(b), file=open('1.txt', 'w',))

def test_decode_utf8():

  # decoded = encoded.decode('utf-8')
  # print(decoded)
  original = b"\xE5\x85\x84\xE5\xBC\x9F\xE9\x9A\xBE\xE5\xBD\x93 \xE6\x9D\x9C\xE6\xAD\x8C"
  original = b"\xDA\x04\xDB\xBD\xFB\xD1\x89\xE6_Q\xBF}%L\xE9\x93\xC9\xF5R\xAAS\xC6\xA6\x93\x07\x82\x1D\x8EG\x9DOS{\x00\xEBP\x8A\xCC1\xA7\xCE\x038\x92Z\xAF\x9B\x1F~U\xD6\xD8\xEE\x99\xE3\x93\xA6\xCC\x15-\xC8\xC08\\9\xD0N\R\x9D<P{O\xA45IG\xA5\xF0\xBB|G\x92\x8B\xE6\x93I@V\x8CC\x08\x91U\xC1C\xBB\xD9\xFC\x97\x99\x06\xEB\x06\xD4T\x03\x9A%'\xE7X\x18\xF8\x83\xB5W\x1A@\x06\x88\x98!\x98\x88"
  import codecs
  encoded4 = codecs.decode(original, 'utf-8')
  print(encoded4)
































































from selenium import webdriver
import selenium
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup
import requests
import logging
import random

BASE_URL = 'http://weixin.sogou.com'

UA = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36"

def get_html(url):
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = (
        UA
    )
    dcap["takesScreenshot"] = (False)
    try:
        driver = webdriver.PhantomJS(desired_capabilities=dcap, service_args=['--load-images=no'])
        driver.set_page_load_timeout(240)
        driver.command_executor._commands['executePhantomScript'] = ('POST', '/session/$sessionId/phantom/execute')

        driver.execute('executePhantomScript', {'script': '''
            var page = this; // won't work otherwise
            page.onResourceRequested = function(requestData, request) {
                if ((/http:\/\/.+?\.css/gi).test(requestData['url']) || requestData['Content-Type'] == 'text/css') {
                    console.log('The url of the request is matching. Aborting: ' + requestData['url']);
                    request.abort();
                }
            }
            ''', 'args': []})
    except selenium.common.exceptions.WebDriverException:
        return None
    try:
        driver.get(url)
        html = driver.page_source
    except Exception as e:
        html = None
        logging.error(e)
    finally:
        driver.quit()
    return html

def get_html_direct(url, cookies=None):
    if not cookies:
        cookies = update_cookies()
    headers = {"User-Agent": UA}
    r = requests.get(url, headers=headers, cookies=cookies, timeout=20)
    return r.text

def get_account_info(open_id=None, link=None, cookies=None):
    url = None
    if open_id:
        url = BASE_URL + '/gzh?openid=' + open_id
    if link:
        url = link
    #html = get_html(url)
    html = get_html_direct(url, cookies=cookies)
    #print(html)
    if not html:
        return None
    soup = BeautifulSoup(html)
    info_box = soup.select('#weixinname')[0].parent
    account_info = {}
    account_info['account'] = info_box.select('h4 span')[0].text.split('：')[1].strip()
    account_info['name'] = info_box.select('#weixinname')[0].text
    account_info['address'] = url
    account_info['description'] = info_box.select('.sp-txt')[0].text
    img_list = soup.select('.pos-box img')
    account_info['logo'] = soup.select(".img-box img")[0]['src']
    account_info['qr_code'] = img_list[1]['src']
    return account_info


def parse_list(open_id=None, link=None):
    if open_id:
        url = BASE_URL + '/gzh?openid=' + open_id
    elif link:
        url = link
    else:
        return None
    html = get_html(url)
    if not html:
        return None
    soup = BeautifulSoup(html)
    ls = soup.select('#wxbox .txt-box')
    link_list = []
    for item in ls:
        item_dict = {}
        item_dict['title'] = item.a.text
        item_dict['link'] = item.a['href']
        link_list.append(item_dict)
    return link_list


def parse_essay(link):
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    try:
        r = s.get(link)
        html = r.text
        soup = BeautifulSoup(html)
        essay = {}
        p = re.compile(r'\?wx_fmt.+?\"')
        content = str(soup.select("#js_content")[0]).replace('data-src', 'src')
        essay['content'] = re.sub(p, '"', content)
        essay['name'] = soup.select('#post-user')[0].text
        essay['date'] = soup.select('#post-date')[0].text
    except Exception:
        return None

    return essay


def weixin_search(name, cookies=None):
    url = BASE_URL + '/weixin?query=' + name
    #html = get_html(url)
    html = get_html_direct(url, cookies=cookies)
    print(html)
    soup = BeautifulSoup(html)
    ls = soup.select("._item")
    search_list = []
    for item in ls:
        account_info = {}
        account_info['account'] = item.select('h4 span')[0].text.split('：')[1].strip()
        account_info['name'] = item.select('.txt-box h3')[0].text
        account_info['address'] = BASE_URL + item['href']
        account_info['open_id'] = item['href'].split('openid=')[1]
        account_info['description'] = item.select('.sp-txt')[0].text
        account_info['logo'] = item.select('.img-box img')[0]['src']
        try:
            account_info['latest_title'] = item.select('.sp-txt a')[0].text
            account_info['latest_link'] = item.select('.sp-txt a')[0]['href']
        except IndexError:
            pass
        search_list.append(account_info)
        #print(account_info)
    return search_list

def update_cookies():
    s = requests.Session()
    headers = {"User-Agent": UA}
    s.headers.update(headers)
    url = BASE_URL + '/weixin?query=123'
    r = s.get(url)
    if 'SNUID' not in s.cookies:
        p = re.compile(r'(?<=SNUID=)\w+')
        s.cookies['SNUID'] = p.findall(r.text)[0]
        suv = ''.join([str(int(time.time()*1000000) + random.randint(0, 1000))])
        s.cookies['SUV'] = suv
    return s.cookies


# if __name__ == '__main__':
#     open_id = 'oIWsFt3nvJ2jaaxm9UOB_LUos02k'
#     #print(weixin_search('简书'))
#     cookies = update_cookies()
#     t0 = time.time()
#     print(get_account_info(open_id,cookies=cookies))
#     #print(weixin_search("简书",cookies))
#     t1 = time.time()
#     print(parse_list(open_id))
#     t2 = time.time()
#     print(parse_essay('http://mp.weixin.qq.com/s?__biz=MjM5NjM4OTAyMA==&mid=205212599&idx=4&sn=6a1de7a7532ba0bcbc633c253b61916f&3rd=MzA3MDU4NTYzMw==&scene=6#rd'))
#     t3 = time.time()
#     print(t1-t0, t2-t1, t3-t2)
