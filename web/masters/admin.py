from django.contrib import admin

from .models import Vendor, VendorMaster, VendorReport, MasterReport, SuperMaster

admin.site.register(Vendor)
admin.site.register(VendorMaster)
admin.site.register(VendorReport)
admin.site.register(MasterReport)
admin.site.register(SuperMaster)