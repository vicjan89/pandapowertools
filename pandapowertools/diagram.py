import math

from pandapowertools.symbols import *


class Symbol:
    def __init__(self, text: list[str], text_coords: tuple[int, int], text_angle: float,
                 lenght: int, diagram):
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

    def __init__(self, bus1_index: int, bus2_index: int,
                 text: list[str],
                 diagram: 'Diagram',
                 text_coords: tuple[int, int] | None = None,
                 text_angle: float | None = None,
                 lenght: int = 20,
                 coords: tuple[tuple[int, int]] | None = None):
        super().__init__(text=text, text_coords=text_coords, text_angle=text_angle,
                         lenght=lenght, diagram=diagram)
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
                    self.text_angle = math.atan2(y2 - y1, abs(x1 - x2))
                x, y = turn(x=x, y=y+0.2 , xcenter=x, ycenter=y,
                            angle=self.text_angle)
                self.text_coords = (x, y)

    def draw(self):
        self.diagram.te.lines(*self.coords)
        label_draw(*self.text_coords, text=self.text, te=self.diagram.te,
                   angle=self.text_angle, length=self.lenght)

class Switch_sym(Symbol):

    def __init__(self, bus_index, et, element_index, text, text_coords: tuple[int, int],
                 diagram):
        super().__init__(text, text_coords, diagram)
        self.bus = self.diagram.get_bus(bus_index)
        self.element = self.diagram.get_element(et, element_index)

    def draw(self):
        ...


class Diagram:
    def __init__(self, te: TextEngine):
        self.te = te
        self.buses = {}
        self.switches = {}
        self.lines = {}

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

        self.lines[index] = Line_sym(bus1_index=bus1_index, bus2_index=bus2_index,
                                     text=text, diagram=self,
                                     text_coords=text_coords,
                                     lenght=lenght,
                                     coords=coords)

    def get_bus(self, index: int) -> Bus_sym | Node_sym | None:
        return self.buses[index]

    def get_element(self, et: str, index: int):
        match et:
            case 'b':
                return self.buses[index]
            case 'l':
                return self.lines[index]

    def add_switch(self, index: int, bus_index, et, elment_index, text: list[str],
                   text_coords: tuple[int, int]):
        self.switches[index] = Switch_sym(bus_index, et, elment_index, text, text_coords, self)

    def draw(self):
        for bus in self.buses.values():
            bus.draw()
        for switch in self.switches.values():
            switch.draw()
        for line in self.lines.values():
            line.draw()
        self.te.save()
