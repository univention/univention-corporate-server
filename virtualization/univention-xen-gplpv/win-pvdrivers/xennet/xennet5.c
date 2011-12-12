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
#include "xennet5.h"

/* Not really necessary but keeps PREfast happy */
DRIVER_INITIALIZE DriverEntry;
static IO_WORKITEM_ROUTINE XenNet_ResumeWorkItem;
#if (VER_PRODUCTBUILD >= 7600)
static KDEFERRED_ROUTINE XenNet_SuspendResume;
#endif

#pragma NDIS_INIT_FUNCTION(DriverEntry)

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
  ULONG backend_sg = 0;
  ULONG backend_gso = 0;

  FUNCTION_ENTER();
  
  ASSERT(KeGetCurrentIrql() < DISPATCH_LEVEL);

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
          backend_sg = 1;
        }
      }
      else if (strcmp(setting, "feature-gso-tcpv4") == 0)
      {
        if (atoi(value))
        {
          backend_gso = 1;
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
  if (xi->config_sg && !backend_sg)
  {
    KdPrint((__DRIVER_NAME "     SG not supported by backend - disabling\n"));
    xi->config_sg = 0;
  }
  if (xi->config_gso && !backend_gso)
  {
    KdPrint((__DRIVER_NAME "     GSO not supported by backend - disabling\n"));
    xi->config_gso = 0;
  }
  FUNCTION_EXIT();
  
  return NDIS_STATUS_SUCCESS;
}

static VOID
XenNet_ResumeWorkItem(PDEVICE_OBJECT device_object, PVOID context)
{
  struct xennet_info *xi = context;
  KIRQL old_irql;
  
  UNREFERENCED_PARAMETER(device_object);
  
  FUNCTION_ENTER();

  ASSERT(xi->resume_work_item);

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

  /* if Rx goes over its per-dpc quota then make sure TxBufferGC doesn't set an event as we are already guaranteed to be called again */
  dont_set_event = XenNet_RxBufferCheck(xi);
  XenNet_TxBufferGC(xi, dont_set_event);
} 

static BOOLEAN
XenNet_HandleEvent(PVOID context)
{
  struct xennet_info *xi = context;
  ULONG suspend_resume_state_pdo;
  
  //FUNCTION_ENTER();
  suspend_resume_state_pdo = xi->device_state->suspend_resume_state_pdo;
  KeMemoryBarrier();
//  KdPrint((__DRIVER_NAME "     connected = %d, inactive = %d, suspend_resume_state_pdo = %d\n",
//    xi->connected, xi->inactive, suspend_resume_state_pdo));
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
  RtlStringCbPrintfA(buf, ARRAY_SIZE(buf), "%d", !xi->config_csum);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_WRITE_STRING, "feature-no-csum-offload", buf, NULL);
  RtlStringCbPrintfA(buf, ARRAY_SIZE(buf), "%d", (int)xi->config_sg);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_WRITE_STRING, "feature-sg", buf, NULL);
  RtlStringCbPrintfA(buf, ARRAY_SIZE(buf), "%d", !!xi->config_gso);
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

  if (!xi->config_sg)
  {
    /* without SG, GSO can be a maximum of PAGE_SIZE */
    xi->config_gso = min(xi->config_gso, PAGE_SIZE);
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
XenNet_Init(
  OUT PNDIS_STATUS OpenErrorStatus,
  OUT PUINT SelectedMediumIndex,
  IN PNDIS_MEDIUM MediumArray,
  IN UINT MediumArraySize,
  IN NDIS_HANDLE MiniportAdapterHandle,
  IN NDIS_HANDLE WrapperConfigurationContext
  )
{
  NDIS_STATUS status;
  BOOLEAN medium_found = FALSE;
  struct xennet_info *xi = NULL;
  UINT nrl_length;
  PNDIS_RESOURCE_LIST nrl;
  PCM_PARTIAL_RESOURCE_DESCRIPTOR prd;
  KIRQL irq_level = 0;
  ULONG irq_vector = 0;
  ULONG irq_mode = 0;
  NDIS_HANDLE config_handle;
  NDIS_STRING config_param_name;
  PNDIS_CONFIGURATION_PARAMETER config_param;
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
  
  UNREFERENCED_PARAMETER(OpenErrorStatus);

  FUNCTION_ENTER();

  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));

  /* deal with medium stuff */
  for (i = 0; i < MediumArraySize; i++)
  {
    if (MediumArray[i] == NdisMedium802_3)
    {
      medium_found = TRUE;
      break;
    }
  }
  if (!medium_found)
  {
    KdPrint(("NIC_MEDIA_TYPE not in MediumArray\n"));
    return NDIS_STATUS_UNSUPPORTED_MEDIA;
  }
  *SelectedMediumIndex = i;

  /* Alloc memory for adapter private info */
  status = NdisAllocateMemoryWithTag((PVOID)&xi, sizeof(*xi), XENNET_POOL_TAG);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("NdisAllocateMemoryWithTag failed with 0x%x\n", status));
    status = NDIS_STATUS_RESOURCES;
    goto err;
  }
  RtlZeroMemory(xi, sizeof(*xi));
  xi->adapter_handle = MiniportAdapterHandle;
  xi->rx_target     = RX_DFL_MIN_TARGET;
  xi->rx_min_target = RX_DFL_MIN_TARGET;
  xi->rx_max_target = RX_MAX_TARGET;
  xi->inactive      = TRUE;
  NdisMSetAttributesEx(xi->adapter_handle, (NDIS_HANDLE) xi, 0, 0 /* the last zero is to give the next | something to | with */
#ifdef NDIS51_MINIPORT
    |NDIS_ATTRIBUTE_USES_SAFE_BUFFER_APIS
#endif
    |NDIS_ATTRIBUTE_DESERIALIZE
    |NDIS_ATTRIBUTE_SURPRISE_REMOVE_OK,
    NdisInterfaceInternal); /* PnpBus option doesn't exist... */
  xi->multicast_list_size = 0;
  xi->current_lookahead = MIN_LOOKAHEAD_LENGTH;

  nrl_length = 0;
  NdisMQueryAdapterResources(&status, WrapperConfigurationContext,
    NULL, (PUINT)&nrl_length);
  KdPrint((__DRIVER_NAME "     nrl_length = %d\n", nrl_length));
  status = NdisAllocateMemoryWithTag((PVOID)&nrl, nrl_length, XENNET_POOL_TAG);
  if (status != NDIS_STATUS_SUCCESS)
  {
    KdPrint((__DRIVER_NAME "     Could not get allocate memory for Adapter Resources 0x%x\n", status));
    return NDIS_STATUS_RESOURCES;
  }
  NdisMQueryAdapterResources(&status, WrapperConfigurationContext,
    nrl, (PUINT)&nrl_length);
  if (status != NDIS_STATUS_SUCCESS)
  {
    KdPrint((__DRIVER_NAME "     Could not get Adapter Resources 0x%x\n", status));
    return NDIS_STATUS_RESOURCES;
  }
  xi->event_channel = 0;
  xi->config_csum = 1;
  xi->config_csum_rx_check = 1;
  xi->config_sg = 1;
  xi->config_gso = 61440;
  xi->config_page = NULL;
  xi->config_rx_interrupt_moderation = 0;
  
  for (i = 0; i < nrl->Count; i++)
  {
    prd = &nrl->PartialDescriptors[i];

    switch(prd->Type)
    {
    case CmResourceTypeInterrupt:
      irq_vector = prd->u.Interrupt.Vector;
      irq_level = (KIRQL)prd->u.Interrupt.Level;
      irq_mode = (prd->Flags & CM_RESOURCE_INTERRUPT_LATCHED)?NdisInterruptLatched:NdisInterruptLevelSensitive;
      KdPrint((__DRIVER_NAME "     irq_vector = %03x, irq_level = %03x, irq_mode = %s\n", irq_vector, irq_level,
        (irq_mode == NdisInterruptLatched)?"NdisInterruptLatched":"NdisInterruptLevelSensitive"));
      break;
    case CmResourceTypeMemory:
      if (xi->config_page)
      {
        KdPrint(("More than one memory range\n"));
        return NDIS_STATUS_RESOURCES;
      }
      else
      {
        status = NdisMMapIoSpace(&xi->config_page, MiniportAdapterHandle, prd->u.Memory.Start, prd->u.Memory.Length);
        if (!NT_SUCCESS(status))
        {
          KdPrint(("NdisMMapIoSpace failed with 0x%x\n", status));
          NdisFreeMemory(nrl, nrl_length, 0);
          return NDIS_STATUS_RESOURCES;
        }
      }
      break;
    }
  }
  NdisFreeMemory(nrl, nrl_length, 0);
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

  NdisMGetDeviceProperty(MiniportAdapterHandle, &xi->pdo, &xi->fdo,
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
  
  NdisOpenConfiguration(&status, &config_handle, WrapperConfigurationContext);
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
    xi->config_sg = 1;
  }
  else
  {
    KdPrint(("ScatterGather = %d\n", config_param->ParameterData.IntegerData));
    xi->config_sg = config_param->ParameterData.IntegerData;
  }
  
  NdisInitUnicodeString(&config_param_name, L"LargeSendOffload");
  NdisReadConfiguration(&status, &config_param, config_handle, &config_param_name, NdisParameterInteger);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not read LargeSendOffload value (%08x)\n", status));
    xi->config_gso = 0;
  }
  else
  {
    KdPrint(("LargeSendOffload = %d\n", config_param->ParameterData.IntegerData));
    xi->config_gso = config_param->ParameterData.IntegerData;
    if (xi->config_gso > 61440)
    {
      xi->config_gso = 61440;
      KdPrint(("(clipped to %d)\n", xi->config_gso));
    }
  }

  NdisInitUnicodeString(&config_param_name, L"ChecksumOffload");
  NdisReadConfiguration(&status, &config_param, config_handle, &config_param_name, NdisParameterInteger);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not read ChecksumOffload value (%08x)\n", status));
    xi->config_csum = 1;
  }
  else
  {
    KdPrint(("ChecksumOffload = %d\n", config_param->ParameterData.IntegerData));
    xi->config_csum = !!config_param->ParameterData.IntegerData;
  }

  NdisInitUnicodeString(&config_param_name, L"ChecksumOffloadRxCheck");
  NdisReadConfiguration(&status, &config_param, config_handle, &config_param_name, NdisParameterInteger);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not read ChecksumOffloadRxCheck value (%08x)\n", status));
    xi->config_csum_rx_check = 1;
  }
  else
  {
    KdPrint(("ChecksumOffloadRxCheck = %d\n", config_param->ParameterData.IntegerData));
    xi->config_csum_rx_check = !!config_param->ParameterData.IntegerData;
  }

  NdisInitUnicodeString(&config_param_name, L"ChecksumOffloadDontFix");
  NdisReadConfiguration(&status, &config_param, config_handle, &config_param_name, NdisParameterInteger);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not read ChecksumOffloadDontFix value (%08x)\n", status));
    xi->config_csum_rx_dont_fix = 0;
  }
  else
  {
    KdPrint(("ChecksumOffloadDontFix = %d\n", config_param->ParameterData.IntegerData));
    xi->config_csum_rx_dont_fix = !!config_param->ParameterData.IntegerData;
  }
  
  
  
  NdisInitUnicodeString(&config_param_name, L"MTU");
  NdisReadConfiguration(&status, &config_param, config_handle, &config_param_name, NdisParameterInteger);  
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not read MTU value (%08x)\n", status));
    xi->config_mtu = 1500;
  }
  else
  {
    KdPrint(("MTU = %d\n", config_param->ParameterData.IntegerData));
    xi->config_mtu = config_param->ParameterData.IntegerData;
  }

  NdisInitUnicodeString(&config_param_name, L"RxInterruptModeration");
  NdisReadConfiguration(&status, &config_param, config_handle, &config_param_name, NdisParameterInteger);  
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Could not read RxInterruptModeration value (%08x)\n", status));
    xi->config_rx_interrupt_moderation = 1500;
  }
  else
  {
    KdPrint(("RxInterruptModeration = %d\n", config_param->ParameterData.IntegerData));
    xi->config_rx_interrupt_moderation = config_param->ParameterData.IntegerData;
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

  xi->config_max_pkt_size = max(xi->config_mtu + XN_HDR_SIZE, xi->config_gso + XN_HDR_SIZE);
  
  NdisCloseConfiguration(config_handle);

  status = XenNet_D0Entry(xi);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Failed to go to D0 (%08x)\n", status));
    goto err;
  }
  return NDIS_STATUS_SUCCESS;
  
err:
  NdisFreeMemory(xi, 0, 0);
  *OpenErrorStatus = status;
  FUNCTION_EXIT_STATUS(status);
  return status;
}

VOID
XenNet_PnPEventNotify(
  IN NDIS_HANDLE MiniportAdapterContext,
  IN NDIS_DEVICE_PNP_EVENT PnPEvent,
  IN PVOID InformationBuffer,
  IN ULONG InformationBufferLength
  )
{
  UNREFERENCED_PARAMETER(MiniportAdapterContext);
  UNREFERENCED_PARAMETER(PnPEvent);
  UNREFERENCED_PARAMETER(InformationBuffer);
  UNREFERENCED_PARAMETER(InformationBufferLength);

  FUNCTION_ENTER();
  switch (PnPEvent)
  {
  case NdisDevicePnPEventSurpriseRemoved:
    KdPrint((__DRIVER_NAME "     NdisDevicePnPEventSurpriseRemoved\n"));
    break;
  case NdisDevicePnPEventPowerProfileChanged :
    KdPrint((__DRIVER_NAME "     NdisDevicePnPEventPowerProfileChanged\n"));
    break;
  default:
    KdPrint((__DRIVER_NAME "     %d\n", PnPEvent));
    break;
  }
  FUNCTION_EXIT();
}

/* Called when machine is shutting down, so just quiesce the HW and be done fast. */
VOID
XenNet_Shutdown(
  IN NDIS_HANDLE MiniportAdapterContext
  )
{
  UNREFERENCED_PARAMETER(MiniportAdapterContext);

  /* remember we are called at >= DIRQL here */
  FUNCTION_ENTER();
  FUNCTION_EXIT();
}

/* Opposite of XenNet_Init */
VOID
XenNet_Halt(
  IN NDIS_HANDLE MiniportAdapterContext
  )
{
  struct xennet_info *xi = MiniportAdapterContext;

  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));
  
  XenNet_D0Exit(xi);

  NdisFreeMemory(xi, 0, 0);

  FUNCTION_EXIT();
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

NDIS_STATUS 
XenNet_Reset(
  PBOOLEAN  AddressingReset,
  NDIS_HANDLE  MiniportAdapterContext
)
{
  UNREFERENCED_PARAMETER(MiniportAdapterContext);

  *AddressingReset = FALSE;
  return NDIS_STATUS_SUCCESS;
}

NTSTATUS
DriverEntry(
  PDRIVER_OBJECT DriverObject,
  PUNICODE_STRING RegistryPath
  )
{
  NTSTATUS status;  
  NDIS_HANDLE ndis_wrapper_handle = NULL;
  NDIS_MINIPORT_CHARACTERISTICS mini_chars;

  FUNCTION_ENTER();

  KdPrint((__DRIVER_NAME "     DriverObject = %p, RegistryPath = %p\n", DriverObject, RegistryPath));
  
  NdisZeroMemory(&mini_chars, sizeof(mini_chars));

  KdPrint((__DRIVER_NAME "     NdisGetVersion = %x\n", NdisGetVersion()));

  KdPrint((__DRIVER_NAME "     ndis_wrapper_handle = %p\n", ndis_wrapper_handle));
  NdisMInitializeWrapper(&ndis_wrapper_handle, DriverObject, RegistryPath, NULL);
  KdPrint((__DRIVER_NAME "     ndis_wrapper_handle = %p\n", ndis_wrapper_handle));
  if (!ndis_wrapper_handle)
  {
    KdPrint((__DRIVER_NAME "     NdisMInitializeWrapper failed\n"));
    return NDIS_STATUS_FAILURE;
  }
  KdPrint((__DRIVER_NAME "     NdisMInitializeWrapper succeeded\n"));

  /* NDIS 5.1 driver */
  mini_chars.MajorNdisVersion = NDIS_MINIPORT_MAJOR_VERSION;
  mini_chars.MinorNdisVersion = NDIS_MINIPORT_MINOR_VERSION;

  KdPrint((__DRIVER_NAME "     MajorNdisVersion = %d,  MinorNdisVersion = %d\n", NDIS_MINIPORT_MAJOR_VERSION, NDIS_MINIPORT_MINOR_VERSION));

  mini_chars.HaltHandler = XenNet_Halt;
  mini_chars.InitializeHandler = XenNet_Init;
  //mini_chars.ISRHandler = XenNet_InterruptIsr;
  //mini_chars.HandleInterruptHandler = XenNet_InterruptDpc;
  mini_chars.QueryInformationHandler = XenNet_QueryInformation;
  mini_chars.ResetHandler = XenNet_Reset;
  mini_chars.SetInformationHandler = XenNet_SetInformation;
  /* added in v.4 -- use multiple pkts interface */
  mini_chars.ReturnPacketHandler = XenNet_ReturnPacket;
  mini_chars.SendPacketsHandler = XenNet_SendPackets;
  /* don't support cancel - no point as packets are never queued for long */
  //mini_chars.CancelSendPacketsHandler = XenNet_CancelSendPackets;

#ifdef NDIS51_MINIPORT
  /* added in v.5.1 */
  mini_chars.PnPEventNotifyHandler = XenNet_PnPEventNotify;
  mini_chars.AdapterShutdownHandler = XenNet_Shutdown;
#else
  // something else here
#endif

  /* set up upper-edge interface */
  KdPrint((__DRIVER_NAME "     about to call NdisMRegisterMiniport\n"));
  status = NdisMRegisterMiniport(ndis_wrapper_handle, &mini_chars, sizeof(mini_chars));
  KdPrint((__DRIVER_NAME "     called NdisMRegisterMiniport\n"));
  if (!NT_SUCCESS(status))
  {
    KdPrint((__DRIVER_NAME "     NdisMRegisterMiniport failed, status = 0x%x\n", status));
    NdisTerminateWrapper(ndis_wrapper_handle, NULL);
    return status;
  }

  FUNCTION_EXIT();

  return status;
}