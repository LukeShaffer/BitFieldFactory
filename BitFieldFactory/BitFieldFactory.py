'''
The goal of this file, as stated in the branch Readme, is to create a master
BitField factory that can be passed a precompiled or user-generated ruleset
(or a list of BitField segments) and for the factory to spit out a working
Python class that allows simple and intuitive access to the fields of the
BitField as defined in the ruleset.
'''

from math import ceil
import sys


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def twos_comp(int_val, num_bits):
    '''
    Compute the twos compliment of an integer with the given bit width
    Returns an integer value
    '''
    # If the most significant bit is set, flip the bits
    if (int_val & (1 << (num_bits - 1))) != 0:
        int_val = int_val - (1 << num_bits)
    return val



class BitField():
    '''
    A base class that provides the basic wrapper around a byte-like object
    '''
    # This is a dummy default value, to be overwritten by each invocation of
    # BitField
    _num_bytes = -1

    def __init__(self, bin_data=None):
        if isinstance(bin_data, bytes):
            bin_data = bytearray(bin_data)

        if bin_data is None:
            bin_data = bytearray(b'\x00' * self._num_bytes)

        assert isinstance(bin_data, bytearray), 'Error creating BitField, '\
            'object constructor not passed a bytes or bytearray object.'

        assert len(bin_data) == self._num_bytes, 'Error constructing '\
            'BitField object: an improper length of data was passed in: {}'\
            '\nExpected {} bytes, got {} byte(s).'\
            .format(bin_data, self._num_bytes, len(bin_data))

        self.bytes = bin_data

    def get_help(self, segment_name):
        '''
        User function to return the help string of a segment, which is passed
        in at construction time.
        '''

        segment_name = segment_name.replace('_as_bits', '')

        return self._help_dict[segment_name]

    def format_details(self, display_format='decimal',
                       display_order='bit_order'):
        '''
        display formats of 'decimal' and 'hex' currently
        display orders = 'bit_order' and 'alphabetic'
        '''
        to_return = '== BitField Details ==\n'
        blacklist = ['get_help', 'format_details', 'print_bytes', 'bytes']

        attribute_names = [
            item for item in dir(self)
            if (not item.startswith('_') and item not in blacklist)]

        wid = len(max(attribute_names, key=len))

        if display_order == 'alphabetic':
            for item in attribute_names:
                if isinstance(self[item], int):
                    val = self[item]

                    if display_format == 'decimal':
                        val = val
                    elif display_format == 'hex':
                        val = hex(val)
                else:
                    # A string was passed in, eg: _as_bits
                    val = self[item]

                to_return += '\t{:{wid}}: {}\n'.format(item, val, wid=wid)

        elif display_order == 'bit_order':
            for segment_name in self._segment_order:
                for item in attribute_names:
                    if item.replace('_as_bits', '') == segment_name:
                        if isinstance(self[item], int):
                            val = self[item]
                            if display_format == 'decimal':
                                val = val
                            elif display_format == 'hex':
                                val = hex(val)
                        else:
                            # A string was passed in, eg: _as_bits
                            val = self[item]
                        to_return += '\t{:{w}}: {}\n'.format(item, val, w=wid)

                        if item.endswith('_as_bits'):
                                break
        return to_return

    def print_bytes(self, bytes_per_line=10):
        '''
        Prints BitField bytes in a binary format that is easy for humans
        to visually inspect for debugging
        '''
        formatted_string = ''

        for line in chunks(self.bytes, bytes_per_line):
            for byte in line:
                formatted_string += '{:08b} '.format(byte)
            formatted_string += '\n'

        print(formatted_string)

    # Create dict-access for the class
    def __getitem__(self, attr_name):
        return getattr(self, attr_name)

    def __setitem__(self, attr_name, value):
        setattr(self, attr_name, value)


class Segment():
    '''
    This is the class I will use to define each segment of a BitField.
    Basically, every slice of bits from a stream of bytes can be cordoned off
    into a named and easily accessible property of the parent BitField class
    by defining each named series of bits with the Segment class.

    This class also contains functionality for holding some help text for each
    field that can be retrieved with the BitField class's get_help() function
    called with the name of the segment.

    As there are situations where the segments of the miniheader for the same
    instrument can have different types (eg, in a mastcamz MiniHeader, bytes
    24-32 will mean different things based on what kind of data the miniheader
    is describing), the start_bit will need to be specified for each segment in
    the interest of keeping things simple.
    
    As of this latest update, we will now be supporting signed segments.  These
    will function completely identically to regular segments (which were
    initially coded as only unsigned) with the appropriate data checks and
    display.
    '''
    def __init__(self,  name='', start_bit=-1, bit_length=-1, is_signed=False, help=''):
        self.name = name
        self.start_bit = start_bit
        self.bit_length = bit_length
        self.is_signed = is_signed
        self.help = help

    @property
    def start_byte(self):
        return int(self.start_bit / 8)

    @property
    def end_byte(self):
        return int((self.start_bit + self.bit_length) / 8)

    @property
    def num_bytes(self):
        return self.end_byte - self.start_byte + 1

    @property
    def max_value(self):
        if not self.is_signed:
            return int('1' * self.bit_length, 2)
        else:
            return int('1' * (self.bit_length - 1), 2)

    @property
    def min_value(self):
        if not self.is_signed:
            return 0
        else:
            return 1 << (self.bit_length - 1)
    


def segment_funcs(segment):
    '''
    This function is used to dynanically create a getter and setter function
    for each bitfield segment's bit values.

    It parses the segment's details and creates two functions, one to get the
    value from the segment bits, and one to set those bits.

    "self" is the parent BitField object that the segment object belongs to.
    '''
    def getter(self):
        # print('getter starting for attribute: ', segment.name)
        to_return = 0
        current_byte = segment.start_byte

        # Iterate over the bits of the segment and construct the value to
        # return bit by bit.
        for bit in range(segment.start_bit, segment.start_bit + segment.bit_length):
            # print('Current byte number: ', current_byte)
            # print('byte under investigation: {} => {:08b}'.format(current_byte, self.bytes[current_byte]))
            # print('\tgetter searching bit number: ', bit)
            val = (self.bytes[current_byte] >> (7 - bit % 8)) & 1
            to_return = to_return << 1
            if val == 0:
                pass
                # to_return was already shifted, so the bottom bit is already 0
            elif val == 1:
                to_return |= val

            if (bit + 1) % 8 == 0:
                current_byte += 1
            # print('\tcurrent acuumulation: ', to_return)
        # print('getter ending, returning: ', hex(to_return))
        # New step, optionally interpret as a twos compliment number

        return to_return

    def setter(self, value):
        if isinstance(value, bytes) or isinstance(value, bytearray):
            value = int.from_bytes(value, byteorder='big')
        if value > segment.max_value:
            raise ValueError('The specified value "{}" is larger than '
                             'the segment "{}" can support (max value {}).'
                             .format(value, segment.name, segment.max_value))

        current_byte = segment.start_byte
        staging_byte = self.bytes[current_byte]
        val_bit = 0
        # Iterate over the bits of the segment of the mini_header
        for bit in range(segment.start_bit, segment.start_bit + segment.bit_length):
            # print('bit: ', bit, end=', ')
            val = (value >> ((segment.bit_length - 1) - val_bit)) & 1
            # print('val: ', val)
            if val == 0:
                staging_byte &= ~(1 << (7 - bit % 8))
            elif val == 1:
                staging_byte |= (1 << (7 - bit % 8))

            # Avoid index out of bounds increment below
            if bit == (segment.start_bit + segment.bit_length) - 1:
                break

            if (bit + 1) % 8 == 0:
                self.bytes[current_byte] = staging_byte
                current_byte += 1
                staging_byte = self.bytes[current_byte]

            val_bit += 1
        self.bytes[current_byte] = staging_byte

    return (getter, setter)


def segment_funcs_asbits(segment):
    '''
    The same as the above "segment_funcs" function, just with a wrapper to
    interpret literal strings of bits ('0010') as an integer value.
    '''
    def getter(self):
        # Use the actual getter function, and just format the data differently
        value = self[segment.name]
        raw_str = '{:0{width}b}'.format(value, width=segment.bit_length)

        formatted_string = ''
        for byte in chunks(raw_str, self._group_size):
            formatted_string += byte + self._group_separator

        return formatted_string.rstrip(self._group_separator)

    def setter(self, value):
        error_message = 'To set the as_bits version of a field, '\
            'use a literal bit-string like "110010" or "1111_0000".'
        assert isinstance(value, str), error_message
        try:
            value = int(value, 2)
        except ValueError:
            print(error_message, file=sys.stderr)
        # Pass the work off to the actual setter function
        self[segment.name] = value

    return (getter, setter)


def new_class(class_name, segments):
    '''
    `segments` is just an iterable of Segment objects you want
    to include in your BitField.  Order matters when you specify these and the
    lsb must be last (the order throughout will determine the order that fields
    appear in the debugging view functions).
    '''
    # First set up a proto-BitField using a cheat from the last segment
    # IMPORTANT - this assumes that the segments will be listed in order and
    # is mostly just a convenience for me during the prototyping phase
    last_segment = segments[-1]
    bf_length = last_segment.start_bit + last_segment.bit_length
    bf_length = ceil(bf_length / 8)

    # Funky magic to create a dynamic class with name class_name, inheriting
    # from BitField, with its own namespace (last argument)

    # Anything listed here will not show up in the __dict__ of an instantiated
    # class, but will still be present as an attribute on it
    to_return = type(class_name, (BitField,), {
        '__init__': BitField.__init__,
        '_help_dict': {},
        '_segment_order': [],
        '_num_bytes': bf_length,
        '_group_size': 8,
        '_group_separator': '',
        }
    )

    # "Register" the name of the class in this file's scope
    globals()[class_name] = to_return

    # Now do the work of populating the bit-segments into the bitfield
    for segment in segments:
        # Keep track of bit order while adding segments
        to_return._segment_order.append(segment.name)

        # Add the getters and setters for each segment
        fget, fset = segment_funcs(segment)
        fget_asb, fset_asb = segment_funcs_asbits(segment)

        setattr(to_return, segment.name, property(fget=fget, fset=fset))
        setattr(to_return, segment.name + '_as_bits', property(fget=fget_asb, fset=fset_asb))

        # Hook up the get_help() function for this segment
        to_return._help_dict[segment.name] = segment.help

    return to_return
