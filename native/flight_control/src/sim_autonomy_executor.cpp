// Fase C · C40 — implementation of `jarvis::fc::SimAutonomyExecutor`.
//
// Host scaffold only. See include/jarvis/fc/sim_autonomy_executor.hpp
// and the Python twin's own module docstring for the full honesty
// statement and verb-map derivation. No GPIO/PWM/DShot, no Safety call,
// no C4 command-surface symbol anywhere in this file.
#include "jarvis/fc/sim_autonomy_executor.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace jarvis::fc {

SimAutonomyExecutor::SimAutonomyExecutor(ToyQuad6DofPlant& plant, double z_land_m, double land_rate_mps)
    : plant_(plant), z_land_m_(z_land_m), land_rate_mps_(land_rate_mps), sample_(plant.sense()) {
    if (!std::isfinite(z_land_m)) {
        throw std::invalid_argument("z_land_m must be finite");
    }
    if (!std::isfinite(land_rate_mps) || land_rate_mps <= 0.0) {
        throw std::invalid_argument("land_rate_mps must be finite and > 0");
    }
}

SimAutonomyTickResult SimAutonomyExecutor::tick(SimAutonomyVerb verb, const SimAutonomyParams& params, double dt_s) {
    if (!std::isfinite(dt_s) || dt_s <= 0.0) {
        throw std::invalid_argument("dt_s must be finite and > 0");
    }
    if (params.x_m.has_value() && !std::isfinite(*params.x_m)) {
        throw std::invalid_argument("x_m must be finite");
    }
    if (params.y_m.has_value() && !std::isfinite(*params.y_m)) {
        throw std::invalid_argument("y_m must be finite");
    }
    if (params.z_m.has_value() && !std::isfinite(*params.z_m)) {
        throw std::invalid_argument("z_m must be finite");
    }

    if (!active_verb_.has_value() || *active_verb_ != verb) {
        hold_setpoint_.reset();
        hold_z_des_.reset();
        goto_z_des_.reset();
        land_setpoint_.reset();
        land_z_des_.reset();
        active_verb_ = verb;
    }

    Vec3 true_position = plant_.true_position_m();
    Vec3 true_velocity = plant_.true_velocity_mps();
    double true_x = true_position[0];
    double true_y = true_position[1];
    double true_z = true_position[2];
    double vx_mps = true_velocity[0];
    double vy_mps = true_velocity[1];
    double vz_mps = true_velocity[2];

    PositionSetpoint xy_setpoint{};
    double z_des_m = 0.0;

    if (verb == SimAutonomyVerb::kHold) {
        if (!hold_setpoint_.has_value()) {
            double x_des = params.x_m.value_or(true_x);
            double y_des = params.y_m.value_or(true_y);
            hold_setpoint_ = PositionSetpoint{x_des, y_des};
        }
        if (!hold_z_des_.has_value()) {
            hold_z_des_ = params.z_m.value_or(true_z);
        }
        xy_setpoint = *hold_setpoint_;
        z_des_m = *hold_z_des_;
    } else if (verb == SimAutonomyVerb::kGoTo) {
        if (!params.x_m.has_value() || !params.y_m.has_value()) {
            throw std::invalid_argument("GO_TO requires x_m and y_m params");
        }
        xy_setpoint = PositionSetpoint{*params.x_m, *params.y_m};
        if (!goto_z_des_.has_value()) {
            goto_z_des_ = params.z_m.value_or(true_z);
        }
        z_des_m = params.z_m.value_or(*goto_z_des_);
    } else {  // SimAutonomyVerb::kLand
        if (!land_setpoint_.has_value()) {
            double x_des = params.x_m.value_or(true_x);
            double y_des = params.y_m.value_or(true_y);
            land_setpoint_ = PositionSetpoint{x_des, y_des};
        }
        if (!land_z_des_.has_value()) {
            land_z_des_ = true_z;
        }
        double floor = params.z_m.value_or(z_land_m_);
        land_z_des_ = std::max(floor, *land_z_des_ - land_rate_mps_ * dt_s);
        xy_setpoint = *land_setpoint_;
        z_des_m = *land_z_des_;
    }

    PositionSample position = pos_hal_.read_position(true_x, true_y, sample_.t_s);
    AltitudeSample altitude = alt_hal_.read_altitude(true_z, sample_.t_s);
    AttitudeSetpoint setpoint = pos_controller_.compute(xy_setpoint, position, vx_mps, vy_mps, sample_.t_s);
    double collective = alt_controller_.compute(z_des_m, altitude, vz_mps);
    ControlTickResult tick_result = loop_.step(sample_, setpoint, collective);
    sample_ = plant_.step(tick_result.forces, dt_s);

    return SimAutonomyTickResult{
        sample_.t_s, verb, xy_setpoint, z_des_m, setpoint, collective, tick_result,
    };
}

}  // namespace jarvis::fc
