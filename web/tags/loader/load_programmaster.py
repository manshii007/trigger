from xml.etree import ElementTree
from tags.models import Channel, Title, ProgramGenre, ProgramTheme, ContentLanguage, ProductionHouse, Program
import tqdm


def load(file='./masters/data/TAM/BrandMstXml_20190416.xml'):
    tree = ElementTree.parse(file)
    root = tree.getroot()
    data = []
    prods= []
    langs = []
    titles = []
    prodkeys = set()
    langkeys = set()
    titlekeys = set()
    for child in tqdm.tqdm(root):
        row_data = []
        for gc in child:
            row_data.append(gc.text)
        data.append(row_data)
    for row_data in tqdm.tqdm(data):
        try:
            # channel, title, language, theme, genre, prod house
            title = Title.objects.filter(name=row_data[2]).first()
            if not title and row_data[2] and row_data[2] not in titlekeys:
                titles.append(Title(name=row_data[2]))
                titlekeys.add(row_data[2])

            lang = ContentLanguage.objects.filter(name=row_data[4]).first()
            if len(row_data)>10:
                prod = ProductionHouse.objects.filter(name=row_data[10]).first()
                if not prod and row_data[10] and row_data[10] not in prodkeys:
                    prods.append(ProductionHouse(name=row_data[10]))
                    prodkeys.add(row_data[10])
        except TypeError:
            pass
    Title.objects.bulk_create(titles,2000)
    ProductionHouse.objects.bulk_create(prods,2000)
    prodkeys.clear()
    titlekeys.clear()
    print("------------------------------STEP 1----------------------------------")
    programs = []
    programkeys = set()
    for row_data in tqdm.tqdm(data):
        # channel, title, language, theme, genre, prod house
        ch = Channel.objects.filter(name=row_data[1]).first()
        title = Title.objects.filter(name=row_data[2]).first()
        pg = ProgramGenre.objects.filter(name=row_data[8]).first()
        lang = ContentLanguage.objects.filter(name=row_data[4]).first()
        if len(row_data)>10:
            prod = ProductionHouse.objects.filter(name=row_data[10]).first()
        else:
            prod = None
        k = "{}----{}".format(row_data[1], row_data[2])
        comm = Program.objects.filter(title=title, channel=ch).first()
        if not comm:
            if title and ch and k not in programkeys:
                programs.append(Program(title=title, channel=ch, program_genre=pg, prod_house=prod, language=lang))
                programkeys.add(k)
    Program.objects.bulk_create(programs, 2000)
    programkeys.clear()
    print("------------------------------Done----------------------------------")