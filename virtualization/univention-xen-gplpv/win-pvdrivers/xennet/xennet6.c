/*
PV Net Driver for Windows Xen HVM Domains
Copyright (C) 2007 James Harper
Copyright (C) 2007 Andrew Grover <andy.grover@oracle.com>

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

#include <stdlib.h>
#include <io/xenbus.h>
#include "xennet6.h"

/* Not really necessary but keeps PREfast happy */
DRIVER_INITIALIZE DriverEntry;
static IO_WORKITEM_ROUTINE XenNet_ResumeWorkItem;
#if (VER_PRODUCTBUILD >= 7600)
static KDEFERRED_ROUTINE XenNet_SuspendResume;
static KDEFERRED_ROUTINE XenNet_RxTxDpc;
#endif

#pragma NDIS_INIT_FUNCTION(DriverEntry)

NDIS_HANDLE driver_handle = NULL;

USHORT ndis_os_major_version = 0;
USHORT ndis_os_minor_version = 0;

/* ----- BEGIN Other people's code --------- */
/* from linux/include/linux/ctype.h, used under GPLv2 */
#define _U      0x01    /* upper */
#define _L      0x02    /* lower */
#define _D      0x04    /* digit */
#define _C      0x08    /* cntrl */
#define _P      0x10    /* punct */
#define _S      0x20    /* white space (space/lf/tab) */
#define _X      0x40    /* hex digit */
#define _SP     0x80    /* hard space (0x20) */

/* from linux/include/lib/ctype.c, used under GPLv2 */
unsigned char _ctype[] = {
_C,_C,_C,_C,_C,_C,_C,_C,                        /* 0-7 */
_C,_C|_S,_C|_S,_C|_S,_C|_S,_C|_S,_C,_C,         /* 8-15 */
_C,_C,_C,_C,_C,_C,_C,_C,                        /* 16-23 */
_C,_C,_C,_C,_C,_C,_C,_C,                        /* 24-31 */
_S|_SP,_P,_P,_P,_P,_P,_P,_P,                    /* 32-39 */
_P,_P,_P,_P,_P,_P,_P,_P,                        /* 40-47 */
_D,_D,_D,_D,_D,_D,_D,_D,                        /* 48-55 */
_D,_D,_P,_P,_P,_P,_P,_P,                        /* 56-63 */
_P,_U|_X,_U|_X,_U|_X,_U|_X,_U|_X,_U|_X,_U,      /* 64-71 */
_U,_U,_U,_U,_U,_U,_U,_U,                        /* 72-79 */
_U,_U,_U,_U,_U,_U,_U,_U,                        /* 80-87 */
_U,_U,_U,_P,_P,_P,_P,_P,                        /* 88-95 */
_P,_L|_X,_L|_X,_L|_X,_L|_X,_L|_X,_L|_X,_L,      /* 96-103 */
_L,_L,_L,_L,_L,_L,_L,_L,                        /* 104-111 */
_L,_L,_L,_L,_L,_L,_L,_L,                        /* 112-119 */
_L,_L,_L,_P,_P,_P,_P,_C,                        /* 120-127 */
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,                /* 128-143 */
0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,                /* 144-159 */
_S|_SP,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,   /* 160-175 */
_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,_P,       /* 176-191 */
_U,_U,_U,_U,_U,_U,_U,_U,_U,_U,_U,_U,_U,_U,_U,_U,       /* 192-207 */
_U,_U,_U,_U,_U,_U,_U,_P,_U,_U,_U,_U,_U,_U,_U,_L,       /* 208-223 */
_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,       /* 224-239 */
_L,_L,_L,_L,_L,_L,_L,_P,_L,_L,_L,_L,_L,_L,_L,_L};      /* 240-255 */

/* from linux/include/linux/ctype.h, used under GPLv2 */
#define __ismask(x) (_ctype[(int)(unsigned char)(x)])

#define isalnum(c)      ((__ismask(c)&(_U|_L|_D)) != 0)
#define isalpha(c)      ((__ismask(c)&(_U|_L)) != 0)
#define iscntrl(c)      ((__ismask(c)&(_C)) != 0)
#define isdigit(c)      ((__ismask(c)&(_D)) != 0)
#define isgraph(c)      ((__ismask(c)&(_P|_U|_L|_D)) != 0)
#define islower(c)      ((__ismask(c)&(_L)) != 0)
#define isprint(c)      ((__ismask(c)&(_P|_U|_L|_D|_SP)) != 0)
#define ispunct(c)      ((__ismask(c)&(_P)) != 0)
#define isspace(c)      ((__ismask(c)&(_S)) != 0)
#define isupper(c)      ((__ismask(c)&(_U)) != 0)
#define isxdigit(c)     ((__ismask(c)&(_D|_X)) != 0)

#define TOLOWER(x) ((x) | 0x20)

/* from linux/lib/vsprintf.c, used under GPLv2 */
/* Copyright (C) 1991, 1992  Linus Torvalds
 * Wirzenius wrote this portably, Torvalds fucked it up :-)
 */
/**
 * simple_strtoul - convert a string to an unsigned long
 * @cp: The start of the string
 * @endp: A pointer to the end of the parsed string will be placed here
 * @base: The number base to use
 */
unsigned long simple_strtoul(const char *cp,char **endp,unsigned int base)
{
  unsigned long result = 0,value;

  if (!base) {
    base = 10;
    if (*cp == '0') {
      base = 8;
      cp++;
      if ((TOLOWER(*cp) == 'x') && isxdigit(cp[1])) {
        cp++;
        base = 16;
      }
    }
  } else if (base == 16) {
    if (cp[0] == '0' && TOLOWER(cp[1]) == 'x')
      cp += 2;
  }
  while (isxdigit(*cp) &&
    (value = isdigit(*cp) ? *cp-'0' : TOLOWER(*cp)-'a'+10) < base) {
    result = result*base + value;
    cp++;
  }
  if (endp)
    *endp = (char *)cp;
  return result;
}
/* end vsprintf.c code */
/* ----- END Other people's code --------- */

static NDIS_STATUS
XenNet_ConnectBackend(struct xennet_info *xi)
{
  PUCHAR ptr;
  UCHAR type;
  PCHAR setting, value, value2;
  UINT i;

  FUNCTION_ENTER();
  
  NT_ASSERT(KeGetCurrentIrql() < DISPATCH_LEVEL);

  xi->backend_csum_supported = TRUE; /* just assume this */
  xi->backend_gso_value = 0;
  xi->backend_sg_supported = FALSE;
  
  ptr = xi->config_page;
  while((type = GET_XEN_INIT_RSP(&ptr, (PVOID)&setting, (PVOID)&value, (PVOID)&value2)) != XEN_INIT_TYPE_END)
  {
    switch(type)
    {
    case XEN_INIT_TYPE_RING: /* frontend ring */
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_RING - %s = %p\n", setting, value));
      if (strcmp(setting, "tx-ring-ref") == 0)
      {
        FRONT_RING_INIT(&xi->tx, (netif_tx_sring_t *)value, PAGE_SIZE);
      } else if (strcmp(setting, "rx-ring-ref") == 0)
      {
        FRONT_RING_INIT(&xi->rx, (netif_rx_sring_t *)value, PAGE_SIZE);
      }
      break;
    case XEN_INIT_TYPE_EVENT_CHANNEL: /* frontend event channel */
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_EVENT_CHANNEL - %s = %d\n", setting, PtrToUlong(value)));
      if (strcmp(setting, "event-channel") == 0)
      {
        xi->event_channel = PtrToUlong(value);
      }
      break;
    case XEN_INIT_TYPE_READ_STRING_FRONT:
      break;
    case XEN_INIT_TYPE_READ_STRING_BACK:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_READ_STRING - %s = %s\n", setting, value));
      if (strcmp(setting, "mac") == 0)
      {
        char *s, *e;
        s = value;
        for (i = 0; i < ETH_ALEN; i++) {
          xi->perm_mac_addr[i] = (uint8_t)simple_strtoul(s, &e, 16);
          if ((s == e) || (*e != ((i == ETH_ALEN-1) ? '\0' : ':'))) {
            KdPrint((__DRIVER_NAME "Error parsing MAC address\n"));
          }
          s = e + 1;
        }
        if ((xi->curr_mac_addr[0] & 0x03) != 0x02)
        {
          /* only copy if curr_mac_addr is not a LUA */
          memcpy(xi->curr_mac_addr, xi->perm_mac_addr, ETH_ALEN);
        }
      }
      else if (strcmp(setting, "feature-sg") == 0)
      {
        if (atoi(value))
        {
          xi->backend_sg_supported = TRUE;
        }
      }
      else if (strcmp(setting, "feature-gso-tcpv4") == 0)
      {
        if (atoi(value))
        {
          xi->backend_gso_value = xi->frontend_gso_value;
        }
      }
      break;
    case XEN_INIT_TYPE_VECTORS:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_VECTORS\n"));
      if (((PXENPCI_VECTORS)value)->length != sizeof(XENPCI_VECTORS) ||
        ((PXENPCI_VECTORS)value)->magic != XEN_DATA_MAGIC)
      {
        KdPrint((__DRIVER_NAME "     vectors mismatch (magic = %08x, length = %d)\n",
          ((PXENPCI_VECTORS)value)->magic, ((PXENPCI_VECTORS)value)->length));
        FUNCTION_EXIT();
        return NDIS_STATUS_ADAPTER_NOT_FOUND;
      }
      else
        memcpy(&xi->vectors, value, sizeof(XENPCI_VECTORS));
      break;
    case XEN_INIT_TYPE_STATE_PTR:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_DEVICE_STATE - %p\n", PtrToUlong(value)));
      xi->device_state = (PXENPCI_DEVICE_STATE)value;
      break;
    default:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_%d\n", type));
      break;
    }
  }
  if (!xi->backend_sg_supported)
    xi->backend_gso_value = min(xi->backend_gso_value, PAGE_SIZE - MAX_PKT_HEADER_LENGTH);

  xi->current_sg_supported = xi->frontend_sg_supported && xi->backend_sg_supported;
  xi->current_csum_supported = xi->frontend_csum_supported && xi->backend_csum_supported;
  xi->current_gso_value = min(xi->backend_gso_value, xi->backend_gso_value);
  xi->current_mtu_value = xi->frontend_mtu_value;
  xi->current_gso_rx_split_type = xi->frontend_gso_rx_split_type;
    
  FUNCTION_EXIT();
  
  return NDIS_STATUS_SUCCESS;
} /* XenNet_ConnectBackend */

static VOID
XenNet_ResumeWorkItem(PDEVICE_OBJECT device_object, PVOID context)
{
  struct xennet_info *xi = context;
  KIRQL old_irql;
  
  UNREFERENCED_PARAMETER(device_object);
  
  FUNCTION_ENTER();

  NT_ASSERT(xi->resume_work_item);

  IoFreeWorkItem(xi->resume_work_item);
  
  XenNet_TxResumeStart(xi);
  XenNet_RxResumeStart(xi);
  XenNet_ConnectBackend(xi);
  XenNet_RxResumeEnd(xi);
  XenNet_TxResumeEnd(xi);

  KeAcquireSpinLock(&xi->resume_lock, &old_irql);
  xi->resume_work_item = NULL;
  KdPrint((__DRIVER_NAME "     *Setting suspend_resume_state_fdo = %d\n", xi->device_state->suspend_resume_state_pdo));
  xi->device_state->suspend_resume_state_fdo = xi->device_state->suspend_resume_state_pdo;
  KdPrint((__DRIVER_NAME "     *Notifying event channel %d\n", xi->device_state->pdo_event_channel));
  xi->vectors.EvtChn_Notify(xi->vectors.context, xi->device_state->pdo_event_channel);
  KeReleaseSpinLock(&xi->resume_lock, old_irql);

  FUNCTION_EXIT();

}

static VOID
XenNet_SuspendResume(PKDPC dpc, PVOID context, PVOID arg1, PVOID arg2)
{
  struct xennet_info *xi = context;
  KIRQL old_irql;
  PIO_WORKITEM resume_work_item;

  UNREFERENCED_PARAMETER(dpc);
  UNREFERENCED_PARAMETER(arg1);
  UNREFERENCED_PARAMETER(arg2);

  FUNCTION_ENTER();
  
  switch (xi->device_state->suspend_resume_state_pdo)
  {
  case SR_STATE_SUSPENDING:
    KdPrint((__DRIVER_NAME "     New state SUSPENDING\n"));
    KeAcquireSpinLock(&xi->rx_lock, &old_irql);
    if (xi->rx_id_free == NET_RX_RING_SIZE)
    {  
      xi->device_state->suspend_resume_state_fdo = SR_STATE_SUSPENDING;
      KdPrint((__DRIVER_NAME "     Notifying event channel %d\n", xi->device_state->pdo_event_channel));
      xi->vectors.EvtChn_Notify(xi->vectors.context, xi->device_state->pdo_event_channel);
    }
    KeReleaseSpinLock(&xi->rx_lock, old_irql);
    break;
  case SR_STATE_RESUMING:
    KdPrint((__DRIVER_NAME "     New state SR_STATE_RESUMING\n"));
    /* do it like this so we don't race and double-free the work item */
    resume_work_item = IoAllocateWorkItem(xi->fdo);
    KeAcquireSpinLock(&xi->resume_lock, &old_irql);
    if (xi->resume_work_item || xi->device_state->suspend_resume_state_fdo == SR_STATE_RESUMING)
    {
      KeReleaseSpinLock(&xi->resume_lock, old_irql);
      IoFreeWorkItem(resume_work_item);
      return;
    }
    xi->resume_work_item = resume_work_item;
    KeReleaseSpinLock(&xi->resume_lock, old_irql);
    IoQueueWorkItem(xi->resume_work_item, XenNet_ResumeWorkItem, DelayedWorkQueue, xi);
    break;
  default:
    KdPrint((__DRIVER_NAME "     New state %d\n", xi->device_state->suspend_resume_state_fdo));
    xi->device_state->suspend_resume_state_fdo = xi->device_state->suspend_resume_state_pdo;
    KdPrint((__DRIVER_NAME "     Notifying event channel %d\n", xi->device_state->pdo_event_channel));
    xi->vectors.EvtChn_Notify(xi->vectors.context, xi->device_state->pdo_event_channel);
    break;
  }
  KeMemoryBarrier();
  
  FUNCTION_EXIT();
}

static VOID
XenNet_RxTxDpc(PKDPC dpc, PVOID context, PVOID arg1, PVOID arg2)
{
  struct xennet_info *xi = context;
  BOOLEAN dont_set_event;

  UNREFERENCED_PARAMETER(dpc);
  UNREFERENCED_PARAMETER(arg1);
  UNREFERENCED_PARAMETER(arg2);

  //FUNCTION_ENTER();
  /* if Rx goes over its per-dpc quota then make sure TxBufferGC doesn't set an event as we are already guaranteed to be called again */
  dont_set_event = XenNet_RxBufferCheck(xi);
  XenNet_TxBufferGC(xi, dont_set_event);
  //FUNCTION_EXIT();
} 

static BOOLEAN
XenNet_HandleEvent(PVOID context)
{
  struct xennet_info *xi = context;
  ULONG suspend_resume_state_pdo;
  
  //FUNCTION_ENTER();
  suspend_resume_state_pdo = xi->device_state->suspend_resume_state_pdo;
  KeMemoryBarrier();

  if (!xi->shutting_down && suspend_resume_state_pdo != xi->device_state->suspend_resume_state_fdo)
  {
    KeInsertQueueDpc(&xi->suspend_dpc, NULL, NULL);
  }
  if (xi->connected && !xi->inactive && suspend_resume_state_pdo != SR_STATE_RESUMING)
  {
    KeInsertQueueDpc(&xi->rxtx_dpc, NULL, NULL);
  }
  //FUNCTION_EXIT();
  return TRUE;
}

#if 0
VOID
XenNet_SetPower(PDEVICE_OBJECT device_object, PVOID context)
{
  NTSTATUS status = STATUS_SUCCESS;
  KIRQL old_irql;
  struct xennet_info *xi = context;
  
  FUNCTION_ENTER();
  UNREFERENCED_PARAMETER(device_object);

  switch (xi->new_power_state)
  {
  case NdisDeviceStateD0:
    KdPrint(("       NdisDeviceStateD0\n"));
    status = XenNet_D0Entry(xi);
    break;
  case NdisDeviceStateD1:
    KdPrint(("       NdisDeviceStateD1\n"));
    if (xi->power_state == NdisDeviceStateD0)
      status = XenNet_D0Exit(xi);
    break;
  case NdisDeviceStateD2:
    KdPrint(("       NdisDeviceStateD2\n"));
    if (xi->power_state == NdisDeviceStateD0)
      status = XenNet_D0Exit(xi);
    break;
  case NdisDeviceStateD3:
    KdPrint(("       NdisDeviceStateD3\n"));
    if (xi->power_state == NdisDeviceStateD0)
      status = XenNet_D0Exit(xi);
    break;
  default:
    KdPrint(("       NdisDeviceState??\n"));
    status = NDIS_STATUS_NOT_SUPPORTED;
    break;
  }
  xi->power_state = xi->new_power_state;

  old_irql = KeRaiseIrqlToDpcLevel();
  NdisMSetInformationComplete(xi->adapter_handle, status);
  KeLowerIrql(old_irql);
  
  FUNCTION_EXIT();
}
#endif

NDIS_STATUS
XenNet_D0Entry(struct xennet_info *xi)
{
  NDIS_STATUS status;
  PUCHAR ptr;
  CHAR buf[128];
  
  FUNCTION_ENTER();

  xi->shutting_down = FALSE;
  
  ptr = xi->config_page;
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_RING, "tx-ring-ref", NULL, NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_RING, "rx-ring-ref", NULL, NULL);
  #pragma warning(suppress:4054)
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_EVENT_CHANNEL, "event-channel", (PVOID)XenNet_HandleEvent, xi);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_READ_STRING_BACK, "mac", NULL, NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_READ_STRING_BACK, "feature-sg", NULL, NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_READ_STRING_BACK, "feature-gso-tcpv4", NULL, NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_WRITE_STRING, "request-rx-copy", "1", NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_WRITE_STRING, "feature-rx-notify", "1", NULL);
  RtlStringCbPrintfA(buf, ARRAY_SIZE(buf), "%d", !xi->frontend_csum_supported);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_WRITE_STRING, "feature-no-csum-offload", buf, NULL);
  RtlStringCbPrintfA(buf, ARRAY_SIZE(buf), "%d", (int)xi->frontend_sg_supported);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_WRITE_STRING, "feature-sg", buf, NULL);
  RtlStringCbPrintfA(buf, ARRAY_SIZE(buf), "%d", !!xi->frontend_gso_value);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_WRITE_STRING, "feature-gso-tcpv4", buf, NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_XB_STATE_MAP_PRE_CONNECT, NULL, NULL, NULL);
  __ADD_XEN_INIT_UCHAR(&ptr, 0); /* no pre-connect required */
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_XB_STATE_MAP_POST_CONNECT, NULL, NULL, NULL);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateConnected);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateConnected);
  __ADD_XEN_INIT_UCHAR(&ptr, 20);
  __ADD_XEN_INIT_UCHAR(&ptr, 0);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_XB_STATE_MAP_SHUTDOWN, NULL, NULL, NULL);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateClosing);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateClosing);
  __ADD_XEN_INIT_UCHAR(&ptr, 50);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateClosed);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateClosed);
  __ADD_XEN_INIT_UCHAR(&ptr, 50);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateInitialising);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateInitWait);
  __ADD_XEN_INIT_UCHAR(&ptr, 50);
  __ADD_XEN_INIT_UCHAR(&ptr, 0);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_END, NULL, NULL, NULL);

  status = xi->vectors.XenPci_XenConfigDevice(xi->vectors.context);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Failed to complete device configuration (%08x)\n", status));
    return status;
  }

  status = XenNet_ConnectBackend(xi);
  
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Failed to complete device configuration (%08x)\n", status));
    return status;
  }

  XenNet_TxInit(xi);
  XenNet_RxInit(xi);

  xi->connected = TRUE;

  KeMemoryBarrier(); // packets could be received anytime after we set Frontent to Connected

  FUNCTION_EXIT();

  return status;
}

// Called at <= DISPATCH_LEVEL
static NDIS_STATUS
XenNet_Initialize(NDIS_HANDLE adapter_handle, NDIS_HANDLE driver_context, PNDIS_MINIPORT_INIT_PARAMETERS init_parameters)
{
  NDIS_STATUS status;
  struct xennet_info *xi = NULL;
  PNDIS_RESOURCE_LIST nrl;
  PCM_PARTIAL_RESOURCE_DESCRIPTOR prd;
  NDIS_HANDLE config_handle;
  NDIS_STRING config_param_name;
  NDIS_CONFIGURATION_OBJECT config_object;
  PNDIS_CONFIGURATION_PARAMETER config_param;
  //PNDIS_MINIPORT_ADAPTER_ATTRIBUTES adapter_attributes;
  ULONG i;
  PUCHAR ptr;
  UCHAR type;
  PCHAR setting, value;
  ULONG length;
  //CHAR buf[128];
  PVOID network_address;
  UINT network_address_length;
  BOOLEAN qemu_hide_filter = FALSE;
  ULONG qemu_hide_flags_value = 0;
  NDIS_MINIPORT_ADAPTER_REGISTRATION_ATTRIBUTES registration_attributes;
  NDIS_MINIPORT_ADAPTER_GENERAL_ATTRIBUTES general_attributes;
  NDIS_MINIPORT_ADAPTER_OFFLOAD_ATTRIBUTES offload_attributes;
  NDIS_OFFLOAD df_offload, hw_offload;
  NDIS_TCP_CONNECTION_OFFLOAD df_conn_offload, hw_conn_offload;
  static NDIS_OID *supported_oids;

  UNREFERENCED_PARAMETER(driver_context);

  FUNCTION_ENTER();

  /* Alloc memory for adapter private info */
  status = NdisAllocateMemoryWithTag((PVOID)&xi, sizeof(*xi), XENNET_POOL_TAG);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("NdisAllocateMemoryWithTag failed with 0x%x\n", status));
    status = NDIS_STATUS_RESOURCES;
    goto err;
  }
  RtlZeroMemory(xi, sizeof(*xi));
  xi->adapter_handle = adapter_handle;
  xi->rx_target     = RX_DFL_MIN_TARGET;
  xi->rx_min_target = RX_DFL_MIN_TARGET;
  xi->rx_max_target = RX_MAX_TARGET;
  xi->inactive      = TRUE;
  
  xi->multicast_list_size = 0;
  xi->current_lookahead = MIN_LOOKAHEAD_LENGTH;

  xi->event_channel = 0;
  xi->stats.Header.Type = NDIS_OBJECT_TYPE_DEFAULT;
  xi->stats.Header.Revision = NDIS_STATISTICS_INFO_REVISION_1;
  xi->stats.Header.Size = NDIS_SIZEOF_STATISTICS_INFO_REVISION_1;
  xi->stats.SupportedStatistics = NDIS_STATISTICS_XMIT_OK_SUPPORTED
    | NDIS_STATISTICS_RCV_OK_SUPPORTED
    | NDIS_STATISTICS_XMIT_ERROR_SUPPORTED
    | NDIS_STATISTICS_RCV_ERROR_SUPPORTED
    | NDIS_STATISTICS_RCV_NO_BUFFER_SUPPORTED
    | NDIS_STATISTICS_DIRECTED_BYTES_XMIT_SUPPORTED
    | NDIS_STATISTICS_DIRECTED_FRAMES_XMIT_SUPPORTED
    | NDIS_STATISTICS_MULTICAST_BYTES_XMIT_SUPPORTED
    | NDIS_STATISTICS_MULTICAST_FRAMES_XMIT_SUPPORTED
    | NDIS_STATISTICS_BROADCAST_BYTES_XMIT_SUPPORTED
    | NDIS_STATISTICS_BROADCAST_FRAMES_XMIT_SUPPORTED
    | NDIS_STATISTICS_DIRECTED_BYTES_RCV_SUPPORTED
    | NDIS_STATISTICS_DIRECTED_FRAMES_RCV_SUPPORTED
    | NDIS_STATISTICS_MULTICAST_BYTES_RCV_SUPPORTED
    | NDIS_STATISTICS_MULTICAST_FRAMES_RCV_SUPPORTED
    | NDIS_STATISTICS_BROADCAST_BYTES_RCV_SUPPORTED
    | NDIS_STATISTICS_BROADCAST_FRAMES_RCV_SUPPORTED
    | NDIS_STATISTICS_RCV_CRC_ERROR_SUPPORTED
    | NDIS_STATISTICS_TRANSMIT_QUEUE_LENGTH_SUPPORTED
    | NDIS_STATISTICS_BYTES_RCV_SUPPORTED
    | NDIS_STATISTICS_BYTES_XMIT_SUPPORTED
    | NDIS_STATISTICS_RCV_DISCARDS_SUPPORTED
    | NDIS_STATISTICS_GEN_STATISTICS_SUPPORTED
    | NDIS_STATISTICS_XMIT_DISCARDS_SUPPORTED;
  
  nrl = init_parameters->AllocatedResources;
  for (i = 0; i < nrl->Count; i++)
  {
    prd = &nrl->PartialDescriptors[i];

    switch(prd->Type)
    {
    case CmResourceTypeInterrupt:
      break;
    case CmResourceTypeMemory:
      if (xi->config_page)
      {
        KdPrint(("More than one memory range\n"));
        return NDIS_STATUS_RESOURCES;
      }
      else
      {
        status = NdisMMapIoSpace(&xi->config_page, xi->adapter_handle, prd->u.Memory.Start, prd->u.Memory.Length);
        if (!NT_SUCCESS(status))
        {
          KdPrint(("NdisMMapIoSpace failed with 0x%x\n", status));
          return NDIS_STATUS_RESOURCES;
        }
      }
      break;
    }
  }
  if (!xi->config_page)
  {
    KdPrint(("No config page given\n"));
    return NDIS_STATUS_RESOURCES;
  }

  KeInitializeDpc(&xi->suspend_dpc, XenNet_SuspendResume, xi);
  KeInitializeSpinLock(&xi->resume_lock);

  KeInitializeDpc(&xi->rxtx_dpc, XenNet_RxTxDpc, xi);
  KeSetTargetProcessorDpc(&xi->rxtx_dpc, 0);
  KeSetImportanceDpc(&xi->rxtx_dpc, HighImportance);

  NdisMGetDeviceProperty(xi->adapter_handle, &xi->pdo, &xi->fdo,
    &xi->lower_do, NULL, NULL);
  xi->packet_filter = 0;

  status = IoGetDeviceProperty(xi->pdo, DevicePropertyDeviceDescription,
    NAME_SIZE, xi->dev_desc, &length);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("IoGetDeviceProperty failed with 0x%x\n", status));
    status = NDIS_STATUS_FAILURE;
    goto err;
  }

  ptr = xi->config_page;
  while((type = GET_XEN_INIT_RSP(&ptr, (PVOID)&setting, (PVOID)&value, (PVOID)&value)) != XEN_INIT_TYPE_END)
  {
    switch(type)
    {
    case XEN_INIT_TYPE_VECTORS:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_VECTORS\n"));
      if (((PXENPCI_VECTORS)value)->length != sizeof(XENPCI_VECTORS) ||
        ((PXENPCI_VECTORS)value)->magic != XEN_DATA_MAGIC)
      {
        KdPrint((__DRIVER_NAME "     vectors mismatch (magic = %08x, length = %d)\n",
          ((PXENPCI_VECTORS)value)->magic, ((PXENPCI_VECTORS)value)->length));
        FUNCTION_EXIT();
        return NDIS_STATUS_FAILURE;
      }
      else
        memcpy(&xi->vectors, value, sizeof(XENPCI_VECTORS));
      break;
    case XEN_INIT_TYPE_STATE_PTR:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_DEVICE_STATE - %p\n", PtrToUlong(value)));
      xi->device_state = (PXENPCI_DEVICE_STATE)value;
      break;
    case XEN_INIT_TYPE_QEMU_HIDE_FLAGS:
      qemu_hide_flags_value = PtrToUlong(value);
      break;
    case XEN_INIT_TYPE_QEMU_HIDE_FILTER:
      qemu_hide_filter = TRUE;
      break;
    default:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_%d\n", type));
      break;
    }
  }

  if ((qemu_hide_flags_value & QEMU_UNPLUG_ALL_IDE_DISKS) || qemu_hide_filter)
    xi->inactive = FALSE;

  xi->power_state = NdisDeviceStateD0;
  xi->power_workitem = IoAllocateWorkItem(xi->fdo);

  // now build config page
  
  config_object.Header.Size = sizeof(NDIS_CONFIGURATION_OBJECT);
  config_object.Header.Type = NDIS_OBJECT_TYPE_CONFIGURATION_OBJECT;
  config_object.Header.Revision = NDIS_CONFIGURATION_OBJECT_REVISION_1;
  config_object.NdisHandle = xi->adapter_handle;
  config_object.Flags = 0;

  status = NdisOpenConfigurationEx(&config_object, &config_handle);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not open config in registry (%08x)\n", status));
    status = NDIS_STATUS_RESOURCES;
    goto err;
  }

  NdisInitUnicodeString(&config_param_name, L"ScatterGather");
  NdisReadConfiguration(&status, &config_param, config_handle, &config_param_name, NdisParameterInteger);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not read ScatterGather value (%08x)\n", status));
    xi->frontend_sg_supported = TRUE;
  }
  else
  {
    KdPrint(("ScatterGather = %d\n", config_param->ParameterData.IntegerData));
    xi->frontend_sg_supported = !!config_param->ParameterData.IntegerData;
  }
  if (xi->frontend_sg_supported && ndis_os_minor_version < 1) {
    FUNCTION_MSG("No support for SG with NDIS 6.0, disabled\n");
    xi->frontend_sg_supported = FALSE;
  }
  
  NdisInitUnicodeString(&config_param_name, L"LargeSendOffload");
  NdisReadConfiguration(&status, &config_param, config_handle, &config_param_name, NdisParameterInteger);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not read LargeSendOffload value (%08x)\n", status));
    xi->frontend_gso_value = 0;
  }
  else
  {
    KdPrint(("LargeSendOffload = %d\n", config_param->ParameterData.IntegerData));
    xi->frontend_gso_value = config_param->ParameterData.IntegerData;
    if (xi->frontend_gso_value > 61440)
    {
      xi->frontend_gso_value = 61440;
      KdPrint(("(clipped to %d)\n", xi->frontend_gso_value));
    }
    if (!xi->frontend_sg_supported && xi->frontend_gso_value > PAGE_SIZE - MAX_PKT_HEADER_LENGTH)
    {
      /* without SG, GSO can be a maximum of PAGE_SIZE - MAX_PKT_HEADER_LENGTH */
      xi->frontend_gso_value = min(xi->frontend_gso_value, PAGE_SIZE - MAX_PKT_HEADER_LENGTH);
      KdPrint(("(clipped to %d with sg disabled)\n", xi->frontend_gso_value));
    }
  }
  if (xi->frontend_sg_supported && ndis_os_minor_version < 1) {
    FUNCTION_MSG("No support for GSO with NDIS 6.0, disabled\n");
    xi->frontend_gso_value = 0;
  }

  NdisInitUnicodeString(&config_param_name, L"LargeSendOffloadRxSplitMTU");
  NdisReadConfiguration(&status, &config_param, config_handle, &config_param_name, NdisParameterInteger);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not read LargeSendOffload value (%08x)\n", status));
    xi->frontend_gso_rx_split_type = RX_LSO_SPLIT_HALF;
  }
  else
  {
    KdPrint(("LargeSendOffloadRxSplitMTU = %d\n", config_param->ParameterData.IntegerData));
    switch (config_param->ParameterData.IntegerData)
    {
    case RX_LSO_SPLIT_MSS:
    case RX_LSO_SPLIT_HALF:
    case RX_LSO_SPLIT_NONE:
      xi->frontend_gso_rx_split_type = config_param->ParameterData.IntegerData;
      break;
    default:
      xi->frontend_gso_rx_split_type = RX_LSO_SPLIT_HALF;
      break;
    }
  }

  NdisInitUnicodeString(&config_param_name, L"ChecksumOffload");
  NdisReadConfiguration(&status, &config_param, config_handle, &config_param_name, NdisParameterInteger);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not read ChecksumOffload value (%08x)\n", status));
    xi->frontend_csum_supported = TRUE;
  }
  else
  {
    KdPrint(("ChecksumOffload = %d\n", config_param->ParameterData.IntegerData));
    xi->frontend_csum_supported = !!config_param->ParameterData.IntegerData;
  }

  NdisInitUnicodeString(&config_param_name, L"MTU");
  NdisReadConfiguration(&status, &config_param, config_handle, &config_param_name, NdisParameterInteger);  
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not read MTU value (%08x)\n", status));
    xi->frontend_mtu_value = 1500;
  }
  else
  {
    KdPrint(("MTU = %d\n", config_param->ParameterData.IntegerData));
    xi->frontend_mtu_value = config_param->ParameterData.IntegerData;
  }
  
  NdisReadNetworkAddress(&status, &network_address, &network_address_length, config_handle);
  if (!NT_SUCCESS(status) || network_address_length != ETH_ALEN || ((((PUCHAR)network_address)[0] & 0x03) != 0x02))
  {
    KdPrint(("Could not read NetworkAddress value (%08x) or value is invalid\n", status));
    memset(xi->curr_mac_addr, 0, ETH_ALEN);
  }
  else
  {
    memcpy(xi->curr_mac_addr, network_address, ETH_ALEN);
    KdPrint(("     Set MAC address from registry to %02X:%02X:%02X:%02X:%02X:%02X\n",
      xi->curr_mac_addr[0], xi->curr_mac_addr[1], xi->curr_mac_addr[2], 
      xi->curr_mac_addr[3], xi->curr_mac_addr[4], xi->curr_mac_addr[5]));
  }

  NdisCloseConfiguration(config_handle);

  status = XenNet_D0Entry(xi);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Failed to go to D0 (%08x)\n", status));
    goto err;
  }

  xi->config_max_pkt_size = max(xi->current_mtu_value + XN_HDR_SIZE, xi->current_gso_value + XN_HDR_SIZE);
    
  registration_attributes.Header.Type = NDIS_OBJECT_TYPE_MINIPORT_ADAPTER_REGISTRATION_ATTRIBUTES;
  registration_attributes.Header.Revision = NDIS_MINIPORT_ADAPTER_REGISTRATION_ATTRIBUTES_REVISION_1;
  registration_attributes.Header.Size = NDIS_SIZEOF_MINIPORT_ADAPTER_REGISTRATION_ATTRIBUTES_REVISION_1;
  registration_attributes.MiniportAdapterContext = xi;
  registration_attributes.AttributeFlags = 0;
  registration_attributes.AttributeFlags |= NDIS_MINIPORT_ATTRIBUTES_HARDWARE_DEVICE;
  registration_attributes.AttributeFlags |= NDIS_MINIPORT_ATTRIBUTES_SURPRISE_REMOVE_OK;
  registration_attributes.CheckForHangTimeInSeconds = 0; /* use default */
  registration_attributes.InterfaceType = NdisInterfacePNPBus;
  status = NdisMSetMiniportAttributes(xi->adapter_handle, (PNDIS_MINIPORT_ADAPTER_ATTRIBUTES)&registration_attributes);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("NdisMSetMiniportAttributes(registration) failed (%08x)\n", status));
    goto err;
  }
  
  general_attributes.Header.Type = NDIS_OBJECT_TYPE_MINIPORT_ADAPTER_GENERAL_ATTRIBUTES;
  general_attributes.Header.Revision = NDIS_MINIPORT_ADAPTER_GENERAL_ATTRIBUTES_REVISION_1; /* revision 2 is NDIS 6.2 */
  general_attributes.Header.Size = NDIS_SIZEOF_MINIPORT_ADAPTER_GENERAL_ATTRIBUTES_REVISION_1;
  general_attributes.Flags = 0;
  general_attributes.MediaType = NdisMedium802_3;
  general_attributes.PhysicalMediumType = NdisPhysicalMediumOther;
  general_attributes.MtuSize = xi->current_mtu_value;
  general_attributes.MaxXmitLinkSpeed = MAX_LINK_SPEED;
  general_attributes.XmitLinkSpeed = MAX_LINK_SPEED;
  general_attributes.MaxRcvLinkSpeed = MAX_LINK_SPEED;
  general_attributes.RcvLinkSpeed = MAX_LINK_SPEED;
  general_attributes.MediaConnectState = MediaConnectStateConnected;
  general_attributes.MediaDuplexState = MediaDuplexStateFull;
  general_attributes.LookaheadSize = xi->current_lookahead;
  general_attributes.PowerManagementCapabilities = NULL;
  general_attributes.MacOptions = NDIS_MAC_OPTION_COPY_LOOKAHEAD_DATA | 
        NDIS_MAC_OPTION_TRANSFERS_NOT_PEND |
        NDIS_MAC_OPTION_NO_LOOPBACK;
  general_attributes.SupportedPacketFilters = SUPPORTED_PACKET_FILTERS;
  general_attributes.MaxMulticastListSize = MULTICAST_LIST_MAX_SIZE;
  general_attributes.MacAddressLength = 6;
  NdisMoveMemory(general_attributes.PermanentMacAddress, xi->perm_mac_addr, general_attributes.MacAddressLength);
  NdisMoveMemory(general_attributes.CurrentMacAddress, xi->curr_mac_addr, general_attributes.MacAddressLength);
  general_attributes.RecvScaleCapabilities = NULL; /* we do want to support this soon */
  general_attributes.AccessType = NET_IF_ACCESS_BROADCAST;
  general_attributes.DirectionType = NET_IF_DIRECTION_SENDRECEIVE;
  general_attributes.ConnectionType = NET_IF_CONNECTION_DEDICATED;
  general_attributes.IfType = IF_TYPE_ETHERNET_CSMACD;
  general_attributes.IfConnectorPresent = TRUE;
  general_attributes.SupportedStatistics = xi->stats.SupportedStatistics;
  general_attributes.SupportedPauseFunctions = NdisPauseFunctionsUnsupported;
  general_attributes.DataBackFillSize = 0; // see NdisRetreatNetBufferDataStart
  general_attributes.ContextBackFillSize = 0; // ?? NFI ??
  
  for (i = 0; xennet_oids[i].oid; i++);
  
  status = NdisAllocateMemoryWithTag((PVOID)&supported_oids, sizeof(NDIS_OID) * i, XENNET_POOL_TAG);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("NdisAllocateMemoryWithTag failed with 0x%x\n", status));
    status = NDIS_STATUS_RESOURCES;
    goto err;
  }

  for (i = 0; xennet_oids[i].oid; i++)
  {
    supported_oids[i] = xennet_oids[i].oid;
    FUNCTION_MSG("Supporting %08x (%s) %s %d bytes\n", xennet_oids[i].oid, xennet_oids[i].oid_name, (xennet_oids[i].query_routine?(xennet_oids[i].set_routine?"get/set":"get only"):(xennet_oids[i].set_routine?"set only":"none")), xennet_oids[i].min_length);
  }
  general_attributes.SupportedOidList = supported_oids;
  general_attributes.SupportedOidListLength = sizeof(NDIS_OID) * i;
  general_attributes.AutoNegotiationFlags = NDIS_LINK_STATE_XMIT_LINK_SPEED_AUTO_NEGOTIATED
    | NDIS_LINK_STATE_RCV_LINK_SPEED_AUTO_NEGOTIATED
    | NDIS_LINK_STATE_DUPLEX_AUTO_NEGOTIATED;
  //general_attributes.PowerManagementCapabilitiesEx = NULL; // >= 6.20
  status = NdisMSetMiniportAttributes(xi->adapter_handle, (PNDIS_MINIPORT_ADAPTER_ATTRIBUTES)&general_attributes);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("NdisMSetMiniportAttributes(general) failed (%08x)\n", status));
    goto err;
  }
  NdisFreeMemory(supported_oids, 0, 0);
    
  /* this is the initial offload state */
  RtlZeroMemory(&df_offload, sizeof(df_offload));
  df_offload.Header.Type = NDIS_OBJECT_TYPE_OFFLOAD;
  df_offload.Header.Revision = NDIS_OFFLOAD_REVISION_1; // revision 2 does exist
  df_offload.Header.Size = NDIS_SIZEOF_NDIS_OFFLOAD_REVISION_1;
  /* this is the supported offload state */
  RtlZeroMemory(&hw_offload, sizeof(hw_offload));
  hw_offload.Header.Type = NDIS_OBJECT_TYPE_OFFLOAD;
  hw_offload.Header.Revision = NDIS_OFFLOAD_REVISION_1; // revision 2 does exist
  hw_offload.Header.Size = NDIS_SIZEOF_NDIS_OFFLOAD_REVISION_1;
  if (xi->current_csum_supported)
  {
    df_offload.Checksum.IPv4Transmit.Encapsulation = NDIS_ENCAPSULATION_IEEE_802_3;
    df_offload.Checksum.IPv4Transmit.IpOptionsSupported = NDIS_OFFLOAD_SET_ON;
    df_offload.Checksum.IPv4Transmit.TcpOptionsSupported = NDIS_OFFLOAD_SET_ON;
    df_offload.Checksum.IPv4Transmit.TcpChecksum = NDIS_OFFLOAD_SET_ON;
    df_offload.Checksum.IPv4Transmit.UdpChecksum = NDIS_OFFLOAD_SET_ON;
    df_offload.Checksum.IPv4Transmit.IpChecksum = NDIS_OFFLOAD_SET_ON;
    df_offload.Checksum.IPv4Receive.Encapsulation = NDIS_ENCAPSULATION_IEEE_802_3;
    df_offload.Checksum.IPv4Receive.IpOptionsSupported = NDIS_OFFLOAD_SET_ON;
    df_offload.Checksum.IPv4Receive.TcpOptionsSupported = NDIS_OFFLOAD_SET_ON;
    df_offload.Checksum.IPv4Receive.TcpChecksum = NDIS_OFFLOAD_SET_ON;
    df_offload.Checksum.IPv4Receive.UdpChecksum = NDIS_OFFLOAD_SET_ON;
    df_offload.Checksum.IPv4Receive.IpChecksum = NDIS_OFFLOAD_SET_ON;
    /* offload.Checksum.IPv6Transmit is not supported */
    /* offload.Checksum.IPv6Receive is not supported */
    hw_offload.Checksum.IPv4Transmit.Encapsulation = NDIS_ENCAPSULATION_IEEE_802_3;
    hw_offload.Checksum.IPv4Transmit.IpOptionsSupported = NDIS_OFFLOAD_SUPPORTED;
    hw_offload.Checksum.IPv4Transmit.TcpOptionsSupported = NDIS_OFFLOAD_SUPPORTED;
    hw_offload.Checksum.IPv4Transmit.TcpChecksum = NDIS_OFFLOAD_SUPPORTED;
    hw_offload.Checksum.IPv4Transmit.UdpChecksum = NDIS_OFFLOAD_SUPPORTED;
    hw_offload.Checksum.IPv4Transmit.IpChecksum = NDIS_OFFLOAD_SUPPORTED;
    hw_offload.Checksum.IPv4Receive.Encapsulation = NDIS_ENCAPSULATION_IEEE_802_3;
    hw_offload.Checksum.IPv4Receive.IpOptionsSupported = NDIS_OFFLOAD_SUPPORTED;
    hw_offload.Checksum.IPv4Receive.TcpOptionsSupported = NDIS_OFFLOAD_SUPPORTED;
    hw_offload.Checksum.IPv4Receive.TcpChecksum = NDIS_OFFLOAD_SUPPORTED;
    hw_offload.Checksum.IPv4Receive.UdpChecksum = NDIS_OFFLOAD_SUPPORTED;
    hw_offload.Checksum.IPv4Receive.IpChecksum = NDIS_OFFLOAD_SUPPORTED;
    /* hw_offload.Checksum.IPv6Transmit is not supported */
    /* hw_offload.Checksum.IPv6Receive is not supported */
  }
  if (xi->current_gso_value)
  {
    hw_offload.LsoV1.IPv4.Encapsulation = NDIS_ENCAPSULATION_IEEE_802_3;
    hw_offload.LsoV1.IPv4.MaxOffLoadSize = xi->current_gso_value;
    hw_offload.LsoV1.IPv4.MinSegmentCount = MIN_LARGE_SEND_SEGMENTS;
    hw_offload.LsoV1.IPv4.TcpOptions = NDIS_OFFLOAD_NOT_SUPPORTED; /* linux can't handle this */
    hw_offload.LsoV1.IPv4.IpOptions = NDIS_OFFLOAD_NOT_SUPPORTED; /* linux can't handle this */
    hw_offload.LsoV2.IPv4.Encapsulation = NDIS_ENCAPSULATION_IEEE_802_3;
    hw_offload.LsoV2.IPv4.MaxOffLoadSize = xi->current_gso_value;
    hw_offload.LsoV2.IPv4.MinSegmentCount = MIN_LARGE_SEND_SEGMENTS;
    /* hw_offload.LsoV2.IPv6 is not supported */
    df_offload.LsoV1.IPv4.Encapsulation = NDIS_ENCAPSULATION_IEEE_802_3;
    df_offload.LsoV1.IPv4.MaxOffLoadSize = xi->current_gso_value;
    df_offload.LsoV1.IPv4.MinSegmentCount = MIN_LARGE_SEND_SEGMENTS;
    df_offload.LsoV1.IPv4.TcpOptions = NDIS_OFFLOAD_NOT_SUPPORTED; /* linux can't handle this */
    df_offload.LsoV1.IPv4.IpOptions = NDIS_OFFLOAD_NOT_SUPPORTED; /* linux can't handle this */
    df_offload.LsoV2.IPv4.Encapsulation = NDIS_ENCAPSULATION_IEEE_802_3;
    df_offload.LsoV2.IPv4.MaxOffLoadSize = xi->current_gso_value;
    df_offload.LsoV2.IPv4.MinSegmentCount = MIN_LARGE_SEND_SEGMENTS;
    /* df_offload.LsoV2.IPv6 is not supported */
  }
  /* hw_offload.IPsecV1 is not supported */
  /* hw_offload.IPsecV2 is not supported */
  /* df_offload.IPsecV1 is not supported */
  /* df_offload.IPsecV2 is not supported */
  hw_offload.Flags = 0;
  df_offload.Flags = 0;
  
  RtlZeroMemory(&df_conn_offload, sizeof(df_conn_offload));
  df_conn_offload.Header.Type = NDIS_OBJECT_TYPE_DEFAULT;
  df_conn_offload.Header.Revision = NDIS_TCP_CONNECTION_OFFLOAD_REVISION_1;
  df_conn_offload.Header.Size = NDIS_SIZEOF_TCP_CONNECTION_OFFLOAD_REVISION_1;

  RtlZeroMemory(&hw_conn_offload, sizeof(hw_conn_offload));
  hw_conn_offload.Header.Type = NDIS_OBJECT_TYPE_DEFAULT;
  hw_conn_offload.Header.Revision = NDIS_TCP_CONNECTION_OFFLOAD_REVISION_1;
  hw_conn_offload.Header.Size = NDIS_SIZEOF_TCP_CONNECTION_OFFLOAD_REVISION_1;
  
  offload_attributes.Header.Type = NDIS_OBJECT_TYPE_MINIPORT_ADAPTER_OFFLOAD_ATTRIBUTES;
  offload_attributes.Header.Revision = NDIS_MINIPORT_ADAPTER_OFFLOAD_ATTRIBUTES_REVISION_1;
  offload_attributes.Header.Size = NDIS_SIZEOF_MINIPORT_ADAPTER_OFFLOAD_ATTRIBUTES_REVISION_1;
  offload_attributes.DefaultOffloadConfiguration = &df_offload;
  offload_attributes.HardwareOffloadCapabilities = &hw_offload;
  offload_attributes.DefaultTcpConnectionOffloadConfiguration = &df_conn_offload;
  offload_attributes.TcpConnectionOffloadHardwareCapabilities  = &hw_conn_offload;
  status = NdisMSetMiniportAttributes(xi->adapter_handle, (PNDIS_MINIPORT_ADAPTER_ATTRIBUTES)&offload_attributes);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("NdisMSetMiniportAttributes(offload) failed (%08x)\n", status));
    goto err;
  }
  
  #if 0
  if (ndis_os_minor_version >= 1) {
    NDIS_MINIPORT_ADAPTER_HARDWARE_ASSIST_ATTRIBUTES hw_assist_attributes;
    NDIS_HD_SPLIT_ATTRIBUTES hd_split_attributes;
    
    RtlZeroMemory(&hd_split_attributes, sizeof(hd_split_attributes));
    hd_split_attributes.Header.Type = NDIS_OBJECT_TYPE_HD_SPLIT_ATTRIBUTES;
    hd_split_attributes.Header.Revision = NDIS_HD_SPLIT_ATTRIBUTES_REVISION_1;
    hd_split_attributes.Header.Size = NDIS_SIZEOF_HD_SPLIT_ATTRIBUTES_REVISION_1;
    hd_split_attributes.HardwareCapabilities = NDIS_HD_SPLIT_CAPS_SUPPORTS_HEADER_DATA_SPLIT | NDIS_HD_SPLIT_CAPS_SUPPORTS_IPV4_OPTIONS | NDIS_HD_SPLIT_CAPS_SUPPORTS_TCP_OPTIONS;
    hd_split_attributes.CurrentCapabilities = hd_split_attributes.HardwareCapabilities;
    /* the other members are set on output */
    
    RtlZeroMemory(&hw_assist_attributes, sizeof(hw_assist_attributes));
    hw_assist_attributes.Header.Type = NDIS_OBJECT_TYPE_MINIPORT_ADAPTER_HARDWARE_ASSIST_ATTRIBUTES;
    hw_assist_attributes.Header.Revision = NDIS_MINIPORT_ADAPTER_HARDWARE_ASSIST_ATTRIBUTES_REVISION_1;
    hw_assist_attributes.Header.Size = NDIS_SIZEOF_MINIPORT_ADAPTER_HARDWARE_ASSIST_ATTRIBUTES_REVISION_1;
    hw_assist_attributes.HDSplitAttributes = &hd_split_attributes;
    status = NdisMSetMiniportAttributes(xi->adapter_handle, (PNDIS_MINIPORT_ADAPTER_ATTRIBUTES)&hw_assist_attributes);
    if (!NT_SUCCESS(status))
    {
      FUNCTION_MSG("NdisMSetMiniportAttributes(hw_assist) failed (%08x)\n", status);
      goto err;
    }
    FUNCTION_MSG("HW Split enabled\n");
    FUNCTION_MSG(" HDSplitFlags = %08x\n", hd_split_attributes.HDSplitFlags);
    FUNCTION_MSG(" BackfillSize = %d\n", hd_split_attributes.BackfillSize);
    FUNCTION_MSG(" MaxHeaderSize = %d\n", hd_split_attributes.MaxHeaderSize);
    //what about backfill here?
  }
  #endif
  return NDIS_STATUS_SUCCESS;
  
err:
  NdisFreeMemory(xi, 0, 0);
  FUNCTION_EXIT_STATUS(status);

  return status;
}

NDIS_STATUS
XenNet_D0Exit(struct xennet_info *xi)
{
  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));

  xi->shutting_down = TRUE;
  KeMemoryBarrier(); /* make sure everyone sees that we are now shutting down */

  XenNet_TxShutdown(xi);
  XenNet_RxShutdown(xi);

  xi->connected = FALSE;
  KeMemoryBarrier(); /* make sure everyone sees that we are now disconnected */

  xi->vectors.XenPci_XenShutdownDevice(xi->vectors.context);

  FUNCTION_EXIT();
  
  return STATUS_SUCCESS;
}

static VOID
XenNet_DevicePnPEventNotify(NDIS_HANDLE adapter_context, PNET_DEVICE_PNP_EVENT pnp_event)
{
  UNREFERENCED_PARAMETER(adapter_context);

  FUNCTION_ENTER();
  switch (pnp_event->DevicePnPEvent)
  {
  case NdisDevicePnPEventSurpriseRemoved:
    KdPrint((__DRIVER_NAME "     NdisDevicePnPEventSurpriseRemoved\n"));
    break;
  case NdisDevicePnPEventPowerProfileChanged :
    KdPrint((__DRIVER_NAME "     NdisDevicePnPEventPowerProfileChanged\n"));
    break;
  default:
    KdPrint((__DRIVER_NAME "     NdisDevicePnPEvent%d\n", pnp_event->DevicePnPEvent));
    break;
  }
  FUNCTION_EXIT();
}

/* called at <= HIGH_IRQL, or PASSIVE_LEVEL, depending on shutdown_action */
VOID
XenNet_Shutdown(NDIS_HANDLE adapter_context, NDIS_SHUTDOWN_ACTION shutdown_action)
{
  UNREFERENCED_PARAMETER(adapter_context);
  UNREFERENCED_PARAMETER(shutdown_action);

  FUNCTION_ENTER();
  FUNCTION_EXIT();
}

static BOOLEAN
XenNet_CheckForHang(NDIS_HANDLE adapter_context)
{
  UNREFERENCED_PARAMETER(adapter_context);

  //FUNCTION_ENTER();
  //FUNCTION_EXIT();
  return FALSE;
}

/* Opposite of XenNet_Init */
static VOID
XenNet_Halt(NDIS_HANDLE adapter_context, NDIS_HALT_ACTION halt_action)
{
  struct xennet_info *xi = adapter_context;
  UNREFERENCED_PARAMETER(halt_action);

  FUNCTION_ENTER();
  
  XenNet_D0Exit(xi);

  NdisFreeMemory(xi, 0, 0);

  FUNCTION_EXIT();
}

static NDIS_STATUS 
XenNet_Reset(NDIS_HANDLE adapter_context, PBOOLEAN addressing_reset)
{
  UNREFERENCED_PARAMETER(adapter_context);

  FUNCTION_ENTER();
  *addressing_reset = FALSE;
  FUNCTION_EXIT();
  return NDIS_STATUS_SUCCESS;
}

/* called at PASSIVE_LEVEL */
static NDIS_STATUS
XenNet_Pause(NDIS_HANDLE adapter_context, PNDIS_MINIPORT_PAUSE_PARAMETERS pause_parameters)
{
  UNREFERENCED_PARAMETER(adapter_context);
  UNREFERENCED_PARAMETER(pause_parameters);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

/* called at PASSIVE_LEVEL */
static NDIS_STATUS
XenNet_Restart(NDIS_HANDLE adapter_context, PNDIS_MINIPORT_RESTART_PARAMETERS restart_parameters)
{
  UNREFERENCED_PARAMETER(adapter_context);
  UNREFERENCED_PARAMETER(restart_parameters);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static VOID
XenNet_Unload(PDRIVER_OBJECT driver_object)
{
  UNREFERENCED_PARAMETER(driver_object);
  FUNCTION_ENTER();
  NdisMDeregisterMiniportDriver(driver_handle);
  FUNCTION_EXIT();
}

static NDIS_STATUS
XenNet_SetOptions(NDIS_HANDLE driver_handle, NDIS_HANDLE driver_context)
{
  UNREFERENCED_PARAMETER(driver_handle);
  UNREFERENCED_PARAMETER(driver_context);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

NTSTATUS
DriverEntry(PDRIVER_OBJECT driver_object, PUNICODE_STRING registry_path)
{
  NTSTATUS status;  
  NDIS_MINIPORT_DRIVER_CHARACTERISTICS mini_chars;
  ULONG ndis_version;
  
  FUNCTION_ENTER();

  ndis_version = NdisGetVersion();
  
  ndis_os_major_version = ndis_version >> 16;
  ndis_os_minor_version = ndis_version & 0xFFFF;

  NdisZeroMemory(&mini_chars, sizeof(mini_chars));

  mini_chars.Header.Type = NDIS_OBJECT_TYPE_MINIPORT_DRIVER_CHARACTERISTICS;
  
  if (ndis_os_minor_version < 1) {
    mini_chars.Header.Revision = NDIS_MINIPORT_DRIVER_CHARACTERISTICS_REVISION_1;
    mini_chars.Header.Size = NDIS_SIZEOF_MINIPORT_DRIVER_CHARACTERISTICS_REVISION_1;

    mini_chars.MajorNdisVersion = 6;
    mini_chars.MinorNdisVersion = 0;
  } else {
    mini_chars.Header.Revision = NDIS_MINIPORT_DRIVER_CHARACTERISTICS_REVISION_2;
    mini_chars.Header.Size = NDIS_SIZEOF_MINIPORT_DRIVER_CHARACTERISTICS_REVISION_2;
    mini_chars.MajorNdisVersion = 6;
    mini_chars.MinorNdisVersion = 1;
  }
  mini_chars.MajorDriverVersion = VENDOR_DRIVER_VERSION_MAJOR;
  mini_chars.MinorDriverVersion = VENDOR_DRIVER_VERSION_MINOR;

  KdPrint((__DRIVER_NAME "     Driver MajorNdisVersion = %d, Driver MinorNdisVersion = %d\n", NDIS_MINIPORT_MAJOR_VERSION, NDIS_MINIPORT_MINOR_VERSION));
  KdPrint((__DRIVER_NAME "     Windows MajorNdisVersion = %d, Windows MinorNdisVersion = %d\n", ndis_os_major_version, ndis_os_minor_version));

  mini_chars.Flags = NDIS_WDM_DRIVER;
  
  mini_chars.SetOptionsHandler = XenNet_SetOptions;
  mini_chars.InitializeHandlerEx = XenNet_Initialize;
  mini_chars.HaltHandlerEx = XenNet_Halt;
  mini_chars.UnloadHandler = XenNet_Unload;
  mini_chars.PauseHandler = XenNet_Pause;
  mini_chars.RestartHandler = XenNet_Restart;
  mini_chars.CheckForHangHandlerEx = XenNet_CheckForHang;
  mini_chars.ResetHandlerEx = XenNet_Reset;
  mini_chars.DevicePnPEventNotifyHandler = XenNet_DevicePnPEventNotify;
  mini_chars.ShutdownHandlerEx = XenNet_Shutdown;

  mini_chars.OidRequestHandler = XenNet_OidRequest;
  mini_chars.CancelOidRequestHandler = XenNet_CancelOidRequest;
  if (ndis_os_minor_version >= 1) {
    mini_chars.DirectOidRequestHandler = NULL;
    mini_chars.CancelDirectOidRequestHandler = NULL;
  }

  mini_chars.SendNetBufferListsHandler = XenNet_SendNetBufferLists;
  mini_chars.CancelSendHandler = XenNet_CancelSend;

  mini_chars.ReturnNetBufferListsHandler = XenNet_ReturnNetBufferLists;

  status = NdisMRegisterMiniportDriver(driver_object, registry_path, NULL, &mini_chars, &driver_handle);
  if (!NT_SUCCESS(status))
  {
    KdPrint((__DRIVER_NAME "     NdisMRegisterMiniportDriver failed, status = 0x%x\n", status));
    return status;
  }

  FUNCTION_EXIT();

  return status;
}
