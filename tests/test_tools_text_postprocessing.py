
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





def test_format_convert_md():
  sample = '''
<strong>魂灵篇-壹</strong>

<p style="text-align: left;"> 3.开荒</p>
<p style="text-align: left;"> 魂灵开荒时，最重要的地形应该算是叶族地了，来自屎大棒，这种地形呈现出不健康的惨绿色，并且有特殊的背景，应该很容易认出来。</p>
<figure class="img-box" contenteditable="false"><img data-src="//i0.hdslb.com/bfs/article/d1ac1c8df27d877ff83e41ef10a9d8f7d81067cb.png" width="1920" height="1080" data-size="259737" />
    <figcaption class="caption" contenteditable="">叶族地形</figcaption>
</figure>
<p style="text-align: left;"> 这种地形有特殊的敌人以及尖刺陷阱，因此比较危险，最好小心探索。</p>
<p style="text-align: center;"> 收益：<span class="color-green-02">创造之祭坛</span></p>
<figure class="img-box" contenteditable="false"><img data-src="//i0.hdslb.com/bfs/article/ec93e495aaae10e5e39b7e8f4f71c177b9e184a0.png" width="467" height="338" data-size="44775" />
    <figcaption class="caption" contenteditable="">上图左下角位置</figcaption>
</figure>
<p style="text-align: left;"> 这玩意其实做起来也不算很贵，但是如果找到叶族地挖到的话，可以省下很大一番功夫，也是比较给力的。</p>
<p style="text-align: center;"><span class="color-green-02">叶族地箱子</span></p>
<figure class="img-box" contenteditable="false"><img src="//i0.hdslb.com/bfs/article/5242b6f4ed0061585aab640756a5486170037e38.png" width="96" height="60" data-size="1670" />
    <figcaption class="caption" contenteditable="">这种东西</figcaption>
</figure>
<p style="text-align: left;"> 里面包含有各种前期武器饰品及材料（比如玻璃瓶，银币，远古树皮等），对前期增强实力有着极大的裨益。<span class="font-size-20">特别是其中的猎人回旋镖</span></p>

  '''

  result = tools.html2md(sample)
  # print(result)
  # html2text 不能识别 `<img data-src=xxx />` 需要事先修正为 `<img src=xxx />`
  assert 'i0.hdslb.com' in result, result

