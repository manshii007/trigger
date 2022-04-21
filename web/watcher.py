import os


from django.conf import settings


# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config")
os.environ.setdefault("DJANGO_CONFIGURATION", "Testing")

# configuration setup
import configurations

configurations.setup()

from utils.watchdog_test import Watcher
print("Starting Watcher")
w = Watcher()
w.run()
