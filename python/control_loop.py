import controls
import numpy

class ControlLoopWriter(object):
  def __init__(self, gain_schedule_name, loops, namespaces=None):
    """Constructs a control loop writer.

    Args:
      gain_schedule_name: string, Name of the overall controller.
      loops: array[ControlLoop], a list of control loops to gain schedule
        in order.
      namespaces: array[string], a list of names of namespaces to nest in
        order.  If None, the default will be used.
    """
    self._gain_schedule_name = gain_schedule_name
    self._loops = loops
    if namespaces:
      self._namespaces = namespaces
    else:
      self._namespaces = ['frc971', 'control_loops']

    self._namespace_start = '\n'.join(
        ['namespace %s {' % name for name in self._namespaces])

    self._namespace_end = '\n'.join(
        ['}  // namespace %s' % name for name in reversed(self._namespaces)])

  def _HeaderGuard(self, header_file):
    return ('FRC971_CONTROL_LOOPS_' +
            header_file.upper().replace('.', '_').replace('/', '_') +
            '_')

  def Write(self, java_file):
    """Writes the loops to the specified files."""
    self.WriteJava(java_file)

  def _GenericType(self, typename):
    """Returns a loop template using typename for the type."""
    num_states = self._loops[0].A.shape[0]
    num_inputs = self._loops[0].B.shape[1]
    num_outputs = self._loops[0].C.shape[0]
    return '%s<%d, %d, %d>' % (
        typename, num_states, num_inputs, num_outputs)

  def _ControllerType(self):
    """Returns a template name for StateFeedbackController."""
    return self._GenericType('StateFeedbackController')

  def _LoopType(self):
    """Returns a template name for StateFeedbackLoop."""
    return self._GenericType('StateFeedbackLoop')

  def _PlantType(self):
    """Returns a template name for StateFeedbackPlant."""
    return self._GenericType('StateFeedbackPlant')

  def _CoeffType(self):
    """Returns a template name for StateFeedbackPlantCoefficients."""
    return self._GenericType('StateFeedbackPlantCoefficients')

  def WriteJava(self, java_file):
    """Writes the java file to the file named java_file."""
    with open(java_file, 'w') as fd:
      fd.write('package com.team254.frc2014;\n')
      fd.write('\n')
      fd.write('import com.team254.lib.StateSpaceGains;\n')
      fd.write('\n')
      fd.write('public class %sGains {\n' % self._gain_schedule_name)
      fd.write('  static public StateSpaceGains[] getGains() {\n')
      fd.write('    return new StateSpaceGains[] {\n')
      for loop in self._loops:
        fd.write(loop.DumpPlantJava())
      fd.write('        };\n')
      fd.write('  }\n')
      fd.write('}\n')

  def WriteHeader(self, header_file):
    """Writes the header file to the file named header_file."""
    with open(header_file, 'w') as fd:
      header_guard = self._HeaderGuard(header_file)
      fd.write('#ifndef %s\n'
               '#define %s\n\n' % (header_guard, header_guard))
      fd.write('#include \"frc971/control_loops/state_feedback_loop.h\"\n')
      fd.write('\n')

      fd.write(self._namespace_start)
      fd.write('\n\n')
      for loop in self._loops:
        fd.write(loop.DumpPlantHeader())
        fd.write('\n')
        fd.write(loop.DumpControllerHeader())
        fd.write('\n')

      fd.write('%s Make%sPlant();\n\n' %
               (self._PlantType(), self._gain_schedule_name))

      fd.write('%s Make%sLoop();\n\n' %
               (self._LoopType(), self._gain_schedule_name))

      fd.write(self._namespace_end)
      fd.write('\n\n')
      fd.write("#endif  // %s\n" % header_guard)

  def WriteCC(self, header_file_name, cc_file):
    """Writes the cc file to the file named cc_file."""
    with open(cc_file, 'w') as fd:
      fd.write('#include \"frc971/control_loops/%s\"\n' % header_file_name)
      fd.write('\n')
      fd.write('#include <vector>\n')
      fd.write('\n')
      fd.write('#include \"frc971/control_loops/state_feedback_loop.h\"\n')
      fd.write('\n')
      fd.write(self._namespace_start)
      fd.write('\n\n')
      for loop in self._loops:
        fd.write(loop.DumpPlant())
        fd.write('\n')

      for loop in self._loops:
        fd.write(loop.DumpController())
        fd.write('\n')

      fd.write('%s Make%sPlant() {\n' %
               (self._PlantType(), self._gain_schedule_name))
      fd.write('  ::std::vector<%s *> plants(%d);\n' % (
          self._CoeffType(), len(self._loops)))
      for index, loop in enumerate(self._loops):
        fd.write('  plants[%d] = new %s(%s);\n' %
                 (index, self._CoeffType(),
                  loop.PlantFunction()))
      fd.write('  return %s(plants);\n' % self._PlantType())
      fd.write('}\n\n')

      fd.write('%s Make%sLoop() {\n' %
               (self._LoopType(), self._gain_schedule_name))
      fd.write('  ::std::vector<%s *> controllers(%d);\n' % (
          self._ControllerType(), len(self._loops)))
      for index, loop in enumerate(self._loops):
        fd.write('  controllers[%d] = new %s(%s);\n' %
                 (index, self._ControllerType(),
                  loop.ControllerFunction()))
      fd.write('  return %s(controllers);\n' % self._LoopType())
      fd.write('}\n\n')

      fd.write(self._namespace_end)
      fd.write('\n')


class ControlLoop(object):
  def __init__(self, name):
    """Constructs a control loop object.

    Args:
      name: string, The name of the loop to use when writing the C++ files.
    """
    self._name = name

  def ContinuousToDiscrete(self, A_continuous, B_continuous, dt):
    """Calculates the discrete time values for A and B.

      Args:
        A_continuous: numpy.matrix, The continuous time A matrix
        B_continuous: numpy.matrix, The continuous time B matrix
        dt: float, The time step of the control loop

      Returns:
        (A, B), numpy.matrix, the control matricies.
    """
    return controls.c2d(A_continuous, B_continuous, dt)

  def InitializeState(self):
    """Sets X, Y, and X_hat to zero defaults."""
    self.X = numpy.zeros((self.A.shape[0], 1))
    self.Y = self.C * self.X
    self.X_hat = numpy.zeros((self.A.shape[0], 1))

  def PlaceControllerPoles(self, poles):
    """Places the controller poles.

    Args:
      poles: array, An array of poles.  Must be complex conjegates if they have
        any imaginary portions.
    """
    self.K = controls.dplace(self.A, self.B, poles)

  def PlaceObserverPoles(self, poles):
    """Places the observer poles.

    Args:
      poles: array, An array of poles.  Must be complex conjegates if they have
        any imaginary portions.
    """
    self.L = controls.dplace(self.A.T, self.C.T, poles).T

  def Update(self, U):
    """Simulates one time step with the provided U."""
    U = numpy.clip(U, self.U_min, self.U_max)
    self.X = self.A * self.X + self.B * U
    self.Y = self.C * self.X + self.D * U

  def UpdateObserver(self, U):
    """Updates the observer given the provided U."""
    self.X_hat = (self.A * self.X_hat + self.B * U +
                  self.L * (self.Y - self.C * self.X_hat - self.D * U))

  def _DumpMatrix(self, matrix_name, matrix):
    """Dumps the provided matrix into a variable called matrix_name.

    Args:
      matrix_name: string, The variable name to save the matrix to.
      matrix: The matrix to dump.

    Returns:
      string, The C++ commands required to populate a variable named matrix_name
        with the contents of matrix.
    """
    ans = ['  Eigen::Matrix<double, %d, %d> %s;\n' % (
        matrix.shape[0], matrix.shape[1], matrix_name)]
    first = True
    for x in xrange(matrix.shape[0]):
      for y in xrange(matrix.shape[1]):
	element = matrix[x, y]
        if first:
          ans.append('  %s << ' % matrix_name)
          first = False
        else:
          ans.append(', ')
        ans.append(str(element))

    ans.append(';\n')
    return ''.join(ans)

  def DumpPlantHeader(self):
    """Writes out a c++ header declaration which will create a Plant object.

    Returns:
      string, The header declaration for the function.
    """
    num_states = self.A.shape[0]
    num_inputs = self.B.shape[1]
    num_outputs = self.C.shape[0]
    return 'StateFeedbackPlantCoefficients<%d, %d, %d> Make%sPlantCoefficients();\n' % (
        num_states, num_inputs, num_outputs, self._name)

  def DumpPlant(self):
    """Writes out a c++ function which will create a PlantCoefficients object.

    Returns:
      string, The function which will create the object.
    """
    num_states = self.A.shape[0]
    num_inputs = self.B.shape[1]
    num_outputs = self.C.shape[0]
    ans = ['StateFeedbackPlantCoefficients<%d, %d, %d>'
           ' Make%sPlantCoefficients() {\n' % (
        num_states, num_inputs, num_outputs, self._name)]

    ans.append(self._DumpMatrix('A', self.A))
    ans.append(self._DumpMatrix('B', self.B))
    ans.append(self._DumpMatrix('C', self.C))
    ans.append(self._DumpMatrix('D', self.D))
    ans.append(self._DumpMatrix('U_max', self.U_max))
    ans.append(self._DumpMatrix('U_min', self.U_min))

    ans.append('  return StateFeedbackPlantCoefficients<%d, %d, %d>'
               '(A, B, C, D, U_max, U_min);\n' % (num_states, num_inputs,
                                                  num_outputs))
    ans.append('}\n')
    return ''.join(ans)

  def PlantFunction(self):
    """Returns the name of the plant coefficient function."""
    return 'Make%sPlantCoefficients()' % self._name

  def ControllerFunction(self):
    """Returns the name of the controller function."""
    return 'Make%sController()' % self._name

  def _DumpJavaMatrix(self, name, matrix, last=False):
    ans = ['            new double[] {']
    
    numbers = []
    for x in xrange(matrix.shape[0]):
      for y in xrange(matrix.shape[1]):
        numbers.append('%f' % matrix[x, y])

    ans.append(', '.join(numbers))
    ans.append('}')
    if last:
      ans.append('),')
    else:
      ans.append(',')
    ans.append('  // %s\n' % name)
    return ''.join(ans)

  def DumpPlantJava(self):
    """Writes out a StateSpaceGains declaration."""
    ans = ['        new StateSpaceGains(\n']
    ans.append(self._DumpJavaMatrix('A', self.A))
    ans.append(self._DumpJavaMatrix('B', self.B))
    ans.append(self._DumpJavaMatrix('C', self.C))
    ans.append(self._DumpJavaMatrix('D', self.D))
    ans.append(self._DumpJavaMatrix('L', self.L))
    ans.append(self._DumpJavaMatrix('K', self.K))
    ans.append(self._DumpJavaMatrix('Umax', self.U_max))
    ans.append(self._DumpJavaMatrix('Umin', self.U_min, last=True))
    return ''.join(ans)

  def DumpControllerHeader(self):
    """Writes out a c++ header declaration which will create a Controller object.

    Returns:
      string, The header declaration for the function.
    """
    num_states = self.A.shape[0]
    num_inputs = self.B.shape[1]
    num_outputs = self.C.shape[0]
    return 'StateFeedbackController<%d, %d, %d> %s;\n' % (
        num_states, num_inputs, num_outputs, self.ControllerFunction())

  def DumpController(self):
    """Returns a c++ function which will create a Controller object.

    Returns:
      string, The function which will create the object.
    """
    num_states = self.A.shape[0]
    num_inputs = self.B.shape[1]
    num_outputs = self.C.shape[0]
    ans = ['StateFeedbackController<%d, %d, %d> %s {\n' % (
        num_states, num_inputs, num_outputs, self.ControllerFunction())]

    ans.append(self._DumpMatrix('L', self.L))
    ans.append(self._DumpMatrix('K', self.K))

    ans.append('  return StateFeedbackController<%d, %d, %d>'
               '(L, K, Make%sPlantCoefficients());\n' % (num_states, num_inputs,
                                             num_outputs, self._name))
    ans.append('}\n')
    return ''.join(ans)
