#!/usr/bin/python
import ccde
import unittest
import numpy
from numpy.testing import *

class TestSequenceFunctions(NumpyTestCase):
    def test_buildSSfromCCDE_reducedOrder(self):
        a = [1, 2, 3]
        b = [4, 5]

        G, H, C = ccde.buildSSfromCCDE(a, b)
        assert_almost_equal(G, numpy.matrix([[ 0.,  1.,  0.], [ 0.,  0.,  1.], [ 3.,  2.,  1.]]))
        assert_almost_equal(H, numpy.matrix([[ 0.], [ 0.], [ 1.]]))
        assert_almost_equal(C, numpy.matrix([[ 0.,  5.,  4.]]))
	
    def test_buildSSfromCCDE_full(self):
        a = [1, 2, 3]
        b = [4, 5, 6]

        G, H, C = ccde.buildSSfromCCDE(a, b)
        assert_almost_equal(G, numpy.matrix([[ 0.,  1.,  0.], [ 0.,  0.,  1.], [ 3.,  2.,  1.]]))
        assert_almost_equal(H, numpy.matrix([[ 0.], [ 0.], [ 1.]]))
        assert_almost_equal(C, numpy.matrix([[ 6.,  5.,  4.]]))

    def test_buildSSfromTF_full(self):
        a = [4, 5, 6]
        b = [1, 1, 2, 3]

        G, H, C = ccde.buildSSfromTF(a, b)
        assert_almost_equal(G, numpy.matrix([[ 0.,  1.,  0.], [ 0.,  0.,  1.], [ -3.,  -2.,  -1.]]))
        assert_almost_equal(H, numpy.matrix([[ 0.], [ 0.], [ 1.]]))
        assert_almost_equal(C, numpy.matrix([[ 6.,  5.,  4.]]))

    def test_buildSSfromTF_reduced(self):
        a = [4, 5]
        b = [1, 1, 2, 3]

        G, H, C = ccde.buildSSfromTF(a, b)
        assert_almost_equal(G, numpy.matrix([[ 0.,  1.,  0.], [ 0.,  0.,  1.], [ -3.,  -2.,  -1.]]))
        assert_almost_equal(H, numpy.matrix([[ 0.], [ 0.], [ 1.]]))
        assert_almost_equal(C, numpy.matrix([[ 5.,  4.,  0.]]))

    def test_ctrb(self):
        A = numpy.matrix([[-2, 1], [-2, 0]])
        B = numpy.matrix([[1], [3]])
        C = numpy.matrix([[1, 0]])
        ct = ccde.ctrb(A, B)
        assert_almost_equal(ct, numpy.matrix([[1, 1], [3, -2]]))
	
	Gb, Hb, Cb, P = ccde.canon(A, B, C)
        assert_almost_equal(Gb, numpy.matrix([[0, 1], [-2, -2]]))
        assert_almost_equal(Hb, numpy.matrix([[ 0.], [ 1.]]))
        assert_almost_equal(Cb, numpy.matrix([[ 3.,  1.]]))

    def test_canon(self):
        a = [4, 5]
        b = [1, 1, 2, 3]

        G, H, C = ccde.buildSSfromTF(a, b)
	Gb, Hb, Cb, P = ccde.canon(G, H, C)
        assert_almost_equal(G, numpy.matrix([[ 0.,  1.,  0.], [ 0.,  0.,  1.], [ -3.,  -2.,  -1.]]))
        assert_almost_equal(H, numpy.matrix([[ 0.], [ 0.], [ 1.]]))
        assert_almost_equal(C, numpy.matrix([[ 5.,  4.,  0.]]))

    def test_acker(self):
        a = [1]
        b = numpy.convolve([1, 3], [1, 4])

        G, H, C = ccde.buildSSfromTF(a, b)

	K = ccde.acker(G, H, [-5, -6])
	eigenvalues, eigenvectors = numpy.linalg.eig(G - H * K)
        assert_almost_equal(K, numpy.matrix([[18, 4]]))
        assert_almost_equal(eigenvalues, numpy.array([-5, -6]))

if __name__ == '__main__':
    unittest.main()
