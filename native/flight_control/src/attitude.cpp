#include "jarvis/fc/attitude.hpp"

#include <stdexcept>

#include "jarvis/fc/quat_math.hpp"

namespace jarvis::fc {

namespace {
constexpr Vec3 kWorldDownEnu{0.0, 0.0, -1.0};
}  // namespace

ComplementaryAttitudeEstimator::ComplementaryAttitudeEstimator(double gain, Quat initial_q)
    : gain_(gain), initial_q_(quat::normalize(initial_q)) {
    if (!(gain > 0.0 && gain <= 1.0)) {
        throw std::invalid_argument("gain must be in (0, 1]");
    }
}

void ComplementaryAttitudeEstimator::reset() {
    q_.reset();
    last_t_s_.reset();
}

AttitudeState ComplementaryAttitudeEstimator::update(const ImuSample& sample) {
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

    q_ = q_new;
    return AttitudeState{sample.t_s, q_new, omega};
}

}  // namespace jarvis::fc
