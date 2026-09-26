#include "jarvis/fc/attitude.hpp"

#include <stdexcept>

#include "jarvis/fc/quat_math.hpp"

namespace jarvis::fc {

namespace {
constexpr Vec3 kWorldDownEnu{0.0, 0.0, -1.0};
// C37 — this estimator's own documented world-north reference, already
// horizontal (Up=0) by convention; matches mag.hpp's own kWorldMagFieldEnu
// (independently defined, not shared via include — same pattern this
// codebase already uses for the gravity constant across plant.cpp/
// attitude.cpp).
constexpr Vec3 kWorldMagNorthEnu{0.0, 1.0, 0.0};
}  // namespace

ComplementaryAttitudeEstimator::ComplementaryAttitudeEstimator(double gain, Quat initial_q, double mag_gain)
    : gain_(gain), mag_gain_(mag_gain), initial_q_(quat::normalize(initial_q)) {
    if (!(gain > 0.0 && gain <= 1.0)) {
        throw std::invalid_argument("gain must be in (0, 1]");
    }
    if (!(mag_gain > 0.0 && mag_gain <= 1.0)) {
        throw std::invalid_argument("mag_gain must be in (0, 1]");
    }
}

void ComplementaryAttitudeEstimator::reset() {
    q_.reset();
    last_t_s_.reset();
}

AttitudeState ComplementaryAttitudeEstimator::update(const ImuSample& sample, std::optional<MagSample> mag) {
    const Vec3& omega = sample.gyro_rad_s;

    if (!q_.has_value()) {
        q_ = initial_q_;
        last_t_s_ = sample.t_s;
        return AttitudeState{sample.t_s, *q_, omega};
    }

    double dt = sample.t_s - *last_t_s_;
    last_t_s_ = sample.t_s;
    if (dt <= 0.0) {
        return AttitudeState{sample.t_s, *q_, omega};
    }

    Vec3 axis_angle{omega[0] * dt, omega[1] * dt, omega[2] * dt};
    Quat q_pred = quat::normalize(quat::multiply(*q_, quat::from_small_angle(axis_angle)));

    Vec3 accel_dir;
    Quat q_new;
    if (!quat::vec_normalize(sample.accel_mps2, accel_dir)) {
        q_new = q_pred;
    } else {
        Vec3 predicted_down_body = quat::rotate_vector(quat::conjugate(q_pred), kWorldDownEnu);
        // Cross product is anti-commutative: this argument order (measured,
        // predicted) is the one that yields a correction pulling
        // predicted_down_body toward accel_dir; the reversed order silently
        // converges away from it. (Same fix as the Python C11 Amendment A.)
        Vec3 error = quat::cross(accel_dir, predicted_down_body);
        Vec3 correction{gain_ * error[0], gain_ * error[1], gain_ * error[2]};
        q_new = quat::normalize(quat::multiply(q_pred, quat::from_small_angle(correction)));
    }

    if (mag.has_value()) {
        // C37 — optional yaw correction. Rotate the measured body mag
        // vector into world frame using the tilt-corrected estimate
        // (q_new above, roll/pitch already trusted), keep only the
        // horizontal component (only that carries a heading reference;
        // never coupled back into roll/pitch).
        Vec3 world_mag = quat::rotate_vector(q_new, mag->mag_body_uT);
        Vec3 measured_horizontal{world_mag[0], world_mag[1], 0.0};
        Vec3 measured_horizontal_dir;
        if (quat::vec_normalize(measured_horizontal, measured_horizontal_dir)) {
            // Cross product is anti-commutative: this order (measured,
            // reference) yields a correction that rotates the measured
            // horizontal heading toward kWorldMagNorthEnu — mirrors the
            // accel branch's own (measured, predicted) convention above.
            // Both operands are horizontal (Up=0), so the result is
            // purely a Z-axis (yaw) rotation by construction.
            Vec3 yaw_error = quat::cross(measured_horizontal_dir, kWorldMagNorthEnu);
            Vec3 yaw_correction{mag_gain_ * yaw_error[0], mag_gain_ * yaw_error[1], mag_gain_ * yaw_error[2]};
            // World-frame correction: composed on the LEFT of q_new (q
            // represents body->world; rotating world-frame vectors by R
            // means q_corrected = R * q, not q * R — the reverse of the
            // accel branch's own body-frame correction above).
            q_new = quat::normalize(quat::multiply(quat::from_small_angle(yaw_correction), q_new));
        }
    }

    q_ = q_new;
    return AttitudeState{sample.t_s, q_new, omega};
}

}  // namespace jarvis::fc
