from django.dispatch import receiver
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from .models import ProxyFrame, Frames, PictureFrame
from contextual.models import PictureGroup
from .tasks import backgroud_face_detection


@receiver(post_save, sender=ProxyFrame)
def add_frame(sender, instance, **kwargs):
    """create frame instance and add into the proxy frame"""
    if kwargs.get('created'):
        frame = Frames.objects.create(file=instance.file.url)
        frame.save()
        instance.frame = frame
        instance.save()
        picture_frame = PictureFrame.objects.create(frame=frame)
        picture_frame.save()
        obj, created = PictureGroup.objects.get_or_create(name="Family")
        obj.frames.add(picture_frame)
        obj.save()
    else:
        if not instance.frame:
            frame = Frames.objects.create(file=instance.file.url)
            frame.save()
            instance.frame = frame
            instance.save()
            picture_frame = PictureFrame.objects.create(frame=frame)
            picture_frame.save()
            obj, created = PictureGroup.objects.get_or_create(name="Family")
            obj.frames.add(picture_frame)
            obj.save()


# @receiver(post_save, sender=Frames)
# def start_face_detection(sender, instance, **kwargs):
#     """perform face detection"""
    # backgroud_face_detection.delay(instance.id)
