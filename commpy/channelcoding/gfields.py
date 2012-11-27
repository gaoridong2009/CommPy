
#   Copyright 2012 Veeresh Taranalli <veeresht@gmail.com>
#
#   This file is part of CommPy.   
#
#   CommPy is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   CommPy is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Galois Fields """

from fractions import gcd
from numpy import array, zeros, arange, convolve, ndarray, concatenate
from itertools import *
from commpy.utilities import dec2bitarray, bitarray2dec

class gf:
    """ Defines a Binary Galois Field of order m, containing n, 
    where n can be a single element or a list of elements within the field.

    Parameters
    ----------
    n : int 
    Represents the Galois field element(s).

    m : int 
    Specifies the order of the Galois Field.

    Returns
    -------
    x : int 
    A Galois Field GF(2\ :sup:`m`) object.

    Examples
    ________
    >>> from GF import gf
    >>> n = range(16)
    >>> m = 4
    >>> x = gf(n, m)
    >>> print x.elements
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

    """

    # Initialization
    def __init__(self, x, m):
        self.m = m
        primpoly_array = array([0, 3, 7, 11, 19, 37, 67, 137, 285, 529, 1033, 
                                   2053, 4179, 8219, 17475, 32771, 69643])
        self.prim_poly = primpoly_array[self.m]
        if type(x) is int and x >= 0 and x < pow(2, m):
            self.elements = array([x])
        elif type(x) is ndarray and len(x) >= 1:
            self.elements = x

    # Overloading addition operator for Galois Field
    def __add__(self, x):
        if len(self.elements) == len(x.elements):
            return gf(self.elements ^ x.elements, self.m)
        else:
            raise ValueError, "The arguments should have the same number of elements"

    # Overloading multiplication operator for Galois Field
    def __mul__(self, x):
        if len(x.elements) == len(self.elements):
            prod_elements = arange(len(self.elements))
            for i in xrange(len(self.elements)):
                prod_elements[i] = polymultiply(self.elements[i], x.elements[i], self.m, self.prim_poly)
            return gf(prod_elements, self.m)
        else:
             raise ValueError, "Two sets of elements cannot be multiplied"

    def power_to_tuple(self):
        y = zeros(len(self.elements))
        for idx, i in enumerate(self.elements):
            if 2**i < 2**self.m:
                y[idx] = 2**i
            else:
                y[idx] = polydivide(2**i, self.prim_poly)
        return gf(y, self.m)

    def tuple_to_power(self):
        y = zeros(len(self.elements))
        for idx, i in enumerate(self.elements):
            if i != 0:
                init_state = 1
                cur_state = 1
                power = 0
                while cur_state != i:
                    cur_state = ((cur_state << 1) & (2**self.m-1)) ^ (-((cur_state & 2**(self.m-1)) >> (self.m - 1)) & 
                                (self.prim_poly & (2**self.m-1)))
                    power+=1
                y[idx] = power
            else:
                y[idx] = 0
        return gf(y, self.m)

    def order(self):
        orders = zeros(len(self.elements))
        power_gf = self.tuple_to_power()
        for idx, i in enumerate(power_gf.elements):
            orders[idx] = (2**self.m - 1)/(gcd(i, 2**self.m-1))
        return orders
    
    def cosets(self):
        coset_list = []
        x = self.tuple_to_power().elements
        mark_list = zeros(len(x))
        coset_count = 1
        for idx in xrange(len(x)):
            if mark_list[idx] == 0:
                a = x[idx]
                mark_list[idx] = coset_count 
                i = 1
                while (a*(2**i) % (2**self.m-1)) != a:
                    for idx2 in xrange(len(x)):
                        if (mark_list[idx2] == 0) and (x[idx2] == a*(2**i)%(2**self.m-1)):
                            mark_list[idx2] = coset_count
                    i+=1
                coset_count+=1

        for counts in xrange(1, coset_count):
            coset_list.append(gf(self.elements[mark_list==counts], self.m))

        return coset_list

    def minpolys(self):
        minpol_list = array([])
        full_gf = gf(arange(2**self.m), self.m)
        full_cosets = full_gf.cosets()
        for x in self.elements:
            for i in xrange(len(full_cosets)):
                if x in full_cosets[i].elements:
                    t = array([1, full_cosets[i].elements[0]])[::-1]
                    for root in full_cosets[i].elements[1:]:
                        t2 = concatenate((zeros(len(t)-1), array([1, root]), zeros(len(t)-1)))
                        prod_poly = array([])
                        for n in xrange(len(t2)-len(t)+1):
                            root_sum = 0
                            for k in xrange(len(t)):
                                root_sum = root_sum ^ polymultiply(int(t[k]), int(t2[n+k]), self.m, self.prim_poly)
                            prod_poly = concatenate((prod_poly, array([root_sum])))
                        t = prod_poly[::-1]
                    minpol_list = concatenate((minpol_list, array([bitarray2dec(t[::-1])])))
    
        return minpol_list.astype(int)
   
# Divide two polynomials and returns the remainder
def polydivide(x, y):
    r = y
    while len(bin(r)) >= len(bin(y)):
        shift_count = len(bin(x)) - len(bin(y))
        if shift_count > 0:
            d = y << shift_count
        else:
            d = y
        x = x ^ d
        r = x
    return r

def polymultiply(x, y, m, prim_poly):
    x_array = dec2bitarray(x, m)
    y_array = dec2bitarray(y, m)
    prod = bitarray2dec(convolve(x_array, y_array) % 2)
    return polydivide(prod, prim_poly)

