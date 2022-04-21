from xml.etree import ElementTree
from tags.models import ContentLanguage
from django.db.utils import IntegrityError
import tqdm


def load(file='./masters/data/TAM/ContentLanguagexml_20190416.xml', vendor="TAM", loc=0):
    batch_size = 2000

    tree = ElementTree.parse(file)
    root = tree.getroot()
    data = []
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        try:
            if not ContentLanguage.objects.filter(code=row_data[0], name=row_data[1]) :
                s = ContentLanguage.objects.create(code=row_data[0], name=row_data[1], id=row_data[2])
        except TypeError:
            pass