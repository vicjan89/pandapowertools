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
    index_capacitor = net.shunt[net.shunt['q_mvar'] < 0].index
    net.shunt.loc[index_capacitor, 'q_mvar'] *= nf
    index_inductance = net.shunt[net.shunt['q_mvar'] > 0].index
    net.shunt.loc[index_inductance, 'q_mvar'] /= nf
    net.load.q_mvar /= nf

def get_i_by_u(net: Net, bus: int, v_pu: float):
    '''
    Возвращает ток ext_grid при котором напряжение на шине bus будет равно v_pu
    :param net: pandapowertools Net
    :param bus:
    :param v_pu: напряжение на шине bus в относительных единицах для которого нужно найти ток
    :return: # ток в кА
    '''
    temp = net.net.ext_grid.loc[0, 'vm_pu']
    net.net.ext_grid.loc[0, 'vm_pu'] = 1
    net.calc_pf_pgm()
    v = net.net.res_bus.loc[bus, 'vm_pu']
    vn_kv = net.net.bus.loc[net.net.ext_grid.bus[0], 'vn_kv']
    s = math.sqrt(net.net.res_ext_grid.loc[0, 'p_mw'] ** 2 + net.net.res_ext_grid.loc[0, 'q_mvar'] ** 2)
    i = s / net.net.ext_grid.loc[0, 'vm_pu'] / vn_kv / math.sqrt(3)
    k = v / v_pu
    i /= k
    net.net.ext_grid.loc[0, 'vm_pu'] = temp
    return i

def get_u_by_i(net: Net, bus: int, i: float):
    '''
    Возвращает напряжение на шине bus при котором ток ext_grid будет равен i
    :param net: pandapowertools Net
    :param bus: номер шины на которой измеряется напряжение и для номинального напряжения которой рассчитан ток ВГ
    :param i: kA
    :return: напряжение в относительных единицах
    '''
    temp = net.net.ext_grid.loc[0, 'vm_pu']
    net.net.ext_grid.loc[0, 'vm_pu'] = 1
    net.calc_pf_pgm()
    v = net.net.res_bus.loc[bus, 'vm_pu']
    vn_kv = net.net.bus.loc[bus, 'vn_kv']
    s = math.sqrt(net.net.res_ext_grid.loc[0, 'p_mw'] ** 2 + net.net.res_ext_grid.loc[0, 'q_mvar'] ** 2)
    i_v1pu = s / net.net.ext_grid.loc[0, 'vm_pu'] / vn_kv / math.sqrt(3)
    k = i_v1pu / i
    v /= k
    net.net.ext_grid.loc[0, 'vm_pu'] = temp
    return v
