#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <wchar.h>

#define MBR_MAGIC 0xaa55
#define GPT_MAGIC "EFI PART"
#define GPT_ENTRY_NAME_LENGTH 72

/* Note sector size may not be 512 bytes */
#define SECTOR_SIZE 512

struct mbr_entry {
    uint8_t me_status;      /* Status of physical dirve */
    uint8_t me_first[3];    /* CHS address of first absolute sector */
    uint8_t me_type;        /* Partition type */
    uint8_t me_last[3];     /* CHS address of last absolute sector */
    uint32_t me_first_lba;  /* LBA of first absolute sector */
    uint32_t me_num_sectors;/* Number of sectors */
} __attribute__((packed));

struct mbr {
    uint8_t m_bca[446];             /* Bootstrap code area */
    struct mbr_entry m_entries[4];  /* Partition table */
    uint16_t m_magic;               /* Magic: 0xAA55 */
} __attribute__((packed));

struct gpt {
    char g_magic[8];        /* Magic: "EFI PART" */
    uint32_t g_revision;    /* Revision */
    uint32_t g_hdr_size;    /* Header size in little endian */
    uint32_t g_hdr_crc32;   /* CRC32/zlib of header */
    uint32_t g_reserved;    /* Reserved; must be zero */
    uint64_t g_hdr_off;     /* Current lba */
    uint64_t g_hdr_off_bu;  /* Backup lba */
    uint64_t g_first;       /* First usable lba for patitions */
    uint64_t g_last;        /* Last usable lba */
    uint8_t g_guid[16];     /* Disk guid */
    uint64_t g_entries_off; /* Starting lba of array of pattition entries */
    uint32_t g_entries_num; /* Number of partition entires */
    uint32_t g_entry_size;  /* Size of a single partition entry */
    uint32_t g_entries_crc32;   /* CRC32/zlib of partition array */
    uint8_t g_reserved2[0]; /* Reserved */
} __attribute__((packed));

struct gpt_entry {
    uint8_t ge_type_guid[16];   /* Partition type guid */
    uint8_t ge_guid[16];        /* Unique partition guid */
    uint64_t ge_first;          /* First lba (little endian) */
    uint64_t ge_last;           /* Last lba */
    uint64_t ge_flags;          /* Attribute flags */
    uint8_t ge_name[GPT_ENTRY_NAME_LENGTH];        /* Partition name (UTF-16LE) */
    uint8_t reserved[0];        /* Reserved */
} __attribute__((packed));

int main(int argc, char **argv)
{
    int fd;
    struct gpt gpt_buf;
    struct gpt_entry *entry = NULL;
    unsigned short mbr_magic;
    int ret = 1;
    int i, j;

    if (argc != 2) {
        fprintf(stderr, "Usage: %s <android-patition-table>\n", argv[0]);
        return ret;
    }

    if ((fd = open(argv[1], O_RDONLY)) == -1) {
        perror("open");
        return ret;
    }

    if (lseek(fd, sizeof(struct mbr) - sizeof(short), SEEK_SET) == -1) {
        perror("lseek");
        goto out;
    }
    if (read(fd, &mbr_magic, sizeof(mbr_magic)) == -1) {
        perror("read");
        goto out;
    }
    if (mbr_magic != (unsigned short) MBR_MAGIC) {
        printf("No mbr found! ignore\n");
    }

    if (read(fd, &gpt_buf, sizeof(gpt_buf)) != sizeof(gpt_buf)) {
        fprintf(stderr, "Can't read gpt\n");
        goto out;
    }
    if (strcmp(gpt_buf.g_magic, GPT_MAGIC)) {
        fprintf(stderr, "No gpt found\n");
        goto out;
    }
    if (lseek(fd, gpt_buf.g_entries_off * SECTOR_SIZE, SEEK_SET) == -1) {
        fprintf(stderr, "Can't seek to gpt entries\n");
        goto out;
    }
    entry = (struct gpt_entry *) malloc(gpt_buf.g_entry_size);
    if (! entry) {
        fprintf(stderr, "OOM\n");
        goto out;
    }
    for (i=0; i<gpt_buf.g_entries_num; ++i) {
        if (read(fd, entry, gpt_buf.g_entry_size) != gpt_buf.g_entry_size) {
            fprintf(stderr, "Failed to read gpt entry %d\n", i);
            goto out;
        }
        printf("p%d: ", i);
        for (j=0; j<GPT_ENTRY_NAME_LENGTH; j+=2) {
            if (entry->ge_name[j] == 0) {
                putchar('\n');
                break;
            }
            putchar(entry->ge_name[j]);
        }
    }
    ret = 0;

out:
    if (entry) {
        free(entry);
    }
    close(fd);
    return ret;
}
