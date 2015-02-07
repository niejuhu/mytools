#!/usr/bin/python

"""
Usage: packbootimage --args <args> --kernel <kernel> --ramdisk <ramdisk> [--second <second>] [--dt <dt>] --output <boot.img>

"""

import sys
import os
import getopt
import struct
import hashlib

BOOT_IMG_HDR_STRUCT = "8sIIIIIIIIII16s512s32s"
BOOT_MAGIC = "ANDROID!"
DEBUG = False

def usage():
    print "Usage: packbootimage --args <args> --kernel <kernel> --ramdisk <ramdisk> [--second <second>] [--dt <dt>] --output <boot.img>"

def loadFromFile(filename):
    if DEBUG:
        print "loadFromFile" + filename

    size = os.path.getsize(filename)
    f = open(filename, "rb")
    data = f.read()
    f.close()

    return data, size

def writeData(data, size, page_size, f):
    f.write(data)
    padding = page_size - (size % page_size)
    if padding != page_size:
        f.write(struct.pack("%ds" % (padding), "\x00"))

def main(argv):
    opts, args = getopt.getopt(argv, "", [
        "kernel=",
        "ramdisk=",
        "args=",
        "second=",
        "dt=",
        "output="])

    kernel = ""
    ramdisk = ""
    args = ""
    second = ""
    dt = ""
    output = "newboot.img"
    for k, v in opts:
        if k == "--kernel":
            kernel = v
        elif k == "--ramdisk":
            ramdisk = v
        elif k == "--args":
            args = v
        elif k == "--second":
            second = v
        elif k == "--dt":
            dt = v
        elif k == "--output":
            output = v
    if not (kernel and ramdisk and args):
        usage()
        return

    kernel_addr = ramdisk_addr = page_size = -1
    tags_addr = 0
    second_addr = 0
    name = struct.pack("16s", "\x00" * 16)
    cmdline = struct.pack("512s", "\x00" * 512)
    argsfile = open(args, "r")
    try:
        for line in argsfile:
            if line.startswith("Kernel:"):
                kernel_addr = int(line[len("Kernel:"):-1])
            elif line.startswith("Ramdisk:"):
                ramdisk_addr = int(line[len("Ramdisk:"):-1])
            elif line.startswith("PageSize:"):
                page_size = int(line[len("PageSize:"):-1])
                if DEBUG: print page_size
            elif line.startswith("Cmdline:"):
                cmdline = line[len("Cmdline:"):-1]
                if DEBUG: print cmdline
            elif line.startswith("Name:"):
                name = line[len("Name:"):-1]
                if DEBUG: print name
            elif line.startswith("Second:"):
                second_addr = int(line[len("Second:"):-1])
            elif line.startswith("Tags:"):
                tags_addr = int(line[len("Tags:"):-1])
    finally:
        argsfile.close()

    if kernel_addr < 0 or ramdisk_addr < 0 or page_size < 0:
        print "invalid args file"
        return

    sha1 = hashlib.sha1()
    kernel, kernel_size = loadFromFile(kernel)
    sha1.update(kernel)
    sha1.update(struct.pack("I", kernel_size))

    ramdisk, ramdisk_size = loadFromFile(ramdisk)
    sha1.update(ramdisk)
    sha1.update(struct.pack("I", ramdisk_size))

    if second:
        second, second_size = loadFromFile(second)
        sha1.update(second)
    else:
        second = 0
        second_size = 0
    sha1.update(struct.pack("I", second_size))

    if dt:
        dt, dt_size = loadFromFile(dt)
        sha1.update(dt)
        sha1.update(struct.pack("I", dt_size))
    else:
        dt_size = 0

    signature = sha1.digest()

    hdr = struct.pack(BOOT_IMG_HDR_STRUCT, BOOT_MAGIC,
            kernel_size, kernel_addr, ramdisk_size, ramdisk_addr,
            second_size, second_addr, tags_addr, page_size,
            dt_size, 0, name, cmdline, signature[:32])
    hdr_size = struct.calcsize(BOOT_IMG_HDR_STRUCT)
    if DEBUG:
        print hdr

    outf = open(output, "wb")
    writeData(hdr, hdr_size, page_size, outf)
    writeData(kernel, kernel_size, page_size, outf)
    writeData(ramdisk, ramdisk_size, page_size, outf)
    if second:
        writeData(second, second_size, page_size, outf)
    if dt:
        writeData(dt, dt_size, page_size, outf)
    outf.close()

if __name__ == "__main__":
    main(sys.argv[1:])
