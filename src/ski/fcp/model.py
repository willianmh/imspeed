from datetime import time
from typing import List, Literal
from pydantic import BaseModel, Field, model_serializer


class RGBAColor(BaseModel):
    red: int
    green: int
    blue: int
    alpha: float

    @model_serializer(mode="plain")
    def serialize_model(self) -> str:
        return f"{self.red} {self.green} {self.blue} {self.alpha}"


class ShadowOffset(BaseModel):
    distance: float
    angle: float

    @model_serializer(mode="plain")
    def serialize_model(self) -> str:
        return f"{self.distance} {self.angle}"


class ShadowProperties(BaseModel):
    color: RGBAColor = RGBAColor(red=0, green=0, blue=0, alpha=0.7)
    offset: ShadowOffset = ShadowOffset(distance=5.0, angle=315.0)
    blur_radius: float = 1.0

    def xml(self) -> str:
        return str(" ").join(
            [
                f'shadowColor="{self.color.model_dump()}"',
                f'shadowOffset="{self.offset.model_dump()}"',
                f'shadowBlurRadius="{self.blur_radius}"',
            ]
        )


fonts = Literal["Helvetica", "Unbounded"]
font_faces = Literal["Regular", "Medium", "SemiBold", "Bold"]


class FontStyle(BaseModel):
    font: fonts = "Helvetica"
    font_size: int = 60
    font_face: font_faces = "Regular"
    font_color: RGBAColor = RGBAColor(red=1, green=1, blue=1, alpha=1.0)
    shadow: ShadowProperties | None = None
    alignment: Literal["left", "center", "right"] = "right"
    bold: int = 0

    def xml(self) -> str:
        return str(" ").join(
            [
                "<text-style ",
                f'font="{self.font}"',
                f'fontSize="{self.font_size}"',
                f'fontFace="{self.font_face}"',
                f'fontColor="{self.font_color.model_dump()}"',
                f'alignment="{self.alignment}"',
                'bold="1"' if self.bold == 1 else "",
                self.shadow.xml() if self.shadow is not None else "",
                "/>",
            ]
        )


class TitleShape(BaseModel):
    text_style_ref: str
    start_time: time
    end_time: time
    text: str
    font_style: FontStyle = FontStyle()
    lane: int = Field(default=1)
    x: float = Field(default=0.0)
    y: float = Field(default=0.0)

    def xml(self, time_base, offset_units, start_units, duration_units) -> List[str]:
        lines = [
            f'              <title ref="r2" lane="{self.lane}" name="ts{self.text_style_ref} - Basic Title" offset="{offset_units}/{time_base}s" start="{start_units}/{time_base}s" duration="{duration_units}/{time_base}s">',
            f'                <param name="Position" key="9999/999166631/999166633/1/100/101" value="{self.x} {self.y}"/>',
            '                <param name="Flatten" key="9999/999166631/999166633/2/351" value="1"/>',
            '                <param name="Alignment" key="9999/999166631/999166633/2/354/999169573/401" value="2 (Right)"/>',
            '                <param name="Alignment" key="9999/999166631/999166633/2/354/999210390/401" value="2 (Right)"/>',
            '                <param name="Alignment" key="9999/999166631/999166633/2/354/999210391/401" value="2 (Right)"/>',
            '                <param name="disableDRT" key="3733" value="1"/>',
            "                <text>",
            f'                  <text-style ref="ts{self.text_style_ref}">{self.text}</text-style>',
            "                </text>",
            f'                <text-style-def id="ts{self.text_style_ref}">',
            f"                  {self.font_style.xml()}"
            "                </text-style-def>",
            "              </title>",
        ]
        return lines
