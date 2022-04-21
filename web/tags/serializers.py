#
#  Copyright (C) Tessact Pvt. Ltd. - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Aswin Chandran <aswin@tessact.com>, January 2017
#
from rest_framework import serializers
from versatileimagefield.serializers import VersatileImageFieldSerializer
from django.contrib.postgres.search import TrigramSimilarity
import random
from content.models import ChannelClip
from .models import (
    Marker,
    Tag,
    TagCategory,
    FrameTag,
    SceneTag,
    KeywordTag,
    Logo,
    LogoTag,
    OCRTag,
    ComplianceStatusTag,
    CheckTag,
    CorrectionTag,
    BarcTag,

    ProgramGenre,
    ProgramTheme,
    AdvertiserGroup,
    Advertiser,
    BrandName,
    BrandSector,
    BrandCategory,
    Title,
    Descriptor,
    Channel,
    ChannelNetwork,
    ChannelGenre,
    Region,
    ContentLanguage,
    ProductionHouse,
    Program,
    Promo,
    Commercial,
    PlayoutTag,

    SpriteTag,
    CommercialTag,
    PromoCategory,
    GenericTag,
    ManualTag,
    ManualTagQCStatus,
    MasterReportGen
)
from comments.models import Comment
from users.models import User
from content.models import Song, Label, Person, Movie
from django.contrib.contenttypes.models import ContentType
from content.models import AssetVersion
from video.serializers import VideoSerializer

class DetailedAssetVersionSerializer(serializers.ModelSerializer):
    video = VideoSerializer(many=False, read_only=True)
    
    class Meta:
        model = AssetVersion
        fields = '__all__'

class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = "__all__"
        read_only_fields = ("id",)


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = "__all__"


class SoftMovieSerializer(serializers.ModelSerializer):

    class Meta:
        model = Movie
        fields = ("id", "movie_title", 'secondary_title', "short_title", "year_of_release", "language", "genre",
                  "content_subject", "content_synopsis", "characters", "created_on", "modified_on",  "channel")
        read_only_fields = ("id",)


class DetailSongSerializer(serializers.ModelSerializer):
    label = LabelSerializer(read_only=True)
    movie = SoftMovieSerializer(read_only=True)
    producers = PersonSerializer(read_only=True, many=True)
    actors = PersonSerializer(read_only=True, many=True)
    music_directors = PersonSerializer(read_only=True, many=True)
    singers = PersonSerializer(read_only=True, many=True)
    song_writers = PersonSerializer(read_only=True, many=True)

    class Meta:
        model = Song
        fields = ("id", "title", "year", "released_on", "recorded_on", "recorded_in", "label",
                  "movie", "genre", "producers", "song_writers", "singers", "length", "music_directors",
                  "actors", "language")


class CommercialTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = CommercialTag
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name',)


class TagCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TagCategory
        fields = ('url', 'id', 'name')


class TagSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(queryset=TagCategory.objects.all(), slug_field='name')

    class Meta:
        model = Tag
        fields = ('url', 'id', 'name', 'category', 'created_on', 'modified_on')


class MildTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name')


class TagByCategorySource(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('url', 'name')


class TagByCategorySerializer(serializers.ModelSerializer):
    tags = TagByCategorySource(many=True, source='tag_set')

    class Meta:
        model = TagCategory
        fields =('url', 'name', 'tags')


class RelatedCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id","user","comment", "submit_datetime")

class DetailGenericTagSerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GenericTag
        fields = ("id", "title", "parent")

    def get_data(self, obj):
        tmp = {}
        if obj:
            tmp['title'] = obj.title
            tmp['id'] = str(obj.id)
            tmp_obj = obj.parent
            tmp['parent'] = self.get_data(tmp_obj) if tmp_obj else {}
        return tmp

    def get_parent(self, obj):
        tmp = self.get_data(obj.parent)
        return tmp

class GenericTagSerializer(serializers.ModelSerializer):

    class Meta:
        model  = GenericTag
        fields = "__all__"

class MarkerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Marker
        fields = "__all__"

class FrameTagSerializer(serializers.ModelSerializer):
    tag = DetailGenericTagSerializer(many=False)
    tagname = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    stopTime = serializers.SerializerMethodField()
    user_comments = RelatedCommentSerializer(read_only=True, many=True)
    created_by = UserSerializer(read_only=True)
    content_type = serializers.SerializerMethodField(read_only=True)
    content_type_title = serializers.SerializerMethodField(read_only=True)
    markers = serializers.SerializerMethodField()

    class Meta:
        model = FrameTag
        fields = ('url', 'id', 'tag', 'tagname', 'category', 'video', 'frame_in', 'frame_out', 'comment', 'time', 'stopTime',
                  'words', 'is_approved', 'user_comments', 'created_by', 'content_type', "content_type_title", 'is_cbfc','collection', 'index', 'created_on', 'modified_on', 'height', 'width', 'up_left_x', 'up_left_y',\
                  'img_width', 'img_height', 'is_edl', 'is_india', 'is_international', 'markers')

    def get_tagname(self, obj):
        if obj.tag:
            return obj.tag.title
        else:
            return None

    def get_category(self, obj):
        if obj.tag:
            return obj.tag.parent.title
        else:
            return None

    def get_time(self, obj):
        return obj.frame_in/obj.video.frame_rate

    def get_stopTime(self, obj):
        return obj.frame_out/obj.video.frame_rate

    def get_content_type_title(self, obj):
        frame_tag_ctype = ContentType.objects.get_for_model(FrameTag)
        return frame_tag_ctype.model

    def get_content_type(self, obj):
        frame_tag_ctype = ContentType.objects.get_for_model(FrameTag)
        return frame_tag_ctype.id
    
    def get_markers(self, obj):
        return MarkerSerializer(Marker.objects.filter(frame_tag__id=obj.id), many=True).data

class CheckTagSerializer(serializers.ModelSerializer):

    autotag = DetailGenericTagSerializer(many=False)
    usertag = DetailGenericTagSerializer(many=False)
    autotagname = serializers.SerializerMethodField()
    usertagname = serializers.SerializerMethodField()
    autotagcategory = serializers.SerializerMethodField()
    usertagcategory = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = CheckTag
        fields = ('id', 'video', 'autotag', 'usertag', 'autotagname', 'usertagname' ,'autotagcategory', 'usertagcategory',
                  'created_by', 'created_on', 'modified_on', 'height', 'width', 'up_left_x', 'up_left_y',\
                  'img_width', 'img_height')

    def get_autotagname(self, obj):
        if obj.autotag:
            return obj.autotag.title
        else:
            return None

    def get_usertagname(self, obj):
        if obj.usertag:
            return obj.usertag.title
        else:
            return None

    def get_autotagcategory(self, obj):
        if obj.autotag:
            return obj.autotag.parent.title
        else:
            return None

    def get_usertagcategory(self, obj):
        if obj.usertag:
            return obj.usertag.parent.title
        else:
            return None


class CreateCheckTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = CheckTag
        fields = "__all__"

class CorrectionTagSerializer(serializers.ModelSerializer):

    time = serializers.SerializerMethodField()
    stopTime = serializers.SerializerMethodField()
    created_by = UserSerializer(read_only=True)
    checktag = CheckTagSerializer(many=True)

    class Meta:
        model = CorrectionTag
        fields = ('image_url', 'id', 'checktag' ,'video', 'frame_in', 'frame_out', 'time', 'stopTime',
                  'created_by', 'created_on', 'modified_on')

    def get_time(self, obj):
        return obj.frame_in/obj.video.frame_rate

    def get_stopTime(self, obj):
        return obj.frame_out/obj.video.frame_rate

class CreateCorrectionTagSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        if attrs['frame_in'] > attrs['frame_out']:
            raise serializers.ValidationError("Frame out should be greater than Frame in")
        return attrs


    class Meta:
        model = CorrectionTag
        fields = "__all__"


class FrameTagCollectionSerializer(serializers.ModelSerializer):
    tag = DetailGenericTagSerializer(many=False)
    tagname = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    stopTime = serializers.SerializerMethodField()
    user_comments = RelatedCommentSerializer(read_only=True, many=True)
    created_by = UserSerializer(read_only=True)
    content_type = serializers.SerializerMethodField(read_only=True)
    content_type_title = serializers.SerializerMethodField(read_only=True)
    asset_version = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FrameTag
        fields = ('url', 'id', 'tag', 'tagname', 'category', 'video', 'frame_in', 'frame_out', 'comment', 'time', 'stopTime',
                  'words', 'is_approved', 'user_comments', 'created_by', 'content_type', "content_type_title", 'is_cbfc','collection', 'index', 
                  'asset_version')

    def get_tagname(self, obj):
        if obj.tag:
            return obj.tag.title
        else:
            return None

    def get_category(self, obj):
        if obj.tag:
            return obj.tag.parent.title
        else:
            return None

    def get_time(self, obj):
        return obj.frame_in/obj.video.frame_rate

    def get_stopTime(self, obj):
        return obj.frame_out/obj.video.frame_rate

    def get_content_type_title(self, obj):
        frame_tag_ctype = ContentType.objects.get_for_model(FrameTag)
        return frame_tag_ctype.model

    def get_content_type(self, obj):
        frame_tag_ctype = ContentType.objects.get_for_model(FrameTag)
        return frame_tag_ctype.id

    def get_asset_version(self, obj):
        return DetailedAssetVersionSerializer(AssetVersion.objects.filter(video=obj.video).first(), many=False, context=self.context).data

class CreateFrameTagSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        if attrs['frame_in'] > attrs['frame_out']:
            raise serializers.ValidationError("Frame out should be greater than Frame in")
        return attrs

    content_type = serializers.SerializerMethodField(read_only=True)
    content_type_title = serializers.SerializerMethodField(read_only=True)
    user_comments = RelatedCommentSerializer(read_only=True, many=True)

    class Meta:
        model = FrameTag
        fields = ('id', 'tag', 'video', 'frame_in', 'frame_out', 'comment', 'words', 'is_approved', 'created_by',
                  "content_type", "content_type_title", "is_cbfc", "user_comments", 'collection', 'index', 'is_edl', 'is_india', 'is_international')
        extra_kwargs={'tag': {"required": False}, 'is_approved':{"required": False}, 'id':{"read_only": True},
                      'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True},
                      'user_comments':{"read_only": True}}

    def get_content_type_title(self, obj):
        frame_tag_ctype = ContentType.objects.get_for_model(FrameTag)
        return frame_tag_ctype.model

    def get_content_type(self, obj):
        frame_tag_ctype = ContentType.objects.get_for_model(FrameTag)
        return frame_tag_ctype.id

class ManualTagSerializer(serializers.ModelSerializer):
    # tags = serializers.PrimaryKeyRelatedField(queryset=GenericTag.objects.all(),many=True, allow_empty=True)
    # tags = DetailGenericTagSerializer(many=True)
    time = serializers.SerializerMethodField()
    stopTime = serializers.SerializerMethodField()
    user_comments = RelatedCommentSerializer(read_only=True, many=True)
    created_by = UserSerializer(read_only=True)
    content_type = serializers.SerializerMethodField(read_only=True)
    tags = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ManualTag
        fields = ('id', 'tags', 'video', 'frame_in', 'frame_out', 'comment', 'time', 'stopTime',
                  'words', 'is_approved', 'user_comments', 'created_by', 'content_type', 'is_cbfc', 'created_on', 'modified_on')

    def get_time(self, obj):
        return obj.frame_in/obj.video.frame_rate

    def get_stopTime(self, obj):
        return obj.frame_out/obj.video.frame_rate

    def get_content_type(self, obj):
        frame_tag_ctype = ContentType.objects.get_for_model(ManualTag)
        return frame_tag_ctype.id

    def get_tags(self, obj):
        manual_tag_qc_list = ManualTagQCStatus.objects.filter(manual_tag=obj)
        dicto = []
        for ob in manual_tag_qc_list:
            generic_tag = GenericTag.objects.filter(id=ob.tag.id).first()
            tag = DetailGenericTagSerializer(generic_tag).data
            tag['qc_approved'] = ob.qc_approved
            dicto.append(tag)
        
        return dicto

class CreateManualTagSerializer(serializers.ModelSerializer):
    content_type = serializers.SerializerMethodField(read_only=True)
    user_comments = RelatedCommentSerializer(read_only=True, many=True)

    class Meta:
        model = ManualTag
        fields = ('id', 'tags', 'video', 'frame_in', 'frame_out', 'comment', 'words', 'is_approved', 'created_by',
                  "content_type", "is_cbfc", "user_comments", 'created_on', 'modified_on')
        extra_kwargs={'tags': {"required": False}, 'is_approved':{"required": False}, 'id':{"read_only": True},
                      'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True},
                      'user_comments':{"read_only": True}}

    def get_content_type(self, obj):
        frame_tag_ctype = ContentType.objects.get_for_model(ManualTag)
        return frame_tag_ctype.id


class SceneTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = SceneTag
        fields = '__all__'


class KeywordTagSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()
    stopTime = serializers.SerializerMethodField()
    user_comments = RelatedCommentSerializer(read_only=True, many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),many=True, allow_empty=True)
    content_type = serializers.SerializerMethodField(read_only=True)
    content_type_title = serializers.SerializerMethodField(read_only=True)
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = KeywordTag
        fields = ('url', 'id', 'tags', 'video', 'words', 'frame_in', 'frame_out', 'comment', 'time', 'stopTime',
                  'sentiment_score', 'sentiment_magnitude', 'is_approved', 'user_comments', 'word_level', "content_type", "content_type_title", "created_by", "is_cbfc",
                  'created_on', 'modified_on')
        read_only_fields = ('time', 'stopTime', 'user_comments')
        extra_kwargs={'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True},}

    def get_time(self, obj):
        return obj.frame_in/obj.video.frame_rate

    def get_stopTime(self, obj):
        return obj.frame_out/obj.video.frame_rate

    def get_content_type_title(self, obj):
        frame_tag_ctype = ContentType.objects.get_for_model(KeywordTag)
        return frame_tag_ctype.model

    def get_content_type(self, obj):
        frame_tag_ctype = ContentType.objects.get_for_model(KeywordTag)
        return frame_tag_ctype.id


class OCRTagSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()
    stopTime = serializers.SerializerMethodField()

    class Meta:
        model = OCRTag
        fields = ('id', 'tags', 'video', 'words', 'frame_in', 'frame_out', 'comment', 'time', 'stopTime',
                  'sentiment_score', 'sentiment_magnitude', 'language')
        read_only_fields = ('time', 'stopTime')

    def get_time(self, obj):
        return obj.frame_in/obj.video.frame_rate

    def get_stopTime(self, obj):
        return obj.frame_out/obj.video.frame_rate


class LogoSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(queryset=TagCategory.objects.all(), slug_field='name')
    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )

    class Meta:
        model = Logo
        fields = ('url', 'id', 'name', 'category', 'created_on', 'modified_on', 'poster')


class LogoTagSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()
    stopTime = serializers.SerializerMethodField()
    tag = LogoSerializer()

    class Meta:
        model = LogoTag
        fields = ('url', 'id', 'tag', 'video', 'frame_in', 'frame_out', 'comment', 'time', 'stopTime')
        read_only_fields = ('time', 'stopTime')

    def get_time(self, obj):
        return obj.frame_in / obj.video.frame_rate

    def get_stopTime(self, obj):
        return obj.frame_out / obj.video.frame_rate


class ComplianceStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceStatusTag
        fields = '__all__'


class TitleSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Title
        fields = ("id", "name", "code")

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class CreateTitleSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Title
        fields = ("id", "name", "code")
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class DescriptorSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Descriptor
        fields = ("id", "text", "code")

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class CreateDescriptorSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Descriptor
        fields = ("id", "text", "code")
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class BrandSectorSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BrandSector
        fields = ("id", "name", "code")

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class CreateBrandSectorSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BrandSector
        fields = ("id", "name", "code")
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class BrandCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandCategory
        fields = "__all__"


class CreateBrandCategorySerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BrandCategory
        fields = ("id", "name", "brand_sector", "code")
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class DetailBrandCategorySerializer(serializers.ModelSerializer):
    brand_sector = BrandSectorSerializer(read_only=True)
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BrandName
        fields = ("id", "name", "code", "brand_sector")

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class BrandNameSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BrandName
        fields = ("id", "name", "code", "brand_category")
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class DetailBrandNameSerializer(serializers.ModelSerializer):
    brand_category = DetailBrandCategorySerializer(read_only=True)
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BrandName
        fields = ("id", "name", "code", "brand_category")

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class AdvertiserGroupSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AdvertiserGroup
        fields = ("id", "name", "code")

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class CreateAdvertiserGroupSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AdvertiserGroup
        fields = ("id", "name", "code")
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class AdvertiserSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Advertiser
        fields = ("id", "name", "advertiser_group", "code")
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class DetailAdvertiserSerializer(serializers.ModelSerializer):
    advertiser_group = AdvertiserGroupSerializer(read_only=True)
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Advertiser
        fields = ("id", "name", "code", "advertiser_group")

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class ProgramThemeSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProgramTheme
        fields = ("id", "name", "code")

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class ProgramGenreSerializer(serializers.ModelSerializer):
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProgramGenre
        fields = ("id", "name", "code", "program_theme", "marked", "deleted")

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class DetailProgramGenreSerializer(serializers.ModelSerializer):
    program_theme = ProgramThemeSerializer(read_only=True)
    # code = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProgramGenre
        fields = ("id", "name", "code", "program_theme", "created_on", "marked", "deleted")

    # def get_code(self, instance):
    #     random.seed(instance.code)
    #     return random.getrandbits(29)


class ChannelNetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelNetwork
        fields = "__all__"


class ChannelGenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChannelGenre
        fields = "__all__"


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = "__all__"


class ContentLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentLanguage
        fields = "__all__"


class ProductionHouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionHouse
        fields = "__all__"


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = "__all__"


class ProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = Program
        fields = "__all__"
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}


class SoftDetailProgramSerializer(serializers.ModelSerializer):
    title = TitleSerializer(read_only=True)
    language = ContentLanguageSerializer(read_only=True)
    prod_house = ProductionHouseSerializer(read_only=True)
    program_genre = DetailProgramGenreSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = Program
        fields = ("id", "title", "language", "prod_house", "program_genre",
                  "channel")


class TDetailProgramSerializer(serializers.ModelSerializer):
    title = TitleSerializer(read_only=True)
    language = ContentLanguageSerializer(read_only=True)
    prod_house = ProductionHouseSerializer(read_only=True)
    program_genre = DetailProgramGenreSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    similars = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Program
        fields = ("id", "title", "language", "prod_house", "program_genre",
                  "channel", "similars")

    def get_similars(self, obj):
        p = Program.objects.filter(title__name__trigram_similar=obj.title.name, channel__name=obj.channel.name).exclude(id=obj.id)[0:5]
        ser = SoftDetailProgramSerializer(p, many=True)
        return ser.data


class DetailProgramSerializer(serializers.ModelSerializer):
    title = TitleSerializer(read_only=True)
    language = ContentLanguageSerializer(read_only=True)
    prod_house = ProductionHouseSerializer(read_only=True)
    program_genre = DetailProgramGenreSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)
    similars = serializers.SerializerMethodField(read_only=True)
    created_by = UserSerializer(read_only=True, many=False)

    class Meta:
        model = Program
        fields = ("id", "title", "language", "prod_house", "program_genre",
                  "channel", "similars", "marked", "deleted", "created_on", "created_by")

    def get_similars(self, obj):
        return ""


class PromoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promo
        fields = "__all__"
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}


class SoftDetailPromoSerializer(serializers.ModelSerializer):
    title = DetailBrandNameSerializer(read_only=True, source='brand_name')
    channel = ChannelSerializer(read_only=True)
    promo_channel = ChannelSerializer(read_only=True)
    brand_name = DetailBrandNameSerializer(read_only=True)
    advertiser = DetailAdvertiserSerializer(read_only=True)
    descriptor = DescriptorSerializer(read_only=True)

    class Meta:
        model = Program
        fields = ("id", "title", "channel", "promo_channel", "brand_name", "advertiser",
                  "descriptor")


class TDetailPromoSerializer(serializers.ModelSerializer):
    title = DetailBrandNameSerializer(read_only=True, source='brand_name')
    channel = ChannelSerializer(read_only=True)
    promo_channel = ChannelSerializer(read_only=True)
    brand_name = DetailBrandNameSerializer(read_only=True)
    advertiser = DetailAdvertiserSerializer(read_only=True)
    descriptor = DescriptorSerializer(read_only=True)
    similars = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Program
        fields = ("id", "title", "channel", "promo_channel", "brand_name", "advertiser",
                  "descriptor", "similars")

    def get_similars(self, obj):
        p = Promo.objects.filter(brand_name__name__trigram_similar=obj.brand_name.name).exclude(id=obj.id)[0:5]
        ser = SoftDetailPromoSerializer(p, many=True)
        return ser.data


class DetailPromoSerializer(serializers.ModelSerializer):
    title = DetailBrandNameSerializer(read_only=True, source='brand_name')
    channel = ChannelSerializer(read_only=True)
    promo_channel = ChannelSerializer(read_only=True)
    brand_name = DetailBrandNameSerializer(read_only=True)
    advertiser = DetailAdvertiserSerializer(read_only=True)
    descriptor = DescriptorSerializer(read_only=True)
    similars = serializers.SerializerMethodField(read_only=True)
    video = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Program
        fields = ("id", "title", "channel", "promo_channel", "brand_name", "advertiser",
                  "descriptor", "similars", "marked", "deleted", "created_on", "created_by", "video")

    def get_similars(self, obj):
        return ""

    def get_video(self, obj):
        if obj.vendorpromo_set.all().count():
            ct = obj.vendorpromo_set.all().filter(video__isnull=False).first()
            if ct:
                return ct.video.all().first().file
            else:
                return ""
        else:
            return ""


class CommercialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Commercial
        fields = "__all__"
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}


class SoftDetailCommercialSerializer(serializers.ModelSerializer):
    title = TitleSerializer(read_only=True)
    brand_name = DetailBrandNameSerializer(read_only=True)
    advertiser = DetailAdvertiserSerializer(read_only=True)
    descriptor = DescriptorSerializer(read_only=True)

    class Meta:
        model = Commercial
        fields = ("id", "title", "brand_name", "advertiser", "descriptor")


class DetailCommercialSerializer(serializers.ModelSerializer):
    title = DetailBrandNameSerializer(read_only=True, source='brand_name')
    brand_name = DetailBrandNameSerializer(read_only=True)
    advertiser = DetailAdvertiserSerializer(read_only=True)
    descriptor = DescriptorSerializer(read_only=True)
    video = serializers.SerializerMethodField(read_only=True)
    similars = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Commercial
        fields = ("id", "title", "brand_name", "advertiser", "descriptor", "video", "similars", "marked", "deleted",
                  "created_on", "created_by")

    def get_video(self, obj):
        if obj.vendorcommercial_set.all().count():
            ct = obj.vendorcommercial_set.all().filter(video__isnull=False).first()
            if ct:
                return ct.video.all().first().file
            else:
                return ""
        else:
            return ""

    def get_similars(self, obj):
        return ""


class TDetailCommercialSerializer(serializers.ModelSerializer):
    title = TitleSerializer(read_only=True)
    brand_name = DetailBrandNameSerializer(read_only=True)
    advertiser = DetailAdvertiserSerializer(read_only=True)
    descriptor = DescriptorSerializer(read_only=True)
    video = serializers.SerializerMethodField(read_only=True)
    similars = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Commercial
        fields = ("id", "title", "brand_name", "advertiser", "descriptor", "video", "similars")

    def get_video(self, obj):
        ct = CommercialTag.objects.all().filter(brand_title=obj.brand_name.name,descriptor=obj.descriptor.text).first()
        if ct:
            return ct.video
        else:
            return ""

    def get_similars(self, obj):
        c = Commercial.objects.filter(brand_name__name__trigram_similar=obj.brand_name.name, descriptor__text__trigram_similar=obj.descriptor.text).exclude(id=obj.id)[0:5]
        ser = SoftDetailCommercialSerializer(c, many=True)
        return ser.data


class BarcRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        if isinstance(value, Program):
            serializer = DetailProgramSerializer(value)
        elif isinstance(value, Promo):
            serializer = DetailPromoSerializer(value)
        elif isinstance(value, Commercial):
            serializer = DetailCommercialSerializer(value)
        elif isinstance(value, Song):
            serializer = DetailSongSerializer(value)
        else:
            raise Exception('Unexpected type of tagged object')

        return serializer.data


class PlayoutTagSerializer(serializers.ModelSerializer):
    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )
    user_comments = RelatedCommentSerializer(read_only=True, many=True)
    time = serializers.SerializerMethodField(read_only=True)
    stopTime = serializers.SerializerMethodField(read_only=True)
    tagged_object = BarcRelatedField(read_only=True)
    clip_start_time = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PlayoutTag
        fields = ("id", "tag", "video", "frame_in", "frame_out", "comment", "is_approved", "user_comments",
                  "poster", "content_type", "tagged_object", "is_original", "created_on", "modified_on", "time",
                  "stopTime", "clip_start_time")

    def get_time(self, obj):
        return obj.frame_in/25

    def get_stopTime(self, obj):
        return obj.frame_out/25

    def get_clip_start_time(self, obj):
        vid = obj.video
        c_clip = ChannelClip.objects.filter(video=vid).first()
        if c_clip:
            return c_clip.start_time
        else:
            return None


class SongPlayoutTagSerializer(serializers.ModelSerializer):

    start_time = serializers.SerializerMethodField(read_only=True)
    end_time = serializers.SerializerMethodField(read_only=True)
    tagged_object = BarcRelatedField(read_only=True)
    clip_start_time = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PlayoutTag
        fields = ("id", "tag", "video", "frame_in", "frame_out", "comment", "is_approved", "user_comments",
                  "poster", "content_type", "tagged_object", "is_original", "created_on", "modified_on", "time",
                  "stopTime", "clip_start_time")

    def get_time(self, obj):
        return obj.frame_in/25

    def get_stopTime(self, obj):
        return obj.frame_out/25

    def get_clip_start_time(self, obj):
        vid = obj.video
        c_clip = ChannelClip.objects.filter(video=vid).first()
        if c_clip:
            return c_clip.start_time
        else:
            return None


class CreatePlayoutTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayoutTag
        fields = "__all__"
        extra_kwargs = {'created_by': {'default': serializers.CurrentUserDefault(), "read_only": True}}


class BarcTagSerializer(serializers.ModelSerializer):
    poster = VersatileImageFieldSerializer(
        sizes='video_poster',
        allow_null=True
    )
    user_comments = RelatedCommentSerializer(read_only=True, many=True)
    time = serializers.SerializerMethodField(read_only=True)
    stopTime = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BarcTag
        fields = ("id", "tag", "video", "frame_in", "frame_out", "comment", "is_approved", "user_comments",
                  "poster", "content_type", "title", "content_language_code", "telecast_start_time",
                  "telecast_end_time",
                  "telecast_duration", "promo_sponsor_name", "is_original", "created_on", "modified_on", "advertiser",
                  "advertiser_group", "brand_category", "brand_sector", "brand_title", "descriptor", "program_genre",
                  "program_theme", "time", "stopTime")

    def get_time(self, obj):
        return obj.frame_in/25

    def get_stopTime(self, obj):
        return obj.frame_out/25


class CreateBarcTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = BarcTag
        fields = "__all__"


class SpriteTagSerializer(serializers.ModelSerializer):
    clip_start_time = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SpriteTag
        fields = ("id", "time", "url", "video", "clip_start_time")

    def get_clip_start_time(self, obj):
        vid = obj.video
        c_clip = ChannelClip.objects.filter(video=vid).first()
        if c_clip:
            return c_clip.start_time
        else:
            return None

class PromoCategorySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PromoCategory
        fields = "__all__"

class ManualTagQCStatusSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ManualTagQCStatus
        fields = "__all__"

class MasterReportGenSerializer(serializers.ModelSerializer):

    class Meta:
        model = MasterReportGen
        fields = "__all__"


