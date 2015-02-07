#!/usr/bin/python

"""
Unpack Android boot.img into kernel, ramdisk.img and other component files.

Usage: unpackbootimg [--outdir <out_dir>] <boot.img>

The file components are extract to seperate files, for example the kernel
is extract to <boot.img>-kernel. The arguments like page_size, cmdline are
write to a file named <boot.img>-args.

On default all the output file are write to the same folder as <boot.img>,
except you specify a folder by --outdir argument in which case output files
are write there.

"""

import sys
import struct
import getopt
import os

# struct boot_img_hdr
# {
#     unsigned char magic[BOOT_MAGIC_SIZE];
#     unsigned kernel_size;  /* size in bytes */
#     unsigned kernel_addr;  /* physical load addr */
#     unsigned ramdisk_size; /* size in bytes */
#     unsigned ramdisk_addr; /* physical load addr */
#     unsigned second_size;  /* size in bytes */
#     unsigned second_addr;  /* physical load addr */
#     unsigned tags_addr;    /* physical addr for kernel tags */
#     unsigned page_size;    /* flash page size we assume */
#     unsigned unused0;      /* device tree in bytes */
#     unsigned unused1;       /* future expansion: should be 0 */
#     unsigned char name[BOOT_NAME_SIZE]; /* asciiz product name */
#     unsigned char cmdline[BOOT_ARGS_SIZE];
#     unsigned id[8]; /* timestamp / checksum / sha1 / etc */
# };

BOOT_IMG_HDR_STRUCT = "8sIIIIIIIIII16s512s32s"
BOOT_MAGIC = "ANDROID!"
DEBUG = False

def usage():
    print "Usage: unpackbootimg [--outdir <out_dir>] <boot.img>"

def upalign(now, pagesize):
    return (now + pagesize) & (~(pagesize - 1))

def writeFile(filename, data, offset, length):
    f = open(filename, "w")
    f.write(data[offset : offset + length])
    f.close()

def main(argv):
    try:
        opts, args = getopt.getopt(argv, "", ["outdir="])
    except:
        usage()
        return

    if (len(args) != 1):
        usage()
        return

    outdir = os.path.dirname(args[0])
    if not outdir:
        outdir = "."
    for k, v in opts:
        if (k == "--outdir"):
            outdir = v
    prefix = outdir + "/" + os.path.basename(args[0]) + "-"

    # Read file content
    imgfile = open(args[0], "r")
    data = imgfile.read()
    offset = 0

    # Get header
    hdr = struct.unpack(BOOT_IMG_HDR_STRUCT, data[:struct.calcsize(BOOT_IMG_HDR_STRUCT)])
    if DEBUG: print hdr
    (magic, kernel_size, kernel_addr, ramdisk_size, ramdisk_addr,
        second_size, second_addr, tags_addr, page_size, dt_size,
        unused, name, cmdline, _id) = hdr
    offset += struct.calcsize(BOOT_IMG_HDR_STRUCT)
    offset = upalign(offset, page_size)

    if magic != BOOT_MAGIC:
        print "Not boot image!"
        return

    print "Kernel address:          0x%x" %(kernel_addr)
    print "Ramdisk address:         0x%x" %(ramdisk_addr)
    print "Page size:               %d"   %(page_size)
    print "Cmdline:                 %s"   %(cmdline)
    print "Product name:            %s"   %(name)
    print "Has second?              %r"   %(second_size != 0)
    print "Has dt?                  %r"   %(dt_size != 0)

    argfile = open(prefix + "args", "w")
    argfile.write("Kernel:%d\n" % (kernel_addr))
    argfile.write("Ramdisk:%d\n" % (ramdisk_addr))
    argfile.write("PageSize:%d\n" % (page_size))
    argfile.write("Cmdline:%s\n" % (cmdline))
    argfile.write("ProductName:%s\n" % (name))
    argfile.write("Second:%d\n" % (second_addr))
    argfile.write("Tags:%d\n" % (tags_addr))
    argfile.close()

    writeFile(prefix + "kernel", data, offset, kernel_size)
    offset += kernel_size
    offset = upalign(offset, page_size)

    writeFile(prefix + "ramdisk", data, offset, ramdisk_size)
    offset += ramdisk_size
    offset = upalign(offset, page_size)

    if second_size != 0:
        writeFile(prefix + "second", data, offset, second_size)
        offset += second_size
        offset = upalign(offset, page_size)

    if dt_size != 0:
        writeFile(prefix + "dt", data, offset, dt_size)
        offset += dt_size
        offset = upalign(offset, dt_size)

if __name__ == "__main__":
    main(sys.argv[1:])
