from xml.etree import ElementTree
from tags.models import Channel, Title, ProgramGenre, ProgramTheme, ContentLanguage, ProductionHouse, Program
import tqdm
from tags.loader.loader import clean_file, silentremove


def load(file):
    tmp_file = clean_file(file, True)
    tree = ElementTree.parse(tmp_file)
    root = tree.getroot()
    data = []

    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        data.append(row_data)
    print("Number of entries : {}".format(len(data)))
    ind = 0
    programs = []
    programkeys = set()
    for row_data in tqdm.tqdm(data, position=2):
        ind +=1
        if len(row_data) > 11:
            comm = Program.objects.filter(id=row_data[12]).first()
            k = row_data[12]
        else:
            comm = Program.objects.filter(id=row_data[10]).first()
            k = row_data[10]

        title = Title.objects.filter(name=row_data[2], code=row_data[3]).first()
        pg = ProgramGenre.objects.filter(name=row_data[8], code=row_data[9]).first()
        lang = ContentLanguage.objects.filter(name=row_data[4], code=row_data[5]).first()
        ch = Channel.objects.filter(code=row_data[0]).first()
        if len(row_data) > 11:
            prod = ProductionHouse.objects.filter(name=row_data[10], code=row_data[11]).first()

        else:
            prod = None

        if not comm:
            if not title:
                if Title.objects.filter(name=row_data[2]).first():
                    title = Title.objects.filter(name=row_data[2]).first()
                    title.code = row_data[3]
                    title.save()
                else:
                    title = Title.objects.create(name=row_data[2], code=row_data[3])
            if not pg:
                if ProgramGenre.objects.filter(name=row_data[8]).first():
                    pg = ProgramGenre.objects.filter(name=row_data[8]).first()
                    pg.code = row_data[9]
                    pg.save()
            if not lang:
                if ContentLanguage.objects.filter(name=row_data[4]).first():
                    lang = ContentLanguage.objects.filter(name=row_data[4]).first()
                    lang.code = row_data[5]
                    lang.save()
            if k not in programkeys:
                programs.append(
                    Program(id=k, title=title, channel=ch, program_genre=pg, prod_house=prod, language=lang))
                programkeys.add(k)
        else:
            c = Program.objects.filter(id=row_data[12]).first()
            c.title = title
            c.channel = ch
            c.program_genre = pg
            c.language = lang
            c.prod_house = prod
            c.save()
    Program.objects.bulk_create(programs, 2000)
    programkeys.clear()
    silentremove(tmp_file)
    print("------------------------------Done----------------------------------")