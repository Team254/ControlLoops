#include "frc971/control_loops/angle_adjust/unaugmented_angle_adjust_motor_plant.h"

#include <vector>

#include "frc971/control_loops/state_feedback_loop.h"

namespace frc971 {
namespace control_loops {

StateFeedbackPlantCoefficients<2, 1, 1> MakeAngleAdjustRawPlantCoefficients() {
  Eigen::Matrix<double, 2, 2> A;
  A << 1.0, 0.00844804908295, 0.0, 0.706562970689;
  Eigen::Matrix<double, 2, 1> B;
  B << 0.000186726546509, 0.0353055515475;
  Eigen::Matrix<double, 1, 2> C;
  C << 1, 0;
  Eigen::Matrix<double, 1, 1> D;
  D << 0;
  Eigen::Matrix<double, 1, 1> U_max;
  U_max << 12.0;
  Eigen::Matrix<double, 1, 1> U_min;
  U_min << -12.0;
  return StateFeedbackPlantCoefficients<2, 1, 1>(A, B, C, D, U_max, U_min);
}

StateFeedbackController<2, 1, 1> MakeAngleAdjustRawController() {
  Eigen::Matrix<double, 2, 1> L;
  L << 1.60656297069, 51.0341417582;
  Eigen::Matrix<double, 1, 2> K;
  K << 264.830871921, 10.681380124;
  return StateFeedbackController<2, 1, 1>(L, K, MakeAngleAdjustRawPlantCoefficients());
}

StateFeedbackPlant<2, 1, 1> MakeRawAngleAdjustPlant() {
  ::std::vector<StateFeedbackPlantCoefficients<2, 1, 1> *> plants(1);
  plants[0] = new StateFeedbackPlantCoefficients<2, 1, 1>(MakeAngleAdjustRawPlantCoefficients());
  return StateFeedbackPlant<2, 1, 1>(plants);
}

StateFeedbackLoop<2, 1, 1> MakeRawAngleAdjustLoop() {
  ::std::vector<StateFeedbackController<2, 1, 1> *> controllers(1);
  controllers[0] = new StateFeedbackController<2, 1, 1>(MakeAngleAdjustRawController());
  return StateFeedbackLoop<2, 1, 1>(controllers);
}

}  // namespace control_loops
}  // namespace frc971
