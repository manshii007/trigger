#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from __future__ import unicode_literals

import uuid
from comments.models import Comment
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField, JSONField
import cognitive_face as CF
from django.db.models.fields import related
from mptt.models import MPTTModel, TreeForeignKey
import logging
from versatileimagefield.fields import VersatileImageField, PPOIField
from versatileimagefield.placeholder import OnStoragePlaceholderImage
from utils.unique_filename import unique_upload
from users.models import User
from video.models import (
	Video, 
	VideoProxyPath,
)
from workgroups.models import WorkGroup
# from tags.models import ContentLanguage

logger = logging.getLogger('debug')


class GenericLibrary(MPTTModel):
	"""
	Generic Library to hold any model
	"""
	# We can have a mptt generic tree where we can attach any thing to it
	# This way we can define specific models for episode, season, title and versions later
	# We can add anything anywhere in the tree
	# we can filter later on the based on descendants
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.UUIDField()
	content_object = GenericForeignKey('content_type', 'object_id')
	parent = TreeForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
	is_removed = models.BooleanField(default=False)


class Channel(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	channel_name = models.CharField(max_length=128, verbose_name="Name")
	parent_company = models.CharField(max_length=128, blank=True)

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

	def poster_img(self):
		if self.poster:
			return u'<img src="%s" />' % self.poster.thumbnail['100x100'].url

	poster_img.short_description = 'Poster'
	poster_img.allow_tags = True
	channel_code = models.IntegerField(null=True)

	def __str__(self):
		return self.channel_name

	class Meta:
		permissions = (("view_channel", "Can view channel"),)


class Playlist(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	channel = models.ForeignKey(Channel, blank=True, null=True)
	date = models.DateField()
	active = models.BooleanField(default=False)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return "{}_{}".format(self.channel.channel_name, self.date)

	class Meta:
		permissions = (("view_playlist", "Can view playlist"),)


class PlaylistEntry(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	playlist = models.ForeignKey(Playlist, null=True, blank=True)
	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.UUIDField(null=True, blank=True)
	content_object = GenericForeignKey('content_type', 'object_id')

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	start_time = models.DateTimeField(null=True)
	end_time = models.DateTimeField(null=True)

	def __str__(self):
		return str(self.content_object.title)

	class Meta:
		permissions = (("view_playlistentry", "Can view playlist entry"),)


class Genre(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=128, null=True, blank=True, verbose_name="Title")

	def __str__(self):
			return self.title if self.title else ""


class ContextType(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	type_name = models.CharField(max_length=128, verbose_name="Name")

	def __str__(self):
		return self.type_name

class Person(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=128)
	dob = models.DateField(blank=True, null=True)
	born_location = models.CharField(max_length=128, blank=True)
	current_location = models.CharField(max_length=128, blank=True)
	description = models.TextField(blank=True, null=True)
	father_name = models.CharField(max_length=128, blank=True, null=True)
	mother_name = models.CharField(max_length=128, blank=True, null=True)
	partner_name = models.CharField(max_length=128, blank=True, null=True)
	religion = models.CharField(max_length=128, null=True, blank=True)
	caste = models.CharField(max_length=128, null=True, blank=True)
	education = models.TextField(blank=True, null=True)
	occupation = models.CharField(max_length=256, blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE)
	charatcer_played = ArrayField(models.CharField(max_length=200), blank=True, null=True)
	picture = models.URLField(null=True, blank=False)

	def __str__(self):
		return self.name

class CloudPerson(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	person = models.ForeignKey(Person)
	cloud_id = models.CharField(max_length=128)

	def __str__(self):
		return self.person.name


class PersonGroup(models.Model):
	"""Person Group for Azure"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=128)
	persons = models.ManyToManyField(Person, blank=True)
	upload_progress = models.FloatField(default='0', null=True)

	def __str__(self):
		return self.title

	def start_training(self):
		CF.person_group.train(self.id)
	start_training.description = "Start Group Model Training in Cloud"

	def get_training_status(self):
		try:
			status = CF.person_group.get_status(str(self.id))
			return status['status']
		except CF.CognitiveFaceException:
			return 'Person Group DoesNotExist'
	get_training_status.description = "Status"

class Series(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=128)
	alternate_title = models.CharField(max_length=128, blank=True)
	short_title = models.CharField(max_length=128, blank=True)
	version = models.CharField(max_length=128, blank=True)
	part = models.PositiveIntegerField(blank=True, default=1, null=True)
	rating = models.FloatField(blank=True, null=True)
	year_of_release = models.DateField(blank=True, null=True)
	number_of_episodes = models.PositiveIntegerField(blank=True,null=True)
	genre = models.ManyToManyField(Genre, blank=True)
	channel = models.ForeignKey(Channel, null=True, blank=True)
	# cast = models.CharField(max_length=128, null=True, blank=True)
	cbfc = models.CharField(max_length=128, null=True, blank=True)
	status = models.CharField(max_length=128, null=True, blank=True)
	remark = models.CharField(max_length=128, null=True, blank=True)
	producers = models.ManyToManyField(Person, related_name="series_producer", blank=True)
	actors = models.ManyToManyField(Person, related_name="series_actors", blank=True)
	directors = models.ManyToManyField(Person, related_name="series_directors", blank=True)
	dop = models.ManyToManyField(Person, related_name="series_dop", blank=True)
	screenplay = models.ManyToManyField(Person, related_name="series_screenplay", blank=True)
	
	series_no = models.CharField(max_length=128, null=True, blank=True)
	programme_id = models.CharField(max_length=128, null=True, blank=True)
	production_number = models.CharField(max_length=128, null=True, blank=True)
	production_house = models.ForeignKey('tags.ProductionHouse', on_delete=models.SET_NULL, blank=True, null=True)
	compilation = models.CharField(max_length=128, null=True, blank=True)
	status = models.CharField(max_length=128, null=True, blank=True)
	certification = models.CharField(max_length=128, null=True, blank=True)
	classification = models.CharField(max_length=128, null=True, blank=True)
	sequence = models.IntegerField(null=True)
	language = models.ForeignKey('tags.ContentLanguage', on_delete=models.SET_NULL, blank=True, null=True)
	slot_duration = models.FloatField(blank=True, null=True)
	tx_run_time = models.FloatField(blank=True, null=True)
	content_subject = models.CharField(max_length=128, blank=True, null=True)
	external_ref_number = models.CharField(max_length=128, null=True, blank=True)
	barcode = models.CharField(max_length=128, null=True, blank=True)
	tx_id = models.CharField(max_length=128, null=True, blank=True)
	synopsis = models.TextField(blank=True, null=True)
	short_synopsis = models.TextField(blank=True, null=True)
	rank = models.IntegerField(null=True, blank=True)
	country_of_origin = models.CharField(max_length=128, null=True, blank=True)

	ingested_on = models.DateField(null=True, blank=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE)

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

	def poster_img(self):
		if self.poster:
			return u'<img src="%s" />' % self.poster.thumbnail['100x100'].url

	poster_img.short_description = 'Poster'
	poster_img.allow_tags = True

	class Meta:
		verbose_name_plural = 'Series'
		permissions = (("view_series", "Can view series"),)

	def __str__(self):
		return self.title + " S" + str(self.part)

class Character(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	character_name = models.CharField(max_length=128, verbose_name='Name')
	tv_series = models.ForeignKey(Series)
	actor = models.ForeignKey(Person)

	def __str__(self):
		return self.character_name

class Season(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=128)
	secondary_title = models.CharField(max_length=128, blank=True)
	short_title = models.CharField(max_length=128, blank=True)
	series = models.ForeignKey(Series, related_name="seasons")
	season_number = models.PositiveIntegerField(blank=True, null=True)
	telecast_date = models.DateField(blank=True, null=True)
	language = models.TextField(blank=True, null=True)
	content_type = models.ForeignKey(ContextType, blank=True, null=True)
	# genre = models.ManyToManyField(Genre, blank=True)
	content_subject = models.CharField(max_length=128, blank=True, null=True)
	synopsis = models.TextField(blank=True, null=True)
	characters = models.ManyToManyField(Character, blank=True)
	set_in_location = models.CharField(max_length=128, blank=True, null=True)

	producers = models.ManyToManyField(Person, related_name="season_producer", blank=True)
	actors = models.ManyToManyField(Person, related_name="season_actors", blank=True)
	directors = models.ManyToManyField(Person, related_name="season_directors", blank=True)
	dop = models.ManyToManyField(Person, related_name="season_dop", blank=True) 
	screenplay = models.ManyToManyField(Person, related_name="season_screenplay", blank=True)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return self.series.title + "_" + str(self.title) + "_" + str(self.season_number)

	class Meta:
		permissions = (("view_season", "Can view season"),)

class Politician(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	person = models.OneToOneField(Person, blank=False, null=True)
	description = models.TextField(blank=True, null=True)
	political_party = models.CharField(max_length=128, null=True, blank=True)
	constituency = models.CharField(max_length=128, null=True, blank=True)
	positions = models.TextField(max_length=256, blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE)

	def __str__(self):
		if self.person:
			return self.person.name
		else:
			return str(self.id)

	class Meta:
		permissions = (("view_politician", "Can view politician"),)


class TVAnchor(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	person = models.OneToOneField(Person, blank=False, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	books = models.TextField(max_length=256, blank=True, null=True)
	organizations = models.TextField(max_length=256, blank=True, null=True)
	notable_credits = models.TextField(max_length=256, blank=True, null=True)
	awards = models.TextField(max_length=256, blank=True, null=True)

	def __str__(self):
		if self.person:
			return self.person.name
		else:
			return str(self.id)

	class Meta:
		permissions = (("view_tvanchor", "Can view tvanchor"),)


class Actor(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	person = models.OneToOneField(Person, blank=False, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	active_from = models.DateTimeField(null=True, blank=True)
	active_till = models.DateTimeField(null=True, blank=True)
	awards = models.TextField(max_length=256, blank=True, null=True)

	def __str__(self):
		if self.person:
			return self.person.name
		else:
			return str(self.id)

	class Meta:
		permissions = (("view_actor", "Can view actor"),)


class Credit(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	credit = JSONField()
	video = models.ForeignKey(Video)

	def __str__(self):
		return self.video.title

	class Meta:
		permissions = (("view_credit", "Can view credit"),)


class AssetVersion(models.Model):
	"""
	Model for Asset Version
	"""
	#different proxy types
	type_choices = (
		('SRC', 'Source'),
		('ITM', 'Intermediate'),
		('MTR', 'Master'),
	)

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=128, null=True, blank=True) #
	version_number = models.IntegerField(null=True, blank=True) #

	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE) 
	object_id = models.UUIDField(null=True, blank=True)
	asset_object = GenericForeignKey('content_type', 'object_id')
	proxy_type = models.CharField(max_length=20, choices=type_choices, default='SRC', null=True, blank=True)
	is_tagged = models.BooleanField(default=False, blank=True)

	video = models.ForeignKey(Video, null=True, blank=True, on_delete=models.CASCADE)
	is_indexed = models.BooleanField(default=False, blank=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL)

	material_id = models.CharField(max_length=32,unique=True, null=True, blank=True) #
	keywords = models.CharField(max_length=1024, null=True, blank=True) #
	status = models.CharField(max_length=128, null=True, blank=True) #
	certification = models.CharField(max_length=128, null=True, blank=True) #
	classification = models.CharField(max_length=128, null=True, blank=True) #
	language = models.ForeignKey('tags.ContentLanguage', on_delete=models.SET_NULL, blank=True, null=True)
	description = models.TextField(blank=True, null=True) #
	barcode = models.CharField(max_length=128, null=True, blank=True) #
	tx_id = models.CharField(max_length=128, null=True, blank=True) #
	compliance_status = models.CharField(max_length=128, null=True, blank=True) #

	audio_tracks = ArrayField(models.CharField(max_length=100), blank=True, null=True) #
	audio_languages = models.ManyToManyField('tags.ContentLanguage', related_name="assetversion_audio_languages", blank=True)
	is_audio_available = models.BooleanField(default=False, blank=True) #
	subtitle_languages = models.ManyToManyField('tags.ContentLanguage', related_name="assetversion_subtitle_languages", blank=True)
	is_subtitle_available = models.BooleanField(default=False, blank=True) #
	end_credit_start_time = models.FloatField(null=True, blank=True) #
	end_credit_end_time = models.FloatField(null=True, blank=True) #
	is_voice_in_ec = models.BooleanField(default=False, blank=True) #
	is_active = models.BooleanField(default=True, blank=True)
	notes = models.TextField(blank=True, null=True)

	def __str__(self):
		return str(self.title)

	class Meta:
		permissions = (("view_asset_version", "Can view asset version"),)
		
# movies model
class Movie(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=128) #
	# secondary_title = models.CharField(max_length=128, blank=True)
	short_title = models.CharField(max_length=128, blank=True) #
	year_of_release = models.DateField(blank=True, null=True) #
	language = models.ForeignKey('tags.ContentLanguage', on_delete=models.SET_NULL, blank=True, null=True)
	channel = models.ForeignKey(Channel, null=True, blank=True) #
	genre = models.ManyToManyField(Genre, blank=True) #
	content_subject = models.CharField(max_length=128, blank=True, null=True)
	# content_synopsis = models.TextField(blank=True, null=True) #
	# characters = models.ManyToManyField(Character, blank=True) #
	producers = models.ManyToManyField(Person, related_name="movie_producer", blank=True) #
	directors = models.ManyToManyField(Person, related_name="movie_directors", blank=True)
	dop = models.ManyToManyField(Person, related_name="movie_dop", blank=True)
	screenplay = models.ManyToManyField(Person, related_name="movie_screenplay", blank=True)
	location = models.CharField(null=True, blank=True, max_length=128)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	ingested_on = models.DateField(null=True, blank=True)
	# cast, channel, date, cbfc, duration, status
	# cast = models.CharField(max_length=128, null=True, blank=True) #
	cbfc = models.CharField(max_length=128, null=True, blank=True)
	# status = models.CharField(max_length=128, null=True, blank=True) 
	remark = models.CharField(max_length=128, null=True, blank=True)
	asset_version = GenericRelation(AssetVersion)

	aka_title = models.CharField(max_length=128, blank=True) #
	# movie_id = models.CharField(max_length=128, null=True, blank=True) #
	# production_number = models.CharField(max_length=128, null=True, blank=True) #
	production_house = models.ForeignKey('tags.ProductionHouse', on_delete=models.SET_NULL, blank=True, null=True)
	keywords = models.CharField(max_length=1024, null=True, blank=True) #
	status = models.CharField(max_length=128, null=True, blank=True) #
	# production = models.CharField(max_length=256, null=True, blank=True)
	# type_movie = models.CharField(max_length=128, null=True, blank=True) #
	certification = models.CharField(max_length=128, null=True, blank=True) #
	# makers =  models.ManyToManyField(Person, related_name="movie_makers", blank=True) #
	classification = models.CharField(max_length=128, null=True, blank=True) #
	slot_duration = models.FloatField(blank=True, null=True) #
	# duration = models.FloatField(blank=True, null=True) #
	tx_run_time = models.FloatField(blank=True, null=True) #
	external_ref_number = models.CharField(max_length=128, null=True, blank=True) #
	# prod_year = models.IntegerField(null=True, blank=True) #
	barcode = models.CharField(max_length=128, null=True, blank=True) #
	tx_id = models.CharField(max_length=128, null=True, blank=True) #
	synopsis = models.TextField(blank=True, null=True) 
	short_synopsis = models.TextField(blank=True, null=True) # 
	actors = models.ManyToManyField(Person, related_name="movie_actors", blank=True)
	# role = models.CharField(max_length=256, null=True, blank=True) #
	rank = models.IntegerField(null=True, blank=True) #
	part_description = models.TextField(blank=True, null=True) #
	country_of_origin = models.CharField(max_length=128, null=True, blank=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='added_movie')

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

	def poster_img(self):
		if self.poster:
			return u'<img src="%s" />' % self.poster.thumbnail['100x100'].url

	poster_img.short_description = 'Poster'
	poster_img.allow_tags = True

	def __str__(self):
		return self.title

	class Meta:
		permissions = (("view_movie", "Can view movie"),)


# movies segment model
class MovieSegment(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	movie = models.ForeignKey(Movie)
	video = models.ForeignKey(Video)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return self.movie.movie_title+'_'+self.video.title

	class Meta:
		permissions = (("view_moviesegment", "Can view movie segment"),)


# movies model
class Promo(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=128) #
	# secondary_title = models.CharField(max_length=128, blank=True)
	short_title = models.CharField(max_length=128, blank=True)
	language = models.ForeignKey('tags.ContentLanguage', on_delete=models.SET_NULL, blank=True, null=True)
	year_of_release = models.DateField(blank=True, null=True) #
	channel = models.ForeignKey(Channel, null=True, blank=True)

	created_on = models.DateTimeField(auto_now_add=True, null=True) #
	modified_on = models.DateTimeField(auto_now=True, null=True) #

	# cast = models.ManyToManyField(Person, blank=True)
	producers = models.ManyToManyField(Person, related_name="promo_producer", blank=True) #
	actors = models.ManyToManyField(Person, related_name="promo_actors", blank=True)
	directors = models.ManyToManyField(Person, related_name="promo_directors", blank=True)
	dop = models.ManyToManyField(Person, related_name="promo_dop", blank=True)
	screenplay = models.ManyToManyField(Person, related_name="promo_screenplay", blank=True)
	location = models.CharField(null=True, blank=True, max_length=128)
	cbfc = models.CharField(max_length=128, null=True, blank=True) 
	status = models.CharField(max_length=128, null=True, blank=True) #
	remark = models.CharField(max_length=128, null=True, blank=True)

	asset_version = GenericRelation(AssetVersion)

	movie = models.ForeignKey(Movie, null=True, blank=True)
	genre = models.ManyToManyField(Genre, blank=True, null=True) #
	promo_number = models.IntegerField(null=True, blank=True) #
	synopsis = models.TextField(blank=True, null=True) #
	modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="promo_modified_by", null=True) #

	aka_title = models.CharField(max_length=128, blank=True) #
	certification = models.CharField(max_length=128, null=True, blank=True) #
	timecode_in = models.DateTimeField(null=True, blank=True) # 
	notes = models.TextField(blank=True, null=True) #
	country_of_origin = models.CharField(max_length=128, null=True, blank=True) #
	unpackaged_master = models.CharField(max_length=128, null=True, blank=True) #
	sequence = models.IntegerField(null=True) #
	ingested_on = models.DateField(null=True, blank=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='added_promo') #

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

	def poster_img(self):
		if self.poster:
			return u'<img src="%s" />' % self.poster.thumbnail['100x100'].url

	poster_img.short_description = 'Poster'
	poster_img.allow_tags = True

	def __str__(self):
		return self.title

	class Meta:
		permissions = (("view_promo", "Can view promo"),)


# movies segment model
class PromoSegment(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	promo = models.ForeignKey(Promo)
	video = models.ForeignKey(Video)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)


	def __str__(self):
		return self.promo.title+'_'+self.video.title

	class Meta:
		permissions = (("view_promosegment", "Can view promo segment"),)


class Label(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	name = models.CharField(max_length=128)
	started_on = models.DateField(null=True, blank=True)
	active = models.BooleanField(default=False, blank=True)

	def __str__(self):
		return self.name

	class Meta:
		permissions = (("view_label", "Can view label"),)


class Song(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	created_on = models.DateTimeField(auto_now_add=True, null=True) 
	modified_on = models.DateTimeField(auto_now=True, null=True) 

	title = models.CharField(max_length=128, null=True, blank=True)  #

	label = models.ForeignKey(Label, null=True, blank=True) 
	year = models.IntegerField(null=True, blank=True) #
	released_on = models.DateField(null=True, blank=True)
	recorded_on = models.DateField(null=True, blank=True)
	# recorded_in = models.CharField(null=True, blank=True, max_length=128)

	movie = models.ForeignKey(Movie, null=True, blank=True)
	genre = models.CharField(max_length=128, null=True, blank=True) #
	producers = models.ManyToManyField(Person, related_name="songs_producer", blank=True)
	song_writers = models.ManyToManyField(Person, related_name="songs_writer", blank=True)
	singers = models.ManyToManyField(Person, related_name="songs_singer", blank=True)
	# length = models.IntegerField(null=True, blank=True)
	music_directors = models.ManyToManyField(Person, related_name="songs_ms_director", blank=True)
	actors = models.ManyToManyField(Person, related_name="songs_actors", blank=True)
	language = models.CharField(null=True, blank=True, max_length=128) #

	movie_directors = models.ManyToManyField(Person, related_name="songs_movie_director", blank=True)
	duration = models.DateTimeField(null=True) #
	tempo = models.CharField(max_length=128, null=True, blank=True)
	lyrics = models.CharField(max_length=5000, null=True, blank=True)
	version = models.CharField(max_length=5000, null=True, blank=True)
	original_remake = models.CharField(max_length=5000, null=True, blank=True)

	aka_title = models.CharField(max_length=256, null=True, blank=True) #
	song_id = models.CharField(max_length=256, null=True, blank=True) # 
	album = models.CharField(max_length=256, null=True, blank=True) #
	production_house = models.CharField(max_length=256, null=True, blank=True) #
	# production = models.CharField(max_length=256, null=True, blank=True)
	keywords = models.CharField(max_length=1024, null=True, blank=True) #
	status = models.CharField(max_length=128, null=True, blank=True) #
	certification = models.CharField(max_length=128, null=True, blank=True)
	classification = models.CharField(max_length=128, null=True, blank=True)
	slot_duration = models.FloatField(blank=True, null=True)
	tx_run_time = models.FloatField(blank=True, null=True)
	external_ref_number = models.CharField(max_length=128, null=True, blank=True)
	prod_year = models.IntegerField(null=True, blank=True)
	barcode = models.CharField(max_length=128, null=True, blank=True)
	tx_id = models.CharField(max_length=128, null=True, blank=True)
	# rank = models.CharField(max_length=128, null=True, blank=True)
	# artists = models.ManyToManyField(Person, related_name="songs_artists", blank=True)
	makers =  models.ManyToManyField(Person, related_name="songs_makers", blank=True)
	role = models.CharField(max_length=256, null=True, blank=True)
	country_of_origin = models.CharField(max_length=128, null=True, blank=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE, related_name='added_song')

	def __str__(self):
		return self.title

	class Meta:
		permissions = (("view_song", "Can view song"),)


class NxSong(Song):
	content_id = models.CharField(max_length=128, null=True, blank=True)
	video = models.ForeignKey(Video, null=True, blank=True)
	is_processed = models.BooleanField(default=False)

	class Meta:
		permissions = (("view_nxsong", "Can view nx song"),)


class Trivia(models.Model):
	edit_choices = (
		('RIV', 'Review'),
		('CLN', 'Clean'),
		('ACP', 'Accepted'),
		('NCP', 'Not Accepted'),
		('CHK', 'Check')
	)
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	movie = models.ManyToManyField(Movie)
	persons = models.ManyToManyField(Person)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	trivia = models.TextField(blank=False)
	tags = models.ManyToManyField('tags.Tag')
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE, related_name='added_trivia')
	source = models.URLField(null=True, blank=False)
	is_approved = models.CharField(max_length=32, null=True, blank=True)
	approved_by = models.ForeignKey(User, null=True, blank=True, related_name='approved_trivia')
	disapproved_reason = models.CharField(max_length=128, null=True)
	original_description = models.TextField(blank=True, null=True)
	edit_request = models.TextField(blank=True, null=True)
	edit_status = models.CharField(max_length=3, choices=edit_choices, default='CLN', null=True, blank=True)

	def __str__(self):
		return self.trivia

	class Meta:
		permissions = (("view_trivia", "Can view trivia"),)


class TriviaEditLog(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey(User, null=True, blank=True)
	trivia = models.ForeignKey(Trivia, null=True, blank=True)
	trivia_before = models.TextField(blank=False)
	trivia_after = models.TextField(blank=False)
	edited_on = models.DateTimeField()


class TriviaReviewLog(models.Model):
	edit_choices = (
		('RIV', 'Review'),
		('CLN', 'Clean'),
		('ACP', 'Accepted'),
		('NCP', 'Not Accepted'),
		('CHK', 'Check')
	)
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	user = models.ForeignKey(User, null=True, blank=True)
	trivia = models.ForeignKey(Trivia, null=True, blank=True)
	is_approved_before = models.CharField(max_length=32, null=True, blank=False)
	is_approved_after = models.CharField(max_length=32, null=True, blank=False)
	edit_status_before = models.CharField(max_length=3, choices=edit_choices, default='CLN', null=True, blank=True)
	edit_status_after = models.CharField(max_length=3, choices=edit_choices, default='CLN', null=True, blank=True)
	timestamp = models.DateTimeField()


class TriviaLog(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	playlist_entry = models.ForeignKey(PlaylistEntry, null=True, blank=True)
	trivia = models.ForeignKey(Trivia, null=True, blank=True)
	timestamp = models.DateTimeField()

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return str(self.id)

	class Meta:
		permissions = (("view_trivialog", "Can view trivia log"),)


class ChannelClip(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	video = models.ForeignKey(Video, null=True, blank=True)

	start_time = models.DateTimeField(null=True)
	end_time = models.DateTimeField(null=True)
	date = models.DateField(null=True)

	channel = models.ForeignKey(Channel, null=False)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	filled_duration = models.IntegerField(null=True, blank=True)

	def __str__(self):
		if not self.video:
			return str(self.id)
		else:
			return self.video.title

	class Meta:
		permissions = (("view_channelclip", "Can view channel clip"),)

class SongVerification(models.Model):
	"""
	Model for Song QC after it has been tagged
	"""
	created_on = models.DateTimeField(auto_now_add=True, null=True)

	song = models.OneToOneField(Song, blank=False, null=True, on_delete=models.CASCADE)
	user = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE)

	def __str__(self):
		return self.song.title

	class Meta:
		permissions = (("view_song_verification", "Can view song verification"),)

class Sequence(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=256, null=True, blank=True, verbose_name="Title")
	description = models.TextField(blank=True, null=True)

	asset_version = models.ForeignKey(AssetVersion, null=True, blank=True)

	def __unicode__(self):
		return str(self.id)

	def __str__(self):
		return str(self.title)

	class Meta:
		permissions = (("view_sequence", "Can view sequence"),)

class Segment(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=128)

	sequence =  models.ForeignKey(Sequence, on_delete=models.CASCADE, null=True, blank=True)
	start_of_media = models.FloatField(blank=True, null=True)
	end_of_media = models.FloatField(blank=True, null=True)
	duration = models.FloatField(blank=True, null=True)
	description = models.CharField(max_length=1000, blank=True)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)


	def __str__(self):
		return str(self.title)

	class Meta:
		permissions = (("Segment", "Creates a new segment"),)

class Rushes(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=128)
	year_of_release = models.DateField(blank=True, null=True)
	language = models.ForeignKey('tags.ContentLanguage', on_delete=models.SET_NULL, blank=True, null=True)
	channel = models.ForeignKey(Channel, null=True, blank=True)
	genre = models.ManyToManyField(Genre, blank=True, null=True)
	content_subject = models.CharField(max_length=128, blank=True, null=True)
	synopsis = models.TextField(blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	asset_version = GenericRelation(AssetVersion)

	producers = models.ManyToManyField(Person, related_name="rushes_producer", blank=True)
	actors = models.ManyToManyField(Person, related_name="rushes_actors", blank=True)
	directors = models.ManyToManyField(Person, related_name="rushes_directors", blank=True)
	dop = models.ManyToManyField(Person, related_name="rushes_dop", blank=True)
	screenplay = models.ManyToManyField(Person, related_name="rushes_screenplay", blank=True)

	mood = models.CharField(max_length=128, blank=True, null=True)
	event_name = models.CharField(max_length=128, blank=True, null=True)
	event_location = models.CharField(max_length=128, blank=True, null=True)
	ingested_on = models.DateField(null=True, blank=True)
	modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='added_rushes')
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

	def poster_img(self):
		if self.poster:
			return u'<img src="%s" />' % self.poster.thumbnail['100x100'].url

	poster_img.short_description = 'Poster'
	poster_img.allow_tags = True

	def __str__(self):
		return self.title

	class Meta:
		permissions = (("view_rushes", "Can view rushes"),)

class WorkFlow(models.Model):
	"""
	Model for Workflow
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	description = models.CharField(max_length=1024, null=True, blank=True)
	title = models.CharField(max_length=128)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return self.title

	class Meta:
		permissions = (
                    ("user_view_workflow", "User level can view workflow"),("team_view_workflow", "Team level can view workflow"), ("org_view_workflow", "Org level can view workflow"),
                    ("user_add_workflow", "User level can add workflow"),("team_add_workflow", "Team level can add workflow"), ("org_add_workflow", "Org level can add workflow"),
                    ("user_change_workflow", "User level can change workflow"),("team_change_workflow", "Team level can change workflow"), ("org_change_workflow", "Org level can change workflow"),
                    ("user_delete_workflow", "User level can delete workflow"),("team_delete_workflow", "Team level can delete workflow"), ("org_delete_workflow", "Org level can delete workflow"),
                )

class WorkFlowStep(models.Model):
	"""
	Model for Workflow Steps
	"""
	status_choices = (
		('NSD', 'Not Started'),
		('REV', 'Review'),
		('APR', 'Approve'),
		('APE', 'Approve with Edits'),
		('REJ', 'Reject'),
		('CMP', 'Completed'),
		('FAI', 'Failed'),
		('PAS', 'Pass'),
		('OVE', 'Override'),
		('IPR', 'In Progress'),
	)
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	workgroup = models.ForeignKey(WorkGroup, on_delete = models.SET_NULL, blank=True, null=True)
	description = models.CharField(max_length=1024, null=True, blank=True)
	title = models.CharField(max_length=128)
	allowed_status = ArrayField(models.CharField(max_length=100, choices=status_choices), blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return self.title

	class Meta:
		permissions = (("view_workflowstep", "Can view work flow step"),)

class WorkFlowInstance(models.Model):
	"""
	Model for a Workflow instance
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	asset_version =  models.ManyToManyField(AssetVersion, blank=True, null=True, through='WorkFlowInstanceMembership', related_name='work_flow_instances')
	work_flow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, blank=True, null=True)
	due_date = models.DateField(blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return self.work_flow.title
	class Meta:
		permissions = (
                    ("user_view_workflowinstance", "User level can view workflowinstance"),("team_view_workflowinstance", "Team level can view workflowinstance"), ("org_view_workflowinstance", "Org level can view workflowinstance"),
                    ("user_add_workflowinstance", "User level can add workflowinstance"),("team_add_workflowinstance", "Team level can add workflowinstance"), ("org_add_workflowinstance", "Org level can add workflowinstance"),
                    ("user_change_workflowinstance", "User level can change workflowinstance"),("team_change_workflowinstance", "Team level can change workflowinstance"), ("org_change_workflowinstance", "Org level can change workflowinstance"),
                    ("user_delete_workflowinstance", "User level can delete workflowinstance"),("team_delete_workflowinstance", "Team level can delete workflowinstance"), ("org_delete_workflowinstance", "Org level can delete workflowinstance"),
                )


class WorkFlowInstanceMembership(models.Model):
	"""
	Model for a Workflow instance member asset version to cater additional details for an asset version which is added to workflowinstance
	"""
	asset_version = models.ForeignKey(AssetVersion, on_delete=models.CASCADE, blank=True, null=True)
	work_flow_instance = models.ForeignKey(WorkFlowInstance, on_delete=models.CASCADE, blank=True, null=True, related_name='workflow_to_asset')
	# created_by = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return self.asset_version.title + "-->" + self.work_flow_instance.work_flow.title

	class Meta:
		permissions = (("view_workflowinstancemembership", "Can view WorkFlowInstanceMembership"),)
		unique_together = ('asset_version', 'work_flow_instance',)


class WorkFlowInstanceStep(models.Model):
	"""
	Model for a Workflow instance steps
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	work_flow_instance = models.ForeignKey(WorkFlowInstance, on_delete=models.CASCADE, null=True, related_name='work_flow_instance_steps')
	work_flow_step = models.ForeignKey(WorkFlowStep, on_delete=models.CASCADE, null=True)
	work_flow_step_status = models.CharField(max_length=100, blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	modified_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL)

	def __str__(self):
		return self.work_flow_instance.work_flow.title + "-->" + self.work_flow_step.title

	class Meta:
		permissions = (
                    ("user_view_workflowinstancestep", "User level can view workflowinstancestep"),("team_view_workflowinstancestep", "Team level can view workflowinstancestep"), ("org_view_workflowinstancestep", "Org level can view workflowinstancestep"),
                    ("user_add_workflowinstancestep", "User level can add workflowinstancestep"),("team_add_workflowinstancestep", "Team level can add workflowinstancestep"), ("org_add_workflowinstancestep", "Org level can add workflowinstancestep"),
                    ("user_change_workflowinstancestep", "User level can change workflowinstancestep"),("team_change_workflowinstancestep", "Team level can change workflowinstancestep"), ("org_change_workflowinstancestep", "Org level can change workflowinstancestep"),
                    ("user_delete_workflowinstancestep", "User level can delete workflowinstancestep"),("team_delete_workflowinstancestep", "Team level can delete workflowinstancestep"), ("org_delete_workflowinstancestep", "Org level can delete workflowinstancestep"),
                )
		unique_together = ('work_flow_instance', 'work_flow_step',)

class AssignWorkFlowInstanceStep(models.Model):
	"""
	Model for assigning Workflow Instance Step
	"""
	assigned_by = models.ForeignKey(User, null=True, blank=True, related_name='assigned_by')
	assigned_to = models.ForeignKey(User, null=True, blank=True, related_name='assigned_to')

	work_flow_instance_step = models.ForeignKey(WorkFlowInstanceStep, null=True, blank=True, related_name='assigned')

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return str(self.assigned_to.first_name)

	class Meta:
		permissions = (("view_assignworkflowinstancestep", "Can view AssignWorkFlowInstanceStep"),)
		unique_together = ('work_flow_instance_step', 'assigned_to')

class WorkFlowStage(models.Model):
	"""
	Model for different workflow stages
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	work_flow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, null=True, related_name='work_flow_stage')
	next_step = models.ForeignKey(WorkFlowStep, on_delete=models.CASCADE, null=True, related_name='next_step')
	prev_step = models.ForeignKey(WorkFlowStep, on_delete=models.CASCADE, null=True, related_name='previous_step')
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

class WorkFlowTransitionHistory(models.Model):
	"""
	Model for Transition history of an asset
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	work_flow_instance = models.ForeignKey(WorkFlowInstance, on_delete=models.CASCADE, null=True)
	transition_from = models.ForeignKey(WorkFlowInstanceStep, on_delete=models.CASCADE, null=True, related_name='transition_from')
	transition_to = models.ForeignKey(WorkFlowInstanceStep, on_delete=models.CASCADE, null=True, related_name='transition_to')
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

class Collection(models.Model):
	""" 
	Model for Creating a new Collection
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	created_by = models.ForeignKey(User,  null=True, blank=False)
	title = models.CharField(max_length=128)
	asset_version = models.ManyToManyField(AssetVersion, null=True, blank=True)
	description = models.CharField(max_length=1000, blank=True)
	channel = models.ForeignKey(Channel, null=True, blank=True)
	
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return str(self.title)

	class Meta:
		permissions = (("view_collection", "Can view collection"),)	

class WorkFlowCollectionInstance(models.Model):
	"""
	Maps the workflow to a collection
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	collection =  models.ForeignKey(Collection, on_delete=models.CASCADE, blank=True, null=True, related_name='work_flow_instances')
	work_flow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE, blank=True, null=True)
	due_date = models.DateField(blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return self.work_flow.title
	class Meta:
		permissions = (("view_workflowcollectioninstance", "Can view WorkFlowCollectionInstance"),)


class WorkFlowCollectionInstanceStep(models.Model):
	"""
	Keeps track of each workflow step status for a collection via workflowcollectioninstance
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	work_flow_instance = models.ForeignKey(WorkFlowCollectionInstance, on_delete=models.CASCADE, null=True, related_name='work_flow_instance_steps')
	work_flow_step = models.ForeignKey(WorkFlowStep, on_delete=models.CASCADE, null=True)
	work_flow_step_status = models.CharField(max_length=100, blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	modified_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL)

	def __str__(self):
		return self.work_flow_instance.work_flow.title + "-->" + self.work_flow_step.title

	class Meta:
		permissions = (("view_workflowcollectioninstancestep", "Can view WorkFlowCollectionInstanceStep"),)
		unique_together = ('work_flow_instance', 'work_flow_step',)

class AssignWorkFlowCollectionInstanceStep(models.Model):
	"""
	Assign a collection workflow step to a user
	"""
	assigned_by = models.ForeignKey(User, null=True, blank=True, related_name='collection_assigned_by')
	assigned_to = models.ForeignKey(User, null=True, blank=True, related_name='collection_assigned_to')

	work_flow_instance_step = models.ForeignKey(WorkFlowCollectionInstanceStep, null=True, blank=True, related_name='assigned')

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return str(self.assigned_to.first_name)

	class Meta:
		permissions = (("view_assignworkflowcollectioninstancestep", "Can view AssignWorkFlowCollectionInstanceStep"),)
		unique_together = ('work_flow_instance_step', 'assigned_to')

class MetadataAudio(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	file = models.URLField()
	asset_version = models.ForeignKey(AssetVersion, null=True, blank=True)
	
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	language = models.CharField(max_length=128, default='english')
	def __unicode__(self):
		return str(self.id)

	def __str__(self):
		return str(self.id)

	class Meta:
		permissions = (("view_audiometadata", "Can view audio_metadata"),)

class SongAsset(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	ingested_on = models.DateField(null=True, blank=True)

	title = models.CharField(max_length=128, null=True, blank=True) #
	channel = models.ForeignKey(Channel, null=True, blank=True)

	label = models.ForeignKey(Label, null=True, blank=True) #
	year = models.IntegerField(null=True, blank=True) #
	released_on = models.DateField(null=True, blank=True) #
	recorded_on = models.DateField(null=True, blank=True) #
	# recorded_in = models.CharField(null=True, blank=True, max_length=128)

	genre = models.ManyToManyField(Genre, blank=True, null=True) #	
	# length = models.IntegerField(null=True, blank=True) #
	language = models.ForeignKey('tags.ContentLanguage', on_delete=models.SET_NULL, blank=True, null=True)
	
	producers = models.ManyToManyField(Person, related_name="songsasset_producers", blank=True)
	actors = models.ManyToManyField(Person, related_name="songsasset_actors", blank=True)
	directors = models.ManyToManyField(Person, related_name="songsasset_directors", blank=True)
	dop = models.ManyToManyField(Person, related_name="songsasset_dop", blank=True)
	screenplay = models.ManyToManyField(Person, related_name="songsasset_screenplay", blank=True)
	song_writers = models.ManyToManyField(Person, related_name="songsasset_song_writers", blank=True)
	singers = models.ManyToManyField(Person, related_name="songsasset_singer", blank=True)
	location = models.CharField(null=True, blank=True, max_length=128)

	tempo = models.CharField(max_length=128, null=True, blank=True)
	lyrics = models.TextField(blank=True, null=True)
	version = models.CharField(max_length=50, null=True, blank=True)
	original_remake = models.CharField(max_length=50, null=True, blank=True)
	synopsis = models.TextField(blank=True, null=True)

	asset_version = GenericRelation(AssetVersion)
	modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
	
	movie = models.ForeignKey(Movie, null=True, blank=True)
	# music_directors = models.ManyToManyField(Person, related_name="songsasset_ms_director", blank=True)
	# actors = models.ManyToManyField(Person, related_name="songsasset_actors", blank=True)
	aka_title = models.CharField(max_length=256, null=True, blank=True) #
	# song_id = models.CharField(max_length=256, null=True, blank=True) #
	album = models.CharField(max_length=256, null=True, blank=True) #
	production_house = models.ForeignKey('tags.ProductionHouse', on_delete=models.SET_NULL, blank=True, null=True)
	# production = models.CharField(max_length=256, null=True, blank=True) #
	keywords = models.CharField(max_length=1024, null=True, blank=True) #
	status = models.CharField(max_length=128, null=True, blank=True) #
	# type_song = models.CharField(max_length=128, null=True, blank=True) #
	certification = models.CharField(max_length=128, null=True, blank=True) #
	classification = models.CharField(max_length=128, null=True, blank=True) #
	slot_duration = models.FloatField(blank=True, null=True) #
	# duration = models.FloatField(blank=True, null=True) #
	tx_run_time = models.FloatField(blank=True, null=True) #
	external_ref_number = models.CharField(max_length=128, null=True, blank=True) #
	# prod_year = models.IntegerField(null=True, blank=True) #
	barcode = models.CharField(max_length=128, null=True, blank=True) #
	tx_id = models.CharField(max_length=128, null=True, blank=True) #
	rank = models.IntegerField(null=True, blank=True) #
	# artists = models.ManyToManyField(Person, related_name="songs_artists", blank=True)
	# makers =  models.ManyToManyField(Person, related_name="songsasset_makers", blank=True) #
	# role = models.CharField(max_length=256, null=True, blank=True) #
	part_description = models.TextField(blank=True, null=True)
	country_of_origin = models.CharField(max_length=128, null=True, blank=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='added_songasset')
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

	def poster_img(self):
		if self.poster:
			return u'<img src="%s" />' % self.poster.thumbnail['100x100'].url

	poster_img.short_description = 'Poster'
	poster_img.allow_tags = True

	def __str__(self):
		return self.title

	class Meta:
		permissions = (("view_songasset", "Can view songasset"),)

class Episode(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=128)
	secondary_title = models.CharField(max_length=128, blank=True)
	short_title = models.CharField(max_length=128, blank=True)
	season = models.ForeignKey(Season, blank=True, null=True, related_name="episodes")
	episode_number = models.PositiveIntegerField(blank=True, null=True)
	telecast_date = models.DateField(blank=True, null=True)
	# language = models.TextField(blank=True, null=True)
	content_type = models.ForeignKey(ContextType, blank=True, null=True)
	# genre = models.ManyToManyField(Genre, blank=True)
	content_subject = models.CharField(max_length=128, blank=True, null=True)
	synopsis = models.TextField(blank=True, null=True)
	characters = models.ManyToManyField(Character, blank=True)
	set_in_location = models.CharField(max_length=128, blank=True, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	series_no = models.CharField(max_length=128, null=True, blank=True)
	tx_order = models.PositiveIntegerField(blank=True, default=1, null=True)
	keywords = models.CharField(max_length=1024, null=True, blank=True)
	status = models.CharField(max_length=128, null=True, blank=True)
	external_ref_number = models.CharField(max_length=128, null=True, blank=True)
	certification = models.CharField(max_length=128, null=True, blank=True)
	classification = models.CharField(max_length=128, null=True, blank=True)
	slot_duration = models.FloatField(blank=True, null=True)
	tx_run_time = models.FloatField(blank=True, null=True)
	part = models.PositiveIntegerField(blank=True, default=1, null=True)
	barcode = models.CharField(max_length=128, null=True, blank=True)
	tx_id = models.CharField(max_length=128, null=True, blank=True)
	short_synopsis = models.TextField(blank=True, null=True)
	rank = models.IntegerField(null=True, blank=True)
	role = models.CharField(max_length=256, null=True, blank=True)
	
	producers = models.ManyToManyField(Person, related_name="episode_producer", blank=True)
	actors = models.ManyToManyField(Person, related_name="episode_actors", blank=True)
	directors = models.ManyToManyField(Person, related_name="episode_directors", blank=True)
	dop = models.ManyToManyField(Person, related_name="episode_dop", blank=True)
	screenplay = models.ManyToManyField(Person, related_name="episode_screenplay", blank=True)
	
	asset_version = GenericRelation(AssetVersion)

	def __str__(self):
		return self.season.title + "_" + self.title + "_" + str(self.episode_number)

	class Meta:
		permissions = (("view_episode", "Can view episode"),)

class EpisodeSegment(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	episode = models.ForeignKey(Episode)
	video = models.ForeignKey(Video)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __str__(self):
		return self.episode.episode_title+"_"+self.video.title

	class Meta:
		permissions = (("view_episodesegment", "Can view episode segment"),)

class Batch(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	processed = models.BooleanField(default=False)
	last_created_on = models.DateTimeField(blank=True, null=True)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __unicode__(self):
		return str(self.id)

	def __str__(self):
		return str(self.id)

	class Meta:
		permissions = (("view_batch", "Can view batch"),)


class VideoProcessingStatus(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
	video = models.ForeignKey(Video, on_delete=models.CASCADE, null=True, blank=True)
	# hardcuts_processed = models.BooleanField(default=False)
	# facedetection_processed = models.BooleanField(default=False)
	# facematching_processed = models.BooleanField(default=False)
	processed = models.BooleanField(default=False)
	completed = models.BooleanField(default=False)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)

	def __unicode__(self):
		return str(self.id)

	def __str__(self):
		return str(self.id)

	class Meta:
		permissions = (("view_videoprocessingstatus", "Can view batch"),)
		unique_together = ('batch', 'video',)

class CommercialAsset(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	title = models.CharField(max_length=128, null=True, blank=True) 
	asset_version = GenericRelation(AssetVersion)
	aka_title = models.CharField(max_length=256, null=True, blank=True)
	production_house = models.ForeignKey('tags.ProductionHouse', on_delete=models.SET_NULL, blank=True, null=True)
	product_code = models.CharField(max_length=256, null=True, blank=True)
	language = models.ForeignKey('tags.ContentLanguage', on_delete=models.SET_NULL, blank=True, null=True)
	ingested_on = models.DateField(null=True, blank=True)
	year_of_release = models.DateField(blank=True, null=True)
	synopsis = models.TextField(blank=True, null=True) 
	remark = models.CharField(max_length=128, null=True, blank=True)
	channel = models.ForeignKey(Channel, null=True, blank=True)
	# country_of_origin = models.CharField(max_length=128, null=True, blank=True)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE, related_name='added_commercialasset')
	country_of_origin = models.CharField(max_length=128, null=True, blank=True)
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

	def poster_img(self):
		if self.poster:
			return u'<img src="%s" />' % self.poster.thumbnail['100x100'].url

	poster_img.short_description = 'Poster'
	poster_img.allow_tags = True
	def __unicode__(self):
		return str(self.id)

	def __str__(self):
		return str(self.title)

	class Meta:
		permissions = (("view_commercialasset", "Can view commercialasset"),)

class DemoOTP(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	uniq_id = models.CharField(max_length=256)
	email = models.CharField(max_length=256)
	
	class Meta:
		permissions = (("view_demo", "Can view demo"),)

class File(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	video_id = models.UUIDField(editable=False, null=True)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	type = models.CharField(max_length=128, null=True)
	title = models.CharField(max_length=128, null=True)
	url = models.URLField(null=True, blank=True)	
	location = models.ForeignKey('Folder', null=True, blank=True, related_name="file_folderlocation")
	category = models.ForeignKey('Folder', null=True, blank=True, related_name="file_category")
	channel = models.ForeignKey(Channel, null=True, blank=True, related_name="file")
	file_metadata = JSONField(default=dict, blank=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE, related_name='%(class)s_file_created_by')
	modified_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE, related_name='%(class)s_file_modified_by')
	# notes = models.CharField(max_length=128, null=True)

	class Meta:
		permissions = (
                    ("user_view_file", "User level can view file"),("team_view_file", "Team level can view file"), ("org_view_file", "Org level can view file"),
                    ("user_add_file", "User level can add file"),("team_add_file", "Team level can add file"), ("org_add_file", "Org level can add file"),
                    ("user_change_file", "User level can change file"),("team_change_file", "Team level can change file"), ("org_change_file", "Org level can change file"),
                    ("user_delete_file", "User level can delete file"),("team_delete_file", "Team level can delete file"), ("org_delete_file", "Org level can delete file"),
                )

class Folder(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	title = models.CharField(max_length=128, null=True)
	parent = models.ForeignKey('self', null=True, blank=True, related_name="folder_parent")
	channel = models.ForeignKey(Channel, null=True, blank=True, related_name="folder")
	category = models.ForeignKey('self', null=True, blank=True, related_name="folder_category")
	title_metadata = JSONField(default=dict, blank=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE, related_name='%(class)s_folder_created_by')
	modified_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.CASCADE, related_name='%(class)s_folder_modified_by')
	# created by, created on, is visible, is deleted
	# ensure atomic transactions

	def __str__(self):
		return str(self.title)

	class Meta:
		permissions = (
                    ("user_view_folder", "User level can view folder"),("team_view_folder", "Team level can view folder"), ("org_view_folder", "Org level can view folder"),
                    ("user_add_folder", "User level can add folder"),("team_add_folder", "Team level can add folder"), ("org_add_folder", "Org level can add folder"),
                    ("user_change_folder", "User level can change folder"),("team_change_folder", "Team level can change folder"), ("org_change_folder", "Org level can change folder"),
                    ("user_delete_folder", "User level can delete folder"),("team_delete_folder", "Team level can delete folder"), ("org_delete_folder", "Org level can delete folder"),
                )

class Demo(models.Model):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=128) 
	email = models.CharField(max_length=256)
	company = models.CharField(max_length=256, null=True, blank=True)
	description = models.TextField(blank=True, null=True) 

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	
	def __unicode__(self):
		return str(self.id)

	def __str__(self):
		return str(self.name)

	class Meta:
		permissions = (("view_demo", "Can view demo"),)

class Projects(models.Model):
	"""
	Model for Projects
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=128)
	description = models.TextField(blank=True, null=True)
	workflow = models.ForeignKey(WorkFlow, null=True, blank=True, on_delete=models.SET_NULL)
	
	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='%(class)s_folder_created_by')
	modified_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='%(class)s_folder_modified_by')

	def __str__(self):
		return str(self.name)

	class Meta:
		permissions = (
                    ("user_view_projects", "User level can view project"),("team_view_projects", "Team level can view project"), ("org_view_projects", "Org level can view project"),
                    ("user_add_projects", "User level can add project"),("team_add_projects", "Team level can add project"), ("org_add_projects", "Org level can add project"),
                    ("user_change_projects", "User level can change project"),("team_change_projects", "Team level can change project"), ("org_change_projects", "Org level can change project"),
                    ("user_delete_projects", "User level can delete project"),("team_delete_projects", "Team level can delete project"), ("org_delete_projects", "Org level can delete project"),
                )

class ProjectVersion(models.Model):
	"""
	Model for different versions of project
	"""
	version_choices = (
		("Master", "master"),	
		("Source", "source"),
		("Intermediate", "intermediate")
	)
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	project = models.ForeignKey(Projects, on_delete=models.CASCADE)
	workflow_instance = models.ForeignKey(WorkFlowInstance, on_delete=models.SET_NULL, null=True)
	version_type = models.CharField(max_length=100, choices=version_choices)
	version_number = models.IntegerField(null=False)
	user_comments = GenericRelation(Comment)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='%(class)s_folder_created_by')
	modified_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='%(class)s_folder_modified_by')

	def __str__(self):
		return str(self.project.name)+ " " + str(self.version_number)

	class Meta:
		permissions = (
                    ("user_view_projectversion", "User level can view projectversion"),("team_view_projectversion", "Team level can view projectversion"), ("org_view_projectversion", "Org level can view projectversion"),
                    ("user_add_projectversion", "User level can add projectversion"),("team_add_projectversion", "Team level can add projectversion"), ("org_add_projectversion", "Org level can add projectversion"),
                    ("user_change_projectversion", "User level can change projectversion"),("team_change_projectversion", "Team level can change projectversion"), ("org_change_projectversion", "Org level can change projectversion"),
                    ("user_delete_projectversion", "User level can delete projectversion"),("team_delete_projectversion", "Team level can delete projectversion"), ("org_delete_projectversion", "Org level can delete projectversion"),
                )

class ProjectFiles(models.Model):
	"""
	Model for saving project files
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	project = models.ForeignKey(Projects, on_delete=models.CASCADE)
	file = models.ForeignKey(File, on_delete=models.CASCADE)
	start_time = models.CharField(max_length=32, null=True, blank=True)
	end_time = models.CharField(max_length=32, null=True, blank=True)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='%(class)s_folder_created_by')
	modified_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='%(class)s_folder_modified_by')

	def __str__(self):
		return str(self.file.title)

	class Meta:
		permissions = (
                    ("user_view_projectfiles", "User level can view project files"),("team_view_projectfiles", "Team level can view project files"), ("org_view_projectfiles", "Org level can view project files"),
                    ("user_add_projectfiles", "User level can add project files"),("team_add_projectfiles", "Team level can add project files"), ("org_add_projectfiles", "Org level can add project files"),
                    ("user_change_projectfiles", "User level can change project files"),("team_change_projectfiles", "Team level can change project files"), ("org_change_projectfiles", "Org level can change project files"),
                    ("user_delete_projectfiles", "User level can delete project files"),("team_delete_projectfiles", "Team level can delete project files"), ("org_delete_projectfiles", "Org level can delete project files"),
                )

class WorkFlowMetadata(models.Model):
	"""
	Model for accomodating workflow based project metadata
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	workflow = models.ForeignKey(WorkFlow, on_delete=models.CASCADE)
	field_name = models.CharField(max_length=126, null=False)
	field_type = models.CharField(max_length=126, null=True, blank=True)
	placeholder = models.CharField(max_length=1024, null=True, blank=True)
	opt_values = ArrayField(models.CharField(max_length=100), blank=True, null=True)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='%(class)s_folder_created_by')
	modified_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='%(class)s_folder_modified_by')


	def __str__(self):
		return str(self.field_name)

	class Meta:
		permissions = (
                    ("user_view_workflowmetadata", "User level can view workflow metadata"),("team_view_workflowmetadata", "Team level can view workflow metadata"), ("org_view_workflowmetadata", "Org level can view workflow metadata"),
                    ("user_add_workflowmetadata", "User level can add workflow metadata"),("team_add_workflowmetadata", "Team level can add workflow metadata"), ("org_add_workflowmetadata", "Org level can add workflow metadata"),
                    ("user_change_workflowmetadata", "User level can change workflow metadata"),("team_change_workflowmetadata", "Team level can change workflow metadata"), ("org_change_workflowmetadata", "Org level can change workflow metadata"),
                    ("user_delete_workflowmetadata", "User level can delete workflow metadata"),("team_delete_workflowmetadata", "Team level can delete workflow metadata"), ("org_delete_workflowmetadata", "Org level can delete workflow metadata"),
                )

class ProjectMetadata(models.Model):
	"""
	Links WorkFlowMetadata with projects and stores the value
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	workflow_metadata = models.ForeignKey(WorkFlowMetadata, on_delete=models.CASCADE)
	project = models.ForeignKey(Projects, on_delete=models.CASCADE)
	value = models.CharField(max_length=1024, null=True, blank=True)

	created_on = models.DateTimeField(auto_now_add=True, null=True)
	modified_on = models.DateTimeField(auto_now=True, null=True)
	created_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='%(class)s_folder_created_by')
	modified_by = models.ForeignKey(User, null=True, blank=False, on_delete=models.SET_NULL, related_name='%(class)s_folder_modified_by')

	class Meta:
		permissions = (
                    ("user_view_projectmetadata", "User level can view project metadata"),("team_view_projectmetadata", "Team level can view project metadata"), ("org_view_projectmetadata", "Org level can view project metadata"),
                    ("user_add_projectmetadata", "User level can add project metadata"),("team_add_projectmetadata", "Team level can add project metadata"), ("org_add_projectmetadata", "Org level can add project metadata"),
                    ("user_change_projectmetadata", "User level can change project metadata"),("team_change_projectmetadata", "Team level can change project metadata"), ("org_change_projectmetadata", "Org level can change project metadata"),
                    ("user_delete_projectmetadata", "User level can delete project metadata"),("team_delete_projectmetadata", "Team level can delete project metadata"), ("org_delete_projectmetadata", "Org level can delete project metadata"),
                )
