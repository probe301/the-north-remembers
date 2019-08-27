

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

![](data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1280' height='720'></svg>)示意图

'''

  # 这里通常是图片的label, 需要改成浅灰色
  pat = r'\!\[\]\(data:image\/svg\+xml;utf8,<svg.+?<\/svg>\)(.+?)\n'
  mdtxt = re.sub(pat, r'<center style="color:gray;">\1</center>\n', mdtxt)
  pat2 = r'\!\[\]\(data:image\/svg\+xml;utf8,<svg.+?<\/svg>\)\n'  # 没有 label
  mdtxt = re.sub(pat2, r'\n', mdtxt)
  return mdtxt


def test_fix_svg_image():
  mdtxt = ''' 删除 svg 图片
![](https://pic1.zhimg.com/v2-de3db9a301472562573c48f2738e78ac_b.jpg)

![](data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1280' height='720'></svg>)示意图

![](https://pic1.zhimg.com/v2-de3db9a301472562573c48f2738e78ac_b.jpg)

![](data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1280' height='720'></svg>)示意图2

'''
  result = ''' 删除 svg 图片
![](https://pic1.zhimg.com/v2-de3db9a301472562573c48f2738e78ac_b.jpg)

<center style="color:gray;">示意图</center>

![](https://pic1.zhimg.com/v2-de3db9a301472562573c48f2738e78ac_b.jpg)

<center style="color:gray;">示意图2</center>

'''
  assert result == fix_svg_image(mdtxt)





def fix_video_link(mdtxt):
  ''' 视频链接形如

[

![](https://pic1.zhimg.com/v2-6a815464926a29329b5e0e68f0a2a375.png)

动物有语言吗 | 混乱博物馆https://www.zhihu.com/video/1125529815624884224](https://www.zhihu.com/video/1125529815624884224)

暂时更新为

![](https://pic1.zhimg.com/v2-6a815464926a29329b5e0e68f0a2a375.png)
[视频: 动物有语言吗 | 混乱博物馆](https://www.zhihu.com/video/1125529815624884224)

'''

  pat = r'\[\n\n(\!\[\]\(https://pic.+?\))\n\n(.*?)(https://www.zhihu.com/video/\d+)\]\(\3\)'
  mdtxt = re.sub(pat, r'\1\n[视频: \2](\3)', mdtxt)
  return mdtxt


def test_fix_video_link():
  sample = ''' 形如

[

![](https://pic1.zhimg.com/v2-6a815464926a29329b5e0e68f0a2a375.png)

动物有语言吗 | 混乱博物馆https://www.zhihu.com/video/1125529815624884224](https://www.zhihu.com/video/1125529815624884224)

'''

  result = ''' 形如

![](https://pic1.zhimg.com/v2-6a815464926a29329b5e0e68f0a2a375.png)
[视频: 动物有语言吗 | 混乱博物馆](https://www.zhihu.com/video/1125529815624884224)

'''
  assert result == fix_video_link(sample)










if __name__ == "__main__":
  test_fix_md_title()
  test_fix_svg_image()
  test_fix_video_link()