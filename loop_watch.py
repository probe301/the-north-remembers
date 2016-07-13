
from models import Task

Task.multiple_watch(sleep_seconds=30, limit=30)
