from django.db import models
import uuid
from utils.unique_filename import unique_upload
from .validator import validate_img_file_type
from tags.models import Tag
from video.models import Video
from content.models import Person
from versatileimagefield.fields import VersatileImageField, PPOIField
from versatileimagefield.placeholder import OnStoragePlaceholderImage


class Frames(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.URLField()

    class Meta:
        verbose_name_plural = 'Frames'

    def __str__(self):
        return str(self.id)

    def full_img(self):
        return u'<img src="%s" width="250">' % self.file

    full_img.short_description = 'Face'
    full_img.allow_tags = True


class Rect(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    x = models.FloatField()
    y = models.FloatField()
    w = models.FloatField()
    h = models.FloatField()
    frame = models.ForeignKey(Frames, related_name='rects')
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return str(self.id)


class VideoFrame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    frame = models.OneToOneField(Frames, null=True, default=None)
    video = models.ForeignKey(Video)
    time = models.FloatField(default=0, null=True)


class PictureFrame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    frame = models.OneToOneField(Frames, null=True, default=None)

    def __str__(self):
        return str(self.id)

    def full_img(self):
        return u'<img src="%s" width="200"/>' % self.frame.file

    full_img.short_description = 'Face'
    full_img.allow_tags = True


class PersonFrame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    frame = models.OneToOneField(Frames, null=True, default=None, blank=False, related_name="personframes")
    person = models.ForeignKey(Person, blank=False, null=True, default=None, related_name="personframes")

    def __str__(self):
        return str(self.person.name)

    def full_img(self):
        return u'<img src="%s" width="200"/>' % self.frame.file

    full_img.short_description = 'Face'
    full_img.allow_tags = True


class ProxyFrame(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    frame = models.OneToOneField(Frames, blank=True, null=True)
    file = VersatileImageField(
        'Picture',
        upload_to=unique_upload,
        ppoi_field='file_ppoi',
        null=True,
        placeholder_image=OnStoragePlaceholderImage(
            path='No_picture_available.png'
        )
    )

    file_ppoi = PPOIField()

    def __str__(self):
        return str(self.id)

    def full_img(self):
        if self.file:
            return u'<img src="%s" width="200">' % self.file.url
        else:
            return '-'

    full_img.short_description = 'Image'
    full_img.allow_tags = True