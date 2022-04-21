from django.db import models
import uuid
from content.models import Person, Character
from tags.models import GenericTag, ManualTag
from video.models import Video
from django.contrib.postgres.fields import ArrayField
from frames.models import Rect, PictureFrame, Frames, VideoFrame


class FaceGroup(models.Model):
    """FaceGroup mapping detected faces to Persons"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(Person, blank=True, null=True)
    video = models.ForeignKey(Video, blank=True, null=True)
    timeline = ArrayField(models.IntegerField(), default=[])
    character = models.ForeignKey(Character, blank=True, null=True)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    @property
    def face_img(self):
        """get a face image"""
        if Face.objects.filter(face_group__id=self.id):
            one_face = Face.objects.filter(face_group__id=self.id)[0]
            return one_face.face_img_url
        else:
            return None

    def set_time_line(self):
        """get time_line of the face group"""
        faces = self.face_set.all()
        time_line_not_sorted = []
        time_line_filtered = []

        for face in faces:
            video_frame = VideoFrame.objects.get(frame=face.face_rect.frame)
            time_line_not_sorted.append(int(video_frame.time))

        for t in sorted(time_line_not_sorted):
            if not time_line_filtered:
                time_line_filtered.append(t)
                time_line_filtered.append(t + 1)
            elif t-2 <= time_line_filtered[-1] <= t:
                time_line_filtered[-1] = t
            elif time_line_filtered[-1] > t:
                continue
            else:
                time_line_filtered.append(t)
                time_line_filtered.append(t+1)
        self.timeline = time_line_filtered
        self.save()
        return time_line_filtered

    def __str__(self):
        if self.person:
            return self.person.name
        else:
            return str(self.id)

    def profile_img(self):
        if Face.objects.filter(face_group__id=self.id):
            one_face = Face.objects.filter(face_group__id=self.id)[0]
            red_url = '/admin/contextual/facegroup/{}/change/'.format(self.id)
            return u'<a href="%s"><img src="%s" width="150"/></a>' % (red_url, one_face.face_img_url)
        else:
            return "None"

    profile_img.short_description = 'Face'
    profile_img.allow_tags = True


class VideoFaceGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    face_group = models.ForeignKey(FaceGroup)
    video = models.ForeignKey(Video)

    def __str__(self):
        return str(self.id)


class PictureGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    frames = models.ManyToManyField(PictureFrame)
    face_groups= models.ManyToManyField(FaceGroup)

    def __str__(self):
        return self.name


class FrameGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    frames = models.ManyToManyField(Frames)
    face_groups = models.ManyToManyField(FaceGroup)

    def __str__(self):
        return self.name


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    locations = models.ManyToManyField(GenericTag)
    manual_tag = models.ForeignKey(ManualTag)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.id)


class Face(models.Model):
    """Face detected in frames or images"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    azure_face_id = models.CharField(max_length=128, verbose_name='Face Id')
    face_img_url = models.URLField(verbose_name='Image URL')
    face_group = models.ForeignKey(FaceGroup, null=True, blank=True, verbose_name="Face Group")
    face_rect = models.ForeignKey(Rect, verbose_name="Rect", null=True)
    selected = models.BooleanField(default=False, blank=True)
    emotion = models.CharField(max_length=128, null=True, blank=True)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return str(self.id)

    def face_img(self):
        return u'<img src="%s" width="150"/>' % self.face_img_url

    face_img.short_description = 'Face'
    face_img.allow_tags = True

    def person_name(self):
        if self.face_group:
            return self.face_group.person.name
        else:
            return '-'

    person_name.short_description = "Name"


class HardCuts(models.Model):
    """Hardcuts detected in a video"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.OneToOneField(Video)
    cuts = ArrayField(ArrayField(models.FloatField()))
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name_plural = 'Hard cuts'

    def __str__(self):
        return self.video.title
