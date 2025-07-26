class general:
    def __init__(self):
        pass

    def get_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the distance between two geographical points.
        :param lat1: Latitude of point 1
        :param lon1: Longitude of point 1
        :param lat2: Latitude of point 2
        :param lon2: Longitude of point 2
        :return: Distance in kilometers
        """
        from geopy.distance import geodesic
        return geodesic((lat1, lon1), (lat2, lon2)).kilometers
    
    @staticmethod
    def get_version():
        return "1.0.0"

    @staticmethod
    def get_author():
        return "JC Visagie"
    
    @staticmethod
    def get_description():
        return "This module provides general utility functions."