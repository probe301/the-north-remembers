
from models import Task
Task.multiple_watch(sleep_seconds=11, limit=900)
Task.report()
