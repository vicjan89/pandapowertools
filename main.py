from pandapowertools.net import Net
from pandapowertools.plot import plot
from pandapowertools.store import *
from textengines.dxfengine import DXF
import pandapower as pp

n = Net('Полоцк')
n.load()