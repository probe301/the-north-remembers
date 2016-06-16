


from zhihu import ZhihuClient


class ZhihuParseError(Exception):
  pass

def generate_cookie():
  # pob....@gmail.com p...
  ZhihuClient().create_cookies('cookies.json')
# generate_cookie()



client = ZhihuClient('cookies.json')


print(client)
