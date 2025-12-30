import argparse
from pathlib import Path
from typing import Optional

from ski.config import AnimationSettings, SettingsFactory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animate a marker moving along a GPX track"
    )
    parser.add_argument(
        "gpx_file",
        nargs="?",
        help="Path to the GPX file (can also be provided via --config)",
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML config file with animation defaults",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        type=str,
        default=None,
        help="Output file",
    )
    parser.add_argument(
        "--track", type=int, default=None, help="Select track id <track>."
    )
    parser.add_argument(
        "--segment",
        type=int,
        default=None,
        help="Select the segment with id <segment> from track <track>.",
    )
    parser.add_argument(
        "--template",
        dest="template",
        type=str,
        default=None,
        help="Title style template",
    )
    parser.add_argument(
        "--interpolate",
        dest="interpolate",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Interpolate positions between GPX timestamps",
    )
    parser.add_argument(
        "--interpolation-step",
        dest="interpolation_step",
        type=float,
        default=None,
        help="Seconds between interpolated samples (when interpolation is enabled)",
    )
    parser.add_argument(
        "--duration",
        dest="duration",
        type=float,
        default=None,
        help="Handful control to limit duration (in seconds) of produced file.",
    )
    parser.add_argument(
        "-f",
        "--fps",
        dest="fps",
        type=int,
        default=None,
        help="Frames per second",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action='store_true',
        help="Increase output verbosity."
    )
    return parser


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def build_settings(args: argparse.Namespace) -> AnimationSettings:
    cli_overrides = {
        key: value
        for key, value in vars(args).items()
        if key not in {"config"} and value is not None
    }

    config_path = Path(args.config) if args.config else None
    return SettingsFactory.from_sources(cli_overrides, config_path)
