/*
PV Drivers for Windows Xen HVM Domains
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

#pragma warning(disable: 4201)
#pragma warning(disable: 4214)

#include <ntddk.h>
#include <wdm.h>
#define NDIS_MINIPORT_DRIVER 1
#if NTDDI_VERSION < NTDDI_WINXP
# define NDIS50_MINIPORT 1
#elif NTDDI_VERSION < NTDDI_VISTA
# define NDIS51_MINIPORT 1
#else
# define NDIS61_MINIPORT 1
#endif
#include <ndis.h>
#define NTSTRSAFE_LIB
#include <ntstrsafe.h>
#include <liblfds.h>

#define VENDOR_DRIVER_VERSION_MAJOR 0
#define VENDOR_DRIVER_VERSION_MINOR 11

#define MAX_LINK_SPEED 10000000000L /* there is not really any theoretical maximum... */

#define VENDOR_DRIVER_VERSION (((VENDOR_DRIVER_VERSION_MAJOR) << 16) | (VENDOR_DRIVER_VERSION_MINOR))

#define __DRIVER_NAME "XenNet"

//#define PACKET_NEXT_PACKET_FIELD MiniportReservedEx[sizeof(PVOID)] // RX & TX
//#define PACKET_FIRST_PB_FIELD MiniportReservedEx[0] // RX
#define PACKET_NEXT_PACKET_FIELD MiniportReservedEx[0] // RX & TX
#define PACKET_FIRST_PB_FIELD MiniportReservedEx[sizeof(PVOID)] // RX
#define PACKET_LIST_ENTRY_FIELD MiniportReservedEx[sizeof(PVOID)] // TX (2 entries)
#define PACKET_NEXT_PACKET(_packet) (*(PNDIS_PACKET *)&(_packet)->PACKET_NEXT_PACKET_FIELD)
#define PACKET_LIST_ENTRY(_packet) (*(PLIST_ENTRY)&(_packet)->PACKET_LIST_ENTRY_FIELD)
#define PACKET_FIRST_PB(_packet) (*(shared_buffer_t **)&(_packet)->PACKET_FIRST_PB_FIELD)

#define NB_LIST_ENTRY_FIELD MiniportReserved[0] // TX (2 entries)
#define NB_FIRST_PB_FIELD MiniportReserved[0] // RX
#define NB_NBL_FIELD MiniportReserved[2] // TX
#define NB_LIST_ENTRY(_nb) (*(PLIST_ENTRY)&(_nb)->NB_LIST_ENTRY_FIELD)
#define NB_NBL(_nb) (*(PNET_BUFFER_LIST *)&(_nb)->NB_NBL_FIELD)
#define NB_FIRST_PB(_nb) (*(shared_buffer_t **)&(_nb)->NB_FIRST_PB_FIELD)

#define NBL_REF_FIELD MiniportReserved[0] // TX
#define NBL_REF(_nbl) (*(ULONG_PTR *)&(_nbl)->NBL_REF_FIELD)

#define NDIS_STATUS_RESOURCES_MAX_LENGTH 64

#include <xen_windows.h>
#include <memory.h>
#include <grant_table.h>
#include <event_channel.h>
#include <hvm/params.h>
#include <hvm/hvm_op.h>
#include <xen_public.h>
#include <io/ring.h>
#include <io/netif.h>
#include <io/xenbus.h>
#include <stdlib.h>
#define XENNET_POOL_TAG (ULONG) 'XenN'

/* Xen macros use these, so they need to be redefined to Win equivs */
#define wmb() KeMemoryBarrier()
#define mb() KeMemoryBarrier()

#define GRANT_INVALID_REF 0

#define NAME_SIZE 64

#define ETH_ALEN 6

static FORCEINLINE USHORT
GET_NET_USHORT(USHORT data) {
  return (data << 8) | (data >> 8);
}

static FORCEINLINE USHORT
GET_NET_PUSHORT(PVOID pdata) {
  return (*((PUSHORT)pdata) << 8) | (*((PUSHORT)pdata) >> 8);
}

static FORCEINLINE VOID
SET_NET_USHORT(PVOID ptr, USHORT data) {
  *((PUSHORT)ptr) = GET_NET_USHORT(data);
}

static FORCEINLINE ULONG
GET_NET_ULONG(ULONG data) {
  ULONG tmp;
  
  tmp = ((data & 0x00ff00ff) << 8) | ((data & 0xff00ff00) >> 8);
  return (tmp << 16) | (tmp >> 16);
}

static FORCEINLINE ULONG
GET_NET_PULONG(PVOID pdata) {
  ULONG tmp;
  
  tmp = ((*((PULONG)pdata) & 0x00ff00ff) << 8) | ((*((PULONG)pdata) & 0xff00ff00) >> 8);
  return (tmp << 16) | (tmp >> 16);
}

static FORCEINLINE VOID
SET_NET_ULONG(PVOID ptr, ULONG data) {
  *((PULONG)ptr) = GET_NET_ULONG(data);
}
/*
#define GET_NET_ULONG(x) ((GET_NET_USHORT(x) << 16) | GET_NET_USHORT(((PUCHAR)&x)[2]))
#define SET_NET_ULONG(y, x) *((ULONG *)&(y)) = ((GET_NET_USHORT(x) << 16) | GET_NET_USHORT(((PUCHAR)&x)[2]))
*/

#define SUPPORTED_PACKET_FILTERS (\
  NDIS_PACKET_TYPE_DIRECTED | \
  NDIS_PACKET_TYPE_MULTICAST | \
  NDIS_PACKET_TYPE_BROADCAST | \
  NDIS_PACKET_TYPE_PROMISCUOUS | \
  NDIS_PACKET_TYPE_ALL_MULTICAST)

/* couldn't get regular xen ring macros to work...*/
#define __NET_RING_SIZE(type, _sz) \
    (__RD32( \
    (_sz - sizeof(struct type##_sring) + sizeof(union type##_sring_entry)) \
    / sizeof(union type##_sring_entry)))

#define NET_TX_RING_SIZE __NET_RING_SIZE(netif_tx, PAGE_SIZE)
#define NET_RX_RING_SIZE __NET_RING_SIZE(netif_rx, PAGE_SIZE)

#pragma warning(disable: 4127) // conditional expression is constant

#define MIN_LARGE_SEND_SEGMENTS 4

/* TODO: crank this up if we support higher mtus? */
#define XN_HDR_SIZE 14
#define XN_MAX_DATA_SIZE 1500
#define XN_MIN_FRAME_SIZE 60
#define XN_MAX_FRAME_SIZE (XN_HDR_SIZE + XN_DATA_SIZE)
/*
#if !defined(OFFLOAD_LARGE_SEND)
  #define XN_MAX_PKT_SIZE (XN_HDR_SIZE + XN_DATA_SIZE)
#else
  #define XN_MAX_PKT_SIZE MAX_LARGE_SEND_OFFLOAD
#endif
*/

#define XN_MAX_SEND_PKTS 16

#define XENSOURCE_MAC_HDR 0x00163E
#define XN_VENDOR_DESC "Xensource"
#define MAX_XENBUS_STR_LEN 128

//#define RX_MIN_TARGET 8
#define RX_DEFAULT_TARGET 256
//#define RX_MAX_TARGET min(NET_RX_RING_SIZE, 256)
#define RX_MAX_PB_FREELIST (NET_RX_RING_SIZE * 4)
#define RX_PACKET_MAX (NET_RX_RING_SIZE * 4)
#define RX_PACKET_HIGH_WATER_MARK (RX_PACKET_MAX * 3 / 4)

//#define MAX_BUFFERS_PER_PACKET NET_RX_RING_SIZE

#define MIN_ETH_HEADER_LENGTH 14
#define MAX_ETH_HEADER_LENGTH 14
#define MIN_IP4_HEADER_LENGTH 20
#define MAX_IP4_HEADER_LENGTH (15 * 4)
#define MIN_TCP_HEADER_LENGTH 20
#define MAX_TCP_HEADER_LENGTH (15 * 4)
#define MAX_PKT_HEADER_LENGTH (MAX_ETH_HEADER_LENGTH + MAX_IP4_HEADER_LENGTH + MAX_TCP_HEADER_LENGTH)

#define MIN_LOOKAHEAD_LENGTH (MAX_IP4_HEADER_LENGTH + MAX_TCP_HEADER_LENGTH)
//#define MAX_LOOKAHEAD_LENGTH PAGE_SIZE
/* optimise the size of header buffers */
#define MAX_LOOKAHEAD_LENGTH (512 - sizeof(shared_buffer_t) - MAX_ETH_HEADER_LENGTH)

#define LINUX_MAX_SG_ELEMENTS 18

#define PAGE_LIST_SIZE (max(NET_RX_RING_SIZE, NET_TX_RING_SIZE) * 4)
#define MULTICAST_LIST_MAX_SIZE 32

#define TX_HEADER_BUFFER_SIZE 512
#define TX_COALESCE_BUFFERS (NET_TX_RING_SIZE)

/* split incoming large packets into MSS sized chunks */
#define RX_LSO_SPLIT_MSS 0
/* split incoming large packets in half, to not invoke the delayed ack timer */
#define RX_LSO_SPLIT_HALF 1
/* don't split incoming large packets. not really useful */
#define RX_LSO_SPLIT_NONE 2

#define DEVICE_STATE_DISCONNECTED  0 /* -> INITIALISING */
#define DEVICE_STATE_INITIALISING  1 /* -> ACTIVE or INACTIVE */
#define DEVICE_STATE_INACTIVE      2
#define DEVICE_STATE_ACTIVE        3 /* -> DISCONNECTING */
#define DEVICE_STATE_DISCONNECTING 4 /* -> DISCONNECTED */

struct _shared_buffer_t;

typedef struct _shared_buffer_t shared_buffer_t;

struct _shared_buffer_t {
  struct netif_rx_response rsp;
  shared_buffer_t *next;
  grant_ref_t gref;
  //USHORT offset;
  PVOID virtual;
  PMDL mdl;
  //USHORT id;
  volatile LONG ref_count;
};

typedef struct {
  #if NTDDI_VERSION < NTDDI_VISTA
  PNDIS_PACKET packet; /* only set on the last packet */
  #else
  PNET_BUFFER packet; /* only set on the last packet */
  #endif
  PVOID *cb;
  grant_ref_t gref;
} tx_shadow_t;

typedef struct {
  ULONG parse_result;
  PMDL first_mdl;
  MDL first_mdl_storage;
  PPFN_NUMBER first_mdl_pfns[17]; /* maximum possible packet size */
  PMDL curr_mdl;
  shared_buffer_t *first_pb;
  shared_buffer_t *curr_pb;
  PUCHAR first_mdl_virtual;
  //ULONG mdl_count;
  ULONG first_mdl_offset;
  ULONG first_mdl_length;
  ULONG curr_mdl_offset;
  USHORT mss;
  //NDIS_TCP_IP_CHECKSUM_PACKET_INFO csum_info;
  BOOLEAN csum_blank;
  BOOLEAN data_validated;
  BOOLEAN split_required;
  UCHAR ip_version;
  PUCHAR header;
  ULONG header_length;
  UCHAR ip_proto;
  BOOLEAN ip_has_options;
  ULONG total_length;
  USHORT ip4_header_length;
  USHORT ip4_length;
  USHORT tcp_header_length;
  BOOLEAN tcp_has_options;
  USHORT tcp_length;
  USHORT tcp_remaining;
  ULONG tcp_seq;
  BOOLEAN is_multicast;
  BOOLEAN is_broadcast;
  /* anything past here doesn't get cleared automatically by the ClearPacketInfo */
  UCHAR header_data[MAX_LOOKAHEAD_LENGTH + MAX_ETH_HEADER_LENGTH];
} packet_info_t;

struct xennet_info
{
  ULONG device_state;
  
  /* Base device vars */
  PDEVICE_OBJECT pdo;
  PDEVICE_OBJECT fdo;
  PDEVICE_OBJECT lower_do;
//  WCHAR dev_desc[NAME_SIZE];

  /* NDIS-related vars */
  NDIS_HANDLE adapter_handle;
  ULONG packet_filter;
  uint8_t perm_mac_addr[ETH_ALEN];
  uint8_t curr_mac_addr[ETH_ALEN];
  ULONG current_lookahead;

  /* Misc. Xen vars */
  XN_HANDLE handle;
  
  evtchn_port_t event_channel;
  ULONG backend_state;
  KEVENT backend_event;
  UCHAR multicast_list[MULTICAST_LIST_MAX_SIZE][6];
  ULONG multicast_list_size;
  KDPC rxtx_dpc;

  /* tx related - protected by tx_lock */
  KSPIN_LOCK tx_lock; /* always acquire rx_lock before tx_lock */
  LIST_ENTRY tx_waiting_pkt_list;
  netif_tx_sring_t *tx_sring;
  grant_ref_t tx_sring_gref;
  struct netif_tx_front_ring tx_ring;
  ULONG tx_ring_free;
  tx_shadow_t tx_shadows[NET_TX_RING_SIZE];
  ULONG tx_outstanding;
  ULONG tx_id_free;
  USHORT tx_id_list[NET_TX_RING_SIZE];
  NPAGED_LOOKASIDE_LIST tx_lookaside_list;
  KEVENT tx_idle_event;

  /* rx_related - protected by rx_lock */
  KSPIN_LOCK rx_lock; /* always acquire rx_lock before tx_lock */
  netif_rx_sring_t *rx_sring;
  grant_ref_t rx_sring_gref;
  struct netif_rx_front_ring rx_ring;
  ULONG rx_id_free;
  packet_info_t *rxpi;
  #if NTDDI_VERSION < NTDDI_VISTA
  #else
  NDIS_HANDLE rx_nbl_pool;
  #endif
  NDIS_HANDLE rx_packet_pool;
  volatile LONG rx_pb_free;
  struct stack_state *rx_pb_stack;
  volatile LONG rx_hb_free;
  struct stack_state *rx_hb_stack;
  shared_buffer_t *rx_ring_pbs[NET_RX_RING_SIZE];
  /* Receive-ring batched refills. */
  ULONG rx_target;
  ULONG rx_max_target;
  ULONG rx_min_target;
  shared_buffer_t *rx_partial_buf;
  BOOLEAN rx_partial_extra_info_flag ;
  BOOLEAN rx_partial_more_data_flag;
  KEVENT rx_idle_event;
  /* how many packets are in the net stack atm */
  LONG rx_outstanding;


  /* config vars from registry */
  /* the frontend_* indicate our willingness to support */
  BOOLEAN frontend_sg_supported;
  BOOLEAN frontend_csum_supported;
  ULONG frontend_gso_value;
  ULONG frontend_mtu_value;
  ULONG frontend_gso_rx_split_type; /* RX_LSO_SPLIT_* */

  BOOLEAN backend_sg_supported;
  BOOLEAN backend_csum_supported;
  ULONG backend_gso_value;
  
  BOOLEAN current_sg_supported;
  BOOLEAN current_csum_supported;
  ULONG current_gso_value;
  ULONG current_mtu_value;
  ULONG current_gso_rx_split_type;

  BOOLEAN config_csum_rx_check;
  BOOLEAN config_csum_rx_dont_fix;
  BOOLEAN config_rx_coalesce;

  #if NTDDI_VERSION < NTDDI_VISTA
  NDIS_TASK_TCP_IP_CHECKSUM setting_csum;
  #else
  #endif

  /* config stuff calculated from the above */
  ULONG config_max_pkt_size;

  /* stats */
  #if NTDDI_VERSION < NTDDI_VISTA
  ULONG64 stat_tx_ok;
  ULONG64 stat_rx_ok;
  ULONG64 stat_tx_error;
  ULONG64 stat_rx_error;
  ULONG64 stat_rx_no_buffer;
  #else
  NDIS_STATISTICS_INFO stats;
  #endif
  
} typedef xennet_info_t;

extern USHORT ndis_os_major_version;
extern USHORT ndis_os_minor_version;

typedef NDIS_STATUS (*XEN_OID_REQUEST)(NDIS_HANDLE context, PVOID information_buffer, ULONG information_buffer_length, PULONG bytes_read, PULONG bytes_needed);

struct xennet_oids_t {
  ULONG oid;
  char *oid_name;
  ULONG min_length;
  XEN_OID_REQUEST query_routine;
  XEN_OID_REQUEST set_routine;
};

extern struct xennet_oids_t xennet_oids[];

#if NTDDI_VERSION < NTDDI_VISTA
NDIS_STATUS
XenNet_QueryInformation(
  IN NDIS_HANDLE MiniportAdapterContext,
  IN NDIS_OID Oid,
  IN PVOID InformationBuffer,
  IN ULONG InformationBufferLength,
  OUT PULONG BytesWritten,
  OUT PULONG BytesNeeded);

NDIS_STATUS
XenNet_SetInformation(
  IN NDIS_HANDLE MiniportAdapterContext,
  IN NDIS_OID Oid,
  IN PVOID InformationBuffer,
  IN ULONG InformationBufferLength,
  OUT PULONG BytesRead,
  OUT PULONG BytesNeeded
  );

VOID
XenNet_SendPackets(
  IN NDIS_HANDLE MiniportAdapterContext,
  IN PPNDIS_PACKET PacketArray,
  IN UINT NumberOfPackets
  );

VOID
XenNet_ReturnPacket(
  IN NDIS_HANDLE MiniportAdapterContext,
  IN PNDIS_PACKET Packet
  );
#else

MINIPORT_OID_REQUEST XenNet_OidRequest;
MINIPORT_CANCEL_OID_REQUEST XenNet_CancelOidRequest;

MINIPORT_SEND_NET_BUFFER_LISTS XenNet_SendNetBufferLists;
MINIPORT_CANCEL_SEND XenNet_CancelSend;

MINIPORT_RETURN_NET_BUFFER_LISTS XenNet_ReturnNetBufferLists;
#endif

NTSTATUS XenNet_Connect(PVOID context, BOOLEAN suspend);
NTSTATUS XenNet_Disconnect(PVOID context, BOOLEAN suspend);
VOID XenNet_DeviceCallback(PVOID context, ULONG callback_type, PVOID value);


BOOLEAN XenNet_RxInit(xennet_info_t *xi);
VOID XenNet_RxShutdown(xennet_info_t *xi);
BOOLEAN XenNet_RxBufferCheck(struct xennet_info *xi);

BOOLEAN XenNet_TxInit(xennet_info_t *xi);
BOOLEAN XenNet_TxShutdown(xennet_info_t *xi);
VOID XenNet_TxBufferGC(struct xennet_info *xi, BOOLEAN dont_set_event);


/* return values */
#define PARSE_OK 0
#define PARSE_TOO_SMALL 1 /* first buffer is too small */
#define PARSE_UNKNOWN_TYPE 2

BOOLEAN XenNet_BuildHeader(packet_info_t *pi, PVOID header, ULONG new_header_size);
VOID XenNet_ParsePacketHeader(packet_info_t *pi, PUCHAR buffer, ULONG min_header_size);
BOOLEAN XenNet_FilterAcceptPacket(struct xennet_info *xi, packet_info_t *pi);

BOOLEAN XenNet_CheckIpHeaderSum(PUCHAR header, USHORT ip4_header_length);
VOID XenNet_SumIpHeader(PUCHAR header, USHORT ip4_header_length);

static __forceinline VOID
XenNet_ClearPacketInfo(packet_info_t *pi) {
  RtlZeroMemory(pi, sizeof(packet_info_t) - FIELD_OFFSET(packet_info_t, header_data));
}

/* Get some data from the current packet, but don't cross a page boundry. */
static __forceinline ULONG
XenNet_QueryData(packet_info_t *pi, ULONG length) {
  ULONG offset_in_page;
  
  if (length > MmGetMdlByteCount(pi->curr_mdl) - pi->curr_mdl_offset)
    length = MmGetMdlByteCount(pi->curr_mdl) - pi->curr_mdl_offset;

  offset_in_page = (MmGetMdlByteOffset(pi->curr_mdl) + pi->curr_mdl_offset) & (PAGE_SIZE - 1);
  if (offset_in_page + length > PAGE_SIZE)
    length = PAGE_SIZE - offset_in_page;
  
  return length;
}

/* Move the pointers forward by the given amount. No error checking is done.  */
static __forceinline VOID
XenNet_EatData(packet_info_t *pi, ULONG length) {
  pi->curr_mdl_offset += length;
  if (pi->curr_mdl_offset >= MmGetMdlByteCount(pi->curr_mdl)) {
    pi->curr_mdl_offset -= MmGetMdlByteCount(pi->curr_mdl);
#if NTDDI_VERSION < NTDDI_VISTA
    NdisGetNextBuffer(pi->curr_mdl, &pi->curr_mdl);
#else
    NdisGetNextMdl(pi->curr_mdl, &pi->curr_mdl);
#endif
  }
}
