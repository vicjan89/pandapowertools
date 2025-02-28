import math

from textengines.interfaces import *

from pandapowertools.functions import split_str, define_c


dx = 2
r = 0.1
text_size = 0.2

def node_draw(x, y, te: TextEngine):
    te.circle(x, y, r=r, black=True)

def label_draw(x, y, text: str | list[str], te: TextEngine, angle: float = 0.,
               length: int = 8):
    '''
    Draw multirows text
    :param x:
    :param y:
    :param text: every row of text is item of list
    :param te: TextEngine
    :param angle: in radians, 0 radian is horizontal
    :param length: max number chars in row
    :return:
    '''

    if isinstance(text, str):
        text = [text]
    dy = text_size * 1.2
    x_init, y_init = x, y
    for t in text:
        if len(t) > length:
            txts = split_str(t, length)
            for txt in txts[::-1]:
                if angle:
                    x_turned, y_turned = turn(x, y, x_init, y_init, angle)
                else:
                    x_turned, y_turned = x, y
                te.label(x_turned, y_turned, text=txt, s=text_size, place='c',
                         angle=math.degrees(angle))
                y += dy
        else:
            if angle:
                x_turned, y_turned = turn(x, y, x_init, y_init, angle)
            else:
                x_turned, y_turned = x, y
            te.label(x_turned, y_turned, text=t, s=text_size, place='c',
                     angle=math.degrees(angle))
            y += dy


def bus_draw(coords, te: TextEngine):
    te.lines((coords[0][0], coords[0][1], 0.2, 0.2), (coords[1][0], coords[1][1], 0.2, 0.2))


def line_draw(coords, te: TextEngine):
    te.lines(*coords)

def turn(x, y, xcenter, ycenter, angle):
    x_res = xcenter + (x - xcenter) * math.cos(angle) - (y - ycenter) * math.sin(angle)
    y_res = ycenter + (x - xcenter) * math.sin(angle) + (y - ycenter) * math.cos(angle)
    return x_res, y_res

def _switch(x, y, angle, te: TextEngine, closed: bool = True, text: str = ''):
    '''
    Draw switch on text engine
    :param x: center of switch
    :param y: center of switch
    :param angle: turn switch
    :param te: TextEngine
    :param closed: switch closes if True else open
    :param text: note for switch
    :return: list of 2 tuples with coordinates to connect lines to switch on the left
    and right sides
    '''
    size = r *2
    xlt = xlb = x - size
    xrt = xrb = x + size
    ylt = yrt = y + size
    ylb = yrb = y - size
    coords = []
    for xc, yc in ((xlt, ylt), (xrt, yrt), (xrb, yrb), (xlb, ylb),
                   (x, y + size), (x, y - size),
                   (x - size, y), (x + size, y)):
        coords.append(_turn(xc, yc, x, y, angle))
    te.lines(*coords[:-4], cycle=True)
    if closed:
        te.lines(coords[-2], coords[-1])
    else:
        te.lines(coords[-4], coords[-3])
    return coords[-2:]


def _switch_bus(x1, y1, x2, y2, te: TextEngine, closed: bool = False):
    middle_x = (x1 + x2) / 2
    middle_y = (y1 + y2) / 2
    angle = math.atan2(y2-y1, x2-x1)
    coords = _switch(middle_x, middle_y, angle, te, closed)
    te.lines((x1, y1), coords[0])
    te.lines((x2, y2), coords[1])

def _switch_line(x1, y1, x2, y2, te: TextEngine, closed: bool = False):
    length = r * 6
    k = math.sqrt((x2 - x1)**2 + (y2 - y1)**2) / length
    x = x1 + (x2 - x1) / k
    y = y1 + (y2 - y1) / k
    angle = math.atan2(y2-y1, x2-x1)
    _switch(x, y, angle, te, closed)

def _resistor(x, y, angle, te: TextEngine):
    size_x = r * 1.5
    size_y = r * 3
    xlt = xlb = x - size_x
    xrt = xrb = x + size_x
    ylt = yrt = y + size_y
    ylb = yrb = y - size_y
    coords = []
    for xc, yc in ((xlt, ylt), (xrt, yrt), (xrb, yrb), (xlb, ylb),
                   (x, y + size_y), (x, y - size_y)):
        coords.append(_turn(xc, yc, x, y, angle))
    te.lines(*coords[:-2], cycle=True)
    return coords[-2:]

def _reactor(x1, y1, x2, y2, te: TextEngine, text: list[str] | str = '', length: int = 6):
    x2 = x1
    y2 += r
    y1 -= r
    y_midle = (y1 + y2) / 2
    r_impedance = r * 4
    te.circle(x1, y_midle, r=r_impedance, st_angle=180, en_angle=90, black=False)
    te.lines((x1, y1), (x2, y_midle+r_impedance))
    te.lines((x2, y2), (x1, y_midle), (x1-r_impedance, y_midle))
    if isinstance(text, str):
        text = [text]
    dy = text_size * 1.2
    for t in text:
        if len(t) > length:
            txts = split_str(t, length)
            for txt in txts[::-1]:
                te.label(x1 + r_impedance-r, y_midle, text=txt, place='e', s=text_size)
                y_midle += dy
        else:
            te.label(x1 + r_impedance - r, y_midle, text=t, place='e', s=text_size)
            y_midle += dy

def _impedance(coord1, coord2, te: TextEngine, text: list[str] | str = '', length: int = 20):
    if isinstance(text, str):
        text = [text]
    x1, y1 = coord1
    x2, y2 = coord2
    middle_x = (x1 + x2) / 2
    middle_y = (y1 + y2) / 2
    angle = math.atan2(x1-x2, y2-y1)
    coords = _resistor(middle_x, middle_y, angle, te)
    x1, y1 = _turn(x1, y1 + r, x1, y1, angle)
    x2, y2 = _turn(x2, y2 - r, x2, y2, angle)
    te.lines((x1, y1), coords[1])
    te.lines((x2, y2), coords[0])
    y = (y1 + y2) / 2
    dx = text_size * 1.2
    x = (x1 + x2) / 2 - r * 5 - dx
    angle_degree = math.degrees(angle) + 90
    if 180 <= angle_degree <= 360:
        angle_degree -= 180
    for t in text:
        if len(t) > length:
            txts = split_str(t, length)
            for txt in txts[::-1]:
                x_turned, y_turned = _turn(x, y, middle_x, middle_y, angle)
                te.label(x_turned, y_turned, text=txt, s=text_size, place='c', angle=angle_degree)
                x -= dx
        else:
            te.label(x, y, text=t, s=text_size, place='c', angle=angle_degree)
            x -= dx


def _trafo(x1, y1, x2, y2, text, te: TextEngine, length: int = 6, vector_group: str = ''):
    if y2 > y1:
        x1, y1, x2, y2 = x2, y2, x1, y1
    x1 = x2
    y2 += r
    y1 -= r
    y_midle = (y1 + y2) / 2
    r_trafo = r * 4
    r2 = r * 2
    te.circle(x1, y_midle+r_trafo-r, r=r_trafo, black=False)
    te.circle(x1, y_midle-r_trafo+r, r=r_trafo, black=False)
    te.lines((x1, y1), (x2, y_midle+r_trafo * 2 - r))
    te.lines((x2, y2), (x1, y_midle-r_trafo * 2 + r))
    if vector_group:
        if 'D' in vector_group:
            y = y_midle + r_trafo - r
            te.lines((x1 - r2, y - r), (x1 + r2, y - r), (x1, y + r2), cycle=True)
        if 'd' in vector_group:
            y = y_midle - r_trafo + r
            te.lines((x1 - r2, y - r), (x1 + r2, y - r), (x1, y + r2), cycle=True)
        if 'Y' in vector_group:
            y = y_midle + r_trafo - r
            te.lines((x1, y), (x1, y + r2))
            te.lines((x1, y), (x1 - r2, y - r))
            te.lines((x1, y), (x1 + r2, y - r))
        if 'y' in vector_group:
            y = y_midle - r_trafo + r
            te.lines((x1, y), (x1, y + r2))
            te.lines((x1, y), (x1 - r2, y - r))
            te.lines((x1, y), (x1 + r2, y - r))
        if 'N' in vector_group:
            y = y_midle + r_trafo - r
            te.lines((x1, y), (x1 + r2, y))
        if 'n' in vector_group:
            y = y_midle - r_trafo + r
            te.lines((x1, y), (x1 + r2, y))
    if isinstance(text, str):
        text = [text]
    dy = text_size * 1.2
    for t in text:
        if len(t) > length:
            txts = split_str(t, length)
            for txt in txts[::-1]:
                te.label(x1 + r_trafo-r, y_midle, text=txt, place='e', s=text_size)
                y_midle += dy
        else:
            te.label(x1 + r_trafo - r, y_midle, text=t, place='e', s=text_size)
            y_midle += dy

def _trafo3w(x1, y1, x2, y2, x3, y3, text, te: TextEngine, vector_group: str = ''):
    y1 -= r
    y2 += r
    y3 += r
    y_midle = (y1 + max(y2, y3)) / 2
    r_trafo = r * 4
    r2 = r * 2
    te.circle(x1, y_midle+r_trafo-r, r=r_trafo, black=False)
    te.circle(x1-r2-r, y_midle-r_trafo+r, r=r_trafo, black=False)
    te.circle(x1+r2+r, y_midle-r_trafo+r, r=r_trafo, black=False)
    te.lines((x1, y1), (x1, y_midle+r_trafo * 2 - r))
    y = y_midle-r_trafo + r
    te.lines((x2, y2), (x2, y), (x1-r2-r-r_trafo, y))
    te.lines((x3, y3), (x3, y), (x1+r2+r+r_trafo, y))
    if vector_group:
        w = n = -r_trafo + r
        for letter in vector_group:
            if letter in 'DYN':
                y = y_midle + r_trafo - r
            if letter == 'D':
                te.lines((x1 - r2, y - r), (x1 + r2, y - r), (x1, y + r2), cycle=True)
            if letter == 'Y':
                te.lines((x1, y), (x1, y + r2))
                te.lines((x1, y), (x1 - r2, y - r))
                te.lines((x1, y), (x1 + r2, y - r))
            if letter == 'N':
                te.lines((x1, y), (x1 + r2, y))
            if letter in 'dyn':
                y = y_midle - r_trafo + r
            if letter == 'd':
                if w > 0 and n < 0:
                    n = -n
                te.lines((x1 - r2 + w, y - r), (x1 + r2 + w, y - r), (x1 + w, y + r2), cycle=True)
                w = -w
            if letter == 'y':
                if w > 0 and n < 0:
                    n = -n
                te.lines((x1 + w, y), (x1 + w, y + r2))
                te.lines((x1 + w, y), (x1 - r2 + w, y - r))
                te.lines((x1 + w, y), (x1 + r2 + w, y - r))
                w = -w
            if letter == 'n':
                te.lines((x1 + n, y), (x1 + r2 + n, y))
                n = -n
    if isinstance(text, str):
        text = [text]
    dy = text_size * 1.2
    y_midle += r
    for t in text:
        te.label(x1 + r + r_trafo, y_midle, text=t, place='e', s=text_size)
        y_midle -= dy

def _ext_grid(x, y, te: TextEngine):
    d = 0.5
    d2 = d * 2
    d3 = d * 3
    d4 = d * 4
    dy = 0.5
    te.lines((x, y+r), (x, y+d2+dy))
    te.lines((x-d, y+d2+dy),(x-d, y+d4+dy), (x+d, y+d4+dy), (x+d, y+d2+dy), cycle=True)
    te.lines((x-d, y+d2+dy), (x+d, y+d4+dy))
    te.lines((x-d, y+d3+dy), (x, y+d4+dy))
    te.lines((x, y+d2+dy), (x+d, y+d3+dy))
    te.lines((x+d, y+d2+dy), (x-d, y+d4+dy))
    te.lines((x+d, y+d3+dy), (x, y+d4+dy))
    te.lines((x, y+d2+dy), (x-d, y+d3+dy))

def _gen(x, y, text, te: TextEngine):
    d = 0.5
    d2 = d * 2
    r_gen = r * 4
    y_midle = y - r_gen * 2
    te.lines((x, y-r), (x, y - r_gen))
    te.circle(x, y_midle, r_gen)
    if isinstance(text, str):
        text = [text]
    dy = text_size * 1.2
    te.label(x, y_midle, 'G', 'c', s=text_size)
    te.label(x, y_midle, '~', 's', s=text_size)
    for t in text:
        te.label(x + r + r_gen, y_midle, text=t, place='e', s=text_size)
        y_midle -= dy

def _capacitor(x, y, text, te: TextEngine):
    d = r * 7
    w = r * 5
    w2 = r * 2
    te.lines((x, y-r), (x, y-d))
    te.lines((x, y-d-r-d), (x, y-d-r))
    te.lines((x-w, y-d), (x+w, y-d))
    te.lines((x-w, y-d-r), (x+w, y-d-r))
    # _ground(x, y - d - d, te)
    dy = text_size * 1.2
    for t in text:
        te.label(x + w2, y - r, text=t, place='e', s=text_size)
        y -= dy

def _ground(x, y, te: TextEngine):
    w1 = r * 3
    w2 = r * 2
    w3 = r
    te.lines((x-w1, y), (x+w1, y))
    te.lines((x-w2, y-r), (x+w2, y-r))
    te.lines((x-w3, y-r*2), (x+w3, y-r*2))

