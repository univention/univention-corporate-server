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

#include "xennet6.h"

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
XenNet_Query##oid(NDIS_HANDLE context, PNDIS_OID_REQUEST request) \
{ \
  struct xennet_info *xi = context; \
  UNREFERENCED_PARAMETER(xi); \
  if (request->DATA.QUERY_INFORMATION.InformationBufferLength < length) \
  { \
    request->DATA.QUERY_INFORMATION.BytesNeeded = length; \
    return NDIS_STATUS_BUFFER_TOO_SHORT; \
  } \
  request->DATA.QUERY_INFORMATION.BytesWritten = length; \
  NdisMoveMemory(request->DATA.QUERY_INFORMATION.InformationBuffer, value, length); \
  return STATUS_SUCCESS; \
}

#define DEF_OID_QUERY_ULONG_ROUTINE(oid, value) \
NDIS_STATUS \
XenNet_Query##oid(NDIS_HANDLE context, PNDIS_OID_REQUEST request) \
{ \
  struct xennet_info *xi = context; \
  UNREFERENCED_PARAMETER(xi); \
  request->DATA.QUERY_INFORMATION.BytesWritten = sizeof(ULONG); \
  *(ULONG *)request->DATA.QUERY_INFORMATION.InformationBuffer = value; \
  return STATUS_SUCCESS; \
}

#define DEF_OID_QUERY_STAT_ROUTINE(oid, value) \
NDIS_STATUS \
XenNet_Query##oid(NDIS_HANDLE context, PNDIS_OID_REQUEST request) \
{ \
  struct xennet_info *xi = context; \
  UNREFERENCED_PARAMETER(xi); \
  if (request->DATA.QUERY_INFORMATION.InformationBufferLength >= 8) \
  { \
    request->DATA.QUERY_INFORMATION.BytesWritten = sizeof(ULONG64); \
    *(ULONG64 *)request->DATA.QUERY_INFORMATION.InformationBuffer = (value); \
  } \
  else if (request->DATA.QUERY_INFORMATION.InformationBufferLength >= 4) \
  { \
    request->DATA.QUERY_INFORMATION.BytesWritten = sizeof(ULONG); \
    request->DATA.QUERY_INFORMATION.BytesNeeded = sizeof(ULONG64); \
    *(ULONG *)request->DATA.QUERY_INFORMATION.InformationBuffer = (ULONG)(value); \
  } \
  else \
  { \
    request->DATA.QUERY_INFORMATION.BytesNeeded = sizeof(ULONG64); \
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
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_HARDWARE_STATUS, xi->connected?NdisHardwareStatusReady:NdisHardwareStatusInitializing)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_VENDOR_ID, 0xFFFFFF) // Not guaranteed to be XENSOURCE_MAC_HDR;
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_VENDOR_DRIVER_VERSION, VENDOR_DRIVER_VERSION)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_MEDIA_SUPPORTED, NdisMedium802_3)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_MEDIA_IN_USE, NdisMedium802_3)
DEF_OID_QUERY_ULONG_ROUTINE(OID_GEN_MAXIMUM_LOOKAHEAD, MAX_LOOKAHEAD_LENGTH)

DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_XMIT_OK, xi->stats.ifHCOutUcastPkts + xi->stats.ifHCOutMulticastPkts + xi->stats.ifHCOutBroadcastPkts)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_XMIT_ERROR, xi->stats.ifOutErrors)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_RCV_OK, xi->stats.ifHCInUcastPkts + xi->stats.ifHCInMulticastPkts + xi->stats.ifHCInBroadcastPkts)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_RCV_ERROR, xi->stats.ifInErrors)
DEF_OID_QUERY_STAT_ROUTINE(OID_GEN_RCV_NO_BUFFER, xi->stats.ifInDiscards)
DEF_OID_QUERY_STAT_ROUTINE(OID_802_3_RCV_ERROR_ALIGNMENT, 0)
DEF_OID_QUERY_STAT_ROUTINE(OID_802_3_XMIT_ONE_COLLISION, 0)
DEF_OID_QUERY_STAT_ROUTINE(OID_802_3_XMIT_MORE_COLLISIONS, 0)

DEF_OID_QUERY_ROUTINE(OID_GEN_VENDOR_DESCRIPTION, XN_VENDOR_DESC, sizeof(XN_VENDOR_DESC))

DEF_OID_QUERY_ROUTINE(OID_802_3_PERMANENT_ADDRESS, xi->perm_mac_addr, ETH_ALEN)
DEF_OID_QUERY_ROUTINE(OID_802_3_CURRENT_ADDRESS, xi->curr_mac_addr, ETH_ALEN)

DEF_OID_QUERY_ROUTINE(OID_802_3_MULTICAST_LIST, xi->multicast_list, xi->multicast_list_size * 6)

NDIS_STATUS
XenNet_SetOID_802_3_MULTICAST_LIST(NDIS_HANDLE context, PNDIS_OID_REQUEST request)
{
  struct xennet_info *xi = context;
  UCHAR *multicast_list;
  int i;

  if (request->DATA.SET_INFORMATION.InformationBufferLength > MULTICAST_LIST_MAX_SIZE * 6)
  {
    return NDIS_STATUS_MULTICAST_FULL;
  }
  
  if (request->DATA.SET_INFORMATION.InformationBufferLength % 6 != 0)
  {
    return NDIS_STATUS_MULTICAST_FULL;
  }
  multicast_list = request->DATA.SET_INFORMATION.InformationBuffer;
  for (i = 0; i < (int)request->DATA.SET_INFORMATION.InformationBufferLength / 6; i++)
  {
    if (!(multicast_list[i * 6 + 0] & 0x01))
    {
      FUNCTION_MSG("Address %d (%02x:%02x:%02x:%02x:%02x:%02x) is not a multicast address\n", i,
        (ULONG)multicast_list[i * 6 + 0], (ULONG)multicast_list[i * 6 + 1], 
        (ULONG)multicast_list[i * 6 + 2], (ULONG)multicast_list[i * 6 + 3], 
        (ULONG)multicast_list[i * 6 + 4], (ULONG)multicast_list[i * 6 + 5]);
      /* the docs say that we should return NDIS_STATUS_MULTICAST_FULL if we get an invalid multicast address but I'm not sure if that's the case... */
    }
  }
  memcpy(xi->multicast_list, multicast_list, request->DATA.SET_INFORMATION.InformationBufferLength);
  xi->multicast_list_size = request->DATA.SET_INFORMATION.InformationBufferLength / 6;
  return NDIS_STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_GEN_CURRENT_PACKET_FILTER(NDIS_HANDLE context, PNDIS_OID_REQUEST request)
{
  struct xennet_info *xi = context;
  PULONG data = request->DATA.SET_INFORMATION.InformationBuffer;
  
  request->DATA.SET_INFORMATION.BytesNeeded = sizeof(ULONG64);
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
  if (*data & ~SUPPORTED_PACKET_FILTERS)
  {
    FUNCTION_MSG("returning NDIS_STATUS_NOT_SUPPORTED\n");
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  xi->packet_filter = *(ULONG *)data;
  request->DATA.SET_INFORMATION.BytesRead = sizeof(ULONG);
  return NDIS_STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_GEN_CURRENT_LOOKAHEAD(NDIS_HANDLE context, PNDIS_OID_REQUEST request)
{
  struct xennet_info *xi = context;
  PULONG data = request->DATA.QUERY_INFORMATION.InformationBuffer;
  xi->current_lookahead = *(ULONG *)data;
  FUNCTION_MSG("Set OID_GEN_CURRENT_LOOKAHEAD %d (%p)\n", xi->current_lookahead, xi);
  return NDIS_STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_GEN_LINK_PARAMETERS(NDIS_HANDLE context, PNDIS_OID_REQUEST request)
{
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(request);
  return STATUS_NOT_SUPPORTED;
}

NDIS_STATUS
XenNet_QueryOID_GEN_INTERRUPT_MODERATION(NDIS_HANDLE context, PNDIS_OID_REQUEST request)
{
  PNDIS_INTERRUPT_MODERATION_PARAMETERS nimp;
  UNREFERENCED_PARAMETER(context);
  nimp = (PNDIS_INTERRUPT_MODERATION_PARAMETERS)request->DATA.QUERY_INFORMATION.InformationBuffer;
  nimp->Header.Type = NDIS_OBJECT_TYPE_DEFAULT;
  nimp->Header.Revision = NDIS_INTERRUPT_MODERATION_PARAMETERS_REVISION_1;
  nimp->Header.Size = NDIS_SIZEOF_INTERRUPT_MODERATION_PARAMETERS_REVISION_1;
  nimp->Flags = 0;
  nimp->InterruptModeration = NdisInterruptModerationNotSupported;
  request->DATA.SET_INFORMATION.BytesRead = sizeof(NDIS_INTERRUPT_MODERATION_PARAMETERS);
  return STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_GEN_INTERRUPT_MODERATION(NDIS_HANDLE context, PNDIS_OID_REQUEST request)
{
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(request);
  return STATUS_NOT_SUPPORTED;
}

NDIS_STATUS
XenNet_QueryOID_GEN_STATISTICS(NDIS_HANDLE context, PNDIS_OID_REQUEST request)
{
  struct xennet_info *xi = context;

  NdisMoveMemory(request->DATA.QUERY_INFORMATION.InformationBuffer, &xi->stats, sizeof(NDIS_STATISTICS_INFO));
  request->DATA.SET_INFORMATION.BytesRead = sizeof(NDIS_STATISTICS_INFO);
  return STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_PNP_SET_POWER(NDIS_HANDLE context, PNDIS_OID_REQUEST request)
{
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(request);
  return STATUS_NOT_SUPPORTED;
}

NDIS_STATUS
XenNet_SetOID_GEN_NETWORK_LAYER_ADDRESSES(NDIS_HANDLE context, PNDIS_OID_REQUEST request)
{
  PNETWORK_ADDRESS_LIST nal = request->DATA.QUERY_INFORMATION.InformationBuffer;
  PNETWORK_ADDRESS na;
  PNETWORK_ADDRESS_IP ip;
  int i;
  
  UNREFERENCED_PARAMETER(context);
  FUNCTION_MSG("AddressType = %d\n", nal->AddressType);
  FUNCTION_MSG("AddressCount = %d\n", nal->AddressCount);
  if (nal->AddressCount == 0)
  {
    // remove addresses of AddressType type
  }
  else
  {
    na = nal->Address;
    for (i = 0; i < nal->AddressCount; i++)
    {
      if ((ULONG_PTR)na - (ULONG_PTR)nal + FIELD_OFFSET(NETWORK_ADDRESS, Address) + na->AddressLength > request->DATA.QUERY_INFORMATION.InformationBufferLength)
      {
        FUNCTION_MSG("Out of bounds\n");
        return NDIS_STATUS_INVALID_DATA;
      }
      switch(na->AddressType)
      {
      case NDIS_PROTOCOL_ID_TCP_IP:
        FUNCTION_MSG("Address[%d].Type = NDIS_PROTOCOL_ID_TCP_IP\n", i);
        FUNCTION_MSG("Address[%d].Length = %d\n", i, na->AddressLength);
        if (na->AddressLength != NETWORK_ADDRESS_LENGTH_IP)
        {
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
XenNet_SetOID_GEN_MACHINE_NAME(NDIS_HANDLE context, PNDIS_OID_REQUEST request)
{
  UNICODE_STRING name;
  UNREFERENCED_PARAMETER(context);
  
  name.Length = (USHORT)request->DATA.QUERY_INFORMATION.InformationBufferLength;
  name.MaximumLength = (USHORT)request->DATA.QUERY_INFORMATION.InformationBufferLength;
  name.Buffer = request->DATA.QUERY_INFORMATION.InformationBuffer;
  FUNCTION_MSG("name = %wZ\n", &name);
  return NDIS_STATUS_SUCCESS;
}

NDIS_STATUS
XenNet_SetOID_OFFLOAD_ENCAPSULATION(NDIS_HANDLE context, PNDIS_OID_REQUEST request)
{
  struct xennet_info *xi = context;
  /* mostly assume that NDIS vets the settings for us */
  PNDIS_OFFLOAD_ENCAPSULATION noe = (PNDIS_OFFLOAD_ENCAPSULATION)request->DATA.SET_INFORMATION.InformationBuffer;
  if (noe->IPv4.EncapsulationType != NDIS_ENCAPSULATION_IEEE_802_3)
  {
    FUNCTION_MSG("Unknown Encapsulation Type %d\n", noe->IPv4.EncapsulationType);
    return NDIS_STATUS_NOT_SUPPORTED;
  }
    
  switch(noe->IPv4.Enabled)
  {
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
  switch(noe->IPv6.Enabled)
  {
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
  FUNCTION_MSG(" IPv6.HeaderSize = %d\n", noe->IPv6.HeaderSize);
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
  DEF_OID_SET(OID_GEN_LINK_PARAMETERS, sizeof(NDIS_LINK_PARAMETERS)),
  DEF_OID_QUERYSET(OID_GEN_INTERRUPT_MODERATION, sizeof(NDIS_INTERRUPT_MODERATION_PARAMETERS)),
  
  DEF_OID_QUERY_ULONG(OID_GEN_MAXIMUM_SEND_PACKETS),
  DEF_OID_QUERY_ULONG(OID_GEN_MEDIA_SUPPORTED),
  DEF_OID_QUERY_ULONG(OID_GEN_MEDIA_IN_USE),
  DEF_OID_QUERY_ULONG(OID_GEN_MAXIMUM_LOOKAHEAD),

  /* general optional */
  DEF_OID_SET(OID_GEN_NETWORK_LAYER_ADDRESSES, FIELD_OFFSET(NETWORK_ADDRESS_LIST, Address)),
  DEF_OID_SET(OID_GEN_MACHINE_NAME, 0),
  DEF_OID_SET(OID_OFFLOAD_ENCAPSULATION, sizeof(NDIS_OFFLOAD_ENCAPSULATION)),

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
  DEF_OID_QUERY(OID_GEN_STATISTICS, sizeof(NDIS_STATISTICS_INFO)),

  /* media-specific */
  DEF_OID_QUERY(OID_802_3_PERMANENT_ADDRESS, 6),
  DEF_OID_QUERY(OID_802_3_CURRENT_ADDRESS, 6),
  DEF_OID_QUERYSET(OID_802_3_MULTICAST_LIST, 0),
  DEF_OID_QUERY_ULONG(OID_802_3_MAXIMUM_LIST_SIZE),
  
  {0, "", 0, NULL, NULL}
};

//static NDIS_OID supported_oids[ARRAY_SIZE(xennet_oids)];

NDIS_STATUS
XenNet_OidRequest(NDIS_HANDLE adapter_context, PNDIS_OID_REQUEST oid_request)
{
  NTSTATUS status;
  int i;
  NDIS_OID oid;
  MINIPORT_OID_REQUEST *routine;
  
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

  if (!xennet_oids[i].oid)
  {
    FUNCTION_MSG("Unsupported OID %08x\n", oid);
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  //FUNCTION_MSG("Oid = %s\n", xennet_oids[i].oid_name);
  routine = NULL;
  switch(oid_request->RequestType)
  {
  case NdisRequestQueryInformation:
  case NdisRequestQueryStatistics:
    if (oid_request->DATA.QUERY_INFORMATION.InformationBufferLength < xennet_oids[i].min_length)
    {
      FUNCTION_MSG("InformationBufferLength %d < min_length %d\n", oid_request->DATA.QUERY_INFORMATION.InformationBufferLength < xennet_oids[i].min_length);
      oid_request->DATA.QUERY_INFORMATION.BytesNeeded = xennet_oids[i].min_length;
      return NDIS_STATUS_BUFFER_TOO_SHORT;
    }
    routine =  xennet_oids[i].query_routine;
    break;
  case NdisRequestSetInformation:
    if (oid_request->DATA.SET_INFORMATION.InformationBufferLength < xennet_oids[i].min_length)
    {
      FUNCTION_MSG("InformationBufferLength %d < min_length %d\n", oid_request->DATA.SET_INFORMATION.InformationBufferLength < xennet_oids[i].min_length);
      oid_request->DATA.SET_INFORMATION.BytesNeeded = xennet_oids[i].min_length;
      return NDIS_STATUS_BUFFER_TOO_SHORT;
    }
    routine =  xennet_oids[i].set_routine;
    break;
  }
  if (!routine)
  {
    //FUNCTION_MSG("Operation not supported\n");
    return NDIS_STATUS_NOT_SUPPORTED;
  }
  status = routine(adapter_context, oid_request);
  //FUNCTION_MSG("status = %08x\n", status);
  
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
