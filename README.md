



## The North Remembers

### 介绍

The North Remembers (以下简称 TNR) 是一个把在线页面同步到本地的项目, 你可以用它监视一个微信公众号, 一个知乎专栏, 当其中有新增或修改文章时 TNR 会将数据收集到本地目录, 用于个人学习笔记或存档备份

TNR 的初衷是保存我关心的互联网数据, 在互联网上, 每天总是有些东西忽然就看不见了 (且未来也看不到好转的希望), TNR 是能够方便留存这些数据的办法

- RSSHub
- archive.org 受 Robot.txt 限制, 受登录账号限制

TNR 的第二个用途是把在线页面转为个人笔记, 经过长期实践, 我觉得以 markdown 格式保存网页摘抄是个好办法, 围绕 markdown 生态的工具数量多, 搭配灵活

推荐 

1. Typora + 同步网盘
2. VSCode + git

对于这个需求, 我参考了这些工具

- 简悦
- Evernote, 有道云笔记 ...


Q: 与 RSSHub 的区别?

1. 本项目主要为把页面存为本地文件, 其次输出 RSS Feed
2. 对正文的排版做了更多修正, 如代码块的语法检测, 视频链接标题, LaTeX
3. 可以存储附件, 主要是指图片和视频, 以防页面丢失
4. 可以抓取页面评论
5. 对少数网站记录了更详尽的统计数据, 比如知乎问答的赞同/感谢数


### 使用方法

创建一个空的目录, 比如 `D:/test-project`, 在目录下创建文档 `.config.yaml`, 内容为

```yaml
listers:
  - url: https://zhuanlan.zhihu.com/frontEndInDepth       
    tip: "专栏 TryFEInDepth"
    option: {limit: 4}
  - url: https://zhuanlan.zhihu.com/learn-vue-source-code
    tip: "专栏 Vue源码研究会"
    option:  # 专属这个 lister url 的 option, 覆盖全局设置
      min_voteup_count: 100
      limit: 3
      banned_text: '有哪些,如何看待'  # 标题/话题中有这些关键词, 就不抓取limit: 10
version_control_option:
  git_commit_path: none
  git_commit_batch: 

task_option:
  save_attachments: false
  lister_max_cycle: 30days 
  lister_min_cycle: 12hours
  weight: 0.5
  limit: 200
  page_max_cycle: 180days
  page_min_cycle: 45days

rss_option:
  title: "zhuanlan-frontend"
  link: https://xxxx

epub_option: none

```

之后执行

```python
path = r'D:/remember-project'      # 修改为你的工作路径
watcher = Watcher.open(path)

watcher.report()                  # 列出当前状态
watcher.watch_once()              # 抓取这个目录下的页面
watcher.to_rss_feed()             # 转换为 RSS
watcher.to_epub()                 # 转换为 epub

```



### 文档

.config.yaml 配置说明如下

```yaml
listers:
  - url: https://zhuanlan.zhihu.com/frontEndInDepth       
    tip: "专栏 TryFEInDepth"
    option: {limit: 4}
  - url: https://zhuanlan.zhihu.com/learn-vue-source-code
    tip: "专栏 Vue源码研究会"
    option:  # 专属这个 lister url 的 option, 覆盖全局设置
      min_voteup_count: 100
      limit: 3
      banned_text: '有哪些,如何看待'  # 标题/话题中有这些关键词, 就不抓取limit: 10

version_control_option:
  git_commit_path: '.'     # 使用 git 提交记录, 可选上一层目录 '..', 当前目录 '.', 或默认 none
  git_commit_batch: 3  # 每 10 个页面执行一个提交

task_option:
  save_attachments: false
  lister_max_cycle: 30days  # 对 Watcher 目录里的所有 lister 起效, 会被具体设置覆盖
  lister_min_cycle: 12hours
  weight: 0.5
  limit: 200
  page_max_cycle: 180days  # 对 Watcher 目录里的所有 page 起效
  page_min_cycle: 45days

rss_option:
  title: "zhuanlan-frontend"
  link: https://xxxx

epub_option: none

```



### 结构

```
  class Watcher (task runner)
    .watch_once()
    .report()
    .is_watcher()

  class Fetcher (fetch url dispatch)
    .is_lister()
    .is_page()
    .get_metadata()


  class Collector (flask json server)

    抓取单个页面
    GET  http://<host>/api/v1/fetcher/<lister_url or page_url>  
    返回 json 抓取结果

    列出 server 上已经存在的 watchers
    GET  http://<host>/api/v1/watchers

    列出 watcher 的明细
    GET  http://<host>/api/v1/watchers/<folder_id>

    创建 watcher
    POST http://<host>/api/v1/watchers/ {folder: "xxx", config}

    运行 watcher
    POST http://<host>/api/v1/watchers/<folder_id>/run


```