from django.db import models
from django.utils import timezone

from utils import distance


class City(models.Model):
    tag = models.SlugField(max_length=20)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=2)

    added_on = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = 'cities'

    def __unicode__(self):
        return self.name

    def clean(self):
        self.code = self.code.lower()


class AvailableBikeShareSystemManager(models.Manager):
    def get_query_set(self):
        return super(AvailableBikeShareSystemManager, self).get_query_set().filter(
            active=True)


class BikeShareSystem(models.Model):
    city = models.ForeignKey(City)
    company = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    name = models.CharField(max_length=100, null=True)
    system = models.CharField(max_length=50)
    tag = models.CharField(max_length=50)
    active = models.BooleanField(default=True)

    added_on = models.DateTimeField(default=timezone.now)
    modified_on = models.DateTimeField(default=timezone.now)
    last_recorded_update = models.DateTimeField(null=True)

    objects = models.Manager()
    available = AvailableBikeShareSystemManager()

    class Meta:
        get_latest_by = 'last_update'

    @staticmethod
    def build_name(name, city, country):
        if name:
            return name
        return u'%s, %s' % (city, country,)


class AvailableStationManager(models.Manager):
    def get_query_set(self):
        return super(AvailableBikeShareSystemManager, self).get_query_set().filter(
            active=True)


class Station(models.Model):
    bike_share_system = models.ForeignKey(BikeShareSystem)
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    active = models.BooleanField(default=True)

    added_on = models.DateTimeField(default=timezone.now)
    modified_on = models.DateTimeField(default=timezone.now)
    last_recorded_communication = models.DateTimeField(null=True)

    objects = models.Manager()
    available = AvailableStationManager()

    class Meta:
        get_latest_by = 'last_recorded_communication'

    def __unicode__(self):
        return self.name

    def neighbor_stations(self, num_stations=None):
        """
        Upon giving it a number of stations to look for, return a list of
        tuples containing the distance of the neighbor stations sorted by
        proximity.
        """
        return Station.closest_stations(self.latitude, self.longitude, self.city,
            num_stations)

    @staticmethod
    def closest_stations(latitude, longitude, bike_share_system=None, num_stations=None):
        """
        Upon giving it a bike share system, latitude, longitude coordinates and a number of
        stations to look for, return a list of tuples containing the distance
        and station sorted by proximity.
        """
        stations = dict()
        stations_qs = Station.objects.exclude(latitude=latitude, longitude=longitude)
        if bike_share_system:
            stations_qs = stations_qs.filter(bike_share_system=bike_share_system)
        for s in stations_qs:
            stations[distance(latitude, longitude, s.latitude, s.longitude)] = s
        sorted_stations = []
        for (i, s) in enumerate(sorted(stations.keys())):
            if num_stations and i == num_stations:
                break
            sorted_stations.append((s, stations[s],))
        return sorted_stations


class StationUpdate(models.Model):
    station = models.ForeignKey(Station)
    bikes = models.IntegerField(help_text='Number of bicycles docked at that moment.')
    free = models.IntegerField(help_text='Number of empty docks at that moment.')

    recorded_on = models.DateTimeField(default=timezone.now)
    update_time = models.DateTimeField(
        help_text='Date and time this update was recorded on the bicycle sharing system. Null if this information is unavailable.',
        null=True
    )
    extra_data = models.TextField(
        help_text="Unparsed update data acquired from the city's bicycle sharing system.",
        null=True
    )

    class Meta:
        get_latest_by = 'pk'

    def __unicode__(self):
        return self.station.name

