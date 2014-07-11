/*
PV Drivers for Windows Xen HVM Domains
Copyright (C) 2007 James Harper

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

#include "xenpci.h"

static BOOLEAN last_newline = TRUE;
static volatile LONG debug_print_lock = 0;

NTSTATUS
XenPci_DebugPrintV(PCHAR format, va_list args) {
  NTSTATUS status;
  KIRQL old_irql;
  CHAR buf[512]; /* truncate anything larger */
  ULONG i;
  ULONGLONG j;
  LARGE_INTEGER current_time;

  status = RtlStringCbVPrintfA(buf, ARRAY_SIZE(buf), format, args);  
  if (status != STATUS_SUCCESS)
    return status;
  KeRaiseIrql(HIGH_LEVEL, &old_irql);
  /* make sure that each print gets to complete in its entirety */
  while(InterlockedCompareExchange(&debug_print_lock, 1, 0) == 1)
    KeStallExecutionProcessor(1);
  for (i = 0; i < strlen(buf); i++) {
    /* only write a timestamp if the last character was a newline */
    if (last_newline) {
      KeQuerySystemTime(&current_time);
      current_time.QuadPart /= 10000; /* convert to ms */
      for (j = 1000000000000000000L; j >= 1; j /= 10)
        if (current_time.QuadPart / j)
          break;
      for (; j >= 1; j /= 10) {
        #pragma warning(suppress:28138)
        WRITE_PORT_UCHAR(XEN_IOPORT_LOG, '0' + (UCHAR)((current_time.QuadPart / j) % 10));
      }
      #pragma warning(suppress:28138)
      WRITE_PORT_UCHAR(XEN_IOPORT_LOG, ':');
      #pragma warning(suppress:28138)
      WRITE_PORT_UCHAR(XEN_IOPORT_LOG, ' ');
    }
    #pragma warning(suppress:28138)
    WRITE_PORT_UCHAR(XEN_IOPORT_LOG, buf[i]);
    last_newline = (buf[i] == '\n');
  }
  /* release the lock */
  InterlockedExchange(&debug_print_lock, 0);
  KeLowerIrql(old_irql);
  return status;
}

NTSTATUS
XenPci_DebugPrint(PCHAR format, ...) {
  NTSTATUS status;
  va_list args;
  
  va_start(args, format);
  status = XenPci_DebugPrintV(format, args);
  va_end(args);
  return status;
}