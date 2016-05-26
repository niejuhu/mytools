#!/usr/bin/env python3

####
# Convert /proc/kallsyms file to idc script which can be load by ida.
####

import sys

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: {} symbols".format(sys.argv[0]))
        sys.exit(1)

    with open(sys.argv[1]) as f:
        with open(sys.argv[1] + ".idc", "w") as wf:
            wf.write("#include <idc.idc>\n")
            wf.write("static main()\n")
            wf.write("{\n")
            for line in f.readlines():
                tokens = line.strip().split(" ")
                wf.write('MakeName(0X{}, "{}");\n'.format(tokens[0], tokens[2]))
                wf.write('MakeCode(0X{});\n'.format(tokens[0]))
            wf.write("}\n")
