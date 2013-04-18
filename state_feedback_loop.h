#ifndef FRC971_CONTROL_LOOPS_STATEFEEDBACKLOOP_H_
#define FRC971_CONTROL_LOOPS_STATEFEEDBACKLOOP_H_

#include <assert.h>

#include <vector>

// Stupid vxworks system headers define it which blows up Eigen...
#undef m_data

#include "Eigen/Dense"

template <int number_of_states, int number_of_inputs, int number_of_outputs>
class StateFeedbackPlantCoefficients {
 public:
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW;

  const Eigen::Matrix<double, number_of_states, number_of_states> A;
  const Eigen::Matrix<double, number_of_states, number_of_inputs> B;
  const Eigen::Matrix<double, number_of_outputs, number_of_states> C;
  const Eigen::Matrix<double, number_of_outputs, number_of_inputs> D;
  const Eigen::Matrix<double, number_of_inputs, 1> U_min;
  const Eigen::Matrix<double, number_of_inputs, 1> U_max;

  StateFeedbackPlantCoefficients(const StateFeedbackPlantCoefficients &other)
      : A(other.A),
        B(other.B),
        C(other.C),
        D(other.D),
        U_min(other.U_min),
        U_max(other.U_max) {
  }

  StateFeedbackPlantCoefficients(
      const Eigen::Matrix<double, number_of_states, number_of_states> &A,
      const Eigen::Matrix<double, number_of_states, number_of_inputs> &B,
      const Eigen::Matrix<double, number_of_outputs, number_of_states> &C,
      const Eigen::Matrix<double, number_of_outputs, number_of_inputs> &D,
      const Eigen::Matrix<double, number_of_outputs, 1> &U_max,
      const Eigen::Matrix<double, number_of_outputs, 1> &U_min)
      : A(A),
        B(B),
        C(C),
        D(D),
        U_min(U_min),
        U_max(U_max) {
  }

 protected:
  // these are accessible from non-templated subclasses
  static const int kNumStates = number_of_states;
  static const int kNumOutputs = number_of_outputs;
  static const int kNumInputs = number_of_inputs;
};

template <int number_of_states, int number_of_inputs, int number_of_outputs>
class StateFeedbackPlant {
 public:
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW;
  ::std::vector<StateFeedbackPlantCoefficients<
      number_of_states, number_of_inputs, number_of_outputs> *> coefficients_;

  const Eigen::Matrix<double, number_of_states, number_of_states> &A() const {
    return coefficients().A;
  }
  double A(int i, int j) const { return A()(i, j); }
  const Eigen::Matrix<double, number_of_states, number_of_inputs> &B() const {
    return coefficients().B;
  }
  double B(int i, int j) const { return B()(i, j); }
  const Eigen::Matrix<double, number_of_outputs, number_of_states> &C() const {
    return coefficients().C;
  }
  double C(int i, int j) const { return C()(i, j); }
  const Eigen::Matrix<double, number_of_outputs, number_of_inputs> &D() const {
    return coefficients().D;
  }
  double D(int i, int j) const { return D()(i, j); }
  const Eigen::Matrix<double, number_of_inputs, 1> &U_min() const {
    return coefficients().U_min;
  }
  double U_min(int i, int j) const { return U_min()(i, j); }
  const Eigen::Matrix<double, number_of_inputs, 1> &U_max() const {
    return coefficients().U_max;
  }
  double U_max(int i, int j) const { return U_max()(i, j); }

  const StateFeedbackPlantCoefficients<
      number_of_states, number_of_inputs, number_of_outputs>
          &coefficients() const {
    return *coefficients_[plant_index_];
  }

  int plant_index() const { return plant_index_; }
  void set_plant_index(int plant_index) {
    if (plant_index < 0) {
      plant_index_ = 0;
    } else if (plant_index >= static_cast<int>(coefficients_.size())) {
      plant_index_ = static_cast<int>(coefficients_.size()) - 1;
    } else {
      plant_index_ = plant_index;
    }
  }

  void Reset() {
    X.setZero();
    Y.setZero();
    U.setZero();
  }

  Eigen::Matrix<double, number_of_states, 1> X;
  Eigen::Matrix<double, number_of_outputs, 1> Y;
  Eigen::Matrix<double, number_of_inputs, 1> U;

  StateFeedbackPlant(
      const ::std::vector<StateFeedbackPlantCoefficients<
          number_of_states, number_of_inputs,
          number_of_outputs> *> &coefficients)
      : coefficients_(coefficients),
        plant_index_(0) {
    Reset();
  }

  StateFeedbackPlant(StateFeedbackPlant &&other)
      : plant_index_(0) {
    Reset();
    ::std::swap(coefficients_, other.coefficients_);
  }

  virtual ~StateFeedbackPlant() {}

  // Assert that U is within the hardware range.
  virtual void CheckU() {
    for (int i = 0; i < kNumOutputs; ++i) {
      assert(U(i, 0) <= U_max(i, 0));
      assert(U(i, 0) >= U_min(i, 0));
    }
  }

  // Computes the new X and Y given the control input.
  void Update() {
    // Powers outside of the range are more likely controller bugs than things
    // that the plant should deal with.
    CheckU();
    X = A() * X + B() * U;
    Y = C() * X + D() * U;
  }

 protected:
  // these are accessible from non-templated subclasses
  static const int kNumStates = number_of_states;
  static const int kNumOutputs = number_of_outputs;
  static const int kNumInputs = number_of_inputs;

 private:
  int plant_index_;
};

// A Controller is a structure which holds a plant and the K and L matrices.
// This is designed such that multiple controllers can share one set of state to
// support gain scheduling easily.
template <int number_of_states, int number_of_inputs, int number_of_outputs>
struct StateFeedbackController {
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW;
  const Eigen::Matrix<double, number_of_states, number_of_outputs> L;
  const Eigen::Matrix<double, number_of_outputs, number_of_states> K;
  StateFeedbackPlantCoefficients<number_of_states, number_of_inputs,
                                 number_of_outputs> plant;

  StateFeedbackController(
      const Eigen::Matrix<double, number_of_states, number_of_outputs> &L,
      const Eigen::Matrix<double, number_of_outputs, number_of_states> &K,
      const StateFeedbackPlantCoefficients<number_of_states, number_of_inputs,
                                           number_of_outputs> &plant)
      : L(L),
        K(K),
        plant(plant) {
  }
};

template <int number_of_states, int number_of_inputs, int number_of_outputs>
class StateFeedbackLoop {
 public:
  EIGEN_MAKE_ALIGNED_OPERATOR_NEW;

  const Eigen::Matrix<double, number_of_states, number_of_states> &A() const {
    return controller().plant.A;
  }
  double A(int i, int j) const { return A()(i, j); }
  const Eigen::Matrix<double, number_of_states, number_of_inputs> &B() const {
    return controller().plant.B;
  }
  double B(int i, int j) const { return B()(i, j); }
  const Eigen::Matrix<double, number_of_outputs, number_of_states> &C() const {
    return controller().plant.C;
  }
  double C(int i, int j) const { return C()(i, j); }
  const Eigen::Matrix<double, number_of_outputs, number_of_inputs> &D() const {
    return controller().plant.D;
  }
  double D(int i, int j) const { return D()(i, j); }
  const Eigen::Matrix<double, number_of_outputs, number_of_states> &K() const {
    return controller().K;
  }
  double K(int i, int j) const { return K()(i, j); }
  const Eigen::Matrix<double, number_of_states, number_of_outputs> &L() const {
    return controller().L;
  }
  double L(int i, int j) const { return L()(i, j); }
  const Eigen::Matrix<double, number_of_inputs, 1> &U_min() const {
    return controller().plant.U_min;
  }
  double U_min(int i, int j) const { return U_min()(i, j); }
  const Eigen::Matrix<double, number_of_inputs, 1> &U_max() const {
    return controller().plant.U_max;
  }
  double U_max(int i, int j) const { return U_max()(i, j); }

  Eigen::Matrix<double, number_of_states, 1> X_hat;
  Eigen::Matrix<double, number_of_states, 1> R;
  Eigen::Matrix<double, number_of_inputs, 1> U;
  Eigen::Matrix<double, number_of_inputs, 1> U_uncapped;
  Eigen::Matrix<double, number_of_outputs, 1> U_ff;
  Eigen::Matrix<double, number_of_outputs, 1> Y;

  ::std::vector<StateFeedbackController<number_of_states, number_of_inputs,
                                        number_of_outputs> *> controllers_;

  const StateFeedbackController<
      number_of_states, number_of_inputs, number_of_outputs>
          &controller() const {
    return *controllers_[controller_index_];
  }

  void Reset() {
    X_hat.setZero();
    R.setZero();
    U.setZero();
    U_uncapped.setZero();
    U_ff.setZero();
    Y.setZero();
  }

  StateFeedbackLoop(
      const StateFeedbackController<number_of_states, number_of_inputs,
                                    number_of_outputs> &controller)
      : controller_index_(0) {
    controllers_.push_back(
        new StateFeedbackController<number_of_states, number_of_inputs,
                                    number_of_outputs>(controller));
    Reset();
  }

  StateFeedbackLoop(
      const ::std::vector<StateFeedbackController<
          number_of_states, number_of_inputs,
          number_of_outputs> *> &controllers)
      : controllers_(controllers),
        controller_index_(0) {
    Reset();
  }

  StateFeedbackLoop(
      const Eigen::Matrix<double, number_of_states, number_of_outputs> &L,
      const Eigen::Matrix<double, number_of_outputs, number_of_states> &K,
      const StateFeedbackPlantCoefficients<number_of_states, number_of_inputs,
                               number_of_outputs> &plant)
      : controller_index_(0) {
    controllers_.push_back(
        new StateFeedbackController<number_of_states, number_of_inputs,
                                    number_of_outputs>(L, K, plant));

    Reset();
  }
  virtual ~StateFeedbackLoop() {}

  virtual void FeedForward() {
    for (int i = 0; i < number_of_outputs; ++i) {
      U_ff[i] = 0.0;
    }
  }

  // If U is outside the hardware range, limit it before the plant tries to use
  // it.
  virtual void CapU() {
    for (int i = 0; i < kNumOutputs; ++i) {
      if (U(i, 0) > U_max(i, 0)) {
        U(i, 0) = U_max(i, 0);
      } else if (U(i, 0) < U_min(i, 0)) {
        U(i, 0) = U_min(i, 0);
      }
    }
  }

  // update_observer is whether or not to use the values in Y.
  // stop_motors is whether or not to output all 0s.
  void Update(bool update_observer, bool stop_motors) {
    if (stop_motors) {
      U.setZero();
    } else {
      U = U_uncapped = K() * (R - X_hat);
      CapU();
    }

    if (update_observer) {
      X_hat = (A() - L() * C()) * X_hat + L() * Y + B() * U;
    } else {
      X_hat = A() * X_hat + B() * U;
    }
  }

  // Sets the current controller to be index and verifies that it isn't out of
  // range.
  void set_controller_index(int index) {
    if (index < 0) {
      controller_index_ = 0;
    } else if (index >= static_cast<int>(controllers_.size())) {
      controller_index_ = static_cast<int>(controllers_.size()) - 1;
    } else {
      controller_index_ = index;
    }
  }

  void controller_index() const { return controller_index_; }

 protected:
  // these are accessible from non-templated subclasses
  static const int kNumStates = number_of_states;
  static const int kNumOutputs = number_of_outputs;
  static const int kNumInputs = number_of_inputs;

  int controller_index_;
};

#endif  // FRC971_CONTROL_LOOPS_STATEFEEDBACKLOOP_H_
