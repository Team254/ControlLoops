#!/usr/bin/python

import numpy
import math
import sys
from matplotlib import pylab
import control_loop

class Shooter(control_loop.ControlLoop):
  def __init__(self, name="Shooter"):
    super(Shooter, self).__init__(name)
    # Stall Torque in N m
    self.stall_torque = 0.49819248
    # Stall Current in Amps
    self.stall_current = 85
    # Free Speed in RPM
    self.free_speed = 19300.0 - 4950.0
    # Free Current in Amps
    self.free_current = 1.4
    # Moment of inertia of the shooter wheel in kg m^2
    self.J = 0.00029
    # Resistance of the motor, divided by 2 to account for the 2 motors
    self.R = 12.0 / self.stall_current / 2
    # Motor velocity constant
    self.Kv = ((self.free_speed / 60.0 * 2.0 * numpy.pi) /
              (12.0 - self.R * self.free_current))
    # Torque constant
    self.Kt = self.stall_torque / self.stall_current
    # Gear ratio
    self.G = 11.0 / 14.0
    # Control loop time step
    self.dt = 0.01

    # State feedback matrices
    self.A_continuous = numpy.matrix(
        [[-self.Kt / self.Kv / (self.J * self.G * self.G * self.R)]])
    self.B_continuous = numpy.matrix(
        [[self.Kt / (self.J * self.G * self.R)]])
    self.C = numpy.matrix([[1]])
    self.D = numpy.matrix([[0]])

    self.A, self.B = self.ContinuousToDiscrete(
        self.A_continuous, self.B_continuous, self.dt)

    self.PlaceControllerPoles([.6])

    self.rpl = .45
    self.ipl = 0.07
    self.PlaceObserverPoles([0.3])

    self.U_max = numpy.matrix([[12.0]])
    self.U_min = numpy.matrix([[-2.0]])

    self.InitializeState()

class ShooterDeltaU(Shooter):
  def __init__(self, name="Shooter"):
    super(ShooterDeltaU, self).__init__(name)
    A_unaugmented = self.A
    B_unaugmented = self.B

    self.A = numpy.matrix([[1.0, 0.0],
                           [0.0, 0.0]])
    self.A[1:2, 1:2] = A_unaugmented
    self.A[1:2, 0:1] = B_unaugmented

    self.B = numpy.matrix([[1.0],
                           [0.0]])
   #self.B[1:2, 0:1] = B_unaugmented

    self.C = numpy.matrix([[0.0, 1.0]])
    self.D = numpy.matrix([[0.0]])

    self.PlaceControllerPoles([0.7, 0.32])

    print "K"
    print self.K
    print "Placed controller poles are"
    print numpy.linalg.eig(self.A - self.B * self.K)[0]

    self.rpl = .05
    self.ipl = 0.008
    self.PlaceObserverPoles([0.75, 0.8])
    print "Placed observer poles are"
    print numpy.linalg.eig(self.A - self.L * self.C)[0]

    self.U_max = numpy.matrix([[12.0]])
    self.U_min = numpy.matrix([[-2.0]])

    self.InitializeState()


def main(argv):
  # Simulate the response of the system to a step input.
  shooter_data = numpy.genfromtxt('shooter/shooter_data254.csv', delimiter=',')
  shooter = Shooter()
  simulated_v = []
  real_x = []
  voltage = []
  x_vel = []
  initial_t = shooter_data[0, 0]
  for i in xrange(shooter_data.shape[0]):
    voltage.append(shooter_data[i, 1] * 12.0 * 10)
    shooter.Update(numpy.matrix([[shooter_data[i, 1] * 12.0]]))
    simulated_v.append(shooter.X[0, 0])
    real_x.append(shooter_data[i, 2] * 2.0 * math.pi / 60.0)

  pylab.plot(range(shooter_data.shape[0]),
             voltage, label='Voltage')
  offset = 1
  pylab.plot(range(offset, shooter_data.shape[0] + offset),
             simulated_v, label='Simulation')
  pylab.plot(range(shooter_data.shape[0]), real_x, label='Reality')
  pylab.legend()
  pylab.show()

  if len(argv) != 3:
    print "Expected .java file names"
  else:
    shooter = ShooterDeltaU()
    loop_writer = control_loop.ControlLoopWriter("Shooter", [shooter])
    loop_writer.Write(argv[1])

    shooter = Shooter()
    loop_writer = control_loop.ControlLoopWriter("PlainShooter", [shooter])
    loop_writer.Write(argv[2])


if __name__ == '__main__':
  sys.exit(main(sys.argv))
