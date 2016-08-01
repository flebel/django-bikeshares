from math import asin, cos, radians, sin, sqrt

import pybikes
from django.conf import settings


def distance(lat1, long1, lat2, long2):
    """
    Calculate the great circle distance in meters between two points on
    Earth (specified in decimal degrees.)
    Taken on May 1st 2013 from http://stackoverflow.com/a/4913653
    """
    # Convert decimal degrees to radians
    rlong1, rlat1, rlong2, rlat2 = map(radians, [long1, lat1, long2, lat2])
    # Haversine formula
    dlon = rlong2 - rlong1
    dlat = rlat2 - rlat1
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))

def get_bike_share_system(tag, system=None):
    if system:
        key = settings.PYBIKES_API_KEYS.get(system.lower())
    else:
        key = None
    return pybikes.get(tag, key=key)

