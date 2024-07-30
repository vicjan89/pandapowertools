import math


from pandapowertools.net import Net


def test_save():
    n = Net('Сеть')
    n.add_bus(10, '1с 10кВ')
    n.add_bus(10, '2с 10кВ')
    n.add_line(0, 1, 1.2, 'А-50')
    n.save()

def test_load():
    n = Net('Сеть')
    n.load()

def i_neitr_tr(ikz_3ph, ikz_1ph, u, z_tr):
    z1 = u / math.sqrt(3) / ikz_3ph
    z0 = u * math.sqrt(3) / ikz_1ph - 2 * z1
    zc0 = 1 / (1 / z0 - 1 / z_tr)
    i0 = ikz_1ph / 3
    c1 = z0 / zc0
    c2 = z0 / z_tr
    i_neitr = i0 * c2
    print(f'i_neitr = {i_neitr}, i0={i0}, z1 = {z1}, z0 = {z0}, zc0={zc0}, c1 = {c1}, c2 = {c2}')

def i_kz1(ikz_3ph, ikz_1ph, u, z_tr):
    z1 = u / math.sqrt(3) / ikz_3ph
    z0 = math.sqrt(3) * u / ikz_1ph - 2 * z1
    ikz_1ph = u * math.sqrt(3) / (2 * z1 + z0)
    print(f'{ikz_1ph=:.1f} {z0=:.2f} {z1=:.2f}')
    z0 = 1 / (1 / z0 + 1 / z_tr)
    ikz_1ph = u * math.sqrt(3) / (2 * z1 + z0)
    print(f'{ikz_1ph=:.1f} {z0=:.2f} {z1=:.2f}')
    print('-' * 30)

def test_start():
    print('test')
    i_kz1(27800, 29679,121000, 42.5)
    i_kz1(13600,  16859, 121000, 36.5)
    i_kz1(8874,  6241, 121000, 26.25)
    i_kz1(8244,  7213, 121000, 26.25)

def test_merge_serial_lines():
    n = Net('..\miory')
    n.load()
    n.merge_serial_lines(0, 1)
