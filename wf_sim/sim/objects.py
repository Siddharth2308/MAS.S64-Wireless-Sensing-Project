"""Procedural test objects with per-face part labels and a part -> material map.

Axisymmetric parts are built by revolving an (r, z) profile, which gives
closed, consistently oriented surfaces. Hollow parts (jar body, mug) have
real inner walls so that transmission through a glass wall can reveal them.
"""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import trimesh

MESH_DIR = Path(__file__).resolve().parent.parent / "meshes"
SECTIONS = 64


@dataclass
class SimObject:
    name: str
    mesh: trimesh.Trimesh
    face_part: np.ndarray       # (F,) int part index per face
    part_names: list
    part_material: dict         # part name -> material name

    def face_material(self, override=None):
        """Material name per face. `override` is a material name (uniform) or
        a dict part name -> material."""
        if isinstance(override, str):
            mats = {p: override for p in self.part_names}
        else:
            mats = {**self.part_material, **(override or {})}
        names = np.array([mats[p] for p in self.part_names])
        return names[self.face_part]


def _revolve(profile):
    m = trimesh.creation.revolve(np.asarray(profile, dtype=float), sections=SECTIONS)
    m.fix_normals()
    return m


def _cup_profile(r_out, height, wall, bottom, z0=0.0):
    """Closed (r, z) outline of an open-top cup with finite wall thickness."""
    r_in = r_out - wall
    return [(0, z0), (r_out, z0), (r_out, z0 + height), (r_in, z0 + height),
            (r_in, z0 + bottom), (0, z0 + bottom)]


def _disc_profile(r, z0, h):
    return [(0, z0), (r, z0), (r, z0 + h), (0, z0 + h)]


def _torus_segment(center, R, r, u_range=(-np.pi / 2, np.pi / 2), nu=24, nv=16):
    """Open tube along a circular arc in the xz-plane (a mug handle)."""
    us = np.linspace(*u_range, nu)
    vs = np.linspace(0, 2 * np.pi, nv, endpoint=False)
    U, V = np.meshgrid(us, vs, indexing="ij")
    ring = R + r * np.cos(V)
    verts = np.stack([ring * np.cos(U), r * np.sin(V), ring * np.sin(U)], -1)
    verts = verts.reshape(-1, 3) + center
    faces = []
    for i in range(nu - 1):
        for j in range(nv):
            a, b = i * nv + j, i * nv + (j + 1) % nv
            c, d = a + nv, b + nv
            faces += [[a, c, b], [b, c, d]]
    mesh = trimesh.Trimesh(verts, np.array(faces), process=False)
    # orient each face away from the tube's centerline
    u_mid = np.arctan2(mesh.triangles_center[:, 2] - center[2],
                       mesh.triangles_center[:, 0] - center[0])
    axis_pt = center + R * np.column_stack([np.cos(u_mid), np.zeros_like(u_mid), np.sin(u_mid)])
    flip = np.einsum("ij,ij->i", mesh.face_normals, mesh.triangles_center - axis_pt) < 0
    f = mesh.faces.copy()
    f[flip] = f[flip][:, ::-1]
    return trimesh.Trimesh(verts, f, process=False)


def _assemble(name, parts, part_material):
    """parts: list of (part_name, mesh)."""
    meshes = [m for _, m in parts]
    face_part = np.concatenate([np.full(len(m.faces), i) for i, m in enumerate(meshes)])
    mesh = trimesh.util.concatenate(meshes)
    return SimObject(name, mesh, face_part, [p for p, _ in parts], part_material)


def bottle():
    body = _revolve([(0, 0), (0.035, 0), (0.035, 0.16), (0.012, 0.19),
                     (0.012, 0.22), (0, 0.22)])
    cap = _revolve(_disc_profile(0.014, 0.22, 0.015))
    return _assemble("bottle", [("body", body), ("cap", cap)],
                     {"body": "PET", "cap": "PP"})


def mug():
    r_out, h = 0.04, 0.10
    body = _revolve(_cup_profile(r_out, h, wall=0.004, bottom=0.006))
    handle = _torus_segment(np.array([r_out - 0.003, 0.0, h / 2]), R=0.028, r=0.006)
    return _assemble("mug", [("body", body), ("handle", handle)],
                     {"body": "glass", "handle": "glass"})


def jar_lid():
    h = 0.11
    body = _revolve(_cup_profile(0.045, h, wall=0.004, bottom=0.005))
    lid = _revolve(_disc_profile(0.047, h, 0.015))
    return _assemble("jar_lid", [("body", body), ("lid", lid)],
                     {"body": "glass", "lid": "metal"})


def box():
    m = trimesh.creation.box(extents=(0.20, 0.15, 0.10))
    m.apply_translation([0, 0, 0.05])
    return _assemble("box", [("box", m)], {"box": "metal"})


PROCEDURAL = {"bottle": bottle, "mug": mug, "jar_lid": jar_lid, "box": box}


def mesh_object(path, material="metal"):
    """Load a user mesh (e.g. YCB .stl/.obj) as a single-part object."""
    m = trimesh.load(path, force="mesh")
    return _assemble(Path(path).stem, [("object", m)], {"object": material})


def mesh_names(mesh_dir=MESH_DIR):
    files = sorted(Path(mesh_dir).glob("*.stl")) + sorted(Path(mesh_dir).glob("*.obj"))
    return [f.stem for f in files]


def get_object(name, mesh_dir=MESH_DIR):
    if name in PROCEDURAL:
        return PROCEDURAL[name]()
    for ext in (".stl", ".obj"):
        path = Path(mesh_dir) / f"{name}{ext}"
        if path.exists():
            return mesh_object(path)
    raise KeyError(f"unknown object {name!r}")


def all_object_names(include_meshes=True):
    return list(PROCEDURAL) + (mesh_names() if include_meshes else [])
