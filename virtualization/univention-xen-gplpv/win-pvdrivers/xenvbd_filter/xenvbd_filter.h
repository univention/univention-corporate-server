/*
PV Drivers for Windows Xen HVM Domains
Copyright (C) 2013 James Harper

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

#if !defined(_XENVBD_H_)
#define _XENVBD_H_

#define __DRIVER_NAME "XenVbdFilter"

#include <ntddk.h>
#include <wdf.h>
#if (NTDDI_VERSION < NTDDI_WINXP) /* srb.h causes warnings under 2K for some reason */
#pragma warning(disable:4201) /* nameless struct/union */
#pragma warning(disable:4214) /* bit field types other than int */
#endif
#include <srb.h>
#include <ntstrsafe.h>
#include "xen_windows.h"
#include <xen_public.h>
#include <io/protocols.h>
#include <memory.h>
#include <event_channel.h>
#include <hvm/params.h>
#include <hvm/hvm_op.h>
#include <io/ring.h>
#include <io/blkif.h>
#include <io/xenbus.h>

#pragma warning(disable: 4127)

#if defined(__x86_64__)
  #define ABI_PROTOCOL "x86_64-abi"
#else
  #define ABI_PROTOCOL "x86_32-abi"
#endif

#include "../xenvbd_common/common.h"

#include "../xenvbd_scsiport/common.h"

typedef struct {
  WDFDEVICE wdf_device;
  WDFIOTARGET wdf_target;
  WDFDPC dpc;
  WDFQUEUE io_queue;
  BOOLEAN hibernate_flag;
  /* event state 0 = no event outstanding, 1 = event outstanding, 2 = need event */
  LONG event_state;
  
  XENVBD_DEVICE_DATA xvdd;
} XENVBD_FILTER_DATA, *PXENVBD_FILTER_DATA;

WDF_DECLARE_CONTEXT_TYPE_WITH_NAME(XENVBD_FILTER_DATA, GetXvfd)

#endif
