from rest_framework import serializers
from .models import VendorReport, VendorMaster, Vendor, SuperMaster, MasterReport, VendorCommercial, VendorProgram, \
    VendorPromo, VendorMasterComparison, SuperProgram, SuperCommercial, SuperPromo, VendorReportPromo, \
    VendorReportCommercial, VendorReportProgram, WeeklyReport, VendorChannel, VendorContentLanguage, \
    VendorProgramGenre, VendorPromoCategory
from django.db.models import Count
from tags.serializers import ChannelSerializer


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"


class DetailVendorReportSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = VendorReport
        fields = ("id", "vendor", "date", "channel", "file", "created_on")


class VendorReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorReport
        fields = "__all__"


class WeeklyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyReport
        fields = "__all__"


class VendorMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorMaster
        fields = "__all__"


class MasterReportSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = MasterReport
        fields = ("channel", "eta", "status", "file", "date", "id")


class SuperMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperMaster
        fields = "__all__"


class VendorCommercialSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorCommercial
        exclude = ['similars', 'durations', 'title_code', 'brand_name_code', 'brand_sector_code',
                   'brand_category_code', 'advertiser_code', 'advertiser_group_code', 'descriptor_code', 'video']


class DetailVendorCommercialSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    durations = serializers.SerializerMethodField(read_only=True)
    video = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VendorCommercial
        fields = ("id", "title", "title_code", "brand_name", "brand_name_code", "brand_sector", "brand_sector_code",
                  "brand_category", "brand_category_code",
                  "advertiser", "advertiser_code",
                  "advertiser_group", "advertiser_group_code",
                  "descriptor", "descriptor_code",
                  "created_on",
                  "durations",
                  "video",
                  "vendor")

    def get_video(self, obj):
        vids = obj.video.all().first()
        if vids:
            return vids.file
        else:
            return ""

    def get_durations(self, instance):
        vc = VendorReportCommercial.objects.filter(commercial=instance).values("duration").order_by("duration").annotate(Count("id"))
        dur = []
        for v in vc:
            dur.append(v['duration'])
        return dur


class DetailSimilarVendorCommercialSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    similars = DetailVendorCommercialSerializer(many=True, read_only=True)
    durations = serializers.SerializerMethodField(read_only=True)
    video = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VendorCommercial
        fields = ("id", "title", "title_code", "brand_name", "brand_name_code", "brand_sector", "brand_sector_code",
                  "brand_category", "brand_category_code",
                  "advertiser", "advertiser_code",
                  "advertiser_group", "advertiser_group_code",
                  "descriptor", "descriptor_code",
                  "created_on",
                  "durations",
                  "similars",
                  "video",
                  "vendor")

    def get_video(self, obj):
        vids = obj.video.all().first()
        if vids:
            return vids.file
        else:
            return ""

    def get_durations(self, instance):
        vc = VendorReportCommercial.objects.filter(commercial=instance).values("duration").order_by("duration").annotate(Count("id"))
        dur = []
        for v in vc:
            dur.append(v['duration'])
        return dur


class VendorPromoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorPromo
        exclude = ['similars', 'durations', 'title_code', 'brand_name_code', 'brand_sector_code',
                   'brand_category_code', 'advertiser_code', 'advertiser_group_code', 'descriptor_code', 'video']


class DetailVendorPromoSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    durations = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VendorPromo
        fields = ("id", "title", "title_code", "brand_name", "brand_name_code", "brand_sector", "brand_sector_code",
                  "brand_category", "brand_category_code",
                  "advertiser", "advertiser_code",
                  "advertiser_group", "advertiser_group_code",
                  "descriptor", "descriptor_code",
                  "created_on",
                  "durations",
                  "vendor")

    def get_durations(self, instance):
        vc = VendorReportPromo.objects.filter(promo=instance).values("duration").order_by("duration").annotate(Count("id"))
        dur = []
        for v in vc:
            dur.append(v['duration'])
        return dur


class DetailSimilarVendorPromoSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    similars = DetailVendorPromoSerializer(many=True, read_only=True)
    durations = serializers.SerializerMethodField(read_only=True)
    video = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = VendorPromo
        fields = ("id", "title", "title_code", "brand_name", "brand_name_code", "brand_sector", "brand_sector_code",
                  "brand_category", "brand_category_code",
                  "advertiser", "advertiser_code",
                  "advertiser_group", "advertiser_group_code",
                  "descriptor", "descriptor_code",
                  "created_on",
                  "durations",
                  "similars",
                  "video",
                  "vendor")

    def get_video(self, obj):
        vids = obj.video.all().first()
        if vids:
            return vids.file
        else:
            return ""

    def get_durations(self, instance):
        vc = VendorReportPromo.objects.filter(promo=instance).values("duration").order_by("duration").annotate(Count("id"))
        dur = []
        for v in vc:
            dur.append(v['duration'])
        return dur


class VendorProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProgram
        exclude = ['similars', 'title_code']


class DetailVendorProgramSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    channel = ChannelSerializer(read_only=True)

    class Meta:
        model = VendorProgram
        fields = ("id", "title", "title_code", "language", "language_code", "program_genre", "program_genre_code",
                  "program_theme", "program_theme_code", "prod_house", "prod_house_code", "channel",
                  "created_on",
                  "vendor")


class SuperCommercialSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperCommercial
        fields = "__all__"


class DetailSuperCommercialSerializer(serializers.ModelSerializer):
    Super = VendorSerializer(read_only=True)

    class Meta:
        model = SuperCommercial
        fields = ("id", "title", "title_code", "brand_name", "brand_name_code", "brand_sector", "brand_sector_code",
                  "brand_category", "brand_category_code",
                  "advertiser", "advertiser_code",
                  "advertiser_group", "advertiser_group_code",
                  "descriptor", "descriptor_code",
                  "created_on",
                  "vendor")


class SuperPromoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperPromo
        fields = "__all__"


class DetailSuperPromoSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)

    class Meta:
        model = SuperPromo
        fields = ("id", "title", "title_code", "brand_name", "brand_name_code", "brand_sector", "brand_sector_code",
                  "brand_category", "brand_category_code",
                  "advertiser", "advertiser_code",
                  "advertiser_group", "advertiser_group_code",
                  "descriptor", "descriptor_code",
                  "created_on",
                  "vendor")


class SuperProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuperProgram
        fields = "__all__"


class DetailSuperProgramSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)

    class Meta:
        model = SuperProgram
        fields = ("id", "title", "title_code", "language", "language_code", "program_genre", "program_genre_code",
                  "program_theme", "program_theme_code", "prod_house", "prod_house_code",
                  "created_on",
                  "vendor")


class SimilarVendorCommercialSerializer(serializers.ModelSerializer):
    similars = serializers.SerializerMethodField(read_only=True)
    vendor = VendorSerializer(read_only=True)

    class Meta:
        model = VendorCommercial
        fields = ("id", "title", "title_code", "brand_name", "brand_sector", "brand_category", "brand_name_code", "advertiser", "advertiser_code",
                  "descriptor", "descriptor_code", "similars", "vendor")

    def get_similars(self, obj):
        c = VendorCommercial.objects.all().exclude(descriptor=obj.descriptor).exclude(id=obj.id)\
            .filter(title=obj.title, descriptor__trigram_similar=obj.descriptor)

        ser = DetailVendorCommercialSerializer(c, many=True)
        return ser.data


class VendorCountSerializer(serializers.Serializer):
    count = serializers.IntegerField(read_only=True)
    vendor__name = serializers.CharField(read_only=True)


class VendorReportCountSerializer(serializers.Serializer):
    id__count = serializers.IntegerField(read_only=True)
    channel__name = serializers.CharField(read_only=True)
    duration = serializers.IntegerField(read_only=True)


class VendorMasterComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorMasterComparison
        # fields = "__all__"
        exclude = ("created_by",)


class CountSerializer(serializers.Serializer):
    vendor__name = serializers.CharField(read_only=True)
    count = serializers.IntegerField(read_only=True)


class VendorContentLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorContentLanguage
        fields = "__all__"


class DetailVendorContentLanguageSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)

    class Meta:
        model = VendorContentLanguage
        fields = "__all__"


class DetailSimilarVendorContentLanguageSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    similars = DetailVendorContentLanguageSerializer(many=True, read_only=True)

    class Meta:
        model = VendorContentLanguage
        fields = "__all__"


class VendorChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorChannel
        fields = "__all__"


class DetailVendorChannelSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)

    class Meta:
        model = VendorChannel
        fields = "__all__"


class DetailSimilarVendorChannelSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    similars = DetailVendorChannelSerializer(many=True, read_only=True)

    class Meta:
        model = VendorChannel
        fields = "__all__"


class VendorPromoCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorPromoCategory
        fields = "__all__"


class DetailVendorPromoCategorySerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)

    class Meta:
        model = VendorPromoCategory
        fields = "__all__"


class DetailSimilarVendorPromoCategorySerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    similars = DetailVendorPromoCategorySerializer(many=True, read_only=True)

    class Meta:
        model = VendorPromoCategory
        fields = "__all__"


class VendorProgramGenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorProgramGenre
        fields = "__all__"


class DetailVendorProgramGenreSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)

    class Meta:
        model = VendorProgramGenre
        fields = "__all__"


class DetailSimilarVendorProgramGenreSerializer(serializers.ModelSerializer):
    vendor = VendorSerializer(read_only=True)
    similars = DetailVendorProgramGenreSerializer(many=True, read_only=True)

    class Meta:
        model = VendorProgramGenre
        fields = "__all__"

