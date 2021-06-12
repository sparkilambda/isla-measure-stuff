import argparse

import numpy as np

from .euclidean import Line
from .video_creator import MeasurementType, create_video


def parse_args():
    parser = argparse.ArgumentParser(
        description='Adds the video of Isla Coleman measuring something ' +
        'in the given image based on the given positions.'
    )

    parser.add_argument('input', type=str, help='Input image path.')
    parser.add_argument('--type', type=str, required=True)  # TODO
    parser.add_argument('--measurement', nargs='+', type=int, required=True)  # TODO
    parser.add_argument('--output', type=str, required=True)  # TODO

    return parser.parse_args()


def main():
    args = parse_args()

    measure_type = MeasurementType(args.type.lower())
    measurement = Line(
        np.array([args.measurement[0], args.measurement[1]]),
        np.array([args.measurement[2], args.measurement[3]])
    )

    create_video(
        args.input,
        measure_type,
        measurement,
        args.output
    )


if __name__ == '__main__':
    main()
