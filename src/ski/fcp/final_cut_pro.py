# Build XML structure
import uuid
from datetime import datetime, time, timedelta
from typing import Dict, List

from ski.fcp.model import TitleShape
from ski.utils import seconds_to_time, time_to_seconds


def time_to_frames(t: time, fps: int) -> int:
    """Convert time object to frame number, using floor for consistency."""
    return int(time_to_seconds(t) * fps)


def frames_to_time_units(frames: int) -> int:
    """Convert frame count to FCPXML time units"""
    return frames * 100


def fcp_header(
    project_title: str,
    fps: int,
    total_duration: int,
    time_base: int,
) -> List[str]:
    event_uid = uuid.uuid4()
    project_uid = uuid.uuid4()
    mod_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S +0000")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        "<!DOCTYPE fcpxml>",
        '<fcpxml version="1.13">',
        "  <resources>",
        f'    <format id="r1" name="FFVideoFormat1080p{fps}" frameDuration="1/{fps}s" width="2048" height="1024" colorSpace="1-1-1 (Rec. 709)"/>',
        '    <effect id="r2" name="Basic Title" uid=".../Titles.localized/Bumper:Opener.localized/Basic Title.localized/Basic Title.moti"/>',
        "  </resources>",
        "  <library>",
        f'    <event name="{project_title}" uid="{event_uid}">',
        f'      <project name="{project_title}" uid="{project_uid}" modDate="{mod_date}">',
        f'        <sequence format="r1" duration="{total_duration}/{time_base}s" tcStart="0/{fps}s" tcFormat="NDF" audioLayout="stereo" audioRate="48k">',
        "          <spine>",
        f'            <gap name="Gap" offset="0s" start="0s" duration="{total_duration}/{time_base}s">',
    ]

    return lines


def fcp_footer():
    return [
        "            </gap>",
        "          </spine>",
        "        </sequence>",
        "      </project>",
        "    </event>",
        '    <smart-collection name="Projects" match="all">',
        '      <match-clip rule="is" type="project"/>',
        "    </smart-collection>",
        '    <smart-collection name="All Video" match="any">',
        '      <match-media rule="is" type="videoOnly"/>',
        '      <match-media rule="is" type="videoWithAudio"/>',
        "    </smart-collection>",
        '    <smart-collection name="Audio Only" match="all">',
        '      <match-media rule="is" type="audioOnly"/>',
        "    </smart-collection>",
        '    <smart-collection name="Stills" match="all">',
        '      <match-media rule="is" type="stills"/>',
        "    </smart-collection>",
        '    <smart-collection name="Favorites" match="all">',
        '      <match-ratings value="favorites"/>',
        "    </smart-collection>",
        "  </library>",
        "</fcpxml>",
    ]


def merge_consecutive_titles(titles: List[TitleShape]) -> List[TitleShape]:
    """This function merges consecutives tiles that have the same text"""
    merged_titles = []
    if titles:
        i = 0
        while i < len(titles):
            current = titles[i]
            end_idx = i

            while (
                end_idx + 1 < len(titles)
                and titles[end_idx].text == titles[end_idx + 1].text
                and titles[end_idx].end_time == titles[end_idx + 1].start_time
            ):
                end_idx += 1

            if end_idx > i:
                # Create merged title with extended duration
                merged = current.model_copy(
                    update={"end_time": titles[end_idx].end_time}
                )
                merged_titles.append(merged)
            else:
                merged_titles.append(current)

            i = end_idx + 1
    return merged_titles


def merge_lanes(titles_per_lane: Dict[int, List[TitleShape]]) -> List[TitleShape]:
    """this function sort the titles in a dict organized by lanes (int).
    e.g.:
    titles_per_lane = {
        1: [title1, title2, title 3],
        2: [title4, title5],
        3: [title6]
    }

    where:
    title1.start_time = 2
    title2.start_time = 3
    title3.start_time = 4
    title4.start_time = 1
    title5.start_time = 2
    title6.start_time = 1

    the final output:
    [title4, title6, title1, title5, title2, title3]
    """
    all_titles = []
    for lane, titles in titles_per_lane.items():
        all_titles.extend(titles)

    # Sort by start_time first, then by lane number
    all_titles.sort(key=lambda t: (t.start_time, t.lane))

    return all_titles


def merge_titles(titles: List[TitleShape]) -> List[TitleShape]:
    # split per lane
    all_lanes = [t.lane for t in titles]
    lanes = list(set(all_lanes))
    titles_per_lane = {lane: [] for lane in lanes}

    for t in titles:
        titles_per_lane[t.lane].append(t)

    # merge titles
    merged_titles_per_lane = {}
    for lane_no, lane in titles_per_lane.items():
        merged_titles_per_lane[lane_no] = merge_consecutive_titles(lane)

    return merge_lanes(merged_titles_per_lane)


def filter_titles(titles: List[TitleShape], duration: float) -> List[TitleShape]:
    filtered_titles = []
    for title in titles:
        title_start_seconds = time_to_seconds(title.start_time)
        title_end_seconds = time_to_seconds(title.end_time)

        # Skip titles that start at or after the duration
        if title_start_seconds >= duration:
            continue

        # If title extends beyond duration, trim it
        if title_end_seconds > duration:
            # Create a copy with adjusted end_time
            trimmed_title = TitleShape(
                text_style_ref=title.text_style_ref,
                start_time=title.start_time,
                end_time=seconds_to_time(duration),
                text=title.text,
                font_style=title.font_style,
                lane=title.lane,
                x=title.x,
                y=title.y,
            )
            filtered_titles.append(trimmed_title)
        else:
            filtered_titles.append(title)
    return filtered_titles


def generate_xml(
    titles: List[TitleShape],
    fps: int,
    project_title: str = "Title",
    duration: timedelta | None = None,
) -> str:
    final_titles = merge_titles(titles)

    # Cut titles to match the specified duration if provided
    if duration is not None:
        duration_seconds = duration.total_seconds()
        final_titles = filter_titles(final_titles, duration_seconds)

        total_frames = int(duration.total_seconds() * fps)
        total_duration = frames_to_time_units(total_frames)

    elif final_titles:
        last_caption = final_titles[-1]
        total_frames = time_to_frames(last_caption.end_time, fps)
        total_duration = frames_to_time_units(total_frames)

    else:
        total_duration = 0

    # Time base for FCPXML (fps * 100)
    time_base = fps * 100

    lines = fcp_header(
        project_title=project_title,
        fps=fps,
        total_duration=total_duration,
        time_base=time_base,
    )

    for _title in final_titles:
        start_frames = time_to_frames(_title.start_time, fps)
        end_frames = time_to_frames(_title.end_time, fps)
        duration_frames = end_frames - start_frames

        offset_units = frames_to_time_units(start_frames)
        start_units = frames_to_time_units(start_frames)
        duration_units = frames_to_time_units(duration_frames)

        title_xml = _title.xml(
            time_base=time_base,
            offset_units=offset_units,
            start_units=start_units,
            duration_units=duration_units,
        )
        lines.extend(title_xml)

    lines.extend(fcp_footer())
    return "\n".join(lines)
