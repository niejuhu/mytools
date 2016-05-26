#!/usr/bin/env python3

####
# Search symbols from kernel binary file and print them in the format of /proc/kallsyms.
#
# See the kernel source file scripts/kallsyms.c for more information.
####

import argparse
import ctypes
import struct
import sys

MATCH_COUNT = 10000

arch_constants = {
        "arm" : {
            "first" : 0xc0008000,
            "ptr_unpack_str" : "<I",
            "ptr_len" : 4,
            "align" : 16,
            },
        "arm64" : {
            "first" : 0xffffffc0080000,
            "ptr_unpack_str" : "<Q",
            "ptr_len" : 8,
            "align" : 256,
            },
        }

def upalign(pos, align):
    return (pos + align - 1) & (~(align - 1))

def search(data, consts, first):
    first = ctypes.c_uint32(int(first)).value if first else ctypes.c_uint(consts["first"]).value
    #print("len(data): {:x}, first: {:2x}".format(len(data), first))
    addresses = -1 # begin of address
    names = -1 # begin of names
    has_type_table = False
    markers = -1
    token_table = -1
    token_index = -1

    pos = 0

    # search addresses
    count = 0
    prev = 0
    while pos < len(data):
        #current, = struct.unpack("<I", data[pos:pos+4])
        current, = struct.unpack(consts["ptr_unpack_str"], data[pos:pos+consts["ptr_len"]])
        pos += consts["ptr_len"]
        if current >= first:
            if count == 0:
                addresses = pos - consts["ptr_len"]
                count = 1
                prev = current
                continue

            if current >= prev:
                count += 1
                prev = current
                # print("pos: {:8x}, count: {}".format(pos, count))
                continue

        if count > MATCH_COUNT:
            syms_num = current
            subpos = pos
            while syms_num == 0:
                #syms_num, = struct.unpack("<I", data[subpos:subpos+4])
                syms_num, = struct.unpack(consts["ptr_unpack_str"],
                        data[subpos:subpos+consts["ptr_len"]])
                subpos += consts["ptr_len"]
            if syms_num == count or syms_num == count + 1:
                pos = subpos
                #print("count: {} syms_num: {} pos: {:x}".format(count, syms_num, pos))
                break
        addresses = -1
        count = 0

    if syms_num == count + 1:
        addresses -= consts["ptr_len"]
    #print("addresses: {:x}".format(addresses))
    #print("syms_num: {}".format(syms_num))

    # search names 
    pos = upalign(pos, consts["align"])
    names = pos
    #print("names: {:x}".format(names))

    # search end of name
    for i in range(syms_num):
        length, = struct.unpack("B", data[pos:pos+1])
        pos += length + 1
    pos = upalign(pos, consts["align"])

    # markers
    markers = pos
    #print("markers: {:x}".format(markers))

    # skip markers
    num_markers = (syms_num - 1 >> 8) + 1
    pos += num_markers * consts["ptr_len"]
    pos = upalign(pos, consts["align"])

    # token table
    token_table = pos
    #print("token table: {:x}".format(token_table))

    # search end of token table
    while True:
        if data[pos] == 0 and data[pos + 1] == 0:
            pos += 1
            break
        pos += 1
    pos = upalign(pos, consts["align"])

    # token index
    token_index = pos
    #print("token index: {:x}".format(token_index))

    # print symbols
    for i in range(syms_num):
        name = []
        p = addresses + i * consts["ptr_len"]
        addr, = struct.unpack(consts["ptr_unpack_str"], data[p:p+consts["ptr_len"]])
        #print("addr: {:x}".format(addr))

        p = markers + (i >> 8) * consts["ptr_len"]
        r = i % 256
        off, = struct.unpack(consts["ptr_unpack_str"], data[p:p+consts["ptr_len"]])
        p = names + off
        j = 0
        while j < r:
            l, = struct.unpack("B", data[p:p+1])
            p += l + 1
            j += 1
        l, = struct.unpack("B", data[p:p+1])
        p += 1
        #print("symbol: {:x}, len: {:x}".format(p, l))

        for k in range(l):
            index = data[p + k]
            off = token_index + index * 2
            token, = struct.unpack("<H", data[off : off+2])
            #print("index: {:x} token: {:x}".format(index, token))
            while data[token_table + token] != 0:
                name.append(chr(data[token_table + token]))
                token += 1
        typ = name[0]
        name = "".join(name[1:])
        print("{:08x} {} {}".format(addr, typ, name))

def search_kallsyms(kernel, arch, first):
    with open(kernel, "rb") as f:
        data = f.read()
        constants = arch_constants[arch]
        search(data, constants, first)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kernel", help="kernel binary")
    parser.add_argument("arch", help="architecture", choices=["arm", "arm64"])
    parser.add_argument("--first", help="the first symbol address")
    args = parser.parse_args()
    search_kallsyms(args.kernel, args.arch, args.first)
