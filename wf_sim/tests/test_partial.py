import numpy as np
import pytest
import trimesh

from sim import geometry, materials as mat, objects
from sim.partial import DEFAULT_APERTURE, simulate_partial


def _single(name, mesh, material="metal"):
    return objects._assemble(name, [("part", mesh)], {"part": material})


def _plate(size=0.10, thick=0.004):
    m = trimesh.creation.box(extents=(size, size, thick))
    m.apply_translation([0, 0, thick / 2])
    return _single("plate", m)


def _face_mask(res, normal_world):
    return res["normals"] @ normal_world > 0.99


def test_plate_facing_up():
    res = simulate_partial(_plate(), pose=(0, 0), n_points=5000)
    up = _face_mask(res, np.array([0, 0, 1.0]))
    down = _face_mask(res, np.array([0, 0, -1.0]))
    assert res["visible_mask"][up].mean() > 0.98
    assert res["visible_mask"][down].mean() == 0.0


def test_plate_tilted_beyond_cutoff():
    # tilt about x moves the normal in the y-z plane; the aperture half-angle
    # in y is atan(0.225 / 0.40) ~ 29 deg, so the limit is ~17 + 29 = 46 deg
    half_angle = np.degrees(np.arctan(DEFAULT_APERTURE["size"][1] / 2 / DEFAULT_APERTURE["height"]))
    tilt = mat.cutoff_deg("metal") + half_angle + 15
    res = simulate_partial(_plate(), pose=(0, tilt), n_points=5000)
    top = _face_mask(res, geometry.pose_rotation(0, tilt) @ np.array([0, 0, 1.0]))
    assert res["visible_mask"][top].mean() < 0.01


def test_sphere_matches_spherical_cap():
    r = 0.02
    sphere = _single("sphere", trimesh.creation.icosphere(subdivisions=4, radius=r))
    res = simulate_partial(sphere, pose=(0, 0), n_points=20000, seed=1)

    # expected: fraction of normals within the cutoff of some direction from
    # the sphere's center to the aperture (ignores parallax across the sphere)
    rng = np.random.default_rng(0)
    n = rng.normal(size=(20000, 3))
    n /= np.linalg.norm(n, axis=1, keepdims=True)
    ap = geometry.aperture_grid(2 * r + DEFAULT_APERTURE["height"],
                                DEFAULT_APERTURE["size"], DEFAULT_APERTURE["spacing"])
    d = ap - np.array([0, 0, r])
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    min_angle = np.degrees(np.arccos(np.clip((n @ d.T).max(axis=1), -1, 1)))
    expected = (min_angle <= mat.cutoff_deg("metal")).mean()
    assert res["coverage_total"] == pytest.approx(expected, rel=0.15)


def test_cube_under_plate_is_occluded():
    plate = trimesh.creation.box(extents=(0.20, 0.20, 0.005))
    plate.apply_translation([0, 0, 0.05])
    cube = trimesh.creation.box(extents=(0.02, 0.02, 0.02))
    cube.apply_translation([0, 0, 0.01])
    obj = objects._assemble("occ", [("plate", plate), ("cube", cube)],
                            {"plate": "metal", "cube": "metal"})
    res = simulate_partial(obj, pose=(0, 0), n_points=10000)
    assert res["coverage_by_part"]["cube"] == 0.0
    assert res["coverage_by_part"]["plate"] > 0.3


@pytest.mark.parametrize("name", ["bottle", "sphere"])
def test_material_ordering(name):
    if name == "sphere":
        obj = _single("sphere", trimesh.creation.icosphere(subdivisions=4, radius=0.03))
    else:
        obj = objects.get_object(name)
    cov = [simulate_partial(obj, pose=(0, 15), materials=m, n_points=10000)["coverage_total"]
           for m in ["metal", "glass", "PET", "PP"]]
    assert cov == sorted(cov, reverse=True)
    if name == "sphere":
        assert cov[0] > cov[-1]


def test_metal_lid_blocks_even_with_transmission():
    jar = objects.get_object("jar_lid")
    res = simulate_partial(jar, pose=(0, 0), transmission=True, n_points=10000)
    assert res["coverage_by_part"]["body"] == 0.0


def test_transmission_reveals_inner_glass_wall():
    jar = objects.get_object("jar_lid")
    kw = dict(pose=(0, 90), n_points=10000)
    off = simulate_partial(jar, transmission=False, **kw)["coverage_by_part"]["body"]
    on = simulate_partial(jar, transmission=True, **kw)["coverage_by_part"]["body"]
    assert on > off


def test_sheet_model_limits():
    eps, f0 = 2.6, 79e9
    n = np.sqrt(eps)
    lam_in = 299_792_458.0 / f0 / n * 1e3                    # mm inside the sheet
    r_half, _ = mat.slab_coefficients(eps, lam_in / 2, f0)   # half-wave sheet: no reflection
    assert abs(r_half) ** 2 < 1e-6
    r_q, t_q = mat.slab_coefficients(eps, lam_in / 4, f0)    # quarter-wave: maximum
    assert abs(r_q) ** 2 == pytest.approx(((1 - eps) / (1 + eps)) ** 2, rel=1e-6)
    assert abs(r_q) ** 2 + abs(t_q) ** 2 == pytest.approx(1.0)   # lossless: energy conserved
    r_lossy, t_lossy = mat.slab_coefficients(eps, 3.0, f0, tan_delta=0.02)
    assert abs(r_lossy) ** 2 + abs(t_lossy) ** 2 < 1.0       # absorption removes energy
