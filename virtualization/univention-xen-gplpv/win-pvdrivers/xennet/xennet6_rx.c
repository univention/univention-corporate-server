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
  if (xi->shutting_down)
    return NULL;
    
  pb = NdisAllocateMemoryWithTagPriority(xi->adapter_handle, sizeof(shared_buffer_t), XENNET_POOL_TAG, LowPoolPriority);
  if (!pb)
    return NULL;
  pb->virtual = NdisAllocateMemoryWithTagPriority(xi->adapter_handle, PAGE_SIZE, XENNET_POOL_TAG, LowPoolPriority);
  if (!pb->virtual)
  {
    NdisFreeMemory(pb, sizeof(shared_buffer_t), 0);
    return NULL;
  }
  pb->mdl = IoAllocateMdl(pb->virtual, PAGE_SIZE, FALSE, FALSE, NULL);
  if (!pb->mdl)
  {
    NdisFreeMemory(pb, PAGE_SIZE, 0);
    NdisFreeMemory(pb->virtual, sizeof(shared_buffer_t), 0);
    return NULL;
  }
  pb->gref = (grant_ref_t)xi->vectors.GntTbl_GrantAccess(xi->vectors.context, 0,
            (ULONG)(MmGetPhysicalAddress(pb->virtual).QuadPart >> PAGE_SHIFT), FALSE, INVALID_GRANT_REF, (ULONG)'XNRX');
  if (pb->gref == INVALID_GRANT_REF)
  {
    IoFreeMdl(pb->mdl);
    NdisFreeMemory(pb, PAGE_SIZE, 0);
    NdisFreeMemory(pb->virtual, sizeof(shared_buffer_t), 0);
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
  if (xi->shutting_down)
    return NULL;
    
  hb = NdisAllocateMemoryWithTagPriority(xi->adapter_handle, sizeof(shared_buffer_t) + MAX_ETH_HEADER_LENGTH + MAX_LOOKAHEAD_LENGTH, XENNET_POOL_TAG, LowPoolPriority);
  if (!hb)
    return NULL;
  NdisZeroMemory(hb, sizeof(shared_buffer_t));
  hb->mdl = IoAllocateMdl(hb + 1, MAX_ETH_HEADER_LENGTH + MAX_LOOKAHEAD_LENGTH, FALSE, FALSE, NULL);
  if (!hb->mdl)
  {
    NdisFreeMemory(hb, sizeof(shared_buffer_t) + MAX_ETH_HEADER_LENGTH + MAX_LOOKAHEAD_LENGTH, 0);
    return NULL;
  }
  MmBuildMdlForNonPagedPool(hb->mdl);
  return hb;
}

static __inline VOID
put_hb_on_freelist(struct xennet_info *xi, shared_buffer_t *hb)
{
  ASSERT(xi);
  hb->mdl->ByteCount = sizeof(shared_buffer_t) + MAX_ETH_HEADER_LENGTH + MAX_LOOKAHEAD_LENGTH;
  hb->mdl->Next = NULL;
  hb->next = NULL;
  stack_push(xi->rx_hb_stack, hb);
  InterlockedIncrement(&xi->rx_hb_free);
}

// Called at DISPATCH_LEVEL with rx lock held
static NDIS_STATUS
XenNet_FillRing(struct xennet_info *xi)
{
  unsigned short id;
  shared_buffer_t *page_buf;
  ULONG i, notify;
  ULONG batch_target;
  RING_IDX req_prod = xi->rx.req_prod_pvt;
  netif_rx_request_t *req;

  //FUNCTION_ENTER();

  batch_target = xi->rx_target - (req_prod - xi->rx.rsp_cons);

  if (batch_target < (xi->rx_target >> 2))
  {
    //FUNCTION_EXIT();
    return NDIS_STATUS_SUCCESS; /* only refill if we are less than 3/4 full already */
  }

  for (i = 0; i < batch_target; i++)
  {
    page_buf = get_pb_from_freelist(xi);
    if (!page_buf)
    {
      KdPrint((__DRIVER_NAME "     Added %d out of %d buffers to rx ring (no free pages)\n", i, batch_target));
      break;
    }
    xi->rx_id_free--;

    /* Give to netback */
    id = (USHORT)((req_prod + i) & (NET_RX_RING_SIZE - 1));
    ASSERT(xi->rx_ring_pbs[id] == NULL);
    xi->rx_ring_pbs[id] = page_buf;
    req = RING_GET_REQUEST(&xi->rx, req_prod + i);
    req->id = id;
    req->gref = page_buf->gref;
    ASSERT(req->gref != INVALID_GRANT_REF);
  }
  KeMemoryBarrier();
  xi->rx.req_prod_pvt = req_prod + i;
  RING_PUSH_REQUESTS_AND_CHECK_NOTIFY(&xi->rx, notify);
  if (notify)
  {
    xi->vectors.EvtChn_Notify(xi->vectors.context, xi->event_channel);
  }

  //FUNCTION_EXIT();

  return NDIS_STATUS_SUCCESS;
}

typedef struct {
  PNET_BUFFER_LIST first_nbl;
  PNET_BUFFER_LIST last_nbl;
  ULONG packet_count;
} rx_context_t;

static BOOLEAN
XenNet_MakePacket(struct xennet_info *xi, rx_context_t *rc, packet_info_t *pi)
{
  PNET_BUFFER_LIST nbl;
  PNET_BUFFER nb;
  PMDL mdl_head, mdl_tail, curr_mdl;
  PUCHAR header_va;
  ULONG out_remaining;
  ULONG header_extra;
  shared_buffer_t *header_buf;
  NDIS_TCP_IP_CHECKSUM_NET_BUFFER_LIST_INFO csum_info;

  //FUNCTION_ENTER();
  
  nbl = NdisAllocateNetBufferList(xi->rx_nbl_pool, 0, 0);
  if (!nbl)
  {
    /* buffers will be freed in MakePackets */
    KdPrint((__DRIVER_NAME "     No free nbl's\n"));
    //FUNCTION_EXIT();
    return FALSE;
  }

  nb = NdisAllocateNetBuffer(xi->rx_nb_pool, NULL, 0, 0);
  if (!nb)
  {
    KdPrint((__DRIVER_NAME "     No free nb's\n"));
    NdisFreeNetBufferList(nbl);
    //FUNCTION_EXIT();
    return FALSE;
  }

  header_buf = get_hb_from_freelist(xi);
  if (!header_buf)
  {
    KdPrint((__DRIVER_NAME "     No free header buffers\n"));
    NdisFreeNetBufferList(nbl);
    NdisFreeNetBuffer(nb);
    //FUNCTION_EXIT();
    return FALSE;
  }
  header_va = (PUCHAR)(header_buf + 1);
  NdisMoveMemory(header_va, pi->header, pi->header_length);
  //KdPrint((__DRIVER_NAME "     header_length = %d, current_lookahead = %d\n", pi->header_length, xi->current_lookahead));
  //KdPrint((__DRIVER_NAME "     ip4_header_length = %d\n", pi->ip4_header_length));
  //KdPrint((__DRIVER_NAME "     tcp_header_length = %d\n", pi->tcp_header_length));
  /* make sure we satisfy the lookahead requirement */
  if (pi->split_required)
  {
    /* for split packets we need to make sure the 'header' is no bigger than header+mss bytes */
    XenNet_BuildHeader(pi, header_va, min((ULONG)MAX_ETH_HEADER_LENGTH + pi->ip4_header_length + pi->tcp_header_length + pi->mss, MAX_ETH_HEADER_LENGTH + max(MIN_LOOKAHEAD_LENGTH, xi->current_lookahead)));
  }
  else
  {
    XenNet_BuildHeader(pi, header_va, max(MIN_LOOKAHEAD_LENGTH, xi->current_lookahead) + MAX_ETH_HEADER_LENGTH);
  }
  header_extra = pi->header_length - (MAX_ETH_HEADER_LENGTH + pi->ip4_header_length + pi->tcp_header_length);
  ASSERT(pi->header_length <= MAX_ETH_HEADER_LENGTH + MAX_LOOKAHEAD_LENGTH);
  header_buf->mdl->ByteCount = pi->header_length;
  mdl_head = mdl_tail = curr_mdl = header_buf->mdl;
  NB_HEADER_BUF(nb) = header_buf;
  header_buf->next = pi->curr_pb;
  NET_BUFFER_FIRST_MDL(nb) = mdl_head;
  NET_BUFFER_CURRENT_MDL(nb) = mdl_head;
  NET_BUFFER_CURRENT_MDL_OFFSET(nb) = 0;
  NET_BUFFER_DATA_OFFSET(nb) = 0;
  NET_BUFFER_DATA_LENGTH(nb) = pi->header_length;

  // TODO: if there are only a few bytes left on the first buffer then add them to the header buffer too... maybe

  if (pi->split_required)
  {
    ULONG tcp_length;
    USHORT new_ip4_length;
    tcp_length = (USHORT)min(pi->mss, pi->tcp_remaining);
    new_ip4_length = (USHORT)(pi->ip4_header_length + pi->tcp_header_length + tcp_length);
    //KdPrint((__DRIVER_NAME "     new_ip4_length = %d\n", new_ip4_length));
    //KdPrint((__DRIVER_NAME "     this tcp_length = %d\n", tcp_length));
    SET_NET_USHORT(&header_va[XN_HDR_SIZE + 2], new_ip4_length);
    SET_NET_ULONG(&header_va[XN_HDR_SIZE + pi->ip4_header_length + 4], pi->tcp_seq);
    pi->tcp_seq += tcp_length;
    pi->tcp_remaining = (USHORT)(pi->tcp_remaining - tcp_length);
    /* part of the packet is already present in the header buffer for lookahead */
    out_remaining = tcp_length - header_extra;
    ASSERT((LONG)out_remaining >= 0);
  }
  else
  {
    out_remaining = pi->total_length - pi->header_length;
    ASSERT((LONG)out_remaining >= 0);
  }
  //KdPrint((__DRIVER_NAME "     before loop - out_remaining = %d\n", out_remaining));

  while (out_remaining != 0)
  {
    //ULONG in_buffer_offset;
    ULONG in_buffer_length;
    ULONG out_length;
    
    //KdPrint((__DRIVER_NAME "     in loop - out_remaining = %d, curr_buffer = %p, curr_pb = %p\n", out_remaining, pi->curr_mdl, pi->curr_pb));
    if (!pi->curr_mdl || !pi->curr_pb)
    {
      KdPrint((__DRIVER_NAME "     out of buffers for packet\n"));
      //KdPrint((__DRIVER_NAME "     out_remaining = %d, curr_buffer = %p, curr_pb = %p\n", out_remaining, pi->curr_mdl, pi->curr_pb));
      // TODO: free some stuff or we'll leak
      /* unchain buffers then free packet */
      //FUNCTION_EXIT();
      return FALSE;
    }

    in_buffer_length = MmGetMdlByteCount(pi->curr_mdl);
    out_length = min(out_remaining, in_buffer_length - pi->curr_mdl_offset);
    curr_mdl = IoAllocateMdl((PUCHAR)MmGetMdlVirtualAddress(pi->curr_mdl) + pi->curr_mdl_offset, out_length, FALSE, FALSE, NULL);
    ASSERT(curr_mdl);
    IoBuildPartialMdl(pi->curr_mdl, curr_mdl, (PUCHAR)MmGetMdlVirtualAddress(pi->curr_mdl) + pi->curr_mdl_offset, out_length);
    mdl_tail->Next = curr_mdl;
    mdl_tail = curr_mdl;
    curr_mdl->Next = NULL; /* I think this might be redundant */
    NET_BUFFER_DATA_LENGTH(nb) += out_length;
    ref_pb(xi, pi->curr_pb);
    pi->curr_mdl_offset = (USHORT)(pi->curr_mdl_offset + out_length);
    if (pi->curr_mdl_offset == in_buffer_length)
    {
      pi->curr_mdl = pi->curr_mdl->Next;
      pi->curr_pb = pi->curr_pb->next;
      pi->curr_mdl_offset = 0;
    }
    out_remaining -= out_length;
  }
  if (pi->split_required)
  {
    // TODO: only if Ip checksum is disabled...
    //XenNet_SumIpHeader(header_va, pi->ip4_header_length);
  }
  if (header_extra > 0)
    pi->header_length -= header_extra;
  //ASSERT(*(shared_buffer_t **)&packet->MiniportReservedEx[0]);
  
  rc->packet_count++;
  NET_BUFFER_LIST_FIRST_NB(nbl) = nb;
  //NET_BUFFER_NEXT_NB(nb) = NULL; /*is this already done for me? */

  if (pi->parse_result == PARSE_OK)
  {
    BOOLEAN checksum_offload = FALSE;
    csum_info.Value = 0;
    if (pi->csum_blank || pi->data_validated || pi->mss)
    {
      if (pi->ip_proto == 6) // && xi->setting_csum.V4Receive.TcpChecksum)
      {
//          if (!pi->tcp_has_options || xi->setting_csum.V4Receive.TcpOptionsSupported)
//          {
          csum_info.Receive.IpChecksumSucceeded = TRUE;
          csum_info.Receive.TcpChecksumSucceeded = TRUE;
          checksum_offload = TRUE;
//          }
      }
      else if (pi->ip_proto == 17) // &&xi->setting_csum.V4Receive.UdpChecksum)
      {
        csum_info.Receive.IpChecksumSucceeded = TRUE;
        csum_info.Receive.UdpChecksumSucceeded = TRUE;
        checksum_offload = TRUE;
      }
    }
    NET_BUFFER_LIST_INFO(nbl, TcpIpChecksumNetBufferListInfo) = csum_info.Value;
  }
  
  //packet_count += NBL_PACKET_COUNT(nbl);
  if (!rc->first_nbl)
  {
    rc->first_nbl = nbl;
  }
  else
  {
    NET_BUFFER_LIST_NEXT_NBL(rc->last_nbl) = nbl;
  }
  rc->last_nbl = nbl;
  NET_BUFFER_LIST_NEXT_NBL(nbl) = NULL;
  InterlockedIncrement(&xi->rx_outstanding);
  if (pi->is_multicast)
  {
    /* multicast */
    xi->stats.ifHCInMulticastPkts++;
    xi->stats.ifHCInMulticastOctets += NET_BUFFER_DATA_LENGTH(nb);
  }
  else if (pi->is_broadcast)
  {
    /* broadcast */
    xi->stats.ifHCInBroadcastPkts++;
    xi->stats.ifHCInBroadcastOctets += NET_BUFFER_DATA_LENGTH(nb);
  }
  else
  {
    /* unicast */
    xi->stats.ifHCInUcastPkts++;
    xi->stats.ifHCInUcastOctets += NET_BUFFER_DATA_LENGTH(nb);
  }
  //FUNCTION_EXIT();
  return TRUE;
}

#if 0
/*
 Windows appears to insist that the checksum on received packets is correct, and won't
 believe us when we lie about it, which happens when the packet is generated on the
 same bridge in Dom0. Doh!
 This is only for TCP and UDP packets. IP checksums appear to be correct anyways.
*/

static BOOLEAN
XenNet_SumPacketData(
  packet_info_t *pi,
  PNDIS_PACKET packet,
  BOOLEAN set_csum
)
{
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
  
  //FUNCTION_ENTER();

  NdisGetFirstBufferFromPacketSafe(packet, &mdl, &buffer, &buffer_length, &total_length, NormalPagePriority);
  ASSERT(mdl);

  ip4_length = GET_NET_PUSHORT(&buffer[XN_HDR_SIZE + 2]);
  data_length = ip4_length + XN_HDR_SIZE;
  
  if ((USHORT)data_length > total_length)
  {
    KdPrint((__DRIVER_NAME "     Size Mismatch %d (ip4_length + XN_HDR_SIZE) != %d (total_length)\n", ip4_length + XN_HDR_SIZE, total_length));
    return FALSE;
  }

  switch (pi->ip_proto)
  {
  case 6:
    ASSERT(buffer_length >= (USHORT)(XN_HDR_SIZE + pi->ip4_header_length + 17));
    csum_ptr = (USHORT *)&buffer[XN_HDR_SIZE + pi->ip4_header_length + 16];
    break;
  case 17:
    ASSERT(buffer_length >= (USHORT)(XN_HDR_SIZE + pi->ip4_header_length + 7));
    csum_ptr = (USHORT *)&buffer[XN_HDR_SIZE + pi->ip4_header_length + 6];
    break;
  default:
    KdPrint((__DRIVER_NAME "     Don't know how to calc sum for IP Proto %d\n", pi->ip_proto));
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
  while (i < data_length)
  {
    /* don't include the checksum field itself in the calculation */
    if ((pi->ip_proto == 6 && i == XN_HDR_SIZE + pi->ip4_header_length + 16) || (pi->ip_proto == 17 && i == XN_HDR_SIZE + pi->ip4_header_length + 6))
    {
      /* we know that this always happens in the header buffer so we are guaranteed the full two bytes */
      i += 2;
      buffer_offset += 2;
      continue;
    }
    if (csum_span)
    {
      /* the other half of the next bit */
      ASSERT(buffer_offset == 0);
      csum += (USHORT)buffer[buffer_offset];
      csum_span = FALSE;
      i += 1;
      buffer_offset += 1;
    }
    else if (buffer_offset == buffer_length - 1)
    {
      /* deal with a buffer ending on an odd byte boundary */
      csum += (USHORT)buffer[buffer_offset] << 8;
      csum_span = TRUE;
      i += 1;
      buffer_offset += 1;
    }
    else
    {
      csum += GET_NET_PUSHORT(&buffer[buffer_offset]);
      i += 2;
      buffer_offset += 2;
    }
    if (buffer_offset == buffer_length && i < total_length)
    {
      NdisGetNextBuffer(mdl, &mdl);
      if (mdl == NULL)
      {
        KdPrint((__DRIVER_NAME "     Ran out of buffers\n"));
        return FALSE; // should never happen
      }
      NdisQueryBufferSafe(mdl, &buffer, &buffer_length, NormalPagePriority);
      ASSERT(buffer_length);
      buffer_offset = 0;
    }
  }
      
  while (csum & 0xFFFF0000)
    csum = (csum & 0xFFFF) + (csum >> 16);
  
  if (set_csum)
  {
    *csum_ptr = (USHORT)~GET_NET_USHORT((USHORT)csum);
  }
  else
  {
    //FUNCTION_EXIT();
    return (BOOLEAN)(*csum_ptr == (USHORT)~GET_NET_USHORT((USHORT)csum));
  }
  //FUNCTION_EXIT();
  return TRUE;
}
#endif

static VOID
XenNet_MakePackets(struct xennet_info *xi, rx_context_t *rc, packet_info_t *pi)
{
  UCHAR psh;
  //PNDIS_BUFFER buffer;
  shared_buffer_t *page_buf;

  //FUNCTION_ENTER();

  XenNet_ParsePacketHeader(pi, NULL, 0);
  //pi->split_required = FALSE;

  if (!XenNet_FilterAcceptPacket(xi, pi))
  {
    goto done;
  }

  if (pi->split_required)
  {
    switch (xi->current_gso_rx_split_type)
    {
    case RX_LSO_SPLIT_HALF:
      pi->mss = (pi->tcp_length + 1) / 2;
      break;
    case RX_LSO_SPLIT_NONE:
      pi->mss = 65535;
      break;
    }
  }

  switch (pi->ip_proto)
  {
  case 6:  // TCP
    if (pi->split_required)
      break;
    /* fall through */
  case 17:  // UDP
    if (!XenNet_MakePacket(xi, rc, pi))
    {
      KdPrint((__DRIVER_NAME "     Ran out of packets\n"));
      xi->stats.ifInDiscards++;
      goto done;
    }
    goto done;
  default:
    if (!XenNet_MakePacket(xi, rc, pi))
    {
      KdPrint((__DRIVER_NAME "     Ran out of packets\n"));
      xi->stats.ifInDiscards++;
      goto done;
    }
    goto done;
  }

  /* this is the split_required code */
  pi->tcp_remaining = pi->tcp_length;

  /* we can make certain assumptions here as the following code is only for tcp4 */
  psh = pi->header[XN_HDR_SIZE + pi->ip4_header_length + 13] & 8;
  while (pi->tcp_remaining)
  {
    if (!XenNet_MakePacket(xi, rc, pi))
    {
      KdPrint((__DRIVER_NAME "     Ran out of packets\n"));
      xi->stats.ifInDiscards++;
      break; /* we are out of memory - just drop the packets */
    }
    if (psh)
    {
      //NdisGetFirstBufferFromPacketSafe(packet, &mdl, &header_va, &buffer_length, &total_length, NormalPagePriority);
      if (pi->tcp_remaining)
        pi->header[XN_HDR_SIZE + pi->ip4_header_length + 13] &= ~8;
      else
        pi->header[XN_HDR_SIZE + pi->ip4_header_length + 13] |= 8;
    }
    //XenNet_SumPacketData(pi, packet, TRUE);
    //entry = (PLIST_ENTRY)&packet->MiniportReservedEx[sizeof(PVOID)];
    //InsertTailList(rx_packet_list, entry);
  }
done:
  page_buf = pi->first_pb;
  while (page_buf)
  {
    shared_buffer_t *next_pb = page_buf->next;
    put_pb_on_freelist(xi, page_buf); /* this doesn't actually free the page_puf if there are outstanding references */
    page_buf = next_pb;
  }
  XenNet_ClearPacketInfo(pi);
  //FUNCTION_EXIT();
  return;
}

/* called at <= DISPATCH_LEVEL */
/* it's okay for return packet to be called while resume_state != RUNNING as the packet will simply be added back to the freelist, the grants will be fixed later */
VOID
XenNet_ReturnNetBufferLists(NDIS_HANDLE adapter_context, PNET_BUFFER_LIST curr_nbl, ULONG return_flags)
{
  struct xennet_info *xi = adapter_context;
  UNREFERENCED_PARAMETER(return_flags);

  //FUNCTION_ENTER();

  //KdPrint((__DRIVER_NAME "     page_buf = %p\n", page_buf));

  ASSERT(xi);
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
      page_buf = NB_HEADER_BUF(curr_nb);
      while (curr_mdl)
      {
        shared_buffer_t *next_buf;
        PMDL next_mdl;
        
        ASSERT(page_buf); /* make sure that there is a pb to match this mdl */
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
  
  if (!xi->rx_outstanding && xi->rx_shutting_down)
    KeSetEvent(&xi->packet_returned_event, IO_NO_INCREMENT, FALSE);

  //FUNCTION_EXIT();
}

/* We limit the number of packets per interrupt so that acks get a chance
under high rx load. The DPC is immediately re-scheduled */
//#define MAXIMUM_PACKETS_PER_INTERRUPT 32 /* this is calculated before large packet split */
//#define MAXIMUM_DATA_PER_INTERRUPT (MAXIMUM_PACKETS_PER_INTERRUPT * 1500) /* help account for large packets */

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
  //LIST_ENTRY rx_header_only_packet_list;
  //PLIST_ENTRY entry;
  ULONG nbl_count = 0;
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

  if (!xi->connected)
    return FALSE; /* a delayed DPC could let this come through... just do nothing */

  rc.first_nbl = NULL;
  rc.last_nbl = NULL;
  rc.packet_count = 0;
  
  /* get all the buffers off the ring as quickly as possible so the lock is held for a minimum amount of time */
  KeAcquireSpinLockAtDpcLevel(&xi->rx_lock);
  
  if (xi->rx_shutting_down)
  {
    /* there is a chance that our Dpc had been queued just before the shutdown... */
    KeReleaseSpinLockFromDpcLevel(&xi->rx_lock);
    return FALSE;
  }

  if (xi->rx_partial_buf)
  {
    head_buf = xi->rx_partial_buf;
    tail_buf = xi->rx_partial_buf;
    while (tail_buf->next)
      tail_buf = tail_buf->next;
    more_data_flag = xi->rx_partial_more_data_flag;
    extra_info_flag = xi->rx_partial_extra_info_flag;
    xi->rx_partial_buf = NULL;
  }

  do {
    prod = xi->rx.sring->rsp_prod;
    KeMemoryBarrier(); /* Ensure we see responses up to 'prod'. */

    for (cons = xi->rx.rsp_cons; cons != prod && packet_count < MAXIMUM_PACKETS_PER_INTERRUPT && packet_data < MAXIMUM_DATA_PER_INTERRUPT; cons++)
    {
      id = (USHORT)(cons & (NET_RX_RING_SIZE - 1));
      page_buf = xi->rx_ring_pbs[id];
      ASSERT(page_buf);
      xi->rx_ring_pbs[id] = NULL;
      xi->rx_id_free++;
      memcpy(&page_buf->rsp, RING_GET_RESPONSE(&xi->rx, cons), max(sizeof(struct netif_rx_response), sizeof(struct netif_extra_info)));
      if (!extra_info_flag)
      {
        if (page_buf->rsp.status <= 0
          || page_buf->rsp.offset + page_buf->rsp.status > PAGE_SIZE)
        {
          KdPrint((__DRIVER_NAME "     Error: rsp offset %d, size %d\n",
            page_buf->rsp.offset, page_buf->rsp.status));
          ASSERT(!extra_info_flag);
          put_pb_on_freelist(xi, page_buf);
          continue;
        }
      }
      
      if (!head_buf)
      {
        head_buf = page_buf;
        tail_buf = page_buf;
      }
      else
      {
        tail_buf->next = page_buf;
        tail_buf = page_buf;
      }
      page_buf->next = NULL;

      if (extra_info_flag)
      {
        ei = (struct netif_extra_info *)&page_buf->rsp;
        extra_info_flag = ei->flags & XEN_NETIF_EXTRA_FLAG_MORE;
      }
      else
      {
        more_data_flag = (BOOLEAN)(page_buf->rsp.flags & NETRXF_more_data);
        extra_info_flag = (BOOLEAN)(page_buf->rsp.flags & NETRXF_extra_info);
        interim_packet_data += page_buf->rsp.status;
      }
      
      if (!extra_info_flag && !more_data_flag)
      {
        last_buf = page_buf;
        packet_count++;
        packet_data += interim_packet_data;
        interim_packet_data = 0;
        }
      buffer_count++;
    }
    xi->rx.rsp_cons = cons;

    /* Give netback more buffers */
    XenNet_FillRing(xi);

    if (packet_count >= MAXIMUM_PACKETS_PER_INTERRUPT || packet_data >= MAXIMUM_DATA_PER_INTERRUPT)
      break;

    more_to_do = RING_HAS_UNCONSUMED_RESPONSES(&xi->rx);
    if (!more_to_do)
    {
      xi->rx.sring->rsp_event = xi->rx.rsp_cons + 1;
      KeMemoryBarrier();
      more_to_do = RING_HAS_UNCONSUMED_RESPONSES(&xi->rx);
    }
  } while (more_to_do);
  
  /* anything past last_buf belongs to an incomplete packet... */
  if (last_buf && last_buf->next)
  {
    KdPrint((__DRIVER_NAME "     Partial receive\n"));
    xi->rx_partial_buf = last_buf->next;
    xi->rx_partial_more_data_flag = more_data_flag;
    xi->rx_partial_extra_info_flag = extra_info_flag;
    last_buf->next = NULL;
  }

  KeReleaseSpinLockFromDpcLevel(&xi->rx_lock);

  if (packet_count >= MAXIMUM_PACKETS_PER_INTERRUPT || packet_data >= MAXIMUM_DATA_PER_INTERRUPT)
  {
    /* fire again immediately */
    KdPrint((__DRIVER_NAME "     Dpc Duration Exceeded\n"));
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

  while (page_buf)
  {
    shared_buffer_t *next_buf = page_buf->next;
    PMDL mdl;

    page_buf->next = NULL;
    if (extra_info_flag)
    {
      //KdPrint((__DRIVER_NAME "     processing extra info\n"));
      ei = (struct netif_extra_info *)&page_buf->rsp;
      extra_info_flag = ei->flags & XEN_NETIF_EXTRA_FLAG_MORE;
      switch (ei->type)
      {
      case XEN_NETIF_EXTRA_TYPE_GSO:
        switch (ei->u.gso.type)
        {
        case XEN_NETIF_GSO_TYPE_TCPV4:
          pi->mss = ei->u.gso.size;
          //KdPrint((__DRIVER_NAME "     mss = %d\n", pi->mss));
          // TODO - put this assertion somewhere ASSERT(header_len + pi->mss <= PAGE_SIZE); // this limits MTU to PAGE_SIZE - XN_HEADER_LEN
          break;
        default:
          KdPrint((__DRIVER_NAME "     Unknown GSO type (%d) detected\n", ei->u.gso.type));
          break;
        }
        break;
      default:
        KdPrint((__DRIVER_NAME "     Unknown extra info type (%d) detected\n", ei->type));
        break;
      }
      put_pb_on_freelist(xi, page_buf);
    }
    else
    {
      ASSERT(!page_buf->rsp.offset);
      if (!more_data_flag) // handling the packet's 1st buffer
      {
        if (page_buf->rsp.flags & NETRXF_csum_blank)
          pi->csum_blank = TRUE;
        if (page_buf->rsp.flags & NETRXF_data_validated)
          pi->data_validated = TRUE;
      }
      mdl = page_buf->mdl;
      mdl->ByteCount = page_buf->rsp.status; //NdisAdjustBufferLength(mdl, page_buf->rsp.status);
      //KdPrint((__DRIVER_NAME "     buffer = %p, pb = %p\n", buffer, page_buf));
      if (pi->first_pb)
      {
        ASSERT(pi->curr_pb);
        //KdPrint((__DRIVER_NAME "     additional buffer\n"));
        pi->curr_pb->next = page_buf;
        pi->curr_pb = page_buf;
        ASSERT(pi->curr_mdl);
        pi->curr_mdl->Next = mdl;
        pi->curr_mdl = mdl;
      }
      else
      {
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
    if (!more_data_flag && !extra_info_flag)
    {
      pi->curr_pb = pi->first_pb;
      pi->curr_mdl = pi->first_mdl;
      XenNet_MakePackets(xi, &rc, pi);
    }

    page_buf = next_buf;
  }
  ASSERT(!more_data_flag && !extra_info_flag);

  if (rc.first_nbl)
  {
    NdisMIndicateReceiveNetBufferLists(xi->adapter_handle, rc.first_nbl, NDIS_DEFAULT_PORT_NUMBER, nbl_count,
      NDIS_RECEIVE_FLAGS_DISPATCH_LEVEL
      //| NDIS_RECEIVE_FLAGS_SINGLE_ETHER_TYPE 
      | NDIS_RECEIVE_FLAGS_PERFECT_FILTERED);
  }
  //FUNCTION_EXIT();
  return dont_set_event;
}

/*
   Free all Rx buffers (on halt, for example) 
   The ring must be stopped at this point.
*/

static VOID
XenNet_PurgeRing(xennet_info_t *xi)
{
  int i;
  for (i = 0; i < NET_RX_RING_SIZE; i++)
  {
    if (xi->rx_ring_pbs[i] != NULL)
    {
      put_pb_on_freelist(xi, xi->rx_ring_pbs[i]);
      xi->rx_ring_pbs[i] = NULL;
    }
  }
}

static VOID
XenNet_BufferFree(xennet_info_t *xi)
{
  shared_buffer_t *sb;

  XenNet_PurgeRing(xi);

  /* because we are shutting down this won't allocate new ones */
  while ((sb = get_pb_from_freelist(xi)) != NULL)
  {
    xi->vectors.GntTbl_EndAccess(xi->vectors.context,
        sb->gref, FALSE, (ULONG)'XNRX');
    IoFreeMdl(sb->mdl);
    NdisFreeMemory(sb->virtual, sizeof(shared_buffer_t), 0);
    NdisFreeMemory(sb, PAGE_SIZE, 0);
  }
  while ((sb = get_hb_from_freelist(xi)) != NULL)
  {
    IoFreeMdl(sb->mdl);
    NdisFreeMemory(sb, sizeof(shared_buffer_t) + MAX_ETH_HEADER_LENGTH + MAX_LOOKAHEAD_LENGTH, 0);
  }
}

VOID
XenNet_BufferAlloc(xennet_info_t *xi)
{
  //NDIS_STATUS status;
  int i;
  
  xi->rx_id_free = NET_RX_RING_SIZE;
  xi->rx_outstanding = 0;

  for (i = 0; i < NET_RX_RING_SIZE; i++)
  {
    xi->rx_ring_pbs[i] = NULL;
  }
}

VOID
XenNet_RxResumeStart(xennet_info_t *xi)
{
  KIRQL old_irql;

  FUNCTION_ENTER();

  KeAcquireSpinLock(&xi->rx_lock, &old_irql);
  XenNet_PurgeRing(xi);
  KeReleaseSpinLock(&xi->rx_lock, old_irql);
  
  FUNCTION_EXIT();
}

VOID
XenNet_RxResumeEnd(xennet_info_t *xi)
{
  KIRQL old_irql;

  FUNCTION_ENTER();

  KeAcquireSpinLock(&xi->rx_lock, &old_irql);
  //XenNet_BufferAlloc(xi);
  XenNet_FillRing(xi);
  KeReleaseSpinLock(&xi->rx_lock, old_irql);
  
  FUNCTION_EXIT();
}

BOOLEAN
XenNet_RxInit(xennet_info_t *xi)
{
  NET_BUFFER_LIST_POOL_PARAMETERS nbl_pool_parameters;
  NET_BUFFER_POOL_PARAMETERS nb_pool_parameters;
  int ret;

  FUNCTION_ENTER();

  xi->rx_shutting_down = FALSE;
  KeInitializeSpinLock(&xi->rx_lock);
  KeInitializeEvent(&xi->packet_returned_event, SynchronizationEvent, FALSE);
  xi->rxpi = NdisAllocateMemoryWithTagPriority(xi->adapter_handle, sizeof(packet_info_t) * NdisSystemProcessorCount(), XENNET_POOL_TAG, NormalPoolPriority);
  if (!xi->rxpi)
  {
    KdPrint(("NdisAllocateMemoryWithTagPriority failed\n"));
    return FALSE;
  }
  NdisZeroMemory(xi->rxpi, sizeof(packet_info_t) * NdisSystemProcessorCount());

  ret = stack_new(&xi->rx_pb_stack, NET_RX_RING_SIZE * 4);
  if (!ret)
  {
    FUNCTION_MSG("Failed to allocate rx_pb_stack\n");
    NdisFreeMemory(xi->rxpi, sizeof(packet_info_t) * NdisSystemProcessorCount(), 0);
    return FALSE;
  }
  stack_new(&xi->rx_hb_stack, NET_RX_RING_SIZE * 4);
  if (!ret)
  {
    FUNCTION_MSG("Failed to allocate rx_hb_stack\n");
    stack_delete(xi->rx_pb_stack, NULL, NULL);
    NdisFreeMemory(xi->rxpi, sizeof(packet_info_t) * NdisSystemProcessorCount(), 0);
    return FALSE;
  }

  XenNet_BufferAlloc(xi);
  
  nbl_pool_parameters.Header.Type = NDIS_OBJECT_TYPE_DEFAULT;
  nbl_pool_parameters.Header.Revision = NET_BUFFER_LIST_POOL_PARAMETERS_REVISION_1;
  nbl_pool_parameters.Header.Size = NDIS_SIZEOF_NET_BUFFER_LIST_POOL_PARAMETERS_REVISION_1;
  nbl_pool_parameters.ProtocolId = NDIS_PROTOCOL_ID_DEFAULT;
  nbl_pool_parameters.fAllocateNetBuffer = FALSE;
  nbl_pool_parameters.ContextSize = 0;
  nbl_pool_parameters.PoolTag = XENNET_POOL_TAG;
  nbl_pool_parameters.DataSize = 0; /* NET_BUFFERS are always allocated separately */
  
  xi->rx_nbl_pool = NdisAllocateNetBufferListPool(xi->adapter_handle, &nbl_pool_parameters);
  if (!xi->rx_nbl_pool)
  {
    KdPrint(("NdisAllocateNetBufferListPool failed\n"));
    return FALSE;
  }

  nb_pool_parameters.Header.Type = NDIS_OBJECT_TYPE_DEFAULT;
  nb_pool_parameters.Header.Revision = NET_BUFFER_POOL_PARAMETERS_REVISION_1;
  nb_pool_parameters.Header.Size = NDIS_SIZEOF_NET_BUFFER_POOL_PARAMETERS_REVISION_1;
  nb_pool_parameters.PoolTag = XENNET_POOL_TAG;
  nb_pool_parameters.DataSize = 0; /* the buffers come from the ring */
  xi->rx_nb_pool = NdisAllocateNetBufferPool(xi->adapter_handle, &nb_pool_parameters);
  if (!xi->rx_nb_pool)
  {
    KdPrint(("NdisAllocateNetBufferPool (rx_nb_pool) failed\n"));
    return FALSE;
  }

  XenNet_FillRing(xi);

  FUNCTION_EXIT();

  return TRUE;
}

BOOLEAN
XenNet_RxShutdown(xennet_info_t *xi)
{
  KIRQL old_irql;
  //PNDIS_PACKET packet;
  UNREFERENCED_PARAMETER(xi);

  FUNCTION_ENTER();

  KeAcquireSpinLock(&xi->rx_lock, &old_irql);
  xi->rx_shutting_down = TRUE;
  KeReleaseSpinLock(&xi->rx_lock, old_irql);

  KeFlushQueuedDpcs();

  while (xi->rx_outstanding)
  {
    KdPrint((__DRIVER_NAME "     Waiting for all packets to be returned\n"));
    KeWaitForSingleObject(&xi->packet_returned_event, Executive, KernelMode, FALSE, NULL);
  }

  NdisFreeMemory(xi->rxpi, sizeof(packet_info_t) * NdisSystemProcessorCount(), 0);

  XenNet_BufferFree(xi);


  stack_delete(xi->rx_pb_stack, NULL, NULL);
  stack_delete(xi->rx_hb_stack, NULL, NULL);
  
  NdisFreeNetBufferPool(xi->rx_nb_pool);
  NdisFreeNetBufferListPool(xi->rx_nbl_pool);

  FUNCTION_EXIT();

  return TRUE;
}
