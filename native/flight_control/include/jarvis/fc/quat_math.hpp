// Fase C · C13 — shared quaternion helpers.
//
// **Documented deviation from the Python ladder (disclosed in the C13
// report):** the Python rungs (`attitude.py`, `plant.py`) each keep a
// small private copy of these helpers, matching this project's
// established per-module-private-helpers style. In this first C++ Buy
// they are factored into one shared internal header instead, purely to
// avoid duplicating ~40 lines of numerically-identical arithmetic across
// two translation units in a brand-new tree — this is a code-organization
// choice only, not a behavioral or algorithmic difference. Same (w, x, y,
// z) convention, same formulas.
#pragma once

#include <algorithm>
#include <cmath>

#include "jarvis/fc/types.hpp"

namespace jarvis::fc::quat {

inline Quat normalize(const Quat& q) {
    double norm = std::sqrt(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z);
    if (norm < 1e-12) {
        return Quat{1.0, 0.0, 0.0, 0.0};
    }
    return Quat{q.w / norm, q.x / norm, q.y / norm, q.z / norm};
}

inline Quat multiply(const Quat& a, const Quat& b) {
    return Quat{
        a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
        a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
        a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
        a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
    };
}

inline Quat conjugate(const Quat& q) { return Quat{q.w, -q.x, -q.y, -q.z}; }

inline Quat from_small_angle(const Vec3& axis_angle) {
    return normalize(Quat{1.0, axis_angle[0] / 2.0, axis_angle[1] / 2.0, axis_angle[2] / 2.0});
}

inline Vec3 rotate_vector(const Quat& q, const Vec3& v) {
    Quat qv{0.0, v[0], v[1], v[2]};
    Quat result = multiply(multiply(q, qv), conjugate(q));
    return Vec3{result.x, result.y, result.z};
}

// Returns `false` (leaving `out` untouched) when `v` is too close to zero
// to normalize — mirrors Python's `_vec_normalize(...) -> Vec3 | None`.
inline bool vec_normalize(const Vec3& v, Vec3& out) {
    double norm = std::sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
    if (norm < 1e-9) {
        return false;
    }
    out = Vec3{v[0] / norm, v[1] / norm, v[2] / norm};
    return true;
}

inline Vec3 cross(const Vec3& a, const Vec3& b) {
    return Vec3{
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    };
}

}  // namespace jarvis::fc::quat
