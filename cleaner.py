

import tools
from tools import parse_type
from tools import UrlType
from tools import create_logger
import re
log = create_logger(__file__)
log_error = create_logger(__file__ + '.error')


def fix_md_title(mdtxt, header_level=3):
  top_level = 100
  for line in mdtxt.splitlines():
    if line.startswith('#'):
      tag = line.split(' ')[0]
      if tag == '#': 
        top_level = min(top_level, 1)
        break
      elif tag == '##': top_level = min(top_level, 2)
      elif tag == '###': top_level = min(top_level, 3)
      elif tag == '####': top_level = min(top_level, 4)
      elif tag == '#####': top_level = min(top_level, 5)
  
  offset = header_level - top_level
  if (top_level == 100) or (offset <= 0):
    return mdtxt
  else:
    pad = '#' * offset
    result = []
    for line in mdtxt.splitlines():
      tag = line.split(' ')[0]
      if tag in ('#', '##', '###', '####', '#####'):
        line = pad + line
      result.append(line)
  return '\n'.join(result)




def test_fix_md_title():
  sample1 = '''

txt1
txt2

txt3
'''
  assert sample1 == fix_md_title(sample1, header_level=1)
  assert sample1 == fix_md_title(sample1, header_level=3)

  sample2 = '''
txt1
# txt2

    # code comment
    # code comment


## txt3
#### txt4

###normaltxt

'''
  sample2_result = '''
txt1
### txt2

    # code comment
    # code comment


#### txt3
###### txt4

###normaltxt
'''
  assert sample2_result == fix_md_title(sample2, header_level=3)











def fix_svg_image(mdtxt):
  ''' 删除 svg 图片
![](https://pic1.zhimg.com/v2-de3db9a301472562573c48f2738e78ac_b.jpg)

![](data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1280' height='720'></svg>)

'''
  pat = r'\n\!\[\]\(data:image\/svg\+xml;utf8,<svg.+?<\/svg>\)\n'
  mdtxt = re.sub(pat, '', mdtxt)
  return mdtxt


def test_fix_svg_image():
  mdtxt = ''' 删除 svg 图片
![](https://pic1.zhimg.com/v2-de3db9a301472562573c48f2738e78ac_b.jpg)

![](data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1280' height='720'></svg>)

'''
  result = ''' 删除 svg 图片
![](https://pic1.zhimg.com/v2-de3db9a301472562573c48f2738e78ac_b.jpg)

'''
  assert result == fix_svg_image(mdtxt)













if __name__ == "__main__":
  test_fix_md_title()
  test_fix_svg_image()