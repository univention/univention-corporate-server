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

#if !defined(_XENADDRESOURCE_H_)
#define _XENADDRESOURCE_H_

#define __attribute__(arg) /* empty */

#include <ntddk.h>
#include <wdm.h>
#include <wdf.h>
#include <initguid.h>
#include <wdmguid.h>
#include <errno.h>

#define NTSTRSAFE_LIB
#include <ntstrsafe.h>

#define __DRIVER_NAME "XenAddResource"
#include <xen_windows.h>

#include <memory.h>
#include <grant_table.h>
#include <event_channel.h>
#include <hvm/params.h>
#include <hvm/hvm_op.h>
#include <xen_public.h>

#define XENADDRESOURCE_POOL_TAG (ULONG) 'XenR'

#define NR_RESERVED_ENTRIES 8
#define NR_GRANT_FRAMES 4
#define NR_GRANT_ENTRIES (NR_GRANT_FRAMES * PAGE_SIZE / sizeof(grant_entry_t))

//#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))

#define ADDRESOURCE_DATA_MAGIC 0x12345678

/*
typedef struct {
  ULONG Magic;
  PXENPCI_XEN_DEVICE_DATA XenDeviceData;
  XEN_IFACE_EVTCHN EvtChnInterface;
  XEN_IFACE_XENBUS XenBusInterface;
  //XEN_IFACE_XEN XenInterface;
  XEN_IFACE_GNTTBL GntTblInterface;
} XENADDRESOURCE_DEVICE_DATA, *PXENADDRESOURCE_DEVICE_DATA;
*/
/*
typedef unsigned long xenbus_transaction_t;
typedef uint32_t XENSTORE_RING_IDX;

#define XBT_NIL ((xenbus_transaction_t)0)
*/

#endif
