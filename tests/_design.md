

### 结构

```python
  class Watcher (task runner):
    .watch_once()
    .report()
    .is_watcher()

  class Fetcher (fetch url dispatch):
    .is_lister()
    .is_page()
    .get_metadata()


  class Collector (flask json server):

    # 抓取单个页面
    # GET  http://<host>/api/v1/fetcher/<lister_url or page_url>  
    # 返回 json 抓取结果

    # 列出 server 上已经存在的 watchers
    # GET  http://<host>/api/v1/watchers

    # 列出 watcher 的明细
    # GET  http://<host>/api/v1/watchers/<folder_id>

    # 创建 watcher
    # POST http://<host>/api/v1/watchers/ {folder: "xxx", config}

    # 运行 watcher
    # POST http://<host>/api/v1/watchers/<folder_id>/run


```





Task - 记录上次执行时间, 安排下次任务时间, 优先级
  存到到 tasks.json

    ListerTask 抓取一个 url 列表 - Fetcher.fetch_data(), Task.create()
    PageTask 抓取单一页面内容 - Fetcher.fetch_data(), Page.create(data)



Fetcher - 抓取页面, 
  解析 html / 转换调用 API 的结果 json api data / 获取 xml feed
  处理异常页面, 已删除 / 禁止评论, 等
  返回 json data
    ZhihuAnswerFetcher
    ZhihuColumnFetcher
    WeixinArticleFetcher
    Fetcher.request(url) => json

  处理页面中的附带资源, image, pdf



def test_2_usage_fetcher():
  data_blog = Fetcher.request(url_of_webpage)
  data_zhihu_answer = Fetcher.request(url_of_jsonapi)
  data_rss_feed = Fetcher.request(rss_feed)

  data_blog         | should.eq({'title': 'xxxx', 'pubDate': 'xxxx', 'content': 'xxxx'})
  data_zhihu_answer | should.eq({'title': 'xxxx', 'author': 'xxxx', 'answer': 'xxxx'})
  data_rss_feed[0]  | should.equal({'title': 'xxxx', 'link': 'xxxx', 'content': 'xxxx', })



Page - 表示单一页面在本地的存档
  以 markdown 为默认格式, 也可以 html, pdf 等
  清理文本的规则
  比对既有存档, 处理内容变化, 预览 diff
  转换为 rss, epub, pdf, 
  
  页面基本结构是 元数据 + 文章主体 + 评论

    ZhihuAnswerPage
    ZhihuColumnPage
    WeixinArticlePage

Page.load()  返回一个读盘的页面, 以小标题分段, 尽量恢复到

def test_3_usage_page():
  page = Page.create(json_data)
  Page.save()
  Page.load()


Watcher -> PageTask -> Page (tmpl, fetcherAPI)
                            ZhihuColumnPage
                            ZhihuAnswerPage
                            WeixinArticlePage


Watcher -> ListerTask -> append more tasks
                         ZhihuColumnIndex


Watcher 仅本地反复抓取时使用

Fetcher 按照网站业务分类
有三类任务 request explore 

对于每个网站
request lister url
过滤 lister (按照每个网站自己的条件)
request page url (可能需要附加 url, 如 api stats)
缓存 html
text processing









#### Fetcher

    ZhihuColumnPage
        .load(path)
        .write(path)
        .compare()

    attr
        task = ForeignKeyField(Task, related_name='task')
        watch_date = DateTimeField()
        title = CharField(null=True)
        author = CharField(null=True)
        content = TextField(null=True)
        metadata = TextField(null=True)
        topic = TextField(null=True)
        question = TextField(null=True)
        comment = TextField(null=True)






#### Collector

处理用户发出的命令

可以是 zhihu answer url, 问题页, 收藏夹页, 需要带有过滤条件
用户可能在过滤条件后再做修补删减

需要转为具体的爬虫任务, 并创建文件夹
单页收集到特定的文件夹, 否则收集到一个自动命名的文件夹

在文件夹下生成task

Resources
global_config
task_config (scanlist)


Collector.append(url, options)


后端, 批量  
Fetcher -> json -> render Page with jinjatmpl
解决 lister, 解决过滤, 解决定时重复抓取
解决检测到某些 url 提前终止

前端, 单页  
Fetcher -> json -> render HTML with Vue, annotation
解决网页里高亮, 注记, 另存 html/md











### Note


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


