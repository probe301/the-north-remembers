
from models import Task

Task.multiple_watch(sleep_seconds=3, limit=3)
