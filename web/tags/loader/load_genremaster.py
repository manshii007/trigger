from xml.etree import ElementTree
from tags.models import ProgramGenre, ProgramTheme
from django.db.utils import IntegrityError
import tqdm


def load(file='./masters/data/TAM/Genremstxml_20190416.xml', vendor="TAM", loc=0):
    tree = ElementTree.parse(file)
    root = tree.getroot()
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        try:
            # brand name, title, brand sector, brand category, advertiser, advertiser group, descriptor
            if loc==0:
                theme = ProgramTheme.objects.filter(name=row_data[3]).first()
                if not theme:
                    theme = ProgramTheme.objects.create(name=row_data[3], code=row_data[2])
                if not ProgramGenre.objects.filter(name=row_data[1], code=row_data[0], id=row_data[4]) :
                    s = ProgramGenre.objects.create(name=row_data[1], program_theme=theme, code=row_data[0], id=row_data[4])
                else:
                    p = ProgramGenre.objects.filter(name=row_data[1]).first()
                    p.theme=theme
                    p.save()
            else:
                theme = ProgramTheme.objects.filter(name=row_data[2]).first()
                if not theme:
                    theme = ProgramTheme.objects.create(name=row_data[2])
                if not ProgramGenre.objects.filter(name=row_data[0]):
                    s = ProgramGenre.objects.create(name=row_data[0], program_theme=theme)
                else:
                    p = ProgramGenre.objects.filter(name=row_data[0]).first()
                    p.theme = theme
                    p.save()
        except TypeError:
            pass