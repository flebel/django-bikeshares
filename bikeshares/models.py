from django.db import models


class AvailableCityManager(models.Manager):
    def get_query_set(self):
        return super(AvailableCityManager, self).get_query_set().filter(
            active=True)


class City(models.Model):
    tag = models.SlugField(
        help_text='Lowercase slug identifying the city.',
        max_length=20
    )
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=2)
    active = models.BooleanField(default=True)

    objects = models.Manager()
    available = AvailableCityManager()

    class Meta:
        verbose_name_plural = 'cities'

    def __unicode__(self):
        return self.name

    def clean(self):
        self.code = self.code.lower()


class BikeShareSystem(models.Model):
    city = models.ForeignKey(City)
    company = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    name = models.CharField(max_length=100, null=True)
    system = models.CharField(max_length=50)
    tag = models.CharField(max_length=50)

    last_recorded_update = models.DateTimeField(
        help_text='Date and time at which an update was recorded on the bicycle sharing system. Null if this information is unavailable.',
        null=True
    )

    class Meta:
        get_latest_by = 'last_update'

    @staticmethod
    def build_name(name, city, country):
        if name:
            return name
        return u'%s, %s' % (city, country,)

