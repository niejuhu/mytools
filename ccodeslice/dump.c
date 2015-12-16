#include <stdio.h>
#include <string.h>

#define print_func printf

/**
 * Dump the content of a buffer as follows:
 *
 *     -----+--------------------------------------------------+-----------------
 *     ADDR | 00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F | ASCII
 *     -----+--------------------------------------------------+-----------------
 *     0000 | 00 f6 58 3f fd 7f 00 00  e8 6a ab 88 51 7f 00 00 | ..X?.....j..Q...
 *     0010 | 00 00 00 00 00 00 00 00  78 3a ab 88 51 7f 00 00 | ........x:..Q...
 *     -----+--------------------------------------------------+-----------------
 *
 * @param data The buffer to be dump.
 * @param sz The size of the buffer.
 * @param addr_mode If set to 0 the ADDR column starts from 0, else it starts from
 *     the real address of the buffer.
 */
void dump(const char *data, size_t sz, int addr_mode)
{
    int i, j;
    int index, lines, last;
    unsigned long addr = 0;
    int addr_size = 4;

    if (data == NULL) {
        return;
    }

    if (addr_mode != 0) {
        addr = (unsigned long) data;
        addr_size = 2 * sizeof(unsigned long);
    }

    // Print header
    for (i=0; i<addr_size; i++) {
        print_func("-");
    }
    print_func("-+--------------------------------------------------+-----------------\n");
    print_func("ADDR");
    for (i=0; i<addr_size-(int)strlen("ADDR"); i++) {
        print_func(" ");
    }
    print_func(" | 00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F | ASCII\n");
    for (i=0; i<addr_size; i++) {
        print_func("-");
    }
    print_func("-+--------------------------------------------------+-----------------\n");

    // Print content
    lines = sz / 16;
    last = sz % 16;
    if (last) {
        ++lines;
    }
    index = 0;

    for (i=0; i<lines; i++, index+=16, addr += 16) {
        int end = (last && i==lines-1) ? last : 16;
        print_func("%0*lx |", addr_size, addr);
        for (j=0; j<end; j++) {
            char c = data[index+j];
            print_func(" %02x", (unsigned) c & 0xff);
            if (j == 7) {
                print_func(" ");
            }
        }
        while (j < 16) {
            print_func("   ");
            if (j == 7) {
                print_func(" ");
            }
            j++;
        }
        print_func(" | ");
        for (j=0; j<end; j++) {
            char c = data[index+j];
            if (c >= '!' && c <= '~') {
                print_func("%c", c);
            } else {
                print_func(".");
            }
        }
        print_func("\n");
    }
    // Print footer.
    for (i=0; i<addr_size; i++) {
        print_func("-");
    }
    print_func("-+--------------------------------------------------+-----------------\n");
}

int main()
{
    char a[100];
    char b[256];

    dump(a, sizeof(a), 0);
    dump(b, sizeof(b), 1);
    return 0;
}
