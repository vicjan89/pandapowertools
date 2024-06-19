import os


from pandapowertools.net import Net
from pandapowertools.plot import plot
from textengines.dxfengine import DXF
from pandapowertools.functions import split_str

def test_plot():
    n = Net('../Полоцк')
    n.load()
    te = DXF('../Полоцк')
    plot(n.net, te, indexes=True)
    # te.to_png(-20, 25, -23, 15)
    te.save()
    os.system('ezdxf view ../Полоцк.dxf')

def test_split_str():
    strings = ('123 4567-89.123456789,', '012 34567890123456-78.901', '012-3456.901234567890123456789')
    for s in strings:
        print(split_str(s, 8))