# The North Remembers


以更加简洁清晰的排版阅读知乎.

Web 版本: 提供主题, 用户动态的 rss 订阅功能, 提供页面编辑状态的变更记录

本地版本: 页面批量抓取, 图片抓取, 制作电子书



功能

定制抓取内容, 包括: 抓取指定答主/收藏夹名/问题/话题下的回答, 抓取赞同数量超过N的回答

展示评论, 以会话的形式组织赞同数较高的评论

保存 epub 或者批量 markdown 文档

自定义的 feed







### todo

- [x] 赞同评论的三个空格

- [x] png 图片抓取替换

- [x] 处理 知乎link

- [x] 处理 评论组 top likes

- [ ] 处理更标准的评论会话 - wait 官方评论组的更新

- [ ] 回答日期如果是当天fetch, 会显示为时间而非日期 - 不重要

- [ ] tex应该存链接, 外加抓取图片

- [ ] 存储图片应存本地备份外加zhihu permanent url



      ​

- [ ] howto response using json?

      ​

- [ ] refetch Zhihu.py Package

- [ ] refactor zhihu-fetcher

- [ ] design element




### URL Schema

 design json API

http://zhihumark.com/answers/131

http://zhihumark.com/topics/math




页面设计

单页面网站应用, 基本上类似搜索引擎的风格和排版.

输入框 - 接受输入ID或URL 答主/收藏夹名/问题名/话题名

选项 - 保留最前的n个回答?

选项 - 赞同数至少是?

选项 - 保留评论? 评论对话中至少有多少 likes

屏蔽 - 不感兴趣的话题, 问题, 答主

返回 - markdown文件列表

批量下载按钮