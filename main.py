import math
import os


from pandapowertools.net import Net
from pandapowertools.plot import plot
from pandapowertools.store import *
from textengines.dxfengine import DXF
import pandapower as pp
from store.store import JsonStorage, YamlStorage, TextStorage

def kz_max():
    os.system(r'ezdxf view "..\CalcUstavkiRZA\Polimir\max_3ph.dxf"')

def kz_min():
    os.system(r'ezdxf view "..\CalcUstavkiRZA\Polimir\min_2ph.dxf"')



if __name__ == '__main__':
    n = Net('Полоцк2')
    n.load()
    # res = n.calc_i_neitral_trafo(203, 3)
    # print(res)
    # n.calc_sc(fault='1ph')
    # print(n.res_bus_sc())