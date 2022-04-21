from django.contrib.admin import AdminSite


class MyAdminSite(AdminSite):
    site_header = 'Trigger v0.2'

admin_site = MyAdminSite(name='admin')