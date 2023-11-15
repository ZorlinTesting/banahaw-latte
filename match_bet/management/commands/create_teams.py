from django.core.management.base import BaseCommand
import csv
from ...models import Team

csv_file_path = 'team_info.csv'

class Command(BaseCommand):
    help = 'My custom Django command'

    def handle(self, *args, **options):
        # Create Team objects from team_info.csv file [name, acronym, base_pr, seed, origin]
        try:
            with open(csv_file_path, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    print(row['origin'])
                    Team.objects.create(
                        name=row['name'],
                        acronym=row['acronym'].strip(' '),
                        base_pr=float(row['base_pr']),
                        current_pr=float(row['base_pr']),
                        seed=int(row['seed'].strip(' ').strip('0').strip('.')),
                        origin=row['origin'].strip(' ').lower()
                    )

            self.stdout.write(self.style.SUCCESS('Teams imported successfully!'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found at path: {csv_file_path}'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))
