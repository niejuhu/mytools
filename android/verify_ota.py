#!/usr/bin/env python

"""
Verify an ota file against a certificate file in x509 format.
See android source code: bootable/recovery/verifyer.cpp:verify_file()
"""

import os
import sys
import struct
from M2Crypto import X509

FOOTER_SIZE = 6
RSANUMBYTES = 256
EOCD_HEADER_SIZE = 22

def usage():
    print "Usage: verify_ota.py ota_zip_file public_key_file"

def verify_ota_file(ota_filename, public_key_filename):
    with open(ota_filename, "rb") as ota_file:
        ota_file.seek(-FOOTER_SIZE, os.SEEK_END)
        footer_data = ota_file.read(FOOTER_SIZE)
        footer = struct.unpack("<HHH", footer_data)
        if footer[1] != 0xffff:
            print "failed to read footer"
            sys.exit(1)

        comment_size = footer[2]
        signature_start = footer[0]

        if signature_start - FOOTER_SIZE < RSANUMBYTES:
            print "signature is too short"
            sys.exit(1)

        eocd_size = comment_size + EOCD_HEADER_SIZE
        ota_file.seek(-eocd_size, os.SEEK_END)
        signed_len = ota_file.tell() + EOCD_HEADER_SIZE - 2
        eocd = ota_file.read(eocd_size)
        if not eocd[0:4] == "\x50\x4b\x05\x06":
            print "signature length doesn't match EOCD marker"
            sys.exit(1)

        i = 4
        while i < eocd_size - 3:
            if eocd[i:i+4] == "\x50\x4b\x05\x06":
                print "EOCD marker occurs after start of EOCD"
                sys.exit(1)
            i += 1

        ota_file.seek(0)
        signed_data = ota_file.read(signed_len)
        signature = eocd[eocd_size - FOOTER_SIZE - RSANUMBYTES:eocd_size - FOOTER_SIZE]
        x509 = X509.load_cert(public_key_filename)
        pubkey = x509.get_pubkey()
        print "Verifying..."
        pubkey.verify_init()
        pubkey.verify_update(signed_data)
        verify_ok = pubkey.verify_final(signature)
        if verify_ok == 1:
            print "Verify OK"
        else:
            print "verify failed"


if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)
    verify_ota_file(sys.argv[1], sys.argv[2])
