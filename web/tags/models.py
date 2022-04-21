#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
import uuid, random
import datetime
from math import floor
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from content.models import Character, Episode, ChannelClip, Collection
from video.models import Video

from versatileimagefield.fields import VersatileImageField, PPOIField
from versatileimagefield.placeholder import OnStoragePlaceholderImage

from utils.unique_filename import unique_upload
from django.contrib.contenttypes.fields import GenericRelation
from comments.models import Comment
from users.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from mptt.models import MPTTModel, TreeForeignKey

def random_code():
    return random.getrandbits(29)


def default_large_code(model_class):
    def default_code():
        max_code_obj = model_class.objects.filter(code__isnull=False).order_by('-code').first()
        max_code = 1
        if max_code_obj:
            max_code = max_code_obj.code + 1
        return int("1901{0:05d}".format(max_code))
    return default_code


def default_small_code(model_class):
    def default_code():
        max_code_obj = model_class.objects.filter(code__isnull=False).order_by('-code').first()
        max_code = 1
        if max_code_obj:
            max_code = max_code_obj.code + 1
    return default_code


class TagCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    class Meta:
        permissions = (("view_tagcategory", "Can view tag category"),)


class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128)
    is_removed = models.BooleanField(default=False)
    category = models.ForeignKey(TagCategory, null=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name

    class Meta:
        permissions = (("view_tag", "Can view tag"),)


class TaggedItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag_name = models.ForeignKey(Tag)
    # TODO fix delete event
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    tagged_object = GenericForeignKey('content_type', 'object_id')
    is_removed = models.BooleanField(default=False)

    # basic modification tracker
    # TODO implement all event tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.tag_name

    def __unicode__(self):
        return self.tag_name

    class Meta:
        permissions = (("view_taggeditem", "Can view tagged item"),)

class GenericTag(MPTTModel):
    """
    Generic Tags to hold tag hierarchy
    """
    # We can have a mptt generic tree where we can attach any thing to it
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=128)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.title)

# Frame level tags as objects
class FrameTag(models.Model):
    edit_choices = (
        ('RIV', 'Review'),
        ('CLN', 'Clean'),
        ('ACP', 'Accepted'),
        ('NCP', 'Not Accepted'),
        ('CHK', 'Check')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.ForeignKey(GenericTag, related_name='frametag', null=True, blank=True)
    video = models.ForeignKey(Video, related_name='frametag')
    frame_in = models.PositiveIntegerField()
    frame_out = models.PositiveIntegerField()
    confidence = models.FloatField(null=True, blank=True, default=0.0)
    comment = models.TextField(null=True)
    words = models.TextField(null=True)
    is_approved = models.BooleanField(default=True, blank=True)
    user_comments = GenericRelation(Comment)
    is_cbfc = models.BooleanField(default=False, blank=True)
    height = models.FloatField(default=0, blank=True)
    width = models.FloatField(default=0, blank=True)
    up_left_x = models.FloatField(default=0, blank=True)
    up_left_y = models.FloatField(default=0, blank=True)
    img_width = models.FloatField(default=0, blank=True)
    img_height = models.FloatField(default=0, blank=True)
    is_india = models.BooleanField(default=True, blank=True)
    is_international = models.BooleanField(default=True, blank=True)
    is_edl = models.BooleanField(default=True, blank=True)

    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True)
    index = models.IntegerField(null=True, blank=True)

    created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)


    def __str__(self):
        if self.words:
            return self.words
        else:
            return "None"

    def __unicode__(self):
        if self.words:
            return self.words
        else:
            return "None"

    class Meta:
        permissions = (('view_frametag', 'Can view frame tags'),)

    def _time_in(self):
        """Returns time in"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_in/self.video.frame_rate)))
        return base_time+":"+str(floor(self.frame_in-floor(self.frame_in/self.video.frame_rate)*self.video.frame_rate))

    def _time_out(self):
        """Returns time out"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_out / self.video.frame_rate)))
        return base_time+":"+str(floor(self.frame_out-floor(self.frame_out/self.video.frame_rate)*self.video.frame_rate))

class Marker(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    frame_tag = models.ForeignKey(FrameTag, null=True, blank=True)
    type = models.TextField(null=True)
    color = models.TextField(null=True)
    radius = models.FloatField(default=0, blank=True)
    startx = models.FloatField(default=0, blank=True)
    starty = models.FloatField(default=0, blank=True)
    last_mousex = models.FloatField(default=0, blank=True)
    last_mousey = models.FloatField(default=0, blank=True)
    width = models.FloatField(default=0, blank=True)
    height = models.FloatField(default=0, blank=True)
    mousex = models.FloatField(default=0, blank=True)
    mousey = models.FloatField(default=0, blank=True)


class CheckTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video, related_name='checktag')
    height = models.FloatField(default=0, blank=True)
    width = models.FloatField(default=0, blank=True)
    up_left_x = models.FloatField(default=0, blank=True)
    up_left_y = models.FloatField(default=0, blank=True)
    img_width = models.FloatField(default=0, blank=True)
    img_height = models.FloatField(default=0, blank=True)
    autotag = models.ForeignKey(GenericTag, related_name='autotag', null=True, blank=True)
    usertag = models.ForeignKey(GenericTag, related_name='usertag', null=True, blank=True)

    created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        if self.autotag:
            return self.autotag.title
        else:
            return "None"

    def __unicode__(self):
        if self.autotag:
            return self.autotag.title
        else:
            return "None"

    class Meta:
        permissions = (('view_checktag', 'Can view check tags'),)


class CorrectionTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video, related_name='correctiontag')
    frame_in = models.PositiveIntegerField()
    frame_out = models.PositiveIntegerField()
    image_url = models.URLField(verbose_name='Image URL')
    checktag = models.ManyToManyField(CheckTag, related_name='tags', null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def _time_in(self):
        """Returns time in"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_in/self.video.frame_rate)))
        return base_time+":"+str(floor(self.frame_in-floor(self.frame_in/self.video.frame_rate)*self.video.frame_rate))

    def _time_out(self):
        """Returns time out"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_out / self.video.frame_rate)))
        return base_time+":"+str(floor(self.frame_out-floor(self.frame_out/self.video.frame_rate)*self.video.frame_rate))

# Frame level tags as objects
class ManualTag(models.Model):
    edit_choices = (
        ('RIV', 'Review'),
        ('CLN', 'Clean'),
        ('ACP', 'Accepted'),
        ('NCP', 'Not Accepted'),
        ('CHK', 'Check')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tags = models.ManyToManyField(GenericTag, related_name='manualtag', null=True, blank=True)
    video = models.ForeignKey(Video, related_name='manualtag')
    frame_in = models.PositiveIntegerField()
    frame_out = models.PositiveIntegerField()
    comment = models.TextField(null=True)
    words = models.TextField(null=True)
    is_approved = models.CharField(max_length=3, choices=edit_choices, null=True, blank=True)
    user_comments = GenericRelation(Comment)
    is_cbfc = models.BooleanField(default=False, blank=True)

    created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        if self.words:
            return self.words
        else:
            return "None"

    def __unicode__(self):
        if self.words:
            return self.words
        else:
            return "None"

    class Meta:
        permissions = (('view_frametag', 'Can view frame tags'),)

    def _time_in(self):
        """Returns time in"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_in/self.video.frame_rate)))
        return base_time+":"+str(floor(self.frame_in-floor(self.frame_in/self.video.frame_rate)*self.video.frame_rate))

    def _time_out(self):
        """Returns time out"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_out / self.video.frame_rate)))
        return base_time+":"+str(floor(self.frame_out-floor(self.frame_out/self.video.frame_rate)*self.video.frame_rate))

    def _seconds_in(self):
        """Returns seconds time in"""
        return self.frame_in/self.video.frame_rate

    def _seconds_out(self):
        """Returns seconds time out"""
        return self.frame_out/self.video.frame_rate

class SceneTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    episode = models.ForeignKey(Episode, related_name='scenes')
    tags = models.ManyToManyField(Tag, related_name='scenes')
    characters = models.ManyToManyField(Character, related_name='scenes')
    frame_in = models.PositiveIntegerField()
    frame_out = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)


# Frame level tags as objects
class KeywordTag(models.Model):
    edit_choices = (
        ('RIV', 'Review'),
        ('CLN', 'Clean'),
        ('ACP', 'Accepted'),
        ('NCP', 'Not Accepted'),
        ('CHK', 'Check')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tags = models.ManyToManyField(Tag, related_name='keywords')
    video = models.ForeignKey(Video, related_name='keywords')
    frame_in = models.PositiveIntegerField()
    frame_out = models.PositiveIntegerField()
    words = models.TextField(blank=False, default="Nothing")
    comment = models.TextField(null=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    sentiment_magnitude = models.FloatField(null=True, blank=True)
    is_approved = models.BooleanField(default=True, blank=True)
    user_comments = GenericRelation(Comment)
    word_level = models.TextField(null=True, blank=True)
    is_cbfc = models.BooleanField(default=False, blank=True)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)


    def __str__(self):
        return self.words

    def __unicode__(self):
        return self.words

    class Meta:
        permissions = (('view_keywordtag', 'Can view keyword tags'),)

    def _time_in(self):
        """Returns time in"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_in/self.video.frame_rate)))
        return base_time+":"+str(self.frame_in)

    def _time_out(self):
        """Returns time out"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_out / self.video.frame_rate)))
        return base_time+":"+str(self.frame_out)


class OCRTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tags = models.ManyToManyField(Tag, related_name='ocrtags')
    video = models.ForeignKey(Video, related_name='ocrtags')
    frame_in = models.PositiveIntegerField()
    frame_out = models.PositiveIntegerField()
    words = models.TextField(blank=False, default="Nothing")
    comment = models.TextField(null=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    sentiment_magnitude = models.FloatField(null=True, blank=True)
    language = models.CharField(null=True, blank=True, choices=settings.LANGUAGES, default='en', max_length=2)

    def __str__(self):
        return self.words

    def __unicode__(self):
        return self.words

    class Meta:
        permissions = (('view_ocrtag', 'Can view ocr tags'),)

    def _time_in(self):
        """Returns time in"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_in/self.video.frame_rate)))
        return base_time+":"+str(self.frame_in)

    def _time_out(self):
        """Returns time out"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_out / self.video.frame_rate)))
        return base_time+":"+str(self.frame_out)


class Logo(Tag):
    poster = VersatileImageField(
        'Poster',
        upload_to=unique_upload,
        ppoi_field='poster_ppoi',
        blank=True,
        null=True,
        placeholder_image=OnStoragePlaceholderImage(
            path='No_picture_available.png'
        )
    )

    poster_ppoi = PPOIField()

    class Meta:
        permissions = (("view_logo", "Can view logo"),)


# Frame level tags as objects
class LogoTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.ForeignKey(Logo, related_name='logotag')
    video = models.ForeignKey(Video, related_name='logotag')
    frame_in = models.PositiveIntegerField()
    frame_out = models.PositiveIntegerField()
    comment = models.TextField(null=True)

    def __str__(self):
        return self.tag.name

    def __unicode__(self):
        return self.tag.name

    class Meta:
        permissions = (('view_logotag', 'Can view logo tags'),)

    def _time_in(self):
        """Returns time in"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_in/self.video.frame_rate)))
        return base_time+":"+str(self.frame_in)

    def _time_out(self):
        """Returns time out"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_out / self.video.frame_rate)))
        return base_time+":"+str(self.frame_out)

    def _duration(self):
        """Returns total duration of the tag"""
        if self.frame_in and self.frame_out:
            dur_seconds = (self.frame_out - self.frame_in)/ self.video.frame_rate
            return dur_seconds
        else:
            return None


class EmotionTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video)
    frame_in = models.PositiveIntegerField()
    frame_out = models.PositiveIntegerField()
    emotion_quo = models.CharField(max_length=64, null=True, blank=True)
    comment = models.TextField(null=True)
    confidence = models.FloatField(null=True, blank=True, default=0.0)


    def __str__(self):
        return str(self.emotion_quo)

    def __unicode__(self):
        return str(self.emotion_quo)

    class Meta:
        permissions = (('view_emotiontag', 'Can view emotion tags'),)

    def _time_in(self):
        """Returns time in"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_in/self.video.frame_rate)))
        return base_time+":"+str(self.frame_in)

    def _time_out(self):
        """Returns time out"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_out / self.video.frame_rate)))
        return base_time+":"+str(self.frame_out)

    def _duration(self):
        """Returns total duration of the tag"""
        if self.frame_in and self.frame_out:
            dur_seconds = (self.frame_out - self.frame_in)/ self.video.frame_rate
            return dur_seconds
        else:
            return None


class ComplianceStatusTag(models.Model):
    edit_choices = (
        ('RIV', 'Review'),
        ('CLN', 'Clean'),
        ('ACP', 'Accepted'),
        ('NCP', 'Not Accepted'),
        ('CHK', 'Check'),
        ('CMP', 'Completed'),
        ('RPT', 'Report Sent'),
        ('WIP', 'In Progress')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.OneToOneField(Video)
    is_approved = models.CharField(max_length=3, choices=edit_choices, null=True, blank=True)
    user_comments = GenericRelation(Comment)

    def __str__(self):
        return str(self.id)

    class Meta:
        permissions = (("view_compliancestatustag", "Can view compliance status tag"),)


def auto_programtheme_code():
    max_code = ProgramTheme.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class ProgramTheme(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128,  db_index=True)
    code = models.IntegerField(blank=True, default=auto_programtheme_code)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


def auto_programgenre_code():
    max_code = ProgramGenre.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class ProgramGenre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, db_index=True)
    code = models.IntegerField(default=auto_programgenre_code, blank=True)
    program_theme = models.ForeignKey(ProgramTheme, null=True, on_delete=models.SET_NULL)

    deleted = models.BooleanField(default=False)
    marked = models.BooleanField(default=False)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


def auto_lang_code():
    max_code = ContentLanguage.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class ContentLanguage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128,  db_index=True)
    code = models.IntegerField(default=auto_lang_code, blank=True, db_index=True)

    deleted = models.BooleanField(default=False)
    marked = models.BooleanField(default=False)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


def auto_prod_code():
    max_code = ProductionHouse.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class ProductionHouse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=256,  db_index=True, null=True, blank=True)
    code = models.IntegerField(default=auto_prod_code, blank=True)
    description = models.TextField(null=True, blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.title


def auto_network_code():
    max_code = ChannelNetwork.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class ChannelNetwork(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128,  db_index=True)
    code = models.IntegerField(blank=True, default=auto_network_code)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


def auto_channelgenre_code():
    max_code = ChannelGenre.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class ChannelGenre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128,  db_index=True)
    code = models.IntegerField(blank=True, default=auto_channelgenre_code)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


def auto_region_code():
    max_code = Region.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class Region(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128,  db_index=True)
    code = models.IntegerField(blank=True, default=auto_region_code)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class Channel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    code = models.IntegerField(blank=True, null=True, db_index=True)
    language = models.ForeignKey(ContentLanguage, null=True, blank=True, on_delete=models.SET_NULL)
    abbr = models.CharField(max_length=5, null=True, blank=False)
    network = models.ForeignKey(ChannelNetwork, null=True, on_delete=models.SET_NULL)
    genre = models.ForeignKey(ChannelGenre, null=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, null=True, on_delete=models.SET_NULL)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    deleted = models.BooleanField(default=False)
    marked = models.BooleanField(default=False)

    def __str__(self):
        return self.name


def auto_adgroup_code():
    max_code = AdvertiserGroup.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class AdvertiserGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128,  db_index=True)
    code = models.IntegerField(default=auto_adgroup_code, blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


def auto_ad_code():
    max_code = Advertiser.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class Advertiser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, db_index=True)
    code = models.IntegerField(default=auto_ad_code, blank=True)
    advertiser_group = models.ForeignKey(AdvertiserGroup, null=True, on_delete=models.SET_NULL)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.name


def auto_sector_code():
    max_code = BrandSector.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class BrandSector(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128,  db_index=True)
    code = models.IntegerField(default=auto_sector_code, blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.name


def auto_cat_code():
    max_code = BrandCategory.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class BrandCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, db_index=True)
    code = models.IntegerField(default=auto_cat_code, blank=True)
    brand_sector = models.ForeignKey(BrandSector, null=True, on_delete=models.SET_NULL)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.name


def auto_brandname_code():
    start_txt = datetime.date.today().strftime("%y%m")
    max_code_obj = BrandName.objects.filter(code__isnull=False, code__istartswith=start_txt).order_by('-code').first()
    max_code = 1
    if max_code_obj:
        max_code = int(str(max_code_obj.code)[4:9]) + 1
    return int("{0:s}{1:05d}".format(start_txt, max_code))


class BrandName(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, db_index=True)
    code = models.IntegerField(default=auto_brandname_code, blank=True)
    brand_category = models.ForeignKey(BrandCategory, null=True, on_delete=models.SET_NULL)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.name


def auto_title_code():
    start_txt = datetime.date.today().strftime("%y%m")
    max_code_obj = Title.objects.filter(code__isnull=False, code__istartswith=start_txt).order_by('-code').first()
    max_code = 1
    if max_code_obj:
        max_code = int(str(max_code_obj.code)[4:9]) + 1
    return int("{0:s}{1:05d}".format(start_txt, max_code))


class Title(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, db_index=True)
    code = models.IntegerField(default=auto_title_code, blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.name


def auto_descriptor_code():
    start_txt = datetime.date.today().strftime("%y%m")
    max_code_obj = Descriptor.objects.filter(code__isnull=False, code__istartswith=start_txt).order_by('-code').first()
    max_code = 1
    if max_code_obj:
        max_code = int(str(max_code_obj.code)[4:9]) + 1
    return int("{0:s}{1:05d}".format(start_txt, max_code))


class Descriptor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=128, db_index=True)
    code = models.IntegerField(default=auto_descriptor_code, blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.text


def auto_promotype_code():
    max_code = PromoType.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class PromoType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128,  db_index=True)
    code = models.IntegerField(default=auto_promotype_code, blank=True)
    abbr = models.CharField(max_length=5, null=False, blank=False)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


def auto_promocat_code():
    max_code = PromoCategory.objects.filter(code__isnull=False).order_by('-code').first()
    if max_code:
        return max_code.code + 1
    else:
        return 1


class PromoCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128,  db_index=True)
    code = models.IntegerField(default=auto_promocat_code, blank=True)

    deleted = models.BooleanField(default=False)
    marked = models.BooleanField(default=False)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class Promo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.ForeignKey(Title, null=True, on_delete=models.SET_NULL)
    channel = models.ForeignKey(Channel, related_name="broadcasted_promo", null=True, on_delete=models.SET_NULL)
    promo_channel = models.ForeignKey(Channel, related_name="self_promo", null=True, on_delete=models.SET_NULL)
    brand_name = models.ForeignKey(BrandName, null=True, on_delete=models.SET_NULL)
    advertiser = models.ForeignKey(Advertiser, null=True, on_delete=models.SET_NULL)
    descriptor = models.ForeignKey(Descriptor, null=True, on_delete=models.SET_NULL)

    deleted = models.BooleanField(default=False)
    marked = models.BooleanField(default=False)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.brand_name.name


class Program(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.ForeignKey(Title, null=True, on_delete=models.SET_NULL)
    language = models.ForeignKey(ContentLanguage, null=True, on_delete=models.SET_NULL)
    prod_house = models.ForeignKey(ProductionHouse, null=True, on_delete=models.SET_NULL)
    program_genre = models.ForeignKey(ProgramGenre, null=True, on_delete=models.SET_NULL)
    channel = models.ForeignKey(Channel, null=True, on_delete=models.SET_NULL)

    deleted = models.BooleanField(default=False)
    marked = models.BooleanField(default=False)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.title.name


class Commercial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.ForeignKey(Title, null=True, on_delete=models.SET_NULL)
    brand_name = models.ForeignKey(BrandName, null=True, on_delete=models.SET_NULL)
    descriptor = models.ForeignKey(Descriptor, null=True, on_delete=models.SET_NULL)
    advertiser = models.ForeignKey(Advertiser, null=True, on_delete=models.SET_NULL)

    deleted = models.BooleanField(default=False)
    marked = models.BooleanField(default=False)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    video = models.FileField(null=True, blank=True)

    def __str__(self):
        return self.brand_name.name


class PlayoutTag(models.Model):
    edit_choices = (
        ('RIV', 'Review'),
        ('CLN', 'Clean'),
        ('ACP', 'Accepted'),
        ('NCP', 'Not Accepted'),
        ('CHK', 'Check')
    )
    content_type_choices = (
        ('promo', 'Promo'),
        ('commercial', 'Commercial'),
        ('program', 'Program'),
        ("song", 'Song')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.ForeignKey(Tag, related_name='playouttag', null=True, blank=True)
    video = models.ForeignKey(Video, related_name='playouttag')
    frame_in = models.PositiveIntegerField()
    frame_out = models.PositiveIntegerField()
    is_checked = models.BooleanField(default=False, blank=True)
    comment = models.TextField(null=True, blank=True)
    is_approved = models.CharField(max_length=3, choices=edit_choices, null=True, default='CLN', blank=True)
    user_comments = GenericRelation(Comment)
    poster = VersatileImageField(
        'Poster',
        upload_to=unique_upload,
        ppoi_field='poster_ppoi',
        blank=True,
        null=True,
        placeholder_image=OnStoragePlaceholderImage(
            path='No_picture_available.png'
        )
    )
    poster_ppoi = PPOIField()

    content_type = models.CharField(choices=content_type_choices, max_length=128, null=True, blank=True)

    object_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    tagged_object = GenericForeignKey('object_content_type', 'object_id')

    is_original = models.BooleanField(default=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return "{}_{}_{}".format(self.video.title, self._time_in(), self._time_out())

    class Meta:
        permissions = (("view_playouttag", "Can view playout tag"),)

    def _time_in(self):
        """Returns time in"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_in/self.video.frame_rate)))
        remaining_frames = self.frame_in - int(self.video.frame_rate*floor(self.frame_in/self.video.frame_rate))
        return base_time+":"+str(remaining_frames)

    def _time_out(self):
        """Returns time out"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_out / self.video.frame_rate)))
        remaining_frames = self.frame_out - int(self.video.frame_rate * floor(self.frame_out / self.video.frame_rate))
        return base_time+":"+str(remaining_frames)

    def start_time(self):
        v_start = ChannelClip.objects.filter(video=self.video).first()
        base_time = str(datetime.timedelta(hours=v_start.start_time.hour, seconds=floor(self.frame_in / self.video.frame_rate)))
        return base_time

    def end_time(self):
        v_start = ChannelClip.objects.filter(video=self.video).first()
        base_time = str(datetime.timedelta(hours=v_start.start_time.hour, seconds=floor(self.frame_out / self.video.frame_rate)))
        return base_time

    def _time_in_sec(self):
        return self.frame_in/25

    def _time_out_sec(self):
        return self.frame_out/25


class BarcTag(models.Model):
    edit_choices = (
        ('RIV', 'Review'),
        ('CLN', 'Clean'),
        ('ACP', 'Accepted'),
        ('NCP', 'Not Accepted'),
        ('CHK', 'Check')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.ForeignKey(Tag, related_name='barctag', null=True, blank=True)
    video = models.ForeignKey(Video, related_name='barctag')
    frame_in = models.PositiveIntegerField()
    frame_out = models.PositiveIntegerField()
    comment = models.TextField(null=True, blank=True)
    is_approved = models.CharField(max_length=3, choices=edit_choices, null=True, default='CLN', blank=True)
    user_comments = GenericRelation(Comment)
    poster = VersatileImageField(
        'Poster',
        upload_to=unique_upload,
        ppoi_field='poster_ppoi',
        blank=True,
        null=True,
        placeholder_image=OnStoragePlaceholderImage(
            path='No_picture_available.png'
        )
    )
    poster_ppoi = PPOIField()

    content_type = models.CharField(max_length=128, null=True, blank=True)
    title = models.CharField(max_length=256, null=True, blank=True)
    content_language_code = models.IntegerField(default=0, null=True, blank=True)
    telecast_start_time = models.TimeField()
    telecast_end_time = models.TimeField()
    telecast_duration = models.IntegerField(default=0, null=True, blank=True)
    promo_sponsor_name = models.CharField(max_length=512, null=True, blank=True)
    is_original = models.BooleanField(default=True)
    program_genre = models.CharField(max_length=128, null=True, blank=True)
    program_theme = models.CharField(max_length=128, null=True, blank=True)
    advertiser_group = models.CharField(max_length=128, null=True, blank=True)
    advertiser = models.CharField(max_length=128, null=True, blank=True)
    brand_title = models.CharField(max_length=128, null=True, blank=True)
    brand_category = models.CharField(max_length=128, null=True, blank=True)
    brand_sector = models.CharField(max_length=128, null=True, blank=True)
    descriptor = models.CharField(max_length=512, null=True, blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return "{}_{}_{}".format(self.video.title, self.telecast_start_time, self.telecast_end_time)

    class Meta:
        permissions = (("view_barctag", "Can view barc tag"),)

    def _time_in(self):
        """Returns time in"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_in/self.video.frame_rate)))
        remaining_frames = self.frame_in - int(self.video.frame_rate*floor(self.frame_in/self.video.frame_rate))
        return base_time+":"+str(remaining_frames)

    def _time_out(self):
        """Returns time out"""
        base_time = str(datetime.timedelta(seconds=floor(self.frame_out / self.video.frame_rate)))
        remaining_frames = self.frame_out - int(self.video.frame_rate * floor(self.frame_out / self.video.frame_rate))
        return base_time+":"+str(remaining_frames)

    def _time_in_sec(self):
        return self.frame_in/self.video.frame_rate

    def _time_out_sec(self):
        return self.frame_out/self.video.frame_rate


class SpriteTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    time = models.IntegerField(default=0, null=False, blank=True)
    url = models.URLField(null=True, blank=True)
    video = models.ForeignKey(Video)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return "{}_{}".format(self.video, self.time)


class CommercialTag(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.URLField(null=True, blank=True)
    content_language = models.CharField(max_length=64, null=True, blank=True)
    telecast_duration = models.IntegerField(default=0, null=True, blank=True)
    advertiser_group = models.CharField(max_length=128, null=True, blank=True)
    advertiser = models.CharField(max_length=128, null=True, blank=True)
    brand_title = models.CharField(max_length=128, null=True, blank=True)
    brand_category = models.CharField(max_length=128, null=True, blank=True)
    brand_sector = models.CharField(max_length=128, null=True, blank=True)
    descriptor = models.CharField(max_length=512, null=True, blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return "{}___{}".format(self.brand_title, self.descriptor)

    def video_player(self):
        if self.video:
            return u'<video width="320" height="240" controls autoplay><source src="%s" type="video/mp4"> Your browser does not support the video tag.</video>' % self.video

    video_player.short_description = 'Video'
    video_player.allow_tags = True

    class Meta:
        permissions = (("view_commercialtag", "Can view commercial tag"),)


class Fingerprint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video = models.ForeignKey(Video, null=True, blank=True)
    fprint = JSONField(null=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        permissions = (("view_fingerprint", "Can view fingerprint"),)

class ManualTagQCStatus(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tag = models.ForeignKey(GenericTag, on_delete=models.CASCADE, null=True, blank=True)
    manual_tag = models.ForeignKey(ManualTag, on_delete=models.CASCADE, null=True, blank=True)
    qc_approved = models.BooleanField(default=True)

    class Meta:
        permissions = (("view_manualtagqcstatus", "Can view manualtagqcstatus"),)
        unique_together = ('tag', 'manual_tag')

class MasterReportGen(models.Model):
    TYPES = (
        ('RDY', 'Ready'),
        ('NRY', 'Not Ready'),
        ("PRG", "In Progress"),
        ('FAI', 'Fail')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)
    status = models.CharField(max_length=4, choices=TYPES, default="NRY")
    file = models.URLField(null=True, blank=True)
