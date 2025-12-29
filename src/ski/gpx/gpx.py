from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import gpxpy
import numpy as np
from geopy.distance import geodesic
from gpxpy.gpx import GPX

from ski.gpx.model import Point, Segment, SpeedPoint
from ski.utils import FileWriter


class GPXData:
    def __init__(self, gpx_path: Path):
        with open(gpx_path, "r") as f:
            _gpx = gpxpy.parse(f)

        self.gpx: GPX = _gpx

    def write(self, file: Path):
        FileWriter.write(file, self.gpx.to_xml())


def _to_time_seconds(times: Sequence[datetime | None]) -> np.ndarray:
    """Convert datetime timestamps to seconds relative to the first point."""
    valid_times = [t for t in times if t is not None]
    if not valid_times:
        # fallback to uniform 1s spacing when timestamps are missing.
        return np.arange(len(times), dtype=float)

    start = valid_times[0]

    # default gap to be 1s or inferred from first two points
    default_gap = (
        (valid_times[1] - valid_times[0]).total_seconds()
        if len(valid_times) > 1
        else 1.0
    )
    default_gap = default_gap if default_gap > 0 else 1.0
    seconds = []
    last_time = start

    for t in times:
        if t is None:
            # assume a default gap for missing timestamps.
            last_time = last_time + timedelta(seconds=default_gap)
        else:
            last_time = t
        seconds.append((last_time - start).total_seconds())

    return np.array(seconds, dtype=float)


def collect_segments(gpx: GPX) -> Dict[int, Segment]:
    segments = {}

    for track in gpx.tracks:
        for i, segment in enumerate(track.segments):
            points = []
            for p in segment.points:
                points.append(
                    Point(
                        **{
                            "time": p.time,
                            "lat": p.latitude,
                            "lon": p.longitude,
                            "ele": p.elevation,
                        }
                    )
                )

            # compute segment bounds safely
            times = [p.time for p in points]
            start, end = min(times), max(times)

            start_elevation, end_elevation = points[0].ele, points[-1].ele

            run_type = "run" if start_elevation > end_elevation else "lift"

            segments[i] = Segment(type=run_type, points=points, start=start, end=end)

    return segments


def collect_points(
    gpx: GPX, track_id: int | None = None, segment_id: int | None = None
) -> List[Point]:
    """Parse GPX file into a list of Points."""
    if track_id is not None:
        if track_id >= len(gpx.tracks):
            raise ValueError(
                f"track_id {track_id} out of range. Len tracks: {len(gpx.tracks)}"
            )

    if segment_id is not None:
        if track_id is None:
            raise ValueError("Provide track_id.")

        if segment_id >= len(gpx.tracks[track_id].segments):
            raise ValueError(
                f"segment_id {segment_id} out of range. Len segments: {len(gpx.tracks[track_id].segments)}"
            )

    points: List[Point] = []
    for _track_id, track in enumerate(gpx.tracks):
        if track_id is not None and _track_id != track_id:
            continue

        for _segment_id, segment in enumerate(track.segments):
            if segment_id is not None and _segment_id != segment_id:
                continue
            for p in segment.points:
                points.append(
                    Point(
                        time=p.time,
                        lat=p.latitude,
                        lon=p.longitude,
                        ele=p.elevation if p.elevation is not None else 0.0,
                    )
                )

    if not points:
        raise ValueError("No track points found in GPX file")

    return points


def find_segment(segments: Dict[int, Segment], target_time: datetime) -> int:
    """
    Given a timestamp as str, find the segment that contains the time.
    Return the segment index if found, otherwise -1.
    """

    # --- parse input time ---
    # try:
    #     target = datetime.fromisoformat(time)
    # except ValueError:
    #     try:
    #         target = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
    #     except ValueError:
    #         return -1

    for seg_id, segment in segments.items():
        if not segment.points:
            continue

        points = segment.points
        # infer timezone from segment

        seg_tz = points[0].time.tzinfo  # type: ignore

        # normalize target time
        if target_time.tzinfo is None and seg_tz is not None:
            target_time = target_time.replace(tzinfo=seg_tz)

        start, end = segment.start, segment.end

        if start <= target_time <= end:
            return seg_id

    return -1


def add_noise(points: List[Point], noise: float = 0.001) -> List[Point]:
    """Add small Gaussian noise to lat/lon/ele for each point."""
    if noise <= 0 or not points:
        return [Point(**p.model_dump()) for p in points]

    lats = np.array([p.lat for p in points])
    lons = np.array([p.lon for p in points])
    eles = np.array([p.ele for p in points])

    lat_span = max(lats.max() - lats.min(), 1e-9)
    lon_span = max(lons.max() - lons.min(), 1e-9)
    ele_span = max(eles.max() - eles.min(), 1e-9)

    rng = np.random.default_rng()
    lat_noise = rng.normal(scale=lat_span * noise, size=len(points))
    lon_noise = rng.normal(scale=lon_span * noise, size=len(points))
    ele_noise = rng.normal(scale=ele_span * noise, size=len(points))

    noisy_points: List[Point] = []
    for p, dlat, dlon, dele in zip(points, lat_noise, lon_noise, ele_noise):
        noisy_points.append(
            Point(
                time=p.time,
                lat=float(p.lat + dlat),
                lon=float(p.lon + dlon),
                ele=float(p.ele + dele),
            )
        )
    return noisy_points


def interpolate_distances(
    points: List[Point],
    step_seconds: float = 0.25,
) -> List[Point]:
    if len(points) < 2:
        return [Point(**p.model_dump()) for p in points]

    t0 = points[0].time

    # original times in sec
    t = np.array([(p.time - t0).total_seconds() for p in points])  # type: ignore

    # uniform time grid
    t_new = np.arange(t[0], t[-1], step_seconds)

    lat = np.interp(t_new, t, [p.lat for p in points])
    lon = np.interp(t_new, t, [p.lon for p in points])
    ele = np.interp(t_new, t, [p.ele for p in points])

    anchor_time = points[0].time or datetime.now()

    result: List[Point] = []
    for t_sec, la, lo, el in zip(t_new, lat, lon, ele):
        result.append(
            Point(
                time=anchor_time + timedelta(seconds=float(t_sec)),
                lat=float(la),
                lon=float(lo),
                ele=float(el),
            )
        )

    return result


def calculate_speed(
    points: List[Point], smooth_window: int = 20, power_factor: float = 1.05
) -> List[SpeedPoint]:
    if not points:
        return []

    lat = [p.lat for p in points]
    lon = [p.lon for p in points]
    ele = [p.ele for p in points]
    t = [p.time for p in points]

    n = len(points)

    # Convert to absolute time in seconds from first point
    time_seconds = _to_time_seconds(t)

    # Calculate time deltas between consecutive points
    dt_s = np.diff(time_seconds, prepend=time_seconds[0])

    # distances
    dist_xy = np.zeros(n)
    for i in range(1, n):
        dist_xy[i] = geodesic((lat[i - 1], lon[i - 1]), (lat[i], lon[i])).meters

    dist_z = np.diff(ele, prepend=ele[0])
    dist_3d = np.sqrt(dist_xy**2 + dist_z**2)

    speed = np.zeros(len(points))
    valid = dt_s > 0
    speed[valid] = dist_3d[valid] / dt_s[valid]

    # smooth (moving average)
    if smooth_window > 1:
        kernel = np.ones(smooth_window) / smooth_window
        speed = np.convolve(speed, kernel, mode="same")

    assert len(points) == dt_s.shape[0]

    result: List[SpeedPoint] = []
    for i in range(n):
        result.append(
            SpeedPoint(
                time=points[i].time,  # type: ignore
                lat=points[i].lat,
                lon=points[i].lon,
                ele=points[i].ele,
                dist_xy_m=float(dist_xy[i]),
                dist_z_m=float(dist_z[i]),
                dist_3d_m=float(dist_3d[i]),
                dt_s=float(dt_s[i]),
                speed_mps=speed[i],
                speed_kmh=speed[i] * 3.6 * power_factor,
            )
        )

    return result


def points_to_arrays(
    points: Sequence[Point],
) -> tuple[
    np.ndarray, np.ndarray, np.ndarray, List[Optional[datetime]], np.ndarray, float
]:
    lons = np.array([p.lon for p in points])
    lats = np.array([p.lat for p in points])
    elevations = np.array([p.ele for p in points])
    times = [p.time for p in points]
    time_seconds = _to_time_seconds(times)
    duration = float(time_seconds[-1]) if len(time_seconds) else 0.0
    return lons, lats, elevations, times, time_seconds, duration
