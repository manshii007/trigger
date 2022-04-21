from masters.models import VendorProgram, VendorPromo, VendorCommercial, Vendor
from tags.models import Promo, Program, Commercial
import tqdm


def compare_brands():
    commercials = VendorCommercial.objects.all().filter(commercial__isnull=True)
    for c in tqdm.tqdm(commercials):
        comm = Commercial.objects.filter(brand_name__name=c.brand_name, descriptor__text=c.descriptor).first()
        if comm:
            c.commercial=comm
    VendorCommercial.objects.bulk_update(commercials,update_fields=['commercial'], batch_size=5000)


def compare_promo():
    promos = VendorPromo.objects.all().filter(promo__isnull=True)
    for c in tqdm.tqdm(promos):
        comm = Promo.objects.filter(brand_name__name=c.brand_name).first()
        if comm:
            c.promo = comm
    VendorPromo.objects.bulk_update(promos, update_fields=['promo'], batch_size=5000)


def compare_program():
    programs = VendorProgram.objects.all().filter(program__isnull=True)
    for c in tqdm.tqdm(programs):
        comm = Program.objects.filter(title__name=c.title, channel=c.channel).first()
        if comm:
            c.program = comm
    VendorProgram.objects.bulk_update(programs, update_fields=['program'], batch_size=5000)