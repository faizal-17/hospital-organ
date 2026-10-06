from django.core.management.base import BaseCommand
import seed_data

class Command(BaseCommand):
    help = 'Seeds sample data for organ request, doctors, government officials, hospitals, and organs.'

    def handle(self, *args, **options):
        seed_data.seed_all()
        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))
