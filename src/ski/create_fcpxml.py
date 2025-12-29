from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from ski.cli import build_settings, parse_args
from ski.config import AnimationSettings
from ski.fcp import TitleShape
from ski.fcp.final_cut_pro import generate_xml
from ski.gpx import (
    GPXData,
    SpeedPoint,
    calculate_speed,
    collect_points,
    interpolate_distances,
)
from ski.resources.templates import TemplateRegistry
from ski.utils import FileWriter


def _create_titles(
    points: List[SpeedPoint],
    template: str,
    initial_time: datetime | None = None,
) -> List[TitleShape]:
    titles = []

    # sync points
    start_idx = 0
    if initial_time is None:
        # no sync needed
        initial_time = points[0].time
    else:
        # chase the sync point
        for i, point in enumerate(points):
            if initial_time < point.time:
                # sync point is before an existing point
                points.insert(
                    i,
                    SpeedPoint(
                        time=initial_time,
                        lat=point.lat,
                        lon=point.lon,
                        ele=point.ele,
                    ),
                )
                start_idx = i
                break
            elif initial_time == point.time:
                # sync point match an existing point
                start_idx = i
                break

    titles = TemplateRegistry.apply(points=points[start_idx:], template=template)

    return titles


def create_fcpxml(settings: AnimationSettings):
    gpx_file = GPXData(settings.gpx_file)
    raw_points = collect_points(
        gpx=gpx_file.gpx, track_id=settings.track, segment_id=settings.segment
    )

    if settings.interpolate:
        raw_points = interpolate_distances(raw_points, step_seconds=0.05)

    points = calculate_speed(raw_points, smooth_window=25)

    titles = _create_titles(points=points, template=settings.template)

    duration = timedelta(seconds=settings.duration) if settings.duration else None

    project_title = Path(settings.output).stem

    xml = generate_xml(
        titles=titles,
        fps=settings.fps,
        project_title=project_title,
        duration=duration,
    )

    FileWriter.write(settings.output, xml)


def main():
    args = parse_args()
    try:
        settings = build_settings(args)
    except Exception as exc:
        print(f"Error: {exc}")
        return

    create_fcpxml(settings=settings)


if __name__ == "__main__":
    main()
