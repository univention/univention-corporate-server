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

#include "xennet.h"

/* Increase the header to a certain size */
BOOLEAN
XenNet_BuildHeader(packet_info_t *pi, PUCHAR header, ULONG new_header_size)
{
  ULONG bytes_remaining;

  //FUNCTION_ENTER();

  if (!header)
    header = pi->header;

  if (new_header_size > pi->total_length) {
    new_header_size = pi->total_length;
  }

  if (new_header_size <= pi->header_length) {
    //FUNCTION_EXIT();
    return TRUE; /* header is already at least the required size */
  }

  if (header == pi->first_mdl_virtual) {
    XN_ASSERT(new_header_size <= PAGE_SIZE);
    /* still working in the first buffer */
    if (new_header_size <= pi->first_mdl_length) {
      /* Trivially expand header_length */
      pi->header_length = new_header_size;
      if (pi->header_length == pi->first_mdl_length) {
        #if NTDDI_VERSION < NTDDI_VISTA
        NdisGetNextBuffer(pi->curr_mdl, &pi->curr_mdl);
        #else
        NdisGetNextMdl(pi->curr_mdl, &pi->curr_mdl);
        #endif
        pi->curr_mdl_offset = 0;
        if (pi->curr_pb)
          pi->curr_pb = pi->curr_pb->next;
      } else {
        pi->curr_mdl_offset = (USHORT)new_header_size;
      }
    }
  }
  
  bytes_remaining = new_header_size - pi->header_length;

  while (bytes_remaining && pi->curr_mdl) {
    ULONG copy_size;
    
    XN_ASSERT(pi->curr_mdl);
    if (MmGetMdlByteCount(pi->curr_mdl)) {
      PUCHAR src_addr;
      src_addr = MmGetSystemAddressForMdlSafe(pi->curr_mdl, NormalPagePriority);
      if (!src_addr) {
        //FUNCTION_EXIT();
        return FALSE;
      }
      copy_size = min(bytes_remaining, MmGetMdlByteCount(pi->curr_mdl) - pi->curr_mdl_offset);
      memcpy(header + pi->header_length,
        src_addr + pi->curr_mdl_offset, copy_size);
      pi->curr_mdl_offset = (USHORT)(pi->curr_mdl_offset + copy_size);
      pi->header_length += copy_size;
      bytes_remaining -= copy_size;
    }
    if (pi->curr_mdl_offset == MmGetMdlByteCount(pi->curr_mdl)) {
      #if NTDDI_VERSION < NTDDI_VISTA
      NdisGetNextBuffer(pi->curr_mdl, &pi->curr_mdl);
      #else
      NdisGetNextMdl(pi->curr_mdl, &pi->curr_mdl);
      #endif
      if (pi->curr_pb)
        pi->curr_pb = pi->curr_pb->next;
      pi->curr_mdl_offset = 0;
    }
  }
  //KdPrint((__DRIVER_NAME "     C bytes_remaining = %d, pi->curr_mdl = %p\n", bytes_remaining, pi->curr_mdl));
  if (bytes_remaining) {
    //KdPrint((__DRIVER_NAME "     bytes_remaining\n"));
    //FUNCTION_EXIT();
    return FALSE;
  }
  //FUNCTION_EXIT();
  return TRUE;
}

VOID
XenNet_ParsePacketHeader(packet_info_t *pi, PUCHAR alt_buffer, ULONG min_header_size)
{
  //FUNCTION_ENTER();

  XN_ASSERT(pi->first_mdl);
  
  #if NTDDI_VERSION < NTDDI_VISTA
  NdisQueryBufferSafe(pi->first_mdl, (PVOID)&pi->first_mdl_virtual, &pi->first_mdl_length, NormalPagePriority);
  #else
  NdisQueryMdl(pi->first_mdl, (PVOID)&pi->first_mdl_virtual, &pi->first_mdl_length, NormalPagePriority);
  #endif
  pi->curr_mdl = pi->first_mdl;
  if (alt_buffer)
    pi->header = alt_buffer;
  else
    pi->header = pi->first_mdl_virtual;

  pi->header_length = 0;
  pi->curr_mdl_offset = pi->first_mdl_offset;
  
  pi->ip_proto = 0;
  pi->ip_version = 0;
  pi->ip4_header_length = 0;
  pi->ip4_length = 0;
  pi->tcp_header_length = 0;
  pi->tcp_length = 0;
  pi->split_required = 0;

  XenNet_BuildHeader(pi, NULL, min_header_size);
  
  if (!XenNet_BuildHeader(pi, NULL, (ULONG)XN_HDR_SIZE)) {
    //KdPrint((__DRIVER_NAME "     packet too small (Ethernet Header)\n"));
    pi->parse_result = PARSE_TOO_SMALL;
    return;
  }

  if (pi->header[0] == 0xFF && pi->header[1] == 0xFF
      && pi->header[2] == 0xFF && pi->header[3] == 0xFF
      && pi->header[4] == 0xFF && pi->header[5] == 0xFF) {
    pi->is_broadcast = TRUE;
  } else if (pi->header[0] & 0x01) {
    pi->is_multicast = TRUE;
  }

  switch (GET_NET_PUSHORT(&pi->header[12])) { // L2 protocol field
  case 0x0800: /* IPv4 */
    //KdPrint((__DRIVER_NAME "     IP\n"));
    if (pi->header_length < (ULONG)(XN_HDR_SIZE + 20)) {
      if (!XenNet_BuildHeader(pi, NULL, (ULONG)(XN_HDR_SIZE + 20))) {
        FUNCTION_MSG("packet too small (IP Header)\n");
        pi->parse_result = PARSE_TOO_SMALL;
        return;
      }
    }
    pi->ip_version = (pi->header[XN_HDR_SIZE + 0] & 0xF0) >> 4;
    if (pi->ip_version != 4) {
      //KdPrint((__DRIVER_NAME "     ip_version = %d\n", pi->ip_version));
      pi->parse_result = PARSE_UNKNOWN_TYPE;
      return;
    }
    pi->ip4_header_length = (pi->header[XN_HDR_SIZE + 0] & 0x0F) << 2;
    if (pi->header_length < (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + 20)) {
      if (!XenNet_BuildHeader(pi, NULL, (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + 20))) {
        //KdPrint((__DRIVER_NAME "     packet too small (IP Header + IP Options + TCP Header)\n"));
        pi->parse_result = PARSE_TOO_SMALL;
        return;
      }
    }
    break;
  case 0x86DD:  /* IPv6 */
    //KdPrint((__DRIVER_NAME "     IPv6\n"));
    //KdPrint((__DRIVER_NAME "     (not currently used)\n"));
    pi->parse_result = PARSE_UNKNOWN_TYPE;
    return;
  default:
    //KdPrint((__DRIVER_NAME "     Not IP (%04x)\n", GET_NET_PUSHORT(&pi->header[12])));
    pi->parse_result = PARSE_UNKNOWN_TYPE;
    return;
  }
  pi->ip_proto = pi->header[XN_HDR_SIZE + 9];
  pi->ip4_length = GET_NET_PUSHORT(&pi->header[XN_HDR_SIZE + 2]);
  pi->ip_has_options = (BOOLEAN)(pi->ip4_header_length > 20);
  switch (pi->ip_proto) {
  case 6:  // TCP
  case 17: // UDP
    break;
  default:
    //KdPrint((__DRIVER_NAME "     Not TCP/UDP (%d)\n", pi->ip_proto));
    pi->parse_result = PARSE_UNKNOWN_TYPE;
    return;
  }
  pi->tcp_header_length = (pi->header[XN_HDR_SIZE + pi->ip4_header_length + 12] & 0xf0) >> 2;

  if (pi->header_length < (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + pi->tcp_header_length)) {
    /* we don't actually need the tcp options to analyse the header */
    if (!XenNet_BuildHeader(pi, NULL, (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + MIN_TCP_HEADER_LENGTH))) {
      //KdPrint((__DRIVER_NAME "     packet too small (IP Header + IP Options + TCP Header (not including TCP Options))\n"));
      pi->parse_result = PARSE_TOO_SMALL;
      return;
    }
  }

  if ((ULONG)XN_HDR_SIZE + pi->ip4_length > pi->total_length) {
    //KdPrint((__DRIVER_NAME "     XN_HDR_SIZE + ip4_length (%d) > total_length (%d)\n", XN_HDR_SIZE + pi->ip4_length, pi->total_length));
    pi->parse_result = PARSE_UNKNOWN_TYPE;
    return;
  }

  pi->tcp_length = pi->ip4_length - pi->ip4_header_length - pi->tcp_header_length;
  pi->tcp_remaining = pi->tcp_length;
  pi->tcp_seq = GET_NET_PULONG(&pi->header[XN_HDR_SIZE + pi->ip4_header_length + 4]);
  pi->tcp_has_options = (BOOLEAN)(pi->tcp_header_length > 20);
  if (pi->mss > 0 && pi->tcp_length > pi->mss)
    pi->split_required = TRUE;

  //KdPrint((__DRIVER_NAME "     ip4_length = %d\n", pi->ip4_length));
  //KdPrint((__DRIVER_NAME "     tcp_length = %d\n", pi->tcp_length));
  //FUNCTION_EXIT();
  
  pi->parse_result = PARSE_OK;
}

BOOLEAN
XenNet_CheckIpHeaderSum(PUCHAR header, USHORT ip4_header_length) {
  ULONG csum = 0;
  USHORT i;

  XN_ASSERT(ip4_header_length > 12);
  XN_ASSERT(!(ip4_header_length & 1));

  for (i = 0; i < ip4_header_length; i += 2) {
    csum += GET_NET_PUSHORT(&header[XN_HDR_SIZE + i]);
  }
  while (csum & 0xFFFF0000)
    csum = (csum & 0xFFFF) + (csum >> 16);
  return (BOOLEAN)(csum == 0xFFFF);
}

VOID
XenNet_SumIpHeader(PUCHAR header, USHORT ip4_header_length) {
  ULONG csum = 0;
  USHORT i;

  XN_ASSERT(ip4_header_length > 12);
  XN_ASSERT(!(ip4_header_length & 1));

  header[XN_HDR_SIZE + 10] = 0;
  header[XN_HDR_SIZE + 11] = 0;
  for (i = 0; i < ip4_header_length; i += 2) {
    csum += GET_NET_PUSHORT(&header[XN_HDR_SIZE + i]);
  }
  while (csum & 0xFFFF0000)
    csum = (csum & 0xFFFF) + (csum >> 16);
  csum = ~csum;
  SET_NET_USHORT(&header[XN_HDR_SIZE + 10], (USHORT)csum);
}

BOOLEAN
XenNet_FilterAcceptPacket(struct xennet_info *xi,packet_info_t *pi)
{
  ULONG i;
  BOOLEAN is_my_multicast = FALSE;
  BOOLEAN is_directed = FALSE;

  if (memcmp(xi->curr_mac_addr, pi->header, ETH_ALEN) == 0)
  {
    is_directed = TRUE;
  }
  else if (pi->is_multicast)
  {
    for (i = 0; i < xi->multicast_list_size; i++)
    {
      if (memcmp(xi->multicast_list[i], pi->header, 6) == 0)
        break;
    }
    if (i < xi->multicast_list_size)
    {
      is_my_multicast = TRUE;
    }
  }
  if (is_directed && (xi->packet_filter & NDIS_PACKET_TYPE_DIRECTED))
  {
    return TRUE;
  }
  if (is_my_multicast && (xi->packet_filter & NDIS_PACKET_TYPE_MULTICAST))
  {
    return TRUE;
  }
  if (pi->is_multicast && (xi->packet_filter & NDIS_PACKET_TYPE_ALL_MULTICAST))
  {
    return TRUE;
  }
  if (pi->is_broadcast && (xi->packet_filter & NDIS_PACKET_TYPE_BROADCAST))
  {
    return TRUE;
  }
  if (xi->packet_filter & NDIS_PACKET_TYPE_PROMISCUOUS)
  {
    return TRUE;
  }
  //return TRUE;
  return FALSE;
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
XenNet_HandleEvent_DIRQL(PVOID context)
{
  struct xennet_info *xi = context;
  //ULONG suspend_resume_state_pdo;
  
  //FUNCTION_ENTER();
  if (xi->device_state == DEVICE_STATE_ACTIVE || xi->device_state == DEVICE_STATE_DISCONNECTING) {
    KeInsertQueueDpc(&xi->rxtx_dpc, NULL, NULL);
  }
  //FUNCTION_EXIT();
  return TRUE;
}

NTSTATUS
XenNet_Connect(PVOID context, BOOLEAN suspend) {
  NTSTATUS status;
  struct xennet_info *xi = context;
  PFN_NUMBER pfn;
  ULONG qemu_hide_filter;
  ULONG qemu_hide_flags_value;
  int i;
  ULONG state;
  ULONG octet;
  PCHAR tmp_string;
  ULONG tmp_ulong;
  LARGE_INTEGER timeout;

  if (!suspend) {
    xi->handle = XnOpenDevice(xi->pdo, XenNet_DeviceCallback, xi);
  }
  if (!xi->handle) {
    FUNCTION_MSG("Cannot open Xen device\n");
    return STATUS_UNSUCCESSFUL;
  }
  XnGetValue(xi->handle, XN_VALUE_TYPE_QEMU_HIDE_FLAGS, &qemu_hide_flags_value);
  XnGetValue(xi->handle, XN_VALUE_TYPE_QEMU_FILTER, &qemu_hide_filter);
  if (!(qemu_hide_flags_value & QEMU_UNPLUG_ALL_NICS) || qemu_hide_filter) {
    FUNCTION_MSG("inactive\n");
    xi->device_state = DEVICE_STATE_INACTIVE;
    /* continue with setup so all the flags and capabilities are correct */
  }
  /* explicitly set the frontend state as it will still be 'closed' if we are restarting the adapter */
  status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "state", XenbusStateInitialising);
  if (xi->device_state != DEVICE_STATE_INACTIVE) {
    for (i = 0; i <= 5 && xi->backend_state != XenbusStateInitialising && xi->backend_state != XenbusStateInitWait && xi->backend_state != XenbusStateInitialised; i++) {
      FUNCTION_MSG("Waiting for XenbusStateInitXxx\n");
      if (xi->backend_state == XenbusStateClosed) {
        status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "state", XenbusStateInitialising);
      }
      timeout.QuadPart = -10 * 1000 * 1000; /* 1 second */
      KeWaitForSingleObject(&xi->backend_event, Executive, KernelMode, FALSE, &timeout);
    }
    if (xi->backend_state != XenbusStateInitialising && xi->backend_state != XenbusStateInitWait && xi->backend_state != XenbusStateInitialised) {
      FUNCTION_MSG("Backend state timeout\n");
      return STATUS_UNSUCCESSFUL;
    }
    if (!NT_SUCCESS(status = XnBindEvent(xi->handle, &xi->event_channel, XenNet_HandleEvent_DIRQL, xi))) {
      FUNCTION_MSG("Cannot allocate event channel\n");
      return STATUS_UNSUCCESSFUL;
    }
    FUNCTION_MSG("event_channel = %d\n", xi->event_channel);
    status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "event-channel", xi->event_channel);
    xi->tx_sring = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENNET_POOL_TAG);
    if (!xi->tx_sring) {
      FUNCTION_MSG("Cannot allocate tx_sring\n");
      return STATUS_UNSUCCESSFUL;
    }
    SHARED_RING_INIT(xi->tx_sring);
    FRONT_RING_INIT(&xi->tx_ring, xi->tx_sring, PAGE_SIZE);
    pfn = (PFN_NUMBER)(MmGetPhysicalAddress(xi->tx_sring).QuadPart >> PAGE_SHIFT);
    FUNCTION_MSG("tx sring pfn = %d\n", (ULONG)pfn);
    xi->tx_sring_gref = XnGrantAccess(xi->handle, (ULONG)pfn, FALSE, INVALID_GRANT_REF, XENNET_POOL_TAG);
    FUNCTION_MSG("tx sring_gref = %d\n", xi->tx_sring_gref);
    status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "tx-ring-ref", xi->tx_sring_gref);  
    xi->rx_sring = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENNET_POOL_TAG);
    if (!xi->rx_sring) {
      FUNCTION_MSG("Cannot allocate rx_sring\n");
      return STATUS_UNSUCCESSFUL;
    }
    SHARED_RING_INIT(xi->rx_sring);
    FRONT_RING_INIT(&xi->rx_ring, xi->rx_sring, PAGE_SIZE);
    pfn = (PFN_NUMBER)(MmGetPhysicalAddress(xi->rx_sring).QuadPart >> PAGE_SHIFT);
    FUNCTION_MSG("rx sring pfn = %d\n", (ULONG)pfn);
    xi->rx_sring_gref = XnGrantAccess(xi->handle, (ULONG)pfn, FALSE, INVALID_GRANT_REF, XENNET_POOL_TAG);
    FUNCTION_MSG("rx sring_gref = %d\n", xi->rx_sring_gref);
    status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "rx-ring-ref", xi->rx_sring_gref);  

    status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "request-rx-copy", 1);
    status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "request-rx-notify", 1);
    status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "feature-no-csum-offload", !xi->frontend_csum_supported);
    status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "feature-sg", (int)xi->frontend_sg_supported);
    status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "feature-gso-tcpv4", !!xi->frontend_gso_value);
  }
  
  /* backend always supports checksum offload */
  xi->backend_csum_supported = TRUE;
  
  status = XnReadInt32(xi->handle, XN_BASE_BACKEND, "feature-sg", &tmp_ulong);
  if (NT_SUCCESS(status) && tmp_ulong) {
    xi->backend_sg_supported = TRUE;
  } else {
    xi->backend_sg_supported = FALSE;
  }
  status = XnReadInt32(xi->handle, XN_BASE_BACKEND, "feature-gso-tcpv4", &tmp_ulong);
  if (NT_SUCCESS(status) && tmp_ulong) {
    xi->backend_gso_value = xi->frontend_gso_value;
  } else {
    xi->backend_gso_value = FALSE;
  }

  status = XnReadString(xi->handle, XN_BASE_BACKEND, "mac", &tmp_string);
  state = 0;
  octet = 0;
  for (i = 0; state != 3 && i < (int)strlen(tmp_string); i++) {
    if (octet == 6) {
      state = 3;
      break;
    }
    switch(state) {
    case 0:
    case 1:
      if (tmp_string[i] >= '0' && tmp_string[i] <= '9') {
        xi->perm_mac_addr[octet] |= (tmp_string[i] - '0') << ((1 - state) * 4);
        state++;
      } else if (tmp_string[i] >= 'A' && tmp_string[i] <= 'F') {
        xi->perm_mac_addr[octet] |= (tmp_string[i] - 'A' + 10) << ((1 - state) * 4);
        state++;
      } else if (tmp_string[i] >= 'a' && tmp_string[i] <= 'f') {
        xi->perm_mac_addr[octet] |= (tmp_string[i] - 'a' + 10) << ((1 - state) * 4);
        state++;
      } else {
        state = 3;
      }
      break;
    case 2:
      if (tmp_string[i] == ':') {
        octet++;
        state = 0;
      } else {
        state = 3;
      }
      break;
    }
  }
  if (octet != 5 || state != 2) {
    FUNCTION_MSG("Failed to parse backend MAC address %s\n", tmp_string);
    XnFreeMem(xi->handle, tmp_string);
    return STATUS_UNSUCCESSFUL;
  } else if ((xi->curr_mac_addr[0] & 0x03) != 0x02) {
    /* only copy if curr_mac_addr is not a LUA */
    memcpy(xi->curr_mac_addr, xi->perm_mac_addr, ETH_ALEN);
  }
  XnFreeMem(xi->handle, tmp_string);
  FUNCTION_MSG("MAC address is %02X:%02X:%02X:%02X:%02X:%02X\n",
    xi->curr_mac_addr[0], xi->curr_mac_addr[1], xi->curr_mac_addr[2], 
    xi->curr_mac_addr[3], xi->curr_mac_addr[4], xi->curr_mac_addr[5]);

  if (xi->device_state != DEVICE_STATE_INACTIVE) {
    status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "state", XenbusStateConnected);

    for (i = 0; i <= 5 && xi->backend_state != XenbusStateConnected; i++) {
      FUNCTION_MSG("Waiting for XenbusStateConnected\n");
      timeout.QuadPart = -10 * 1000 * 1000; /* 1 second */
      KeWaitForSingleObject(&xi->backend_event, Executive, KernelMode, FALSE, &timeout);
    }
    if (xi->backend_state != XenbusStateConnected) {
      FUNCTION_MSG("Backend state timeout\n");
      return STATUS_UNSUCCESSFUL;
    }
    XenNet_TxInit(xi);
    XenNet_RxInit(xi);
  }

  /* we don't set device_state = DEVICE_STATE_ACTIVE here - has to be done during init once ndis is ready */
  
  return STATUS_SUCCESS;
}

NTSTATUS
XenNet_Disconnect(PVOID context, BOOLEAN suspend) {
  struct xennet_info *xi = (struct xennet_info *)context;
  //PFN_NUMBER pfn;
  LARGE_INTEGER timeout;
  NTSTATUS status;

  if (xi->device_state != DEVICE_STATE_ACTIVE && xi->device_state != DEVICE_STATE_INACTIVE) {
    FUNCTION_MSG("state not DEVICE_STATE_(IN)ACTIVE, is %d instead\n", xi->device_state);
    FUNCTION_EXIT();
    return STATUS_SUCCESS;
  }
  if (xi->device_state != DEVICE_STATE_INACTIVE) {
    xi->device_state = DEVICE_STATE_DISCONNECTING;
    status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "state", XenbusStateClosing);
    while (xi->backend_state != XenbusStateClosing && xi->backend_state != XenbusStateClosed) {
      FUNCTION_MSG("Waiting for XenbusStateClosing/Closed\n");
      timeout.QuadPart = -10 * 1000 * 1000; /* 1 second */
      KeWaitForSingleObject(&xi->backend_event, Executive, KernelMode, FALSE, &timeout);
    }
    status = XnWriteInt32(xi->handle, XN_BASE_FRONTEND, "state", XenbusStateClosed);
    while (xi->backend_state != XenbusStateClosed) {
      FUNCTION_MSG("Waiting for XenbusStateClosed\n");
      timeout.QuadPart = -10 * 1000 * 1000; /* 1 second */
      KeWaitForSingleObject(&xi->backend_event, Executive, KernelMode, FALSE, &timeout);
    }
    XnUnbindEvent(xi->handle, xi->event_channel);
    
  #if NTDDI_VERSION < WINXP
    KeFlushQueuedDpcs();
  #endif
    XenNet_TxShutdown(xi);
    XenNet_RxShutdown(xi);
    XnEndAccess(xi->handle, xi->rx_sring_gref, FALSE, XENNET_POOL_TAG);
    ExFreePoolWithTag(xi->rx_sring, XENNET_POOL_TAG);
    XnEndAccess(xi->handle, xi->tx_sring_gref, FALSE, XENNET_POOL_TAG);
    ExFreePoolWithTag(xi->tx_sring, XENNET_POOL_TAG);
  }
  if (!suspend) {
    XnCloseDevice(xi->handle);
  }
  xi->device_state = DEVICE_STATE_DISCONNECTED;
  return STATUS_SUCCESS;
}

VOID
XenNet_DeviceCallback(PVOID context, ULONG callback_type, PVOID value) {
  struct xennet_info *xi = (struct xennet_info *)context;
  ULONG state;
  NTSTATUS status;
  
  FUNCTION_ENTER();
  switch (callback_type) {
  case XN_DEVICE_CALLBACK_BACKEND_STATE:
    state = (ULONG)(ULONG_PTR)value;
    if (state == xi->backend_state) {
      FUNCTION_MSG("same state %d\n", state);
      FUNCTION_EXIT();
    }
    FUNCTION_MSG("XenBusState = %d -> %d\n", xi->backend_state, state);
    xi->backend_state = state;
    KeSetEvent(&xi->backend_event, 0, FALSE);
    break;
  case XN_DEVICE_CALLBACK_SUSPEND:
    FUNCTION_MSG("XN_DEVICE_CALLBACK_SUSPEND");
    XenNet_Disconnect(xi, TRUE);
    break;
  case XN_DEVICE_CALLBACK_RESUME:
    FUNCTION_MSG("XN_DEVICE_CALLBACK_RESUME");
    xi->device_state = DEVICE_STATE_INITIALISING;
    status = XenNet_Connect(xi, TRUE);
    // TODO: what to do here if not success?
    if (xi->device_state != DEVICE_STATE_INACTIVE) {
      xi->device_state = DEVICE_STATE_ACTIVE;
    }
    KeInsertQueueDpc(&xi->rxtx_dpc, NULL, NULL);
    break;
  }
  FUNCTION_EXIT();
}

