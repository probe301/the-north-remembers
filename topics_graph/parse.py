

import json
from pprint import pprint
def test_parse():
  path = 'crawlResult copy.json'
  print(path)
  with open(path, encoding='utf-8') as file:
    s = file.read()
    j = json.loads(s, )
    pprint(j)