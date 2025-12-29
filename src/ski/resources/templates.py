from abc import ABC, abstractmethod
from datetime import datetime, time
from typing import List
from ski.fcp.model import FontStyle, RGBAColor, ShadowProperties, TitleShape
from ski.gpx.model import SpeedPoint
from ski.utils import seconds_to_time


simple_shadow = ShadowProperties(
    color=RGBAColor(red=0, green=0, blue=0, alpha=0.8),
    blur_radius=1.8
)

default_font_style = FontStyle(
    font="Unbounded",
    font_size=60,
    font_face="Medium",
    shadow=simple_shadow,
    alignment="right",
)


class Style(ABC):
    @staticmethod
    @abstractmethod
    def apply(points: List[SpeedPoint]) -> List[TitleShape]:
        ...

class Default(Style):
    @staticmethod
    def apply(points: List[SpeedPoint]) -> List[TitleShape]:
        
        initial_time = points[0].time
        titles = []
        for i in range(len(points) - 1):
            start_time = titles[-1].end_time if len(titles) > 0 else time()
            
            dt = (points[i+1].time - initial_time).total_seconds()
            end_time = seconds_to_time(dt)
            
            # speed title
            text = f"""⏱ {points[i].speed_kmh:.1f} km/h"""
            titles.append(
                TitleShape(
                    text_style_ref=f"ts{i + 1}-speed",
                    start_time=start_time,
                    lane=1,
                    end_time=end_time,
                    text=text,
                    font_style=default_font_style,
                    x=-480.0,
                    y=-400.0,
                )
            )

            # elevation caption
            text = f"⛰︎ {int(points[i].ele)} m"
            titles.append(
                TitleShape(
                    text_style_ref=f"ts{i + 1}-elevation",
                    start_time=start_time,
                    lane=2,
                    end_time=end_time,
                    text=text,
                    font_style=default_font_style,
                    x=880.0,
                    y=-400.0,
                )
            )
        return titles

class TemplateRegistry:
    @staticmethod
    def apply(points: List[SpeedPoint], template: str = "default") -> List[TitleShape]:
        templates = {
            "default": Default,
        }

        
        temp = templates.get(template)
        if temp is None:
            raise ValueError(f"Unknown template {template}. Available templates: {templates.keys()}")

        return temp.apply(points)