"""Material table, Fresnel reflectivity and the dB-threshold -> cutoff mapping.

All permittivities are approximate real values at 77-81 GHz (assumptions,
see README). Metal is treated as a perfect conductor (|Gamma| = 1).

Two reflectivity models:
- half-space (r0_*): a single air/material interface, i.e. thick material.
  This is what the simulator uses.
- thin sheet (slab_*): a sheet of finite thickness, where reflections from
  its front and back faces interfere. Used to compare with measurements of
  real sheets and container walls.
"""
import numpy as np

# name -> relative permittivity (None = perfect conductor)
MATERIALS = {
    "metal": None,
    "glass": 6.0,
    "PET": 3.0,
    "PP": 2.3,
    "acrylic": 2.6,   # PMMA
}

BAND_GHZ = (77.0, 81.0)
C = 299_792_458.0

DEFAULT_LOBE_DEG = 8.0
DEFAULT_THRESH_DB = -20.0

# 10*log10(e): converts the Gaussian lobe exp(-(D/lobe)^2) into dB
_DB_PER_NEPER2 = 10.0 * np.log10(np.e)


def is_metal(material):
    return MATERIALS[material] is None


def fresnel_power(eps, theta_deg):
    """Power reflectivity (R_TE, R_TM) for a planar air/dielectric interface."""
    theta = np.radians(np.asarray(theta_deg, dtype=float))
    if eps is None:
        one = np.ones_like(theta)
        return one, one
    cos_t = np.cos(theta)
    root = np.sqrt(eps - np.sin(theta) ** 2)
    g_te = (cos_t - root) / (cos_t + root)
    g_tm = (eps * cos_t - root) / (eps * cos_t + root)
    return g_te ** 2, g_tm ** 2


def r0_linear(material):
    """Normal-incidence power reflectivity."""
    eps = MATERIALS[material]
    if eps is None:
        return 1.0
    return float(((1 - np.sqrt(eps)) / (1 + np.sqrt(eps))) ** 2)


def r0_db(material):
    return 10.0 * np.log10(r0_linear(material))


def brewster_deg(material):
    eps = MATERIALS[material]
    return None if eps is None else float(np.degrees(np.arctan(np.sqrt(eps))))


def received_level_db(material_r0_db, delta_deg, lobe_deg=DEFAULT_LOBE_DEG):
    """Level relative to a metal plate at normal incidence (dB)."""
    return material_r0_db - _DB_PER_NEPER2 * (np.asarray(delta_deg) / lobe_deg) ** 2


def cutoff_deg(material, lobe_deg=DEFAULT_LOBE_DEG, thresh_db=DEFAULT_THRESH_DB):
    """Largest specular deviation still detected: solves L(delta) = thresh."""
    margin = r0_db(material) - thresh_db
    if margin <= 0:
        return 0.0
    return float(lobe_deg * np.sqrt(np.log(10) / 10 * margin))


def transmission_loss_db(material):
    """Two-way loss crossing one interface of `material` (negative dB)."""
    return 2 * 10.0 * np.log10(1.0 - r0_linear(material))


def slab_coefficients(eps, thickness_mm, freq_hz, tan_delta=0.0):
    """Normal-incidence (reflection, transmission) amplitude of a sheet in air.

    eps may be given with a loss tangent; the sheet is treated as a
    Fabry-Perot slab (multiple internal reflections summed exactly).
    """
    n = np.sqrt(eps * (1 - 1j * tan_delta))
    g = (1 - n) / (1 + n)
    phase = np.exp(-1j * 2 * np.pi * np.asarray(freq_hz) * n * thickness_mm * 1e-3 / C)
    denom = 1 - g ** 2 * phase ** 2
    refl = g * (1 - phase ** 2) / denom
    trans = (1 - g ** 2) * phase / denom
    return refl, trans


def sheet_prediction(material, thickness_mm, tan_delta=0.0, band_ghz=BAND_GHZ, n_freq=401):
    """Model predictions for a flat sheet at normal incidence, in dB relative
    to a metal plate: half-space R0, band-averaged thin-sheet reflectivity
    (with its min/max across the band) and two-way transmission."""
    eps = MATERIALS[material]
    f = np.linspace(band_ghz[0], band_ghz[1], n_freq) * 1e9
    refl, trans = slab_coefficients(eps, thickness_mm, f, tan_delta)
    R = np.abs(refl) ** 2
    T2 = np.abs(trans) ** 4                                  # through and back
    db = lambda x: float(10 * np.log10(x))
    return dict(material=material, eps=eps, thickness_mm=thickness_mm, tan_delta=tan_delta,
                halfspace_R0_dB=round(float(r0_db(material)), 2),
                sheet_R_dB=round(db(R.mean()), 2),
                sheet_R_min_dB=round(db(R.min()), 2), sheet_R_max_dB=round(db(R.max()), 2),
                sheet_two_way_transmission_dB=round(db(T2.mean()), 2))
