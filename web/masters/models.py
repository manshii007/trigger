from django.db import models
import uuid
from tags.models import Channel
from users.models import User
from django.contrib.postgres.fields import ArrayField
from tags.models import Commercial, Program, Promo
from tags.models import ContentLanguage as Clang
from tags.models import ProgramGenre as Pgenre
from tags.models import PromoCategory as Pcat
from video.models import Video
from django_bulk_update.manager import BulkUpdateManager


class Vendor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, null=False, blank=False)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        permissions = (("view_vendor", "Can view vendor"),)


class VendorReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.URLField(null=False, blank=False)
    vendor = models.ForeignKey(Vendor, null=False, blank=False)
    date = models.DateField(null=False, blank=False)
    channel = models.ForeignKey(Channel, null=False, blank=False)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        permissions = (("view_vendorreport", "Can view vendor report"),)


class VendorMaster(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.URLField(null=False, blank=False)
    vendor = models.ForeignKey(Vendor, null=False, blank=False)
    date = models.DateField(null=False, blank=False)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        permissions = (("view_vendormaster", "Can view vendor master"),)


class MasterReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.URLField(null=False, blank=False)
    date = models.DateField(null=False, blank=False)
    channel = models.ForeignKey(Channel, null=False, blank=False)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    eta = models.IntegerField(default=0)
    status = models.CharField(null=True, max_length=128, default="NPR")

    class Meta:
        permissions = (("view_masterreport", "Can view master report"),)


class SuperMaster(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.URLField(null=False, blank=False)
    date = models.DateField(null=False, blank=False)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        permissions = (("view_masterreport", "Can view master report"),)


class WeeklyReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    master_file = models.URLField(null=False, blank=False)
    report_file = models.URLField(null=False, blank=False)
    week = models.IntegerField(null=False, blank=False)

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        permissions = (("view_weeklyreport", "Can view weekly report"),)


class ProgramTheme(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    code = models.BigAutoField(primary_key=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class ProgramGenre(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    code = models.BigAutoField(primary_key=True)
    program_theme = models.ForeignKey(ProgramTheme, null=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class ContentLanguage(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    code = models.BigAutoField(primary_key=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class ProductionHouse(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    code = models.BigAutoField(primary_key=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class AdvertiserGroup(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    code = models.BigAutoField(primary_key=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class Advertiser(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    code = models.BigAutoField(primary_key=True)
    advertiser_group = models.ForeignKey(AdvertiserGroup, null=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class BrandSector(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    code = models.BigAutoField(primary_key=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class BrandCategory(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    code = models.BigAutoField(primary_key=True)
    brand_sector = models.ForeignKey(BrandSector, null=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class BrandName(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    code = models.BigAutoField(primary_key=True)
    brand_category = models.ForeignKey(BrandCategory, null=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class Title(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, db_index=True)
    code = models.BigAutoField(primary_key=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class Descriptor(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    text = models.CharField(max_length=128, db_index=True)
    code = models.BigAutoField(primary_key=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.text


class PromoType(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, unique=True)
    code = models.BigAutoField(primary_key=True)
    abbr = models.CharField(max_length=5, null=False, blank=False)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class PromoCategory(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    name = models.CharField(max_length=128, unique=True)
    code = models.BigAutoField(primary_key=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name


class SuperPromo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.ForeignKey(Title, null=True)
    channel = models.ForeignKey(Channel, related_name="broadcasted_super_promo", null=True)
    promo_channel = models.ForeignKey(Channel, related_name="super_promo", null=True)
    brand_name = models.ForeignKey(BrandName)
    advertiser = models.ForeignKey(Advertiser, null=True)
    descriptor = models.ForeignKey(Descriptor, null=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.brand_name.name


class SuperProgram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.ForeignKey(Title)
    language = models.ForeignKey(ContentLanguage, null=True)
    prod_house = models.ForeignKey(ProductionHouse, null=True)
    program_genre = models.ForeignKey(ProgramGenre, null=True)
    channel = models.ForeignKey(Channel)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.title.name


class SuperCommercial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.ForeignKey(Title)
    brand_name = models.ForeignKey(BrandName, null=True)
    descriptor = models.ForeignKey(Descriptor, null=True)
    advertiser = models.ForeignKey(Advertiser, null=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True)

    def __str__(self):
        return self.title.name


class VendorPromo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)

    title = models.CharField(max_length=128, db_index=True)
    title_code = models.CharField(max_length=128, db_index=True)
    brand_name = models.CharField(max_length=128, db_index=True)
    brand_name_code = models.CharField(max_length=128, db_index=True)
    brand_sector = models.CharField(max_length=128, db_index=True)
    brand_sector_code = models.CharField(max_length=128)
    brand_category = models.CharField(max_length=128, db_index=True)
    brand_category_code = models.CharField(max_length=128)
    advertiser = models.CharField(max_length=128, null=True, db_index=True)
    advertiser_code = models.CharField(max_length=128, null=True)
    advertiser_group = models.CharField(max_length=128, null=True, db_index=True)
    advertiser_group_code = models.CharField(max_length=128, null=True)
    descriptor = models.CharField(max_length=128, null=True, db_index=True)
    descriptor_code = models.CharField(max_length=128, null=True)

    # mapping
    super_promo = models.ForeignKey(SuperPromo, null=True, blank=True, on_delete=models.SET_NULL)
    promo = models.ForeignKey(Promo, null=True, blank=True, on_delete=models.SET_NULL)
    is_mapped = models.BooleanField(default=False)
    similars = models.ManyToManyField("self", blank=True)

    video = models.ManyToManyField(Video)

    durations = ArrayField(
        models.IntegerField(blank=True),
        size=12,
        null=True
    )

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.brand_name

    objects = BulkUpdateManager()


class VendorProgram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)

    title = models.CharField(max_length=128, null=True, db_index=True)
    title_code = models.CharField(max_length=128, null=True, db_index=True)
    language = models.CharField(max_length=128, null=True, db_index=True)
    language_code = models.CharField(max_length=128, null=True)
    prod_house = models.CharField(max_length=128, null=True, db_index=True)
    prod_house_code = models.CharField(max_length=128, null=True)
    program_genre = models.CharField(max_length=128, null=True, db_index=True)
    program_genre_code = models.CharField(max_length=128, null=True, db_index=True)
    program_theme = models.CharField(max_length=128, null=True, db_index=True)
    program_theme_code = models.CharField(max_length=128, null=True, db_index=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, null=True, db_index=True)

    # mapping
    super_program = models.ForeignKey(SuperProgram, null=True, blank=True, on_delete=models.SET_NULL)
    program = models.ForeignKey(Program, null=True, blank=True, on_delete=models.SET_NULL)
    is_mapped = models.BooleanField(default=False)
    similars = models.ManyToManyField("self", blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.title

    objects = BulkUpdateManager()


class VendorCommercial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)

    title = models.CharField(max_length=128, db_index=True)
    title_code = models.CharField(max_length=128, db_index=True)
    brand_name = models.CharField(max_length=128, db_index=True)
    brand_name_code = models.CharField(max_length=128, db_index=True)
    brand_sector = models.CharField(max_length=128, db_index=True, null=True)
    brand_sector_code = models.CharField(max_length=128)
    brand_category = models.CharField(max_length=128, db_index=True, null=True)
    brand_category_code = models.CharField(max_length=128)
    advertiser = models.CharField(max_length=128, db_index=True, null=True)
    advertiser_code = models.CharField(max_length=128)
    advertiser_group = models.CharField(max_length=128, db_index=True, null=True)
    advertiser_group_code = models.CharField(max_length=128)
    descriptor = models.CharField(max_length=128, db_index=True, null=True)
    descriptor_code = models.CharField(max_length=128, db_index=True, null=True)

    # mapping
    super_commercial = models.ForeignKey(SuperCommercial, null=True, blank=True, on_delete=models.SET_NULL)
    commercial = models.ForeignKey(Commercial, null=True, blank=True, on_delete=models.SET_NULL)
    is_mapped = models.BooleanField(default=False)
    similars = models.ManyToManyField("self", blank=True)

    video = models.ManyToManyField(Video)

    durations = ArrayField(
            models.IntegerField(blank=True),
            size=12,
            null=True
        )

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.title

    objects = BulkUpdateManager()


class VendorChannel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)

    name = models.CharField(max_length=128, db_index=True)
    code = models.CharField(max_length=128, db_index=True)
    network_name = models.CharField(max_length=128, db_index=True, null=True)
    network_name_code = models.CharField(max_length=128, null=True)
    language = models.CharField(max_length=128, db_index=True, null=True)
    language_code = models.CharField(max_length=128, db_index=True, null=True)
    region = models.CharField(max_length=128, db_index=True, null=True)
    region_code = models.CharField(max_length=128, db_index=True, null=True)
    genre = models.CharField(max_length=128, db_index=True, null=True)
    genre_code = models.CharField(max_length=128, db_index=True, null=True)

    # mapping
    channel = models.ForeignKey(Channel, null=True, blank=True, on_delete=models.SET_NULL)
    is_mapped = models.BooleanField(default=False)
    similars = models.ManyToManyField("self", blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class VendorContentLanguage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)

    name = models.CharField(max_length=128, db_index=True)
    code = models.CharField(max_length=128, db_index=True)

    # mapping
    content_language = models.ForeignKey(Clang, null=True, blank=True, on_delete=models.SET_NULL)
    is_mapped = models.BooleanField(default=False)
    similars = models.ManyToManyField("self", blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class VendorProgramGenre(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)

    name = models.CharField(max_length=128, db_index=True)
    code = models.CharField(max_length=128, db_index=True)
    program_theme = models.CharField(max_length=128, db_index=True)
    program_theme_code = models.CharField(max_length=128, db_index=True)

    # mapping
    program_genre = models.ForeignKey(Pgenre, null=True, blank=True, on_delete=models.SET_NULL)
    is_mapped = models.BooleanField(default=False)
    similars = models.ManyToManyField("self", blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class VendorPromoCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)

    name = models.CharField(max_length=128, db_index=True)
    code = models.CharField(max_length=128, db_index=True)

    # mapping
    promo_type = models.ForeignKey(Pcat, null=True, blank=True, on_delete=models.SET_NULL)
    is_mapped = models.BooleanField(default=False)
    similars = models.ManyToManyField("self", blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class VendorMasterComparison(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=128,null=False)
    eta = models.FloatField(default=0)
    step = models.IntegerField(default=1)
    date = models.DateField(null=True, blank=True)

    # basic modification tracker
    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return "{}_{}".format(self.status, self.eta)


class VendorReportProgram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, null=False, blank=False)
    date = models.DateField(null=False, blank=False)
    channel = models.ForeignKey(Channel, null=False, blank=False)
    program = models.ForeignKey(VendorProgram, null=True)

    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.IntegerField()

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        permissions = (("view_vendorreportprogram", "Can view vendor report program"),)


class VendorReportPromo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, null=False, blank=False)
    date = models.DateField(null=False, blank=False)
    channel = models.ForeignKey(Channel, null=False, blank=False)
    promo = models.ForeignKey(VendorPromo, null=True)

    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.IntegerField()

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        permissions = (("view_vendorreportpromo", "Can view vendor report promo"),)


class VendorReportCommercial(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey(Vendor, null=False, blank=False)
    date = models.DateField(null=False, blank=False)
    channel = models.ForeignKey(Channel, null=False, blank=False)
    commercial = models.ForeignKey(VendorCommercial, null=True)

    start_time = models.TimeField()
    end_time = models.TimeField()
    duration = models.IntegerField()

    created_on = models.DateTimeField(auto_now_add=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        permissions = (("view_vendorreportcommercial", "Can view vendor report commercial"),)