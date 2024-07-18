import math

from pandapowertools.harmonics import i2lc

def test_i2lc():
    l, c = i2lc(86.8, 10000, 5)
    w = 100 * math.pi * 5
    xl = w * l
    xc = 1 / (w * c)
    x = xl - xc
    print(f'l = {l}, c = {c}, w = {w} xl = {xl}, xc = {xc} x = {x}')
    assert  x < 1e-10