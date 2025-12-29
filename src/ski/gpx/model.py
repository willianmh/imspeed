from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel


class Point(BaseModel):
    time: Optional[datetime] = None
    lat: float
    lon: float
    ele: float


class Segment(BaseModel):
    type: Literal["lift", "run"]
    start: datetime
    end: datetime
    points: List[Point]


class SpeedPoint(BaseModel):
    time: datetime
    lat: float
    lon: float
    ele: float
    dist_xy_m: float = 0.0
    dist_z_m: float = 0.0
    dist_3d_m: float = 0.0
    dt_s: float = 0.0
    speed_mps: float = 0.0
    speed_kmh: float = 0.0
