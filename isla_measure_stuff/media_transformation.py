from dataclasses import dataclass
from typing import Tuple

import numpy as np

from .euclidean import Line, angle_between, rotate_vector


@dataclass
class ImageTransformations:
    rotation: float
    rotation_dimensions: np.ndarray
    scale: float
    position: np.ndarray


def match_measurement_lines(image_dimensions: np.ndarray, origin_measure: Line, dest_measure: Line):
    assert(image_dimensions.shape == (2,))
    image_center = image_dimensions / 2

    # Rotation
    rotation = angle_between(dest_measure.vector, origin_measure.vector)
    rotated_width = rotate_vector(np.array([image_dimensions[0], 0]), rotation)
    rotated_height = rotate_vector(np.array([0, image_dimensions[1]]), rotation)
    rotation_dimensions = np.array([
        abs(rotated_width[0]) + abs(rotated_height[0]),
        abs(rotated_width[1]) + abs(rotated_height[1])
    ])

    # Scale
    scale = np.linalg.norm(dest_measure.vector) / np.linalg.norm(origin_measure.vector)

    # Position
    image_dim_increase = scale * rotation_dimensions / image_dimensions
    new_center = image_center * image_dim_increase
    transformed_start_position = new_center + scale * rotate_vector(origin_measure.begin - image_center, rotation)
    position = dest_measure.begin - transformed_start_position

    return ImageTransformations(
        rotation,
        rotation_dimensions,
        scale,
        position
    )


def fit_video(
        video_dims: np.ndarray, image_trans: ImageTransformations,
        isla_boundaries: Tuple[int, int], rescale_limit: float):
    assert(video_dims.shape == (2,))

    image_total_height = video_dims[1] - image_trans.position[1]
    # If image height is greater than the video height then scale it down
    y_rescale = min(1, video_dims[1] / image_total_height)

    image_x_end = image_trans.position[0] + image_trans.rotation_dimensions[0] * image_trans.scale
    x_min = min(isla_boundaries[0], image_trans.position[0])
    x_max = max(isla_boundaries[1], image_x_end)
    total_width = x_max - x_min
    # If the total width of the image with Isla is greater than the video width then scale it down
    x_rescale = min(1, video_dims[0] / total_width)

    rescale = max(min(x_rescale, y_rescale), rescale_limit)

    # Centralize image
    new_x_min = (video_dims[0] - rescale * total_width) / 2
    x_increase = new_x_min - rescale * x_min
    # Assuming Isla has the same dimensions as the video and she is initially at position (0,0)
    isla_x = x_increase
    isla_y = video_dims[1] - (video_dims[1] * rescale)

    image_x = rescale * image_trans.position[0] + x_increase
    image_y = image_trans.position[1] + image_total_height - (image_total_height * rescale)

    # Fit Isla
    scaled_boundaries = np.array(isla_boundaries) * rescale
    if isla_x + scaled_boundaries[0] < 0:
        x_increase = -scaled_boundaries[0] - isla_x
        isla_x += x_increase
        image_x += x_increase

    if isla_x + scaled_boundaries[1] > video_dims[0]:
        x_decrease = scaled_boundaries[1] - video_dims[0]
        isla_x -= x_decrease
        image_x -= x_decrease

    return ImageTransformations(
        image_trans.rotation,
        image_trans.rotation_dimensions,
        rescale * image_trans.scale,
        np.array([image_x, image_y])
    ), rescale, np.array([isla_x, isla_y])
