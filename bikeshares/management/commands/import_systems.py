import pybikes
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.utils import timezone

from bikeshares.models import BikeShareSystem, City


class Command(BaseCommand):
    help = 'Import bike share systems from PyBikes'

    def handle(self, *args, **options):
        added_bss_count = 0
        system_ids = []
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
            system_ids.append(system.pk)
            added_bss_count += int(created)
        deactivated_count = BikeShareSystem.available.exclude(pk__in=system_ids).update(active=False, modified_on=timezone.now())
        print 'Added %i new bike share systems and deactivated %i for a total of %i active bike share systems.' % (added_bss_count, deactivated_count, BikeShareSystem.available.count(),)

