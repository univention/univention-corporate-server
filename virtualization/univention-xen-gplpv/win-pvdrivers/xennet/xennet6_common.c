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

/* Increase the header to a certain size */
BOOLEAN
XenNet_BuildHeader(packet_info_t *pi, PUCHAR header, ULONG new_header_size)
{
  ULONG bytes_remaining;

  //FUNCTION_ENTER();

  if (!header)
    header = pi->header;

  if (new_header_size > pi->total_length)
  {
    new_header_size = pi->total_length;
  }

  if (new_header_size <= pi->header_length)
  {
    //FUNCTION_EXIT();
    return TRUE; /* header is already at least the required size */
  }

  if (header == pi->first_mdl_virtual)
  {
    /* still working in the first buffer */
    if (new_header_size <= pi->first_mdl_length)
    {
      //KdPrint((__DRIVER_NAME "     new_header_size <= pi->first_mdl_length\n"));
      pi->header_length = new_header_size;
      if (pi->header_length == pi->first_mdl_length)
      {
        NdisGetNextMdl(pi->curr_mdl, &pi->curr_mdl);
        pi->curr_mdl_offset = 0;
        if (pi->curr_pb)
          pi->curr_pb = pi->curr_pb->next;
      }
      else
      {
        pi->curr_mdl_offset = (USHORT)new_header_size;
      }
      //FUNCTION_EXIT();
      return TRUE;
    }
    else
    {
      //KdPrint((__DRIVER_NAME "     Switching to header_data\n"));
      memcpy(pi->header_data, header, pi->header_length);
      header = pi->header = pi->header_data;
    }
  }
  
  bytes_remaining = new_header_size - pi->header_length;
  // TODO: if there are only a small number of bytes left in the current buffer then increase to consume that too... it would have to be no more than the size of header+mss though

  //KdPrint((__DRIVER_NAME "     A bytes_remaining = %d, pi->curr_mdl = %p\n", bytes_remaining, pi->curr_mdl));
  while (bytes_remaining && pi->curr_mdl)
  {
    ULONG copy_size;
    
    ASSERT(pi->curr_mdl);
    //KdPrint((__DRIVER_NAME "     B bytes_remaining = %d, pi->curr_mdl = %p\n", bytes_remaining, pi->curr_mdl));
    if (MmGetMdlByteCount(pi->curr_mdl))
    {
      PUCHAR src_addr;
      src_addr = MmGetSystemAddressForMdlSafe(pi->curr_mdl, NormalPagePriority);
      if (!src_addr)
      {
        //FUNCTION_EXIT();
        return FALSE;
      }
      copy_size = min(bytes_remaining, MmGetMdlByteCount(pi->curr_mdl) - pi->curr_mdl_offset);
      //KdPrint((__DRIVER_NAME "     B copy_size = %d\n", copy_size));
      memcpy(header + pi->header_length,
        src_addr + pi->curr_mdl_offset, copy_size);
      pi->curr_mdl_offset = (USHORT)(pi->curr_mdl_offset + copy_size);
      pi->header_length += copy_size;
      bytes_remaining -= copy_size;
    }
    if (pi->curr_mdl_offset == MmGetMdlByteCount(pi->curr_mdl))
    {
      NdisGetNextMdl(pi->curr_mdl, &pi->curr_mdl);
      if (pi->curr_pb)
        pi->curr_pb = pi->curr_pb->next;
      pi->curr_mdl_offset = 0;
    }
  }
  //KdPrint((__DRIVER_NAME "     C bytes_remaining = %d, pi->curr_mdl = %p\n", bytes_remaining, pi->curr_mdl));
  if (bytes_remaining)
  {
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

  ASSERT(pi->first_mdl);
  
  NdisQueryMdl(pi->first_mdl, (PVOID)&pi->first_mdl_virtual, &pi->first_mdl_length, NormalPagePriority);
  pi->curr_mdl = pi->first_mdl;
  if (alt_buffer)
    pi->header = alt_buffer;
  else
    pi->header = pi->first_mdl_virtual;

  pi->header_length = 0;
  pi->curr_mdl_offset = pi->first_mdl_offset;

  XenNet_BuildHeader(pi, NULL, min_header_size);
  
  if (!XenNet_BuildHeader(pi, NULL, (ULONG)XN_HDR_SIZE))
  {
    //KdPrint((__DRIVER_NAME "     packet too small (Ethernet Header)\n"));
    pi->parse_result = PARSE_TOO_SMALL;
    return;
  }

  if (pi->header[0] == 0xFF && pi->header[1] == 0xFF
      && pi->header[2] == 0xFF && pi->header[3] == 0xFF
      && pi->header[4] == 0xFF && pi->header[5] == 0xFF)
  {
    pi->is_broadcast = TRUE;
  }
  else if (pi->header[0] & 0x01)
  {
    pi->is_multicast = TRUE;
  }

  switch (GET_NET_PUSHORT(&pi->header[12])) // L2 protocol field
  {
  case 0x0800: /* IPv4 */
    //KdPrint((__DRIVER_NAME "     IP\n"));
    if (pi->header_length < (ULONG)(XN_HDR_SIZE + 20))
    {
      if (!XenNet_BuildHeader(pi, NULL, (ULONG)(XN_HDR_SIZE + 20)))
      {
        KdPrint((__DRIVER_NAME "     packet too small (IP Header)\n"));
        pi->parse_result = PARSE_TOO_SMALL;
        return;
      }
    }
    pi->ip_version = (pi->header[XN_HDR_SIZE + 0] & 0xF0) >> 4;
    if (pi->ip_version != 4)
    {
      //KdPrint((__DRIVER_NAME "     ip_version = %d\n", pi->ip_version));
      pi->parse_result = PARSE_UNKNOWN_TYPE;
      return;
    }
    pi->ip4_header_length = (pi->header[XN_HDR_SIZE + 0] & 0x0F) << 2;
    if (pi->header_length < (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + 20))
    {
      if (!XenNet_BuildHeader(pi, NULL, (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + 20)))
      {
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
  switch (pi->ip_proto)
  {
  case 6:  // TCP
  case 17: // UDP
    break;
  default:
    //KdPrint((__DRIVER_NAME "     Not TCP/UDP (%d)\n", pi->ip_proto));
    pi->parse_result = PARSE_UNKNOWN_TYPE;
    return;
  }
  pi->ip4_length = GET_NET_PUSHORT(&pi->header[XN_HDR_SIZE + 2]);
  pi->tcp_header_length = (pi->header[XN_HDR_SIZE + pi->ip4_header_length + 12] & 0xf0) >> 2;

  if (pi->header_length < (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + pi->tcp_header_length))
  {
    /* we don't actually need the tcp options to analyse the header */
    if (!XenNet_BuildHeader(pi, NULL, (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + MIN_TCP_HEADER_LENGTH)))
    {
      //KdPrint((__DRIVER_NAME "     packet too small (IP Header + IP Options + TCP Header (not including TCP Options))\n"));
      pi->parse_result = PARSE_TOO_SMALL;
      return;
    }
  }

  if ((ULONG)XN_HDR_SIZE + pi->ip4_length > pi->total_length)
  {
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

VOID
XenNet_SumIpHeader(
  PUCHAR header,
  USHORT ip4_header_length
)
{
  ULONG csum = 0;
  USHORT i;

  ASSERT(ip4_header_length > 12);
  ASSERT(!(ip4_header_length & 1));

  header[XN_HDR_SIZE + 10] = 0;
  header[XN_HDR_SIZE + 11] = 0;
  for (i = 0; i < ip4_header_length; i += 2)
  {
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
