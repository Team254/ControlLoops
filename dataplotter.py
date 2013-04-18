#!/usr/bin/python

import numpy
import math
import sys
from matplotlib import pylab

def main(argv):
  # Simulate the response of the system to a step input.
  shooter_data = []
  line_number = 0
  with open(argv[1], 'r') as fd:
    for line in fd:
      line_number += 1
      line = line.strip()
      if line[0:2] == 'D:' and line[-2:] == ':D':
        line = line[2:-2]
        numbers = line.split(',')
        if len(numbers) != 3:
          print 'Error on line number', line_number
        else:
          shooter_data.append(numpy.matrix([[float(n) for n in numbers]]))
    shooter_data = numpy.vstack(shooter_data)

  voltage = []
  real_x = []
  initial_t = shooter_data[0, 0]
  time = []
  for i in xrange(shooter_data.shape[0]):
    voltage.append(shooter_data[i, 1] * 1000)
    real_x.append(shooter_data[i, 2] * 2.0 * math.pi / 60.0)
    time.append(shooter_data[i, 0] - initial_t)

  pylab.plot(time, voltage, label='Voltage')
  pylab.plot(time, real_x, label='Reality')
  pylab.legend()
  pylab.show()


if __name__ == '__main__':
  sys.exit(main(sys.argv))
