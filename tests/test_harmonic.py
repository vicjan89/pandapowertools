import math


from pandapowertools.harmonics import i2lc
import matplotlib.pyplot as plt
from pandapowertools.net import Net
from pandapowertools.harmonics import recalc_imp_harm


def test_i2lc():
    l, c = i2lc(86.8, 10000, 5)
    w = 100 * math.pi * 5
    xl = w * l
    xc = 1 / (w * c)
    x = xl - xc
    print(f'l = {l}, c = {c}, w = {w} xl = {xl}, xc = {xc} x = {x}')
    assert  x < 1e-10

def test_nr():
    for h in range(2, 41):
        n = Net(r'..\..\calcsetting\calcsetting\source\Miory\miory_only_filter')
        n.load()
        recalc_imp_harm(n.net, h)
        res = []
        x = []
        y = []
        z = []
        i_c = []
        power = []
        for v in range(1, 11):
            u = v / 10
            n.net.ext_grid.vm_pu[0] = u
            n.calc_pf_pgm(max_iteration=1000)
            i = n.net.res_line.loc[3, 'i_ka']
            vm = n.net.res_bus.loc[4, 'vm_pu']
            s = math.sqrt(n.net.res_ext_grid.loc[0, 'p_mw'] ** 2 + n.net.res_ext_grid.loc[0, 'q_mvar'] ** 2)
            i_calc = s / 10 / u / math.sqrt(3)
            res.append(f'{u=} v_bus4={vm}')
            x.append(u)
            y.append(i)
            z.append(vm)
            i_c.append(i_calc)
            power.append(s)
        plt.figure(figsize=(7, 21))
        plt.subplot(3, 1, 1)
        plt.plot(x, y, x, i_c)
        plt.title(f'{h} гармоника - ток источника гармоник, кА')
        plt.subplot(3, 1, 2)
        plt.plot(x, z)
        plt.title(f'{h} гармоника - напряжение на 1с 10кВ, о.е.')
        plt.subplot(3, 1, 3)
        plt.plot(x, power)
        plt.title(f'{h} гармоника - мощность источника гармоник, МВА')
        plt.savefig(f'{h}.png')
        plt.cla()
    print('\n'.join(res))