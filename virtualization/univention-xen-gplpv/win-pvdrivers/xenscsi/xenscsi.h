#if !defined(_XENSCSI_H_)
#define _XENSCSI_H_

#include <ntifs.h>
#include <ntddk.h>
#include <wdm.h>
#include <initguid.h>
#include <ntdddisk.h>
//#include <srb.h>

#define NTSTRSAFE_LIB
#include <ntstrsafe.h>

#define __DRIVER_NAME "XenSCSI"

#include <xen_windows.h>
#include <memory.h>
#include <grant_table.h>
#include <event_channel.h>
#include <hvm/params.h>
#include <hvm/hvm_op.h>
#include <xen_public.h>
#include <io/ring.h>
#include <io/vscsiif.h>

//#include <io/blkif.h>
//#include <storport.h>
#include <scsi.h>
//#include <ntddscsi.h>
//#include <ntdddisk.h>
#include <stdlib.h>
#include <io/xenbus.h>
#include <io/protocols.h>


typedef struct vscsiif_request vscsiif_request_t;
typedef struct vscsiif_response vscsiif_response_t;

#define XENSCSI_POOL_TAG (ULONG) 'XSCS'

#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))
#define VSCSIIF_RING_SIZE __RING_SIZE((vscsiif_sring_t *)0, PAGE_SIZE)

typedef struct {
  vscsiif_request_t req;
  PSCSI_REQUEST_BLOCK Srb;
} vscsiif_shadow_t;

#define SHADOW_ENTRIES 32
#define MAX_GRANT_ENTRIES 512

#define SCSI_DEV_NODEV ((ULONG)-1)

typedef struct {
  LIST_ENTRY entry;
  ULONG dev_no; // SCSI_DEV_NODEV == end
  ULONG state;
  BOOLEAN validated;
  UCHAR host;
  UCHAR channel;
  UCHAR id;
  UCHAR lun;
} scsi_dev_t;

#if 0
#define SCSI_STATE_ENUM_PENDING     0
#define SCSI_STATE_ENUM_IN_PROGRESS 1
#define SCSI_STATE_ENUM_COMPLETE    2

#define XENSCSI_MAX_ENUM_TIME 5
#endif

#define SHARED_PAUSED_SCSIPORT_UNPAUSED 0
#define SHARED_PAUSED_PASSIVE_PAUSED    1
#define SHARED_PAUSED_SCSIPORT_PAUSED   2
#define SHARED_PAUSED_PASSIVE_UNPAUSED  3

struct
{
  vscsiif_shadow_t shadows[SHADOW_ENTRIES];
  USHORT shadow_free_list[SHADOW_ENTRIES];
  USHORT shadow_free;

  grant_ref_t grant_free_list[MAX_GRANT_ENTRIES];
  USHORT grant_free;
  USHORT grant_entries;

  evtchn_port_t event_channel;

  vscsiif_front_ring_t ring;
  
  XENPCI_VECTORS vectors;
  
  LIST_ENTRY dev_list_head;
    
  //BOOLEAN pause_req;
  //BOOLEAN pause_ack;
  volatile LONG shared_paused;
  ULONG scsiport_paused; /* scsiport code has acknowledged pause */
  ULONG bus_changes[8];
} typedef XENSCSI_DEVICE_DATA, *PXENSCSI_DEVICE_DATA;

struct {
  UCHAR sense_len;
  UCHAR sense_buffer[VSCSIIF_SENSE_BUFFERSIZE];
} typedef XENSCSI_LU_DATA, *PXENSCSI_LU_DATA;

enum dma_data_direction {
        DMA_BIDIRECTIONAL = 0,
        DMA_TO_DEVICE = 1,
        DMA_FROM_DEVICE = 2,
        DMA_NONE = 3,
};

VOID
XenScsi_FillInitCallbacks(PHW_INITIALIZATION_DATA HwInitializationData);

#endif
