import os
import numpy as np
import struct



def write_imgs_bmp(image ,filepath):
    with open(filepath, 'wb+') as f:
        f.write(get_buffer(image))


def get_buffer(image_data):
    [im_height, im_width] = np.shape(image_data)
    bpp = 16 if np.max(image_data) > 255 else 8

    write_buffer = bytearray(im_width * im_height * bpp / 8 + 1500)

    a = bytearray(image_data)

    struct.pack_into('<L', write_buffer, 0,
                     int((np.binary_repr(ord('M'), width=8) + np.binary_repr(ord('B'), width=8)), 2))
    struct.pack_into('<L', write_buffer, 2, im_width * im_height * bpp / 8 + 1500)  # size of the file
    struct.pack_into('<L', write_buffer, 10, 70)  # the byte where the image data begins
    struct.pack_into('<L', write_buffer, 14, 40)  # size of this header
    struct.pack_into('<L', write_buffer, 18, im_width)  # width
    struct.pack_into('<L', write_buffer, 22, im_height)  # height
    struct.pack_into('<L', write_buffer, 26, 1)  # number of colour planes
    struct.pack_into('<L', write_buffer, 28, bpp)  # bits per pixel
    struct.pack_into('<L', write_buffer, 30, 0)  # compression method
    struct.pack_into('<L', write_buffer, 34, 0)  # dummy image size
    struct.pack_into('<L', write_buffer, 38, 3000)  # horizontal pixels per meter
    struct.pack_into('<L', write_buffer, 42, 3000)  # vertical pixels per meter
    struct.pack_into('<L', write_buffer, 46, 0)  # dummy colour info
    struct.pack_into('<L', write_buffer, 50, 0)  # dummy colour info

    if bpp == 8:  # this is if the image is in Mono8 mode (8 bits per pixel)
        for i in range(256):
            bin_string = np.binary_repr(i, width=8)
            int_to_write = int('00000000' + bin_string + bin_string + bin_string, 2)
            struct.pack_into('<L', write_buffer, 54 + 4 * i, int_to_write)

        row_size = int(np.floor((8 * im_width + 31) / 32.) * 4)
        last_offset = 1074

        for i in range(im_height)[::-1]:
            current = row_size * i
            for j in range(row_size / 4):
                last_offset += 4
                write_buffer[last_offset] = a[current]  # first pixel
                write_buffer[last_offset + 1] = a[current + 1]  # next pixel
                write_buffer[last_offset + 2] = a[current + 2]  # third pixel
                write_buffer[last_offset + 3] = a[current + 3]  # last pixel in this byte
                current += 4

    elif bpp == 16:  # this is if the image is in Mono16 mode (16 bits per pixel)
        struct.pack_into('<L', write_buffer, 30, 3)  # change compression method to use colour maps

        struct.pack_into('>L', write_buffer, 54 + 0, int('0000FFFF', 16))  # red bits - will contain nothing
        struct.pack_into('>L', write_buffer, 54 + 4, int('FF000000', 16))  # green bits - will contain MSB
        struct.pack_into('>L', write_buffer, 54 + 8, int('00FF0000', 16))  # blue bits - will contain LSB

        last_offset = 54 + 12

        # this saves the MSB digits into the green channel, and LSB into blue channel in little endian format (X,Blue,Green,Red)
        # here the LSB is only 6 bits, leaving the 2 last bits as 0
        for i in range(im_height)[::-1]:
            current = 2 * im_width * i
            for j in range(im_width / 2):
                last_offset += 4
                write_buffer[last_offset + 1] = a[current + 0]  # LSB to the blue channel
                write_buffer[last_offset + 0] = a[current + 1]  # MSB to the green channel
                # next pixel
                write_buffer[last_offset + 3] = a[current + 2]  # LSB to the blue channel
                write_buffer[last_offset + 2] = a[current + 3]  # MSB to the green channel
                current += 4
    return write_buffer