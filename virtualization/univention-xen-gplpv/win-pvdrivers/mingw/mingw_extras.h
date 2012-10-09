#include <stdio.h>

#define __FUNCTION__ __func__

NTSTATUS bit_scan_forward(unsigned long *index, unsigned long mask);
int synch_set_bit(int nr, volatile long * addr);
int synch_clear_bit(int nr, volatile long * addr);

/* windows wchar 2 bytes, Linux's is 4! */
typedef unsigned short win_wchar_t;

NTSTATUS
RtlStringCbPrintfW(
  win_wchar_t *dest_str,
  size_t dest_size,
  win_wchar_t *format,
  ...);

