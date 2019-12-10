
import os, sys 
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
sys.path.insert(0, parentdir)

import tools
from pyshould import should
import pytest




def test_fix_md_title():
  sample1 = '''

txt1
txt2

txt3
'''
  assert sample1 == tools.fix_md_title(sample1, header_level=1)
  assert sample1 == tools.fix_md_title(sample1, header_level=3)

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
  assert sample2_result == tools.fix_md_title(sample2, header_level=3)




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
  assert result.strip() == tools.fix_svg_image(mdtxt).strip()






def test_fix_video_link():
  # import tools
  # for p in tools.all_files(r'D:\DataStore\test', '*.md'):
  #   t = tools.text_load(p)
  #   for i, line in tools.enumer(t.splitlines()):
  #     if line == '[':  # if 'https://www.zhihu.com/video/' in line:
  #       print(f'found in {p}')
  #       print(''.join(t.splitlines(1)[i-5:i+5]))
  #       print()
  sample = ''' 形如

[

![](https://pic1.zhimg.com/v2-6a815464926a29329b5e0e68f0a2a375.png)

动物有语言吗 | 混乱博物馆https://www.zhihu.com/video/1125529815624884224](https://www.zhihu.com/video/1125529815624884224)


[

![](https://pic1.zhimg.com/v2-923d0e1a87cace4ecef9e7cbb3622418.jpg)

https://www.zhihu.com/video/1084268180037431296](https://www.zhihu.com/video/1084268180037431296)


[

![](https://pic2.zhimg.com/v2-28e3dd4489fd75514aca0bdb23492d61.jpg)

https://www.zhihu.com/video/1111685179147534336](https://www.zhihu.com/video/1111685179147534336)


[

![](http://pic7.qiyipic.com/image/20161028/75/4e/v_111202885_m_601.jpg)

你所有的热爱，全在这里http://www.iqiyi.com/v_19rr96ulbo.html](http://www.iqiyi.com/v_19rr96ulbo.html)


[![]()Get Cheras to IKEA Cheras—在线播放—优酷网，视频高清在线观看http://v.youku.com/v_show/id_XMTM3NjU1MTAzMg==.html](http://v.youku.com/v_show/id_XMTM3NjU1MTAzMg==.html)
'''

  result = ''' 形如

![](https://pic1.zhimg.com/v2-6a815464926a29329b5e0e68f0a2a375.png)  
[视频: 动物有语言吗 | 混乱博物馆](https://www.zhihu.com/video/1125529815624884224)


![](https://pic1.zhimg.com/v2-923d0e1a87cace4ecef9e7cbb3622418.jpg)  
[视频: ](https://www.zhihu.com/video/1084268180037431296)


![](https://pic2.zhimg.com/v2-28e3dd4489fd75514aca0bdb23492d61.jpg)  
[视频: ](https://www.zhihu.com/video/1111685179147534336)


![](http://pic7.qiyipic.com/image/20161028/75/4e/v_111202885_m_601.jpg)  
[视频: 你所有的热爱，全在这里](http://www.iqiyi.com/v_19rr96ulbo.html)


[视频: Get Cheras to IKEA Cheras—在线播放—优酷网，视频高清在线观看](http://v.youku.com/v_show/id_XMTM3NjU1MTAzMg==.html)
'''
  assert result == tools.fix_video_link(sample)


def test_fix_image_alt():
  mdtxt = '''
还是用图片来说明更加清楚
下图说明了Redux和React的状态流分别是怎么样的；

![](https://pic3.zhimg.com/v2-46d1f94bb780f90a11ad97454d0add3a_b.jpg)

下图说明了使用Redux管理状态为什么是可预测的

![](https://pic3.zhimg.com/v2-62027cb65fb533ad42d401bdbbf6155e_b.png)
Redux的数据是如何流动的其实也是理解Redux的好处的关键部分之一，
[A Cartoon intro to redux]([https://code-cartoons.com/a-cartoon-intro-to-redux-3afb775501a6#.alj778pma](https://code-cartoons.com/a-cartoon-intro-to-redux-3afb775501a6#.alj778pma))

'''

  result = '''
还是用图片来说明更加清楚
下图说明了Redux和React的状态流分别是怎么样的；

![image](https://pic3.zhimg.com/v2-46d1f94bb780f90a11ad97454d0add3a_b.jpg)

下图说明了使用Redux管理状态为什么是可预测的

![image](https://pic3.zhimg.com/v2-62027cb65fb533ad42d401bdbbf6155e_b.png)
Redux的数据是如何流动的其实也是理解Redux的好处的关键部分之一，
[A Cartoon intro to redux]([https://code-cartoons.com/a-cartoon-intro-to-redux-3afb775501a6#.alj778pma](https://code-cartoons.com/a-cartoon-intro-to-redux-3afb775501a6#.alj778pma))

'''
  assert tools.fix_image_alt(mdtxt).strip() == result.strip()

