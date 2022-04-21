from masters.models import VendorPromo
from tags.models import Promo
import tqdm


def remaining():
    """
    find the remaining queryset without a mapping to a supermaster entry
    :return:
    vendor_programs : QuerySet
    """
    v = VendorPromo.objects.filter(is_mapped=True,promo__isnull=True)
    return v


def mapping():
    """
    map the remaining queryset with a supermaster entry if possible
    :return:
    remaining_entries : QuerySet
    """
    remaining_entries = remaining()
    master_data = Promo.objects.all().order_by().values("brand_name__name", "id")
    masters_keys = {}
    print("Starting Master keys preparation")
    for data_literal in tqdm.tqdm(master_data):
        if data_literal['brand_name__name'] not in masters_keys:
            masters_keys[data_literal['brand_name__name']]=data_literal['id']
        else:
            masters_keys[data_literal['brand_name__name']]=data_literal['id']
    print("Completed Master keys preparation")
    print("Started Remapping")
    for remain_literal in tqdm.tqdm(remaining_entries):
        if remain_literal.brand_name and remain_literal.brand_name in masters_keys:
            matched_id = masters_keys[remain_literal.brand_name]
            remain_literal.promo=Promo.objects.get(id=matched_id)
    print('ended Remapping and Starting Bulk Update')
    # update the queryset for program field
    VendorPromo.objects.bulk_update(remaining_entries, update_fields=['promo'], batch_size=5000)
    print("Bulk Update Over")
    final_remaining = remaining()
    print("{} remaining entries left out".format(final_remaining.count()))
