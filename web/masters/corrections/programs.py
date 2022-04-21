from masters.models import VendorProgram
from tags.models import *
import tqdm

def correct():
    vpgs = VendorProgram.objects.all().filter(program__isnull=True)
    for vc in tqdm.tqdm(vpgs):
        title = Title.objects.filter(name=vc.title).first()
        if not title and vc.title:
            title = Title.objects.create(name=vc.title)

        program_theme = ProgramTheme.objects.filter(name=vc.program_theme).first()
        if not program_theme and vc.program_theme:
            program_theme = ProgramTheme.objects.create(name=vc.program_theme)

        program_genre = ProgramGenre.objects.filter(name=vc.program_genre, program_theme=program_theme).first()
        if not program_genre and vc.program_genre:
            program_genre = ProgramGenre.objects.create(name=vc.program_genre, program_theme=program_theme)

        language = ContentLanguage.objects.filter(name=vc.language).first()
        if not language and vc.language:
            language = ContentLanguage.objects.create(name=vc.language)

        if vc.prod_house and vc.channel:
            prod_house = ProductionHouse.objects.filter(name=vc.prod_house).first()
            if not prod_house and vc.prod_house:
                prod_house = ProductionHouse.objects.create(name=vc.prod_house)

            super_program, c = Program.objects.get_or_create(title=title, program_genre=program_genre,
                                                             language=language, prod_house=prod_house,
                                                             channel=vc.channel)
        elif vc.channel:
            super_program, c = Program.objects.get_or_create(title=title, program_genre=program_genre,
                                                             language=language, channel=vc.channel)
        else:
            super_program = None
        vc.program = super_program
        vc.is_mapped = True
        vc.save()