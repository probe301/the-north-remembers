

import re
import os
import time
import html2text
import time
import tools
import shutil
import re
import requests

from tools import create_logger
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')


UA = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.13 Safari/537.36"
session = requests.Session()

def common_get(url, cache=True, referer=None):
  '''# requests with UA, referer, cache'''
  md5 = tools.md5(url, 6)
  file_url = tools.remove_invalid_char(','.join(url.split('/')[2:]))
  cache_file = f'temp/{file_url}-{md5}'
  
  if cache and os.path.exists(cache_file):
    modify_time = tools.time_now_stamp() - os.path.getmtime(cache_file)
    if modify_time < 3600: # 在60分钟以内修改
      log(f'using cached `{url}`\n    `{cache_file}`')
      return tools.text_load(cache_file)

  # 没有 cache, 需要抓取
  if referer is None: referer = '/'.join(url.split('/')[:3])
  log(f'referer {referer}')
  headers = { "User-Agent" : UA, "Referer": referer}
  resp = session.get(url, headers=headers)
  log(f'resp.status_code { resp.status_code }')
  if resp.status_code != 200:
    raise requests.RequestException(f'can not get url {url}, resp.status_code={resp.status_code}')

  data = bytes.decode(resp.content, encoding='utf-8')
  if cache: tools.text_save(data=data, path=cache_file)
  return data





























