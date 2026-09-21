#include "jarvis/fc/plant.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

#include "jarvis/fc/quat_math.hpp"

namespace jarvis::fc {

namespace {
constexpr double kGravityMps2 = 9.81;
constexpr Vec3 kWorldGravityEnu{0.0, 0.0, -kGravityMps2};
}  // namespace

ToyQuadAttitudePlant::ToyQuadAttitudePlant(double torque_gain, double angular_damping)
    : torque_gain_(torque_gain), angular_damping_(angular_damping) {
    if (!std::isfinite(torque_gain) || torque_gain <= 0.0) {
        throw std::invalid_argument("torque_gain must be finite and > 0");
    }
    if (!std::isfinite(angular_damping) || angular_damping < 0.0) {
        throw std::invalid_argument("angular_damping must be finite and >= 0");
    }
}

void ToyQuadAttitudePlant::reset(Quat initial_q, Vec3 initial_omega) {
    q_ = quat::normalize(initial_q);
    omega_ = initial_omega;
    t_s_ = 0.0;
}

AttitudeState ToyQuadAttitudePlant::true_attitude() const {
    return AttitudeState{t_s_, q_, omega_};
}

ImuSample ToyQuadAttitudePlant::sense() const {
    return ImuSample{t_s_, quat::rotate_vector(quat::conjugate(q_), kWorldGravityEnu), omega_};
}

ImuSample ToyQuadAttitudePlant::step(const MotorForceCommand& forces, double dt_s) {
    if (!std::isfinite(dt_s) || dt_s <= 0.0) {
        throw std::invalid_argument("dt_s must be finite and > 0");
    }

    double fr = forces.motor_forces[0];
    double fl = forces.motor_forces[1];
    double rl = forces.motor_forces[2];
    double rr = forces.motor_forces[3];
    double roll_proxy = (fl + rl) - (fr + rr);
    double pitch_proxy = (fr + fl) - (rl + rr);
    double yaw_proxy = (fl + rr) - (fr + rl);

    Vec3 angular_accel{
        torque_gain_ * roll_proxy - angular_damping_ * omega_[0],
        torque_gain_ * pitch_proxy - angular_damping_ * omega_[1],
        torque_gain_ * yaw_proxy - angular_damping_ * omega_[2],
    };

    Vec3 new_omega{
        omega_[0] + angular_accel[0] * dt_s,
        omega_[1] + angular_accel[1] * dt_s,
        omega_[2] + angular_accel[2] * dt_s,
    };
    Vec3 axis_angle{new_omega[0] * dt_s, new_omega[1] * dt_s, new_omega[2] * dt_s};
    Quat new_q = quat::normalize(quat::multiply(q_, quat::from_small_angle(axis_angle)));

    omega_ = new_omega;
    q_ = new_q;
    t_s_ += dt_s;

    return ImuSample{t_s_, quat::rotate_vector(quat::conjugate(new_q), kWorldGravityEnu), new_omega};
}

double tilt_angle_rad(const Quat& q) {
    double w = std::max(-1.0, std::min(1.0, q.w));
    return 2.0 * std::acos(std::abs(w));
}

}  // namespace jarvis::fc
