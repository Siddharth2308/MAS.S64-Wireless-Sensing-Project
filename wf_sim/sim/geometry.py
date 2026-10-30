"""Rotations, object posing and the synthetic-aperture grid.

Conventions (see README): meters, z up, degrees at the API boundary,
radians inside. Pose R = Rz(yaw) @ Rx(tilt), applied about the object's
centroid, then the object is re-seated so its lowest point is at z = 0 and
its bounding-box center is at x = y = 0.
"""
import numpy as np


def rot_x(deg):
    t = np.radians(deg)
    c, s = np.cos(t), np.sin(t)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_z(deg):
    t = np.radians(deg)
    c, s = np.cos(t), np.sin(t)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def pose_rotation(yaw_deg, tilt_deg):
    """Tilt about x first, then yaw about z."""
    return rot_z(yaw_deg) @ rot_x(tilt_deg)


def pose_transform(mesh, yaw_deg, tilt_deg):
    """4x4 transform that rotates `mesh` about its centroid and re-seats it."""
    R = pose_rotation(yaw_deg, tilt_deg)
    c = mesh.centroid
    v = (mesh.vertices - c) @ R.T + c
    lo, hi = v.min(axis=0), v.max(axis=0)
    shift = np.array([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = c - R @ c + shift
    return T


def apply_transform(T, points, normals):
    R = T[:3, :3]
    return points @ R.T + T[:3, 3], normals @ R.T


def aperture_grid(z, size=(0.60, 0.45), spacing=0.02, center_xy=(0.0, 0.0)):
    """Planar grid of monostatic radar positions at height z (M x 3).

    size[0] spans x, size[1] spans y.
    """
    nx = int(round(size[0] / spacing)) + 1
    ny = int(round(size[1] / spacing)) + 1
    xs = np.linspace(-size[0] / 2, size[0] / 2, nx) + center_xy[0]
    ys = np.linspace(-size[1] / 2, size[1] / 2, ny) + center_xy[1]
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    return np.column_stack([X.ravel(), Y.ravel(), np.full(X.size, z)])
