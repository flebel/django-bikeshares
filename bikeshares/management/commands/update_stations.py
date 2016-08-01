import lxml
import pybikes
import requests
from django.core.management.base import BaseCommand, CommandError

from bikeshares.models import BikeShareSystem, City, Station, StationUpdate
from bikeshares.utils import get_bike_share_system


class Command(BaseCommand):
    args = '[<city_tag city_tag ...>]'
    help = 'Updates the current bike and dock counts for a given list of cities, or all cities if run without parameters.'

    def __init__(self):
        self._reset_counts()
        return super(Command, self).__init__()

    def _increase_created_count(self):
        self.created = self.created + 1

    def _increase_status_quo_count(self):
        self.status_quo = self.status_quo + 1

    def _reset_counts(self):
        self.created = 0
        self.status_quo = 0

    def handle(self, *args, **options):
        city_tags = args or map(lambda x: x[0], City.objects.all().values_list('tag'))

        for city_tag in city_tags:
            try:
                systems = BikeShareSystem.objects.filter(city__tag=city_tag)
            except City.DoesNotExist:
                raise CommandError("City '%s' does not exist or offers bike share systems." % city_tag)

            self._reset_counts()

            for bss in systems:
                system = get_bike_share_system(bss.tag, bss.system)
                try:
                    system.update()
                except (AssertionError, KeyError, lxml.etree.XMLSyntaxError, requests.exceptions.ConnectionError,):
                    # TODO: log errors
                    continue
                most_recent_timestamp = 0
                for s in system.stations:
                    try:
                        station = Station.objects.get(bike_share_system=bss, name=s.name)
                    except Station.DoesNotExist:
                        self.stdout.write(u"Missing station '%s' for bike share system '%s'." % (s.name, bss.name,))

                    print station.last_recorded_communication # TODO: Remove

                    updated = True
                    if station.last_recorded_communication:
                        updated = station.last_recorded_communication < s.timestamp
                    else:
                        updated = not StationUpdate.objects.filter(station=station, bikes=s.bikes, free=s.free).exists()
                    if not updated:
                        self._increase_status_quo_count()
                        continue

                    last_recorded_communication = s.timestamp

                    if StationUpdate.objects.filter(station=station, recorded_on=last_recorded_communication).exists():
                        self._increase_status_quo_count()
                        continue

                    # TODO: Inspect `s.extra['status']['online'] to take stations online or offline
                    StationUpdate.objects.create(
                        bikes=s.bikes or 0,
                        free=s.free or 0,
                        recorded_on=last_recorded_communication,
                        extra_data=s.extra,
                        station=station,
                    )
                    self._increase_created_count()

                    if not most_recent_timestamp or s.timestamp > most_recent_timestamp:
                        most_recent_timestamp = s.timestamp

            if most_recent_timestamp:
                bss.last_recorded_update = s.timestamp
                bss.save()

            self.stdout.write(u'\nSuccessfully updated bike counts for %s in %s.' % (bss.name, bss.city.name,))
            self.stdout.write(u'Created: %s' % (self.created,))
            self.stdout.write(u'Status quo: %s' % (self.status_quo,))

