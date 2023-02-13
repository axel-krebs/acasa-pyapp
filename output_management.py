"""
* ACASA Output Managament Module
* 
"""
import os
from pathlib import Path
#os.chdir(Path())
# importing modules
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors

# TODO convenience method, to replaced by queue
def print_receipt(order: dict) -> float:
    sum_all = 0
    for bestell_pos in order.keys():
        item = bestell_pos[0]
        item_cnt = order[bestell_pos]
        sum_pos = item_cnt * bestell_pos[1]
        sum_all += sum_pos
        print(
            item,
            ", Anzahl:",
            item_cnt,
            ", Summe: ",
            sum_pos)
    return sum_all