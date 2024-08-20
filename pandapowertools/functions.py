import tomllib
import re
import unicodedata
import os


import pandapower as pp


def define_c(u: float, case: str, lv_tol_percent: int) -> float:
    '''
    Определяет коэффициент коррекции напряжения по IEC60909
    :param u: корректируемое напряжение
    :param case: режим работы энергосистемы 'min' или 'max'
    :param lv_tol_percent: допуск 10% или 6%
    :return: c
    '''
    if case not in ('max', 'min') or lv_tol_percent not in (6, 10) or u < 0:
        raise UserWarning("Неправильные параметры для определения коэффициента коррекции напряжения c")
    if u <= 1:
        cmin = 0.95
        if lv_tol_percent == 10:
            cmax = 1.1
        else:
            cmax = 1.05
    else:
        cmin = 1.0
        cmax = 1.1
    if case == 'max':
        return cmax
    else:
        return cmin



def russian_to_attribute_name(text: str):
    text = text.replace('-', '_')
    text = text.replace('/', '_')
    text = text.replace('.', '_')
    text = text.replace('(', '_')
    text = text.replace(')', '_')
    text = text.replace(' ', '_')
    text = text.replace('№', '_')
    text = text.replace('=', '_')
    text = text.replace('*', '_')
    text = text.replace(',', '_')
    text = text.replace('+', '_')
    return text

def split_str(text: str, num: int) -> list:
    '''
    Split string into elements with num characters
    :param text:
    :param num:
    :return:
    '''
    res = []
    sep = ' ,.-_'
    while len(text) > num:
        if text[num] in sep:
            res.append(text[:num])
            text = text[num:]
        else:
            n = num - 1
            while text[n] not in sep and n > 1:
                n -= 1
            if n == 1:
                n = num - 1
            res.append(text[:n+1])
            text = text[n+1:]
    res.append(text)
    return res