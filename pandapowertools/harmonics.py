import math


from pandapower import pandapowerNet
from pandapowertools.net import Net
import pandas as pd
import matplotlib.pyplot as plt


def i2lc(i, u, nf):
    '''
    Расчёт ёмкости и индуктивности фильтра высших гармоник по току на основной гармонике и номеру фильтруемой гармоники
    :param i:
    :param nf:
    :return:
    '''
    z = u / i / math.sqrt(3)
    print(f'z = {z}')
    w= 100 * math.pi
    c = (nf ** 2 - 1) / w / z / nf / nf
    l = 1 / nf / nf / w / w / c
    qc = u ** 2 * w * c
    ql = w * l
    print('c F, l H, qc VA, ql VA, w')
    return c, l, qc, ql, w

def read_excel():
    data = pd.read_excel(r'D:\Cloud-Drive_vicjan89@gmail.com\obsidian\work\CopyFromServer\Projects\-=ПСД=-\24013_ММПЗ_листопр цех\Рабочие материалы\РЗА\измерения 01\архивы 2024-03-27\Р-1246 ГПП-118\uf2a_1246_240326.xls')

def recalc_imp_harm(net: pandapowerNet, nf: int):
    '''
    Пересчитывает сопротивления сети под источник другой гармоники
    :param net: сеть с сопротивлениями для основной гармоники
    :param nf: номер новой гармоники
    :return:
    '''
    if any([not net[item].empty for item in ('trafo', 'trafo3w', 'gen', 'sgen')]):
        raise NotImplementedError('Recalc for trafo, trafo3w, gen, sgen not implemented')
    net.line.x_ohm_per_km *= nf
    net.shunt.q_mvar *= nf
    net.load.q_mvar /= nf

def get_i_by_u(net: Net, bus: int, v_pu: float, dv_limit = 1e-14):
    '''
    Возвращает ток ext_grid при котором напряжение на шине bus будет равно v_pu
    :param net:
    :param bus:
    :param v_pu:
    :return:
    '''
    v_ext_grid = 0.5
    dv = 0.25
    greater = False
    v_ext_grid_data = []
    v_data = []
    while True:
        net.net.ext_grid.vm_pu = v_ext_grid
        net.calc_pf(max_iteration=20, verbal=False, algorithm='nr')
        v = net.net.res_bus.vm_pu[bus]
        v_ext_grid_data.append(v_ext_grid)
        v_data.append(v)
        # print(f'{v=} {v_ext_grid=} {dv=}')
        if abs(v - v_pu) < 0.001:
            vn_kv = net.net.bus.vn_kv[net.net.ext_grid.bus[0]]
            s = math.sqrt(net.net.res_ext_grid.p_mw[0] ** 2 + net.net.res_ext_grid.q_mvar[0] ** 2)
            i = s / net.net.ext_grid.vm_pu[0] / vn_kv / math.sqrt(3)
            plt.plot(v_ext_grid_data, v_data, 'o')
            plt.show()
            return i
        elif v > v_pu:
            if not greater:
                dv /= 2
            greater = True
            v_ext_grid -= dv
        else:
            if greater:
                dv /= 2
            greater = False
            v_ext_grid += dv
        if dv < dv_limit:
            plt.plot(v_ext_grid_data, v_data, 'o')
            plt.show()
            raise Exception(f'dv too small: {dv=}')

