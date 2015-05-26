This repo contains some development tools.

## android/bootimg/

Used to pack/unpack android boot/recovery image. I use them as follow:

* Dump boot.img from android phone
* unpack boot.img
* Change something like property in the ramdisk
* Repack boot.img
* Flash new boot.img back to android phone

## unpack.py

Used to unpack pseudo crypt zip/apk file.

## android/verify\_ota.py

Used to verify an ota file against a certificate file in x509 format.
