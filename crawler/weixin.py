

import re

import time

import html2text
from jinja2 import Template

import time
import tools
from tools import datalines

import shutil

from urllib.parse import unquote
from jinja2 import Template
import re

import requests
from pyquery import PyQuery as pq
from tools import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')




def weixin_blog_html2md(html):
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







def fetch_weixin_article_page(url):
  content = requests.get(url).content
  doc = pq(content)
  msg = doc('.page_msg').text()
  if msg:
    return { 'metadata': {
                          'title': '-1', 
                          'author_name': '-1',
                          'author_id': '-1',
                          'publish_date': '',
                          'fetch_date': tools.time_now_str(),
                          'count': 0,
                          'url': url,
                        },
            'content': msg,
          }

  title = doc('#activity-name').text().strip()
  author_name, author_id, _ = doc.find('#js_profile_qrcode').text().strip().split('\n')
  author_id = author_id.split(' ')[-1]
  publish_date = doc('#publish_time').text().strip()
  body = doc('#js_content').html()
  body = weixin_fix_markdown(weixin_blog_html2md(body))

  # publish_date = parse_json_date(article.updated_time)
  fetch_date = tools.time_now_str()

  # TODO: 加上 header bg 图

  metadata = {
    'title': title, 
    'author_name': author_name,
    'author_id': author_id,
    'publish_date': publish_date,
    'fetch_date': fetch_date,
    'count': len(body),
    'url': url,
  }
  return { 'metadata': metadata,
           'content': body.strip(),
         }




def test_rss():
  feed = 'http://www.vccoo.com/a/vzr62/rss.xml'
  feed = 'http://www.vccoo.com/v/f5b94c'
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    # 'Referer': 'http://www.vccoo.com',
    # 'Accept-Encoding': 'gzip, deflate, sdch',
  }

  # cookies = {'ASP.NET_SessionId': 'kbnrrb45ovcumwfy25xooxec'}
  s = requests.Session()
  r = s.get(feed, headers=headers)
  log(r.content[:400])
  # r = s.get(feed, headers=headers, stream=True)
  # log(r)












def test_knowledgewealth():

  s_finish = '''
    # zhaohaoyang
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672803&idx=1&sn=032a476cef35b974ed5f39e9b07fefa9#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672799&idx=1&sn=27453994634bb0245e9b4aaea0942b2b#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672791&idx=1&sn=c72f74615feb49c29d2d039bd20d8c09#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672788&idx=1&sn=4851efd729fa6b28c6335b9ba911393b#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672773&idx=1&sn=c06f03b9f0d72a33281e4ff71a09b2ee#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672765&idx=1&sn=d7472177530167c4031e8bfda8e74ef1#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672749&idx=1&sn=f0fbfcf12ae9f691e7ec61730613b0fb#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672739&idx=1&sn=e72ac99a37b0076dcd28446814aaa702#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672734&idx=1&sn=bbb6f4805603e04917cf1a7c99f328f6#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672727&idx=1&sn=102ab61d5d2299bffe26087f3f190b23#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672721&idx=1&sn=736094e9955e5bead81524fecf90bc7f#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672712&idx=1&sn=5f0ec02b5191a0cfea1067e25b8a844d#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672708&idx=1&sn=4b1f7d3e02a52c50217d8d274c10e325#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672687&idx=1&sn=03e8a22e114f6de57865a5a26e32f640#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=2650672679&idx=1&sn=aa72c26e937580b45df811e0efc957ee#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=403189023&idx=1&sn=8f5774a37f965d3e33901172d191ac91#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402667616&idx=1&sn=bff275d46d168f9844d1ebacc5d70ec6#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402419132&idx=1&sn=3d4c50c89f487cd2de18e381d339f0e8#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402782125&idx=1&sn=8ffaad2bc1e94f2f550f02eb01759d69#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402997622&idx=1&sn=f9eaa33a7d8894cc754b84949d89d096#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402265925&idx=1&sn=5de1f01d0c586185a06f71b0818e3568#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402904215&idx=1&sn=c2c52de290010b9af4b0361b3e3290ce#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=403020365&idx=1&sn=0937c509bf719c7735ea0c834a82b602#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402345108&idx=1&sn=b41b60214c36cfb20e9a05e9d2a35704#rd
    http://mp.weixin.qq.com/s?__biz=MjM5NzE2NTY0Ng==&mid=402149805&idx=1&sn=76473bc0189c5b70bb438ef0dfd326a1#rd
  '''


  zhenjiaolujun = '''
    # 今年我见过最惊艳的项目，没有之一
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691376&idx=1&sn=caccc74c9b639b3f824821fc3d02f04b&chksm=84147a83b363f395d433bdc9706018c2e660f72938c404841f272aa42c8798f2307ba5dfff3e#rd
    # 今天下午4点，卢俊在斗鱼直播
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691376&idx=2&sn=4cb8b4b8e133d2c5af847f3f9b39a4e8&chksm=84147a83b363f3957847479f99a31836bf6c04e07e9154a2d18c38ae3957af54366243f7b370#rd
    # 商业地产的希望之处，来自走投无路
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691331&idx=1&sn=8c0756fa629940953ac8e353d662bf8d&chksm=84147ab0b363f3a6460df0e4581c0853f31b68a0bb0d729a52374af38414cd44fb9596e56205#rd
    # 这是一场霸气的发布会
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691331&idx=2&sn=f672fb6ba3c0ef904d42f94d920bfc4e&chksm=84147ab0b363f3a6cfd9694d4808534093373c57828bdced1ce78ba5940d81ed1e903190abd9#rd
    # 做商业地产，也许可以听听这段异类的观点
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691310&idx=1&sn=dc8a15db8b83762102c782cff6d080c5&chksm=84147a5db363f34b0d0b7ff6590bd517e4ab20c7a893328a3caab5cd4cab4c7bcf67a3d06282#rd
    # 马云开放湖畔大学，我成了第一批学员
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691279&idx=2&sn=370e37b815ff58e8266ac09d53182949&chksm=84147a7cb363f36ab4244a9219e197b00acbdcfbf5d6f53897c3389e5314e12014df939cfbeb#rd
    # 20天，我卖了1200套……
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691260&idx=2&sn=931dab791cba8cce5dd14fb1e4ed5f07&chksm=84147a0fb363f319b4e22e03397bc968ea28ac9cc3ffd81c6dedd0c58146919d574986a9d025#rd
    # 共享经济的前提是共享文明
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691260&idx=1&sn=49654f335b8ec54086e2776de0f37b62&chksm=84147a0fb363f31928698a98025dc9cad27992a87c951c0344a7661c42a5a3533d511ebb8bbf#rd
    # 哪有什么爱恨情仇，郭曹互杀早已在各行各业千百回上演
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691255&idx=1&sn=66a0d824bf66ec612dd011a49046f0bc&chksm=84147a04b363f3126057870680fa02ac3664f4bafc727c5efb0c6cd85184ba79d0115c9a39ac#rd
    # 微微一笑大结局，偶像剧的剧情但三观比谁都正
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691169&idx=1&sn=00fd50fa72bbd58e380858bba720a96b&chksm=84147bd2b363f2c41cff8324d2d6a59ff94baf4e860a18625531e7d481b31c1c633843e426aa#rd
    # 我想说个故事：地产人的无能为力和无可奈何
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691115&idx=1&sn=bace23bc811274b0b420c9a481a21a69&chksm=84147b98b363f28ea4262d28a1a9bf91d4da9a04b15c58bfb4a395b1d48a9884381fce16591e#rd
    # 今天下午四点，我开好房等你……
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691115&idx=4&sn=d16eca2b401ca1c5bc1ffa48eb4fa09d&chksm=84147b98b363f28ea37d3afc7aaef6879522da9a006083b54c9ab17f10e4c5c299578592275d#rd
    # 天蓬元帅撩嫦娥为啥会失败？
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691115&idx=3&sn=5ab5881be36243f0baffd234c9dc358b&chksm=84147b98b363f28e2eb6d313f924948d797d05dfac2b49d7b0a196d6af351a03e490d3afacab#rd
    # 如果有一天我不见了，来这个小号找我
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691115&idx=2&sn=c40b165adec5d261860b9b2b41bcedfc&chksm=84147b98b363f28e08f93ae992be7359ffe7878fb1d650e2629b386ebcc0e69d65b8beb1db96#rd
    # 明天，我开好房等你……
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691110&idx=2&sn=911dfaca546980abfb1d6a0f3168d12e#rd
    # 为了买房，我们会不会过的像这部三级片一样
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691110&idx=1&sn=a21361e29cfd24ebbd0050bf8bc33850#rd
    # 这么多年过去了，它依然是上海地产史上第一奇葩
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691045&idx=1&sn=227e10184742f6cca4b3830764f3b141#rd
    # 深夜，一个地产人走进方丈的禅房
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690966&idx=1&sn=a5b384dce9f040405c1e3be37beef581#rd
    # 疯了
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690948&idx=1&sn=8bfb9cba2915b34d9873eea746bf5448#rd
    # 这可能是当下三观最正的买房建议了
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690955&idx=1&sn=d105d46dcc2f22495b6416dc4b293da3#rd
    # 高低配让开发商赚了钱，却让我们忘了别墅真正的模样
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690955&idx=2&sn=9f8a8c23ca60ac68d1b8647f8d80dd8f#rd
    # 易居合并，哪有无缘无故的爱
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690930&idx=1&sn=845fc27ea2e2521074ca4a01dd2198b4#rd
    # 从这两个撩妹的故事，学会如何送客户礼物
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690930&idx=2&sn=d485a48e795182175f04b8c105701adb#rd
    # 地产人的小目标都在这里
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690928&idx=1&sn=69c273ebc040b9622d24e57fffcef7a0#rd
    # 生意最好的时候，我却关闭了购房咨询服务
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690886&idx=1&sn=383d22499d8e5875fc89df755f8406f7#rd
    # 此刻，房地产这口饭，没人能够下咽
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690883&idx=1&sn=b1660e5c170a4e1ef00c231c713df387#rd
    # 这可能是关于联合办公空间设计最棒的书
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690883&idx=2&sn=a9550df4c15e28b0dc1a0071ca669343#rd
    # 90+出了个从里到外真正的好三房
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690845&idx=1&sn=ade8502a5d066dea1c54d297e2ccfd4e#rd
    # 卖断货的真叫卢俊笔记本，又上架啦
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690845&idx=2&sn=e51f3fb84274a978479db9ee7c932840#rd
    # 令我不安的地产鸦片战争终归还是来了
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690826&idx=1&sn=313e015789f514a3318b1de88524f6f8#rd
    # 卢俊定制公交卡获奖名单公布！看看有你么~
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690826&idx=2&sn=2e02761c1dc5a50ce07c80f261f388ec#rd
    # 上海的2040，去年纲要和今年草案有几个微妙变化
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690797&idx=1&sn=26e6ebddbcb0bb171c36f5bc193c34da#rd
    # 从这两个撩妹的故事，学会如何送客户礼物
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690797&idx=2&sn=258820d645eda2040585310e7f250dc5#rd
    # 每个人心中都有一个猴子捞月的故事【LU的店】
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690753&idx=2&sn=78d112528fe4922f3e72481943f9d1d0#rd
    # 丢人啊，在奥运会上贴牛皮癣，还是做房地产的
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690753&idx=1&sn=f13898a65d06589cf82a2efdea73c59e#rd
    # 千年老二未必悲情，这是李宗伟即将开始的另一种身份
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690733&idx=1&sn=95e30a0b611a44773dd2ffaf4daf7df7#rd
    # 为这个盒子花的心思，比一个楼盘还多
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690718&idx=1&sn=6b9eb5bfd633996babdc9d11f1fc95f1#rd
    # 再重温下《美人鱼》里那场土拍狂欢吧
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690714&idx=1&sn=19fb48f860a6c4ee287ec971d82f039d#rd
    # 顾村地王要出，这一次值多少钱
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690678&idx=2&sn=7ce9f73f5be0bb63c926928a8b7bd7cd#rd
    # 一个只有女人看得懂的户型
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690678&idx=1&sn=4362d9c90d67c3787470297f4d08a940#rd
    # 说三个成功的故事，却是劝你别碰商业地产
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690668&idx=1&sn=914c6163f8692f4c013d9d30f758145b#rd
    # 这是首严肃的地产狗之歌
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690645&idx=1&sn=7164effd38bdfa4f7fc9ebebd4183571#rd
    # 联合办公们，你真的懂创业者的需求？
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690646&idx=1&sn=b78f2800758b1c68d70aec0beace3509#rd
    # 做地产这行，谁没碰到点极品事
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690638&idx=1&sn=253cc878e53c3972b81edd8bb97ec158#rd
    # 奥运画风都变了，房地产却高傲的没有一丝改变
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690636&idx=1&sn=d7b516ea9cae72842afd2029b8ee53e9#rd
    # 一个没人敢复制的项目
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690628&idx=1&sn=26a87fc2b35d3c45c89246149b8dc083#rd
    # 地产人，我们必须试着接受这些惨烈现实
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690560&idx=1&sn=59cc3ffc26d03ba2e6d3c4f1995dbf7f#rd
    # 我最关心的三个楼市问题，这次都有了答案
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690547&idx=1&sn=bbb3b7023c621b58190f561021e7bdd1#rdok
    # 恒大买万科，无非是拿回一个月前的头条而已
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690540&idx=1&sn=b976bf014f1c36524e38db729c69f978#rd
    # 地产这扇门已经对一些人关闭
    http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690522&idx=1&sn=a4635c06a9eee3a612f97414872c4c1c#rd


  '''
  zhenjiaolujun = 'http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652690646&idx=1&sn=b78f2800758b1c68d70aec0beace3509#rd'

  for url in datalines(s_finish):
    page = fetch_weixin_blog(url)
    path = format_weixin_filename(page['title'] + '.md')
    print(page['content'], file=open('zhao/' + path, 'w', encoding='utf-8'))









def test_follow_redirect():
  url = 'http://www.iwgc.cn/link/2655245'
  url = 'http://www.vccoo.com/v/f5b94c'
  new_url = follow_redirect(url)
  log(new_url)
  # => http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691331&idx=1&sn=8c0756fa629940953ac8e353d662bf8d&chksm=84147ab0b363f3a6460df0e4581c0853f31b68a0bb0d729a52374af38414cd44fb9596e56205&scene=0#rd














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

  url = 'http://mp.weixin.qq.com/s?__biz=MzA4MzA3MzExNg==&mid=2652691115&idx=1&sn=bace23bc811274b0b420c9a481a21a69&chksm=84147b98b363f28ea4262d28a1a9bf91d4da9a04b15c58bfb4a395b1d48a9884381fce16591e&scene=0#wechat_redirect'

  # url = 'http://mp.weixin.qq.com/s?src=3&timestamp=1473128750&ver=1&signature=P9LX1wt*2XYCHzwdy16NomH3-DFE80OK3aBvpnQuW6a0uWedkoFoqcpAb0mSw9Mo5UAfmbjkNEwcGdOU4s1Et2tojz4nyq8tELr-mbPKZ1Lyb1Kb5pbp6M60SA2Ldg2EF21K8iMDNIScALKdLllw-QrOYtJyBo5N0yhm3mvyX-g=' # 马克思主义经济观 utl type 2 # 这种url里有评论但是timestamp会过期
  page = fetch_weixin_blog(url)

  path = format_weixin_filename(page['title'] + '.md')
  print(page['content'], file=open(path, 'w', encoding='utf-8'))










def test_extract_from_feedly():
  s = '''


  '''
  for m in re.findall(re.compile(r'http://www.iwgc.cn/link/\d+" title="Open in a tab"'), s):
    log(m)


  lujun = '''
    http://www.iwgc.cn/link/2670235
    http://www.iwgc.cn/link/2670236
    http://www.iwgc.cn/link/2655245
    http://www.iwgc.cn/link/2655246
    http://www.iwgc.cn/link/2646045
    http://www.iwgc.cn/link/2635896
    http://www.iwgc.cn/link/2635897
    http://www.iwgc.cn/link/2619649
    http://www.iwgc.cn/link/2619650
    http://www.iwgc.cn/link/2604910
    http://www.iwgc.cn/link/2589555
    http://www.iwgc.cn/link/2574680
    http://www.iwgc.cn/link/2574681
    http://www.iwgc.cn/link/2574682
    http://www.iwgc.cn/link/2574683
    http://www.iwgc.cn/link/2560099
    http://www.iwgc.cn/link/2560100
    http://www.iwgc.cn/link/2551255
    http://www.iwgc.cn/link/2541138
    http://www.iwgc.cn/link/2525326
    http://www.iwgc.cn/link/2510911
    http://www.iwgc.cn/link/2510912
    http://www.iwgc.cn/link/2496765
    http://www.iwgc.cn/link/2484168
    http://www.iwgc.cn/link/2484169
    http://www.iwgc.cn/link/2479068
    http://www.iwgc.cn/link/2464949
    http://www.iwgc.cn/link/2452090
    http://www.iwgc.cn/link/2432996
    http://www.iwgc.cn/link/2432997
    http://www.iwgc.cn/link/2405024
    http://www.iwgc.cn/link/2405026
    http://www.iwgc.cn/link/2390655
    http://www.iwgc.cn/link/2390656
    http://www.iwgc.cn/link/2375201
    http://www.iwgc.cn/link/2375202
    http://www.iwgc.cn/link/2365437
    http://www.iwgc.cn/link/2358060
    http://www.iwgc.cn/link/2358061
    http://www.iwgc.cn/link/2342950
    http://www.iwgc.cn/link/2328750
    http://www.iwgc.cn/link/2314370
    http://www.iwgc.cn/link/2314371
    http://www.iwgc.cn/link/2300987
    http://www.iwgc.cn/link/2286410
    http://www.iwgc.cn/link/2282945
    http://www.iwgc.cn/link/2267813
    http://www.iwgc.cn/link/2253591
    http://www.iwgc.cn/link/2239724
    http://www.iwgc.cn/link/2225524
    http://www.iwgc.cn/link/2211918
    http://www.iwgc.cn/link/2197250
    http://www.iwgc.cn/link/2186136
    http://www.iwgc.cn/link/2178762
    http://www.iwgc.cn/link/2163341
    http://www.iwgc.cn/link/2146572
    http://www.iwgc.cn/link/2133531
    http://www.iwgc.cn/link/2133532
    http://www.iwgc.cn/link/2104149
    http://www.iwgc.cn/link/2088232
    http://www.iwgc.cn/link/2085611
    http://www.iwgc.cn/link/2085612
    http://www.iwgc.cn/link/2060372
    http://www.iwgc.cn/link/2053396
    http://www.iwgc.cn/link/2053397
    http://www.iwgc.cn/link/2032724
    http://www.iwgc.cn/link/2019454
    http://www.iwgc.cn/link/1975169
    http://www.iwgc.cn/link/1961362
    http://www.iwgc.cn/link/1948955
    http://www.iwgc.cn/link/1935489
    http://www.iwgc.cn/link/1932479
    http://www.iwgc.cn/link/1906131
    http://www.iwgc.cn/link/1896068
    http://www.iwgc.cn/link/1878990
    http://www.iwgc.cn/link/1878991
    http://www.iwgc.cn/link/1865523
    http://www.iwgc.cn/link/1855315
    http://www.iwgc.cn/link/1825157
    http://www.iwgc.cn/link/1813284
    http://www.iwgc.cn/link/1799826
    http://www.iwgc.cn/link/1797474
    http://www.iwgc.cn/link/1782863
    http://www.iwgc.cn/link/1782864
    http://www.iwgc.cn/link/1761694
    http://www.iwgc.cn/link/1755062
    http://www.iwgc.cn/link/1734276
    http://www.iwgc.cn/link/1729074
    http://www.iwgc.cn/link/1716920
    http://www.iwgc.cn/link/1697153
    http://www.iwgc.cn/link/1697155
    http://www.iwgc.cn/link/1684030
    http://www.iwgc.cn/link/1664936
    http://www.iwgc.cn/link/1664939
    http://www.iwgc.cn/link/1653583
    http://www.iwgc.cn/link/1653584
    http://www.iwgc.cn/link/1653585
    http://www.iwgc.cn/link/1641499
    http://www.iwgc.cn/link/1636158
    http://www.iwgc.cn/link/1612030
    http://www.iwgc.cn/link/1605039
    http://www.iwgc.cn/link/1589824
    http://www.iwgc.cn/link/1573083
    http://www.iwgc.cn/link/1573087
    http://www.iwgc.cn/link/1560570
    http://www.iwgc.cn/link/1560571
    http://www.iwgc.cn/link/1549146
    http://www.iwgc.cn/link/1549147
    http://www.iwgc.cn/link/1537436
    http://www.iwgc.cn/link/1537437
    http://www.iwgc.cn/link/1526917
    http://www.iwgc.cn/link/1526918
    http://www.iwgc.cn/link/1526919
    http://www.iwgc.cn/link/1511471
    http://www.iwgc.cn/link/1489468
    http://www.iwgc.cn/link/1489469
    http://www.iwgc.cn/link/1477584
    http://www.iwgc.cn/link/1477585
    http://www.iwgc.cn/link/1477586
    http://www.iwgc.cn/link/1465988
    http://www.iwgc.cn/link/1465989
    http://www.iwgc.cn/link/1465990
    http://www.iwgc.cn/link/1445356
  '''
