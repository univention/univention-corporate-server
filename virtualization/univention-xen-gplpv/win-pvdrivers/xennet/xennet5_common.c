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

#include "xennet5.h"

/* Increase the header to a certain size */
BOOLEAN
XenNet_BuildHeader(packet_info_t *pi, PUCHAR header, ULONG new_header_size)
{
  ULONG bytes_remaining;

  //FUNCTION_ENTER();

  if (!header)
    header = pi->header;

  if (new_header_size <= pi->header_length)
  {
    return TRUE; /* header is already at least the required size */
  }

  if (header == pi->first_buffer_virtual)
  {
    /* still working in the first buffer */
    if (new_header_size <= pi->first_buffer_length)
    {
      //KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ " new_header_size <= pi->first_buffer_length\n"));
      pi->header_length = new_header_size;
      if (pi->header_length == pi->first_buffer_length)
      {
        NdisGetNextBuffer(pi->curr_buffer, &pi->curr_buffer);
        pi->curr_mdl_offset = 0;
        if (pi->curr_pb)
          pi->curr_pb = pi->curr_pb->next;
      }
      else
      {
        pi->curr_mdl_offset = (USHORT)new_header_size;
      }      
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

  //KdPrint((__DRIVER_NAME "     A bytes_remaining = %d, pi->curr_buffer = %p, pi->mdl_count = %d\n", bytes_remaining, pi->curr_buffer, pi->mdl_count));
  while (bytes_remaining && pi->curr_buffer)
  {
    ULONG copy_size;
    
    ASSERT(pi->curr_buffer);
    //KdPrint((__DRIVER_NAME "     B bytes_remaining = %d, pi->curr_buffer = %p, pi->mdl_count = %d\n", bytes_remaining, pi->curr_buffer, pi->mdl_count));
    if (MmGetMdlByteCount(pi->curr_buffer))
    {
      PUCHAR src_addr;
      src_addr = MmGetSystemAddressForMdlSafe(pi->curr_buffer, NormalPagePriority);
      if (!src_addr)
        return FALSE;
      copy_size = min(bytes_remaining, MmGetMdlByteCount(pi->curr_buffer) - pi->curr_mdl_offset);
      //KdPrint((__DRIVER_NAME "     B copy_size = %d\n", copy_size));
      memcpy(header + pi->header_length,
        src_addr + pi->curr_mdl_offset, copy_size);
      pi->curr_mdl_offset = (USHORT)(pi->curr_mdl_offset + copy_size);
      pi->header_length += copy_size;
      bytes_remaining -= copy_size;
    }
    if (pi->curr_mdl_offset == MmGetMdlByteCount(pi->curr_buffer))
    {
      NdisGetNextBuffer(pi->curr_buffer, &pi->curr_buffer);
      if (pi->curr_pb)
        pi->curr_pb = pi->curr_pb->next;
      pi->curr_mdl_offset = 0;
    }
  }
  //KdPrint((__DRIVER_NAME "     C bytes_remaining = %d, pi->curr_buffer = %p, pi->mdl_count = %d\n", bytes_remaining, pi->curr_buffer, pi->mdl_count));
  if (bytes_remaining)
  {
    //KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ " bytes_remaining\n"));
    return FALSE;
  }
  //FUNCTION_EXIT();
  return TRUE;
}

ULONG
XenNet_ParsePacketHeader(packet_info_t *pi, PUCHAR alt_buffer, ULONG min_header_size)
{
  //FUNCTION_ENTER();

  ASSERT(pi->first_buffer);
  
  NdisQueryBufferSafe(pi->first_buffer, (PVOID)&pi->first_buffer_virtual, &pi->first_buffer_length, NormalPagePriority);
  pi->curr_buffer = pi->first_buffer;
  if (alt_buffer)
    pi->header = alt_buffer;
  else
    pi->header = pi->first_buffer_virtual;

  pi->header_length = 0;
  pi->curr_mdl_offset = 0;

  XenNet_BuildHeader(pi, NULL, min_header_size);
  
  if (!XenNet_BuildHeader(pi, NULL, (ULONG)XN_HDR_SIZE))
  {
    KdPrint((__DRIVER_NAME "     packet too small (Ethernet Header)\n"));
    return PARSE_TOO_SMALL;
  }

  switch (GET_NET_PUSHORT(&pi->header[12])) // L2 protocol field
  {
  case 0x0800:
    //KdPrint((__DRIVER_NAME "     IP\n"));
    if (pi->header_length < (ULONG)(XN_HDR_SIZE + 20))
    {
      if (!XenNet_BuildHeader(pi, NULL, (ULONG)(XN_HDR_SIZE + 20)))
      {
        KdPrint((__DRIVER_NAME "     packet too small (IP Header)\n"));
        return PARSE_TOO_SMALL;
      }
    }
    pi->ip_version = (pi->header[XN_HDR_SIZE + 0] & 0xF0) >> 4;
    if (pi->ip_version != 4)
    {
      KdPrint((__DRIVER_NAME "     ip_version = %d\n", pi->ip_version));
      return PARSE_UNKNOWN_TYPE;
    }
    pi->ip4_header_length = (pi->header[XN_HDR_SIZE + 0] & 0x0F) << 2;
    pi->ip_has_options = (BOOLEAN)(pi->ip4_header_length > 20);
    if (pi->header_length < (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + 20))
    {
      if (!XenNet_BuildHeader(pi, NULL, (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + 20)))
      {
        //KdPrint((__DRIVER_NAME "     packet too small (IP Header + IP Options + TCP Header)\n"));
        return PARSE_TOO_SMALL;
      }
    }
    break;
  default:
    //KdPrint((__DRIVER_NAME "     Not IP (%d)\n", GET_NET_PUSHORT(&pi->header[12])));
    return PARSE_UNKNOWN_TYPE;
  }
  pi->ip_proto = pi->header[XN_HDR_SIZE + 9];
  switch (pi->ip_proto)
  {
  case 6:  // TCP
  case 17: // UDP
    break;
  default:
    //KdPrint((__DRIVER_NAME "     Not TCP/UDP (%d)\n", pi->ip_proto));
    return PARSE_UNKNOWN_TYPE;
  }
  pi->ip4_length = GET_NET_PUSHORT(&pi->header[XN_HDR_SIZE + 2]);
  pi->tcp_header_length = (pi->header[XN_HDR_SIZE + pi->ip4_header_length + 12] & 0xf0) >> 2;

  if (pi->header_length < (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + pi->tcp_header_length))
  {
    if (!XenNet_BuildHeader(pi, NULL, (ULONG)(XN_HDR_SIZE + pi->ip4_header_length + pi->tcp_header_length)))
    {
      //KdPrint((__DRIVER_NAME "     packet too small (IP Header + IP Options + TCP Header + TCP Options)\n"));
      return PARSE_TOO_SMALL;
    }
  }
  
  if ((ULONG)XN_HDR_SIZE + pi->ip4_length > pi->total_length)
  {
    KdPrint((__DRIVER_NAME "     XN_HDR_SIZE + ip4_length (%d) > total_length (%d)\n", XN_HDR_SIZE + pi->ip4_length, pi->total_length));
    return PARSE_UNKNOWN_TYPE;
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
  
  return PARSE_OK;
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
XenNet_CheckIpHeader(
  PUCHAR header,
  USHORT ip4_header_length
)
{
  ULONG csum = 0;
  USHORT i;

  ASSERT(ip4_header_length > 12);
  ASSERT(!(ip4_header_length & 1));

  for (i = 0; i < ip4_header_length; i += 2)
  {
    csum += GET_NET_PUSHORT(&header[XN_HDR_SIZE + i]);
  }
  while (csum & 0xFFFF0000)
    csum = (csum & 0xFFFF) + (csum >> 16);
  return (BOOLEAN)(csum == 0xFFFF);
}

BOOLEAN
XenNet_FilterAcceptPacket(struct xennet_info *xi,packet_info_t *pi)
{
  BOOLEAN is_multicast = FALSE;
  BOOLEAN is_my_multicast = FALSE;
  BOOLEAN is_broadcast = FALSE;
  BOOLEAN is_directed = FALSE;
  ULONG i;

  if (pi->header[0] == 0xFF && pi->header[1] == 0xFF
      && pi->header[2] == 0xFF && pi->header[3] == 0xFF
      && pi->header[4] == 0xFF && pi->header[5] == 0xFF)
  {
    is_broadcast = TRUE;
  }
  else if (pi->header[0] & 0x01)
  {
    is_multicast = TRUE;
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
  if (memcmp(xi->curr_mac_addr, pi->header, ETH_ALEN) == 0)
  {
    is_directed = TRUE;
  }

  if (is_directed && (xi->packet_filter & NDIS_PACKET_TYPE_DIRECTED))
  {
    return TRUE;
  }  
  if (is_my_multicast && (xi->packet_filter & NDIS_PACKET_TYPE_MULTICAST))
  {
    return TRUE;
  }
  if (is_multicast && (xi->packet_filter & NDIS_PACKET_TYPE_ALL_MULTICAST))
  {
    return TRUE;
  }
  if (is_broadcast && (xi->packet_filter & NDIS_PACKET_TYPE_BROADCAST))
  {
    return TRUE;
  }
  if (xi->packet_filter & NDIS_PACKET_TYPE_PROMISCUOUS)
  {
    return TRUE;
  }
  return FALSE;
}
