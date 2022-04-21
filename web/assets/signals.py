from django.dispatch import receiver
from django.db.models.signals import post_save
from .tasks import convert
from .models import RO
import logging, errno

KEY = 'e80b3b4c298043f8aa6fca9a6e5f343c'  # Replace with a valid subscription key (keeping the quotes in place).

AZURE_ACCOUNT_NAME = 'triggerbackendnormal'
AZURE_ACCOUNT_KEY = 'tadQP8+aFdnxzHBx37KYLoIV92H+Ju9U7a+k1qtwaQDE0tH23qQ7mUUD1qzvXBGd6cGgo7rW4jeA8H6AzXZdPg=='
AZURE_CONTAINER = 'backend-media'

FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"

MODE = "info"

logger = logging.getLogger('debug')
logger.setLevel(logging.DEBUG)


@receiver(post_save, sender=RO)
def process_ro(sender, instance, **kwargs):

    if kwargs.get('created'):
        convert.delay(instance.id)