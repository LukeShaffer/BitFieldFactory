import pytest
import os

import BitFieldFactory as bff

'''
General tests on the initial conception of bff, by default assumes all fields
are unsigned.
'''

cross_byte_rules = ('test_name', [
    bff.Segment(name='first_6', start_bit=0, bit_length=6, help='first_6 help string'),
    bff.Segment(name='cross', start_bit=6, bit_length=6, help='helpful string'),
    # Remaining nibble (4 LS bits) of second byte unaccessible/unused
    bff.Segment(name='long', start_bit=16, bit_length=32, help='this crosses multiple bytes')
	]
)

# The "proof of concept" run to create dynamic classes
def test_class_factory():

	# 'test_class' is now an alias for bff.BitFieldFactory.test_name
	test_class = bff.new_class(*cross_byte_rules)
	assert test_class == bff.BitFieldFactory.test_name

	test_inst = test_class()
	assert test_inst.bytes == bytearray(b'\x00' * 6)

	test_inst = test_class(b'\x01\x02\x03\x04\x05\x06')
	assert test_inst.bytes == bytearray(b'\x01\x02\x03\x04\x05\x06')

	assert isinstance(test_inst, test_class)

	assert isinstance(test_inst, bff.BitFieldFactory.test_name)

	


def test_getter_setter():
	test_class = bff.new_class(*cross_byte_rules)

	#1101_1110_0111_1110_0101_0111_1010_1011_0001_1110_0000_0001
	test_inst = test_class(b'\xde\x7e\x57\xab\x1e\x01')
	assert test_inst.first_6 == 0b1101_11
	assert test_inst.first_6_as_bits == '110111'

	assert test_inst.cross == 0b10_0111
	assert test_inst.cross_as_bits == '100111'

	assert test_inst.long == 0b0101_0111_1010_1011_0001_1110_0000_0001
	assert test_inst.long_as_bits == '01010111101010110001111000000001'

	test_inst.first_6 = 1
	assert test_inst.first_6 == 1
	assert test_inst.first_6_as_bits == '000001'
	assert test_inst.bytes[0] == 0b000001_10
	test_inst.first_6 = 2
	assert test_inst.bytes[0] == 0b000010_10

	test_inst.long = 1
	assert test_inst.long == 1
	assert test_inst.long_as_bits == '00000000000000000000000000000001'
	assert test_inst.bytes[2:6] == bytearray(b'\x00\x00\x00\x01')
	test_inst.long = 0xa
	assert test_inst.long == 0xa
	assert test_inst.long_as_bits == '00000000000000000000000000001010'
	assert test_inst.bytes[2:6] == bytearray(b'\x00\x00\x00\x0a')

	# Setting from as_bits

	test_inst.first_6_as_bits = '111111'
	assert test_inst.first_6 == 0b1111_11
	assert test_inst.first_6_as_bits == '111111'
	assert test_inst.bytes[0] == 0b111111_10

	test_inst.long_as_bits = '0000_0000_0000_0000_0000_0000_0000_0001'
	assert test_inst.long == 1
	assert test_inst.long_as_bits == '00000000000000000000000000000001'
	assert test_inst.bytes[2:6] == bytearray(b'\x00\x00\x00\x01')


def test_get_help():
	alias = bff.new_class(*cross_byte_rules)

	inst = alias(b'\xde\x7e\x57\xab\x1e\x01')

	assert inst.get_help('first_6') == inst.get_help('first_6_as_bits') == \
		'first_6 help string'


def test_as_bits_sep():
	test_class = bff.new_class(*cross_byte_rules)
	test_inst = test_class()

	test_inst.long = 1
	assert test_inst.long == 1
	assert test_inst.long_as_bits == '00000000000000000000000000000001'

	test_inst._group_size = 4
	test_inst._group_separator = '_'
	assert test_inst.long_as_bits == '0000_0000_0000_0000_0000_0000_0000_0001'


def test_boundary_checks():
	test_class = bff.new_class(*cross_byte_rules)
	with pytest.raises(AssertionError):
		a = test_class('blah blah blah')
	with pytest.raises(AssertionError):
		a = test_class(b'\x00')

	with pytest.raises(ValueError):
		a = test_class()
		# Put 8 bit value into 6 bit field
		a.first_6 = 0b1111_1111

	with pytest.raises(ValueError):
		a = test_class()
		# Put 8 bit value into 6 bit field
		a.first_6_as_bits = '11111111'


def test_overlapping_segments():
	'''
	Makes sure that segments defined over the same bits behave properly,
	ie, the names of fields are just aliases for the bits of the structure
	that they cover
	'''
	overlapping_rules = ('test_name', [
		bff.Segment('start', 0, 8),
		bff.Segment('start2', 0, 8),
		bff.Segment('middle', 2, 8),
		bff.Segment('end', 6, 8)
		# last 2 bit unused
		]
	)
	test_class = bff.new_class(*overlapping_rules)
	test_inst = test_class()
	assert test_inst.bytes == bytearray(b'\x00' * 2)

	test_inst.start = 12
	assert test_inst.bytes == bytearray(b'\x0c\x00')
	assert test_inst.start2 == 12
	assert test_inst.start2_as_bits == '00001100'
	assert test_inst.middle == 0b0011_0000
	assert test_inst.middle_as_bits == '00110000'
	assert test_inst.end == 0

	# should be 00_11111111_000000
	test_inst.middle = 0b11111111
	assert test_inst.bytes == bytearray((0b00_11111111_000000).to_bytes(2, 'big'))
	assert test_inst.start == 0b00_111111
	assert test_inst.start2 == 0b00_111111
	assert test_inst.end == 0b1111_0000
	test_inst.start2_as_bits = '11_00'


