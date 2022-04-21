from masters.models import VendorCommercial
from tags.models import Commercial
import tqdm


def remaining():
    """
    find the remaining queryset without a mapping to a supermaster entry
    :return:
    vendor_programs : QuerySet
    """
    v = VendorCommercial.objects.filter(is_mapped=True,commercial__isnull=True)
    return v


def mapping():
    """
    map the remaining queryset with a supermaster entry if possible
    :return:
    remaining_entries : QuerySet
    """
    remaining_entries = remaining()
    master_data = Commercial.objects.all().order_by().values("brand_name__name", "descriptor__text", "id")
    masters_keys = {}
    print("Starting Master keys preparation")
    for data_literal in tqdm.tqdm(master_data):
        if data_literal['brand_name__name'] not in masters_keys:
            masters_keys[data_literal['brand_name__name']]={
                data_literal['descriptor__text']:data_literal['id']
            }
        else:
            masters_keys[data_literal['brand_name__name']][data_literal['descriptor__text']]=data_literal['id']
    print("Completed Master keys preparation")
    print("Started Remapping")
    for remain_literal in tqdm.tqdm(remaining_entries):
        if remain_literal.brand_name and remain_literal.brand_name in masters_keys and remain_literal.descriptor in masters_keys[remain_literal.brand_name]:
            matched_id = masters_keys[remain_literal.brand_name][remain_literal.descriptor]
            remain_literal.commercial=Commercial.objects.get(id=matched_id)
    print('ended Remapping and Starting Bulk Update')
    # update the queryset for program field
    VendorCommercial.objects.bulk_update(remaining_entries, update_fields=['commercial'], batch_size=5000)
    print("Bulk Update Over")
    final_remaining = remaining()
    print("{} remaining entries left out".format(final_remaining.count()))
