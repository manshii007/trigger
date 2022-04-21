from masters.models import VendorProgram
from tags.models import Program
import tqdm


def remaining():
    """
    find the remaining queryset without a mapping to a supermaster entry
    :return:
    vendor_programs : QuerySet
    """
    v = VendorProgram.objects.filter(is_mapped=True,program__isnull=True)
    return v


def mapping():
    """
    map the remaining queryset with a supermaster entry if possible
    :return:
    remaining_entries : QuerySet
    """
    remaining_entries = remaining()
    master_data = Program.objects.all().order_by().values("title__name", "channel", "id")
    masters_keys = {}
    print("Starting Master keys preparation")
    for data_literal in tqdm.tqdm(master_data):
        if data_literal['channel'] not in masters_keys:
            masters_keys[data_literal['channel']]={
                data_literal['title__name']:data_literal['id']
            }
        else:
            masters_keys[data_literal['channel']][data_literal['title__name']]=data_literal['id']
    print("Completed Master keys preparation")
    print("Started Remapping")
    for remain_literal in tqdm.tqdm(remaining_entries):
        if remain_literal.channel and remain_literal.channel.id in masters_keys and remain_literal.title in masters_keys[remain_literal.channel.id]:
            matched_id = masters_keys[remain_literal.channel.id][remain_literal.title]
            remain_literal.program=Program.objects.get(id=matched_id)
    print('ended Remapping and Starting Bulk Update')
    # update the queryset for program field
    VendorProgram.objects.bulk_update(remaining_entries, update_fields=['program'], batch_size=5000)
    print("Bulk Update Over")
    final_remaining = remaining()
    print("{} remaining entries left out".format(final_remaining.count()))
