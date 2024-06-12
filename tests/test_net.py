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
