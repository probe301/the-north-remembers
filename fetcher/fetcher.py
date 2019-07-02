

class Fetcher:
  '''
  抓取任务, 分为发现新Page, 和抓取Page变化两种
  '''
  def __init__(self):
    self.task_type
    self.url
    self.label
    self.last_watch_time
    self.next_watch_time
    self.weight

  def fetch(self):
    pass


  def to_dict(self):
    pass



class ZhihuDetectNewAnswer(Fetcher):
  pass


class ZhihuAnswer(Fetcher):
  pass


class ZhihuColumn(Fetcher):
  pass


