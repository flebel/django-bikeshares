import pybikes
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify

from bikeshares.models import BikeShareSystem, City


class Command(BaseCommand):
    help = 'Import bike share systems from PyBikes'

    def handle(self, *args, **options):
        number_added_bss = 0
        for name, data in pybikes.get_instances():
            lookup = {'tag': data['tag']}
            meta = data['meta']

            city_fields = {
                'name': meta['city'],
                'country': meta['country'],
            }
            city, created = City.objects.get_or_create(defaults=city_fields, tag=slugify(city_fields['name']))

            bss_fields = {
                'city': city,
                'latitude': meta['latitude'],
                'longitude': meta['longitude'],
                'name': BikeShareSystem.build_name(meta.get('name'), city.name, meta['country']),
            }
            system, created = BikeShareSystem.objects.get_or_create(defaults=bss_fields, **lookup)
            number_added_bss += int(created)
        print 'Added %i new bike share systems for a total of %i supported bike share systems.' % (number_added_bss, BikeShareSystem.objects.count(),)

