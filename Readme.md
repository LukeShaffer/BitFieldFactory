# Mission Statement
This project is made to take away the hassle of parsing/creating binary data in
Python and allow the programmer to use high level constructs to inspect binary
data to check if the data is semantically correct instead of manually counting
1's and 0's to match everything up properly. 

# Implementation Details

## Features at a Glance

* ### Quickly and Easily create a Robust Class to model any kind of bitfield
	This library is designed first and foremost with flexibility for the designer/programmer in mind.  You can create any kind of convoluted mis-matched, overlapping set of bits, ram them together into a structure, and use this library to index it based on the fields' human-readable names.

	* **As a general rule in this library, the field names are just aliases for the bit positions they represent in the structure. So if you have multiple fields pointing to the same bits, updating the bits from one field will update them for all fields.**

	* **The only stipulation is that currently, all structures created must be a multiple of whole bytes, so no 13-bit structures are allowed, they will get automatically bumped up to 16-bits (2-bytes) with the last 3 bits having no easy human-readable alias.**

	* **ALSO during prototyping, I expect the last segment to be the LSB of your structure, and if it isn't, the library will fail to properly detect the actual byte length you require.**

	Example Use:

			import BitFieldFactory as bff
			simple_ruleset = ('class_name', [
				bff.Segment('first_6_bits', 0, 6),
				bff.Segment('first_6_bits_again', 0, 6),
				bff.Segment('cross_byte_boundary', 6, 6),
				bff.Segment('long_first_byte', 16, 8),
				bff.Segment('long', 16, 32)
				]
			)
			alias = bff.new_class(*simple_ruleset)
			class_instance = bff.BitFieldFactory.class_name()
			# OR
			class_instance = alias()
			# OR if you want actual data in the slots:
			instance = alias(b'\xa0' * 6)
			# Substitute binary data you have read from a .dat for instance

	And then BOOM, you have a 6-byte structure that you can easily index the first 6 bits (two different ways), next 6 bits, a field that crosses the 1st and 2nd byte, the 3rd byte, and final 4 bytes (which starts at the third byte) of that structure.  I go over that in the next section.

* ### Painless and Intelligent Get and Set Methods
	The worst part about working with data on the binary level is the constant fear of making an off-by-one error or messing up and assigning a value that is too large for the field, but instead of catching the error and complaining, the field just silently truncates the input data and carries along.  To address this, I have created a set of flexible and intelligent methods to aid the developer in whatever binary-level task they are carrying out.

	Continued from the code example above:

		# Getting values is as simple as can be
		>>> class_instance.first_6_bits
		0
		>>> class_instance.first_6_bits_as_bits
		'000000'

		# Setting values as well
		>>> class_instance.first_6_bits = 5
		>>> class_instance.first_6_bits
		5
		>>> class_instance.first_6_bits_as_bits
		'000101'
		>>> class_instance.first_6_bits_again
		5

		>>> class_instance.first_6_bits_as_bits = '111000'
		# OR
		>>> class_instance.first_6_bits_as_bits = '111_000' # Any '_' in the bits will be ignored by Python

		# You can even format and display the binary values as easily as you want
		>>> class_instance._group_size = 4
		>>> class_instance._group_separator = '_'
		>>> class_instance.long_as_bits
		'0000_0000_0000_0000_0000_0000_0000_0000'

	You'll notice that even though in the field declaration in the first code bubble we didn't define any "as_bits" fields, they were set automatically behind the scenes for us to use as a convenience. 

	This way, you have both the exact number of bits exactly as they are in the structure - ready for binary-level logic (and human debug inspection) - as well as the decimal representation for higher-level business logic both at the tips of your fingers.

	But that's not all!!  The setter methods also come with built-in safeguards to help prevent a nasty overflow from slipping silently by.  If you try to assign a value to a field that is larger than its count of bits allows, the library will raise a ValueError and tell you all about it.

		# Assign a 7-bit number to a 6-bit field
		>>> class_instance.first_6_bits = 0b1111111
		ValueError: The specified value "127" is larger than the segment "first_6_bits" can support (max value 63).

		# The same error happens if you try to assign it from the corresponding _as_bits as well
		>>> class_instance.first_6_bits_as_bits = '111_111_1'
		ValueError: The specified value "127" is larger than the segment "first_6_bits" can support (max value 63).


* ### Built-in Debugging Views of Your Structure
	If you're sifting around some data, trying to figure out why it isn't passing a test it should most definitely be passing, the first thing you're going to try to do is to create a different way to inspect your data.  While I know this is far from comprehensive, I have created two helper functions in this library that come bundled with every structure to act as a quick first step.

	They are the **format_details()** and **print_bytes()** functions.  Here is what they look like.

		# bytes_per_line is 10 by default
		>>> class_instance.print_bytes(bytes_per_line=10)
		00000000 00000000 00000000 00000000 00000000 00000000 

		# display_format is 'decimal' by default
		>>> print(class_instance.format_details())
		== BitField Details ==
			first_6_bits               : 0
			first_6_bits_as_bits       : 000000
			first_6_bits_again         : 0
			first_6_bits_again_as_bits : 000000
			cross_byte_boundary        : 0
			cross_byte_boundary_as_bits: 000000
			long_first_byte            : 0
			long_first_byte_as_bits    : 00000000
			long                       : 0
			long_as_bits               : 00000000000000000000000000000000

		# It is also important to note that the "_as_bits" representations in
		# format_details will be influenced by the instance's _group_size and _group_separator
		>>> class_instance._group_separator = '_'
		>>> class_instance._group_size = 8
		>>> print(class_instance.format_details(data_display='hex'))
		== BitField Details ==
			first_6_bits               : 0x0
			first_6_bits_as_bits       : 000000
			first_6_bits_again         : 0x0
			first_6_bits_again_as_bits : 000000
			cross_byte_boundary        : 0x0
			cross_byte_boundary_as_bits: 000000
			long_first_byte            : 0x0
			long_first_byte_as_bits    : 00000000
			long                       : 0x0
			long_as_bits               : 00000000_00000000_00000000_00000000

	The list of details can be sorted alphabetically (ASCII order, so caps
	first) or in the order they were specified in the ruleset with the
	display_order parameter

		>>> print(class_instance.format_details(display_format='hex', display_order='alphabetic'))
		== BitField Details ==
			cross_byte_boundary        : 0x0
			cross_byte_boundary_as_bits: 000000
			first_6_bits               : 0x0
			first_6_bits_again         : 0x0
			first_6_bits_again_as_bits : 000000
			first_6_bits_as_bits       : 000000
			long                       : 0x0
			long_as_bits               : 00000000_00000000_00000000_00000000
			long_first_byte            : 0x0
			long_first_byte_as_bits    : 00000000



