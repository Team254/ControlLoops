#!/usr/bin/python

#import scipy
import numpy

# TODO(aschuh): Objects for a TF, and SS controller.  Similar to Matlab.
# Make it easy to see what you have for everything.
# TODO(aschuh): Rewrite most of this...

# Build the shift matrix
def shiftn(n):
  return nshiftn(1, n)

def nshiftn(amount, n):
  mat = numpy.zeros((n, n))
  for i in range(0, amount):
    mat[i, n - amount + i] = 1
  for j in range(amount, n):
    mat[j, j - amount] = 1
  return mat

# [a1, a2, a3, ...]
# [b1, b2, b3, ...]
# y(n + 1) = a1 y(n) + a2 y(n - 1) + a3 y(n - 2) ... + b1 u(n) + b2 u(n - 1) + b3 u(n - 2)
#     [ 0  1  0]     [0]
# G = [ 0  0  1] B = [0]
#     [a3 a2 a1]     [1]
#
# C = [b3 b2 b1]
#
### x(n + 1) = G x(n) + H u(n)
### y(n)     = C x(n)
### returns G, H, C matricies
def buildSSfromCCDE(a, b):
  if len(b) > len(a):
    raise Exception("Error: B must be less than to A")

  b = b + [0.0] * (len(a) - len(b))

  dim = len(a)

  H = numpy.matrix(numpy.zeros(dim)).T
  H[dim - 1, 0] = 1

  G = numpy.matrix(numpy.zeros((dim, dim)))
  for i in range(0, dim - 1):
    G[i, i + 1] = 1

  for i in range(0, dim):
    G[dim - 1, i] = a[-i - 1]


  C = numpy.matrix(numpy.zeros(dim))
  lenb = len(b)
  for i in range(0, lenb):
    C[0, dim - i - 1] = b[i]
	
  return G, H, C

# [a1, a2, a3, ...]
# [b1, b2, b3, ...]
# m < n
# H = (a1 z^m + a2 z^m-1 + a3 z^m-2 +...)/(b0 z^n+ b1 z^n-1 + b2 z^n-2 +...)
#     [     0      1      0]     [0]
# G = [     0      0      1] B = [0]
#     [-b3/b0 -b2/b0 -b1/b0]     [1]
#
# C = [ a3/b0  a2/b0  a1/b0]
#
### x(n + 1) = G x(n) + H u(n)
### y(n)     = C x(n)
### returns G, H, C matricies
def buildSSfromTF(a, b):
  if len(a) > len(b) - 1:
    raise Exception("Error: a must be less than to b")

  dim = len(b) - 1

  a = [0.0] * (dim - len(a)) + a

  H = numpy.matrix(numpy.zeros(dim)).T
  H[dim - 1, 0] = 1

  G = numpy.matrix(numpy.zeros((dim, dim)))
  for i in range(0, dim - 1):
    G[i, i + 1] = 1

  for i in range(0, dim):
    G[-1, i] = -b[-i - 1] / b[0]


  C = numpy.matrix(numpy.zeros(dim))
  lena = len(a)
  for i in range(0, lena):
    C[0, dim - i - 1] = a[i] / b[0]
	
  return G, H, C

# To get if something is controlable, use the following algorythm.
# http://www.math.epn.edu.ec/eventos/ev_pdf/staircase.pdf

def ctrb(G, H):
	Cscript = numpy.matrix(numpy.zeros(G.shape))
	Cscript[:,0] = temp = H[:]
	for i in range(1,G.shape[0]):
		Cscript[:,i] = temp = G*temp
	return(Cscript)

def canon(G, H, C = None):
  contrl = ctrb(G, H)
  P = numpy.matrix(numpy.zeros(G.shape))
  P1 = numpy.matrix(numpy.zeros(G.shape[0]))
  P1[0, -1] = 1
  P1 = P1 * numpy.linalg.inv(contrl)
  P[0,:] = P1
  for i in range(1,G.shape[0]):
    P[i,:] = P[i-1,:] * G
  invP = numpy.linalg.inv(P)

  Gb = P * G * invP
  Hb = P * H
  if C != None:
    Cb = C * invP
    return Gb, Hb, Cb, P
  else:
    return Gb, Hb, P

def rank(A, eps=1e-12):
  u, s, vh = numpy.linalg.svd(A)
  return len([x for x in s if abs(x) > eps])

def get_term(array,level):
  if(level == -1):
    return(1)
  ret = 0
  for i in range(0,len(array) - level):
    ret += (-array[i]*get_term(array[i+1:],level - 1))
  return ret

def expand_poles(poles):
  ret = [1]*(len(poles) + 1)
  for i in range(0,len(poles)):
    ret[i+1] = get_term(poles,i)
  return(ret)

def acker(A, B, poles):
  if B.shape[1] != 1:
    raise Exception("Invalid shape %s for B" % (str(B.shape), ))
  Gb, Hb, P = canon(A, B)
  dim = Gb.shape[0]
  K = numpy.matrix(numpy.zeros(dim))

  #p = [1, -poles[0]]
  #for pole in poles[1:]:
  #	p = numpy.convolve([1, -pole], p)
  p = expand_poles(poles)
	
  for i in range(0, dim):
    K[0, i] = Gb[-1, i] + p[-i - 1]

  return K * P

def c2d(A, B, dt):
  """Converts from continuous time State Space representation to discrete time.
     Evaluates e^(A dt) for the discrete time version of A, and
     integral(e^(A t) * B, 0, dt).
     Returns (A, B).  C and D are unchanged."""
  e, P = numpy.linalg.eig(A)
  diag = numpy.matrix(numpy.eye(A.shape[0]))
  diage = numpy.matrix(numpy.eye(A.shape[0]))
  for eig, count in zip(e, range(0, A.shape[0])):
    diag[count, count] = math.exp(eig * dt)
    if abs(eig) < 1.0e-16:
      diage[count, count] = dt
    else:
      diage[count, count] = (math.exp(eig * dt) - 1.0) / eig

  return (P * diag * numpy.linalg.inv(P), P * diage * numpy.linalg.inv(P) * B)

