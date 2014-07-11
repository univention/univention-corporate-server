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

static __inline shared_buffer_t *
get_pb_from_freelist(struct xennet_info *xi)
{
  shared_buffer_t *pb;
  PVOID ptr_ref;

  if (stack_pop(xi->rx_pb_stack, &ptr_ref))
  {
    pb = ptr_ref;
    pb->ref_count = 1;
    InterlockedDecrement(&xi->rx_pb_free);
    return pb;
  }

  /* don't allocate a new one if we are shutting down */
  if (xi->device_state != DEVICE_STATE_INITIALISING && xi->device_state != DEVICE_STATE_ACTIVE)
    return NULL;
    
  pb = ExAllocatePoolWithTagPriority(NonPagedPool, sizeof(shared_buffer_t), XENNET_POOL_TAG, LowPoolPriority);
  if (!pb)
    return NULL;
  pb->virtual = ExAllocatePoolWithTagPriority(NonPagedPool, PAGE_SIZE, XENNET_POOL_TAG, LowPoolPriority);
  if (!pb->virtual)
  {
    ExFreePoolWithTag(pb, XENNET_POOL_TAG);
    return NULL;
  }
  pb->mdl = IoAllocateMdl(pb->virtual, PAGE_SIZE, FALSE, FALSE, NULL);
  if (!pb->mdl)
  {
    ExFreePoolWithTag(pb->virtual, XENNET_POOL_TAG);
    ExFreePoolWithTag(pb, XENNET_POOL_TAG);
    return NULL;
  }
  pb->gref = (grant_ref_t)XnGrantAccess(xi->handle,
            (ULONG)(MmGetPhysicalAddress(pb->virtual).QuadPart >> PAGE_SHIFT), FALSE, INVALID_GRANT_REF, (ULONG)'XNRX');
  if (pb->gref == INVALID_GRANT_REF)
  {
    IoFreeMdl(pb->mdl);
    ExFreePoolWithTag(pb->virtual, XENNET_POOL_TAG);
    ExFreePoolWithTag(pb, XENNET_POOL_TAG);
    return NULL;
  }
  MmBuildMdlForNonPagedPool(pb->mdl);
  pb->ref_count = 1;
  return pb;
}

static __inline VOID
ref_pb(struct xennet_info *xi, shared_buffer_t *pb)
{
  UNREFERENCED_PARAMETER(xi);
  InterlockedIncrement(&pb->ref_count);
}

static __inline VOID
put_pb_on_freelist(struct xennet_info *xi, shared_buffer_t *pb)
{
  if (InterlockedDecrement(&pb->ref_count) == 0)
  {
    //NdisAdjustBufferLength(pb->buffer, PAGE_SIZE);
    //NDIS_BUFFER_LINKAGE(pb->buffer) = NULL;
    if (xi->rx_pb_free > RX_MAX_PB_FREELIST)
    {
      XnEndAccess(xi->handle, pb->gref, FALSE, (ULONG)'XNRX');
      IoFreeMdl(pb->mdl);
      ExFreePoolWithTag(pb->virtual, XENNET_POOL_TAG);
      ExFreePoolWithTag(pb, XENNET_POOL_TAG);
      return;
    }
    pb->mdl->ByteCount = PAGE_SIZE;
    pb->mdl->Next = NULL;
    pb->next = NULL;
    stack_push(xi->rx_pb_stack, pb);
    InterlockedIncrement(&xi->rx_pb_free);
  }
}

static __inline shared_buffer_t *
get_hb_from_freelist(struct xennet_info *xi)
{
  shared_buffer_t *hb;
  PVOID ptr_ref;

  if (stack_pop(xi->rx_hb_stack, &ptr_ref))
  {
    hb = ptr_ref;
    InterlockedDecrement(&xi->rx_hb_free);
    return hb;
  }

  /* don't allocate a new one if we are shutting down */
  if (xi->device_state != DEVICE_STATE_INITIALISING && xi->device_state != DEVICE_STATE_ACTIVE)
    return NULL;
    
  hb = ExAllocatePoolWithTagPriority(NonPagedPool, sizeof(shared_buffer_t) + MAX_ETH_HEADER_LENGTH + MAX_LOOKAHEAD_LENGTH, XENNET_POOL_TAG, LowPoolPriority);
  if (!hb)
    return NULL;
  NdisZeroMemory(hb, sizeof(shared_buffer_t));
  hb->mdl = IoAllocateMdl(hb + 1, MAX_ETH_HEADER_LENGTH + MAX_LOOKAHEAD_LENGTH, FALSE, FALSE, NULL);
  if (!hb->mdl) {
    ExFreePoolWithTag(hb, XENNET_POOL_TAG);
    return NULL;
  }
  MmBuildMdlForNonPagedPool(hb->mdl);
  return hb;
}

static __inline VOID
put_hb_on_freelist(struct xennet_info *xi, shared_buffer_t *hb)
{
  XN_ASSERT(xi);
  hb->mdl->ByteCount = sizeof(shared_buffer_t) + MAX_ETH_HEADER_LENGTH + MAX_LOOKAHEAD_LENGTH;
  hb->mdl->Next = NULL;
  hb->next = NULL;
  stack_push(xi->rx_hb_stack, hb);
  InterlockedIncrement(&xi->rx_hb_free);
}

// Called at DISPATCH_LEVEL with rx lock held
static VOID
XenNet_FillRing(struct xennet_info *xi)
{
  unsigned short id;
  shared_buffer_t *page_buf;
  ULONG i, notify;
  ULONG batch_target;
  RING_IDX req_prod = xi->rx_ring.req_prod_pvt;
  netif_rx_request_t *req;

  //FUNCTION_ENTER();

  if (xi->device_state != DEVICE_STATE_ACTIVE)
    return;

  batch_target = xi->rx_target - (req_prod - xi->rx_ring.rsp_cons);

  if (batch_target < (xi->rx_target >> 2)) {
    //FUNCTION_EXIT();
    return; /* only refill if we are less than 3/4 full already */
  }

  for (i = 0; i < batch_target; i++) {
    page_buf = get_pb_from_freelist(xi);
    if (!page_buf) {
      FUNCTION_MSG("Added %d out of %d buffers to rx ring (no free pages)\n", i, batch_target);
      break;
    }
    xi->rx_id_free--;

    /* Give to netback */
    id = (USHORT)((req_prod + i) & (NET_RX_RING_SIZE - 1));
    XN_ASSERT(xi->rx_ring_pbs[id] == NULL);
    xi->rx_ring_pbs[id] = page_buf;
    req = RING_GET_REQUEST(&xi->rx_ring, req_prod + i);
    req->id = id;
    req->gref = page_buf->gref;
    XN_ASSERT(req->gref != INVALID_GRANT_REF);
  }
  KeMemoryBarrier();
  xi->rx_ring.req_prod_pvt = req_prod + i;
  RING_PUSH_REQUESTS_AND_CHECK_NOTIFY(&xi->rx_ring, notify);
  if (notify) {
    XnNotify(xi->handle, xi->event_channel);
  }

  //FUNCTION_EXIT();

  return;
}

#if NTDDI_VERSION < NTDDI_VISTA
typedef struct {
  PNDIS_PACKET first_packet;
  PNDIS_PACKET last_packet;
  ULONG packet_count;
} rx_context_t;
#else
typedef struct {
  PNET_BUFFER_LIST first_nbl;
  PNET_BUFFER_LIST last_nbl;
  ULONG packet_count;
  ULONG nbl_count;
} rx_context_t;
#endif

#if NTDDI_VERSION < NTDDI_VISTA
/*
 NDIS5 appears to insist that the checksum on received packets is correct, and won't
 believe us when we lie about it, which happens when the packet is generated on the
 same bridge in Dom0. Doh!
 This is only for TCP and UDP packets. IP checksums appear to be correct anyways.
*/

static BOOLEAN
XenNet_SumPacketData(
    packet_info_t *pi,
    PNDIS_PACKET packet,
    BOOLEAN set_csum) {
  USHORT i;
  PUCHAR buffer;
  PMDL mdl;
  UINT total_length;
  UINT data_length;
  UINT buffer_length;
  USHORT buffer_offset;
  ULONG csum;
  PUSHORT csum_ptr;
  USHORT remaining;
  USHORT ip4_length;
  BOOLEAN csum_span = TRUE; /* when the USHORT to be checksummed spans a buffer */
  
  NdisGetFirstBufferFromPacketSafe(packet, &mdl, &buffer, &buffer_length, &total_length, NormalPagePriority);
  if (!buffer) {
    FUNCTION_MSG("NdisGetFirstBufferFromPacketSafe failed, buffer == NULL\n");
    return FALSE;
  }
  XN_ASSERT(mdl);

  ip4_length = GET_NET_PUSHORT(&buffer[XN_HDR_SIZE + 2]);
  data_length = ip4_length + XN_HDR_SIZE;
  
  if ((USHORT)data_length > total_length) {
    FUNCTION_MSG("Size Mismatch %d (ip4_length + XN_HDR_SIZE) != %d (total_length)\n", ip4_length + XN_HDR_SIZE, total_length);
    return FALSE;
  }

  switch (pi->ip_proto) {
  case 6:
    XN_ASSERT(buffer_length >= (USHORT)(XN_HDR_SIZE + pi->ip4_header_length + 17));
    csum_ptr = (USHORT *)&buffer[XN_HDR_SIZE + pi->ip4_header_length + 16];
    break;
  case 17:
    XN_ASSERT(buffer_length >= (USHORT)(XN_HDR_SIZE + pi->ip4_header_length + 7));
    csum_ptr = (USHORT *)&buffer[XN_HDR_SIZE + pi->ip4_header_length + 6];
    break;
  default:
    FUNCTION_MSG("Don't know how to calc sum for IP Proto %d\n", pi->ip_proto);
    //FUNCTION_EXIT();
    return FALSE; // should never happen
  }

  if (set_csum)  
    *csum_ptr = 0;

  csum = 0;
  csum += GET_NET_PUSHORT(&buffer[XN_HDR_SIZE + 12]) + GET_NET_PUSHORT(&buffer[XN_HDR_SIZE + 14]); // src
  csum += GET_NET_PUSHORT(&buffer[XN_HDR_SIZE + 16]) + GET_NET_PUSHORT(&buffer[XN_HDR_SIZE + 18]); // dst
  csum += ((USHORT)buffer[XN_HDR_SIZE + 9]);

  remaining = ip4_length - pi->ip4_header_length;

  csum += remaining;
  
  csum_span = FALSE;
  buffer_offset = i = XN_HDR_SIZE + pi->ip4_header_length;
  while (i < data_length) {
    /* don't include the checksum field itself in the calculation */
    if ((pi->ip_proto == 6 && i == XN_HDR_SIZE + pi->ip4_header_length + 16) || (pi->ip_proto == 17 && i == XN_HDR_SIZE + pi->ip4_header_length + 6)) {
      /* we know that this always happens in the header buffer so we are guaranteed the full two bytes */
      i += 2;
      buffer_offset += 2;
      continue;
    }
    if (csum_span) {
      /* the other half of the next bit */
      XN_ASSERT(buffer_offset == 0);
      csum += (USHORT)buffer[buffer_offset];
      csum_span = FALSE;
      i += 1;
      buffer_offset += 1;
    } else if (buffer_offset == buffer_length - 1) {
      /* deal with a buffer ending on an odd byte boundary */
      csum += (USHORT)buffer[buffer_offset] << 8;
      csum_span = TRUE;
      i += 1;
      buffer_offset += 1;
    } else {
      csum += GET_NET_PUSHORT(&buffer[buffer_offset]);
      i += 2;
      buffer_offset += 2;
    }
    if (buffer_offset == buffer_length && i < total_length) {
      NdisGetNextBuffer(mdl, &mdl);
      if (mdl == NULL) {
        FUNCTION_MSG(__DRIVER_NAME "     Ran out of buffers\n");
        return FALSE; // should never happen
      }
      NdisQueryBufferSafe(mdl, &buffer, &buffer_length, NormalPagePriority);
      XN_ASSERT(buffer_length);
      buffer_offset = 0;
    }
  }
      
  while (csum & 0xFFFF0000)
    csum = (csum & 0xFFFF) + (csum >> 16);
  
  if (set_csum) {
    *csum_ptr = (USHORT)~GET_NET_USHORT((USHORT)csum);
  } else {
    return (BOOLEAN)(*csum_ptr == (USHORT)~GET_NET_USHORT((USHORT)csum));
  }
  return TRUE;
}
#endif

static BOOLEAN
XenNet_MakePacket(struct xennet_info *xi, rx_context_t *rc, packet_info_t *pi) {
  #if NTDDI_VERSION < NTDDI_VISTA
  NDIS_STATUS status;
  PNDIS_PACKET packet;
  #else
  PNET_BUFFER_LIST nbl;
  PNET_BUFFER packet;
  #endif
  PMDL mdl_head, mdl_tail, curr_mdl;
  PUCHAR header_va;
  ULONG out_remaining;
  ULONG header_extra;
  shared_buffer_t *header_buf;
  ULONG outstanding;
  #if NTDDI_VERSION < NTDDI_VISTA
  PNDIS_TCP_IP_CHECKSUM_PACKET_INFO csum_info;
  //UINT packet_length;
  #else
  NDIS_TCP_IP_CHECKSUM_NET_BUFFER_LIST_INFO csum_info;
  #endif
  //FUNCTION_ENTER();

  #if NTDDI_VERSION < NTDDI_VISTA
  NdisAllocatePacket(&status, &packet, xi->rx_packet_pool);
  if (status != NDIS_STATUS_SUCCESS) {
    FUNCTION_MSG("No free packets\n");
    return FALSE;
  }
  
  NdisZeroMemory(packet->MiniportReservedEx, sizeof(packet->MiniportReservedEx));
  NDIS_SET_PACKET_HEADER_SIZE(packet, XN_HDR_SIZE);
  #else  
  nbl = NdisAllocateNetBufferList(xi->rx_nbl_pool, 0, 0);
  if (!nbl) {
    /* buffers will be freed in MakePackets */
    FUNCTION_MSG("No free nbls\n");
    //FUNCTION_EXIT();
    return FALSE;
  }

  packet = NdisAllocateNetBuffer(xi->rx_packet_pool, NULL, 0, 0);
  if (!packet) {
    FUNCTION_MSG("No free packets\n");
    NdisFreeNetBufferList(nbl);
    //FUNCTION_EXIT();
    return FALSE;
  }
  #endif

  if ((!pi->first_mdl->Next || (xi->config_rx_coalesce && pi->total_length <= PAGE_SIZE)) && !pi->split_required) {
    /* a single buffer <= MTU */
    header_buf = NULL;
    /* get all the packet into the header */
    XenNet_BuildHeader(pi, pi->first_mdl_virtual, PAGE_SIZE);
    #if NTDDI_VERSION < NTDDI_VISTA
    NdisChainBufferAtBack(packet, pi->first_mdl);
    PACKET_FIRST_PB(packet) = pi->first_pb;
    #else
    NET_BUFFER_FIRST_MDL(packet) = pi->first_mdl;
    NET_BUFFER_CURRENT_MDL(packet) = pi->first_mdl;
    NET_BUFFER_CURRENT_MDL_OFFSET(packet) = 0;
    NET_BUFFER_DATA_OFFSET(packet) = 0;
    NET_BUFFER_DATA_LENGTH(packet) = pi->total_length;
    NB_FIRST_PB(packet) = pi->first_pb;
    #endif
    ref_pb(xi, pi->first_pb);
  } else {
    XN_ASSERT(ndis_os_minor_version >= 1);
    header_buf = get_hb_from_freelist(xi);
    if (!header_buf) {
      FUNCTION_MSG("No free header buffers\n");
      #if NTDDI_VERSION < NTDDI_VISTA
      NdisUnchainBufferAtFront(packet, &curr_mdl);
      NdisFreePacket(packet);
      #else
      NdisFreeNetBufferList(nbl);
      NdisFreeNetBuffer(packet);
      #endif
      return FALSE;
    }
    header_va = (PUCHAR)(header_buf + 1);
    NdisMoveMemory(header_va, pi->header, pi->header_length);
    //if (pi->ip_proto == 50) {
    //  FUNCTION_MSG("header_length = %d, current_lookahead = %d\n", pi->header_length, xi->current_lookahead);
    //  FUNCTION_MSG("ip4_header_length = %d\n", pi->ip4_header_length);
    //  FUNCTION_MSG("tcp_header_length = %d\n", pi->tcp_header_length);
    //}
    /* make sure only the header is in the first buffer (or the entire packet, but that is done in the above case) */
    XenNet_BuildHeader(pi, header_va, MAX_ETH_HEADER_LENGTH + pi->ip4_header_length + pi->tcp_header_length);
    header_extra = pi->header_length - (MAX_ETH_HEADER_LENGTH + pi->ip4_header_length + pi->tcp_header_length);
    XN_ASSERT(pi->header_length <= MAX_ETH_HEADER_LENGTH + MAX_LOOKAHEAD_LENGTH);
    header_buf->mdl->ByteCount = pi->header_length;
    mdl_head = mdl_tail = curr_mdl = header_buf->mdl;
    #if NTDDI_VERSION < NTDDI_VISTA
    PACKET_FIRST_PB(packet) = header_buf;
    header_buf->next = pi->curr_pb;
    NdisChainBufferAtBack(packet, mdl_head);
    #else
    NB_FIRST_PB(packet) = header_buf;
    header_buf->next = pi->curr_pb;
    NET_BUFFER_FIRST_MDL(packet) = mdl_head;
    NET_BUFFER_CURRENT_MDL(packet) = mdl_head;
    NET_BUFFER_CURRENT_MDL_OFFSET(packet) = 0;
    NET_BUFFER_DATA_OFFSET(packet) = 0;
    NET_BUFFER_DATA_LENGTH(packet) = pi->header_length;
    #endif

    if (pi->split_required) {
      /* must be ip4 */
      ULONG tcp_length;
      USHORT new_ip4_length;
      tcp_length = (USHORT)min(pi->mss, pi->tcp_remaining);
      new_ip4_length = (USHORT)(pi->ip4_header_length + pi->tcp_header_length + tcp_length);
      SET_NET_USHORT(&header_va[XN_HDR_SIZE + 2], new_ip4_length);
      SET_NET_ULONG(&header_va[XN_HDR_SIZE + pi->ip4_header_length + 4], pi->tcp_seq);
      pi->tcp_seq += tcp_length;
      pi->tcp_remaining = (USHORT)(pi->tcp_remaining - tcp_length);
      /* part of the packet is already present in the header buffer for lookahead */
      out_remaining = tcp_length - header_extra;
      XN_ASSERT((LONG)out_remaining >= 0);
    } else {
      out_remaining = pi->total_length - pi->header_length;
      XN_ASSERT((LONG)out_remaining >= 0);
    }

    while (out_remaining != 0) {
      //ULONG in_buffer_offset;
      ULONG in_buffer_length;
      ULONG out_length;
      
      //if (pi->ip_proto == 50) {
      //  FUNCTION_MSG("in loop - out_remaining = %d, curr_buffer = %p, curr_pb = %p\n", out_remaining, pi->curr_mdl, pi->curr_pb);
      //}
      if (!pi->curr_mdl || !pi->curr_pb) {
        FUNCTION_MSG("out of buffers for packet\n");
        //KdPrint((__DRIVER_NAME "     out_remaining = %d, curr_buffer = %p, curr_pb = %p\n", out_remaining, pi->curr_mdl, pi->curr_pb));
        // TODO: free some stuff or we'll leak
        /* unchain buffers then free packet */
        //FUNCTION_EXIT();
        return FALSE;
      }

      in_buffer_length = MmGetMdlByteCount(pi->curr_mdl);
      out_length = min(out_remaining, in_buffer_length - pi->curr_mdl_offset);
      curr_mdl = IoAllocateMdl((PUCHAR)MmGetMdlVirtualAddress(pi->curr_mdl) + pi->curr_mdl_offset, out_length, FALSE, FALSE, NULL);
      XN_ASSERT(curr_mdl);
      IoBuildPartialMdl(pi->curr_mdl, curr_mdl, (PUCHAR)MmGetMdlVirtualAddress(pi->curr_mdl) + pi->curr_mdl_offset, out_length);
      mdl_tail->Next = curr_mdl;
      mdl_tail = curr_mdl;
      curr_mdl->Next = NULL; /* I think this might be redundant */
      #if NTDDI_VERSION < NTDDI_VISTA
      #else
      NET_BUFFER_DATA_LENGTH(packet) += out_length;
      #endif
      ref_pb(xi, pi->curr_pb);
      pi->curr_mdl_offset = (USHORT)(pi->curr_mdl_offset + out_length);
      if (pi->curr_mdl_offset == in_buffer_length) {
        pi->curr_mdl = pi->curr_mdl->Next;
        pi->curr_pb = pi->curr_pb->next;
        pi->curr_mdl_offset = 0;
      }
      out_remaining -= out_length;
    }
    #if NTDDI_VERSION < NTDDI_VISTA
    if (pi->split_required) {
      // TODO: only if Ip checksum is disabled...
      XenNet_SumIpHeader(header_va, pi->ip4_header_length);
    }
    #endif
    if (header_extra > 0)
      pi->header_length -= header_extra;
  }
  
  rc->packet_count++;
  #if NTDDI_VERSION < NTDDI_VISTA
  #else
  NET_BUFFER_LIST_FIRST_NB(nbl) = packet;
  #endif

  if (pi->parse_result == PARSE_OK) {
    #if NTDDI_VERSION < NTDDI_VISTA
    csum_info = (PNDIS_TCP_IP_CHECKSUM_PACKET_INFO)&NDIS_PER_PACKET_INFO_FROM_PACKET(
      packet, TcpIpChecksumPacketInfo);
    csum_info->Value = 0;
    if (pi->csum_blank || pi->data_validated || pi->split_required) {
      BOOLEAN checksum_offload = FALSE;
      /* we know this is IPv4, and we know Linux always validates the IPv4 checksum for us */
      if (xi->setting_csum.V4Receive.IpChecksum) {
        if (!pi->ip_has_options || xi->setting_csum.V4Receive.IpOptionsSupported) {
          if (XenNet_CheckIpHeaderSum(pi->header, pi->ip4_header_length))
            csum_info->Receive.NdisPacketIpChecksumSucceeded = TRUE;
          else
            csum_info->Receive.NdisPacketIpChecksumFailed = TRUE;
        }
      }
      if (xi->setting_csum.V4Receive.TcpChecksum && pi->ip_proto == 6) {
        if (!pi->tcp_has_options || xi->setting_csum.V4Receive.TcpOptionsSupported) {
          csum_info->Receive.NdisPacketTcpChecksumSucceeded = TRUE;
          checksum_offload = TRUE;
        }
      } else if (xi->setting_csum.V4Receive.UdpChecksum && pi->ip_proto == 17) {
        csum_info->Receive.NdisPacketUdpChecksumSucceeded = TRUE;
        checksum_offload = TRUE;
      }
      if (pi->csum_blank && (!xi->config_csum_rx_dont_fix || !checksum_offload)) {
        XenNet_SumPacketData(pi, packet, TRUE);
      }
    } else if (xi->config_csum_rx_check && pi->ip_version == 4) {
      if (xi->setting_csum.V4Receive.IpChecksum) {
        if (!pi->ip_has_options || xi->setting_csum.V4Receive.IpOptionsSupported) {
          if (XenNet_CheckIpHeaderSum(pi->header, pi->ip4_header_length))
            csum_info->Receive.NdisPacketIpChecksumSucceeded = TRUE;
         else
            csum_info->Receive.NdisPacketIpChecksumFailed = TRUE;
        }
      }
      if (xi->setting_csum.V4Receive.TcpChecksum && pi->ip_proto == 6) {
        if (!pi->tcp_has_options || xi->setting_csum.V4Receive.TcpOptionsSupported) {
          if (XenNet_SumPacketData(pi, packet, FALSE)) {
            csum_info->Receive.NdisPacketTcpChecksumSucceeded = TRUE;
          } else {
            csum_info->Receive.NdisPacketTcpChecksumFailed = TRUE;
          }
        }
      } else if (xi->setting_csum.V4Receive.UdpChecksum && pi->ip_proto == 17) {
        if (XenNet_SumPacketData(pi, packet, FALSE)) {
          csum_info->Receive.NdisPacketUdpChecksumSucceeded = TRUE;
        } else {
          csum_info->Receive.NdisPacketUdpChecksumFailed = TRUE;
        }
      }
    }
    #else
    csum_info.Value = 0;
    if (pi->csum_blank || pi->data_validated || pi->mss) {
      if (pi->ip_proto == 6) {
        csum_info.Receive.IpChecksumSucceeded = TRUE;
        csum_info.Receive.TcpChecksumSucceeded = TRUE;
      } else if (pi->ip_proto == 17) {
        csum_info.Receive.IpChecksumSucceeded = TRUE;
        csum_info.Receive.UdpChecksumSucceeded = TRUE;
      }
    }
    NET_BUFFER_LIST_INFO(nbl, TcpIpChecksumNetBufferListInfo) = csum_info.Value;
    #endif
  }

  #if NTDDI_VERSION < NTDDI_VISTA
  if (!rc->first_packet) {
    rc->first_packet = packet;
  } else {
    PACKET_NEXT_PACKET(rc->last_packet) = packet;
  }
  rc->last_packet = packet;
  rc->packet_count++;
  #else
  if (!rc->first_nbl) {
    rc->first_nbl = nbl;
  } else {
    NET_BUFFER_LIST_NEXT_NBL(rc->last_nbl) = nbl;
  }
  rc->last_nbl = nbl;
  NET_BUFFER_LIST_NEXT_NBL(nbl) = NULL;
  rc->nbl_count++;
  if (pi->is_multicast) {
    /* multicast */
    xi->stats.ifHCInMulticastPkts++;
    xi->stats.ifHCInMulticastOctets += NET_BUFFER_DATA_LENGTH(packet);
  } else if (pi->is_broadcast) {
    /* broadcast */
    xi->stats.ifHCInBroadcastPkts++;
    xi->stats.ifHCInBroadcastOctets += NET_BUFFER_DATA_LENGTH(packet);
  } else {
    /* unicast */
    xi->stats.ifHCInUcastPkts++;
    xi->stats.ifHCInUcastOctets += NET_BUFFER_DATA_LENGTH(packet);
  }
  #endif

  outstanding = InterlockedIncrement(&xi->rx_outstanding);
  #if NTDDI_VERSION < NTDDI_VISTA
  if (outstanding > RX_PACKET_HIGH_WATER_MARK || !xi->rx_pb_free) {
    NDIS_SET_PACKET_STATUS(packet, NDIS_STATUS_RESOURCES);
  } else {
    NDIS_SET_PACKET_STATUS(packet, NDIS_STATUS_SUCCESS);
  }
  #if 0
  /* windows gets lazy about ack packets and holds on to them forever under high load situations. we don't like this */
  NdisQueryPacketLength(packet, &packet_length);
  if (pi->parse_result != PARSE_OK || (pi->ip_proto == 6 && packet_length <= NDIS_STATUS_RESOURCES_MAX_LENGTH))
    NDIS_SET_PACKET_STATUS(packet, NDIS_STATUS_RESOURCES);
  else
    NDIS_SET_PACKET_STATUS(packet, NDIS_STATUS_SUCCESS);
  #endif
  #endif

  //FUNCTION_EXIT();
  return TRUE;
}

static VOID
XenNet_MakePackets(struct xennet_info *xi, rx_context_t *rc, packet_info_t *pi)
{
  UCHAR tcp_flags;
  shared_buffer_t *page_buf;

  XenNet_ParsePacketHeader(pi, NULL, XN_HDR_SIZE + xi->current_lookahead);

  if (!XenNet_FilterAcceptPacket(xi, pi)) {
    goto done;
  }

  if (pi->split_required) {
    #if NTDDI_VERSION < NTDDI_VISTA
    /* need to split to mss for NDIS5 */
    #else
    switch (xi->current_gso_rx_split_type) {
    case RX_LSO_SPLIT_HALF:
      pi->mss = max((pi->tcp_length + 1) / 2, pi->mss);
      break;
    case RX_LSO_SPLIT_NONE:
      pi->mss = 65535;
      break;
    }
    #endif
  }

  switch (pi->ip_proto) {
  case 6:  // TCP
    if (pi->split_required)
      break;
    /* fall through */
  case 17:  // UDP
    if (!XenNet_MakePacket(xi, rc, pi)) {
      FUNCTION_MSG("Failed to make packet\n");
      #if NTDDI_VERSION < NTDDI_VISTA
      xi->stat_rx_no_buffer++;
      #else
      xi->stats.ifInDiscards++;
      #endif
      goto done;
    }
    goto done;
  default:
    if (!XenNet_MakePacket(xi, rc, pi)) {
      FUNCTION_MSG("Failed to make packet\n");
      #if NTDDI_VERSION < NTDDI_VISTA
      xi->stat_rx_no_buffer++;
      #else
      xi->stats.ifInDiscards++;
      #endif
      goto done;
    }
    goto done;
  }

  /* this is the split_required code */
  pi->tcp_remaining = pi->tcp_length;

  /* we can make certain assumptions here as the following code is only for tcp4 */
  tcp_flags = pi->header[XN_HDR_SIZE + pi->ip4_header_length + 13];
  /* clear all tcp flags except ack except for the last packet */
  pi->header[XN_HDR_SIZE + pi->ip4_header_length + 13] &= 0x10;
  while (pi->tcp_remaining) {
    if (pi->tcp_remaining <= pi->mss) {
      /* restore tcp flags for the last packet */
      pi->header[XN_HDR_SIZE + pi->ip4_header_length + 13] = tcp_flags;
    }
    if (!XenNet_MakePacket(xi, rc, pi)) {
      FUNCTION_MSG("Failed to make packet\n");
      #if NTDDI_VERSION < NTDDI_VISTA
      xi->stat_rx_no_buffer++;
      #else
      xi->stats.ifInDiscards++;
      #endif
      break; /* we are out of memory - just drop the packets */
    }
  }
done:
  page_buf = pi->first_pb;
  while (page_buf) {
    shared_buffer_t *next_pb = page_buf->next;
    put_pb_on_freelist(xi, page_buf); /* this doesn't actually free the page_puf if there are outstanding references */
    page_buf = next_pb;
  }
  XenNet_ClearPacketInfo(pi);
  //FUNCTION_EXIT();
  return;
}

#if NTDDI_VERSION < NTDDI_VISTA
/* called at DISPATCH_LEVEL */
/* it's okay for return packet to be called while resume_state != RUNNING as the packet will simply be added back to the freelist, the grants will be fixed later */
VOID
XenNet_ReturnPacket(NDIS_HANDLE adapter_context, PNDIS_PACKET packet) {
  struct xennet_info *xi = adapter_context;
  PNDIS_BUFFER buffer;
  shared_buffer_t *page_buf = PACKET_FIRST_PB(packet);

  //FUNCTION_ENTER();
  NdisUnchainBufferAtFront(packet, &buffer);
  
  while (buffer) {
    shared_buffer_t *next_buf;
    XN_ASSERT(page_buf);
    next_buf = page_buf->next;
    if (!page_buf->virtual) {
      /* this is a hb not a pb because virtual is NULL (virtual is just the memory after the hb */
      put_hb_on_freelist(xi, (shared_buffer_t *)MmGetMdlVirtualAddress(buffer) - 1);
    } else {
      if (buffer != page_buf->mdl)
        NdisFreeBuffer(buffer);
      put_pb_on_freelist(xi, page_buf);
    }
    NdisUnchainBufferAtFront(packet, &buffer);
    page_buf = next_buf;
  }

  NdisFreePacket(packet);
  InterlockedDecrement(&xi->rx_outstanding);
  if (!xi->rx_outstanding && xi->device_state != DEVICE_STATE_ACTIVE)
    KeSetEvent(&xi->rx_idle_event, IO_NO_INCREMENT, FALSE);
  //FUNCTION_EXIT();
}
#else
/* called at <= DISPATCH_LEVEL */
/* it's okay for return packet to be called while resume_state != RUNNING as the packet will simply be added back to the freelist, the grants will be fixed later */
VOID
XenNet_ReturnNetBufferLists(NDIS_HANDLE adapter_context, PNET_BUFFER_LIST curr_nbl, ULONG return_flags)
{
  struct xennet_info *xi = adapter_context;
  UNREFERENCED_PARAMETER(return_flags);

  //FUNCTION_ENTER();

  //KdPrint((__DRIVER_NAME "     page_buf = %p\n", page_buf));

  XN_ASSERT(xi);
  while (curr_nbl)
  {
    PNET_BUFFER_LIST next_nbl;
    PNET_BUFFER curr_nb;
    
    next_nbl = NET_BUFFER_LIST_NEXT_NBL(curr_nbl);
    curr_nb = NET_BUFFER_LIST_FIRST_NB(curr_nbl);
    while (curr_nb)
    {
      PNET_BUFFER next_nb;
      PMDL curr_mdl;
      shared_buffer_t *page_buf;
      
      next_nb = NET_BUFFER_NEXT_NB(curr_nb);
      curr_mdl = NET_BUFFER_FIRST_MDL(curr_nb);
      page_buf = NB_FIRST_PB(curr_nb);
      while (curr_mdl)
      {
        shared_buffer_t *next_buf;
        PMDL next_mdl;
        
        XN_ASSERT(page_buf); /* make sure that there is a pb to match this mdl */
        next_mdl = curr_mdl->Next;
        next_buf = page_buf->next;
        if (!page_buf->virtual)
        {
          /* this is a hb not a pb because virtual is NULL (virtual is just the memory after the hb */
          put_hb_on_freelist(xi, (shared_buffer_t *)MmGetMdlVirtualAddress(curr_mdl) - 1);
        }
        else
        {
          //KdPrint((__DRIVER_NAME "     returning page_buf %p with id %d\n", page_buf, page_buf->id));
          if (curr_mdl != page_buf->mdl)
          {
            //KdPrint((__DRIVER_NAME "     curr_mdl = %p, page_buf->mdl = %p\n", curr_mdl, page_buf->mdl));
            IoFreeMdl(curr_mdl);
          }
          put_pb_on_freelist(xi, page_buf);
        }
        curr_mdl = next_mdl;
        page_buf = next_buf;
      }

      NdisFreeNetBuffer(curr_nb);
      InterlockedDecrement(&xi->rx_outstanding);

      curr_nb = next_nb;
    }
    NdisFreeNetBufferList(curr_nbl);
    curr_nbl = next_nbl;
  }
  
  if (!xi->rx_outstanding && xi->device_state != DEVICE_STATE_ACTIVE)
    KeSetEvent(&xi->rx_idle_event, IO_NO_INCREMENT, FALSE);

  //FUNCTION_EXIT();
}
#endif

/* We limit the number of packets per interrupt so that acks get a chance
under high rx load. The DPC is immediately re-scheduled */

#define MAXIMUM_PACKETS_PER_INDICATE 32

#define MAXIMUM_PACKETS_PER_INTERRUPT 2560 /* this is calculated before large packet split */
#define MAXIMUM_DATA_PER_INTERRUPT (MAXIMUM_PACKETS_PER_INTERRUPT * 1500) /* help account for large packets */

// Called at DISPATCH_LEVEL
BOOLEAN
XenNet_RxBufferCheck(struct xennet_info *xi)
{
  RING_IDX cons, prod;
  ULONG packet_count = 0;
  ULONG packet_data = 0;
  ULONG buffer_count = 0;
  USHORT id;
  int more_to_do = FALSE;
  shared_buffer_t *page_buf;
  #if NTDDI_VERSION < NTDDI_VISTA
  PNDIS_PACKET packets[MAXIMUM_PACKETS_PER_INDICATE];
  PNDIS_PACKET first_header_only_packet;
  PNDIS_PACKET last_header_only_packet;
  #else
  #endif
  //ULONG nbl_count = 0;
  ULONG interim_packet_data = 0;
  struct netif_extra_info *ei;
  rx_context_t rc;
  packet_info_t *pi = &xi->rxpi[KeGetCurrentProcessorNumber() & 0xff];
  shared_buffer_t *head_buf = NULL;
  shared_buffer_t *tail_buf = NULL;
  shared_buffer_t *last_buf = NULL;
  BOOLEAN extra_info_flag = FALSE;
  BOOLEAN more_data_flag = FALSE;
  BOOLEAN dont_set_event;
  //FUNCTION_ENTER();

  #if NTDDI_VERSION < NTDDI_VISTA
  rc.first_packet = NULL;
  rc.last_packet = NULL;
  rc.packet_count = 0;
  #else
  rc.first_nbl = NULL;
  rc.last_nbl = NULL;
  rc.packet_count = 0;
  rc.nbl_count = 0;
  #endif
  
  /* get all the buffers off the ring as quickly as possible so the lock is held for a minimum amount of time */
  KeAcquireSpinLockAtDpcLevel(&xi->rx_lock);
  
  if (xi->device_state != DEVICE_STATE_ACTIVE) {
    /* there is a chance that our Dpc had been queued just before the shutdown... */
    KeReleaseSpinLockFromDpcLevel(&xi->rx_lock);
    return FALSE;
  }

  if (xi->rx_partial_buf) {
    head_buf = xi->rx_partial_buf;
    tail_buf = xi->rx_partial_buf;
    while (tail_buf->next)
      tail_buf = tail_buf->next;
    more_data_flag = xi->rx_partial_more_data_flag;
    extra_info_flag = xi->rx_partial_extra_info_flag;
    xi->rx_partial_buf = NULL;
  }

  do {
    prod = xi->rx_ring.sring->rsp_prod;
    KeMemoryBarrier(); /* Ensure we see responses up to 'prod'. */

    for (cons = xi->rx_ring.rsp_cons; cons != prod && packet_count < MAXIMUM_PACKETS_PER_INTERRUPT && packet_data < MAXIMUM_DATA_PER_INTERRUPT; cons++) {
      id = (USHORT)(cons & (NET_RX_RING_SIZE - 1));
      page_buf = xi->rx_ring_pbs[id];
      XN_ASSERT(page_buf);
      xi->rx_ring_pbs[id] = NULL;
      xi->rx_id_free++;
      memcpy(&page_buf->rsp, RING_GET_RESPONSE(&xi->rx_ring, cons), max(sizeof(struct netif_rx_response), sizeof(struct netif_extra_info)));
      if (!extra_info_flag) {
        if (page_buf->rsp.status <= 0 || page_buf->rsp.offset + page_buf->rsp.status > PAGE_SIZE) {
          FUNCTION_MSG("Error: rsp offset %d, size %d\n",
            page_buf->rsp.offset, page_buf->rsp.status);
          XN_ASSERT(!extra_info_flag);
          put_pb_on_freelist(xi, page_buf);
          continue;
        }
      }
      
      if (!head_buf) {
        head_buf = page_buf;
        tail_buf = page_buf;
      } else {
        tail_buf->next = page_buf;
        tail_buf = page_buf;
      }
      page_buf->next = NULL;

      if (extra_info_flag) {
        ei = (struct netif_extra_info *)&page_buf->rsp;
        extra_info_flag = ei->flags & XEN_NETIF_EXTRA_FLAG_MORE;
      } else {
        more_data_flag = (BOOLEAN)(page_buf->rsp.flags & NETRXF_more_data);
        extra_info_flag = (BOOLEAN)(page_buf->rsp.flags & NETRXF_extra_info);
        interim_packet_data += page_buf->rsp.status;
      }
      
      if (!extra_info_flag && !more_data_flag) {
        last_buf = page_buf;
        packet_count++;
        packet_data += interim_packet_data;
        interim_packet_data = 0;
        }
      buffer_count++;
    }
    xi->rx_ring.rsp_cons = cons;

    /* Give netback more buffers */
    XenNet_FillRing(xi);

    if (packet_count >= MAXIMUM_PACKETS_PER_INTERRUPT || packet_data >= MAXIMUM_DATA_PER_INTERRUPT)
      break;

    more_to_do = RING_HAS_UNCONSUMED_RESPONSES(&xi->rx_ring);
    if (!more_to_do) {
      xi->rx_ring.sring->rsp_event = xi->rx_ring.rsp_cons + 1;
      KeMemoryBarrier();
      more_to_do = RING_HAS_UNCONSUMED_RESPONSES(&xi->rx_ring);
    }
  } while (more_to_do);
  
  /* anything past last_buf belongs to an incomplete packet... */
  if (last_buf && last_buf->next)
  {
    FUNCTION_MSG("Partial receive\n");
    xi->rx_partial_buf = last_buf->next;
    xi->rx_partial_more_data_flag = more_data_flag;
    xi->rx_partial_extra_info_flag = extra_info_flag;
    last_buf->next = NULL;
  }

  KeReleaseSpinLockFromDpcLevel(&xi->rx_lock);

  if (packet_count >= MAXIMUM_PACKETS_PER_INTERRUPT || packet_data >= MAXIMUM_DATA_PER_INTERRUPT)
  {
    /* fire again immediately */
    FUNCTION_MSG("Dpc Duration Exceeded\n");
    /* we want the Dpc on the end of the queue. By definition we are already on the right CPU so we know the Dpc queue will be run immediately */
//    KeSetImportanceDpc(&xi->rxtx_dpc, MediumImportance);
    KeInsertQueueDpc(&xi->rxtx_dpc, NULL, NULL);
    /* dont set an event in TX path */
    dont_set_event = TRUE;
  }
  else
  {
    /* make sure the Dpc queue is run immediately next interrupt */
//    KeSetImportanceDpc(&xi->rxtx_dpc, HighImportance);
    /* set an event in TX path */
    dont_set_event = FALSE;
  }

  /* make packets out of the buffers */
  page_buf = head_buf;
  extra_info_flag = FALSE;
  more_data_flag = FALSE;

  while (page_buf) {
    shared_buffer_t *next_buf = page_buf->next;
    PMDL mdl;

    page_buf->next = NULL;
    if (extra_info_flag) {
      //KdPrint((__DRIVER_NAME "     processing extra info\n"));
      ei = (struct netif_extra_info *)&page_buf->rsp;
      extra_info_flag = ei->flags & XEN_NETIF_EXTRA_FLAG_MORE;
      switch (ei->type)
      {
      case XEN_NETIF_EXTRA_TYPE_GSO:
        switch (ei->u.gso.type) {
        case XEN_NETIF_GSO_TYPE_TCPV4:
          pi->mss = ei->u.gso.size;
          // TODO - put this assertion somewhere XN_ASSERT(header_len + pi->mss <= PAGE_SIZE); // this limits MTU to PAGE_SIZE - XN_HEADER_LEN
          break;
        default:
          FUNCTION_MSG("Unknown GSO type (%d) detected\n", ei->u.gso.type);
          break;
        }
        break;
      default:
        FUNCTION_MSG("Unknown extra info type (%d) detected\n", ei->type);
        break;
      }
      put_pb_on_freelist(xi, page_buf);
    } else {
      XN_ASSERT(!page_buf->rsp.offset);
      if (!more_data_flag) { // handling the packet's 1st buffer
        if (page_buf->rsp.flags & NETRXF_csum_blank)
          pi->csum_blank = TRUE;
        if (page_buf->rsp.flags & NETRXF_data_validated)
          pi->data_validated = TRUE;
      }
      mdl = page_buf->mdl;
      mdl->ByteCount = page_buf->rsp.status; //NdisAdjustBufferLength(mdl, page_buf->rsp.status);
      //KdPrint((__DRIVER_NAME "     buffer = %p, pb = %p\n", buffer, page_buf));
      if (pi->first_pb) {
        XN_ASSERT(pi->curr_pb);
        //KdPrint((__DRIVER_NAME "     additional buffer\n"));
        pi->curr_pb->next = page_buf;
        pi->curr_pb = page_buf;
        XN_ASSERT(pi->curr_mdl);
        pi->curr_mdl->Next = mdl;
        pi->curr_mdl = mdl;
      } else {
        pi->first_pb = page_buf;
        pi->curr_pb = page_buf;
        pi->first_mdl = mdl;
        pi->curr_mdl = mdl;
      }
      //pi->mdl_count++;
      extra_info_flag = (BOOLEAN)(page_buf->rsp.flags & NETRXF_extra_info);
      more_data_flag = (BOOLEAN)(page_buf->rsp.flags & NETRXF_more_data);
      pi->total_length = pi->total_length + page_buf->rsp.status;
    }

    /* Packet done, add it to the list */
    if (!more_data_flag && !extra_info_flag) {
      pi->curr_pb = pi->first_pb;
      pi->curr_mdl = pi->first_mdl;
      XenNet_MakePackets(xi, &rc, pi);
    }

    page_buf = next_buf;
  }
  XN_ASSERT(!more_data_flag && !extra_info_flag);

  #if NTDDI_VERSION < NTDDI_VISTA
  packet_count = 0;
  first_header_only_packet = NULL;
  last_header_only_packet = NULL;

  while (rc.first_packet) {
    PNDIS_PACKET packet;
    NDIS_STATUS status;

    packet = rc.first_packet;
    XN_ASSERT(PACKET_FIRST_PB(packet));
    rc.first_packet = PACKET_NEXT_PACKET(packet);
    status = NDIS_GET_PACKET_STATUS(packet);
    if (status == NDIS_STATUS_RESOURCES) {
      if (!first_header_only_packet) {
        first_header_only_packet = packet;
      } else {
        PACKET_NEXT_PACKET(last_header_only_packet) = packet;
      }
      last_header_only_packet = packet;
      PACKET_NEXT_PACKET(packet) = NULL;
    }
    packets[packet_count++] = packet;
    /* if we indicate a packet with NDIS_STATUS_RESOURCES then any following packet can't be NDIS_STATUS_SUCCESS */
    if (packet_count == MAXIMUM_PACKETS_PER_INDICATE || !rc.first_packet
        || (NDIS_GET_PACKET_STATUS(rc.first_packet) == NDIS_STATUS_SUCCESS
        && status == NDIS_STATUS_RESOURCES)) {
      NdisMIndicateReceivePacket(xi->adapter_handle, packets, packet_count);
      packet_count = 0;
    }
  }
  /* now return the packets for which we indicated NDIS_STATUS_RESOURCES */
  while (first_header_only_packet) {
    PNDIS_PACKET packet = first_header_only_packet;
    first_header_only_packet = PACKET_NEXT_PACKET(packet);
    XenNet_ReturnPacket(xi, packet);
  }
  #else
  if (rc.first_nbl) {
    NdisMIndicateReceiveNetBufferLists(xi->adapter_handle, rc.first_nbl,
      NDIS_DEFAULT_PORT_NUMBER, rc.nbl_count,
      NDIS_RECEIVE_FLAGS_DISPATCH_LEVEL
      //| NDIS_RECEIVE_FLAGS_SINGLE_ETHER_TYPE 
      | NDIS_RECEIVE_FLAGS_PERFECT_FILTERED);
  }
  #endif
  //FUNCTION_EXIT();
  return dont_set_event;
}

static VOID
XenNet_BufferFree(xennet_info_t *xi)
{
  shared_buffer_t *sb;
  int i;

  for (i = 0; i < NET_RX_RING_SIZE; i++) {
    if (xi->rx_ring_pbs[i] != NULL) {
      put_pb_on_freelist(xi, xi->rx_ring_pbs[i]);
      xi->rx_ring_pbs[i] = NULL;
    }
  }

  /* because we are shutting down this won't allocate new ones */
  while ((sb = get_pb_from_freelist(xi)) != NULL) {
    XnEndAccess(xi->handle,
        sb->gref, FALSE, (ULONG)'XNRX');
    IoFreeMdl(sb->mdl);
    ExFreePoolWithTag(sb->virtual, XENNET_POOL_TAG);
    ExFreePoolWithTag(sb, XENNET_POOL_TAG);
  }
  while ((sb = get_hb_from_freelist(xi)) != NULL) {
    IoFreeMdl(sb->mdl);
    ExFreePoolWithTag(sb, XENNET_POOL_TAG);
  }
}

BOOLEAN
XenNet_RxInit(xennet_info_t *xi) {
  #if NTDDI_VERSION < NTDDI_VISTA
  NDIS_STATUS status;
  #else
  NET_BUFFER_LIST_POOL_PARAMETERS nbl_pool_parameters;
  NET_BUFFER_POOL_PARAMETERS nb_pool_parameters;
  #endif
  int ret;
  int i;
  
  FUNCTION_ENTER();

  // this stuff needs to be done once only...
  KeInitializeSpinLock(&xi->rx_lock);
  KeInitializeEvent(&xi->rx_idle_event, SynchronizationEvent, FALSE);
  xi->rxpi = ExAllocatePoolWithTagPriority(NonPagedPool, sizeof(packet_info_t) * NdisSystemProcessorCount(), XENNET_POOL_TAG, NormalPoolPriority);
  if (!xi->rxpi) {
    FUNCTION_MSG("ExAllocatePoolWithTagPriority failed\n");
    return FALSE;
  }
  NdisZeroMemory(xi->rxpi, sizeof(packet_info_t) * NdisSystemProcessorCount());

  ret = stack_new(&xi->rx_pb_stack, NET_RX_RING_SIZE * 4);
  if (!ret) {
    FUNCTION_MSG("Failed to allocate rx_pb_stack\n");
    ExFreePoolWithTag(xi->rxpi, XENNET_POOL_TAG);
    return FALSE;
  }
  ret = stack_new(&xi->rx_hb_stack, NET_RX_RING_SIZE * 4);
  if (!ret) {
    FUNCTION_MSG("Failed to allocate rx_hb_stack\n");
    stack_delete(xi->rx_pb_stack, NULL, NULL);
    ExFreePoolWithTag(xi->rxpi, XENNET_POOL_TAG);
    return FALSE;
  }

  xi->rx_id_free = NET_RX_RING_SIZE;
  xi->rx_outstanding = 0;

  for (i = 0; i < NET_RX_RING_SIZE; i++) {
    xi->rx_ring_pbs[i] = NULL;
  }
  
  #if NTDDI_VERSION < NTDDI_VISTA
  NdisAllocatePacketPool(&status, &xi->rx_packet_pool, NET_RX_RING_SIZE * 4, PROTOCOL_RESERVED_SIZE_IN_PACKET);
  if (status != NDIS_STATUS_SUCCESS) {
    FUNCTION_MSG("NdisAllocatePacketPool failed with 0x%x\n", status);
    return FALSE;
  }
  #else
  nbl_pool_parameters.Header.Type = NDIS_OBJECT_TYPE_DEFAULT;
  nbl_pool_parameters.Header.Revision = NET_BUFFER_LIST_POOL_PARAMETERS_REVISION_1;
  nbl_pool_parameters.Header.Size = NDIS_SIZEOF_NET_BUFFER_LIST_POOL_PARAMETERS_REVISION_1;
  nbl_pool_parameters.ProtocolId = NDIS_PROTOCOL_ID_DEFAULT;
  nbl_pool_parameters.fAllocateNetBuffer = FALSE;
  nbl_pool_parameters.ContextSize = 0;
  nbl_pool_parameters.PoolTag = XENNET_POOL_TAG;
  nbl_pool_parameters.DataSize = 0; /* NET_BUFFERS are always allocated separately */
  
  xi->rx_nbl_pool = NdisAllocateNetBufferListPool(xi->adapter_handle, &nbl_pool_parameters);
  if (!xi->rx_nbl_pool) {
    FUNCTION_MSG("NdisAllocateNetBufferListPool failed\n");
    return FALSE;
  }

  nb_pool_parameters.Header.Type = NDIS_OBJECT_TYPE_DEFAULT;
  nb_pool_parameters.Header.Revision = NET_BUFFER_POOL_PARAMETERS_REVISION_1;
  nb_pool_parameters.Header.Size = NDIS_SIZEOF_NET_BUFFER_POOL_PARAMETERS_REVISION_1;
  nb_pool_parameters.PoolTag = XENNET_POOL_TAG;
  nb_pool_parameters.DataSize = 0; /* the buffers come from the ring */
  xi->rx_packet_pool = NdisAllocateNetBufferPool(xi->adapter_handle, &nb_pool_parameters);
  if (!xi->rx_packet_pool) {
    FUNCTION_MSG("NdisAllocateNetBufferPool (rx_packet_pool) failed\n");
    return FALSE;
  }
  #endif
  XenNet_FillRing(xi);

  FUNCTION_EXIT();

  return TRUE;
}

VOID
XenNet_RxShutdown(xennet_info_t *xi) {
  KIRQL old_irql;
  UNREFERENCED_PARAMETER(xi);  

  FUNCTION_ENTER();

  KeAcquireSpinLock(&xi->rx_lock, &old_irql);
  while (xi->rx_outstanding) {
    FUNCTION_MSG("Waiting for %d packets to be returned\n", xi->rx_outstanding);
    KeReleaseSpinLock(&xi->rx_lock, old_irql);
    KeWaitForSingleObject(&xi->rx_idle_event, Executive, KernelMode, FALSE, NULL);
    KeAcquireSpinLock(&xi->rx_lock, &old_irql);
  }
  KeReleaseSpinLock(&xi->rx_lock, old_irql);
  
  XenNet_BufferFree(xi);

  stack_delete(xi->rx_pb_stack, NULL, NULL);
  stack_delete(xi->rx_hb_stack, NULL, NULL);
  

  ExFreePoolWithTag(xi->rxpi, XENNET_POOL_TAG);

  #if NTDDI_VERSION < NTDDI_VISTA
  NdisFreePacketPool(xi->rx_packet_pool);
  #else
  NdisFreeNetBufferPool(xi->rx_packet_pool);
  NdisFreeNetBufferListPool(xi->rx_nbl_pool);
  #endif

  FUNCTION_EXIT();
  return;
}
