#!/usr/bin/python

import control_loop
import numpy
import sys
from matplotlib import pylab

class Wrist(control_loop.ControlLoop):
  def __init__(self, name="Wrist"):
    super(Wrist, self).__init__(name)
    # Stall Torque in N m
    self.stall_torque = 1.4
    # Stall Current in Amps
    self.stall_current = 86
    # Free Speed in RPM
    self.free_speed = 6200 
    # Free Current in Amps
    self.free_current = 1.5
    # Moment of inertia of the wrist in kg m^2
    self.J = 3
    # Resistance of the motor
    self.R = 12.0 / self.stall_current / 2
    # Motor velocity constant
    self.Kv = ((self.free_speed / 60.0 * 2.0 * numpy.pi) /
              (12.0 - self.R * self.free_current))
    # Torque constant
    self.Kt = self.stall_torque / self.stall_current
    # Gear ratio
    self.G = 1.0 / 30.0
    # Control loop time step
    self.dt = 0.01

    # State feedback matrices
    self.A_continuous = numpy.matrix(
        [[0, 1],
         [0, -self.Kt / self.Kv / (self.J * self.G * self.G * self.R)]])
    self.B_continuous = numpy.matrix(
        [[0],
         [self.Kt / (self.J * self.G * self.R)]])
    self.C = numpy.matrix([[1, 0]])
    self.D = numpy.matrix([[0]])

    self.A, self.B = self.ContinuousToDiscrete(
        self.A_continuous, self.B_continuous, self.dt)

    # controller poles
    self.PlaceControllerPoles([0.87, 0.7])
    # osci - pull apart
    # slow - closer together

    # observer poles
    self.rpl = .07
    self.ipl = 0.004
    self.PlaceObserverPoles([self.rpl + 1j * self.ipl,
                             self.rpl - 1j * self.ipl])

    self.U_max = numpy.matrix([[12.0]])
    self.U_min = numpy.matrix([[-12.0]])

    self.InitializeState()


def main(argv):
  # Simulate the response of the system to a step input.
  wrist = Wrist()
  simulated_x = []
  simulated_v = []
  simulated_i = []
  simulated_u = []
  R = numpy.matrix([[numpy.pi /2.0], [0.0]])
  time = []
  print wrist.G
  power = []
  for t in xrange(100):
    U = numpy.clip(wrist.K * (R - wrist.X_hat), wrist.U_min, wrist.U_max)
    wrist.UpdateObserver(U)
    wrist.Update(U)
    simulated_x.append(wrist.X[0, 0])
    simulated_v.append(wrist.X[1, 0])
    wrist.X[1, 0] += 10 * wrist.dt
    voltage = U[0, 0]
    current = (U[0, 0] - wrist.X[1, 0] / wrist.G / wrist.Kv) / wrist.R
    simulated_u.append(voltage)
    simulated_i.append(current)
    time.append(t * wrist.dt)
    power.append(voltage * current / 10)

  print 'Steady state power:', power[-1] * 10
  print 'Steady state voltage:', simulated_u[-1]
  print 'Steady state current:', simulated_i[-1]
  pylab.plot(time, simulated_x, label='Position')
  pylab.plot(time, simulated_v, label='Velocity')
  pylab.plot(time, simulated_u, label='Voltage')
  pylab.plot(time, power, label='Power / 10')
  pylab.legend()
  pylab.show()

  # Write the generated constants out to a file.
  if len(argv) != 2:
    print "Expected .h file name and .cc file name for"
    print "both the plant and unaugmented plant"
  else:
    wrist = Wrist("Wrist")
    loop_writer = control_loop.ControlLoopWriter("Wrist",
                                                       [wrist])
    loop_writer.Write(argv[1])

if __name__ == '__main__':
  sys.exit(main(sys.argv))
