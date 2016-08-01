import lxml
import pybikes
import requests
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.utils import timezone

from bikeshares.utils import get_bike_share_system
from bikeshares.models import BikeShareSystem, City, Station


class Command(BaseCommand):
    help = 'Import and update all bike share systems and stations'

    def handle(self, *args, **options):
        added_bss_count = 0
        system_ids = []
        for system_name, data in pybikes.get_instances():
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
                'system': system_name,
            }
            system, created = BikeShareSystem.objects.get_or_create(defaults=bss_fields, tag=data['tag'])
            system_ids.append(system.pk)
            added_bss_count += int(created)
        deactivated_count = BikeShareSystem.available.exclude(pk__in=system_ids).update(active=False, modified_on=timezone.now())
        print 'Added %i new bike share systems and deactivated %i for a total of %i active bike share systems.' % (added_bss_count, deactivated_count, BikeShareSystem.available.count(),)

        added_station_count = 0
        for bss in BikeShareSystem.available.all():
            pybikes_bss = get_bike_share_system(bss.tag, bss.system)
            try:
                pybikes_bss.update()
            except (AssertionError, KeyError, lxml.etree.XMLSyntaxError, requests.exceptions.ConnectionError,):
                # TODO: log errors
                continue
            for station in pybikes_bss.stations:
                lookup = {'bike_share_system': bss, 'name': station.name}
                station_fields = {
                    'latitude': station.latitude,
                    'longitude': station.longitude,
                }
                station, created = Station.objects.get_or_create(defaults=station_fields, **lookup)
                added_station_count += int(created)
        print 'Added %i new bike share stations for a total of %i active bike share stations.' % (added_station_count, Station.available.count(),)

