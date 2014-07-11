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

#define DEF_OID_QUERY(oid, min_length) {oid, #oid, min_length, XenNet_Query##oid, NULL}
#define DEF_OID_QUERYSET(oid, min_length) {oid, #oid, min_length, XenNet_Query##oid, XenNet_Set##oid}
#define DEF_OID_SET(oid, min_length) {oid, #oid, min_length, NULL, XenNet_Set##oid}
#define DEF_OID_NONE(oid) {oid, #oid, 0, NULL, NULL} /* define this for a silent but unsupported oid */

#define DEF_OID_QUERY_STAT(oid) DEF_OID_QUERY(##oid, 0) /* has to be 0 so the 4/8 size works */
#define DEF_OID_QUERY_ULONG(oid) DEF_OID_QUERY(##oid, sizeof(ULONG))
#define DEF_OID_QUERYSET_ULONG(oid) DEF_OID_QUERYSET(##oid, sizeof(ULONG))
#define DEF_OID_SET_ULONG(oid) DEF_OID_SET(##oid, sizeof(ULONG))

#define DEF_OID_QUERY_ROUTINE(oid, value, length) \
NDIS_STATUS \
XenNet_Query##oid(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_written, PULONG bytes_needed) { \
  struct xennet_info *xi = context; \
  UNREFERENCED_PARAMETER(xi); \
  if (information_buffer_length < length) \
  { \
    *bytes_needed = length; \
    return NDIS_STATUS_BUFFER_TOO_SHORT; \
  } \
  *bytes_written = length; \
  NdisMoveMemory(information_buffer, value, length); \
  return STATUS_SUCCESS; \
}

#define DEF_OID_QUERY_ULONG_ROUTINE(oid, value) \
NDIS_STATUS \
XenNet_Query##oid(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_written, PULONG bytes_needed) { \
  struct xennet_info *xi = context; \
  UNREFERENCED_PARAMETER(xi); \
  UNREFERENCED_PARAMETER(information_buffer_length); \
  UNREFERENCED_PARAMETER(bytes_needed); \
  *bytes_written = sizeof(ULONG); \
  *(ULONG *)information_buffer = value; \
  return STATUS_SUCCESS; \
}

#define DEF_OID_QUERY_STAT_ROUTINE(oid, value) \
NDIS_STATUS \
XenNet_Query##oid(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_written, PULONG bytes_needed) { \
  struct xennet_info *xi = context; \
  UNREFERENCED_PARAMETER(xi); \
  if (information_buffer_length >= sizeof(ULONG64)) \
  { \
    *bytes_written = sizeof(ULONG64); \
    *(ULONG64 *)information_buffer = (value); \
  } \
  else if (information_buffer_length >= sizeof(ULONG)) \
  { \
    *bytes_written = sizeof(ULONG); \
    *bytes_needed = sizeof(ULONG64); \
    *(ULONG *)information_buffer = (ULONG)(value); \
  } \
  else \
  { \
    *bytes_needed = sizeof(ULONG64); \
    return NDIS_STATUS_BUFFER_TOO_SHORT; \
  } \
  return STATUS_SUCCESS; \
}

DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_MAXIMUM_TOTAL_SIZE, xi->current_mtu_value + XN_HDR_SIZE)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_CURRENT_PACKET_FILTER, xi->packet_filter)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_CURRENT_LOOKAHEAD, xi->current_lookahead)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_TRANSMIT_BUFFER_SPACE, PAGE_SIZE * NET_TX_RING_SIZE * 4)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_RECEIVE_BUFFER_SPACE, PAGE_SIZE * NET_RX_RING_SIZE * 2)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_TRANSMIT_BLOCK_SIZE, PAGE_SIZE)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_RECEIVE_BLOCK_SIZE, PAGE_SIZE)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_MAXIMUM_SEND_PACKETS, 0)
DEF_OID_QUERY_ULONG_ROUTINE(OID_802_3_MAXIMUM_LIST_SIZE, MULTICAST_LIST_MAX_SIZE)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_HARDWARE_STATUS, (xi->device_state == DEVICE_STATE_INACTIVE || xi->device_state == DEVICE_STATE_ACTIVE)?NdisHardwareStatusReady:NdisHardwareStatusInitializing)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_VENDOR_ID, 0xFFFFFF) // Not guaranteed to be XENSOURCE_MAC_HDR;
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_VENDOR_DRIVER_VERSION, VENDOR_DRIVER_VERSION)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_MEDIA_SUPPORTED, NdisMedium802_3)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_MEDIA_IN_USE, NdisMedium802_3)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_MAXIMUM_LOOKAHEAD, MAX_LOOKAHEAD_LENGTH)

#if NTDDI_VERSION < NTDDI_VISTA
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_MAXIMUM_FRAME_SIZE, xi->current_mtu_value);
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_MAC_OPTIONS, NDIS_MAC_OPTION_COPY_LOOKAHEAD_DATA | NDIS_MAC_OPTION_TRANSFERS_NOT_PEND | NDIS_MAC_OPTION_NO_LOOPBACK);
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_MEDIA_CONNECT_STATUS, (xi->device_state == DEVICE_STATE_ACTIVE)?NdisMediaStateConnected:NdisMediaStateDisconnected);
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_LINK_SPEED, (ULONG)(MAX_LINK_SPEED / 100));

DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_XMIT_OK, xi->stat_tx_ok)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_XMIT_ERROR, xi->stat_tx_error)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_RCV_OK, xi->stat_rx_ok)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_RCV_ERROR, xi->stat_rx_error)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_RCV_NO_BUFFER, xi->stat_rx_no_buffer)
#else
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_XMIT_OK, xi->stats.ifHCOutUcastPkts + xi->stats.ifHCOutMulticastPkts + xi->stats.ifHCOutBroadcastPkts)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_XMIT_ERROR, xi->stats.ifOutErrors)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_RCV_OK, xi->stats.ifHCInUcastPkts + xi->stats.ifHCInMulticastPkts + xi->stats.ifHCInBroadcastPkts)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_RCV_ERROR, xi->stats.ifInErrors)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_RCV_NO_BUFFER, xi->stats.ifInDiscards)
#endif
DEF_OID_QUERY_STAT_ROUTINE(OID_802_3_RCV_ERROR_ALIGNMENT, 0)
DEF_OID_QUERY_STAT_ROUTINE(OID_802_3_XMIT_ONE_COLLISION, 0)
DEF_OID_QUERY_STAT_ROUTINE(OID_802_3_XMIT_MORE_COLLISIONS, 0)

DEF_OID_QUERY_ROUTINE(OID_GEN_VENDOR_DESCRIPTION, XN_VENDOR_DESC, sizeof(XN_VENDOR_DESC))

DEF_OID_QUERY_ROUTINE(OID_802_3_PERMANENT_ADDRESS, xi->perm_mac_addr, ETH_ALEN)
DEF_OID_QUERY_ROUTINE(OID_802_3_CURRENT_ADDRESS, xi->curr_mac_addr, ETH_ALEN)

DEF_OID_QUERY_ROUTINE(OID_802_3_MULTICAST_LIST, xi->multicast_list, xi->multicast_list_size * 6)

NDIS_STATUS
XenNet_SetOID_802_3_MULTICAST_LIST(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed) {
  struct xennet_info *xi = context;
  UCHAR *multicast_list;
  int i;
  UNREFERENCED_PARAMETER(bytes_read);
  UNREFERENCED_PARAMETER(bytes_needed);

  if (information_buffer_length > MULTICAST_LIST_MAX_SIZE * 6) {
    return NDIS_STATUS_MULTICAST_FULL;
  }
  
  if (information_buffer_length % 6 != 0) {
    return NDIS_STATUS_MULTICAST_FULL;
  }
  multicast_list = information_buffer;
  for (i = 0; i < (int)information_buffer_length / 6; i++) {
    if (!(multicast_list[i * 6 + 0] & 0x01)) {
      FUNCTION_MSG("Address %d (%02x:%02x:%02x:%02x:%02x:%02x) is not a multicast address\n", i,
        (ULONG)multicast_list[i * 6 + 0], (ULONG)multicast_list[i * 6 + 1], 
        (ULONG)multicast_list[i * 6 + 2], (ULONG)multicast_list[i * 6 + 3], 
        (ULONG)multicast_list[i * 6 + 4], (ULONG)multicast_list[i * 6 + 5]);
      /* the docs say that we should return NDIS_STATUS_MULTICAST_FULL if we get an invalid multicast address but I'm not sure if that's the case... */
    }
  }
  memcpy(xi->multicast_list, multicast_list, information_buffer_length);
  xi->multicast_list_size = information_buffer_length / 6;
  return NDIS_STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_GEN_CURRENT_PACKET_FILTER(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed) {
  struct xennet_info *xi = context;
  PULONG data = information_buffer;
  
  UNREFERENCED_PARAMETER(information_buffer_length);
  *bytes_needed = sizeof(ULONG64);
  if (*data & NDIS_PACKET_TYPE_DIRECTED)
    FUNCTION_MSG("NDIS_PACKET_TYPE_DIRECTED\n");
  if (*data & NDIS_PACKET_TYPE_MULTICAST)
    FUNCTION_MSG("NDIS_PACKET_TYPE_MULTICAST\n");
  if (*data & NDIS_PACKET_TYPE_ALL_MULTICAST)
    FUNCTION_MSG("NDIS_PACKET_TYPE_ALL_MULTICAST\n");
  if (*data & NDIS_PACKET_TYPE_BROADCAST)
    FUNCTION_MSG("NDIS_PACKET_TYPE_BROADCAST\n");
  if (*data & NDIS_PACKET_TYPE_PROMISCUOUS)
    FUNCTION_MSG("NDIS_PACKET_TYPE_PROMISCUOUS\n");
  if (*data & NDIS_PACKET_TYPE_ALL_FUNCTIONAL)
    FUNCTION_MSG("NDIS_PACKET_TYPE_ALL_FUNCTIONAL (not supported)\n");
  if (*data & NDIS_PACKET_TYPE_ALL_LOCAL)
    FUNCTION_MSG("NDIS_PACKET_TYPE_ALL_LOCAL (not supported)\n");
  if (*data & NDIS_PACKET_TYPE_FUNCTIONAL)
    FUNCTION_MSG("NDIS_PACKET_TYPE_FUNCTIONAL (not supported)\n");
  if (*data & NDIS_PACKET_TYPE_GROUP)
    FUNCTION_MSG("NDIS_PACKET_TYPE_GROUP (not supported)\n");
  if (*data & ~SUPPORTED_PACKET_FILTERS) {
    FUNCTION_MSG("returning NDIS_STATUS_NOT_SUPPORTED\n");
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  xi->packet_filter = *(ULONG *)data;
  *bytes_read = sizeof(ULONG);
  return NDIS_STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_GEN_CURRENT_LOOKAHEAD(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed) {
  struct xennet_info *xi = context;
  PULONG data = information_buffer;
  UNREFERENCED_PARAMETER(information_buffer_length);
  UNREFERENCED_PARAMETER(bytes_read);
  UNREFERENCED_PARAMETER(bytes_needed);
  xi->current_lookahead = *(ULONG *)data;
  FUNCTION_MSG("Set OID_GEN_CURRENT_LOOKAHEAD %d (%p)\n", xi->current_lookahead, xi);
  return NDIS_STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_GEN_LINK_PARAMETERS(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed) {
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(information_buffer);
  UNREFERENCED_PARAMETER(information_buffer_length);
  UNREFERENCED_PARAMETER(bytes_read);
  UNREFERENCED_PARAMETER(bytes_needed);
  return STATUS_NOT_SUPPORTED;
}

#if NTDDI_VERSION < NTDDI_VISTA
NDIS_STATUS
XenNet_QueryOID_GEN_SUPPORTED_LIST(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_written, PULONG bytes_needed) {
  PNDIS_OID supported_oids;
  int i;
  
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(information_buffer);
  UNREFERENCED_PARAMETER(information_buffer_length);
  UNREFERENCED_PARAMETER(bytes_written);
  UNREFERENCED_PARAMETER(bytes_needed);

  for (i = 0; xennet_oids[i].oid; i++);

  if (information_buffer_length < sizeof(NDIS_OID) * i) {
    *bytes_needed = sizeof(NDIS_OID) * i;
    return NDIS_STATUS_BUFFER_TOO_SHORT;
  }

  supported_oids = information_buffer;
  for (i = 0; xennet_oids[i].oid; i++) {
    supported_oids[i] = xennet_oids[i].oid;
    FUNCTION_MSG("Supporting %08x (%s) %s %d bytes\n", xennet_oids[i].oid, xennet_oids[i].oid_name, (xennet_oids[i].query_routine?(xennet_oids[i].set_routine?"get/set":"get only"):(xennet_oids[i].set_routine?"set only":"none")), xennet_oids[i].min_length);
  }
  return STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_QueryOID_GEN_DRIVER_VERSION(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_written, PULONG bytes_needed) {
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(bytes_needed);
  UNREFERENCED_PARAMETER(information_buffer_length);
  *(PUSHORT)information_buffer = (NDIS_MINIPORT_MAJOR_VERSION << 8) | NDIS_MINIPORT_MINOR_VERSION;
  *bytes_written = sizeof(USHORT);
  return STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_QueryOID_PNP_CAPABILITIES(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_written, PULONG bytes_needed) {
  PNDIS_PNP_CAPABILITIES npc = (PNDIS_PNP_CAPABILITIES)information_buffer;
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(information_buffer_length);
  UNREFERENCED_PARAMETER(bytes_needed);
  npc->Flags = 0;
  npc->WakeUpCapabilities.MinMagicPacketWakeUp = NdisDeviceStateUnspecified;
  npc->WakeUpCapabilities.MinPatternWakeUp = NdisDeviceStateUnspecified;
  npc->WakeUpCapabilities.MinLinkChangeWakeUp = NdisDeviceStateUnspecified;
  *bytes_written = sizeof(NDIS_PNP_CAPABILITIES);
  return STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_QueryOID_PNP_QUERY_POWER(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_written, PULONG bytes_needed) {
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(information_buffer);
  UNREFERENCED_PARAMETER(information_buffer_length);
  UNREFERENCED_PARAMETER(bytes_written);
  UNREFERENCED_PARAMETER(bytes_needed);
  /* all we need to do here is return STATUS_SUCCESS to acknowledge - SET_POWER will happen later */
  return STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_GEN_PROTOCOL_OPTIONS(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed) {
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(information_buffer);
  UNREFERENCED_PARAMETER(information_buffer_length);
  UNREFERENCED_PARAMETER(bytes_read);
  UNREFERENCED_PARAMETER(bytes_needed);
  /* nothing useful here */
  return STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_QueryOID_TCP_TASK_OFFLOAD(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_written, PULONG bytes_needed) {
  struct xennet_info *xi = context;
  PNDIS_TASK_OFFLOAD_HEADER ntoh;
  PNDIS_TASK_OFFLOAD nto;
  PNDIS_TASK_TCP_IP_CHECKSUM nttic;
  PNDIS_TASK_TCP_LARGE_SEND nttls;

  *bytes_needed = sizeof(NDIS_TASK_OFFLOAD_HEADER);

  if (xi->backend_csum_supported)
    *bytes_needed += FIELD_OFFSET(NDIS_TASK_OFFLOAD, TaskBuffer) + sizeof(NDIS_TASK_TCP_IP_CHECKSUM);

  if (xi->backend_gso_value)
    *bytes_needed += FIELD_OFFSET(NDIS_TASK_OFFLOAD, TaskBuffer) + sizeof(NDIS_TASK_TCP_LARGE_SEND);

  if (*bytes_needed > information_buffer_length)
    return NDIS_STATUS_BUFFER_TOO_SHORT;

  ntoh = (PNDIS_TASK_OFFLOAD_HEADER)information_buffer;
  if (ntoh->Version != NDIS_TASK_OFFLOAD_VERSION
    || ntoh->Size != sizeof(*ntoh)
    || !(ntoh->EncapsulationFormat.Encapsulation == IEEE_802_3_Encapsulation
      || (ntoh->EncapsulationFormat.Encapsulation == UNSPECIFIED_Encapsulation
          && ntoh->EncapsulationFormat.EncapsulationHeaderSize == XN_HDR_SIZE))) {
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  
  ntoh->OffsetFirstTask = 0; 
  nto = NULL;

  if (xi->backend_csum_supported) {
    if (ntoh->OffsetFirstTask == 0) {
      ntoh->OffsetFirstTask = ntoh->Size;
      nto = (PNDIS_TASK_OFFLOAD)((PCHAR)(ntoh) + ntoh->OffsetFirstTask);
    } else {
      nto->OffsetNextTask = FIELD_OFFSET(NDIS_TASK_OFFLOAD, TaskBuffer)
        + nto->TaskBufferLength;
      nto = (PNDIS_TASK_OFFLOAD)((PCHAR)(nto) + nto->OffsetNextTask);
    }
    /* fill in first nto */
    nto->Version = NDIS_TASK_OFFLOAD_VERSION;
    nto->Size = sizeof(NDIS_TASK_OFFLOAD);
    nto->Task = TcpIpChecksumNdisTask;
    nto->TaskBufferLength = sizeof(NDIS_TASK_TCP_IP_CHECKSUM);

    FUNCTION_MSG("config_csum enabled\n");
    FUNCTION_MSG("nto = %p\n", nto);
    FUNCTION_MSG("nto->Size = %d\n", nto->Size);
    FUNCTION_MSG("nto->TaskBufferLength = %d\n", nto->TaskBufferLength);

    /* fill in checksum offload struct */
    nttic = (PNDIS_TASK_TCP_IP_CHECKSUM)nto->TaskBuffer;
    nttic->V4Transmit.IpChecksum = 0;
    nttic->V4Transmit.IpOptionsSupported = 0;
    nttic->V4Transmit.TcpChecksum = 1;
    nttic->V4Transmit.TcpOptionsSupported = 1;
    nttic->V4Transmit.UdpChecksum = 1;
    nttic->V4Receive.IpChecksum = 1;
    nttic->V4Receive.IpOptionsSupported = 1;
    nttic->V4Receive.TcpChecksum = 1;
    nttic->V4Receive.TcpOptionsSupported = 1;
    nttic->V4Receive.UdpChecksum = 1;
    nttic->V6Transmit.IpOptionsSupported = 0;
    nttic->V6Transmit.TcpOptionsSupported = 0;
    nttic->V6Transmit.TcpChecksum = 0;
    nttic->V6Transmit.UdpChecksum = 0;
    nttic->V6Receive.IpOptionsSupported = 0;
    nttic->V6Receive.TcpOptionsSupported = 0;
    nttic->V6Receive.TcpChecksum = 0;
    nttic->V6Receive.UdpChecksum = 0;
  }
  if (xi->backend_gso_value) {
    if (ntoh->OffsetFirstTask == 0) {
      ntoh->OffsetFirstTask = ntoh->Size;
      nto = (PNDIS_TASK_OFFLOAD)((PCHAR)(ntoh) + ntoh->OffsetFirstTask);
    } else {
      nto->OffsetNextTask = FIELD_OFFSET(NDIS_TASK_OFFLOAD, TaskBuffer)
        + nto->TaskBufferLength;
      nto = (PNDIS_TASK_OFFLOAD)((PCHAR)(nto) + nto->OffsetNextTask);
    }

    /* fill in second nto */
    nto->Version = NDIS_TASK_OFFLOAD_VERSION;
    nto->Size = sizeof(NDIS_TASK_OFFLOAD);
    nto->Task = TcpLargeSendNdisTask;
    nto->TaskBufferLength = sizeof(NDIS_TASK_TCP_LARGE_SEND);

    FUNCTION_MSG("config_gso enabled\n");
    FUNCTION_MSG("nto = %p\n", nto);
    FUNCTION_MSG("nto->Size = %d\n", nto->Size);
    FUNCTION_MSG("nto->TaskBufferLength = %d\n", nto->TaskBufferLength);

    /* fill in large send struct */
    nttls = (PNDIS_TASK_TCP_LARGE_SEND)nto->TaskBuffer;
    nttls->Version = 0;
    nttls->MaxOffLoadSize = xi->backend_gso_value;
    nttls->MinSegmentCount = MIN_LARGE_SEND_SEGMENTS;
    nttls->TcpOptions = FALSE; /* linux can't handle this */
    nttls->IpOptions = FALSE; /* linux can't handle this */
    FUNCTION_MSG("&(nttls->IpOptions) = %p\n", &(nttls->IpOptions));        
  }

  if (nto)
    nto->OffsetNextTask = 0; /* last one */

  *bytes_written = *bytes_needed;
  return STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_TCP_TASK_OFFLOAD(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed) {
  struct xennet_info *xi = context;
  PNDIS_TASK_OFFLOAD_HEADER ntoh;
  PNDIS_TASK_OFFLOAD nto;
  PNDIS_TASK_TCP_IP_CHECKSUM nttic = NULL;
  PNDIS_TASK_TCP_LARGE_SEND nttls = NULL;
  ULONG offset;

  UNREFERENCED_PARAMETER(bytes_needed);
  UNREFERENCED_PARAMETER(information_buffer_length);
  
  // we should disable everything here, then enable what has been set
  ntoh = (PNDIS_TASK_OFFLOAD_HEADER)information_buffer;
  if (ntoh->Version != NDIS_TASK_OFFLOAD_VERSION) {
    FUNCTION_MSG("Invalid version (%d passed but must be %d)\n", ntoh->Version, NDIS_TASK_OFFLOAD_VERSION);
    return NDIS_STATUS_INVALID_DATA;
  }
  if (ntoh->Version != NDIS_TASK_OFFLOAD_VERSION || ntoh->Size != sizeof(NDIS_TASK_OFFLOAD_HEADER)) {
    FUNCTION_MSG("Invalid size (%d passed but must be %d)\n", ntoh->Size, sizeof(NDIS_TASK_OFFLOAD_HEADER));
    return NDIS_STATUS_INVALID_DATA;
  }
  *bytes_read = sizeof(NDIS_TASK_OFFLOAD_HEADER);
  offset = ntoh->OffsetFirstTask;
  nto = (PNDIS_TASK_OFFLOAD)ntoh; // not really, just to get the first offset right
  while (offset != 0) {
    *bytes_read += FIELD_OFFSET(NDIS_TASK_OFFLOAD, TaskBuffer);
    nto = (PNDIS_TASK_OFFLOAD)(((PUCHAR)nto) + offset);
    switch (nto->Task) {
    case TcpIpChecksumNdisTask:
      *bytes_read += sizeof(NDIS_TASK_TCP_IP_CHECKSUM);
      nttic = (PNDIS_TASK_TCP_IP_CHECKSUM)nto->TaskBuffer;
      FUNCTION_MSG("TcpIpChecksumNdisTask\n");
      FUNCTION_MSG("  V4Transmit.IpOptionsSupported  = %d\n", nttic->V4Transmit.IpOptionsSupported);
      FUNCTION_MSG("  V4Transmit.TcpOptionsSupported = %d\n", nttic->V4Transmit.TcpOptionsSupported);
      FUNCTION_MSG("  V4Transmit.TcpChecksum         = %d\n", nttic->V4Transmit.TcpChecksum);
      FUNCTION_MSG("  V4Transmit.UdpChecksum         = %d\n", nttic->V4Transmit.UdpChecksum);
      FUNCTION_MSG("  V4Transmit.IpChecksum          = %d\n", nttic->V4Transmit.IpChecksum);
      FUNCTION_MSG("  V4Receive.IpOptionsSupported   = %d\n", nttic->V4Receive.IpOptionsSupported);
      FUNCTION_MSG("  V4Receive.TcpOptionsSupported  = %d\n", nttic->V4Receive.TcpOptionsSupported);
      FUNCTION_MSG("  V4Receive.TcpChecksum          = %d\n", nttic->V4Receive.TcpChecksum);
      FUNCTION_MSG("  V4Receive.UdpChecksum          = %d\n", nttic->V4Receive.UdpChecksum);
      FUNCTION_MSG("  V4Receive.IpChecksum           = %d\n", nttic->V4Receive.IpChecksum);
      FUNCTION_MSG("  V6Transmit.IpOptionsSupported  = %d\n", nttic->V6Transmit.IpOptionsSupported);
      FUNCTION_MSG("  V6Transmit.TcpOptionsSupported = %d\n", nttic->V6Transmit.TcpOptionsSupported);
      FUNCTION_MSG("  V6Transmit.TcpChecksum         = %d\n", nttic->V6Transmit.TcpChecksum);
      FUNCTION_MSG("  V6Transmit.UdpChecksum         = %d\n", nttic->V6Transmit.UdpChecksum);
      FUNCTION_MSG("  V6Receive.IpOptionsSupported   = %d\n", nttic->V6Receive.IpOptionsSupported);
      FUNCTION_MSG("  V6Receive.TcpOptionsSupported  = %d\n", nttic->V6Receive.TcpOptionsSupported);
      FUNCTION_MSG("  V6Receive.TcpChecksum          = %d\n", nttic->V6Receive.TcpChecksum);
      FUNCTION_MSG("  V6Receive.UdpChecksum          = %d\n", nttic->V6Receive.UdpChecksum);
      /* check for stuff we outright don't support */
      if (nttic->V6Transmit.IpOptionsSupported ||
          nttic->V6Transmit.TcpOptionsSupported ||
          nttic->V6Transmit.TcpChecksum ||
          nttic->V6Transmit.UdpChecksum ||
          nttic->V6Receive.IpOptionsSupported ||
          nttic->V6Receive.TcpOptionsSupported ||
          nttic->V6Receive.TcpChecksum ||
          nttic->V6Receive.UdpChecksum) {
        FUNCTION_MSG("IPv6 offload not supported\n");
        return NDIS_STATUS_INVALID_DATA;
      }
      if (nttic->V4Transmit.IpOptionsSupported || nttic->V4Transmit.IpChecksum) {
        FUNCTION_MSG("IPv4 IP Transmit offload not supported\n");
        return NDIS_STATUS_INVALID_DATA;
      }
      if (nttic->V4Receive.IpOptionsSupported && !nttic->V4Receive.IpChecksum) {
        FUNCTION_MSG("Invalid combination\n");
        return NDIS_STATUS_INVALID_DATA;
      }
      if (nttic->V4Transmit.TcpOptionsSupported && !nttic->V4Transmit.TcpChecksum) {
        FUNCTION_MSG("Invalid combination\n");
        return NDIS_STATUS_INVALID_DATA;
      }
      if (nttic->V4Receive.TcpOptionsSupported && !nttic->V4Receive.TcpChecksum) {
        FUNCTION_MSG("Invalid combination\n");
        return NDIS_STATUS_INVALID_DATA;
      }
      break;
    case TcpLargeSendNdisTask:
      *bytes_read += sizeof(NDIS_TASK_TCP_LARGE_SEND);
      FUNCTION_MSG("TcpLargeSendNdisTask\n");
      nttls = (PNDIS_TASK_TCP_LARGE_SEND)nto->TaskBuffer;
      FUNCTION_MSG("  MaxOffLoadSize                 = %d\n", nttls->MaxOffLoadSize);
      FUNCTION_MSG("  MinSegmentCount                = %d\n", nttls->MinSegmentCount);
      FUNCTION_MSG("  TcpOptions                     = %d\n", nttls->TcpOptions);
      FUNCTION_MSG("  IpOptions                      = %d\n", nttls->IpOptions);
      if (nttls->MinSegmentCount != MIN_LARGE_SEND_SEGMENTS) {
        FUNCTION_MSG("MinSegmentCount should be %d\n", MIN_LARGE_SEND_SEGMENTS);
        return NDIS_STATUS_INVALID_DATA;
      }
      if (nttls->IpOptions) {
        FUNCTION_MSG("IpOptions not supported\n");
        return NDIS_STATUS_INVALID_DATA;
      }
      if (nttls->TcpOptions) {
        FUNCTION_MSG("TcpOptions not supported\n");
        return NDIS_STATUS_INVALID_DATA;
      }
      break;
    default:
      FUNCTION_MSG("Unknown Task %d\n", nto->Task);
    }
    offset = nto->OffsetNextTask;
  }
  if (nttic != NULL) {
    xi->current_csum_supported = TRUE;
    xi->setting_csum = *nttic;
  } else {
    RtlZeroMemory(&xi->setting_csum, sizeof(NDIS_TASK_TCP_IP_CHECKSUM));
    FUNCTION_MSG("csum offload disabled\n", nto->Task);
  }        
  if (nttls != NULL)
    xi->current_gso_value = nttls->MaxOffLoadSize;
  else {
    xi->current_gso_value = 0;
    FUNCTION_MSG("LSO disabled\n", nto->Task);
  }
  return STATUS_SUCCESS;
}
#else
NDIS_STATUS
XenNet_QueryOID_GEN_INTERRUPT_MODERATION(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_written, PULONG bytes_needed) {
  PNDIS_INTERRUPT_MODERATION_PARAMETERS nimp;
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(bytes_needed);
  UNREFERENCED_PARAMETER(information_buffer_length);
  nimp = (PNDIS_INTERRUPT_MODERATION_PARAMETERS)information_buffer;
  nimp->Header.Type = NDIS_OBJECT_TYPE_DEFAULT;
  nimp->Header.Revision = NDIS_INTERRUPT_MODERATION_PARAMETERS_REVISION_1;
  nimp->Header.Size = NDIS_SIZEOF_INTERRUPT_MODERATION_PARAMETERS_REVISION_1;
  nimp->Flags = 0;
  nimp->InterruptModeration = NdisInterruptModerationNotSupported;
  *bytes_written = sizeof(NDIS_INTERRUPT_MODERATION_PARAMETERS);
  return STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_GEN_INTERRUPT_MODERATION(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed) {
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(information_buffer);
  UNREFERENCED_PARAMETER(information_buffer_length);
  UNREFERENCED_PARAMETER(bytes_read);
  UNREFERENCED_PARAMETER(bytes_needed);
  return STATUS_NOT_SUPPORTED;
}

NDIS_STATUS
XenNet_QueryOID_GEN_STATISTICS(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_written, PULONG bytes_needed) {
  struct xennet_info *xi = context;
  UNREFERENCED_PARAMETER(bytes_needed);
  UNREFERENCED_PARAMETER(information_buffer_length);

  NdisMoveMemory(information_buffer, &xi->stats, sizeof(NDIS_STATISTICS_INFO));
  *bytes_written = sizeof(NDIS_STATISTICS_INFO);
  return STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_OFFLOAD_ENCAPSULATION(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed) {
  struct xennet_info *xi = context;
  PNDIS_OFFLOAD_ENCAPSULATION noe = (PNDIS_OFFLOAD_ENCAPSULATION)information_buffer;
  UNREFERENCED_PARAMETER(bytes_needed);
  UNREFERENCED_PARAMETER(information_buffer_length);
  /* mostly assume that NDIS vets the settings for us */
  if (noe->IPv4.EncapsulationType != NDIS_ENCAPSULATION_IEEE_802_3) {
    FUNCTION_MSG("Unknown Encapsulation Type %d\n", noe->IPv4.EncapsulationType);
    return NDIS_STATUS_NOT_SUPPORTED;
  }
    
  switch(noe->IPv4.Enabled) {
  case NDIS_OFFLOAD_SET_ON:
    FUNCTION_MSG(" IPv4.Enabled = NDIS_OFFLOAD_SET_ON\n");
    xi->current_csum_supported = xi->backend_csum_supported && xi->frontend_csum_supported;
    xi->current_gso_value = min(xi->backend_csum_supported, xi->frontend_csum_supported);
    break;
  case NDIS_OFFLOAD_SET_OFF:
    FUNCTION_MSG(" IPv4.Enabled = NDIS_OFFLOAD_SET_OFF\n");
    xi->current_csum_supported = FALSE;
    xi->current_gso_value = 0;
    break;
  case NDIS_OFFLOAD_SET_NO_CHANGE:
    FUNCTION_MSG(" IPv4.Enabled = NDIS_OFFLOAD_NO_CHANGE\n");
    break;
  }
  FUNCTION_MSG(" IPv4.HeaderSize = %d\n", noe->IPv4.HeaderSize);
  FUNCTION_MSG(" IPv6.EncapsulationType = %d\n", noe->IPv6.EncapsulationType);
  switch(noe->IPv6.Enabled) {
  case NDIS_OFFLOAD_SET_ON:
    FUNCTION_MSG(" IPv6.Enabled = NDIS_OFFLOAD_SET_ON (this is an error)\n");
    break;
  case NDIS_OFFLOAD_SET_OFF:
    FUNCTION_MSG(" IPv6.Enabled = NDIS_OFFLOAD_SET_OFF\n");
    break;
  case NDIS_OFFLOAD_SET_NO_CHANGE:
    FUNCTION_MSG(" IPv6.Enabled = NDIS_OFFLOAD_NO_CHANGE\n");
    break;
  }
  *bytes_read = sizeof(NDIS_OFFLOAD_ENCAPSULATION);
  FUNCTION_MSG(" IPv6.HeaderSize = %d\n", noe->IPv6.HeaderSize);
  return NDIS_STATUS_SUCCESS;
}
#endif

NDIS_STATUS
XenNet_SetOID_PNP_SET_POWER(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed) {
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(information_buffer);
  UNREFERENCED_PARAMETER(information_buffer_length);
  UNREFERENCED_PARAMETER(bytes_read);
  UNREFERENCED_PARAMETER(bytes_needed);
  return STATUS_NOT_SUPPORTED;
}

NDIS_STATUS
XenNet_SetOID_GEN_NETWORK_LAYER_ADDRESSES(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed) {
  PNETWORK_ADDRESS_LIST nal = information_buffer;
  PNETWORK_ADDRESS na;
  PNETWORK_ADDRESS_IP ip;
  int i;
  
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(bytes_read);
  UNREFERENCED_PARAMETER(bytes_needed);
  FUNCTION_MSG("AddressType = %d\n", nal->AddressType);
  FUNCTION_MSG("AddressCount = %d\n", nal->AddressCount);
  if (nal->AddressCount == 0) {
    // remove addresses of AddressType type
  } else {
    na = nal->Address;
    for (i = 0; i < nal->AddressCount; i++) {
      if ((ULONG_PTR)na - (ULONG_PTR)nal + FIELD_OFFSET(NETWORK_ADDRESS, Address) + na->AddressLength > information_buffer_length) {
        FUNCTION_MSG("Out of bounds\n");
        return NDIS_STATUS_INVALID_DATA;
      }
      switch(na->AddressType) {
      case NDIS_PROTOCOL_ID_TCP_IP:
        FUNCTION_MSG("Address[%d].Type = NDIS_PROTOCOL_ID_TCP_IP\n", i);
        FUNCTION_MSG("Address[%d].Length = %d\n", i, na->AddressLength);
        if (na->AddressLength != NETWORK_ADDRESS_LENGTH_IP) {
          FUNCTION_MSG("Length is invalid\n");
          break;
        }
        ip = (PNETWORK_ADDRESS_IP)na->Address;
        FUNCTION_MSG("Address[%d].in_addr = %d.%d.%d.%d\n", i, ip->in_addr & 0xff, (ip->in_addr >> 8) & 0xff, (ip->in_addr >> 16) & 0xff, (ip->in_addr >> 24) & 0xff);
        break;
      default:
        FUNCTION_MSG("Address[%d].Type = %d\n", i, na->AddressType);
        FUNCTION_MSG("Address[%d].Length = %d\n", i, na->AddressLength);
        break;
      }
      na = (PNETWORK_ADDRESS)((PUCHAR)na + FIELD_OFFSET(NETWORK_ADDRESS, Address) + na->AddressLength);
    }
  }
  
  return NDIS_STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_GEN_MACHINE_NAME(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed) {
  UNICODE_STRING name;
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(bytes_read);
  UNREFERENCED_PARAMETER(bytes_needed);
   
  name.Length = (USHORT)information_buffer_length;
  name.MaximumLength = (USHORT)information_buffer_length;
  name.Buffer = information_buffer;
  FUNCTION_MSG("name = %wZ\n", &name);
  return NDIS_STATUS_SUCCESS;
}

struct xennet_oids_t xennet_oids[] = {
  DEF_OID_QUERY_ULONG(OID_GEN_HARDWARE_STATUS),

  DEF_OID_QUERY_ULONG(OID_GEN_TRANSMIT_BUFFER_SPACE),
  DEF_OID_QUERY_ULONG(OID_GEN_RECEIVE_BUFFER_SPACE),
  DEF_OID_QUERY_ULONG(OID_GEN_TRANSMIT_BLOCK_SIZE),
  DEF_OID_QUERY_ULONG(OID_GEN_RECEIVE_BLOCK_SIZE),

  DEF_OID_QUERY_ULONG(OID_GEN_VENDOR_ID),
  DEF_OID_QUERY(OID_GEN_VENDOR_DESCRIPTION, sizeof(XN_VENDOR_DESC)),
  DEF_OID_QUERY_ULONG(OID_GEN_VENDOR_DRIVER_VERSION),

  DEF_OID_QUERYSET_ULONG(OID_GEN_CURRENT_PACKET_FILTER),
  DEF_OID_QUERYSET_ULONG(OID_GEN_CURRENT_LOOKAHEAD),
  DEF_OID_QUERY_ULONG(OID_GEN_MAXIMUM_TOTAL_SIZE),
  
  DEF_OID_QUERY_ULONG(OID_GEN_MAXIMUM_SEND_PACKETS),
  DEF_OID_QUERY_ULONG(OID_GEN_MEDIA_SUPPORTED),
  DEF_OID_QUERY_ULONG(OID_GEN_MEDIA_IN_USE),
  DEF_OID_QUERY_ULONG(OID_GEN_MAXIMUM_LOOKAHEAD),

  /* general optional */
  DEF_OID_SET(OID_GEN_NETWORK_LAYER_ADDRESSES, FIELD_OFFSET(NETWORK_ADDRESS_LIST, Address)),
  DEF_OID_SET(OID_GEN_MACHINE_NAME, 0),

  /* power */
  DEF_OID_SET_ULONG(OID_PNP_SET_POWER),
  
  /* stats */
  DEF_OID_QUERY_STAT(OID_GEN_XMIT_OK),
  DEF_OID_QUERY_STAT(OID_GEN_RCV_OK),
  DEF_OID_QUERY_STAT(OID_GEN_XMIT_ERROR),
  DEF_OID_QUERY_STAT(OID_GEN_RCV_ERROR),
  DEF_OID_QUERY_STAT(OID_GEN_RCV_NO_BUFFER),
  DEF_OID_QUERY_STAT(OID_802_3_RCV_ERROR_ALIGNMENT),
  DEF_OID_QUERY_STAT(OID_802_3_XMIT_ONE_COLLISION),
  DEF_OID_QUERY_STAT(OID_802_3_XMIT_MORE_COLLISIONS),
  DEF_OID_NONE(OID_IP4_OFFLOAD_STATS),
  DEF_OID_NONE(OID_IP6_OFFLOAD_STATS),

  /* media-specific */
  DEF_OID_QUERY(OID_802_3_PERMANENT_ADDRESS, 6),
  DEF_OID_QUERY(OID_802_3_CURRENT_ADDRESS, 6),
  DEF_OID_QUERYSET(OID_802_3_MULTICAST_LIST, 0),
  DEF_OID_QUERY_ULONG(OID_802_3_MAXIMUM_LIST_SIZE),

#if NTDDI_VERSION < NTDDI_VISTA
  DEF_OID_QUERY(OID_GEN_SUPPORTED_LIST, 0),
  DEF_OID_QUERY_ULONG(OID_GEN_MAXIMUM_FRAME_SIZE),
  DEF_OID_QUERY_ULONG(OID_GEN_LINK_SPEED),
  DEF_OID_QUERY(OID_GEN_DRIVER_VERSION, sizeof(USHORT)),
  DEF_OID_QUERY_ULONG(OID_GEN_MAC_OPTIONS),
  DEF_OID_QUERY_ULONG(OID_GEN_MEDIA_CONNECT_STATUS),
  DEF_OID_QUERYSET(OID_TCP_TASK_OFFLOAD, 0),
  DEF_OID_QUERY(OID_PNP_CAPABILITIES, sizeof(NDIS_PNP_CAPABILITIES)),
  DEF_OID_QUERY(OID_PNP_QUERY_POWER, 0),
  DEF_OID_SET(OID_GEN_PROTOCOL_OPTIONS, 0),
#else
  DEF_OID_SET(OID_GEN_LINK_PARAMETERS, sizeof(NDIS_LINK_PARAMETERS)),
  DEF_OID_QUERYSET(OID_GEN_INTERRUPT_MODERATION, sizeof(NDIS_INTERRUPT_MODERATION_PARAMETERS)),
  DEF_OID_SET(OID_OFFLOAD_ENCAPSULATION, sizeof(NDIS_OFFLOAD_ENCAPSULATION)),
  DEF_OID_QUERY(OID_GEN_STATISTICS, sizeof(NDIS_STATISTICS_INFO)),
#endif  
  {0, "", 0, NULL, NULL}
};

//static NDIS_OID supported_oids[ARRAY_SIZE(xennet_oids)];
#if NTDDI_VERSION < NTDDI_VISTA
NDIS_STATUS
XenNet_SetInformation(
    NDIS_HANDLE adapter_context,
    NDIS_OID oid,
    PVOID information_buffer,
    ULONG information_buffer_length,
    PULONG bytes_read,
    PULONG bytes_needed) {
  NTSTATUS status;
  int i;
  
  FUNCTION_ENTER();
  for (i = 0; xennet_oids[i].oid && xennet_oids[i].oid != oid; i++);

  if (!xennet_oids[i].oid) {
    FUNCTION_MSG("Unsupported OID %08x\n", oid);
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  if (information_buffer_length < xennet_oids[i].min_length) {
    FUNCTION_MSG("%s Set InformationBufferLength %d < min_length %d\n", xennet_oids[i].oid_name, information_buffer_length, xennet_oids[i].min_length);
    *bytes_needed = xennet_oids[i].min_length;
    return NDIS_STATUS_BUFFER_TOO_SHORT;
  }
  if (!xennet_oids[i].set_routine) {
    FUNCTION_MSG("%s Set not supported\n", xennet_oids[i].oid_name);
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  FUNCTION_MSG("%s\n", xennet_oids[i].oid_name);
  status = xennet_oids[i].set_routine(adapter_context, information_buffer, information_buffer_length, bytes_read, bytes_needed);
  FUNCTION_EXIT();
  return status;
}

NDIS_STATUS
XenNet_QueryInformation(
    IN NDIS_HANDLE adapter_context,
    IN NDIS_OID oid,
    IN PVOID information_buffer,
    IN ULONG information_buffer_length,
    OUT PULONG bytes_written,
    OUT PULONG bytes_needed) {
  NTSTATUS status;
  int i;
  
  for (i = 0; xennet_oids[i].oid && xennet_oids[i].oid != oid; i++);

  if (!xennet_oids[i].oid) {
    FUNCTION_MSG("Unsupported OID %08x\n", oid);
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  if (information_buffer_length < xennet_oids[i].min_length) {
    FUNCTION_MSG("%s Query InformationBufferLength %d < min_length %d\n", xennet_oids[i].oid_name, information_buffer_length, xennet_oids[i].min_length);
    *bytes_needed = xennet_oids[i].min_length;
    return NDIS_STATUS_BUFFER_TOO_SHORT;
  }
  if (!xennet_oids[i].query_routine) {
    FUNCTION_MSG("%s Query not supported\n", xennet_oids[i].oid_name);
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  //FUNCTION_MSG("%s\n", xennet_oids[i].oid_name);
  status = xennet_oids[i].query_routine(adapter_context, information_buffer, information_buffer_length, bytes_written, bytes_needed);
  return status;
}

#else
NDIS_STATUS
XenNet_OidRequest(NDIS_HANDLE adapter_context, PNDIS_OID_REQUEST oid_request)
{
  NTSTATUS status;
  int i;
  NDIS_OID oid;
  
  //FUNCTION_ENTER();
  switch(oid_request->RequestType)
  {
  case NdisRequestQueryInformation:
    //FUNCTION_MSG("RequestType = NdisRequestQueryInformation\n");
    oid = oid_request->DATA.QUERY_INFORMATION.Oid;
    break;
  case NdisRequestSetInformation:
    //FUNCTION_MSG("RequestType = NdisRequestSetInformation\n");
    oid = oid_request->DATA.SET_INFORMATION.Oid;
    break;
  case NdisRequestQueryStatistics:
    //FUNCTION_MSG("RequestType = NdisRequestQueryStatistics\n");
    oid = oid_request->DATA.QUERY_INFORMATION.Oid;
    break;
  default:
    //FUNCTION_MSG("RequestType = NdisRequestQuery%d\n", oid_request->RequestType);
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  for (i = 0; xennet_oids[i].oid && xennet_oids[i].oid != oid; i++);

  if (!xennet_oids[i].oid) {
    FUNCTION_MSG("Unsupported OID %08x\n", oid);
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  //FUNCTION_MSG("Oid = %s\n", xennet_oids[i].oid_name);
  switch(oid_request->RequestType)
  {
  case NdisRequestQueryInformation:
  case NdisRequestQueryStatistics:
    if (oid_request->DATA.QUERY_INFORMATION.InformationBufferLength < xennet_oids[i].min_length) {
      FUNCTION_MSG("InformationBufferLength %d < min_length %d\n", oid_request->DATA.QUERY_INFORMATION.InformationBufferLength, xennet_oids[i].min_length);
      oid_request->DATA.QUERY_INFORMATION.BytesNeeded = xennet_oids[i].min_length;
      return NDIS_STATUS_BUFFER_TOO_SHORT;
    }
    if (!xennet_oids[i].query_routine) {
      //FUNCTION_MSG("Operation not supported\n");
      return NDIS_STATUS_NOT_SUPPORTED;
    }
    status = xennet_oids[i].query_routine(adapter_context, oid_request->DATA.QUERY_INFORMATION.InformationBuffer, oid_request->DATA.QUERY_INFORMATION.InformationBufferLength, (PULONG)&oid_request->DATA.QUERY_INFORMATION.BytesWritten, (PULONG)&oid_request->DATA.QUERY_INFORMATION.BytesNeeded);
    break;
  case NdisRequestSetInformation:
    if (oid_request->DATA.SET_INFORMATION.InformationBufferLength < xennet_oids[i].min_length) {
      FUNCTION_MSG("InformationBufferLength %d < min_length %d\n", oid_request->DATA.SET_INFORMATION.InformationBufferLength, xennet_oids[i].min_length);
      oid_request->DATA.SET_INFORMATION.BytesNeeded = xennet_oids[i].min_length;
      return NDIS_STATUS_BUFFER_TOO_SHORT;
    }
    if (!xennet_oids[i].set_routine) {
      //FUNCTION_MSG("Operation not supported\n");
      return NDIS_STATUS_NOT_SUPPORTED;
    }
    status = xennet_oids[i].set_routine(adapter_context, oid_request->DATA.SET_INFORMATION.InformationBuffer, oid_request->DATA.SET_INFORMATION.InformationBufferLength, (PULONG)&oid_request->DATA.SET_INFORMATION.BytesRead, (PULONG)&oid_request->DATA.SET_INFORMATION.BytesNeeded);
    break;
  default:
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  //FUNCTION_EXIT();
  return status;
}

VOID
XenNet_CancelOidRequest(NDIS_HANDLE adapter_context, PVOID request_id)
{
  UNREFERENCED_PARAMETER(adapter_context);
  UNREFERENCED_PARAMETER(request_id);
  FUNCTION_ENTER();
  FUNCTION_EXIT();
}
#endif