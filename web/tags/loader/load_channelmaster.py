from xml.etree import ElementTree
from tags.models import Channel, ChannelGenre, ChannelNetwork, Region, ContentLanguage
from django.db.utils import IntegrityError
import tqdm


def load(file='./masters/data/TAM/ChnMstXml_20190416.xml', vendor="TAM", loc=0):
    tree = ElementTree.parse(file)
    root = tree.getroot()
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            network = ChannelNetwork.objects.filter(name=row_data[2]).first()
            if not network and row_data[2]:
                network = ChannelNetwork.objects.create(name=row_data[2])

            region = Region.objects.filter(name=row_data[6]).first()
            if not region and row_data[6]:
                region = Region.objects.create(name=row_data[6])

            genre = ChannelGenre.objects.filter(name=row_data[8]).first()
            if not genre:
                genre = ChannelGenre.objects.create(name=row_data[8])

            lang = ContentLanguage.objects.filter(name=row_data[4]).first()
            if not lang:
                lang = ContentLanguage.objects.create(name=row_data[4])

            if not Channel.objects.filter(name=row_data[0]) :
                s = Channel.objects.create(name=row_data[0], code=int(row_data[1]), network=network, language=lang, region=region,
                                           genre=genre, id=row_data[10]
                                           )
            else:
                c = Channel.objects.filter(name=row_data[0]).first()
                c.language = lang
                c.network = network
                c.genre = genre
                c.region = region
                c.save()
        except TypeError as e:
            raise e