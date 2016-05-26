#!/usr/bin/env python3

####
# Search the compressed kernel from zImage file.
####

import sys

def search_pattern(heystack, needle, prefix):
    i = 0
    found = False
    while i < len(heystack) - len(needle):
        for j in range(len(needle)):
            if needle[j] != heystack[i + j]:
                break
        else:
            print("{}:{}".format(prefix, i))
            found = True
        i += 1
    return found

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} zImage".format(sys.argv[0]))
        sys.exit(1)

    with open(sys.argv[1], "rb") as f:
        data = f.read()
        if not search_pattern(data, [0xFD, 0x37, 0x7A, 0x58, 0x5A, 0x00], "xz"):
            if not search_pattern(data, [0x1f, 0x8b, 0x08], "gz"):
                if not search_pattern(data, [0x89, ord("L"), ord("Z"), ord("O"), 0x00], "lzo"):
                    if not search_pattern(data, [0x02, 0x21, 0x4c, 0x18], "lz4"):
                        pass
