'''
A file to house all of my new negative segment tests
'''
import pytest
import os

import BitFieldFactory as bff
from BitFieldFactory import Segment

negative_rules = ('negative_field', (
    Segment(name='first_5_bits', start_bit=0, bit_length=5, is_signed=False),
    Segment(name='shifted', start_bit=1, bit_length=3, is_signed=True),
    Segment(name='end', start_bit=8, bit_length=8, is_signed=True),
    )
)
alias = bff.new_class(*negative_rules)

def test_negative_display():
    '''
    Just tests if signed segments can be set properly and if their contents
    get displayed properly
    '''
    inst = alias()
    inst.shifted = -1
    assert inst.shifted == -1
    assert inst.shifted_as_bits == '111'

