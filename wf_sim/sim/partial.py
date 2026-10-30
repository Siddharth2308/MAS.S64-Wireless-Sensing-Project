"""Geometric mmWave visibility model -> partial point cloud.

A simplified model inspired by Wave-Former's published description, NOT
Wave-Former's simulator. Per surface sample p with normal n:

  1. best aperture point a* = argmin over a of angle(n, a - p), with n.(a-p) > 0
  2. level L = R0_dB(material) - 10 log10(e) (delta / lobe)^2   [dB re metal plate]
  3. detected if L >= thresh_db
  4. occlusion: ray p + eps n -> a* must not hit the mesh
     (transmission=True: dielectric faces pass with two-way interface loss,
      metal faces always block)
"""
import numpy as np
import trimesh

from . import geometry, materials as mat

DEFAULT_APERTURE = dict(size=(0.60, 0.45), spacing=0.02, height=0.40)


def _best_aperture(points, normals, ap, chunk=4096):
    """Max cos(n, a - p) over aperture points, and its index (chunked)."""
    n = len(points)
    best_cos = np.empty(n, dtype=np.float32)
    best_idx = np.empty(n, dtype=np.int64)
    ap_sq = (ap ** 2).sum(axis=1)
    for s in range(0, n, chunk):
        p, nr = points[s:s + chunk], normals[s:s + chunk]
        # n.(a - p) / |a - p| as (c, M) matrices, without the (c, M, 3) array
        dot = nr @ ap.T - (nr * p).sum(axis=1, keepdims=True)
        dist_sq = (p ** 2).sum(axis=1, keepdims=True) - 2 * p @ ap.T + ap_sq
        cos = (dot / np.sqrt(dist_sq)).astype(np.float32)
        best_idx[s:s + chunk] = cos.argmax(axis=1)
        best_cos[s:s + chunk] = cos.max(axis=1)
    return best_cos, best_idx


def _transmission(mesh, face_mat, origins, dirs, extra_loss_db):
    """Per ray: (blocked_by_metal, total two-way loss in dB, <= 0)."""
    blocked = np.zeros(len(origins), dtype=bool)
    loss = np.zeros(len(origins))
    if len(origins) == 0:
        return blocked, loss
    locs, iray, itri = mesh.ray.intersects_location(origins, dirs, multiple_hits=True)
    if len(iray) == 0:
        return blocked, loss
    # drop duplicate hits where a ray crosses a shared edge/vertex
    t = np.linalg.norm(locs - origins[iray], axis=1)
    _, keep = np.unique(np.column_stack([iray, np.round(t / 1e-5)]), axis=0, return_index=True)
    iray, itri = iray[keep], itri[keep]
    hit_mat = face_mat[itri]
    metal = np.array([mat.is_metal(m) for m in hit_mat])
    blocked[iray[metal]] = True
    per_hit = np.array([mat.transmission_loss_db(m) if not mat.is_metal(m) else 0.0
                        for m in hit_mat]) - extra_loss_db
    np.add.at(loss, iray, per_hit)
    return blocked, loss


def simulate_partial(obj, pose=(0.0, 0.0), materials=None, aperture=None,
                     n_points=20000, lobe_deg=mat.DEFAULT_LOBE_DEG,
                     thresh_db=mat.DEFAULT_THRESH_DB, transmission=False,
                     extra_loss_db=0.0, noise_sigma=0.002, seed=0, eps=1e-4):
    """Simulate one planar-aperture scan of `obj` (a sim.objects.SimObject).

    pose: (yaw_deg, tilt_deg). materials: None (object defaults), a material
    name (uniform) or a dict part -> material. Surface samples are drawn in
    the object frame with `seed`, so sample i is the same surface point at
    every pose (needed for union coverage across scans).
    """
    ap_cfg = {**DEFAULT_APERTURE, **(aperture or {})}
    face_mat = obj.face_material(materials)

    pts0, fidx = trimesh.sample.sample_surface(obj.mesh, n_points, seed=seed)
    T = geometry.pose_transform(obj.mesh, *pose)
    points, normals = geometry.apply_transform(T, pts0, obj.mesh.face_normals[fidx])
    posed = obj.mesh.copy()
    posed.apply_transform(T)

    z_ap = posed.bounds[1, 2] + ap_cfg["height"]
    ap = geometry.aperture_grid(z_ap, ap_cfg["size"], ap_cfg["spacing"])

    best_cos, best_idx = _best_aperture(points, normals, ap)
    front = best_cos > 0
    delta = np.degrees(np.arccos(np.clip(best_cos, -1, 1)))

    sample_mat = face_mat[fidx]
    r0 = np.array([mat.r0_db(m) for m in sample_mat])
    level = mat.received_level_db(r0, delta, lobe_deg)
    cand = np.flatnonzero(front & (level >= thresh_db))

    dirs = ap[best_idx[cand]] - points[cand]
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    origins = points[cand] + eps * normals[cand]

    visible = np.zeros(n_points, dtype=bool)
    if transmission:
        blocked, loss = _transmission(posed, face_mat, origins, dirs, extra_loss_db)
        level[cand] += loss
        visible[cand] = ~blocked & (level[cand] >= thresh_db)
    elif len(cand):
        visible[cand] = ~posed.ray.intersects_any(origins, dirs)

    part_ids = obj.face_part[fidx]
    coverage_by_part = {name: float(visible[part_ids == i].mean())
                        for i, name in enumerate(obj.part_names)}

    rng = np.random.default_rng(seed + 1)
    partial = points[visible] + rng.normal(0.0, noise_sigma, (visible.sum(), 3))

    return dict(points=points, normals=normals, visible_mask=visible,
                part_ids=part_ids, partial=partial, delta_deg=delta,
                level_db=level, coverage_total=float(visible.mean()),
                coverage_by_part=coverage_by_part, aperture=ap)
