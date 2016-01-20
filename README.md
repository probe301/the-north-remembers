



Zhihumark



后端 Python API 国内 Python3 云或者 Keroku

前端 React 国内静态托管平台

Flask 响应需要包装为 json

UI Bootstrap Bootstap-Flat-UI





- [x] 赞同评论的三个空格


- [ ] png图片抓取替换
- [ ] 处理 知乎link 



``` markdown
 [Central limit theorem](//link.zhihu.com/?target=https%3A//en.wikipedia.org/wiki/Central_limit_theorem) ）可知， ![S_n/\\sqrt{n}](//zhihu.com/equation?tex=S_n%2F%5Csqrt%7Bn%7D) 依分布收敛于一个正态分布。粗略来说 ![S_n](//zhihu.com/equation?tex=S_n) 大概是 ![\\sqrt{n}](//zhihu.com/equation?tex=%5Csqrt%7Bn%7D) 量级。而大偏差理论（ [Large deviations theory](//link.zhihu.com/?target=https%3A//en.wikipedia.org/wiki/Large_deviations_theory) ）研究的是 ![S_n](//zhihu.com/equation?tex=S_n) 处在n量级的概
```







- [ ] design json API
      
- [ ] howto response using json?
      
      ​
      
- [ ] refetch Zhihu.py Package
      
- [ ] refactor zhihu-fetcher
      
- [ ] design UI
      
- [ ] howto use Flat UI
      
- [ ] design react flow

zhihumark 知乎马克



### URL Schema

http://zhihumark.com/answers/131

http://zhihumark.com/topics/math











描述

以更加简洁清晰的排版阅读知乎. 用户指定一个知乎网站上的问题, zhihumark 抓取相应的回答内容, 以 markdown 文档的形式提供给用户阅读和下载.



功能

可以自由定制想抓取的内容, 这包括: 抓取指定答主/收藏夹名/问题/话题下的回答, 抓取赞同数量超过N的回答.

可以设置黑名单, 不抓取特定的问题或者答主.

抓取评论, 以会话的形式组织起来, 让上下文相关的评论出现在一起, 尽量滤除没有价值的评论.

将收集到的一系列文档保存为epub或者pdf, 或者批量下载 markdown 文档, 以便离线阅读.

(待定)制作成 feed 以便放入 rss 阅读器, 获取实时更新.



观念

提倡使用简洁, 优雅的 markdown 格式排版, 阅读, 分享简单的文档.

欣赏认真, 朴实, 严谨的 (即使是略显无趣的) 的回答和讨论, 不欣赏抖机灵的回答.

更关注在较长时间内有价值的, 半衰期较长的话题, 相对不关注一时的新闻热点.

相信评论区是对回答的重要补充, 也有随回答保留的必要, 但需处理评论区良莠不齐, 引用回复混乱的问题.



技术和工具

prototyper(原型) HTML5 Python Flask(网站引擎) SAE(部署)



页面设计

单页面网站应用, 基本上类似搜索引擎的风格和排版.

输入框 - 接受输入ID或URL 答主/收藏夹名/问题名/话题名

选项 - 保留最前的n个回答?

选项 - 赞同数至少是?

选项 - 保留评论? 评论对话中至少有多少 likes

屏蔽 - 不感兴趣的话题, 问题, 答主

返回 - markdown文件列表

批量下载按钮