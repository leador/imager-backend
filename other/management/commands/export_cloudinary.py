from django.core.management import BaseCommand
from os import walk

class Command(BaseCommand):
    def handle(self, *args, **options):
        for (dirpath, dirnames, filenames) in walk('../../../static/media/'):
            self.stdout.write(f"DIRPATH {dirpath}")
            self.stdout.write(f"DIRNAME {dirnames}")
            self.stdout.write(f"FILENAME {filenames}", ending='\n\n')