import numpy as np


class Line:
    def __init__(self, begin: np.ndarray, end: np.ndarray) -> None:
        assert(begin.shape == end.shape)
        self.begin = begin
        self.end = end

    @property
    def vector(self):
        return self.end - self.begin

    @property
    def shape(self):
        return self.begin.shape


def angle_between(v1: np.ndarray, v2: np.ndarray):
    unit_v1 = v1 / np.linalg.norm(v1)
    unit_v2 = v2 / np.linalg.norm(v2)
    angle = np.arctan2(*unit_v2) - np.arctan2(*unit_v1)
    return angle


def rotate_vector(v: np.ndarray, angle: float):
    rot = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    return np.dot(rot, v)
