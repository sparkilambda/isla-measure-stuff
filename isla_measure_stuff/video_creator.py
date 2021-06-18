from dataclasses import dataclass
from enum import Enum
from functools import cached_property
from typing import Tuple

import ffmpeg
from ffmpeg.nodes import Stream
import numpy as np

from .euclidean import Line
from .media_transformation import ImageTransformations, match_measurement_lines, fit_video
from .constants import BG_IMAGE_FILE, ISLA_RESCALE_LIMIT


@dataclass
class IslaMeasurementData:
    filename: str
    measure_position: Line
    boundaries: Tuple[int, int]

    @cached_property
    def fps(self):
        metadata = ffmpeg.probe(self.filename)
        video_streams = [s for s in metadata['streams'] if s['codec_type'] == 'video']
        fps = video_streams[0]['r_frame_rate']
        return fps


class MeasurementType(Enum):
    BIG = 'big'
    SMALL = 'small'

    def get_isla_data(self) -> IslaMeasurementData:
        return _DATA_FOR_TYPE[self]


_DATA_FOR_TYPE = {
    MeasurementType.BIG: IslaMeasurementData(
        filename='resources/IslaBig.mov',
        measure_position=Line(np.array([1240, 490]), np.array([1873, 487])),
        boundaries=(510, 1900)
    ),
    MeasurementType.SMALL: IslaMeasurementData(
        filename='resources/IslaSmall.mov',
        measure_position=Line(np.array([1381, 740]), np.array([1496, 740])),
        boundaries=(510, 1530)
    )
}


def create_video(input_image_path, measure_type: MeasurementType, measurement: Line, output_path: str):
    assert(measurement.shape == (2,))

    isla_data = measure_type.get_isla_data()

    bg_image = ffmpeg.input(BG_IMAGE_FILE).filter('fps', isla_data.fps)

    image_transformations = match_measurement_lines(
        np.array(_get_media_dimensions(input_image_path)),
        measurement,
        isla_data.measure_position
    )

    fit_image_transformations, isla_scale, isla_position = fit_video(
        np.array(_get_media_dimensions(BG_IMAGE_FILE)),
        image_transformations,
        isla_data.boundaries,
        ISLA_RESCALE_LIMIT
    )

    transformed_image = _transform_image(
        ffmpeg.input(input_image_path),
        bg_image,
        fit_image_transformations
    )

    isla_stream = ffmpeg.input(isla_data.filename)
    generated_video = _overlay_isla(
        transformed_image,
        isla_stream,
        isla_scale,
        isla_position
    )
    out = ffmpeg.output(generated_video, isla_stream.audio, output_path)
    out.run()


def _transform_image(image_stream: Stream, bg_image: Stream, image_trans: ImageTransformations) -> Stream:
    transformed_image = image_stream \
        .filter(
            'rotate',
            image_trans.rotation,
            ow=image_trans.rotation_dimensions[0],
            oh=image_trans.rotation_dimensions[1]
        ) \
        .filter('scale', f'in_w*{image_trans.scale}', f'in_h*{image_trans.scale}')

    positioned_image = ffmpeg.overlay(bg_image, transformed_image, x=image_trans.position[0], y=image_trans.position[1])
    return positioned_image


def _overlay_isla(image_stream: Stream, isla_stream: Stream, isla_scale: float, isla_position: np.ndarray) -> Stream:
    scaled_isla = isla_stream.filter('scale', f'in_w*{isla_scale}', f'in_h*{isla_scale}')
    return ffmpeg.overlay(image_stream, scaled_isla, x=isla_position[0], y=isla_position[1])


def _get_media_dimensions(media_path: str) -> Tuple[int, int]:
    metadata = ffmpeg.probe(media_path)
    video_metadata = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
    width = video_metadata['coded_width']
    height = video_metadata['coded_height']
    return (width, height)
