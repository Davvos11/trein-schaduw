import math
from dataclasses import dataclass


@dataclass
class Point:
    lat: float
    lon: float

    def __repr__(self):
        return f"({self.lat}, {self.lon})"

    @staticmethod
    def from_geojson(item: list[float]):
        return Point(item[1], item[0])

    def lat_rad(self) -> float:
        return math.radians(self.lat)

    def lon_rad(self) -> float:
        return math.radians(self.lon)


def get_bearing(point1: Point, point2: Point) -> float:
    """
    See https://en.wikipedia.org/wiki/Great-circle_navigation
    """
    phi_1 = point1.lat_rad()
    phi_2 = point2.lat_rad()
    lambda_12 = math.radians(point2.lon - point1.lon)

    x = math.cos(phi_2) * math.sin(lambda_12)
    y = math.cos(phi_1) * math.sin(phi_2) - math.sin(phi_1) * math.cos(phi_2) * math.cos(lambda_12)

    angle = math.atan2(x, y)
    return angle


def bearing_to_compass(bearing: float) -> str:
    bearing = math.degrees(bearing)
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    index = round(bearing / 45) % 8
    return directions[index]


def get_distance(point1: Point, point2: Point) -> float:
    """
    See https://en.wikipedia.org/wiki/Haversine_formula
    """
    earth_radius = 6378137  # in meters
    phi_1 = point1.lat_rad()
    phi_2 = point2.lat_rad()
    delta_phi = phi_2 - phi_1
    delta_lambda = math.radians(point2.lon - point1.lon)

    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


@dataclass
class Vec:
    x: float
    y: float

    @staticmethod
    def from_bearing(bearing: float) -> 'Vec':
        return Vec(
            math.cos(bearing),
            math.sin(bearing),
        )

    def rotate_left(self) -> 'Vec':
        # (x', y') = (-y, x)
        return Vec(-self.y, self.x)

    def rotate_right(self) -> 'Vec':
        # (x', y') = (y, -x)
        return Vec(self.y, -self.x)

    def dot(self, other: 'Vec') -> float:
        return self.x * other.x + self.y * other.y

    def __neg__(self) -> 'Vec':
        return Vec(-self.x, -self.y)
