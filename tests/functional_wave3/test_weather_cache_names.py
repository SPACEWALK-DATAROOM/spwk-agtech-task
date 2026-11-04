"""Actual source contracts: weather_cache_names."""
from .loader import load

def test_weather_cache_key_truncates_signed_coordinates_without_home_io():
    fn=load('spwk_agtech/make_weather_cache.py',['_get_cache_filename'])['_get_cache_filename']
    assert fn(52.56,-124.78)=='NASAPowerWeatherDataProvider_LAT00525_LON-1247.cache'
    assert fn(0,0)=='NASAPowerWeatherDataProvider_LAT00000_LON00000.cache'
