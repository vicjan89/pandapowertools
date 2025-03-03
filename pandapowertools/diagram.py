import math

from pandapowertools.symbols import *


class Symbol:
    def __init__(self, text: str | list[str] | tuple[str],
                 diagram,
                 text_coords: tuple[int, int] | None = None,
                 text_angle: float | None = None,
                 lenght: int = 10,
                 ):
        '''

        :param text:
        :param text_coords:
        :param text_angle: in radians, 0 is horizontal
        :param lenght: num chars in row text
        :param diagram:
        '''
        self.text = text
        self.text_coords = text_coords
        self.text_angle = text_angle
        self.lenght = lenght
        self.diagram = diagram

    def draw(self):
        ...

class Node_sym(Symbol):
    def __init__(self, x, y,
                 diagram,
                 text: str | list[str] = '',
                 text_coords: tuple[int, int] | None = None,
                 text_angle: float = 0.,
                 lenght: int = 10,
                 ):
        super().__init__(text=text, text_coords=text_coords, text_angle=text_angle,
                         lenght=lenght, diagram=diagram)
        self.x = x
        self.y = y
        if not self.text_coords:
            self.text_coords = (x+0.2, y+0.2)

    @property
    def coords_middle(self):
        return (self.x, self.y)

    def get_coords_switch(self, bus_index):
        return (self.x, self.y)

    def draw(self):
        self.diagram.te.circle(self.x, self.y, r=0.1, black=True)
        label_draw(*self.text_coords, text=self.text, te=self.diagram.te,
                   length=self.lenght, angle=self.text_angle)


class Bus_sym(Symbol):
    '''
    Symbol if bus
    '''
    def __init__(self, coords: tuple[int] | list[int],
                 diagram: 'Diagram',
                 text: list[str],
                 text_coords: tuple[int, int],
                 text_angle: float | None = None,
                 ):
        super().__init__(text=text, text_coords=text_coords, text_angle=text_angle,
                         diagram=diagram)
        self.coords = coords

    @property
    def coords_middle(self):
        x1, y1 = self.coords[0]
        x2, y2 = self.coords[1]
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    def draw(self):
        bus_draw(self.coords, self.text, self.diagram.te,
             xt=self.text_coords[0], yt=self.text_coords[1])

class Line_sym(Symbol):

    def __init__(self, index, bus1_index: int, bus2_index: int,
                 text: list[str],
                 diagram: 'Diagram',
                 text_coords: tuple[int, int] | None = None,
                 text_angle: float | None = None,
                 lenght: int = 20,
                 coords: tuple[tuple[int, int]] | None = None):
        super().__init__(text=text, text_coords=text_coords, text_angle=text_angle,
                         lenght=lenght, diagram=diagram)
        self.index = index
        self.bus1_index = bus1_index
        self.bus2_index = bus2_index
        if coords:
            self.coords = coords
        else:
            bus1 = self.diagram.get_bus(bus1_index)
            bus2 = self.diagram.get_bus(bus2_index)
            self.coords = [bus1.coords_middle, bus2.coords_middle]
        if not self.text_coords:
                (x1, y1), (x2, y2) = self.coords[0], self.coords[-1]
                x = (x1 + x2) / 2
                y = (y1 + y2) / 2
                if not self.text_angle:
                    self.text_angle = math.atan2(x1 - x2, y2 - y1) + math.pi / 2
                    if self.text_angle > math.pi / 2:
                        self.text_angle -= math.pi
                x, y = turn(x=x, y=y+0.2 , xcenter=x, ycenter=y,
                            angle=self.text_angle)
                self.text_coords = (x, y)

    def get_coords_switch(self, bus_index):
        if bus_index == self.bus1_index:
            x1, y1 = self.coords[0]
            x2, y2 = self.coords[1]
        elif bus_index == self.bus2_index:
            x1, y1 = self.coords[-1]
            x2, y2 = self.coords[-2]
        else:
            raise ValueError('Line not have bus with bus_index')
        vector = complex(x2 - x1, y2 - y1)
        vector /= abs(vector)
        vector *= 3
        return x1 + vector.real, y1 + vector.imag

    def draw(self):
        switch1 = self.diagram.get_switch(bus_index=self.bus1_index, et='l',
                                               element_index=self.index)
        if switch1:
            self.diagram.te.lines(self.coords[0], switch1.coords_connect[0])
            self.diagram.te.lines(switch1.coords_connect[1], *self.coords[1:])

        switch2 = self.diagram.get_switch(bus_index=self.bus2_index, et='l',
                                               element_index=self.index)
        if switch2:
            self.diagram.te.lines(self.coords[-1], switch2.coords_connect[1])
            self.diagram.te.lines(switch2.coords_connect[0], *self.coords[:-1])

        if not (switch1 or switch2):
            self.diagram.te.lines(*self.coords)
        label_draw(*self.text_coords, text=self.text, te=self.diagram.te,
                   angle=self.text_angle, length=self.lenght)

class Switch_sym(Symbol):

    def __init__(self, bus_index, et, element_index,
                 diagram,
                 text: str | list[str] | tuple[str] = '',
                 text_coords: tuple[int, int] | None = None,
                 closed: bool = True,
                 ):
        super().__init__(text=text, text_coords=text_coords, diagram=diagram)
        self.bus = self.diagram.get_bus(bus_index)
        self.bus_index = bus_index
        self.et = et
        self.element_index = element_index
        self.element = self.diagram.get_element(et, element_index)
        self.closed = closed

    def draw(self):
        x1, y1 = self.bus.get_coords_switch(self.bus_index)
        x2, y2 = self.element.get_coords_switch(self.bus_index)
        x_middle = (x1 + x2) / 2
        y_middle = (y1 + y2) / 2
        angle = math.atan2(x1 - x2, y2 - y1) + math.pi / 2
        self.coords_connect = switch_draw(x_middle, y_middle, angle, self.diagram.te,
                                     closed=self.closed)
        if isinstance(self.element, (Node_sym, Bus_sym)):
            self.diagram.te.lines((x1, y1), self.coords_connect[0])
            self.diagram.te.lines((x2, y2), self.coords_connect[1])

class Gen_sym(Symbol):

    def __init__(self, bus_index: int, text: str | list[str], diagram: 'Diagram'):
        super().__init__(text=text, diagram=diagram)
        self.bus = self.diagram.get_bus(bus_index)


    def draw(self):
        gen_draw(self.bus.x, self.bus.y, self.text, self.diagram.te)

class Ext_grid_sym(Symbol):

    def __init__(self, bus_index: int,
                 diagram: 'Diagram',
                 text: str | list[str] = '',
                 ):
        super().__init__(text=text, diagram=diagram)
        self.bus = self.diagram.get_bus(bus_index)

    def draw(self):
        ext_grid_draw(self.bus.x, self.bus.y, self.diagram.te)


class Diagram:
    def __init__(self, te: TextEngine):
        self.te = te
        self.buses = {}
        self.switches = {}
        self.lines = {}
        self.gens = {}
        self.ext_grids = {}

    def add_bus(self, index: int, coords: tuple[int] | list[int], text: list[str],
                text_coords: tuple[int, int]):
        self.buses[index] = Bus_sym(coords, text, text_coords, self)

    def add_node(self, index: int, coords: tuple[int, int] | list[int, int], text: list[str],
                 text_coords: tuple[int, int], lenght: int = 10):
        self.buses[index] = Node_sym(x=coords[0], y=coords[1], text=text,
                                     text_coords=text_coords, lenght=lenght,
                                     diagram=self)

    def add_line(self, index: int, bus1_index: int, bus2_index: int,
                 text: str | list[str],
                 coords: tuple[tuple[int, int]] | None = None,
                 text_coords: tuple[int, int] | None = None,
                 lenght: int = 20,
                 ):

        self.lines[index] = Line_sym(index=index, bus1_index=bus1_index,
                                     bus2_index=bus2_index,
                                     text=text, diagram=self,
                                     text_coords=text_coords,
                                     lenght=lenght,
                                     coords=coords)

    def add_gen(self, index: int, bus_index: int, text: str | list[str] | tuple[str]):
        self.gens[index] = Gen_sym(bus_index=bus_index, text=text, diagram=self)

    def get_bus(self, index: int) -> Bus_sym | Node_sym | None:
        return self.buses[index]

    def get_element(self, et: str, index: int):
        match et:
            case 'b':
                return self.buses[index]
            case 'l':
                return self.lines[index]

    def add_switch(self, index: int, bus_index, et, element_index, closed: bool = True):
        self.switches[index] = Switch_sym(bus_index=bus_index, et=et,
                                          element_index=element_index,
                                          closed=closed,
                                          diagram=self)

    def add_ext_grid(self, index: int, bus_index):
        self.ext_grids[index] = Ext_grid_sym(bus_index=bus_index, diagram=self)

    def get_switch(self, bus_index: int, et: str, element_index: int):
        for switch in self.switches.values():
            if (switch.bus_index == bus_index and
                switch.element_index == element_index and
                switch.et==et):
                return switch

    def draw(self):
        for bus in self.buses.values():
            bus.draw()
        for switch in self.switches.values():
            switch.draw()
        for line in self.lines.values():
            line.draw()
        for gen in self.gens.values():
            gen.draw()
        for ext_grid in self.ext_grids.values():
            ext_grid.draw()
        self.te.save()
