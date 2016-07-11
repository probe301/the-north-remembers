
from models import Task

Task.loop_watch(sleep_seconds=10, times=4)
