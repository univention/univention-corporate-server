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


static USHORT
get_id_from_freelist(struct xennet_info *xi)
{
  XN_ASSERT(xi->tx_id_free);
  xi->tx_id_free--;

  return xi->tx_id_list[xi->tx_id_free];
}

static VOID
put_id_on_freelist(struct xennet_info *xi, USHORT id)
{
  XN_ASSERT(id >= 0 && id < NET_TX_RING_SIZE);
  xi->tx_id_list[xi->tx_id_free] = id;
  xi->tx_id_free++;
}

#define SWAP_USHORT(x) (USHORT)((((x & 0xFF) << 8)|((x >> 8) & 0xFF)))

static __forceinline struct netif_tx_request *
XenNet_PutCbOnRing(struct xennet_info *xi, PVOID coalesce_buf, ULONG length, grant_ref_t gref)
{
  struct netif_tx_request *tx;
  tx = RING_GET_REQUEST(&xi->tx_ring, xi->tx_ring.req_prod_pvt);
  xi->tx_ring.req_prod_pvt++;
  XN_ASSERT(xi->tx_ring_free);
  xi->tx_ring_free--;
  tx->id = get_id_from_freelist(xi);
  XN_ASSERT(xi->tx_shadows[tx->id].gref == INVALID_GRANT_REF);
  XN_ASSERT(!xi->tx_shadows[tx->id].cb);
  xi->tx_shadows[tx->id].cb = coalesce_buf;
  tx->gref = XnGrantAccess(xi->handle, (ULONG)(MmGetPhysicalAddress(coalesce_buf).QuadPart >> PAGE_SHIFT), FALSE, gref, (ULONG)'XNTX');
  xi->tx_shadows[tx->id].gref = tx->gref;
  tx->offset = 0;
  tx->size = (USHORT)length;
  XN_ASSERT(tx->offset + tx->size <= PAGE_SIZE);
  XN_ASSERT(tx->size);
  return tx;
}

#if 0
static VOID dump_packet_data(PNDIS_PACKET packet, PCHAR header) {
  UINT mdl_count;
  PMDL first_mdl;
  UINT total_length;
  
  NdisQueryPacket(packet, NULL, (PUINT)&mdl_count, &first_mdl, (PUINT)&total_length);
  FUNCTION_MSG("%s mdl_count = %d, first_mdl = %p, total_length = %d\n", header, mdl_count, first_mdl, total_length);
}
#endif
  
/* Called at DISPATCH_LEVEL with tx_lock held */
/*
 * Send one NDIS_PACKET. This may involve multiple entries on TX ring.
 */
#if NTDDI_VERSION < NTDDI_VISTA
static BOOLEAN
XenNet_HWSendPacket(struct xennet_info *xi, PNDIS_PACKET packet) {
#else
static BOOLEAN
XenNet_HWSendPacket(struct xennet_info *xi, PNET_BUFFER packet) {
#endif
  struct netif_tx_request *tx0 = NULL;
  struct netif_tx_request *txN = NULL;
  struct netif_extra_info *ei = NULL;
  ULONG mss = 0;
  #if NTDDI_VERSION < NTDDI_VISTA
  PNDIS_TCP_IP_CHECKSUM_PACKET_INFO csum_info;
  UINT mdl_count;
  #else
  NDIS_TCP_LARGE_SEND_OFFLOAD_NET_BUFFER_LIST_INFO lso_info;
  NDIS_TCP_IP_CHECKSUM_NET_BUFFER_LIST_INFO csum_info;
  #endif
  uint16_t flags = NETTXF_more_data;
  packet_info_t pi;
  BOOLEAN ndis_lso = FALSE;
  BOOLEAN xen_gso = FALSE;
  ULONG remaining;
  ULONG frags = 0;
  BOOLEAN coalesce_required = FALSE;
  PVOID coalesce_buf;
  ULONG coalesce_remaining = 0;
  grant_ref_t gref;
  ULONG tx_length = 0;
  
  gref = XnAllocateGrant(xi->handle, (ULONG)'XNTX');
  if (gref == INVALID_GRANT_REF)
  {
    FUNCTION_MSG("out of grefs\n");
    return FALSE;
  }
  coalesce_buf = NdisAllocateFromNPagedLookasideList(&xi->tx_lookaside_list);
  if (!coalesce_buf)
  {
    XnFreeGrant(xi->handle, gref, (ULONG)'XNTX');
    FUNCTION_MSG("out of memory\n");
    return FALSE;
  }
  XenNet_ClearPacketInfo(&pi);
  #if NTDDI_VERSION < NTDDI_VISTA
  NdisQueryPacket(packet, NULL, (PUINT)&mdl_count, &pi.first_mdl, (PUINT)&pi.total_length);
  pi.curr_mdl = pi.first_mdl;
  #else
  /* create a new MDL over the data portion of the first MDL in the packet... it's just easier this way */
  IoBuildPartialMdl(packet->CurrentMdl,
    &pi.first_mdl_storage,
    (PUCHAR)MmGetMdlVirtualAddress(packet->CurrentMdl) + packet->CurrentMdlOffset,
    MmGetMdlByteCount(packet->CurrentMdl) - packet->CurrentMdlOffset);
  pi.total_length = packet->DataLength;
  pi.first_mdl_storage.Next = packet->CurrentMdl->Next;
  pi.first_mdl = pi.curr_mdl = &pi.first_mdl_storage;
  #endif
  pi.first_mdl_offset = pi.curr_mdl_offset = 0;
  remaining = min(pi.total_length, PAGE_SIZE);
  while (remaining) { /* this much gets put in the header */
    ULONG length = XenNet_QueryData(&pi, remaining);
    remaining -= length;
    XenNet_EatData(&pi, length);
  }
  frags++;
  if (pi.total_length > PAGE_SIZE) { /* these are the frags we care about */
    remaining = pi.total_length - PAGE_SIZE;
    while (remaining) {
      ULONG length = XenNet_QueryData(&pi, PAGE_SIZE);
      if (length != 0) {
        frags++;
        if (frags > LINUX_MAX_SG_ELEMENTS)
          break; /* worst case there could be hundreds of fragments - leave the loop now */
      }
      remaining -= length;
      XenNet_EatData(&pi, length);
    }
  }
  if (frags > LINUX_MAX_SG_ELEMENTS) {
    frags = LINUX_MAX_SG_ELEMENTS;
    coalesce_required = TRUE;
  }

  /* if we have enough space on the ring then we have enough id's so no need to check for that */
  if (xi->tx_ring_free < frags + 1) {
    XnFreeGrant(xi->handle, gref, (ULONG)'XNTX');
    NdisFreeToNPagedLookasideList(&xi->tx_lookaside_list, coalesce_buf);
    //FUNCTION_MSG("Full on send - ring full\n");
    return FALSE;
  }
  XenNet_ParsePacketHeader(&pi, coalesce_buf, PAGE_SIZE);
  remaining = pi.total_length - pi.header_length;
  if (pi.ip_version == 4 && pi.ip_proto == 6 && pi.ip4_length == 0) {
    *((PUSHORT)(pi.header + 0x10)) = GET_NET_USHORT((USHORT)pi.total_length - XN_HDR_SIZE);
  }

  #if NTDDI_VERSION < NTDDI_VISTA
  if (NDIS_GET_PACKET_PROTOCOL_TYPE(packet) == NDIS_PROTOCOL_ID_TCP_IP) {
    csum_info = (PNDIS_TCP_IP_CHECKSUM_PACKET_INFO)&NDIS_PER_PACKET_INFO_FROM_PACKET(
      packet, TcpIpChecksumPacketInfo);
    if (csum_info->Transmit.NdisPacketChecksumV4) {
      if (csum_info->Transmit.NdisPacketTcpChecksum) {
        flags |= NETTXF_csum_blank | NETTXF_data_validated;
      } else if (csum_info->Transmit.NdisPacketUdpChecksum) {
        flags |= NETTXF_csum_blank | NETTXF_data_validated;
      }
    }
  }
  #else
  csum_info.Value = NET_BUFFER_LIST_INFO(NB_NBL(packet), TcpIpChecksumNetBufferListInfo);
  if (csum_info.Transmit.IsIPv4) {
    if (csum_info.Transmit.TcpChecksum) {
      flags |= NETTXF_csum_blank | NETTXF_data_validated;
    } else if (csum_info.Transmit.UdpChecksum) {
      flags |= NETTXF_csum_blank | NETTXF_data_validated;
    }
  } else if (csum_info.Transmit.IsIPv6) {
    FUNCTION_MSG("Transmit.IsIPv6 not supported\n");
  }
  #endif
  
  #if NTDDI_VERSION < NTDDI_VISTA
  mss = PtrToUlong(NDIS_PER_PACKET_INFO_FROM_PACKET(packet, TcpLargeSendPacketInfo));
  #else
  lso_info.Value = NET_BUFFER_LIST_INFO(NB_NBL(packet), TcpLargeSendNetBufferListInfo);
  switch (lso_info.Transmit.Type) {
  case NDIS_TCP_LARGE_SEND_OFFLOAD_V1_TYPE:
    mss = lso_info.LsoV1Transmit.MSS;
    /* should make use of TcpHeaderOffset too... maybe just assert if it's not what we expect */
    break;
  case NDIS_TCP_LARGE_SEND_OFFLOAD_V2_TYPE:
    mss = lso_info.LsoV2Transmit.MSS;
    /* should make use of TcpHeaderOffset too... maybe just assert if it's not what we expect */
    break;
  }
  #endif
  if (mss && pi.parse_result == PARSE_OK) {
    ndis_lso = TRUE;
  }

  if (ndis_lso) {    
    ULONG csum;
    flags |= NETTXF_csum_blank | NETTXF_data_validated; /* these may be implied but not specified when lso is used*/
    if (pi.tcp_length >= mss) {
      flags |= NETTXF_extra_info;
      xen_gso = TRUE;
    }
    /* Adjust pseudoheader checksum to be what Linux expects (remove the tcp_length) */
    csum = ~RtlUshortByteSwap(*(PUSHORT)&pi.header[XN_HDR_SIZE + pi.ip4_header_length + 16]);
    csum -= (pi.ip4_length - pi.ip4_header_length);
    while (csum & 0xFFFF0000)
      csum = (csum & 0xFFFF) + (csum >> 16);
    *(PUSHORT)&pi.header[XN_HDR_SIZE + pi.ip4_header_length + 16] = ~RtlUshortByteSwap((USHORT)csum);
  }
/*
* See io/netif.h. Must put (A) 1st request, then (B) optional extra_info, then
* (C) rest of requests on the ring. Only (A) has csum flags.
*/

  /* (A) */
  tx0 = XenNet_PutCbOnRing(xi, coalesce_buf, pi.header_length, gref);
  XN_ASSERT(tx0); /* this will never happen */
  tx0->flags = flags;
  tx_length += pi.header_length;

  /* lso implies IpHeaderChecksum */
  #if NTDDI_VERSION < NTDDI_VISTA
  if (ndis_lso) {
    XenNet_SumIpHeader(coalesce_buf, pi.ip4_header_length);
  }
  #else
  if (ndis_lso || csum_info.Transmit.IpHeaderChecksum) {
    XenNet_SumIpHeader(coalesce_buf, pi.ip4_header_length);
  }
  #endif
  txN = tx0;

  /* (B) */
  if (xen_gso) {
    XN_ASSERT(flags & NETTXF_extra_info);
    ei = (struct netif_extra_info *)RING_GET_REQUEST(&xi->tx_ring, xi->tx_ring.req_prod_pvt);
    //KdPrint((__DRIVER_NAME "     pos = %d\n", xi->tx_ring.req_prod_pvt));
    xi->tx_ring.req_prod_pvt++;
    XN_ASSERT(xi->tx_ring_free);
    xi->tx_ring_free--;
    ei->type = XEN_NETIF_EXTRA_TYPE_GSO;
    ei->flags = 0;
    ei->u.gso.size = (USHORT)mss;
    ei->u.gso.type = XEN_NETIF_GSO_TYPE_TCPV4;
    ei->u.gso.pad = 0;
    ei->u.gso.features = 0;
  }

  XN_ASSERT(xi->current_sg_supported || !remaining);
  
  /* (C) - only if data is remaining */
  coalesce_buf = NULL;
  while (remaining > 0) {
    ULONG length;
    PFN_NUMBER pfn;

    XN_ASSERT(pi.curr_mdl);
    if (coalesce_required) {
      PVOID va;
      if (!coalesce_buf) {
        gref = XnAllocateGrant(xi->handle, (ULONG)'XNTX');
        if (gref == INVALID_GRANT_REF) {
          FUNCTION_MSG("out of grefs - partial send\n");
          break;
        }
        coalesce_buf = NdisAllocateFromNPagedLookasideList(&xi->tx_lookaside_list);
        if (!coalesce_buf) {
          XnFreeGrant(xi->handle, gref, (ULONG)'XNTX');
          FUNCTION_MSG("out of memory - partial send\n");
          break;
        }
        coalesce_remaining = min(PAGE_SIZE, remaining);
      }
      length = XenNet_QueryData(&pi, coalesce_remaining);
      va = NdisBufferVirtualAddressSafe(pi.curr_mdl, LowPagePriority);
      if (!va) {
        FUNCTION_MSG("failed to map buffer va - partial send\n");
        coalesce_remaining = 0;
        remaining -= min(PAGE_SIZE, remaining);
        NdisFreeToNPagedLookasideList(&xi->tx_lookaside_list, coalesce_buf);
      } else {
        memcpy((PUCHAR)coalesce_buf + min(PAGE_SIZE, remaining) - coalesce_remaining, (PUCHAR)va + pi.curr_mdl_offset, length);
        coalesce_remaining -= length;
      }
    } else {
      length = XenNet_QueryData(&pi, PAGE_SIZE);
    }
    if (!length || coalesce_remaining) { /* sometimes there are zero length buffers... */
      XenNet_EatData(&pi, length); /* do this so we actually move to the next buffer */
      continue;
    }

    if (coalesce_buf) {
      if (remaining) {
        txN = XenNet_PutCbOnRing(xi, coalesce_buf, min(PAGE_SIZE, remaining), gref);
        XN_ASSERT(txN);
        coalesce_buf = NULL;
        tx_length += min(PAGE_SIZE, remaining);
        remaining -= min(PAGE_SIZE, remaining);
      }
    } else {
      ULONG offset;
      
      gref = XnAllocateGrant(xi->handle, (ULONG)'XNTX');
      if (gref == INVALID_GRANT_REF) {
        FUNCTION_MSG("out of grefs - partial send\n");
        break;
      }
      txN = RING_GET_REQUEST(&xi->tx_ring, xi->tx_ring.req_prod_pvt);
      xi->tx_ring.req_prod_pvt++;
      XN_ASSERT(xi->tx_ring_free);
      xi->tx_ring_free--;
      txN->id = get_id_from_freelist(xi);
      XN_ASSERT(xi->tx_shadows[txN->id].gref == INVALID_GRANT_REF);
      XN_ASSERT(!xi->tx_shadows[txN->id].cb);
      offset = MmGetMdlByteOffset(pi.curr_mdl) + pi.curr_mdl_offset;
      pfn = MmGetMdlPfnArray(pi.curr_mdl)[offset >> PAGE_SHIFT];
      txN->offset = (USHORT)offset & (PAGE_SIZE - 1);
      txN->gref = XnGrantAccess(xi->handle, (ULONG)pfn, FALSE, gref, (ULONG)'XNTX');
      xi->tx_shadows[txN->id].gref = txN->gref;
      //ASSERT(sg->Elements[sg_element].Length > sg_offset);
      txN->size = (USHORT)length;
      XN_ASSERT(txN->offset + txN->size <= PAGE_SIZE);
      XN_ASSERT(txN->size);
      XN_ASSERT(txN->gref != INVALID_GRANT_REF);
      remaining -= length;
      tx_length += length;
    }
    tx0->size = tx0->size + txN->size;
    txN->flags = NETTXF_more_data;
    XenNet_EatData(&pi, length);
  }
  txN->flags &= ~NETTXF_more_data;
  XN_ASSERT(tx0->size == pi.total_length);
  XN_ASSERT(!xi->tx_shadows[txN->id].packet);
  xi->tx_shadows[txN->id].packet = packet;

  #if NTDDI_VERSION < NTDDI_VISTA
  if (ndis_lso) {
    NDIS_PER_PACKET_INFO_FROM_PACKET(packet, TcpLargeSendPacketInfo) = UlongToPtr(tx_length - MAX_ETH_HEADER_LENGTH - pi.ip4_header_length - pi.tcp_header_length);
  }
  #else
  switch (lso_info.Transmit.Type) {
  case NDIS_TCP_LARGE_SEND_OFFLOAD_V1_TYPE:
    lso_info.LsoV1TransmitComplete.TcpPayload = tx_length - MAX_ETH_HEADER_LENGTH - pi.ip4_header_length - pi.tcp_header_length;
    break;
  case NDIS_TCP_LARGE_SEND_OFFLOAD_V2_TYPE:
    break;
  }
  #endif

  xi->tx_outstanding++;
  return TRUE;
}

/* Called at DISPATCH_LEVEL with tx_lock held */
static VOID
XenNet_SendQueuedPackets(struct xennet_info *xi)
{
  PLIST_ENTRY entry;
  #if NTDDI_VERSION < NTDDI_VISTA
  PNDIS_PACKET packet;
  #else
  PNET_BUFFER packet;
  #endif
  int notify;

  if (xi->device_state != DEVICE_STATE_ACTIVE)
    return;

  while (!IsListEmpty(&xi->tx_waiting_pkt_list)) {
    entry = RemoveHeadList(&xi->tx_waiting_pkt_list);
    #if NTDDI_VERSION < NTDDI_VISTA
    packet = CONTAINING_RECORD(entry, NDIS_PACKET, PACKET_LIST_ENTRY_FIELD);
    #else
    packet = CONTAINING_RECORD(entry, NET_BUFFER, NB_LIST_ENTRY_FIELD);
    #endif    
    if (!XenNet_HWSendPacket(xi, packet)) {
      InsertHeadList(&xi->tx_waiting_pkt_list, entry);
      break;
    }
  }

  RING_PUSH_REQUESTS_AND_CHECK_NOTIFY(&xi->tx_ring, notify);
  if (notify) {
    XnNotify(xi->handle, xi->event_channel);
  }
}

// Called at DISPATCH_LEVEL
VOID
XenNet_TxBufferGC(struct xennet_info *xi, BOOLEAN dont_set_event) {
  RING_IDX cons, prod;
  #if NTDDI_VERSION < NTDDI_VISTA
  PNDIS_PACKET head = NULL, tail = NULL;
  PNDIS_PACKET packet;
  #else
  PNET_BUFFER_LIST head = NULL;
  PNET_BUFFER_LIST tail = NULL;  
  PNET_BUFFER_LIST nbl;
  PNET_BUFFER packet;
  #endif
  ULONG tx_packets = 0;

  XN_ASSERT(KeGetCurrentIrql() == DISPATCH_LEVEL);

  KeAcquireSpinLockAtDpcLevel(&xi->tx_lock);

  if (xi->device_state != DEVICE_STATE_ACTIVE && !xi->tx_outstanding) {
    /* there is a chance that our Dpc had been queued just before the shutdown... */
    KeSetEvent(&xi->tx_idle_event, IO_NO_INCREMENT, FALSE);
    KeReleaseSpinLockFromDpcLevel(&xi->tx_lock);
    return;
  }

  do {
    prod = xi->tx_ring.sring->rsp_prod;
    KeMemoryBarrier(); /* Ensure we see responses up to 'rsp_prod'. */

    for (cons = xi->tx_ring.rsp_cons; cons != prod; cons++)
    {
      struct netif_tx_response *txrsp;
      tx_shadow_t *shadow;
      
      txrsp = RING_GET_RESPONSE(&xi->tx_ring, cons);
      
      xi->tx_ring_free++;
      
      if (txrsp->status == NETIF_RSP_NULL) {
        continue;
      }

      shadow = &xi->tx_shadows[txrsp->id];
      if (shadow->cb) {
        NdisFreeToNPagedLookasideList(&xi->tx_lookaside_list, shadow->cb);
        shadow->cb = NULL;
      }
      
      if (shadow->gref != INVALID_GRANT_REF) {
        XnEndAccess(xi->handle, shadow->gref, FALSE, (ULONG)'XNTX');
        shadow->gref = INVALID_GRANT_REF;
      }
      
      if (shadow->packet) {
        PMDL mdl;
        PUCHAR header;
        packet = shadow->packet;
        #if NTDDI_VERSION < NTDDI_VISTA
        mdl = NDIS_PACKET_FIRST_NDIS_BUFFER(packet);
        #else
        mdl = NET_BUFFER_CURRENT_MDL(packet);
        #endif
        #pragma warning(suppress:28193) /* already mapped so guaranteed to work */
        header = MmGetSystemAddressForMdlSafe(mdl, LowPagePriority);
        #if NTDDI_VERSION < NTDDI_VISTA
        #else
        header += NET_BUFFER_CURRENT_MDL_OFFSET(packet);
        #endif

        #if NTDDI_VERSION < NTDDI_VISTA
        #else
        xi->stats.ifHCOutOctets += packet->DataLength;
        if (packet->DataLength < XN_HDR_SIZE || !(header[0] & 0x01)) {
          /* unicast or tiny packet */
          xi->stats.ifHCOutUcastPkts++;
          xi->stats.ifHCOutUcastOctets += packet->DataLength;
        }
        else if (header[0] == 0xFF && header[1] == 0xFF && header[2] == 0xFF
                 && header[3] == 0xFF && header[4] == 0xFF && header[5] == 0xFF) {
          /* broadcast */
          xi->stats.ifHCOutBroadcastPkts++;
          xi->stats.ifHCOutBroadcastOctets += packet->DataLength;
        } else {
          /* multicast */
          xi->stats.ifHCOutMulticastPkts++;
          xi->stats.ifHCOutMulticastOctets += packet->DataLength;
        }
        #endif
        
        #if NTDDI_VERSION < NTDDI_VISTA
        PACKET_NEXT_PACKET(packet) = NULL;
        if (!head) {
          head = packet;
        } else {
          PACKET_NEXT_PACKET(tail) = packet;
        }
        tail = packet;
        #else
        nbl = NB_NBL(packet);
        NBL_REF(nbl)--;
        if (!NBL_REF(nbl)) {
          NET_BUFFER_LIST_NEXT_NBL(nbl) = NULL;
          if (head) {
            NET_BUFFER_LIST_NEXT_NBL(tail) = nbl;
            tail = nbl;
          } else {
            head = nbl;
            tail = nbl;
          }
        }
        #endif
        shadow->packet = NULL;
        tx_packets++;
      }
      XN_ASSERT(xi->tx_shadows[txrsp->id].gref == INVALID_GRANT_REF);
      XN_ASSERT(!xi->tx_shadows[txrsp->id].cb);
      put_id_on_freelist(xi, txrsp->id);
    }

    xi->tx_ring.rsp_cons = prod;
    /* resist the temptation to set the event more than +1... it breaks things */
    if (!dont_set_event)
      xi->tx_ring.sring->rsp_event = prod + 1;
    KeMemoryBarrier();
  } while (prod != xi->tx_ring.sring->rsp_prod);

  /* if queued packets, send them now */
  XenNet_SendQueuedPackets(xi);

  KeReleaseSpinLockFromDpcLevel(&xi->tx_lock);

  /* must be done without holding any locks */
  #if NTDDI_VERSION < NTDDI_VISTA
  while (head) {
    packet = (PNDIS_PACKET)head;
    head = PACKET_NEXT_PACKET(packet);
    NdisMSendComplete(xi->adapter_handle, packet, NDIS_STATUS_SUCCESS);
  }
  #else
  if (head)
    NdisMSendNetBufferListsComplete(xi->adapter_handle, head, NDIS_SEND_COMPLETE_FLAGS_DISPATCH_LEVEL);
  #endif

  /* must be done after we have truly given back all packets */
  KeAcquireSpinLockAtDpcLevel(&xi->tx_lock);
  xi->tx_outstanding -= tx_packets;
  if (xi->device_state != DEVICE_STATE_ACTIVE && !xi->tx_outstanding) {
    KeSetEvent(&xi->tx_idle_event, IO_NO_INCREMENT, FALSE);
  }
  KeReleaseSpinLockFromDpcLevel(&xi->tx_lock);
}

#if NTDDI_VERSION < NTDDI_VISTA
VOID
XenNet_SendPackets(NDIS_HANDLE MiniportAdapterContext, PPNDIS_PACKET PacketArray, UINT NumberOfPackets) {
  struct xennet_info *xi = MiniportAdapterContext;
  PNDIS_PACKET packet;
  UINT i;
  PLIST_ENTRY entry;
  KIRQL old_irql;

  if (xi->device_state != DEVICE_STATE_ACTIVE) {
    for (i = 0; i < NumberOfPackets; i++) {
      NdisMSendComplete(xi->adapter_handle, PacketArray[i], NDIS_STATUS_FAILURE);
    }
    return;
  }

  KeAcquireSpinLock(&xi->tx_lock, &old_irql);

  for (i = 0; i < NumberOfPackets; i++) {
    packet = PacketArray[i];
    XN_ASSERT(packet);
    entry = &PACKET_LIST_ENTRY(packet);
    InsertTailList(&xi->tx_waiting_pkt_list, entry);
  }

  XenNet_SendQueuedPackets(xi);

  KeReleaseSpinLock(&xi->tx_lock, old_irql);
}
#else
// called at <= DISPATCH_LEVEL
VOID
XenNet_SendNetBufferLists(
    NDIS_HANDLE adapter_context,
    PNET_BUFFER_LIST nb_lists,
    NDIS_PORT_NUMBER port_number,
    ULONG send_flags) {
  struct xennet_info *xi = adapter_context;
  PLIST_ENTRY nb_entry;
  KIRQL old_irql;
  PNET_BUFFER_LIST curr_nbl;
  PNET_BUFFER_LIST next_nbl;

  UNREFERENCED_PARAMETER(port_number);

  if (xi->device_state == DEVICE_STATE_INACTIVE) {
    curr_nbl = nb_lists;
    for (curr_nbl = nb_lists; curr_nbl; curr_nbl = NET_BUFFER_LIST_NEXT_NBL(curr_nbl)) {
      curr_nbl->Status = NDIS_STATUS_FAILURE;
    }
    /* this actions the whole list */
    NdisMSendNetBufferListsComplete(xi->adapter_handle, nb_lists, (send_flags & NDIS_SEND_FLAGS_DISPATCH_LEVEL)?NDIS_SEND_COMPLETE_FLAGS_DISPATCH_LEVEL:0);
    return;
  }

  KeAcquireSpinLock(&xi->tx_lock, &old_irql);
  
  for (curr_nbl = nb_lists; curr_nbl; curr_nbl = next_nbl) {
    PNET_BUFFER curr_nb;
    NBL_REF(curr_nbl) = 0;
    next_nbl = NET_BUFFER_LIST_NEXT_NBL(curr_nbl);
    NET_BUFFER_LIST_NEXT_NBL(curr_nbl) = NULL;
    for (curr_nb = NET_BUFFER_LIST_FIRST_NB(curr_nbl); curr_nb; curr_nb = NET_BUFFER_NEXT_NB(curr_nb)) {
      NB_NBL(curr_nb) = curr_nbl;
      nb_entry = &NB_LIST_ENTRY(curr_nb);
      InsertTailList(&xi->tx_waiting_pkt_list, nb_entry);
      NBL_REF(curr_nbl)++;
    }
  }

  XenNet_SendQueuedPackets(xi);

  KeReleaseSpinLock(&xi->tx_lock, old_irql);
}
#endif

VOID
XenNet_CancelSend(NDIS_HANDLE adapter_context, PVOID cancel_id)
{
  UNREFERENCED_PARAMETER(adapter_context);
  UNREFERENCED_PARAMETER(cancel_id);
  FUNCTION_ENTER();
    
  FUNCTION_EXIT();
}

BOOLEAN
XenNet_TxInit(xennet_info_t *xi) {
  USHORT i;
  UNREFERENCED_PARAMETER(xi);
  
  KeInitializeSpinLock(&xi->tx_lock);
  InitializeListHead(&xi->tx_waiting_pkt_list);

  KeInitializeEvent(&xi->tx_idle_event, SynchronizationEvent, FALSE);
  xi->tx_outstanding = 0;
  xi->tx_ring_free = NET_TX_RING_SIZE;
  
  NdisInitializeNPagedLookasideList(&xi->tx_lookaside_list, NULL, NULL, 0,
    PAGE_SIZE, XENNET_POOL_TAG, 0);

  xi->tx_id_free = 0;
  for (i = 0; i < NET_TX_RING_SIZE; i++) {
    xi->tx_shadows[i].gref = INVALID_GRANT_REF;
    xi->tx_shadows[i].cb = NULL;
    put_id_on_freelist(xi, i);
  }

  return TRUE;
}

/*
The ring is completely closed down now. We just need to empty anything left
on our freelists and harvest anything left on the rings.
*/

BOOLEAN
XenNet_TxShutdown(xennet_info_t *xi) {
  #if NTDDI_VERSION < NTDDI_VISTA
  PNDIS_PACKET packet;
  #else
  PNET_BUFFER packet;
  PNET_BUFFER_LIST nbl;
  #endif
  PLIST_ENTRY entry;
  LARGE_INTEGER timeout;
  KIRQL old_irql;

  FUNCTION_ENTER();

  KeAcquireSpinLock(&xi->tx_lock, &old_irql);

  while (xi->tx_outstanding) {
    KeReleaseSpinLock(&xi->tx_lock, old_irql);
    FUNCTION_MSG("Waiting for %d remaining packets to be sent\n", xi->tx_outstanding);
    timeout.QuadPart = -1 * 1 * 1000 * 1000 * 10; /* 1 second */
    KeWaitForSingleObject(&xi->tx_idle_event, Executive, KernelMode, FALSE, &timeout);
    KeAcquireSpinLock(&xi->tx_lock, &old_irql);
  }
  KeReleaseSpinLock(&xi->tx_lock, old_irql);

  /* Free packets in tx queue */
  while (!IsListEmpty(&xi->tx_waiting_pkt_list)) {
    entry = RemoveHeadList(&xi->tx_waiting_pkt_list);
    #if NTDDI_VERSION < NTDDI_VISTA
    packet = CONTAINING_RECORD(entry, NDIS_PACKET, PACKET_LIST_ENTRY_FIELD);
    NdisMSendComplete(xi->adapter_handle, packet, NDIS_STATUS_FAILURE);
    entry = RemoveHeadList(&xi->tx_waiting_pkt_list);
    #else
    packet = CONTAINING_RECORD(entry, NET_BUFFER, NB_LIST_ENTRY_FIELD);
    nbl = NB_NBL(packet);
    NBL_REF(nbl)--;
    if (!NBL_REF(nbl)) {
      nbl->Status = NDIS_STATUS_FAILURE;
      NdisMSendNetBufferListsComplete(xi->adapter_handle, nbl, NDIS_SEND_COMPLETE_FLAGS_DISPATCH_LEVEL);
    }
    #endif
  }
  NdisDeleteNPagedLookasideList(&xi->tx_lookaside_list);

  FUNCTION_EXIT();

  return TRUE;
}
