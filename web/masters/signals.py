from django.dispatch import receiver
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from .models import VendorMasterComparison
from .tasks import load_vendor_masters


@receiver(signal=post_save, sender=VendorMasterComparison)
def vendor_master_comparison_created(sender, instance, **kwargs):
    if kwargs.get('created') and instance.status=="wait" and instance.step==1:
        print("Master Comparison created Created")
        load_vendor_masters.delay(instance.id, instance.date.strftime("%Y%m%d"))
