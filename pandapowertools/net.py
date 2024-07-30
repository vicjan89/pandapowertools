import os
import json
import tomllib
import math
from collections import Counter


import pandapower as pp


from pandapowertools.functions import russian_to_attribute_name


class Attrs:
    ...

class Net:

    def __init__(self, name: str, path: str = ''):
        self.name = name
        self.path = path
        self.modes = {}
        self.net = pp.create_empty_network(name)
        self.b = Attrs()
        self.l = Attrs()
        self.t = Attrs()
        self.t3 = Attrs()
        self.s = Attrs()
        self._update_std()
        self.et = Attrs()
        self.et.line = 'l'
        self.et.trafo = 't'
        self.et.trafo3w = 't3'
        self.et.bus = 'b'

    def add_std(self):
        current_path = os.path.realpath(__file__)
        current_path = os.path.dirname(current_path)
        with open(os.path.join(current_path, 'std_lines.toml'), 'rb') as f:
            data = tomllib.load(f)
        pp.create_std_types(self.net, data, element='line', overwrite=True, check_required=True)
        with open(os.path.join(current_path, 'std_trafos.toml'), 'rb') as f:
            data = tomllib.load(f)
        pp.create_std_types(self.net, data, element='trafo', overwrite=True, check_required=True)
        with open(os.path.join(current_path, 'std_trafos3w.toml'), 'rb') as f:
            data = tomllib.load(f)
        pp.create_std_types(self.net, data, element='trafo3w', overwrite=True, check_required=True)
        self._update_std()


    def _update_std(self):
        attrs = {}
        for key, value in self.net.std_types.items():
            for name_std in value:
                if key == 'trafo3w':
                    prefix = 't3_'
                else:
                    prefix = key[0] + '_'
                attrs[f'{prefix}{russian_to_attribute_name(name_std)}'] = name_std
        self.std = Attrs()
        self.std.__dict__.update(attrs)

    def _line_to_attr(self, index):
        return 'l' + russian_to_attribute_name(self.name_line(index))

    def add_line(self, from_bus: int, to_bus: int, length: float, std_type: str, parallel: int = 1):
        index = pp.create_line(self.net, from_bus, to_bus, length, std_type, parallel=parallel)
        self.net.line["endtemp_degree"] = 20
        self.l.__dict__.update({self._line_to_attr(index): index})
        return index

    def line_impedance(self, index: int):
        l = self.net.line.at[index, 'length_km']
        p = self.net.line.at[index, 'parallel']
        r = self.net.line.at[index, 'r_ohm_per_km'] * l / p
        x = self.net.line.at[index, 'x_ohm_per_km'] * l / p
        return r, x

    def merge_serial_lines(self, index1, index2):
        line1 = self.net.line.loc[index1]
        line2 = self.net.line.loc[index2]
        buses = [line1['from_bus'], line1['to_bus'], line2['from_bus'], line2['to_bus']]
        count_buses = Counter(buses)
        buses_alone = [bus for bus, count in count_buses.items() if count == 1]
        if len(buses_alone) != 2:
            raise ValueError('Lines must have common bus')
        r1, x1 = self.line_impedance(index1)
        r2, x2 = self.line_impedance(index2)
        pp.create_line_from_parameters(net=self.net, from_bus=buses_alone[0], to_bus=buses_alone[1], length_km=1,
                                       r_ohm_per_km=r1 + r2, x_ohm_per_km=x1 + x2, c_nf_per_km=0, max_i_ka=100)
        self.net.line.drop(index=index1, inplace=True)
        self.net.line.drop(index=index2, inplace=True)

    def _switch_to_attr(self, index):
        return 's' + russian_to_attribute_name(self.name_switch(index))

    def add_switch(self, bus, element, et, closed=True):
        index = pp.create_switch(self.net, bus, element, et, closed)
        self.s.__dict__.update({self._switch_to_attr(index): index})
        return index

    def switch(self, n, closed=True):
        self.net.switch.at[n, 'closed'] = closed

    def add_bus(self, un: float, name: str = ''):
        index = pp.create_bus(self.net, un, name)
        self.b.__dict__.update({'b' + russian_to_attribute_name(name): index})
        return index

    def _trafo_to_attr(self, index):
        name = f'{self.net.trafo.at[index, "name"]}'
        return 't' + russian_to_attribute_name(name)

    def add_trafo(self, hv_bus, lv_bus, std_type, name):
        index = pp.create_transformer(self.net, hv_bus, lv_bus, std_type, name)
        self.t.__dict__.update({self._trafo_to_attr(index): index})
        return index

    def _trafo3w_to_attr(self, index):
        name = f'{self.net.trafo3w.at[index, "name"]}'
        return 't' + russian_to_attribute_name(name)

    def add_trafo3w(self, hv_bus, mv_bus, lv_bus, std_type, name):
        index = pp.create_transformer3w(self.net, hv_bus, mv_bus, lv_bus, std_type, name)
        self.t3.__dict__.update({self._trafo3w_to_attr(index): index})
        return index

    def add_impedance(self, from_bus: int, to_bus: int, r: float, x: float):
        '''
        создаёт элемент сопротивления (например токоограничивающий реактор)
        :param from_bus:
        :param to_bus:
        :param r: Ohm
        :param x: Ohm
        :return:
        '''
        return pp.create_line_from_parameters(net=self.net, from_bus=from_bus, to_bus=to_bus, length_km=1, r_ohm_per_km=r,
                                           x_ohm_per_km=x, c_nf_per_km=0, max_i_ka=100)

    # def add_impedance2(self, from_bus: int, to_bus: int, r: float, x: float, s: float):
    #     '''
    #     создаёт элемент сопротивления (например токоограничивающий реактор)
    #     :param from_bus:
    #     :param to_bus:
    #     :param r: Ohm
    #     :param x: Ohm
    #     :param s: MVA
    #     :return:
    #     '''
    #     u = self.net.bus.loc[from_bus, "vn_kv"]
    #     zb = u ** 2 / s
    #     r_pu = r / zb
    #     x_pu = x / zb
    #     return pp.create_impedance(net=self.net, from_bus=from_bus, to_bus=to_bus, rft_pu=r_pu, rtf_pu=r_pu,
    #                                xtf_pu=x_pu, xft_pu=x_pu, sn_mva=s)
    def add_shunt(self, bus: int, q, p = 0):
        return pp.create_shunt(self.net, bus, q, p)

    def add_gen(self, bus, vn_kv, sn_mva, xdss_pu, cos_phi, rdss_ohm=0, name=''):
        return pp.create_gen(self.net, bus, sn_mva=sn_mva, vn_kv=vn_kv, name=name, xdss_pu=xdss_pu, rdss_ohm=rdss_ohm,
                             cos_phi=cos_phi)

    def _calc_s_for_ext_grid(self, u_bus, ikz_max, ikz_min, i1kz_max: float | None = None):
        item = {}
        item['s_sc_max_mva'] = u_bus * ikz_max * math.sqrt(3)
        item['s_sc_min_mva'] = u_bus * ikz_min * math.sqrt(3)
        if i1kz_max:
            item['x0x_max'] = ikz_max / i1kz_max
        return item


    def add_ext_grid(self, bus, ikz_max: float, ikz_min: float | None = None, i1kz_max: float | None = None,
                     i1kz_min: float | None = None, name = ''):
        '''
        Create extension grid
        :param bus: bus where the slack is connected
        :param ikz_max: ikz in maximum mode in kiloampere
        :param ikz_min: ikz in minimum mode in kiloampere
        :param i1kz_max: single phase ikz in maximum mode in kiloampere
        :param i1kz_min: single phase ikz in minimum mode in kiloampere
        :return:
        '''
        if not ikz_min:
            ikz_min = ikz_max
        u_bus = self.net.bus.at[bus, 'vn_kv']
        item = self._calc_s_for_ext_grid(u_bus, ikz_max, ikz_min, i1kz_max)
        item['bus'] = bus
        item['rx_max'] = 0.1
        item['r0x0_max'] = 0.1
        item['rx_min'] = 0.1
        item['name'] = name
        return pp.create_ext_grid(net=self.net, **item)

    def ext_grid(self, n, in_service = True):
        self.net.ext_grid.at[n, 'in_service'] = in_service

    def change_ext_grid(self, num, ikz_max: float, ikz_min: float | None = None, i1kz_max: float | None = None):
        bus = self.net.ext_grid.loc[num, 'bus']
        u_bus = self.net.bus.loc[bus, 'vn_kv']
        item = self._calc_s_for_ext_grid(u_bus, ikz_max, ikz_min, i1kz_max)
        self.net.ext_grid.loc[num, 's_sc_max_mva'] = item['s_sc_max_mva']
        self.net.ext_grid.loc[num, 's_sc_min_mva'] = item['s_sc_min_mva']
        if item.get('x0x_max'):
            self.net.ext_grid.loc[num, 'x0x_max'] = item['x0x_max']

    def add_load(self, bus, s_mva: float | None = None, p_mw: float | None = None, cosf: float = 1):
        if s_mva is None and p_mw is not None:
            s_mva = p_mw / cosf
        elif p_mw is None and s_mva is not None:
            p_mw = s_mva * cosf
        elif s_mva is None and p_mw is None:
            raise ValueError('s_mva and p_mw cannot be both None')
        return pp.create_load(net=self.net, bus=bus, p_mw=p_mw, q_mvar=math.sqrt(s_mva ** 2 - p_mw **2),
                              const_z_percent=100)

    def add_load_as_shunt(self, bus, s_mva: float | None = None, p_mw: float | None = None, cosf: float = 1):
        if s_mva is None and p_mw is not None:
            s_mva = p_mw / cosf
        elif p_mw is None and s_mva is not None:
            p_mw = s_mva * cosf
        elif s_mva is None and p_mw is None:
            raise ValueError('s_mva and p_mw cannot be both None')
        return pp.create_shunt(net=self.net, bus=bus, p_mw=p_mw, q_mvar=math.sqrt(s_mva ** 2 - p_mw **2))

    def add_load_rx(self, bus, r_ohm: float, x_ohm: float):
        v = self.net.bus.at[bus, 'vn_kv']
        # if not r_ohm:
        #     r_ohm = x_ohm * 0.001
        p = v ** 2 / r_ohm
        q = v ** 2 / x_ohm
        return pp.create_load(net=self.net, bus=bus, p_mw=p, q_mvar=q,
                              const_z_percent=100)

    def add_trafo_as_impedance(self, from_bus, to_bus, s_mva: float, vk_percent: float, name=''):
        v = self.net.bus.at[from_bus, 'vn_kv']
        x = vk_percent * v ** 2 / s_mva / 100
        return pp.create_line_from_parameters(net=self.net, from_bus=from_bus, to_bus=to_bus, length_km=1, r_ohm_per_km=0,
                                              x_ohm_per_km=x, c_nf_per_km=0, max_i_ka=100, name=name)

    def add_c(self, bus, c, nf=1):
        '''
        Создаёт конденсаторную батарею для расчётов PowerFlow (например для представления фильтра высших гармоник)
        :param bus:
        :param c: F
        :param nf: номер гармоники для которой выполняется расчёт
        :return:
        '''
        u = self.net.bus.loc[bus, "vn_kv"]
        q = - u ** 2 * 100 * math.pi * nf * c
        pp.create_shunt_as_capacitor(net=self.net, bus=bus, q_mvar=q, loss_factor=0.0000000001)

    # def add_l2(self, from_bus, to_bus, l, nf):
    #     '''
    #     Создаёт индуктивность для расчётов PowerFlow (например для представления фильтра высших гармоник)
    #     :param bus:
    #     :param l: H
    #     :param nf: номер гармоники для которой выполняется расчёт
    #     :return:
    #     '''
    #     u = self.net.bus.loc[from_bus, "vn_kv"]
    #     x = 100 * math.pi * nf * l / u / u
    #     self.add_impedance(from_bus, to_bus, r=0, x=x, s=1)

    def add_l(self, from_bus, to_bus, l, nf=1):
        '''
        Создаёт индуктивность для расчётов PowerFlow (например для представления фильтра высших гармоник)
        :param bus:
        :param l: H
        :param nf: номер гармоники для которой выполняется расчёт
        :return:
        '''
        x = 100 * math.pi * nf * l
        pp.create_line_from_parameters(net=self.net, from_bus=from_bus, to_bus=to_bus, length_km=1, r_ohm_per_km=0,
                                       x_ohm_per_km=x, c_nf_per_km=0, max_i_ka=100)

    def save(self, name = ''):
        if not name:
            name = self.name
        file = f'{name}.json'
        if self.path:
            path = os.path.join(self.path, file)
        else:
            path = file
        pp.to_json(self.net, path)
        if self.modes:
            file = f'{name}_modes.json'
            if self.path:
                path = os.path.join(self.path, file)
            else:
                path = file
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.modes, f, ensure_ascii=False, indent=4)

    def load(self):
        file = f'{self.name}.json'
        if self.path:
            path = os.path.join(self.path, file)
        else:
            path = file
        self.net = pp.from_json(path)
        attrs = {}
        for i, b in self.net.bus.iterrows():
            attrs['b' + russian_to_attribute_name(b['name'])] = i
        self.b.__dict__.update(attrs)
        attrs = {}
        for i in self.net.line.index.to_list():
            attrs[self._line_to_attr(i)] = i
        self.l.__dict__.update(attrs)
        attrs = {}
        for i in self.net.trafo.index.to_list():
            attrs[self._trafo_to_attr(i)] = i
        self.t.__dict__.update(attrs)
        attrs = {}
        for i in self.net.trafo3w.index.to_list():
            attrs[self._trafo3w_to_attr(i)] = i
        self.t3.__dict__.update(attrs)
        attrs = {}
        for i in self.net.switch.index.to_list():
            attrs[self._switch_to_attr(i)] = i
        self.s.__dict__.update(attrs)
        attrs = {}
        for key, value in self.net.std_types.items():
            for name_std in value:
                if key == 'trafo3w':
                    prefix = 't3_'
                else:
                    prefix = key[0] + '_'
                attrs[f'{prefix}{russian_to_attribute_name(name_std)}'] = name_std
        self.std.__dict__.update(attrs)

        try:
            file = f'{self.name}_modes.json'
            if self.path:
                path = os.path.join(self.path, file)
            else:
                path = file
            with open(path, 'r', encoding='utf-8') as f:
                self.modes = json.load(f)
        except FileNotFoundError:
            print('File of modes not exist!')

    def scheme(self, find: str = ''):
        res = []
        res.append('bus')
        for i, row in self.net.bus.sort_index().iterrows():
            name_bus = row['name'].ljust(20)
            istr = str(i).rjust(4)
            try:
                x = self.net.bus_geodata.loc[i, 'x']
                y = self.net.bus_geodata.loc[i, 'y']
            except:
                x = 'No'
                y = 'No'
            in_service = '' if row['in_service'] else ' (not in_service)'
            res.append(f'{istr}) {name_bus} {str(row["vn_kv"]).ljust(7)} x={x} y={y}{in_service}')
        res.append('ext_grid')
        for i, row in self.net.ext_grid.sort_index().iterrows():
            name_bus = self.net.bus.loc[row['bus'], 'name'].ljust(28)
            in_service = '' if row['in_service'] else ' (not in_service)'
            name = row['name'].ljust(25)
            res.append(f'{i}) {name_bus} {name} s_sc_max_mva={row["s_sc_max_mva"]} s_sc_min_mva={row["s_sc_min_mva"]}'
                       f'{in_service}')
        res.append('gen')
        for i, row in self.net.gen.sort_index().iterrows():
            name_bus = self.net.bus.loc[row['bus'], 'name'].ljust(28)
            in_service = '' if row['in_service'] else ' (not in_service)'
            res.append(f'{i}) {row['name']} {name_bus} sn_mva={row["sn_mva"]} xdss_pu={row["xdss_pu"]} '
                       f'rdss_ohm={row["rdss_ohm"]} cos_phi={row["cos_phi"]} vn_kv={row["vn_kv"]}{in_service}')
        res.append('line')
        for i, row in self.net.line.sort_index().iterrows():
            name_from = self.net.bus.loc[row['from_bus'], 'name'].ljust(18)
            name_to = self.net.bus.loc[row['to_bus'], 'name'].rjust(18)
            l = row['length_km']
            r = row['r_ohm_per_km'] * l
            x = row['x_ohm_per_km'] * l
            z = math.sqrt(r**2 + x**2)
            if 'r0_ohm_per_km' in row:
                r0 = row['r0_ohm_per_km'] * l
                x0 = row['x0_ohm_per_km'] * l
                z0 = math.sqrt(r0**2 + x0**2)
            std_type = row['std_type']
            if std_type:
                std_type = std_type.ljust(18)
            else:
                std_type = ' ' * 18
            istr = str(i).rjust(3)
            l = str(l).rjust(7)
            in_service = '' if row['in_service'] else ' (not in_service)'
            s = f'{istr}) {name_from} {name_to} {row["parallel"]:.0f}*{std_type} {l} z={r:.4f}+j{x:.4f}={z:.4f}'
            if 'r0_ohm_per_km' in row:
                s += f' z0={r0:.4f}+j{x0:.4f}={z0:.4f}'
            res.append(s + f' {in_service}')
        res.append('trafo')
        for i, row in self.net.trafo.sort_index().iterrows():
            name_hv = self.net.bus.loc[row['hv_bus'], 'name'].ljust(28)
            name_lv = self.net.bus.loc[row['lv_bus'], 'name'].rjust(28)
            in_service = '' if row['in_service'] else ' (not in_service)'
            res.append(f'{i}) {name_hv} {name_lv} {row["name"]} {row["std_type"]}{in_service}')
        res.append('trafo3w')
        for i, row in self.net.trafo3w.sort_index().iterrows():
            name_hv = self.net.bus.loc[row['hv_bus'], 'name'].ljust(28)
            name_mv = self.net.bus.loc[row['mv_bus'], 'name'].ljust(28)
            name_lv = self.net.bus.loc[row['lv_bus'], 'name'].rjust(28)
            in_service = '' if row['in_service'] else ' (not in_service)'
            res.append(f'{i}) {name_hv} {name_mv} {name_lv} {row["name"]} {row["std_type"]} {row["vector_group"]} {in_service}')
        res.append('impedance')
        for i, row in self.net.impedance.sort_index().iterrows():
            name_from = self.net.bus.loc[row['from_bus'], 'name'].ljust(28)
            name_to = self.net.bus.loc[row['to_bus'], 'name'].rjust(28)
            u2 = self.net.bus.loc[row['from_bus'], 'vn_kv'] ** 2
            zb = u2 / row['sn_mva']
            rpu = row['rtf_pu']
            xpu = row['xtf_pu']
            in_service = '' if row['in_service'] else ' (not in_service)'
            res.append(f'{i}) {name_from} {name_to} rft_pu={rpu} xft_pu={xpu} r={rpu*zb} x={xpu*zb}{in_service}')
        res.append('switch')
        names = self.names_switch
        for i, row in self.net.switch.iterrows():
            res.append(f'{i}) {names[i]} {"closed" if row["closed"] else "opened"}')
        res.append('load')
        for i, row in self.net.load.sort_index().iterrows():
            name_bus = self.net.bus.loc[row['bus'], 'name'].ljust(28)
            in_service = '' if row['in_service'] else ' (not in_service)'
            res.append(f'{i}) {name_bus} p_mw={row["p_mw"]:.5f} q_mvar={row["q_mvar"]:.5f}'
                       f'{in_service}')
        res.append('shunt')
        for i, row in self.net.shunt.sort_index().iterrows():
            name_bus = self.net.bus.loc[row['bus'], 'name'].ljust(28)
            in_service = '' if row['in_service'] else ' (not in_service)'
            v = self.net.bus.at[row['bus'], 'vn_kv']
            r = v ** 2 / row['p_mw']
            x = v ** 2 / row['q_mvar']
            res.append(f'{i}) {name_bus} p_mw={row["p_mw"]:.5f} q_mvar={row["q_mvar"]:.5f}'
                       f' {r=} {x=} {in_service}')
        if find:
            for row in res:
                if find in row:
                    print(row)
        else:
            print('\n'.join(res))
# calc
    def add_mode(self, name: str, closed: tuple = tuple(), opened: tuple = tuple()):
        self.modes[name] = {'closed': closed, 'opened': opened}

    def make_mode(self, mode_name):
        if mode_name in self.modes:
            self.net.switch.loc[self.modes[mode_name]['closed'], 'closed'] = True
            self.net.switch.loc[self.modes[mode_name]['opened'], 'closed'] = False
        else:
            print('Mode not specified')

    def calc_pf_pgm(self, algorithm='nr', mode_name='', max_iteration=20, verbal=False):
        tolerance = 1e-8
        if mode_name:
            self.make_mode(mode_name)
        for i in range(15):
            try:
                pp.runpp_pgm(self.net, error_tolerance_vm_pu=tolerance, algorithm=algorithm,
                         max_iterations=max_iteration)
                if verbal:
                    print(f'PowerFlow calculated witn tolerance {tolerance}')
                break
            except pp.powerflow.LoadflowNotConverged:
                tolerance *= 10
        else:
            if verbal:
                print(f'PowerFlow not calculated with tolerance {tolerance}')

    def calc_pf(self, algorithm='nr', mode_name='', max_iteration='auto', verbal=False, init='auto'):
        tolerance = 1e-8
        if mode_name:
            self.make_mode(mode_name)
        for i in range(15):
            try:
                u = self.net.ext_grid.at[0, 'vm_pu']
                pp.runpp(self.net, tolerance_mva=tolerance, algorithm=algorithm,
                         calculate_voltage_angles=False, max_iteration=max_iteration, init=init,
                         check_connectivity=True, distributed_slack=False)#, init_vm_pu=u, init_va_degree=.0)
                if verbal:
                    print(f'PowerFlow calculated witn tolerance {tolerance}')
                break
            except pp.powerflow.LoadflowNotConverged:
                tolerance *= 10
        else:
            if verbal:
                print(f'PowerFlow not calculated with tolerance {tolerance}')

    def res_line(self):
        names = self.names_line
        res = {names[i]: value['i_ka'] for i, value in self.net.res_line.sort_index().iterrows()}
        return res

    @property
    def res(self):
        print(f'res_bus\n{self.net.res_bus}')
        print(f'\nres_line\n{self.net.res_line}')
        print(f'\nres_ext_grid\n{self.net.res_ext_grid}')
        print(f'\nres_load\n{self.net.res_load}')
        print(f'\nres_shunt\n{self.net.res_shunt}')

    def create_mode_magnetizing_current_inrush(self, k: float=4):
        self.net.load['in_service'] = False
        index_magnetizing_current_inrush = []
        for i, tr in self.net.trafo.iterrows():
            index_magnetizing_current_inrush.append(pp.create_load(self.net, tr.hv_bus, p_mw=tr.sn_mva * k))
        for i, tr in self.net.trafo3w.iterrows():
            index_magnetizing_current_inrush.append(pp.create_load(self.net, tr.hv_bus, p_mw=tr.sn_hv_mva * k))
        return index_magnetizing_current_inrush

    def delete_mode_magnetizing_current_inrush(self, index_magnetizing_current_inrush: list):
        pp.toolbox.drop_elements(self.net, element_type='load', element_index=index_magnetizing_current_inrush)
        for i, l in self.net.load.iterrows():
            l.in_service = True

    def calc_sc_mode(self, mode_name: str, fault: str='3ph', case: str='max'):
        self.make_mode(mode_name)
        pp.shortcircuit.calc_sc(self.net, fault=fault, case=case, branch_results=True, return_all_currents=True)

    def calc_sc(self, fault: str='3ph', case: str='max', branch_results=False, return_all_currents=False):
        pp.shortcircuit.calc_sc(self.net, fault=fault, case=case, branch_results=branch_results,
                                return_all_currents=return_all_currents)

    def calc_i_neitral_trafo(self, bus, trafo3w, case='max'):
        vector_group = self.net.trafo3w.loc[trafo3w, 'vector_group']
        if vector_group[1] not in ('N', 'n'):
            print('Trafo3w vector group must be YN or Yn')
            return
        self.calc_sc(fault='1ph', case=case)
        rk0_neitral = float(self.net.res_bus_sc.loc[bus, 'rk0_ohm'])
        xk0_neitral = float(self.net.res_bus_sc.loc[bus, 'xk0_ohm'])
        ik_neitral = float(self.net.res_bus_sc.loc[bus, 'ikss_ka'])
        self.net.trafo3w.loc[trafo3w, 'vector_group'] = vector_group[0] + vector_group[2:]
        self.calc_sc(fault='1ph', case=case)
        rk0 = float(self.net.res_bus_sc.loc[bus, 'rk0_ohm'])
        xk0 = float(self.net.res_bus_sc.loc[bus, 'xk0_ohm'])
        ik = float(self.net.res_bus_sc.loc[bus, 'ikss_ka'])
        self.net.trafo3w.loc[trafo3w, 'vector_group'] = vector_group
        z_system = math.sqrt(rk0 ** 2 + xk0 ** 2)
        z_all = math.sqrt(rk0_neitral ** 2 + xk0_neitral ** 2)
        c = 1 - z_all / z_system
        print(f'i_neitral={ik_neitral * c:.5f}, ikz_with_neitral={ik_neitral}, ikz_without_neitral={ik}, '
              f'ikz_with_neitral - ikz_without_neitral={(ik_neitral - ik) * 3}')

    def res_bus_sc(self):
        res = {}
        for i, value in self.net.res_bus_sc.sort_index().iterrows():
            res_row = [self.net.bus.loc[i, 'name'], float(value['ikss_ka']) * 1000,
                       math.sqrt(value['rk_ohm']**2 + value['xk_ohm']**2)]
            if 'rk0_ohm' in value:
                z0 = math.sqrt(value['rk0_ohm'] ** 2 + value['xk0_ohm'] ** 2)
                res_row.append(z0)
            res[i] = res_row
        return res

    def res_line_sc(self, bus):
        names = self.names_line
        res = {i: [names[i], float(value['ikss_ka']) * 1000]
               for i, value in self.net.res_line_sc.xs(bus, level=1).sort_index().iterrows()}
        return res

    def res_bus_sc_md(self):
        s = 'Точка КЗ | Ток КЗ, кА | r, Ом | x, Ом | z, Ом\n-|-|-|-|-\n'
        res = self.net.res_bus_sc
        for index, row in res.sort_index().iterrows():
            name = self.net.bus.loc[index, 'name'].ljust(28)
            i = f'{row.loc["ikss_ka"] * 1000:.1f}'.ljust(7)
            r = row.loc["rk_ohm"]
            rstr = f'{r:.6f}'.ljust(10)
            x = row.loc["xk_ohm"]
            xstr = f'{x:.6f}'.ljust(10)
            s += f'{name} | {i} | {rstr} | {xstr} | {math.sqrt(r**2 + x**2):.6f}\n'
        return s


    def name_line(self, index):
        name1 = ''
        try:
            name1 = self.net.bus.at[self.net.line.at[index, 'from_bus'], 'name']
        except KeyError:
            ...
        name2 = ''
        try:
            name2 = self.net.bus.at[self.net.line.at[index, 'to_bus'], 'name']
        except KeyError:
            ...
        name = name1 + ' - ' + name2
        return name

    @property
    def names_line(self):
        names = {i: self.name_line(i) for i in self.net.line.index}
        return names

    @property
    def names_trafo(self):
        return self.net.trafo['name'].tolist()

    @property
    def names_trafo3w(self):
        return self.net.trafo3w['name'].tolist()

    def name_switch(self, index):
        name1 = ''
        try:
            name1 = self.net.bus.at[self.net.switch.at[index, 'bus'], 'name']
        except KeyError:
            ...
        name2 = ''
        et = self.net.switch.at[index, 'et']
        element = self.net.switch.at[index, 'element']
        try:
            if et == 't':
                name2 = self.net.trafo.at[element, 'name']
            if et == 'l':
                name2 = self.name_line(element)
            if et == 'b':
                name2 = self.net.bus.at[element, 'name']
        except KeyError:
            ...
        name = name1 + ' - ' + name2
        return name

    @property
    def names_switch(self):
        names = [self.name_switch(i) for i in self.net.switch.index]
        return names

    @property
    def names_bus(self):
        return self.net.bus['name'].to_list()

# coords
    def bus_geodata(self):
        for i, geodata in self.net.bus_geodata.sort_index().iterrows():
            name = self.net.bus.loc[i, 'name'].ljust(20)
            istr = str(i).rjust(4)
            print(f'{istr}) {name} x={geodata["x"]} y={geodata["y"]}')

    def clear_geodata(self):
        self.net.bus_geodata.drop(self.net.bus_geodata.index, inplace=True)

    def scale_geodata(self, n):
        self.net.bus_geodata.x *= n
        self.net.bus_geodata.y *= n

    def busxy(self, i, x, y):
        self.net.bus_geodata.loc[i, 'x'] = x
        self.net.bus_geodata.loc[i, 'y'] = y

    def place_buses(self, buses: int | list | tuple, bus_to: int | None=None, x=0, y=0, step=2):
        if isinstance(buses, int):
            buses = [buses]
        if bus_to is not None:
            x = self.net.bus_geodata.loc[bus_to, 'x'] + x
            y = self.net.bus_geodata.loc[bus_to, 'y'] + y
        for bus in buses:
            self.net.bus_geodata.loc[bus, 'x'] = x
            self.net.bus_geodata.loc[bus, 'y'] = y
            x += step

    def move_bus(self, bus, bus_to, dx: float | None = None, dy: float | None = None):
        if dx is not None:
            self.net.bus_geodata.loc[bus, 'x'] = self.net.bus_geodata.loc[bus_to, 'x'] + dx
        if dy is not None:
            self.net.bus_geodata.loc[bus, 'y'] = self.net.bus_geodata.loc[bus_to, 'y'] + dy

    def shift_buses(self, buses, bus_to: int | None=None, dx=0, dy=0):
        '''
        Shift coords of buses. If define bus_to then shift is doing from coords bus_to and buses[0]
        :param buses:
        :param bus_to:
        :param dx:
        :param dy:
        :return:
        '''
        if isinstance(buses, int):
            buses = [buses]
        if bus_to is not None:
            dx = self.net.bus_geodata.loc[bus_to, 'x'] - self.net.bus_geodata.loc[buses[0], 'x'] + dx
            dy = self.net.bus_geodata.loc[bus_to, 'y'] - self.net.bus_geodata.loc[buses[0], 'y'] + dy
        for bus in buses:
            self.net.bus_geodata.loc[bus, 'x'] += dx
            self.net.bus_geodata.loc[bus, 'y'] += dy

    def select_rect(self, x1, y1, x2, y2):
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        buses = []
        for i, bus_geodata in self.net.bus_geodata.iterrows():
            if x1 <= bus_geodata['x'] <= x2 and y1 <= bus_geodata['y'] <= y2:
                buses.append(i)
        return buses

    def coord_buses(self, buses, x: float | None = None, y: float | None = None):
        if isinstance(buses, int):
            buses = [buses]
        for bus in buses:
            if x is not None:
                self.net.bus_geodata.loc[bus, 'x'] = x
            if y is not None:
                self.net.bus_geodata.loc[bus, 'y'] = y

    def turn_right(self):
        temp = self.net.bus_geodata.x
        self.net.bus_geodata.x = self.net.bus_geodata.y
        self.net.bus_geodata.y = temp

    def mirror_x(self):
        self.net.bus_geodata.y *= -1

    def mirror_y(self):
        self.net.bus_geodata.x *= -1
