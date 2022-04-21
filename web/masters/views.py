from django.shortcuts import render
from .serializers import (
    VendorMasterSerializer,
    VendorReportSerializer,
    VendorSerializer,
    SuperMasterSerializer,
    MasterReportSerializer,
    DetailVendorReportSerializer,
    VendorCommercialSerializer,
    DetailVendorCommercialSerializer,
    SimilarVendorCommercialSerializer,
    VendorCountSerializer,
    VendorPromoSerializer,
    DetailVendorProgramSerializer,
    DetailVendorPromoSerializer,
    VendorProgramSerializer,
    SuperCommercialSerializer,
    DetailSuperCommercialSerializer,
    SimilarVendorCommercialSerializer,
    SuperPromoSerializer,
    DetailSuperProgramSerializer,
    DetailSuperPromoSerializer,
    SuperProgramSerializer,
    VendorMasterComparisonSerializer,
    VendorReportCountSerializer,
    DetailSimilarVendorCommercialSerializer,
    DetailSimilarVendorPromoSerializer,
    CountSerializer,
    WeeklyReportSerializer,
    VendorChannelSerializer,
    VendorContentLanguageSerializer,
    VendorPromoCategorySerializer,
    VendorProgramGenreSerializer,
    DetailSimilarVendorChannelSerializer,
    DetailSimilarVendorContentLanguageSerializer,
    DetailSimilarVendorProgramGenreSerializer,
    DetailSimilarVendorPromoCategorySerializer,
    DetailVendorChannelSerializer,
    DetailVendorContentLanguageSerializer,
    DetailVendorProgramGenreSerializer,
    DetailVendorPromoCategorySerializer
)
from .models import (
    VendorMaster,
    VendorReport,
    Vendor,
    SuperMaster,
    MasterReport,
    VendorCommercial,
    VendorPromo,
    VendorProgram,
    SuperCommercial,
    SuperPromo,
    SuperProgram,
    VendorMasterComparison,
    VendorReportCommercial,
    VendorReportPromo,
    WeeklyReport,
    VendorPromoCategory,
    VendorContentLanguage,
    VendorChannel,
    VendorProgramGenre
)
from django.core.mail import send_mail
from tags.models import (
    BrandName,
    BrandCategory,
    BrandSector,
    ContentLanguage,
    ProgramGenre,
    ProgramTheme,
    PromoCategory,
    PromoType,
    Descriptor,
    Advertiser,
    AdvertiserGroup,
    ProductionHouse,
    Title,
    Promo,
    Program,
    Commercial,
    Channel,
    ChannelGenre,
    ChannelNetwork,
    Region,
)
from django.db.models import Count, Sum
from django.db import IntegrityError
from rest_framework import status
import datetime
from django.db.models.functions import Cast
from django.db.models.fields import DateField
from rest_framework_tracking.mixins import LoggingMixin
from rest_framework import viewsets, permissions, response, filters
import django_filters
from rest_framework.decorators import list_route, detail_route
import math
from .tasks import initial_master, similar_commercial, similar_promo, accept_commercial, accept_program, accept_promo, \
    load_masters, load_durs, accept_channel, accept_content_language, accept_program_genre, accept_promo_category, zip_finalmasters, zip_finalreports, generate_custom_reports


def get_pending():
    c = VendorPromo.objects.filter(is_mapped=False).count() + VendorProgram.objects.filter(
            is_mapped=False).count() + VendorCommercial.objects.filter(is_mapped=False).count() + \
        VendorPromoCategory.objects.filter(is_mapped=False).count() + \
        VendorProgramGenre.objects.filter(is_mapped=False).count() + \
        VendorContentLanguage.objects.filter(is_mapped=False).count() + \
        VendorChannel.objects.filter(is_mapped=False).count()

    return c


class VendorMasterViewSet(viewsets.ModelViewSet):
    queryset = VendorMaster.objects.all()
    serializer_class = VendorMasterSerializer
    permission_classes = (permissions.IsAuthenticated,)


class VendorReportViewSet(viewsets.ModelViewSet):
    queryset = VendorReport.objects.all()
    serializer_class = VendorReportSerializer
    permission_classes = (permissions.IsAuthenticated,)

    action_serializer_classes = {
        "list": DetailVendorReportSerializer,
        "retrieve": DetailVendorReportSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(VendorReportViewSet, self).get_serializer_class()


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @list_route(methods=['get'])
    def start_load(self, request):
        search = request.query_params.get("date", "")
        vendors = request.query_params.get("vendors", "")
        load_masters.delay(search,vendors)

    @list_route(methods=['get'])
    def start_durload(self, request):
        search = request.query_params.get("date", "")
        vendors = request.query_params.get("vendors", "")
        load_durs.delay(search, vendors)


class SuperMasterViewSet(viewsets.ModelViewSet):
    queryset = SuperMaster.objects.all().order_by('-date')
    serializer_class = SuperMasterSerializer
    permission_classes = (permissions.IsAuthenticated,)


class MasterReportViewSet(viewsets.ModelViewSet):
    queryset = MasterReport.objects.all()
    serializer_class = MasterReportSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, pk=None):
        status = request.query_params.get("status", "")
        date = request.query_params.get("date", "")
        channel = request.query_params.get("channel", "")
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset().filter(status__icontains=status)
        if channel:
            qs=qs.filter(channel__name__icontains=channel)
        if date:
            qs=qs.filter(date=date)

        ser = MasterReportSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        status_data_t = qs.values("status").annotate(Count('id'))
        status_data = []
        for s in status_data_t:
            status_data.append({"status": s['status'], "count": s['id__count']})
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(
            data={"results": ser.data, "count": count, "page": page,
                  "total_pages": total_pages,
                  "status_data": status_data,
                  "page_size": page_size, "eta": "22"})

    @list_route(methods=['get'])
    def initiate_processing(self, request):
        send_mail("SuperMaster Processing Status - Started for TAM, PFT",
                  "Hi Users, The Master processing for PFT, TAM is initiated", "support@tessact.com",
                  ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
                   "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])
        return response.Response(data={'msg': "success"})

    @list_route(methods=['get'])
    def generate_custom_reports(self, request):
        send_mail("SuperMaster Processing Status - Custom Report Generation Started",
                  "Hi Users, The Custom Report Generation is initiated", "support@tessact.com",
                  ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
                   "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])
        date = request.query_params.get("date",None)
        headers = request.query_params.get("fields",None)
        channels = request.query_params.get("channel",None)
        if headers and date:
            generate_custom_reports.delay(date,headers.split(","))
        return response.Response(data={'msg': "success"})

    @list_route(methods=['get'])
    def initiate_completion(self, request):
        c = get_pending()
        send_mail("SuperMaster Processing Status - Completed for TAM, PFT",
                  "Hi Users, The Master processing for PFT, TAM is completed. Please start your merging activity. We have a total of {} unique tags today".format(c),
                  "support@tessact.com",
                  ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
                   "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])
        return response.Response(data={'msg': "success"})

    @list_route(methods=['get'])
    def zip(self, request):
        date = request.query_params.get("date", "")
        dobj = datetime.datetime.strptime(date, '%Y%m%d')
        ndate = dobj.strftime('%Y-%m-%d')
        zip_finalmasters.delay(date)
        zip_finalreports.delay(date)

    @list_route(methods=['get'])
    def drop_mail(self, request):
        date = request.query_params.get("date", "")
        dobj = datetime.datetime.strptime(date, '%Y%m%d')
        ndate = dobj.strftime('%Y-%m-%d')
        send_mail("SuperMaster Processing Status - Report Generation Completed for TAM, PFT",
                  "Hi Users, The Master Report Generation for PFT is completed. please find the changelog at "
                  "https://barc-playout-files.s3.ap-south-1.amazonaws.com/supermaster/{}/BARC_MasterReportsXmls_{}.zip and "
                  "master reports at "
                  "https://barc-playout-files.s3.ap-south-1.amazonaws.com/supermaster/{}/BARC_ChannelReportsXmls_{}.zip . "
                  "You can download the files by clicking on the links".format(ndate, date, ndate, date),
                  "support@tessact.com",
                  ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
                   "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in", "operations@barcindia.co.in"])
        return response.Response(data={'msg': "success"})

    @list_route(methods=['get'])
    def initiate_report(self, request):
        date = request.query_params.get("date","")
        initial_master.delay(date)
        send_mail("SuperMaster Processing Status - Report Generation is initiated for TAM, PFT",
                  "Hi Users, The Master Report Generation for PFT, TAM is initiated.", "support@tessact.com",
                  ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
                   "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])
        # #
        # send_mail("SuperMaster Processing Status - Report Generation Completed for TAM, PFT",
        #           "Hi Users, The Master Report Generation for PFT, TAM is completed. please find the supermasters at "
        #           "https://barc-playout-files.s3.ap-south-1.amazonaws.com/supermaster/2019-07-20/BARC_MasterReportsXmls_20190720.zip and "
        #           "master reports at "
        #           "https://barc-playout-files.s3.ap-south-1.amazonaws.com/supermaster/2019-07-20/BARC_ChannelReportsXmls_20190720.zip . "
        #           "You can download the files by clicking on the links",
        #           "support@tessact.com",
        #           ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
        #            "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in", "operations@barcindia.co.in"])

        #
        # send_mail("SuperMaster Processing Status - Completed for TAM, PFT",
        #           "Hi Users, The Master processing for PFT, TAM is completed. Please start your merging activity. We have a total of 1274 unique tags today", "support@tessact.com",
        #           ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
        #            "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])
        #
        # send_mail("SuperMaster Processing Status - Started for TAM, PFT",
        #           "Hi Users, The Master processing for PFT, TAM is initiated", "support@tessact.com",
        #           ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
        #            "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])

        return response.Response(status=status.HTTP_200_OK)


class VendorCommercialViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = VendorCommercial.objects.all()
    serializer_class = VendorCommercialSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("vendor__name","title","brand_name","brand_sector","brand_category","advertiser",
                     "advertiser_group", "descriptor")
    search_fields = ("title","brand_name")
    action_serializer_classes = {
        "list": DetailVendorCommercialSerializer,
        "retrieve": DetailVendorCommercialSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(VendorCommercialViewSet, self).get_serializer_class()

    def list(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        title = request.query_params.get("title", None)
        brand_name = request.query_params.get("brand_name", None)
        brand_sector = request.query_params.get("brand_sector", None)
        brand_category = request.query_params.get("brand_category",None)
        advertiser = request.query_params.get("advertiser", None)
        advertiser_group = request.query_params.get("advertiser_group", None)
        descriptor = request.query_params.get("descriptor", None)
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor",None)
        has_dur = request.query_params.get("has_dur",False)
        commercial = request.query_params.get("commercial", None)
        page = int(request.query_params.get("page", 1))
        qs = VendorCommercial.objects.all().filter(is_mapped=True)
        if title:
            qs = qs.filter(title__icontains=title)
        if brand_sector:
            qs = qs.filter(brand_sector__icontains=brand_sector)
        if brand_name:
            qs = qs.filter(brand_name__icontains=brand_name)
        if brand_category:
            qs = qs.filter(brand_category__icontains=brand_category)
        if advertiser:
            qs = qs.filter(advertiser__icontains=advertiser)
        if advertiser_group:
            qs = qs.filter(advertiser_group__icontains=advertiser_group)
        if vendor_name:
            qs = qs.filter(vendor__name__icontains=vendor_name)
        if descriptor:
            qs = qs.filter(descriptor__icontains=descriptor)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        if has_dur:
            qs = qs.filter(vendorreportcommercial__isnull=False).distinct()
        if commercial:
            qs = qs.filter(commercial__id=commercial)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailVendorCommercialSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = Commercial.objects.all().count()
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data})

    @list_route(methods=['get'])
    def duplicates(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", "")
        brand_name = request.query_params.get("brand_name", "")
        brand_sector = request.query_params.get("brand_sector", "")
        advertiser = request.query_params.get("advertiser","")
        advertiser_group = request.query_params.get("advertiser_group","")
        descriptor = request.query_params.get("descriptor", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor","")

        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset().filter(is_mapped=False)
        if created_on:
            qs = qs.filter(created_on__date__lte=created_on)
        if title:
            qs = qs.filter(title__istartswith=title)
        if brand_sector:
            qs = qs.filter(brand_sector__istartswith=brand_sector)
        if brand_name:
            qs = qs.filter(brand_name__istartswith=brand_name)
        if advertiser:
            qs = qs.filter(advertiser__istartswith=advertiser)
        if advertiser_group:
            qs = qs.filter(advertiser_group__istartswith=advertiser_group)
        if vendor_name:
            qs = qs.filter(vendor__name__istartswith=vendor_name)
        if descriptor:
            qs=qs.filter(descriptor__istartswith=descriptor)

        qs = qs.annotate(num_similars=Count('similars')).order_by("-num_similars", "title")
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailSimilarVendorCommercialSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = Commercial.objects.all().count()
        pending = get_pending()
        if pending==0:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            date = yesterday.strftime('%Y-%m-%d')
            # initial_master.delay(date)
            # send_mail("SuperMaster Processing Status - Report Generation Started for TAM, PFT",
            #           "Hi Users, The Master Report Generation for PFT, TAM is initiated", "support@tessact.com",
            #           ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
            #            "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])

        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data, "pending": pending})

    @list_route(methods=['get'])
    def merge(self, request, pk=None):
        vendor_name = request.query_params.get("vendor", "")
        qs = self.queryset.filter(is_mapped=False, vendor__name=vendor_name)
        qs.update(is_mapped=True)
        ids = qs.values_list("id", flat=True)
        idstr = ",".join([str(x) for x in ids])
        accept_commercial.delay(idstr)
        return response.Response(data={"message": "success"})

    @list_route(methods=['get'])
    def multi_merge(self, request, pk=None):
        ids = request.query_params.get("ids", "")

        qs = self.queryset.filter(id__in=ids.split(","))
        vc = self.queryset.filter(id=ids.split(",")[0]).first()
        # try:
        brand_sector = BrandSector.objects.filter(name=vc.brand_sector).first()
        if not brand_sector:
            brand_sector = BrandSector.objects.create(name=vc.brand_sector)

        brand_category = BrandCategory.objects.filter(name=vc.brand_category, brand_sector=brand_sector).first()
        if not brand_category:
            brand_category = BrandCategory.objects.create(name=vc.brand_category, brand_sector=brand_sector)

        brand_name = BrandName.objects.filter(name=vc.brand_name, brand_category=brand_category).first()
        if not brand_name:
            brand_name = BrandName.objects.create(name=vc.brand_name, brand_category=brand_category)

        # title = Title.objects.filter(name=vc.title).first()
        # if not title:
        #     title = Title.objects.create(name=vc.title)

        advertiser_group = AdvertiserGroup.objects.filter(name=vc.advertiser_group).first()
        if not advertiser_group:
            advertiser_group = AdvertiserGroup.objects.create(name=vc.advertiser_group)

        advertiser = Advertiser.objects.filter(name=vc.advertiser, advertiser_group=advertiser_group).first()
        if not advertiser:
            advertiser = Advertiser.objects.create(name=vc.advertiser, advertiser_group=advertiser_group)

        descriptor = Descriptor.objects.filter(text=vc.descriptor).first()
        if not descriptor:
            descriptor = Descriptor.objects.create(text=vc.descriptor)

        super_commercial, c = Commercial.objects.get_or_create(title=None, brand_name=brand_name,
                                                               advertiser=advertiser,
                                                               descriptor=descriptor)
        super_commercial.created_by = self.request.user
        super_commercial.save()

        qs.update(commercial=super_commercial, is_mapped=True)
        for q in qs:
            similar_commercial.delay(q.id)
        return response.Response(data={"id": super_commercial.id}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def report_events(self, request, pk=None):
        vcr = VendorReportCommercial.objects.filter(commercial=self.get_object()).values("channel__name", "duration"). \
            order_by("channel__name", "duration").annotate(Count("id"))
        total = vcr.aggregate(total=Sum('id__count'))
        ser = VendorReportCountSerializer(vcr, many=True)
        resp = {
            "results": ser.data,
            "total": total['total']
        }
        return response.Response(data=resp)

    @list_route(methods=['get'])
    def accept(self, request, pk=None):
        ids = request.query_params.get("ids", "")
        qs = VendorCommercial.objects.all().filter(id__in=ids.split(","))
        qs.update(is_mapped=True)
        accept_commercial.delay(ids)
        return response.Response(data={"message": "success"}, status=status.HTTP_200_OK)


class VendorPromoViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = VendorPromo.objects.all()
    serializer_class = VendorPromoSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("vendor__name","title","brand_name","brand_sector","brand_category","advertiser",
                     "advertiser_group", "descriptor")
    search_fields = ("title","brand_name")
    action_serializer_classes = {
        "list": DetailVendorPromoSerializer,
        "retrieve": DetailVendorPromoSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(VendorPromoViewSet, self).get_serializer_class()

    def list(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", "")
        brand_name = request.query_params.get("brand_name", "")
        brand_sector = request.query_params.get("brand_sector", "")
        brand_category = request.query_params.get("brand_category", "")
        descriptor = request.query_params.get("descriptor", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor","")
        has_dur = request.query_params.get("has_dur",False)
        promo = request.query_params.get("promo",None)
        page = int(request.query_params.get("page", 1))

        qs = self.get_queryset()
        if title:
            qs = qs.filter(title__istartswith=title)
        if brand_sector:
            qs = qs.filter(brand_sector__istartswith=brand_sector)
        if brand_category:
            qs = qs.filter(brand_category__istartswith=brand_category)
        if brand_name:
            qs = qs.filter(brand_name__istartswith=brand_name)
        if vendor_name:
            qs = qs.filter(vendor__name__istartswith=vendor_name)
        if descriptor:
            qs=qs.filter(descriptor__istartswith=descriptor)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        if descriptor:
            qs = qs.filter(descriptor__istartswith=descriptor)
        if has_dur:
            qs = qs.filter(vendorreportpromo__isnull=False).distinct()
        if promo:
            qs = qs.filter(promo__id=promo)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailVendorPromoSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = Promo.objects.all().count()
        # supermaster_count = supermaster_count.count()
        # pending = VendorPromo.objects.filter(is_mapped=False).count() + VendorProgram.objects.filter(
        #     is_mapped=False).count() + VendorCommercial.objects.filter(is_mapped=False).count()

        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data, "pending":0})

    @list_route(methods=['get'])
    def duplicates(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", "")
        brand_name = request.query_params.get("brand_name", "")
        brand_sector = request.query_params.get("brand_sector", "")
        brand_category = request.query_params.get("brand_category", "")
        advertiser = request.query_params.get("advertiser","")
        advertiser_group = request.query_params.get("advertiser_group","")
        descriptor = request.query_params.get("descriptor", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor","")

        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset().filter(is_mapped=False)
        if created_on:
            qs = qs.filter(created_on__date__lte=created_on)
        if title:
            qs = qs.filter(title__icontains=title)
        if brand_sector:
            qs = qs.filter(brand_sector__icontains=brand_sector)
        if brand_name:
            qs = qs.filter(brand_name__icontains=brand_name)
        if brand_category:
            qs = qs.filter(brand_category__istartswith=brand_category)
        if advertiser:
            qs = qs.filter(advertiser__icontains=advertiser)
        if advertiser_group:
            qs = qs.filter(advertiser_group__icontains=advertiser_group)
        if vendor_name:
            qs = qs.filter(vendor__name__icontains=vendor_name)
        if descriptor:
            qs=qs.filter(descriptor__icontains=descriptor)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        qs = qs.annotate(num_similars=Count('similars')).order_by("-num_similars", "title")
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailSimilarVendorPromoSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = Promo.objects.all().count()
        pending = get_pending()

        # if pending==0:
        #     yesterday = datetime.date.today() - datetime.timedelta(days=1)
        #     date = yesterday.strftime('%Y-%m-%d')
        #     initial_master.delay(date)
        #     send_mail("SuperMaster Processing Status - Report Generation Started for TAM, PFT",
        #               "Hi Users, The Master Report Generation for PFT, TAM is initiated", "support@tessact.com",
        #               ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
        #                "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])

        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data, "pending":pending})

    @list_route(methods=['get'])
    def merge(self, request, pk=None):
        vendor_name = request.query_params.get("vendor", "")
        qs = self.queryset.filter(is_mapped=False, vendor__name=vendor_name)
        qs.update(is_mapped=True)
        ids = qs.values_list("id", flat=True)
        idstr = ",".join([str(x) for x in ids])
        accept_promo.delay(idstr)
        return response.Response(data={"message": "success"})

    @list_route(methods=['get'])
    def multi_merge(self, request, pk=None):
        ids = request.query_params.get("ids", "")

        qs = self.queryset.filter(id__in=ids.split(","))
        vc = self.queryset.filter(id=ids.split(",")[0]).first()
        try:
            brand_sector = BrandSector.objects.filter(name=vc.brand_sector).first()
            if not brand_sector:
                brand_sector = BrandSector.objects.create(name=vc.brand_sector)

            brand_category = BrandCategory.objects.filter(name=vc.brand_category, brand_sector=brand_sector).first()
            if not brand_category:
                brand_category = BrandCategory.objects.create(name=vc.brand_category, brand_sector=brand_sector)

            brand_name = BrandName.objects.filter(name=vc.brand_name, brand_category=brand_category).first()
            if not brand_name:
                brand_name = BrandName.objects.create(name=vc.brand_name, brand_category=brand_category)

            # title = Title.objects.filter(name=vc.title).first()
            # if not title:
            #     title = Title.objects.create(name=vc.title)

            advertiser_group = AdvertiserGroup.objects.filter(name=vc.advertiser_group).first()
            if not advertiser_group and vc.advertiser_group:
                advertiser_group = AdvertiserGroup.objects.create(name=vc.advertiser_group)

            advertiser = Advertiser.objects.filter(name=vc.advertiser, advertiser_group=advertiser_group).first()
            if not advertiser and vc.advertiser:
                advertiser = Advertiser.objects.create(name=vc.advertiser, advertiser_group=advertiser_group)

            if vc.descriptor:
                descriptor = Descriptor.objects.filter(text=vc.descriptor).first()
                if not descriptor:
                    descriptor = Descriptor.objects.create(text=vc.descriptor)
                super_promo = Promo.objects.filter(title=None, brand_name=brand_name,
                                                                  advertiser=advertiser,
                                                                  descriptor=descriptor).first()
                if not super_promo:
                    super_promo = Promo.objects.create(title=None, brand_name=brand_name,
                                                                  advertiser=advertiser,
                                                                  descriptor=descriptor)
            else:
                descriptor = None
                super_promo = Promo.objects.filter(title=None, brand_name=brand_name,
                                                   advertiser=advertiser,
                                                   descriptor=descriptor).first()
                if not super_promo:
                    super_promo = Promo.objects.create(title=None, brand_name=brand_name,
                                                       advertiser=advertiser,
                                                       descriptor=descriptor)

            super_promo.created_by = self.request.user
            super_promo.save()
            qs.update(promo=super_promo, is_mapped=True)
            for q in qs:
                similar_promo.delay(q.id)
        except KeyError:
            print(vc.id)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            print(vc.id)
            print(e)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        return response.Response(data={"id": super_promo.id}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def report_events(self, request, pk=None):
        vcr = VendorReportPromo.objects.filter(promo=self.get_object()).values("channel__name","duration"). \
            order_by("channel__name","duration").annotate(Count("id"))
        total = vcr.aggregate(total=Sum('id__count'))
        ser = VendorReportCountSerializer(vcr, many=True)
        resp = {
            "results": ser.data,
            "total": total['total']
        }
        return response.Response(data=resp)

    @list_route(methods=['get'])
    def accept(self, request, pk=None):
        ids = request.query_params.get("ids", "")
        qs = VendorPromo.objects.all().filter(id__in=ids.split(","))
        qs.update(is_mapped=True)
        accept_promo.delay(ids)
        return response.Response(data={"message": "success"}, status=status.HTTP_200_OK)


class VendorProgramViewSet(LoggingMixin, viewsets.ModelViewSet):
    queryset = VendorProgram.objects.all()
    serializer_class = VendorProgramSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("vendor__name","title","language", "program_theme", "program_genre", "prod_house")
    search_fields = ("title",)
    action_serializer_classes = {
        "list": DetailVendorProgramSerializer,
        "retrieve": DetailVendorProgramSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(VendorProgramViewSet, self).get_serializer_class()

    def list(self, request):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", "")
        language = request.query_params.get("language", "")
        program_genre = request.query_params.get("program_genre", "")
        program_theme = request.query_params.get("program_theme", "")
        prod_house = request.query_params.get("prod_house", "")
        channel = request.query_params.get("channel", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor","")
        program = request.query_params.get("program","")
        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if title:
            qs =qs.filter(title__icontains=title)
        if program_theme:
            qs =qs.filter(program_theme__icontains=program_theme)
        if program_genre:
            qs =qs.filter(program_genre__icontains=program_genre)
        if language:
            qs =qs.filter(language__icontains=language)
        if channel:
            qs =qs.filter(channel__name__icontains=channel)
        if vendor_name:
            qs =qs.filter(vendor_name__icontains=vendor_name)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        if program:
            qs = qs.filter(program__id=program)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailVendorProgramSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = Program.objects.all().count()
        pending = 0
        # if pending==0:
        #     yesterday = datetime.date.today() - datetime.timedelta(days=1)
        #     date = yesterday.strftime('%Y-%m-%d')
        #     initial_master.delay(date)
        #     send_mail("SuperMaster Processing Status - Report Generation Started for TAM, PFT",
        #               "Hi Users, The Master Report Generation for PFT, TAM is initiated", "support@tessact.com",
        #               ["aswin@tessact.com", "tanya.makhija@mdlindia.agency", "akshay.parab@mdlindia.agency",
        #                "sandhya.chotrani@barcindia.co.in", "m.premnath@barcindia.co.in"])
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count,"page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data, "pending": pending})

    @list_route(methods=['get'])
    def duplicates(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", "")
        language = request.query_params.get("language", "")
        program_genre = request.query_params.get("program_genre", "")
        program_theme = request.query_params.get("program_theme", "")
        prod_house = request.query_params.get("prod_house", "")
        created_on = request.query_params.get("created_on", None)
        channel = request.query_params.get("channel", "")
        vendor_name = request.query_params.get("vendor","")

        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset().filter(is_mapped=False)
        if created_on:
            qs = qs.filter(created_on__date__lte=created_on)
        if title:
            qs = qs.filter(title__istartswith=title)
        if program_genre:
            qs = qs.filter(program_genre__istartswith=program_genre)
        if program_theme:
            qs =qs.filter(program_theme__istartswith=program_theme)
        if language:
            qs = qs.filter(language__istartswith=language)
        if prod_house:
            qs = qs.filter(prod_house__istartswith=prod_house)
        if channel:
            qs = qs.filter(channel__name__istartswith=channel)
        if vendor_name:
            qs = qs.filter(vendor__name__istartswith=vendor_name)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        qs = qs.order_by("title")
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailVendorProgramSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)

        supermaster_count = Program.objects.all().count()
        pending = get_pending()
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count,"page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data, "pending":pending})

    @list_route(methods=['get'])
    def merge(self, request, pk=None):
        vendor_name = request.query_params.get("vendor", "")
        qs = self.queryset.filter(is_mapped=False, vendor__name=vendor_name)
        qs.update(is_mapped=True)
        ids = qs.values_list("id", flat=True)
        idstr = ",".join([str(x) for x in ids])
        accept_program.delay(idstr)
        return response.Response(data={"message": "success"})

    @list_route(methods=['get'])
    def multi_merge(self, request, pk=None):
        ids = request.query_params.get("ids", "")

        qs = self.queryset.filter(id__in=ids.split(","))
        vc = self.queryset.filter(id=ids.split(",")[0]).first()
        try:
            title = Title.objects.filter(name=vc.title).first()
            if not title:
                title = Title.objects.create(name=vc.title)

            program_theme = ProgramTheme.objects.filter(name=vc.program_theme).first()
            if not program_theme:
                program_theme = ProgramTheme.objects.create(name=vc.program_theme)

            program_genre = ProgramGenre.objects.filter(name=vc.program_genre, program_theme=program_theme).first()
            if not program_genre:
                program_genre = ProgramGenre.objects.create(name=vc.program_genre, program_theme=program_theme)

            language = ContentLanguage.objects.filter(name=vc.language).first()
            if not language:
                language = ContentLanguage.objects.create(name=vc.language)

            if vc.prod_house and vc.channel:
                prod_house = ProductionHouse.objects.filter(name=vc.prod_house).first()
                if not prod_house:
                    prod_house = ProductionHouse.objects.create(name=vc.prod_house)

                super_program = Program.objects.filter(title=title, program_genre=program_genre,
                                                                 language=language, prod_house=prod_house,
                                                                 channel=vc.channel).first()
                if not super_program:
                    super_program = Program.objects.create(title=title, program_genre=program_genre,
                                                                     language=language, prod_house=prod_house,
                                                                     channel=vc.channel)
            elif vc.channel:
                super_program = Program.objects.filter(title=title, program_genre=program_genre,
                                                       language=language,
                                                       channel=vc.channel).first()
                if not super_program:
                    super_program = Program.objects.create(title=title, program_genre=program_genre,
                                                           language=language,
                                                           channel=vc.channel)
            else:
                raise KeyError
            super_program.created_by = self.request.user
            super_program.save()
            qs.update(program=super_program, is_mapped=True)
        except KeyError:
            print(vc.id)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            print(vc.id)
            print(e)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        return response.Response(data={"id": super_program.id}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def accept(self, request, pk=None):
        ids = request.query_params.get("ids", "")
        qs = VendorProgram.objects.all().filter(id__in=ids.split(","))
        qs.update(is_mapped=True)
        accept_program.delay(ids)
        return response.Response(data={"message": "success"}, status=status.HTTP_200_OK)


class SuperCommercialViewSet(viewsets.ModelViewSet):
    queryset = SuperCommercial.objects.all().order_by("created_on")
    serializer_class = SuperCommercialSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("vendor__name","title","brand_name","brand_sector","brand_category","advertiser",
                     "advertiser_group", "descriptor")
    search_fields = ("title","brand_name")
    action_serializer_classes = {
        "list": DetailSuperCommercialSerializer,
        "retrieve": DetailSuperCommercialSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(SuperCommercialViewSet, self).get_serializer_class()

    @list_route(methods=['get'])
    def duplicates(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", "")
        brand_name = request.query_params.get("brand_name", "")
        brand_sector = request.query_params.get("brand_sector", "")
        descriptor = request.query_params.get("descriptor", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor","")

        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset().filter(is_mapped=False).filter(title__icontains=title,
                                                                brand_sector__icontains=brand_sector,
                                                                descriptor__icontains=descriptor,
                                                                brand_name__icontains=brand_name,
                                                                vendor__name__icontains=vendor_name
                                                                )
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailSuperCommercialSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": 0, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data})


class SuperPromoViewSet(viewsets.ModelViewSet):
    queryset = SuperPromo.objects.all().order_by("created_on")
    serializer_class = SuperPromoSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("vendor__name","title","brand_name","brand_sector","brand_category","advertiser",
                     "advertiser_group", "descriptor")
    search_fields = ("title","brand_name")
    action_serializer_classes = {
        "list": DetailSuperPromoSerializer,
        "retrieve": DetailSuperPromoSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(SuperPromoViewSet, self).get_serializer_class()

    def list(self):
        request = self.request
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", "")
        brand_name = request.query_params.get("brand_name", "")
        brand_sector = request.query_params.get("brand_sector", "")
        descriptor = request.query_params.get("descriptor", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor","")

        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset().filter(is_mapped=False).filter(title__icontains=title,
                                                                brand_sector__icontains=brand_sector,
                                                                descriptor__icontains=descriptor,
                                                                brand_name__icontains=brand_name,
                                                                vendor__name__icontains=vendor_name
                                                                )
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailSuperPromoSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": 0, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data})

    @list_route(methods=['get'])
    def duplicates(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", "")
        brand_name = request.query_params.get("brand_name", "")
        brand_sector = request.query_params.get("brand_sector", "")
        descriptor = request.query_params.get("descriptor", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor","")

        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset().filter(is_mapped=False).filter(title__icontains=title,
                                                                brand_sector__icontains=brand_sector,
                                                                descriptor__icontains=descriptor,
                                                                brand_name__icontains=brand_name,
                                                                vendor__name__icontains=vendor_name
                                                                )
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailSuperPromoSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": 0, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data})


class SuperProgramViewSet(viewsets.ModelViewSet):
    queryset = SuperProgram.objects.all().order_by("created_on")
    serializer_class = SuperProgramSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("vendor__name","title","language", "program_theme", "program_genre", "prod_house")
    search_fields = ("title",)
    action_serializer_classes = {
        "list": DetailSuperProgramSerializer,
        "retrieve": DetailSuperProgramSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(SuperProgramViewSet, self).get_serializer_class()

    def list(self):
        request = self.request
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", "")
        language = request.query_params.get("language", "")
        program_genre = request.query_params.get("program_genre", "")
        program_theme = request.query_params.get("program_theme", "")
        prod_house = request.query_params.get("prod_house", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor","")
        channel = request.query_params.get("channel","")

        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset().filter(title__icontains=title,
                                        prod_house__icontains=prod_house,
                                        program_theme__icontains=program_theme,
                                        program_genre__icontains=program_genre,
                                        language__icontains=language,
                                        channel__name__icontains=channel,
                                        vendor__name__icontains=vendor_name
                                        )
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailSuperProgramSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": 0,"page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data})

    @list_route(methods=['get'])
    def duplicates(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        title = request.query_params.get("title", "")
        language = request.query_params.get("language", "")
        program_genre = request.query_params.get("program_genre", "")
        program_theme = request.query_params.get("program_theme", "")
        prod_house = request.query_params.get("prod_house", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor","")
        channel = request.query_params.get("channel","")

        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset().filter(is_mapped=False).filter(title__icontains=title,
                                                                prod_house__icontains=prod_house,
                                                                program_theme__icontains=program_theme,
                                                                program_genre__icontains=program_genre,
                                                                language__icontains=language,
                                                                channel__name__icontains=channel,
                                                                vendor__name__icontains=vendor_name
                                                                )
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailSuperProgramSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": 0,"page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data})


class VendorMasterComparisonViewSet(viewsets.ModelViewSet):
    queryset = VendorMasterComparison.objects.all().order_by('-created_on')
    serializer_class = VendorMasterComparisonSerializer
    permission_classes = (permissions.IsAuthenticated,)


class WeeklyReportViewSet(viewsets.ModelViewSet):
    queryset = WeeklyReport.objects.all().order_by('-created_on')
    serializer_class = WeeklyReportSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_fields = ("week",)

    def list(self, request, *args, **kwargs):
        page_size = int(request.query_params.get("page_size", 10))
        week = request.query_params.get("week","")
        page = int(request.query_params.get("page", 1))
        qs = WeeklyReport.objects.all().order_by('-created_on')
        if week:
            qs = qs.filter(week=week)
        ser = WeeklyReportSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        return response.Response(data={"results":ser.data, "count":count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size})

    @list_route(methods=['get'])
    def weeks(self, request, pk=None):
        qs = WeeklyReport.objects.all().values("week").order_by('-week').distinct()
        data = []
        for q in qs:
            data.append(q['week'])
        return response.Response(data=data, status=status.HTTP_200_OK)


class StatViewSet(viewsets.ViewSet):
    def list(self, request):
        date = request.query_params.get("date", None)
        td = datetime.datetime.today().strftime("%Y-%m-%d")
        if not date:
            dt = VendorCommercial.objects.all().annotate(date=Cast('created_on', DateField())).values('date').distinct().order_by('-date')
            latest = dt[0]['date'].strftime("%Y-%m-%d")
            date = latest
        vp = VendorPromo.objects.all().filter(created_on__date=date).values("vendor__name").order_by(
            "vendor__name").annotate(count=Count("id"))
        vp_data = CountSerializer(vp, many=True).data
        vc = VendorCommercial.objects.all().filter(created_on__date=date).values("vendor__name").order_by(
            "vendor__name").annotate(count=Count("id"))
        vc_data = CountSerializer(vc, many=True).data
        vpg = VendorProgram.objects.all().filter(created_on__date=date).values("vendor__name").order_by(
            "vendor__name").annotate(count=Count("id"))
        vpg_data = CountSerializer(vpg, many=True).data
        new_masters = Program.objects.all().filter(vendorprogram__created_on__date=date, created_on__date=date).count()+Commercial.objects.all().filter(vendorcommercial__created_on__date=date, created_on__date=date).count()+Promo.objects.all().filter(vendorpromo__created_on__date=date, created_on__date=date).count()
        # new_vendor_tags = VendorProgram.objects.all().filter(created_on__date=date).count()+VendorCommercial.objects.all().filter(created_on__date=date).count()+VendorPromo.objects.all().filter(created_on__date=date).count()
        data = {
            "promo": vp_data,
            "commercial": vc_data,
            "program": vpg_data,
            "new_count": new_masters
        }
        return response.Response(data=data, status=status.HTTP_200_OK)


class VendorChannelViewset(viewsets.ModelViewSet):
    queryset = VendorChannel.objects.all().order_by('name')
    serializer_class = VendorChannelSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("vendor__name","name","code","network_name","region","genre")
    search_fields = ("name",)
    action_serializer_classes = {
        "list": DetailVendorChannelSerializer,
        "retrieve": DetailVendorChannelSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(VendorChannelViewset, self).get_serializer_class()

    def filter_qs(self, request):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        name = request.query_params.get("name", "")
        network = request.query_params.get("network", "")
        region = request.query_params.get("region", "")
        genre = request.query_params.get("genre", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor", "")
        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if name:
            qs = qs.filter(name__icontains=name)
        if network:
            qs = qs.filter(network_name__icontains=network)
        if region:
            qs = qs.filter(region__icontains=region)
        if genre:
            qs = qs.filter(genre__icontains=genre)
        if vendor_name:
            qs = qs.filter(vendor__name__icontains=vendor_name)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        return qs

    def list(self, request, *args, **kwargs):
        page_size = int(request.query_params.get("page_size", 10))
        page = int(request.query_params.get("page", 1))
        qs = self.filter_qs(request)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailVendorChannelSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = 0
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data})

    @list_route(methods=['get'])
    def duplicates(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        page = int(request.query_params.get("page", 1))
        qs = self.filter_qs(request)
        qs = qs.filter(is_mapped=False)

        qs = qs.annotate(num_similars=Count('similars')).order_by("-num_similars", "name")
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailSimilarVendorChannelSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = 0
        pending = get_pending()
        if pending==0:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            date = yesterday.strftime('%Y-%m-%d')

        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data, "pending": pending})

    @list_route(methods=['get'])
    def merge(self, request, pk=None):
        vendor_name = request.query_params.get("vendor", "")
        qs = self.queryset.filter(is_mapped=False, vendor__name=vendor_name)
        qs.update(is_mapped=True)
        return response.Response(data={"message": "success"})

    @list_route(methods=['get'])
    def multi_merge(self, request, pk=None):
        ids = request.query_params.get("ids", "")

        qs = self.queryset.filter(id__in=ids.split(","))
        vc = self.queryset.filter(id=ids.split(",")[0]).first()
        try:
            network = ChannelNetwork.objects.filter(name=vc.network_name if vc.network_name else '').first()
            if not network:
                network = ChannelNetwork.objects.create(name=vc.network_name if vc.network_name else '')

            region = Region.objects.filter(name=vc.region if vc.region else '').first()
            if not region:
                region = Region.objects.create(name=vc.region if vc.region else '')

            genre = ChannelGenre.objects.filter(name=vc.genre).first()
            if not genre:
                genre = ChannelGenre.objects.create(name=vc.genre)

            language = ContentLanguage.objects.filter(name=vc.language).first()
            if not language:
                language = ContentLanguage.objects.create(name=vc.language)

            super_channel = Channel.objects.filter(code=int(vc.code)).first()
            if not super_channel:
                super_channel = Channel.objects.create(name=vc.name, code=int(vc.code), genre=genre, region=region,
                                                       network=network,
                                                       language=language)
            else:
                super_channel.name=vc.name
            super_channel.created_by = self.request.user
            super_channel.save()
            qs.update(channel=super_channel, is_mapped=True)
        except KeyError:
            print(vc.id)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            print(vc.id)
            print(e)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        return response.Response(data={"id": ''}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def accept(self, request, pk=None):
        ids = request.query_params.get("ids", "")
        qs = VendorChannel.objects.all().filter(id__in=ids.split(","))
        qs.update(is_mapped=True)
        accept_channel.delay(ids)
        return response.Response(data={"message": "success"}, status=status.HTTP_200_OK)


class VendorPromoCategoryViewset(viewsets.ModelViewSet):
    queryset = VendorPromoCategory.objects.all().order_by('name')
    serializer_class = VendorPromoCategorySerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("vendor__name","name","code")
    search_fields = ("name",)
    action_serializer_classes = {
        "list": DetailVendorPromoCategorySerializer,
        "retrieve": DetailVendorPromoCategorySerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(VendorPromoCategoryViewset, self).get_serializer_class()

    def filter_qs(self, request):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        name = request.query_params.get("name", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor", "")
        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if name:
            qs = qs.filter(name__icontains=name)
        if vendor_name:
            qs = qs.filter(vendor__name__icontains=vendor_name)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        return qs

    def list(self, request, *args, **kwargs):
        page_size = int(request.query_params.get("page_size", 10))
        page = int(request.query_params.get("page", 1))
        qs = self.filter_qs(request)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailVendorPromoCategorySerializer(qs[(page-1)*page_size:page*page_size], many=True)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = 0
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data})

    @list_route(methods=['get'])
    def duplicates(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        page = int(request.query_params.get("page", 1))
        qs = self.filter_qs(request)
        qs = qs.filter(is_mapped=False)
        qs = qs.annotate(num_similars=Count('similars')).order_by("-num_similars", "name")
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailSimilarVendorPromoCategorySerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = 0
        pending = get_pending()
        if pending==0:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            date = yesterday.strftime('%Y-%m-%d')

        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data, "pending": pending})

    @list_route(methods=['get'])
    def merge(self, request, pk=None):
        vendor_name = request.query_params.get("vendor", "")
        qs = self.queryset.filter(is_mapped=False, vendor__name=vendor_name)
        qs.update(is_mapped=True)
        return response.Response(data={"message": "success"})

    @list_route(methods=['get'])
    def multi_merge(self, request, pk=None):
        ids = request.query_params.get("ids", "")

        qs = self.queryset.filter(id__in=ids.split(","))
        vc = self.queryset.filter(id=ids.split(",")[0]).first()
        try:
            super_promo_cat, c = PromoCategory.objects.get_or_create(name=vc.name)
            super_promo_cat.created_by = self.request.user
            super_promo_cat.save()
            qs.update(promo_type=super_promo_cat, is_mapped=True)
        except KeyError:
            print(vc.id)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            print(vc.id)
            print(e)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        return response.Response(data={"id": ''}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def accept(self, request, pk=None):
        ids = request.query_params.get("ids", "")
        qs = self.queryset.filter(id__in=ids.split(","))
        qs.update(is_mapped=True)
        accept_promo_category.delay(ids)
        return response.Response(data={"message": "success"}, status=status.HTTP_200_OK)


class VendorProgramGenreViewset(viewsets.ModelViewSet):
    queryset = VendorProgramGenre.objects.all().order_by('name')
    serializer_class = VendorProgramGenreSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("vendor__name","name","code", "program_theme")
    search_fields = ("name",)
    action_serializer_classes = {
        "list": DetailVendorProgramGenreSerializer,
        "retrieve": DetailVendorProgramGenreSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(VendorProgramGenreViewset, self).get_serializer_class()

    def filter_qs(self, request):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        name = request.query_params.get("name", "")
        program_theme = request.query_params.get("program_theme", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor", "")
        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if name:
            qs = qs.filter(name__icontains=name)
        if program_theme:
            qs = qs.filter(program_theme__icontains=program_theme)
        if vendor_name:
            qs = qs.filter(vendor__name__icontains=vendor_name)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        return qs

    def list(self, request, *args, **kwargs):
        page_size = int(request.query_params.get("page_size", 10))
        page = int(request.query_params.get("page", 1))
        qs = self.filter_qs(request)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailVendorProgramGenreSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = 0
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data})

    @list_route(methods=['get'])
    def duplicates(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        page = int(request.query_params.get("page", 1))
        qs = self.filter_qs(request)
        qs = qs.filter(is_mapped=False)
        qs = qs.annotate(num_similars=Count('similars')).order_by("-num_similars", "name")
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailSimilarVendorProgramGenreSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = 0
        pending = get_pending()
        if pending==0:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            date = yesterday.strftime('%Y-%m-%d')

        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data, "pending": pending})

    @list_route(methods=['get'])
    def merge(self, request, pk=None):
        vendor_name = request.query_params.get("vendor", "")
        qs = self.queryset.filter(is_mapped=False, vendor__name=vendor_name)
        qs.update(is_mapped=True)
        return response.Response(data={"message": "success"})

    @list_route(methods=['get'])
    def multi_merge(self, request, pk=None):
        ids = request.query_params.get("ids", "")

        qs = self.queryset.filter(id__in=ids.split(","))
        vc = self.queryset.filter(id=ids.split(",")[0]).first()
        try:
            program_theme = ProgramTheme.objects.filter(name=vc.program_theme).first()
            if not program_theme:
                program_theme = ProgramTheme.objects.create(name=vc.program_theme)
            program_genre, c = ProgramGenre.objects.get_or_create(name=vc.name, program_theme=program_theme)
            program_genre.created_by = self.request.user
            program_genre.save()
            qs.update(program_genre=program_genre, is_mapped=True)
        except KeyError:
            print(vc.id)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            print(vc.id)
            print(e)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        return response.Response(data={"id": ''}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def accept(self, request, pk=None):
        ids = request.query_params.get("ids", "")
        qs = self.queryset.filter(id__in=ids.split(","))
        qs.update(is_mapped=True)
        accept_program_genre.delay(ids)
        return response.Response(data={"message": "success"}, status=status.HTTP_200_OK)


class VendorContentLanguageViewset(viewsets.ModelViewSet):
    queryset = VendorContentLanguage.objects.all().order_by('name')
    serializer_class = VendorContentLanguageSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, django_filters.rest_framework.DjangoFilterBackend)
    filter_fields = ("vendor__name","name","code")
    search_fields = ("name",)
    action_serializer_classes = {
        "list": DetailVendorContentLanguageSerializer,
        "retrieve": DetailVendorContentLanguageSerializer,
    }

    def get_serializer_class(self):
        try:
            return self.action_serializer_classes[self.action]
        except (KeyError, AttributeError):
            return super(VendorContentLanguageViewset, self).get_serializer_class()

    def filter_qs(self, request):
        page_size = int(request.query_params.get("page_size", 10))
        search = request.query_params.get("search", "")
        name = request.query_params.get("name", "")
        created_on = request.query_params.get("created_on", None)
        vendor_name = request.query_params.get("vendor", "")
        page = int(request.query_params.get("page", 1))
        qs = self.get_queryset()
        if name:
            qs = qs.filter(name__icontains=name)
        if vendor_name:
            qs = qs.filter(vendor__name__icontains=vendor_name)
        if created_on:
            qs = qs.filter(created_on__date=created_on)
        return qs

    def list(self, request, *args, **kwargs):
        page_size = int(request.query_params.get("page_size", 10))
        page = int(request.query_params.get("page", 1))
        qs = self.filter_qs(request)
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailVendorContentLanguageSerializer(qs[(page-1)*page_size:page*page_size], many=True)
        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = 0
        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data})

    @list_route(methods=['get'])
    def duplicates(self, request, pk=None):
        page_size = int(request.query_params.get("page_size", 10))
        page = int(request.query_params.get("page", 1))
        qs = self.filter_qs(request)
        qs = qs.filter(is_mapped=False)

        qs = qs.annotate(num_similars=Count('similars')).order_by("-num_similars", "name")
        vendor_count = qs.values('vendor__name').order_by('vendor__name').annotate(count=Count('vendor__name'))
        vendor_count_data = VendorCountSerializer(vendor_count,many=True)
        ser = DetailSimilarVendorContentLanguageSerializer(qs[(page-1)*page_size:page*page_size], many=True)

        count = qs.count()
        total_pages = math.ceil(count/page_size)
        supermaster_count = 0
        pending = get_pending()
        if pending==0:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            date = yesterday.strftime('%Y-%m-%d')

        return response.Response(data={"results":ser.data, "count":count, "supermaster_count": supermaster_count, "page":page, "total_pages": total_pages,
                                       "page_size":page_size, "vendor_count":vendor_count_data.data, "pending": pending})

    @list_route(methods=['get'])
    def merge(self, request, pk=None):
        vendor_name = request.query_params.get("vendor", "")
        qs = self.queryset.filter(is_mapped=False, vendor__name=vendor_name)
        qs.update(is_mapped=True)
        return response.Response(data={"message": "success"})

    @list_route(methods=['get'])
    def multi_merge(self, request, pk=None):
        ids = request.query_params.get("ids", "")

        qs = self.queryset.filter(id__in=ids.split(","))
        vc = self.queryset.filter(id=ids.split(",")[0]).first()
        try:
            content_lang, c = ContentLanguage.objects.get_or_create(name=vc.name)
            content_lang.created_by = self.request.user
            content_lang.save()
            qs.update(content_language=content_lang, is_mapped=True)
        except KeyError:
            print(vc.id)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            print(vc.id)
            print(e)
            return response.Response(status=status.HTTP_400_BAD_REQUEST)
        return response.Response(data={"id": ''}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def accept(self, request, pk=None):
        ids = request.query_params.get("ids", "")
        qs = self.queryset.filter(id__in=ids.split(","))
        qs.update(is_mapped=True)
        accept_content_language.delay(ids)
        return response.Response(data={"message": "success"}, status=status.HTTP_200_OK)