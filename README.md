# I am Speed

## Project Description

This is a Final Cut Pro tool to create Speed metrics (and other metadata) from GPX into FCP.

![Sample video](imgs/ski_small.gif "Sample Clip")

In this example, the data was captured using the app [Slopes](https://getslopes.com/).

## Usage

```bash
uv run create_fcpxml <gpx_file>
```
or
```bash
python src.ski
```

## Collecting GPX points and calculating speed

Luckily for us GPX file is a well-behaved file and [gpxpy](https://github.com/tkrajina/gpxpy) is pretty handy.
A GPX file contains tracks, each track contains a list of segments, each segment contains a list of track points.

```python
# we can then simplify the representation of a point with the only essential information
class Point(BaseModel):
    time: Optional[datetime] = None
    lat: float
    lon: float
    ele: float
```

The only problem is that I had data points in intervals of 1 to 2 seconds.
To create a cool more realistic smooth animation, I needed more data points, so before creating shapes, we need to interpolate the distances.

## FCP Shapes

FCPXML file, in the other hand, is not so well-behaved, and I didn't want to spend too much time digging into the Final Cut Pro development world in this first moment.
So basically I created 3-4 frames in FCP manually, with the formatting I wanted and exported it.
From there I had a header, a footer and the shape XML with Timecode definition.

To represent a Title Shape, I created the following definition:

```python
class TitleShape(BaseModel):
    text_style_ref: str
    start_time: time # the time code of the first frame
    end_time: time  # the time code of the last frame
    text: str
    font_style: FontStyle = FontStyle()
    lane: int = Field(default=1)
    x: float = Field(default=0.0)
    y: float = Field(default=0.0)
```

For what I needed, there were not too much styling to add to the text, so I could represent the styling as:

```python
class FontStyle(BaseModel):
    font: fonts = "Helvetica"
    font_size: int = 60
    font_face: font_faces = "Regular"
    font_color: RGBAColor = RGBAColor(red=1, green=1, blue=1, alpha=1.0)
    shadow: ShadowProperties | None = None
    alignment: Literal["left", "center", "right"] = "right"
    bold: int = 0
```

## Putting all together

For every single speed point we can then create a single title shape in Final Cut Pro and export a _.fcpxml_ file.

In Final Cut Pro: `File -> Import XML -> Select .fcpxml`.

## Next

### Data Model Refactor
While writing this README, I realize I am not using gpxpy in my favor, and just added a huge amount of overload into data representation with two ways of representing data points. 
A refactor here will be appreciated.

### FCPXML final result

When creating a big file (more than ~20k shapes) it gets pretty painful to upload into FCP and edit the clip, sync, etc.
I believe it could be better done, if I could directly export a clip composition, so I would have only one object to manipulate in my FCP project.

### DaVinci Resolve support

Why not extending support to other tools?

### Can I render directly?

In the end, I dont need the individual objects to render and manipulate in my video editing tool, I only need a clip with the speed animation.
Can I build the end-to-end pipeline that receives a GPX file, and export the video?



