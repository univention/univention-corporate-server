/*
PV Drivers for Windows Xen HVM Domains
Copyright (C) 2007 James Harper

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

#define INITGUID
#include "xenvbd_storport.h"

#pragma warning(disable: 4127)

#if defined(__x86_64__)
  #define LongLongToPtr(x) (PVOID)(x)
#else
  #define LongLongToPtr(x) UlongToPtr(x)
#endif

/* Not really necessary but keeps PREfast happy */
DRIVER_INITIALIZE DriverEntry;
static BOOLEAN XenVbd_HandleEvent(PVOID DeviceExtension);

static BOOLEAN dump_mode = FALSE;
#define DUMP_MODE_ERROR_LIMIT 64
static ULONG dump_mode_errors = 0;

CHAR scsi_device_manufacturer[8];
CHAR scsi_disk_model[16];
CHAR scsi_cdrom_model[16];

ULONGLONG parse_numeric_string(PCHAR string)
{
  ULONGLONG val = 0;
  while (*string != 0)
  {
    val = val * 10 + (*string - '0');
    string++;
  }
  return val;
}

static blkif_shadow_t *
get_shadow_from_freelist(PXENVBD_DEVICE_DATA xvdd)
{
  if (xvdd->shadow_free == 0)
  {
    KdPrint((__DRIVER_NAME "     No more shadow entries\n"));
    return NULL;
  }
  xvdd->shadow_free--;
  if (xvdd->shadow_free < xvdd->shadow_min_free)
    xvdd->shadow_min_free = xvdd->shadow_free;
  return &xvdd->shadows[xvdd->shadow_free_list[xvdd->shadow_free]];
}

static VOID
put_shadow_on_freelist(PXENVBD_DEVICE_DATA xvdd, blkif_shadow_t *shadow)
{
  xvdd->shadow_free_list[xvdd->shadow_free] = (USHORT)(shadow->req.id & SHADOW_ID_ID_MASK);
  shadow->srb = NULL;
  shadow->reset = FALSE;
  xvdd->shadow_free++;
}

static blkif_response_t *
XenVbd_GetResponse(PXENVBD_DEVICE_DATA xvdd, int i)
{
  blkif_other_response_t *rep;
  if (!xvdd->use_other)
    return RING_GET_RESPONSE(&xvdd->ring, i);
  rep = RING_GET_RESPONSE(&xvdd->other_ring, i);
  xvdd->tmp_rep.id = rep->id;
  xvdd->tmp_rep.operation = rep->operation;
  xvdd->tmp_rep.status = rep->status;
  return &xvdd->tmp_rep;
}

static VOID
XenVbd_PutRequest(PXENVBD_DEVICE_DATA xvdd, blkif_request_t *req)
{
  blkif_other_request_t *other_req;

  if (!xvdd->use_other)
  {
    *RING_GET_REQUEST(&xvdd->ring, xvdd->ring.req_prod_pvt) = *req;
  }
  else
  {  
    other_req = RING_GET_REQUEST(&xvdd->other_ring, xvdd->ring.req_prod_pvt);
    other_req->operation = req->operation;
    other_req->nr_segments = req->nr_segments;
    other_req->handle = req->handle;
    other_req->id = req->id;
    other_req->sector_number = req->sector_number;
    memcpy(other_req->seg, req->seg, sizeof(struct blkif_request_segment) * req->nr_segments);
  }
  xvdd->ring.req_prod_pvt++;
}

static ULONG
XenVbd_InitConfig(PXENVBD_DEVICE_DATA xvdd)
{
  ULONG status;
  PUCHAR ptr;
  USHORT type;
  PCHAR setting, value, value2;

  FUNCTION_ENTER();
  /* first read the default config items */
  ptr = xvdd->device_base;
  while((type = GET_XEN_INIT_RSP(&ptr, (PVOID)&setting, (PVOID)&value, (PVOID)&value2)) != XEN_INIT_TYPE_END)
  {
    switch(type)
    {
    case XEN_INIT_TYPE_VECTORS:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_VECTORS\n"));
      if (((PXENPCI_VECTORS)value)->length != sizeof(XENPCI_VECTORS) ||
        ((PXENPCI_VECTORS)value)->magic != XEN_DATA_MAGIC)
      {
        KdPrint((__DRIVER_NAME "     vectors mismatch (magic = %08x, length = %d)\n",
          ((PXENPCI_VECTORS)value)->magic, ((PXENPCI_VECTORS)value)->length));
        KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ "\n"));
        return SP_RETURN_BAD_CONFIG;
      }
      else
        memcpy(&xvdd->vectors, value, sizeof(XENPCI_VECTORS));
      break;
    default:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_%d\n", type));
      break;
    }
  }

  /* then set up all the configuration requests */
  ptr = xvdd->device_base;
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_RING, "ring-ref", NULL, NULL);
  #pragma warning(suppress:4054)
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_EVENT_CHANNEL_DPC, "event-channel", (PVOID)XenVbd_HandleEvent, xvdd);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_READ_STRING_FRONT, "device-type", NULL, NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_READ_STRING_BACK, "mode", NULL, NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_READ_STRING_BACK, "sectors", NULL, NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_READ_STRING_BACK, "sector-size", NULL, NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_XB_STATE_MAP_PRE_CONNECT, NULL, NULL, NULL);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateInitialised);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateConnected);
  __ADD_XEN_INIT_UCHAR(&ptr, 20);
  __ADD_XEN_INIT_UCHAR(&ptr, 0);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_XB_STATE_MAP_POST_CONNECT, NULL, NULL, NULL);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateConnected);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateConnected);
  __ADD_XEN_INIT_UCHAR(&ptr, 20);
  __ADD_XEN_INIT_UCHAR(&ptr, 0);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_XB_STATE_MAP_SHUTDOWN, NULL, NULL, NULL);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateClosing);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateClosing);
  __ADD_XEN_INIT_UCHAR(&ptr, 50);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateClosed);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateClosed);
  __ADD_XEN_INIT_UCHAR(&ptr, 50);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateInitialising);
  __ADD_XEN_INIT_UCHAR(&ptr, XenbusStateInitWait);
  __ADD_XEN_INIT_UCHAR(&ptr, 50);
  __ADD_XEN_INIT_UCHAR(&ptr, 0);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_END, NULL, NULL, NULL);

  /* then configure */
  status = xvdd->vectors.XenPci_XenConfigDevice(xvdd->vectors.context);
  if (!NT_SUCCESS(status))
  {
    KdPrint(("Failed to complete device configuration (%08x)\n", status));
    FUNCTION_EXIT();
    return SP_RETURN_BAD_CONFIG;
  }
  FUNCTION_EXIT();
  return SP_RETURN_FOUND;
}

static ULONG
XenVbd_InitFromConfig(PXENVBD_DEVICE_DATA xvdd)
{
  ULONG i;
  PUCHAR ptr;
  USHORT type;
  PCHAR setting, value, value2;
  ULONG qemu_protocol_version = 0;
  BOOLEAN qemu_hide_filter = FALSE;
  ULONG qemu_hide_flags_value = 0;

  FUNCTION_ENTER();
  
  xvdd->device_type = XENVBD_DEVICETYPE_UNKNOWN;
  xvdd->sring = NULL;
  xvdd->event_channel = 0;
  
  xvdd->inactive = TRUE;  
  
  ptr = xvdd->device_base;
  while((type = GET_XEN_INIT_RSP(&ptr, (PVOID)&setting, (PVOID)&value, (PVOID)&value2)) != XEN_INIT_TYPE_END)
  {
    switch(type)
    {
    case XEN_INIT_TYPE_VECTORS:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_VECTORS\n"));
      if (dump_mode)
      {
        if (((PXENPCI_VECTORS)value)->length != sizeof(XENPCI_VECTORS) ||
          ((PXENPCI_VECTORS)value)->magic != XEN_DATA_MAGIC)
        {
          KdPrint((__DRIVER_NAME "     vectors mismatch (magic = %08x, length = %d)\n",
            ((PXENPCI_VECTORS)value)->magic, ((PXENPCI_VECTORS)value)->length));
          KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ "\n"));
          return SP_RETURN_BAD_CONFIG;
        }
        else
          memcpy(&xvdd->vectors, value, sizeof(XENPCI_VECTORS));
      }
      break;
    case XEN_INIT_TYPE_RING: /* frontend ring */
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_RING - %s = %p\n", setting, value));
      if (strcmp(setting, "ring-ref") == 0)
      {
        xvdd->sring = (blkif_sring_t *)value;
        FRONT_RING_INIT(&xvdd->ring, xvdd->sring, PAGE_SIZE);
        /* this bit is for when we have to take over an existing ring on a crash dump */
        xvdd->ring.req_prod_pvt = xvdd->sring->req_prod;
        xvdd->ring.rsp_cons = xvdd->ring.req_prod_pvt;
      }
      break;
    case XEN_INIT_TYPE_EVENT_CHANNEL_DPC: /* frontend event channel */
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_EVENT_CHANNEL - %s = %d (%08x)\n", setting, PtrToUlong(value) & 0x3FFFFFFF, PtrToUlong(value)));
      if (strcmp(setting, "event-channel") == 0)
      {
        /* cheat here - save the state of the ring in the topmost bits of the event-channel */
        xvdd->event_channel_ptr = (ULONG *)(((PCHAR)ptr) - sizeof(ULONG));
        xvdd->event_channel = PtrToUlong(value) & 0x3FFFFFFF;
        if (PtrToUlong(value) & 0x80000000)
        {
          xvdd->cached_use_other = (BOOLEAN)!!(PtrToUlong(value) & 0x40000000);
          KdPrint((__DRIVER_NAME "     cached_use_other = %d\n", xvdd->cached_use_other));
        }
      }
      break;
    case XEN_INIT_TYPE_READ_STRING_BACK:
    case XEN_INIT_TYPE_READ_STRING_FRONT:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_READ_STRING - %s = %s\n", setting, value));
      if (strcmp(setting, "sectors") == 0)
        xvdd->total_sectors = parse_numeric_string(value);
      else if (strcmp(setting, "sector-size") == 0)
        xvdd->bytes_per_sector = (ULONG)parse_numeric_string(value);
      else if (strcmp(setting, "device-type") == 0)
      {
        if (strcmp(value, "disk") == 0)
        {
          KdPrint((__DRIVER_NAME "     device-type = Disk\n"));    
          xvdd->device_type = XENVBD_DEVICETYPE_DISK;
        }
        else if (strcmp(value, "cdrom") == 0)
        {
          KdPrint((__DRIVER_NAME "     device-type = CDROM\n"));    
          xvdd->device_type = XENVBD_DEVICETYPE_CDROM;
        }
        else
        {
          KdPrint((__DRIVER_NAME "     device-type = %s (This probably won't work!)\n", value));
          xvdd->device_type = XENVBD_DEVICETYPE_UNKNOWN;
        }
      }
      else if (strcmp(setting, "mode") == 0)
      {
        if (strncmp(value, "r", 1) == 0)
        {
          KdPrint((__DRIVER_NAME "     mode = r\n"));    
          xvdd->device_mode = XENVBD_DEVICEMODE_READ;
        }
        else if (strncmp(value, "w", 1) == 0)
        {
          KdPrint((__DRIVER_NAME "     mode = w\n"));    
          xvdd->device_mode = XENVBD_DEVICEMODE_WRITE;
        }
        else
        {
          KdPrint((__DRIVER_NAME "     mode = unknown\n"));
          xvdd->device_mode = XENVBD_DEVICEMODE_UNKNOWN;
        }
      }
      break;
    case XEN_INIT_TYPE_QEMU_PROTOCOL_VERSION:
      qemu_protocol_version = PtrToUlong(value);
      break;
    case XEN_INIT_TYPE_QEMU_HIDE_FLAGS:
      qemu_hide_flags_value = PtrToUlong(value);
      KdPrint((__DRIVER_NAME "     qemu_hide_flags_value = %d\n", qemu_hide_flags_value));
      break;
    case XEN_INIT_TYPE_QEMU_HIDE_FILTER:
      qemu_hide_filter = TRUE;
      KdPrint((__DRIVER_NAME "     qemu_hide_filter = TRUE\n"));
      break;
    case XEN_INIT_TYPE_STATE_PTR:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_DEVICE_STATE - %p\n", PtrToUlong(value)));
      xvdd->device_state = (PXENPCI_DEVICE_STATE)value;
      break;
    default:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_%d\n", type));
      break;
    }
  }

  if (((qemu_hide_flags_value & QEMU_UNPLUG_ALL_IDE_DISKS) && xvdd->device_type != XENVBD_DEVICETYPE_CDROM) || qemu_hide_filter)
    xvdd->inactive = FALSE;
  
  if (!xvdd->inactive && (xvdd->device_type == XENVBD_DEVICETYPE_UNKNOWN
      || xvdd->sring == NULL
      || xvdd->event_channel == 0
      || xvdd->total_sectors == 0
      || xvdd->bytes_per_sector == 0))
  {
    KdPrint((__DRIVER_NAME "     Missing settings\n"));
    FUNCTION_EXIT();
    return SP_RETURN_BAD_CONFIG;
  }

  if (xvdd->inactive)
    KdPrint((__DRIVER_NAME "     Device is inactive\n"));
  else
  {
    if (xvdd->device_type == XENVBD_DEVICETYPE_CDROM)
    {
      /* CD/DVD drives must have bytes_per_sector = 2048. */
      xvdd->bytes_per_sector = 2048;
    }

    /* for some reason total_sectors is measured in 512 byte sectors always, so correct this to be in bytes_per_sectors */
    xvdd->total_sectors /= xvdd->bytes_per_sector / 512;

    xvdd->shadow_free = 0;
    memset(xvdd->shadows, 0, sizeof(blkif_shadow_t) * SHADOW_ENTRIES);
    for (i = 0; i < SHADOW_ENTRIES; i++)
    {
      xvdd->shadows[i].req.id = i;
      /* make sure leftover real requests's are never confused with dump mode requests */
      if (dump_mode)
        xvdd->shadows[i].req.id |= SHADOW_ID_DUMP_FLAG;
      put_shadow_on_freelist(xvdd, &xvdd->shadows[i]);
    }
  }

  FUNCTION_EXIT();
  return SP_RETURN_FOUND;
}

static __inline ULONG
decode_cdb_length(PSCSI_REQUEST_BLOCK srb)
{
  switch (srb->Cdb[0])
  {
  case SCSIOP_READ:
  case SCSIOP_WRITE:
    return ((ULONG)(UCHAR)srb->Cdb[7] << 8) | (ULONG)(UCHAR)srb->Cdb[8];
  case SCSIOP_READ16:
  case SCSIOP_WRITE16:
    return ((ULONG)(UCHAR)srb->Cdb[10] << 24) | ((ULONG)(UCHAR)srb->Cdb[11] << 16) | ((ULONG)(UCHAR)srb->Cdb[12] << 8) | (ULONG)(UCHAR)srb->Cdb[13];    
  default:
    return 0;
  }
}

static __inline ULONGLONG
decode_cdb_sector(PSCSI_REQUEST_BLOCK srb)
{
  ULONGLONG sector;
  
  switch (srb->Cdb[0])
  {
  case SCSIOP_READ:
  case SCSIOP_WRITE:
    sector = ((ULONG)(UCHAR)srb->Cdb[2] << 24) | ((ULONG)(UCHAR)srb->Cdb[3] << 16) | ((ULONG)(UCHAR)srb->Cdb[4] << 8) | (ULONG)(UCHAR)srb->Cdb[5];
    break;
  case SCSIOP_READ16:
  case SCSIOP_WRITE16:
    sector = ((ULONGLONG)(UCHAR)srb->Cdb[2] << 56) | ((ULONGLONG)(UCHAR)srb->Cdb[3] << 48)
           | ((ULONGLONG)(UCHAR)srb->Cdb[4] << 40) | ((ULONGLONG)(UCHAR)srb->Cdb[5] << 32)
           | ((ULONGLONG)(UCHAR)srb->Cdb[6] << 24) | ((ULONGLONG)(UCHAR)srb->Cdb[7] << 16)
           | ((ULONGLONG)(UCHAR)srb->Cdb[8] << 8) | ((ULONGLONG)(UCHAR)srb->Cdb[9]);
    //KdPrint((__DRIVER_NAME "     sector_number = %d (high) %d (low)\n", (ULONG)(sector >> 32), (ULONG)sector));
    break;
  default:
    sector = 0;
    break;
  }
  return sector;
}

static __inline BOOLEAN
decode_cdb_is_read(PSCSI_REQUEST_BLOCK srb)
{
  switch (srb->Cdb[0])
  {
  case SCSIOP_READ:
  case SCSIOP_READ16:
    return TRUE;
  case SCSIOP_WRITE:
  case SCSIOP_WRITE16:
    return FALSE;
  default:
    return FALSE;
  }
}

static VOID
XenVbd_PutSrbOnList(PXENVBD_DEVICE_DATA xvdd, PSCSI_REQUEST_BLOCK srb)
{
  srb_list_entry_t *srb_entry = srb->SrbExtension;
  srb_entry->srb = srb;
  if (srb->Function == SRB_FUNCTION_EXECUTE_SCSI)
  {
    srb_entry->outstanding_requests = 0;
    srb_entry->length = srb->DataTransferLength;
    srb_entry->offset = 0;
    srb_entry->error = FALSE;
  }
  InsertTailList(&xvdd->srb_list, (PLIST_ENTRY)srb_entry);
}

static VOID
XenVbd_PutQueuedSrbsOnRing(PXENVBD_DEVICE_DATA xvdd)
{
  PSCSI_REQUEST_BLOCK srb;
  srb_list_entry_t *srb_entry;
  ULONGLONG sector_number;
  ULONG block_count;
  blkif_shadow_t *shadow;
  ULONG remaining, offset, length;
  grant_ref_t gref;
  PUCHAR ptr;
  int notify;
  int i;
  PVOID system_address;

  //if (dump_mode) FUNCTION_ENTER();

  while(!xvdd->aligned_buffer_in_use && xvdd->shadow_free && (srb_entry = (srb_list_entry_t *)RemoveHeadList(&xvdd->srb_list)) != (srb_list_entry_t *)&xvdd->srb_list)
  {
    srb = srb_entry->srb;
    ASSERT(srb);
    if (srb->Function != SRB_FUNCTION_EXECUTE_SCSI)
    {
      KdPrint((__DRIVER_NAME "     SRB_FUNCTION_%02x retrieved from ring\n", srb->Function));
      if (xvdd->shadow_free != SHADOW_ENTRIES)
      {
        KdPrint((__DRIVER_NAME "     busy\n"));
        /* put it back at the end of the list just in case something is queued that needs to be processed */
        InsertTailList(&xvdd->srb_list, (PLIST_ENTRY)srb->SrbExtension);
        break; /* stall the queue until it's all empty */
      }
      else
      {
        KdPrint((__DRIVER_NAME "     completing\n"));
        srb->SrbStatus = SRB_STATUS_SUCCESS;
        StorPortNotification(RequestComplete, xvdd, srb);
        continue;
      }
    }

    if (!dump_mode)
    {
      if (StorPortGetSystemAddress(xvdd, srb, &system_address) != STOR_STATUS_SUCCESS)
      {
        KdPrint((__DRIVER_NAME "     Failed to map DataBuffer\n"));
        srb->SrbStatus = SRB_STATUS_BUSY;
        StorPortNotification(RequestComplete, xvdd, srb);
        continue;
      }
      system_address = (PUCHAR)system_address + srb_entry->offset;
    }
    else
    {
      //KdPrint((__DRIVER_NAME "     DataBuffer = %p\n", srb->DataBuffer));
      system_address = (PUCHAR)srb->DataBuffer + srb_entry->offset;
    }
    block_count = decode_cdb_length(srb);
    block_count *= xvdd->bytes_per_sector / 512;
    sector_number = decode_cdb_sector(srb);
    sector_number *= xvdd->bytes_per_sector / 512;

    ASSERT(block_count * xvdd->bytes_per_sector == srb->DataTransferLength);
    
    //KdPrint((__DRIVER_NAME "     srb sector_number = %d, block_count = %d\n", (ULONG)sector_number, block_count));
    
    sector_number += srb_entry->offset / 512;
    block_count -= srb_entry->offset / 512;

    /* look for pending writes that overlap this one */
    /* we get warnings from drbd if we don't */
    if (srb_entry->offset == 0)
    {
      for (i = 0; i < MAX_SHADOW_ENTRIES; i++)
      {
        PSCSI_REQUEST_BLOCK srb2;
        ULONGLONG sector_number2;
        ULONG block_count2;
        
        srb2 = xvdd->shadows[i].srb;
        if (!srb2)
          continue;
        if (decode_cdb_is_read(srb2))
          continue;
        block_count2 = decode_cdb_length(srb2);;
        block_count2 *= xvdd->bytes_per_sector / 512;
        sector_number2 = decode_cdb_sector(srb2);
        sector_number2 *= xvdd->bytes_per_sector / 512;
        
        if (sector_number < sector_number2 && sector_number + block_count <= sector_number2)
          continue;
        if (sector_number2 < sector_number && sector_number2 + block_count2 <= sector_number)
          continue;

        KdPrint((__DRIVER_NAME "     Concurrent outstanding write detected (%I64d, %d) (%I64d, %d)\n",
          sector_number, block_count, sector_number2, block_count2));
        /* put the srb back at the start of the queue */
        InsertHeadList(&xvdd->srb_list, (PLIST_ENTRY)srb->SrbExtension);
        break; /* stall the queue */
      }
      if (i != MAX_SHADOW_ENTRIES)
      {
        break; /* stall the queue but submit any outstanding requests */
      }
    }
    
    shadow = get_shadow_from_freelist(xvdd);
    if (!shadow)
    {
      /* put the srb back at the start of the queue */
      InsertHeadList(&xvdd->srb_list, (PLIST_ENTRY)srb->SrbExtension);
      break; /* stall the queue but submit any outstanding requests */
    }
    ASSERT(!shadow->aligned_buffer_in_use);
    ASSERT(!shadow->srb);
    shadow->req.sector_number = sector_number;
    shadow->req.handle = 0;
    shadow->req.operation = decode_cdb_is_read(srb)?BLKIF_OP_READ:BLKIF_OP_WRITE;
    shadow->req.nr_segments = 0;
    shadow->srb = srb;
    shadow->length = 0;
    shadow->system_address = system_address;
    shadow->reset = FALSE;

    if (!dump_mode)
    {
      if ((ULONG_PTR)shadow->system_address & 511)
      {
        xvdd->aligned_buffer_in_use = TRUE;
        /* limit to aligned_buffer_size */
        block_count = min(block_count, xvdd->aligned_buffer_size / 512);
        ptr = (PUCHAR)xvdd->aligned_buffer;
        if (!decode_cdb_is_read(srb))
          memcpy(ptr, shadow->system_address, block_count * 512);
        shadow->aligned_buffer_in_use = TRUE;
      }
      else
      {
        ptr = (PUCHAR)shadow->system_address;
        shadow->aligned_buffer_in_use = FALSE;
      }
    }
    else
    {
      ASSERT(!((ULONG_PTR)shadow->system_address & 511));
      ptr = shadow->system_address;
      shadow->aligned_buffer_in_use = FALSE;
    }

    //KdPrint((__DRIVER_NAME "     sector_number = %d, block_count = %d\n", (ULONG)sector_number, block_count));
    //KdPrint((__DRIVER_NAME "     DataBuffer   = %p\n", srb->DataBuffer));
    //KdPrint((__DRIVER_NAME "     system_address   = %p\n", shadow->system_address));
    //KdPrint((__DRIVER_NAME "     offset   = %d, length = %d\n", srb_entry->offset, srb_entry->length));
    //KdPrint((__DRIVER_NAME "     ptr   = %p\n", ptr));

    //KdPrint((__DRIVER_NAME "     handle = %d\n", shadow->req.handle));
    //KdPrint((__DRIVER_NAME "     operation = %d\n", shadow->req.operation));
    
    remaining = block_count * 512;
    while (remaining > 0 && shadow->req.nr_segments < BLKIF_MAX_SEGMENTS_PER_REQUEST)
    {
      PHYSICAL_ADDRESS physical_address;

      if (!dump_mode)
      {
        physical_address = MmGetPhysicalAddress(ptr);
      }
      else
      {
        ULONG length;       
        physical_address = StorPortGetPhysicalAddress(xvdd, srb, ptr, &length);
      }
      gref = xvdd->vectors.GntTbl_GrantAccess(xvdd->vectors.context, 0,
             (ULONG)(physical_address.QuadPart >> PAGE_SHIFT), FALSE, INVALID_GRANT_REF, xvdd->grant_tag);
      if (gref == INVALID_GRANT_REF)
      {
        ULONG i;
        for (i = 0; i < shadow->req.nr_segments; i++)
        {
          xvdd->vectors.GntTbl_EndAccess(xvdd->vectors.context,
            shadow->req.seg[i].gref, FALSE, xvdd->grant_tag);
        }
        if (shadow->aligned_buffer_in_use)
        {
          shadow->aligned_buffer_in_use = FALSE;
          xvdd->aligned_buffer_in_use = FALSE;
        }
        /* put the srb back at the start of the queue */
        InsertHeadList(&xvdd->srb_list, (PLIST_ENTRY)srb->SrbExtension);
        put_shadow_on_freelist(xvdd, shadow);
        KdPrint((__DRIVER_NAME "     Out of gref's. Deferring\n"));
        break; /* stall the queue but submit any outstanding requests */
      }
      offset = physical_address.LowPart & (PAGE_SIZE - 1);
      length = min(PAGE_SIZE - offset, remaining);
      //if (dump_mode) KdPrint((__DRIVER_NAME "     length = %d\n", length));
      //if (dump_mode) KdPrint((__DRIVER_NAME "     offset = %d\n", length));
      ASSERT((offset & 511) == 0);
      ASSERT((length & 511) == 0);
      ASSERT(offset + length <= PAGE_SIZE);
      shadow->req.seg[shadow->req.nr_segments].gref = gref;
      shadow->req.seg[shadow->req.nr_segments].first_sect = (UCHAR)(offset / 512);
      shadow->req.seg[shadow->req.nr_segments].last_sect = (UCHAR)(((offset + length) / 512) - 1);
      //if (dump_mode) KdPrint((__DRIVER_NAME "     gref = %d\n", shadow->req.seg[shadow->req.nr_segments].gref));
      //if (dump_mode) KdPrint((__DRIVER_NAME "     first_sect = %d\n", shadow->req.seg[shadow->req.nr_segments].first_sect));
      //if (dump_mode) KdPrint((__DRIVER_NAME "     last_sect = %d\n", shadow->req.seg[shadow->req.nr_segments].last_sect));
      remaining -= length;
      ptr += length;
      shadow->length += length;
      shadow->req.nr_segments++;
    }
    srb_entry->offset += shadow->length;
    srb_entry->outstanding_requests++;
    //KdPrint((__DRIVER_NAME "     outstanding_requests   = %p\n", srb_entry->outstanding_requests));
    //KdPrint((__DRIVER_NAME "     offset   = %d, length = %d\n", srb_entry->offset, srb_entry->length));
    //KdPrint((__DRIVER_NAME "     ptr   = %p\n", ptr));
    if (srb_entry->offset < srb_entry->length)
    {
      if (dump_mode) KdPrint((__DRIVER_NAME "     inserting back into list\n"));
      /* put the srb back at the start of the queue to continue on the next request */
      InsertHeadList(&xvdd->srb_list, (PLIST_ENTRY)srb_entry);
    }

    XenVbd_PutRequest(xvdd, &shadow->req);
  }
  RING_PUSH_REQUESTS_AND_CHECK_NOTIFY(&xvdd->ring, notify);
  if (notify)
  {
    //KdPrint((__DRIVER_NAME "     Notifying\n"));
    xvdd->vectors.EvtChn_Notify(xvdd->vectors.context, xvdd->event_channel);
  }
    
  //if (dump_mode) FUNCTION_EXIT();
}

static ULONG
XenVbd_VirtualHwStorFindAdapter(PVOID DeviceExtension, PVOID HwContext, PVOID BusInformation, PVOID LowerDevice, PCHAR ArgumentString, PPORT_CONFIGURATION_INFORMATION ConfigInfo, PBOOLEAN Again)
{
//  PACCESS_RANGE AccessRange;
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)DeviceExtension;
  ULONG status;
//  PXENPCI_XEN_DEVICE_DATA XenDeviceData;
  PACCESS_RANGE access_range;

  UNREFERENCED_PARAMETER(HwContext);
  UNREFERENCED_PARAMETER(BusInformation);
  UNREFERENCED_PARAMETER(LowerDevice);
  UNREFERENCED_PARAMETER(ArgumentString);

  FUNCTION_ENTER(); 
  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));
  KdPrint((__DRIVER_NAME "     xvdd = %p\n", xvdd));

  RtlZeroMemory(xvdd, sizeof(XENVBD_DEVICE_DATA));
  *Again = FALSE;

  KdPrint((__DRIVER_NAME "     BusInterruptLevel = %d\n", ConfigInfo->BusInterruptLevel));
  KdPrint((__DRIVER_NAME "     BusInterruptVector = %03x\n", ConfigInfo->BusInterruptVector));

  if (!dump_mode)
  {
    KdPrint((__DRIVER_NAME "     NumberOfAccessRanges = %d\n", ConfigInfo->NumberOfAccessRanges));    
    if (ConfigInfo->NumberOfAccessRanges != 1 && ConfigInfo->NumberOfAccessRanges != 2)
    {
      return SP_RETURN_BAD_CONFIG;
    }

    access_range = &((*(ConfigInfo->AccessRanges))[0]);
    KdPrint((__DRIVER_NAME "     RangeStart = %08x, RangeLength = %08x\n",
      access_range->RangeStart.LowPart, access_range->RangeLength));
    xvdd->device_base = StorPortGetDeviceBase(
      DeviceExtension,
      PNPBus, //AdapterInterfaceType,
      ConfigInfo->SystemIoBusNumber,
      access_range->RangeStart,
      access_range->RangeLength,
      !access_range->RangeInMemory);
    if (!xvdd->device_base)
    {
      KdPrint((__DRIVER_NAME "     StorPortGetDeviceBase failed\n"));
      FUNCTION_EXIT(); 
      return SP_RETURN_BAD_CONFIG;
    }
    status = XenVbd_InitConfig(xvdd);
    if (status != SP_RETURN_FOUND)
    {
      FUNCTION_EXIT();
      return status;
    }
    xvdd->grant_tag = (ULONG)'VBD0';
  }
  else
  {
    xvdd->device_base = ConfigInfo->Reserved;
    xvdd->grant_tag = (ULONG)'DUMP';
  }
  
  xvdd->ring_detect_state = RING_DETECT_STATE_NOT_STARTED;
  status = XenVbd_InitFromConfig(xvdd);
  if (status != SP_RETURN_FOUND)
  {
    FUNCTION_EXIT();
    return status;
  }

  xvdd->aligned_buffer_in_use = FALSE;
  /* align the buffer to PAGE_SIZE */
  xvdd->aligned_buffer = (PVOID)((ULONG_PTR)((PUCHAR)xvdd->aligned_buffer_data + PAGE_SIZE - 1) & ~(PAGE_SIZE - 1));
  KdPrint((__DRIVER_NAME "     aligned_buffer_data = %p\n", xvdd->aligned_buffer_data));
  KdPrint((__DRIVER_NAME "     aligned_buffer = %p\n", xvdd->aligned_buffer));

  ConfigInfo->MaximumTransferLength = 4 * 1024 * 1024; //BLKIF_MAX_SEGMENTS_PER_REQUEST * PAGE_SIZE;
  ConfigInfo->NumberOfPhysicalBreaks = ConfigInfo->MaximumTransferLength >> PAGE_SHIFT; //BLKIF_MAX_SEGMENTS_PER_REQUEST - 1;
  KdPrint((__DRIVER_NAME "     ConfigInfo->MaximumTransferLength = %d\n", ConfigInfo->MaximumTransferLength));
  KdPrint((__DRIVER_NAME "     ConfigInfo->NumberOfPhysicalBreaks = %d\n", ConfigInfo->NumberOfPhysicalBreaks));
  if (!dump_mode)
  {
    ConfigInfo->VirtualDevice = TRUE;
    xvdd->aligned_buffer_size = BLKIF_MAX_SEGMENTS_PER_REQUEST * PAGE_SIZE;
  }
  else
  {
    ConfigInfo->VirtualDevice = FALSE;
    xvdd->aligned_buffer_size = DUMP_MODE_UNALIGNED_PAGES * PAGE_SIZE;
  }
  
  KdPrint((__DRIVER_NAME "     ConfigInfo->VirtualDevice = %d\n", ConfigInfo->VirtualDevice));
  ConfigInfo->ScatterGather = TRUE;
  ConfigInfo->Master = TRUE;
  ConfigInfo->CachesData = FALSE;
  ConfigInfo->MapBuffers = STOR_MAP_ALL_BUFFERS;
  KdPrint((__DRIVER_NAME "     ConfigInfo->NeedPhysicalAddresses = %d\n", ConfigInfo->NeedPhysicalAddresses));
  ConfigInfo->SynchronizationModel = StorSynchronizeFullDuplex;
  ConfigInfo->AlignmentMask = 0;
  ConfigInfo->NumberOfBuses = 1;
  ConfigInfo->InitiatorBusId[0] = 1;
  ConfigInfo->MaximumNumberOfLogicalUnits = 1;
  ConfigInfo->MaximumNumberOfTargets = 2;
  //ConfigInfo->BufferAccessScsiPortControlled = FALSE;
  if (ConfigInfo->Dma64BitAddresses == SCSI_DMA64_SYSTEM_SUPPORTED)
  {
    ConfigInfo->Dma64BitAddresses = SCSI_DMA64_MINIPORT_SUPPORTED;
    //ConfigInfo->Dma32BitAddresses = FALSE;
    KdPrint((__DRIVER_NAME "     Dma64BitAddresses supported\n"));
  }
  else
  {
    //ConfigInfo->Dma32BitAddresses = TRUE;
    KdPrint((__DRIVER_NAME "     Dma64BitAddresses not supported\n"));
  }

  FUNCTION_EXIT();

  return SP_RETURN_FOUND;
}

static ULONG
XenVbd_HwStorFindAdapter(PVOID DeviceExtension, PVOID HwContext, PVOID BusInformation, PCHAR ArgumentString, PPORT_CONFIGURATION_INFORMATION ConfigInfo, PBOOLEAN Again)
{
  ULONG status;
  
  FUNCTION_ENTER();
  status = XenVbd_VirtualHwStorFindAdapter(DeviceExtension, HwContext, BusInformation, NULL, ArgumentString, ConfigInfo, Again);
  FUNCTION_EXIT();
  return status;
}

//do this in StartIo instead to prevent races with the driver initialisation
static VOID
XenVbd_StartRingDetection(PXENVBD_DEVICE_DATA xvdd)
{
  blkif_request_t *req;
  int notify;

  xvdd->ring_detect_state = RING_DETECT_STATE_DETECT1;
  RtlZeroMemory(xvdd->sring->ring, PAGE_SIZE - FIELD_OFFSET(blkif_sring_t, ring));
  req = RING_GET_REQUEST(&xvdd->ring, xvdd->ring.req_prod_pvt);
  req->operation = 0xff;
  xvdd->ring.req_prod_pvt++;
  req = RING_GET_REQUEST(&xvdd->ring, xvdd->ring.req_prod_pvt);
  req->operation = 0xff;
  xvdd->ring.req_prod_pvt++;

  RING_PUSH_REQUESTS_AND_CHECK_NOTIFY(&xvdd->ring, notify);
  if (notify)
    xvdd->vectors.EvtChn_Notify(xvdd->vectors.context, xvdd->event_channel);
}

static BOOLEAN
XenVbd_HwStorInitialize(PVOID DeviceExtension)
{
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)DeviceExtension;
  
  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));
  KdPrint((__DRIVER_NAME "     dump_mode = %d\n", dump_mode));

  if (!xvdd->inactive)
  {
    if (dump_mode)
    {
      if (xvdd->cached_use_other)
      {
        xvdd->ring.nr_ents = BLK_OTHER_RING_SIZE;
        xvdd->use_other = TRUE;
      }
      xvdd->ring_detect_state = RING_DETECT_STATE_COMPLETE;
    }
    InitializeListHead(&xvdd->srb_list);
  }
  FUNCTION_EXIT();

  return TRUE;
}

static ULONG
XenVbd_FillModePage(PXENVBD_DEVICE_DATA xvdd, PSCSI_REQUEST_BLOCK srb)
{
  PMODE_PARAMETER_HEADER parameter_header = NULL;
  PMODE_PARAMETER_HEADER10 parameter_header10 = NULL;
  PMODE_PARAMETER_BLOCK param_block;
  PMODE_FORMAT_PAGE format_page;
  ULONG offset = 0;
  UCHAR buffer[1024];
  BOOLEAN valid_page = FALSE;
  BOOLEAN cdb_llbaa;
  BOOLEAN cdb_dbd;
  UCHAR cdb_page_code;
  USHORT cdb_allocation_length;

  UNREFERENCED_PARAMETER(xvdd);

  RtlZeroMemory(srb->DataBuffer, srb->DataTransferLength);
  RtlZeroMemory(buffer, ARRAY_SIZE(buffer));
  offset = 0;

  //KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));
  
  switch (srb->Cdb[0])
  {
  case SCSIOP_MODE_SENSE:
    cdb_llbaa = FALSE;
    cdb_dbd = (BOOLEAN)!!(srb->Cdb[1] & 8);
    cdb_page_code = srb->Cdb[2] & 0x3f;
    cdb_allocation_length = srb->Cdb[4];
    KdPrint((__DRIVER_NAME "     SCSIOP_MODE_SENSE llbaa = %d, dbd = %d, page_code = %d, allocation_length = %d\n",
      cdb_llbaa, cdb_dbd, cdb_page_code, cdb_allocation_length));
    parameter_header = (PMODE_PARAMETER_HEADER)&buffer[offset];
    parameter_header->MediumType = 0;
    parameter_header->DeviceSpecificParameter = 0;
    if (xvdd->device_mode == XENVBD_DEVICEMODE_READ)
    {
      KdPrint((__DRIVER_NAME " Mode sense to a read only disk.\n"));
      parameter_header->DeviceSpecificParameter |= MODE_DSP_WRITE_PROTECT; 
    }
    offset += sizeof(MODE_PARAMETER_HEADER);
    break;
  case SCSIOP_MODE_SENSE10:
    cdb_llbaa = (BOOLEAN)!!(srb->Cdb[1] & 16);
    cdb_dbd = (BOOLEAN)!!(srb->Cdb[1] & 8);
    cdb_page_code = srb->Cdb[2] & 0x3f;
    cdb_allocation_length = (srb->Cdb[7] << 8) | srb->Cdb[8];
    KdPrint((__DRIVER_NAME "     SCSIOP_MODE_SENSE10 llbaa = %d, dbd = %d, page_code = %d, allocation_length = %d\n",
      cdb_llbaa, cdb_dbd, cdb_page_code, cdb_allocation_length));
    parameter_header10 = (PMODE_PARAMETER_HEADER10)&buffer[offset];
    parameter_header10->MediumType = 0;
    parameter_header10->DeviceSpecificParameter = 0;
    if (xvdd->device_mode == XENVBD_DEVICEMODE_READ)
    {
      KdPrint((__DRIVER_NAME " Mode sense to a read only disk.\n"));
      parameter_header10->DeviceSpecificParameter |= MODE_DSP_WRITE_PROTECT; 
    }
    offset += sizeof(MODE_PARAMETER_HEADER10);
    break;
  default:
    KdPrint((__DRIVER_NAME "     SCSIOP_MODE_SENSE_WTF (%02x)\n", (ULONG)srb->Cdb[0]));
    return FALSE;
  }  
  
  if (!cdb_dbd)
  {
    param_block = (PMODE_PARAMETER_BLOCK)&buffer[offset];
    if (xvdd->device_type == XENVBD_DEVICETYPE_DISK)
    {
      if (xvdd->total_sectors >> 32) 
      {
        param_block->DensityCode = 0xff;
        param_block->NumberOfBlocks[0] = 0xff;
        param_block->NumberOfBlocks[1] = 0xff;
        param_block->NumberOfBlocks[2] = 0xff;
      }
      else
      {
        param_block->DensityCode = (UCHAR)((xvdd->total_sectors >> 24) & 0xff);
        param_block->NumberOfBlocks[0] = (UCHAR)((xvdd->total_sectors >> 16) & 0xff);
        param_block->NumberOfBlocks[1] = (UCHAR)((xvdd->total_sectors >> 8) & 0xff);
        param_block->NumberOfBlocks[2] = (UCHAR)((xvdd->total_sectors >> 0) & 0xff);
      }
      param_block->BlockLength[0] = (UCHAR)((xvdd->bytes_per_sector >> 16) & 0xff);
      param_block->BlockLength[1] = (UCHAR)((xvdd->bytes_per_sector >> 8) & 0xff);
      param_block->BlockLength[2] = (UCHAR)((xvdd->bytes_per_sector >> 0) & 0xff);
    }
    offset += sizeof(MODE_PARAMETER_BLOCK);
  }
  switch (srb->Cdb[0])
  {
  case SCSIOP_MODE_SENSE:
    parameter_header->BlockDescriptorLength = (UCHAR)(offset - sizeof(MODE_PARAMETER_HEADER));
    break;
  case SCSIOP_MODE_SENSE10:
    parameter_header10->BlockDescriptorLength[0] = (UCHAR)((offset - sizeof(MODE_PARAMETER_HEADER10)) >> 8);
    parameter_header10->BlockDescriptorLength[1] = (UCHAR)(offset - sizeof(MODE_PARAMETER_HEADER10));
    break;
  }
  if (xvdd->device_type == XENVBD_DEVICETYPE_DISK && (cdb_page_code == MODE_PAGE_FORMAT_DEVICE || cdb_page_code == MODE_SENSE_RETURN_ALL))
  {
    valid_page = TRUE;
    format_page = (PMODE_FORMAT_PAGE)&buffer[offset];
    format_page->PageCode = MODE_PAGE_FORMAT_DEVICE;
    format_page->PageLength = sizeof(MODE_FORMAT_PAGE) - FIELD_OFFSET(MODE_FORMAT_PAGE, PageLength);
    /* 256 sectors per track */
    format_page->SectorsPerTrack[0] = 0x01;
    format_page->SectorsPerTrack[1] = 0x00;
    /* xxx bytes per sector */
    format_page->BytesPerPhysicalSector[0] = (UCHAR)(xvdd->bytes_per_sector >> 8);
    format_page->BytesPerPhysicalSector[1] = (UCHAR)(xvdd->bytes_per_sector & 0xff);
    format_page->HardSectorFormating = TRUE;
    format_page->SoftSectorFormating = TRUE;
    offset += sizeof(MODE_FORMAT_PAGE);
  }
  if (xvdd->device_type == XENVBD_DEVICETYPE_DISK && (cdb_page_code == MODE_PAGE_CACHING || cdb_page_code == MODE_SENSE_RETURN_ALL))
  {
    PMODE_CACHING_PAGE caching_page;
    valid_page = TRUE;
    caching_page = (PMODE_CACHING_PAGE)&buffer[offset];
    caching_page->PageCode = MODE_PAGE_CACHING;
    caching_page->PageLength = sizeof(MODE_CACHING_PAGE) - FIELD_OFFSET(MODE_CACHING_PAGE, PageLength);
    // caching_page-> // all zeros is just fine... maybe
    offset += sizeof(MODE_CACHING_PAGE);
  }
  if (xvdd->device_type == XENVBD_DEVICETYPE_DISK && (cdb_page_code == MODE_PAGE_MEDIUM_TYPES || cdb_page_code == MODE_SENSE_RETURN_ALL))
  {
    PUCHAR medium_types_page;
    valid_page = TRUE;
    medium_types_page = &buffer[offset];
    medium_types_page[0] = MODE_PAGE_MEDIUM_TYPES;
    medium_types_page[1] = 0x06;
    medium_types_page[2] = 0;
    medium_types_page[3] = 0;
    medium_types_page[4] = 0;
    medium_types_page[5] = 0;
    medium_types_page[6] = 0;
    medium_types_page[7] = 0;
    offset += 8;
  }
  switch (srb->Cdb[0])
  {
  case SCSIOP_MODE_SENSE:
    parameter_header->ModeDataLength = (UCHAR)(offset - 1);
    break;
  case SCSIOP_MODE_SENSE10:
    parameter_header10->ModeDataLength[0] = (UCHAR)((offset - 2) >> 8);
    parameter_header10->ModeDataLength[1] = (UCHAR)(offset - 2);
    break;
  }

  if (!valid_page && cdb_page_code != MODE_SENSE_RETURN_ALL)
  {
    srb->SrbStatus = SRB_STATUS_ERROR;
  }
  else if(offset < srb->DataTransferLength)
    srb->SrbStatus = SRB_STATUS_DATA_OVERRUN;
  else
    srb->SrbStatus = SRB_STATUS_SUCCESS;
  srb->DataTransferLength = min(srb->DataTransferLength, offset);
  srb->ScsiStatus = 0;
  memcpy(srb->DataBuffer, buffer, srb->DataTransferLength);
  
  //FUNCTION_EXIT();

  return TRUE;
}

static ULONG
XenVbd_MakeSense(PXENVBD_DEVICE_DATA xvdd, PSCSI_REQUEST_BLOCK srb, UCHAR sense_key, UCHAR additional_sense_code)
{
  PSENSE_DATA sd = srb->SenseInfoBuffer;
 
  UNREFERENCED_PARAMETER(xvdd);
  
  if (!srb->SenseInfoBuffer)
    return 0;
  
  sd->ErrorCode = 0x70;
  sd->Valid = 1;
  sd->SenseKey = sense_key;
  sd->AdditionalSenseLength = sizeof(SENSE_DATA) - FIELD_OFFSET(SENSE_DATA, AdditionalSenseLength);
  sd->AdditionalSenseCode = additional_sense_code;
  return sizeof(SENSE_DATA);
}

static VOID
XenVbd_MakeAutoSense(PXENVBD_DEVICE_DATA xvdd, PSCSI_REQUEST_BLOCK srb)
{
  if (srb->SrbStatus == SRB_STATUS_SUCCESS || srb->SrbFlags & SRB_FLAGS_DISABLE_AUTOSENSE)
    return;
  XenVbd_MakeSense(xvdd, srb, xvdd->last_sense_key, xvdd->last_additional_sense_code);
  srb->SrbStatus |= SRB_STATUS_AUTOSENSE_VALID;
}

static BOOLEAN
XenVbd_HandleEventSynchronised(PVOID DeviceExtension, PVOID context)
{
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)DeviceExtension;
  PSCSI_REQUEST_BLOCK srb;
  RING_IDX i, rp;
  ULONG j;
  blkif_response_t *rep;
  //int block_count;
  int more_to_do = TRUE;
  blkif_shadow_t *shadow;
  ULONG suspend_resume_state_pdo;
  srb_list_entry_t *srb_entry;

  UNREFERENCED_PARAMETER(context);
  
  //if (dump_mode) FUNCTION_ENTER();

  suspend_resume_state_pdo = xvdd->device_state->suspend_resume_state_pdo;
  KeMemoryBarrier();

  if (suspend_resume_state_pdo != xvdd->device_state->suspend_resume_state_fdo)
  {
    //FUNCTION_ENTER();
    switch (suspend_resume_state_pdo)
    {
      case SR_STATE_SUSPENDING:
        KdPrint((__DRIVER_NAME "     New pdo state SR_STATE_SUSPENDING\n"));
        break;
      case SR_STATE_RESUMING:
        KdPrint((__DRIVER_NAME "     New pdo state SR_STATE_RESUMING\n"));
        XenVbd_InitFromConfig(xvdd);
        xvdd->device_state->suspend_resume_state_fdo = suspend_resume_state_pdo;
        xvdd->vectors.EvtChn_Notify(xvdd->vectors.context, xvdd->device_state->pdo_event_channel);
        break;
      case SR_STATE_RUNNING:
        KdPrint((__DRIVER_NAME "     New pdo state %d\n", suspend_resume_state_pdo));
        xvdd->device_state->suspend_resume_state_fdo = suspend_resume_state_pdo;
        xvdd->ring_detect_state = RING_DETECT_STATE_NOT_STARTED; /* could be running on different hardware */
        xvdd->vectors.EvtChn_Notify(xvdd->vectors.context, xvdd->device_state->pdo_event_channel);
      default:
        KdPrint((__DRIVER_NAME "     New pdo state %d\n", suspend_resume_state_pdo));
        xvdd->device_state->suspend_resume_state_fdo = suspend_resume_state_pdo;
        xvdd->vectors.EvtChn_Notify(xvdd->vectors.context, xvdd->device_state->pdo_event_channel);
        break;
    }
    KeMemoryBarrier();
  }

  if (xvdd->device_state->suspend_resume_state_fdo != SR_STATE_RUNNING)
  {
    return TRUE;
  }

  while (more_to_do)
  {
    rp = xvdd->ring.sring->rsp_prod;
    KeMemoryBarrier();
    for (i = xvdd->ring.rsp_cons; i < rp; i++)
    {
      rep = XenVbd_GetResponse(xvdd, i);
/*
* This code is to automatically detect if the backend is using the same
* bit width or a different bit width to us. Later versions of Xen do this
* via a xenstore value, but not all. That 0x0fffffff (notice
* that the msb is not actually set, so we don't have any problems with
* sign extending) is to signify the last entry on the right, which is
* different under 32 and 64 bits, and that is why we set it up there.

* To do the detection, we put two initial entries on the ring, with an op
* of 0xff (which is invalid). The first entry is mostly okay, but the
* second will be grossly misaligned if the backend bit width is different,
* and we detect this and switch frontend structures.
*/
      switch (xvdd->ring_detect_state)
      {
      case RING_DETECT_STATE_NOT_STARTED:
        KdPrint((__DRIVER_NAME "     premature IRQ\n"));
        break;
      case RING_DETECT_STATE_DETECT1:
        KdPrint((__DRIVER_NAME "     ring_detect_state = %d, index = %d, operation = %x, id = %lx, status = %d\n", xvdd->ring_detect_state, i, rep->operation, rep->id, rep->status));
        KdPrint((__DRIVER_NAME "     req_prod = %d, rsp_prod = %d, rsp_cons = %d\n", xvdd->sring->req_prod, xvdd->sring->rsp_prod, xvdd->ring.rsp_cons));
        xvdd->ring_detect_state = RING_DETECT_STATE_DETECT2;
        break;
      case RING_DETECT_STATE_DETECT2:
        KdPrint((__DRIVER_NAME "     ring_detect_state = %d, index = %d, operation = %x, id = %lx, status = %d\n", xvdd->ring_detect_state, i, rep->operation, rep->id, rep->status));
        KdPrint((__DRIVER_NAME "     req_prod = %d, rsp_prod = %d, rsp_cons = %d\n", xvdd->sring->req_prod, xvdd->sring->rsp_prod, xvdd->ring.rsp_cons));
        *xvdd->event_channel_ptr |= 0x80000000;
        if (rep->operation != 0xff)
        {
          KdPrint((__DRIVER_NAME "     switching to 'other' ring size\n"));
          xvdd->ring.nr_ents = BLK_OTHER_RING_SIZE;
          xvdd->use_other = TRUE;
          *xvdd->event_channel_ptr |= 0x40000000;
        }
        xvdd->ring_detect_state = RING_DETECT_STATE_COMPLETE;
        break;
      case RING_DETECT_STATE_COMPLETE:
        shadow = &xvdd->shadows[rep->id & SHADOW_ID_ID_MASK];
        if (shadow->reset)
        {
          KdPrint((__DRIVER_NAME "     discarding reset shadow\n"));
          for (j = 0; j < shadow->req.nr_segments; j++)
          {
            xvdd->vectors.GntTbl_EndAccess(xvdd->vectors.context,
              shadow->req.seg[j].gref, FALSE, xvdd->grant_tag);
          }
        }
        else if (dump_mode && !(rep->id & SHADOW_ID_DUMP_FLAG))
        {
          KdPrint((__DRIVER_NAME "     discarding stale (non-dump-mode) shadow\n"));
        }
        else
        {
          srb = shadow->srb;
          ASSERT(srb);
          srb_entry = srb->SrbExtension;
          ASSERT(srb_entry);
          /* a few errors occur in dump mode because Xen refuses to allow us to map pages we are using for other stuff. Just ignore them */
          if (rep->status == BLKIF_RSP_OKAY || (dump_mode &&  dump_mode_errors++ < DUMP_MODE_ERROR_LIMIT))
            srb->SrbStatus = SRB_STATUS_SUCCESS;
          else
          {
            KdPrint((__DRIVER_NAME "     Xen Operation returned error\n"));
            if (decode_cdb_is_read(srb))
              KdPrint((__DRIVER_NAME "     Operation = Read\n"));
            else
              KdPrint((__DRIVER_NAME "     Operation = Write\n"));
            srb_entry->error = TRUE;
          }
          if (shadow->aligned_buffer_in_use)
          {
            ASSERT(xvdd->aligned_buffer_in_use);
            xvdd->aligned_buffer_in_use = FALSE;
            if (srb->SrbStatus == SRB_STATUS_SUCCESS && decode_cdb_is_read(srb))
              memcpy((PUCHAR)shadow->system_address, xvdd->aligned_buffer, shadow->length);
          }
          for (j = 0; j < shadow->req.nr_segments; j++)
          {
            xvdd->vectors.GntTbl_EndAccess(xvdd->vectors.context,
              shadow->req.seg[j].gref, FALSE, xvdd->grant_tag);
          }
          srb_entry->outstanding_requests--;
          if (!srb_entry->outstanding_requests && srb_entry->offset == srb_entry->length)
          {
            if (srb_entry->error)
            {
              srb->SrbStatus = SRB_STATUS_ERROR;
              srb->ScsiStatus = 0x02;
              xvdd->last_sense_key = SCSI_SENSE_MEDIUM_ERROR;
              xvdd->last_additional_sense_code = SCSI_ADSENSE_NO_SENSE;
              XenVbd_MakeAutoSense(xvdd, srb);
            }        
            StorPortNotification(RequestComplete, xvdd, srb);
          }
        }
        shadow->aligned_buffer_in_use = FALSE;
        shadow->srb = NULL;
        shadow->reset = FALSE;
        put_shadow_on_freelist(xvdd, shadow);
        break;
      }
    }

    xvdd->ring.rsp_cons = i;
    if (i != xvdd->ring.req_prod_pvt)
    {
      RING_FINAL_CHECK_FOR_RESPONSES(&xvdd->ring, more_to_do);
    }
    else
    {
      xvdd->ring.sring->rsp_event = i + 1;
      more_to_do = FALSE;
    }
  }

  //if (start_ring_detect_state == RING_DETECT_STATE_COMPLETE)
  XenVbd_PutQueuedSrbsOnRing(xvdd);

  if (suspend_resume_state_pdo == SR_STATE_SUSPENDING)
  {
    if (xvdd->inactive || xvdd->shadow_free == SHADOW_ENTRIES)
    {
      /* all entries are purged from the list (or we are inactive). ready to suspend */
      xvdd->device_state->suspend_resume_state_fdo = suspend_resume_state_pdo;
      KeMemoryBarrier();
      KdPrint((__DRIVER_NAME "     Set fdo state SR_STATE_SUSPENDING\n"));
      KdPrint((__DRIVER_NAME "     Notifying event channel %d\n", xvdd->device_state->pdo_event_channel));
      xvdd->vectors.EvtChn_Notify(xvdd->vectors.context, xvdd->device_state->pdo_event_channel);
    }
  }
  //if (dump_mode) FUNCTION_EXIT();

  return TRUE;
}

static BOOLEAN
XenVbd_HandleEvent(PVOID DeviceExtension)
{
  BOOLEAN retval;
  STOR_LOCK_HANDLE lock_handle;
  
  //if (dump_mode) FUNCTION_ENTER();
  StorPortAcquireSpinLock(DeviceExtension, StartIoLock, NULL, &lock_handle);
  retval = StorPortSynchronizeAccess(DeviceExtension, XenVbd_HandleEventSynchronised, NULL);
  StorPortReleaseSpinLock (DeviceExtension, &lock_handle);
  //if (dump_mode) FUNCTION_EXIT();
  return retval;
}

/* this is only used during hiber and dump */
static BOOLEAN
XenVbd_HwStorInterrupt(PVOID DeviceExtension)
{
  BOOLEAN retval;
  
  //FUNCTION_ENTER();
  retval = XenVbd_HandleEventSynchronised(DeviceExtension, NULL);
  //FUNCTION_EXIT();
  return retval;
}

static BOOLEAN
XenVbd_HwStorResetBus(PVOID DeviceExtension, ULONG PathId)
{
  PXENVBD_DEVICE_DATA xvdd = DeviceExtension;
  //srb_list_entry_t *srb_entry;
  int i;
  /* need to make sure that each SRB is only reset once */
  LIST_ENTRY srb_reset_list;
  PLIST_ENTRY list_entry;
  //STOR_LOCK_HANDLE lock_handle;

  UNREFERENCED_PARAMETER(PathId);

  FUNCTION_ENTER();

  /* It appears that the StartIo spinlock is already held at this point */

  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));

  if (xvdd->ring_detect_state == RING_DETECT_STATE_COMPLETE && xvdd->device_state->suspend_resume_state_pdo == SR_STATE_RUNNING)
  {
    xvdd->aligned_buffer_in_use = FALSE;
    
    InitializeListHead(&srb_reset_list);
    
    while((list_entry = RemoveHeadList(&xvdd->srb_list)) != &xvdd->srb_list)
    {
      #if DBG
      srb_list_entry_t *srb_entry = CONTAINING_RECORD(list_entry, srb_list_entry_t, list_entry);
      KdPrint((__DRIVER_NAME "     adding queued SRB %p to reset list\n", srb_entry->srb));
      #endif
      InsertTailList(&srb_reset_list, list_entry);
    }
    
    for (i = 0; i < MAX_SHADOW_ENTRIES; i++)
    {
      if (xvdd->shadows[i].srb)
      {
        srb_list_entry_t *srb_entry = xvdd->shadows[i].srb->SrbExtension;
        for (list_entry = srb_reset_list.Flink; list_entry != &srb_reset_list; list_entry = list_entry->Flink)
        {
          if (list_entry == &srb_entry->list_entry)
            break;
        }
        if (list_entry == &srb_reset_list)
        {
          KdPrint((__DRIVER_NAME "     adding in-flight SRB %p to reset list\n", srb_entry->srb));
          InsertTailList(&srb_reset_list, &srb_entry->list_entry);
        }
        /* set reset here so that the interrupt won't do anything with the srb but will dispose of the shadow entry correctly */
        xvdd->shadows[i].reset = TRUE;
        xvdd->shadows[i].srb = NULL;
        xvdd->shadows[i].aligned_buffer_in_use = FALSE;
      }
    }

    while((list_entry = RemoveHeadList(&srb_reset_list)) != &srb_reset_list)
    {
      srb_list_entry_t *srb_entry = CONTAINING_RECORD(list_entry, srb_list_entry_t, list_entry);
      srb_entry->srb->SrbStatus = SRB_STATUS_BUS_RESET;
      KdPrint((__DRIVER_NAME "     completing SRB %p with status SRB_STATUS_BUS_RESET\n", srb_entry->srb));
      StorPortNotification(RequestComplete, xvdd, srb_entry->srb);
    }

    /* send a notify to Dom0 just in case it was missed for some reason (which should _never_ happen) */
    xvdd->vectors.EvtChn_Notify(xvdd->vectors.context, xvdd->event_channel);
  
    StorPortNotification(NextRequest, DeviceExtension);
  }

  //StorPortReleaseSpinLock(DeviceExtension, &lock_handle);

  FUNCTION_EXIT();

  return TRUE;
}

static BOOLEAN
XenVbd_HwStorStartIo(PVOID DeviceExtension, PSCSI_REQUEST_BLOCK srb)
{
  PUCHAR data_buffer;
  PSCSI_PNP_REQUEST_BLOCK sprb;
  PSCSI_POWER_REQUEST_BLOCK spwrb;
  PMINIPORT_DUMP_POINTERS dump_pointers;
  PCDB cdb;
  PXENVBD_DEVICE_DATA xvdd = DeviceExtension;
  ULONG data_transfer_length;
  UCHAR srb_status = SRB_STATUS_PENDING;
  STOR_LOCK_HANDLE lock_handle;

  //if (dump_mode) FUNCTION_ENTER();
  //if (dump_mode) KdPrint((__DRIVER_NAME "     srb = %p\n", srb));

  StorPortAcquireSpinLock(DeviceExtension, StartIoLock, NULL, &lock_handle);

  data_transfer_length = srb->DataTransferLength;
  
  if (xvdd->inactive)
  {
    KdPrint((__DRIVER_NAME "     Inactive srb->Function = %08X\n", srb->Function));
    srb->SrbStatus = SRB_STATUS_NO_DEVICE;
    StorPortNotification(RequestComplete, DeviceExtension, srb);
    StorPortReleaseSpinLock (DeviceExtension, &lock_handle);
    return TRUE;
  }

  if (xvdd->ring_detect_state == RING_DETECT_STATE_NOT_STARTED)
  {
    XenVbd_StartRingDetection(DeviceExtension);
  }

  // If we haven't enumerated all the devices yet then just defer the request
  if (xvdd->ring_detect_state < RING_DETECT_STATE_COMPLETE)
  {
    srb->SrbStatus = SRB_STATUS_BUSY;
    StorPortNotification(RequestComplete, DeviceExtension, srb);
    KdPrint((__DRIVER_NAME " --- HwStorStartIo (Still figuring out ring)\n"));
    StorPortReleaseSpinLock (DeviceExtension, &lock_handle);
    return TRUE;
  }

  if (!dump_mode && xvdd->device_state->suspend_resume_state_pdo != SR_STATE_RUNNING)
  {
    //KdPrint((__DRIVER_NAME " --> HwStorStartIo (Suspending/Resuming)\n"));
    srb->SrbStatus = SRB_STATUS_BUSY;
    StorPortNotification(RequestComplete, DeviceExtension, srb);
    //KdPrint((__DRIVER_NAME " <-- HwStorStartIo (Suspending/Resuming)\n"));
    StorPortReleaseSpinLock (DeviceExtension, &lock_handle);
    return TRUE;
  }

  if (srb->PathId != 0 || srb->TargetId != 0 || srb->Lun != 0)
  {
    srb->SrbStatus = SRB_STATUS_NO_DEVICE;
    StorPortNotification(RequestComplete, DeviceExtension, srb);
    KdPrint((__DRIVER_NAME " --- HwStorStartIo (Out of bounds - PathId = %d, TargetId = %d, Lun = %d)\n", srb->PathId, srb->TargetId, srb->Lun));
    StorPortReleaseSpinLock (DeviceExtension, &lock_handle);
    return TRUE;
  }

  switch (srb->Function)
  {
  case SRB_FUNCTION_EXECUTE_SCSI:
    cdb = (PCDB)srb->Cdb;

    switch(cdb->CDB6GENERIC.OperationCode)
    {
    case SCSIOP_TEST_UNIT_READY:
      if (dump_mode)
        KdPrint((__DRIVER_NAME "     Command = TEST_UNIT_READY\n"));
      srb_status = SRB_STATUS_SUCCESS;
      srb->ScsiStatus = 0;
      break;
    case SCSIOP_INQUIRY:
      if (dump_mode)
        KdPrint((__DRIVER_NAME "     Command = INQUIRY\n"));
//      KdPrint((__DRIVER_NAME "     (LUN = %d, EVPD = %d, Page Code = %02X)\n", srb->Cdb[1] >> 5, srb->Cdb[1] & 1, srb->Cdb[2]));
//      KdPrint((__DRIVER_NAME "     (Length = %d)\n", srb->DataTransferLength));
      
      //data_buffer = LongLongToPtr(ScsiPortGetPhysicalAddress(xvdd, srb, srb->DataBuffer, &data_buffer_length).QuadPart);
      data_buffer = srb->DataBuffer;
      RtlZeroMemory(data_buffer, srb->DataTransferLength);
      srb_status = SRB_STATUS_SUCCESS;
      switch (xvdd->device_type)
      {
      case XENVBD_DEVICETYPE_DISK:
        if ((srb->Cdb[1] & 1) == 0)
        {
          if (srb->Cdb[2])
          {
            srb_status = SRB_STATUS_ERROR;
          }
          else
          {
            PINQUIRYDATA id = (PINQUIRYDATA)data_buffer;
            id->DeviceType = DIRECT_ACCESS_DEVICE;
            id->Versions = 4; /* minimum that WHQL says we must support */
            id->ResponseDataFormat = 2; /* not sure about this but WHQL complains otherwise */
            id->HiSupport = 1; /* WHQL test says we should set this */
            //id->AdditionalLength = FIELD_OFFSET(INQUIRYDATA, VendorSpecific) - FIELD_OFFSET(INQUIRYDATA, AdditionalLength);
            id->AdditionalLength = sizeof(INQUIRYDATA) - FIELD_OFFSET(INQUIRYDATA, AdditionalLength) - 1;
            id->CommandQueue = 1;
            memcpy(id->VendorId, scsi_device_manufacturer, 8); // vendor id
            memcpy(id->ProductId, scsi_disk_model, 16); // product id
            memcpy(id->ProductRevisionLevel, "0000", 4); // product revision level
            data_transfer_length = FIELD_OFFSET(INQUIRYDATA, VendorSpecific);
          }
        }
        else
        {
          switch (srb->Cdb[2])
          {
          case VPD_SUPPORTED_PAGES: /* list of pages we support */
            data_buffer[0] = DIRECT_ACCESS_DEVICE;
            data_buffer[1] = VPD_SUPPORTED_PAGES;
            data_buffer[2] = 0x00;
            data_buffer[3] = 2;
            data_buffer[4] = 0x00;
            data_buffer[5] = 0x80;
            data_transfer_length = 6;
            break;
          case VPD_SERIAL_NUMBER: /* serial number */
            data_buffer[0] = DIRECT_ACCESS_DEVICE;
            data_buffer[1] = VPD_SERIAL_NUMBER;
            data_buffer[2] = 0x00;
            data_buffer[3] = 8;
            memset(&data_buffer[4], ' ', 8);
            data_transfer_length = 12;
            break;
          case VPD_DEVICE_IDENTIFIERS: /* identification - we don't support any so just return zero */
            data_buffer[0] = DIRECT_ACCESS_DEVICE;
            data_buffer[1] = VPD_DEVICE_IDENTIFIERS;
            data_buffer[2] = 0x00;
            data_buffer[3] = 4 + (UCHAR)strlen(xvdd->vectors.path); /* length */
            data_buffer[4] = 2; /* ASCII */
            data_buffer[5] = 1; /* VendorId */
            data_buffer[6] = 0;
            data_buffer[7] = (UCHAR)strlen(xvdd->vectors.path);
            memcpy(&data_buffer[8], xvdd->vectors.path, strlen(xvdd->vectors.path));
            data_transfer_length = (ULONG)(8 + strlen(xvdd->vectors.path));
            break;
          default:
            //KdPrint((__DRIVER_NAME "     Unknown Page %02x requested\n", srb->Cdb[2]));
            srb_status = SRB_STATUS_ERROR;
            break;
          }
        }
        break;
      case XENVBD_DEVICETYPE_CDROM:
        if ((srb->Cdb[1] & 1) == 0)
        {
          PINQUIRYDATA id = (PINQUIRYDATA)data_buffer;
          id->DeviceType = READ_ONLY_DIRECT_ACCESS_DEVICE;
          id->RemovableMedia = 1;
          id->Versions = 3;
          id->ResponseDataFormat = 0;
          id->AdditionalLength = FIELD_OFFSET(INQUIRYDATA, VendorSpecific) - FIELD_OFFSET(INQUIRYDATA, AdditionalLength);
          id->CommandQueue = 1;
          memcpy(id->VendorId, scsi_device_manufacturer, 8); // vendor id
          memcpy(id->ProductId, scsi_cdrom_model, 16); // product id
          memcpy(id->ProductRevisionLevel, "0000", 4); // product revision level
          data_transfer_length = sizeof(INQUIRYDATA);
        }
        else
        {
          switch (srb->Cdb[2])
          {
          case 0x00:
            data_buffer[0] = READ_ONLY_DIRECT_ACCESS_DEVICE;
            data_buffer[1] = 0x00;
            data_buffer[2] = 0x00;
            data_buffer[3] = 2;
            data_buffer[4] = 0x00;
            data_buffer[5] = 0x80;
            data_transfer_length = 6;
            break;
          case 0x80:
            data_buffer[0] = READ_ONLY_DIRECT_ACCESS_DEVICE;
            data_buffer[1] = 0x80;
            data_buffer[2] = 0x00;
            data_buffer[3] = 8;
            data_buffer[4] = 0x31;
            data_buffer[5] = 0x32;
            data_buffer[6] = 0x33;
            data_buffer[7] = 0x34;
            data_buffer[8] = 0x35;
            data_buffer[9] = 0x36;
            data_buffer[10] = 0x37;
            data_buffer[11] = 0x38;
            data_transfer_length = 12;
            break;
          default:
            //KdPrint((__DRIVER_NAME "     Unknown Page %02x requested\n", srb->Cdb[2]));
            srb_status = SRB_STATUS_ERROR;
            break;
          }
        }
        break;
      default:
        //KdPrint((__DRIVER_NAME "     Unknown DeviceType %02x requested\n", xvdd->device_type));
        srb_status = SRB_STATUS_ERROR;
        break;
      }
      break;
    case SCSIOP_READ_CAPACITY:
      if (dump_mode)
        KdPrint((__DRIVER_NAME "     Command = READ_CAPACITY\n"));
      //KdPrint((__DRIVER_NAME "       LUN = %d, RelAdr = %d\n", srb->Cdb[1] >> 4, srb->Cdb[1] & 1));
      //KdPrint((__DRIVER_NAME "       LBA = %02x%02x%02x%02x\n", srb->Cdb[2], srb->Cdb[3], srb->Cdb[4], srb->Cdb[5]));
      //KdPrint((__DRIVER_NAME "       PMI = %d\n", srb->Cdb[8] & 1));
      //data_buffer = LongLongToPtr(ScsiPortGetPhysicalAddress(xvdd, srb, srb->DataBuffer, &data_buffer_length).QuadPart);
      data_buffer = srb->DataBuffer;
      RtlZeroMemory(data_buffer, srb->DataTransferLength);
      if ((xvdd->total_sectors - 1) >> 32)
      {
        data_buffer[0] = 0xff;
        data_buffer[1] = 0xff;
        data_buffer[2] = 0xff;
        data_buffer[3] = 0xff;
      }
      else
      {
        data_buffer[0] = (unsigned char)((xvdd->total_sectors - 1) >> 24) & 0xff;
        data_buffer[1] = (unsigned char)((xvdd->total_sectors - 1) >> 16) & 0xff;
        data_buffer[2] = (unsigned char)((xvdd->total_sectors - 1) >> 8) & 0xff;
        data_buffer[3] = (unsigned char)((xvdd->total_sectors - 1) >> 0) & 0xff;
      }
      data_buffer[4] = (unsigned char)(xvdd->bytes_per_sector >> 24) & 0xff;
      data_buffer[5] = (unsigned char)(xvdd->bytes_per_sector >> 16) & 0xff;
      data_buffer[6] = (unsigned char)(xvdd->bytes_per_sector >> 8) & 0xff;
      data_buffer[7] = (unsigned char)(xvdd->bytes_per_sector >> 0) & 0xff;
      data_transfer_length = 8;
      srb->ScsiStatus = 0;
      srb_status = SRB_STATUS_SUCCESS;
      break;
    case SCSIOP_READ_CAPACITY16:
      if (dump_mode)
        KdPrint((__DRIVER_NAME "     Command = READ_CAPACITY\n"));
      //KdPrint((__DRIVER_NAME "       LUN = %d, RelAdr = %d\n", srb->Cdb[1] >> 4, srb->Cdb[1] & 1));
      //KdPrint((__DRIVER_NAME "       LBA = %02x%02x%02x%02x\n", srb->Cdb[2], srb->Cdb[3], srb->Cdb[4], srb->Cdb[5]));
      //KdPrint((__DRIVER_NAME "       PMI = %d\n", srb->Cdb[8] & 1));
      //data_buffer = LongLongToPtr(ScsiPortGetPhysicalAddress(xvdd, srb, srb->DataBuffer, &data_buffer_length).QuadPart);
      data_buffer = srb->DataBuffer;
      RtlZeroMemory(data_buffer, srb->DataTransferLength);
      data_buffer[0] = (unsigned char)((xvdd->total_sectors - 1) >> 56) & 0xff;
      data_buffer[1] = (unsigned char)((xvdd->total_sectors - 1) >> 48) & 0xff;
      data_buffer[2] = (unsigned char)((xvdd->total_sectors - 1) >> 40) & 0xff;
      data_buffer[3] = (unsigned char)((xvdd->total_sectors - 1) >> 32) & 0xff;
      data_buffer[4] = (unsigned char)((xvdd->total_sectors - 1) >> 24) & 0xff;
      data_buffer[5] = (unsigned char)((xvdd->total_sectors - 1) >> 16) & 0xff;
      data_buffer[6] = (unsigned char)((xvdd->total_sectors - 1) >> 8) & 0xff;
      data_buffer[7] = (unsigned char)((xvdd->total_sectors - 1) >> 0) & 0xff;
      data_buffer[8] = (unsigned char)(xvdd->bytes_per_sector >> 24) & 0xff;
      data_buffer[9] = (unsigned char)(xvdd->bytes_per_sector >> 16) & 0xff;
      data_buffer[10] = (unsigned char)(xvdd->bytes_per_sector >> 8) & 0xff;
      data_buffer[11] = (unsigned char)(xvdd->bytes_per_sector >> 0) & 0xff;
      data_transfer_length = 12;
      srb->ScsiStatus = 0;
      srb_status = SRB_STATUS_SUCCESS;
      break;
    case SCSIOP_MODE_SENSE:
    case SCSIOP_MODE_SENSE10:
      if (dump_mode)
        KdPrint((__DRIVER_NAME "     Command = MODE_SENSE (DBD = %d, PC = %d, Page Code = %02x)\n", srb->Cdb[1] & 0x08, srb->Cdb[2] & 0xC0, srb->Cdb[2] & 0x3F));
      data_transfer_length = XenVbd_FillModePage(xvdd, srb);
      srb_status = SRB_STATUS_SUCCESS;
      break;
    case SCSIOP_READ:
    case SCSIOP_READ16:
    case SCSIOP_WRITE:
    case SCSIOP_WRITE16:
      //KdPrint((__DRIVER_NAME "     srb = %p\n", srb));  
      XenVbd_PutSrbOnList(xvdd, srb);
      XenVbd_PutQueuedSrbsOnRing(xvdd);
      break;
    case SCSIOP_VERIFY:
    case SCSIOP_VERIFY16:
      // Should we do more here?
      if (dump_mode)
        KdPrint((__DRIVER_NAME "     Command = VERIFY\n"));
      srb_status = SRB_STATUS_SUCCESS;
      break;
#if 0
    case SCSIOP_REPORT_LUNS:
      if (dump_mode)
        KdPrint((__DRIVER_NAME "     Command = REPORT_LUNS\n"));
      switch (srb->Cdb[1])
      {
      }
      srb_status = SRB_STATUS_SUCCESS;;
      break;
#endif
    case SCSIOP_REQUEST_SENSE:
      if (dump_mode)
        KdPrint((__DRIVER_NAME "     Command = REQUEST_SENSE\n"));
      data_transfer_length = XenVbd_MakeSense(xvdd, srb, xvdd->last_sense_key, xvdd->last_additional_sense_code);
      srb_status = SRB_STATUS_SUCCESS;
      break;      
    case SCSIOP_READ_TOC:
      if (dump_mode)
        KdPrint((__DRIVER_NAME "     Command = READ_TOC\n"));
      data_buffer = srb->DataBuffer;
/*
#define READ_TOC_FORMAT_TOC         0x00
#define READ_TOC_FORMAT_SESSION     0x01
#define READ_TOC_FORMAT_FULL_TOC    0x02
#define READ_TOC_FORMAT_PMA         0x03
#define READ_TOC_FORMAT_ATIP        0x04
*/
//      KdPrint((__DRIVER_NAME "     Msf = %d\n", cdb->READ_TOC.Msf));
//      KdPrint((__DRIVER_NAME "     LogicalUnitNumber = %d\n", cdb->READ_TOC.LogicalUnitNumber));
//      KdPrint((__DRIVER_NAME "     Format2 = %d\n", cdb->READ_TOC.Format2));
//      KdPrint((__DRIVER_NAME "     StartingTrack = %d\n", cdb->READ_TOC.StartingTrack));
//      KdPrint((__DRIVER_NAME "     AllocationLength = %d\n", (cdb->READ_TOC.AllocationLength[0] << 8) | cdb->READ_TOC.AllocationLength[1]));
//      KdPrint((__DRIVER_NAME "     Control = %d\n", cdb->READ_TOC.Control));
//      KdPrint((__DRIVER_NAME "     Format = %d\n", cdb->READ_TOC.Format));
      switch (cdb->READ_TOC.Format2)
      {
      case READ_TOC_FORMAT_TOC:
        data_buffer[0] = 0; // length MSB
        data_buffer[1] = 10; // length LSB
        data_buffer[2] = 1; // First Track
        data_buffer[3] = 1; // Last Track
        data_buffer[4] = 0; // Reserved
        data_buffer[5] = 0x14; // current position data + uninterrupted data
        data_buffer[6] = 1; // last complete track
        data_buffer[7] = 0; // reserved
        data_buffer[8] = 0; // MSB Block
        data_buffer[9] = 0;
        data_buffer[10] = 0;
        data_buffer[11] = 0; // LSB Block
        data_transfer_length = 12;
        srb_status = SRB_STATUS_SUCCESS;
        break;
      case READ_TOC_FORMAT_SESSION:
      case READ_TOC_FORMAT_FULL_TOC:
      case READ_TOC_FORMAT_PMA:
      case READ_TOC_FORMAT_ATIP:
        srb_status = SRB_STATUS_ERROR;
        break;
      default:
        srb_status = SRB_STATUS_ERROR;
        break;
      }
      break;
    case SCSIOP_START_STOP_UNIT:
      KdPrint((__DRIVER_NAME "     Command = SCSIOP_START_STOP_UNIT\n"));
      srb_status = SRB_STATUS_SUCCESS;
      break;
    case SCSIOP_RESERVE_UNIT:
      KdPrint((__DRIVER_NAME "     Command = SCSIOP_RESERVE_UNIT\n"));
      srb_status = SRB_STATUS_SUCCESS;
      break;
    case SCSIOP_RELEASE_UNIT:
      KdPrint((__DRIVER_NAME "     Command = SCSIOP_RELEASE_UNIT\n"));
      srb_status = SRB_STATUS_SUCCESS;
      break;
    default:
      KdPrint((__DRIVER_NAME "     Unhandled EXECUTE_SCSI Command = %02X\n", srb->Cdb[0]));
      srb_status = SRB_STATUS_ERROR;
      break;
    }
    if (srb_status == SRB_STATUS_ERROR)
    {
      KdPrint((__DRIVER_NAME "     EXECUTE_SCSI Command = %02X returned error %02x\n", srb->Cdb[0], xvdd->last_sense_key));
      if (xvdd->last_sense_key == SCSI_SENSE_NO_SENSE)
      {
        xvdd->last_sense_key = SCSI_SENSE_ILLEGAL_REQUEST;
        xvdd->last_additional_sense_code = SCSI_ADSENSE_INVALID_CDB;
      }
      srb->SrbStatus = srb_status;
      srb->ScsiStatus = 0x02;
      XenVbd_MakeAutoSense(xvdd, srb);
      StorPortNotification(RequestComplete, DeviceExtension, srb);
    }
    else if (srb_status != SRB_STATUS_PENDING)
    {
      if (data_transfer_length > srb->DataTransferLength)
        KdPrint((__DRIVER_NAME "     data_transfer_length too big - %d > %d\n", data_transfer_length, srb->DataTransferLength));
      
      if (srb_status == SRB_STATUS_SUCCESS && data_transfer_length < srb->DataTransferLength)
      {
        srb->SrbStatus = SRB_STATUS_DATA_OVERRUN;
        srb->DataTransferLength = data_transfer_length;
      }
      else
      {
        srb->SrbStatus = srb_status;
      }
      xvdd->last_sense_key = SCSI_SENSE_NO_SENSE;
      xvdd->last_additional_sense_code = SCSI_ADSENSE_NO_SENSE;
      StorPortNotification(RequestComplete, DeviceExtension, srb);
    }
    break;
  case SRB_FUNCTION_IO_CONTROL:
    KdPrint((__DRIVER_NAME "     SRB_FUNCTION_IO_CONTROL\n"));
    srb->SrbStatus = SRB_STATUS_INVALID_REQUEST;
    StorPortNotification(RequestComplete, DeviceExtension, srb);
    break;
  case SRB_FUNCTION_FLUSH:
    KdPrint((__DRIVER_NAME "     SRB_FUNCTION_FLUSH %p, xvdd->shadow_free = %d\n", srb, xvdd->shadow_free));
    srb->SrbStatus = SRB_STATUS_SUCCESS;
    StorPortNotification(RequestComplete, DeviceExtension, srb);
    break;
  case SRB_FUNCTION_PNP:
    KdPrint((__DRIVER_NAME "     SRB_FUNCTION_PNP\n"));
    sprb = (PSCSI_PNP_REQUEST_BLOCK)srb;
    switch (sprb->PnPAction)
    {
    case StorStartDevice:
      KdPrint((__DRIVER_NAME "      StorStartDevice\n"));
      break;
    case StorRemoveDevice:
      KdPrint((__DRIVER_NAME "      StorRemoveDevice\n"));
      break;
    case StorStopDevice:
      KdPrint((__DRIVER_NAME "      StorStopDevice\n"));
      break;
    case StorQueryCapabilities:
      KdPrint((__DRIVER_NAME "      StorQueryCapabilities\n"));
      break;
    case StorFilterResourceRequirements:
      KdPrint((__DRIVER_NAME "      StorFilterResourceRequirements\n"));
      break;
    default:
      KdPrint((__DRIVER_NAME "      Stor%d\n", sprb->PnPAction));
      break;
    }
    KdPrint((__DRIVER_NAME "      SrbPnPFlags = %08x\n", sprb->SrbPnPFlags));
    srb->SrbStatus = SRB_STATUS_SUCCESS;
    StorPortNotification(RequestComplete, DeviceExtension, srb);
    break;
    
  case SRB_FUNCTION_POWER:
    KdPrint((__DRIVER_NAME "     SRB_FUNCTION_POWER\n"));
    spwrb = (PSCSI_POWER_REQUEST_BLOCK)srb;
    switch (spwrb->PowerAction)
    {
    case StorPowerActionNone:
      KdPrint((__DRIVER_NAME "      StorPowerActionNone\n"));
      break;
    case StorPowerActionReserved:
      KdPrint((__DRIVER_NAME "      StorPowerActionReserved\n"));
      break;
    case StorPowerActionSleep:
      KdPrint((__DRIVER_NAME "      StorPowerActionSleep\n"));
      break;
    case StorPowerActionHibernate:
      KdPrint((__DRIVER_NAME "      StorPowerActionHibernate\n"));
      break;
    case StorPowerActionShutdown:
      KdPrint((__DRIVER_NAME "      StorPowerActionShutdown\n"));
      break;
    case StorPowerActionShutdownReset:
      KdPrint((__DRIVER_NAME "      StorPowerActionShutdownReset\n"));
      break;
    case StorPowerActionShutdownOff:
      KdPrint((__DRIVER_NAME "      StorPowerActionShutdownOff\n"));
      break;
    case StorPowerActionWarmEject:
      KdPrint((__DRIVER_NAME "      StorPowerActionWarmEject\n"));
      break;
    default:
      KdPrint((__DRIVER_NAME "      Stor%d\n", spwrb->PowerAction));
      break;
    }
    XenVbd_PutSrbOnList(xvdd, srb);
    XenVbd_PutQueuedSrbsOnRing(xvdd);
    break;
  case SRB_FUNCTION_DUMP_POINTERS:
    KdPrint((__DRIVER_NAME "     SRB_FUNCTION_DUMP_POINTERS\n"));
    KdPrint((__DRIVER_NAME "     DataTransferLength = %d\n", srb->DataTransferLength));
    dump_pointers = srb->DataBuffer;
    KdPrint((__DRIVER_NAME "      Version = %d\n", dump_pointers->Version));
    KdPrint((__DRIVER_NAME "      Size = %d\n", dump_pointers->Size));
    KdPrint((__DRIVER_NAME "      DriverName = %S\n", dump_pointers->DriverName));
    KdPrint((__DRIVER_NAME "      AdapterObject = %p\n", dump_pointers->AdapterObject));
    KdPrint((__DRIVER_NAME "      MappedRegisterBase = %d\n", dump_pointers->MappedRegisterBase));
    KdPrint((__DRIVER_NAME "      CommonBufferSize = %d\n", dump_pointers->CommonBufferSize));
    KdPrint((__DRIVER_NAME "      MiniportPrivateDumpData = %p\n", dump_pointers->MiniportPrivateDumpData));
    KdPrint((__DRIVER_NAME "      SystemIoBusNumber = %d\n", dump_pointers->SystemIoBusNumber));
    KdPrint((__DRIVER_NAME "      AdapterInterfaceType = %d\n", dump_pointers->AdapterInterfaceType));
    KdPrint((__DRIVER_NAME "      MaximumTransferLength = %d\n", dump_pointers->MaximumTransferLength));
    KdPrint((__DRIVER_NAME "      NumberOfPhysicalBreaks = %d\n", dump_pointers->NumberOfPhysicalBreaks));
    KdPrint((__DRIVER_NAME "      AlignmentMask = %d\n", dump_pointers->AlignmentMask));
    KdPrint((__DRIVER_NAME "      NumberOfAccessRanges = %d\n", dump_pointers->NumberOfAccessRanges));
    KdPrint((__DRIVER_NAME "      NumberOfBuses = %d\n", dump_pointers->NumberOfBuses));
    KdPrint((__DRIVER_NAME "      Master = %d\n", dump_pointers->Master));
    KdPrint((__DRIVER_NAME "      MapBuffers = %d\n", dump_pointers->MapBuffers));
    KdPrint((__DRIVER_NAME "      MaximumNumberOfTargets = %d\n", dump_pointers->MaximumNumberOfTargets));

    dump_pointers->Version = DUMP_MINIPORT_VERSION_1;
    dump_pointers->Size = sizeof(MINIPORT_DUMP_POINTERS);
    RtlStringCchCopyW(dump_pointers->DriverName, DUMP_MINIPORT_NAME_LENGTH, L"xenvbd.sys");
    dump_pointers->AdapterObject = NULL;
    dump_pointers->MappedRegisterBase = 0;
    dump_pointers->CommonBufferSize = 0;
    dump_pointers->MiniportPrivateDumpData = (PVOID)xvdd->device_base;
    //dump_pointers->SystemIoBusNumber = 0;
    dump_pointers->AdapterInterfaceType = Internal;
    dump_pointers->MaximumTransferLength = 4 * 1024 * 1024; //BLKIF_MAX_SEGMENTS_PER_REQUEST * PAGE_SIZE;;
    dump_pointers->NumberOfPhysicalBreaks = dump_pointers->MaximumTransferLength >> PAGE_SHIFT; //BLKIF_MAX_SEGMENTS_PER_REQUEST - 1;
    dump_pointers->AlignmentMask = 0;
    dump_pointers->NumberOfAccessRanges = 1;
    dump_pointers->NumberOfBuses = 1;
    dump_pointers->Master = TRUE;
    dump_pointers->MapBuffers = STOR_MAP_NON_READ_WRITE_BUFFERS;
    dump_pointers->MaximumNumberOfTargets = 2;

    KdPrint((__DRIVER_NAME "      Version = %d\n", dump_pointers->Version));
    KdPrint((__DRIVER_NAME "      Size = %d\n", dump_pointers->Size));
    //KdPrint((__DRIVER_NAME "      DriverName = %S\n", dump_pointers->DriverName));
    KdPrint((__DRIVER_NAME "      AdapterObject = %p\n", dump_pointers->AdapterObject));
    KdPrint((__DRIVER_NAME "      MappedRegisterBase = %d\n", dump_pointers->MappedRegisterBase));
    KdPrint((__DRIVER_NAME "      CommonBufferSize = %d\n", dump_pointers->CommonBufferSize));
    KdPrint((__DRIVER_NAME "      MiniportPrivateDumpData = %p\n", dump_pointers->MiniportPrivateDumpData));
    KdPrint((__DRIVER_NAME "      SystemIoBusNumber = %d\n", dump_pointers->SystemIoBusNumber));
    KdPrint((__DRIVER_NAME "      AdapterInterfaceType = %d\n", dump_pointers->AdapterInterfaceType));
    KdPrint((__DRIVER_NAME "      MaximumTransferLength = %d\n", dump_pointers->MaximumTransferLength));
    KdPrint((__DRIVER_NAME "      NumberOfPhysicalBreaks = %d\n", dump_pointers->NumberOfPhysicalBreaks));
    KdPrint((__DRIVER_NAME "      AlignmentMask = %d\n", dump_pointers->AlignmentMask));
    KdPrint((__DRIVER_NAME "      NumberOfAccessRanges = %d\n", dump_pointers->NumberOfAccessRanges));
    KdPrint((__DRIVER_NAME "      NumberOfBuses = %d\n", dump_pointers->NumberOfBuses));
    KdPrint((__DRIVER_NAME "      Master = %d\n", dump_pointers->Master));
    KdPrint((__DRIVER_NAME "      MapBuffers = %d\n", dump_pointers->MapBuffers));
    KdPrint((__DRIVER_NAME "      MaximumNumberOfTargets = %d\n", dump_pointers->MaximumNumberOfTargets));

    srb->SrbStatus = SRB_STATUS_SUCCESS;
    StorPortNotification(RequestComplete, DeviceExtension, srb);
    break;
  case SRB_FUNCTION_SHUTDOWN:
    KdPrint((__DRIVER_NAME "     SRB_FUNCTION_SHUTDOWN %p, xvdd->shadow_free = %d\n", srb, xvdd->shadow_free));
    //ASSERT(IsListEmpty(&xvdd->srb_list));
    //ASSERT(xvdd->shadow_free == SHADOW_ENTRIES);
    XenVbd_PutSrbOnList(xvdd, srb);
    XenVbd_PutQueuedSrbsOnRing(xvdd);
    //srb->SrbStatus = SRB_STATUS_SUCCESS;
    //StorPortNotification(RequestComplete, DeviceExtension, srb);
    break;
  case SRB_FUNCTION_RESET_BUS:
  case SRB_FUNCTION_RESET_DEVICE:
  case SRB_FUNCTION_RESET_LOGICAL_UNIT:
    /* the path doesn't matter here - only ever one device*/
    XenVbd_HwStorResetBus(DeviceExtension, 0);
    srb->SrbStatus = SRB_STATUS_SUCCESS;
    StorPortNotification(RequestComplete, DeviceExtension, srb);    
    break;
  
  default:
    KdPrint((__DRIVER_NAME "     Unhandled srb->Function = %08X\n", srb->Function));
    srb->SrbStatus = SRB_STATUS_INVALID_REQUEST;
    StorPortNotification(RequestComplete, DeviceExtension, srb);
    break;
  }

  //if (dump_mode) FUNCTION_EXIT();
  StorPortReleaseSpinLock(DeviceExtension, &lock_handle);
  return TRUE;
}

static SCSI_ADAPTER_CONTROL_STATUS
XenVbd_HwStorAdapterControl(PVOID DeviceExtension, SCSI_ADAPTER_CONTROL_TYPE ControlType, PVOID Parameters)
{
  PXENVBD_DEVICE_DATA xvdd = DeviceExtension;
  SCSI_ADAPTER_CONTROL_STATUS Status = ScsiAdapterControlSuccess;
  PSCSI_SUPPORTED_CONTROL_TYPE_LIST SupportedControlTypeList;
  //KIRQL OldIrql;

  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));
  KdPrint((__DRIVER_NAME "     xvdd = %p\n", xvdd));

  switch (ControlType)
  {
  case ScsiQuerySupportedControlTypes:
    SupportedControlTypeList = (PSCSI_SUPPORTED_CONTROL_TYPE_LIST)Parameters;
    KdPrint((__DRIVER_NAME "     ScsiQuerySupportedControlTypes (Max = %d)\n", SupportedControlTypeList->MaxControlType));
    SupportedControlTypeList->SupportedTypeList[ScsiQuerySupportedControlTypes] = TRUE;
    SupportedControlTypeList->SupportedTypeList[ScsiStopAdapter] = TRUE;
    SupportedControlTypeList->SupportedTypeList[ScsiRestartAdapter] = TRUE;
    break;
  case ScsiStopAdapter:
    KdPrint((__DRIVER_NAME "     ScsiStopAdapter\n"));
    if (xvdd->inactive)
    {
      KdPrint((__DRIVER_NAME "     inactive - nothing to do\n"));
      break;
    }
    ASSERT(IsListEmpty(&xvdd->srb_list));
    ASSERT(xvdd->shadow_free == SHADOW_ENTRIES);
    break;
  case ScsiRestartAdapter:
    KdPrint((__DRIVER_NAME "     ScsiRestartAdapter\n"));
    if (xvdd->inactive)
    {
      KdPrint((__DRIVER_NAME "     inactive - nothing to do\n"));
      break;
    }
    /* increase the tag every time we stop/start to track where the gref's came from */
    xvdd->grant_tag++;
    if (XenVbd_InitFromConfig(xvdd) != SP_RETURN_FOUND)
      KeBugCheckEx(DATA_COHERENCY_EXCEPTION, 0, (ULONG_PTR)xvdd, 0, 0);
    xvdd->ring_detect_state = RING_DETECT_STATE_NOT_STARTED;
    
    //XenVbd_StartRingDetection(xvdd);
    break;
  case ScsiSetBootConfig:
    KdPrint((__DRIVER_NAME "     ScsiSetBootConfig\n"));
    break;
  case ScsiSetRunningConfig:
    KdPrint((__DRIVER_NAME "     ScsiSetRunningConfig\n"));
    break;
  default:
    KdPrint((__DRIVER_NAME "     UNKNOWN\n"));
    break;
  }

  FUNCTION_EXIT();
  
  return Status;
}

NTSTATUS
DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath)
{
  ULONG status;
  VIRTUAL_HW_INITIALIZATION_DATA VHwInitializationData;
  HW_INITIALIZATION_DATA HwInitializationData;
  OBJECT_ATTRIBUTES oa;
  HANDLE service_handle;
  UNICODE_STRING param_name;
  HANDLE param_handle;
  UNICODE_STRING value_name;
  CHAR buf[256];
  ULONG buf_len;
  PKEY_VALUE_PARTIAL_INFORMATION kpv;
  
  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));
  KdPrint((__DRIVER_NAME "     DriverObject = %p, RegistryPath = %p\n", DriverObject, RegistryPath));

  /* RegistryPath == NULL when we are invoked as a crash dump driver */
  if (!RegistryPath)
  {
    dump_mode = TRUE;
  }
  
  if (!dump_mode)
  {
    InitializeObjectAttributes(&oa, RegistryPath, OBJ_CASE_INSENSITIVE, NULL, NULL);
    status = ZwOpenKey(&service_handle, KEY_READ, &oa);
    if(!NT_SUCCESS(status))
    {
      KdPrint((__DRIVER_NAME "     ZwOpenKey(Service) returned %08x\n", status));
    }
    else
    {
      RtlInitUnicodeString(&param_name, L"Parameters");
      InitializeObjectAttributes(&oa, &param_name, OBJ_CASE_INSENSITIVE, service_handle, NULL);
      status = ZwOpenKey(&param_handle, KEY_READ, &oa);
      if(!NT_SUCCESS(status))
      {
        KdPrint((__DRIVER_NAME "     ZwOpenKey(Parameters) returned %08x\n", status));
      }
      else
      {
        kpv = (PKEY_VALUE_PARTIAL_INFORMATION)buf;
        RtlFillMemory(scsi_device_manufacturer, 8, ' ');
        RtlFillMemory(scsi_disk_model, 16, ' ');
        RtlFillMemory(scsi_cdrom_model, 16, ' ');

        RtlInitUnicodeString(&value_name, L"Manufacturer");
        buf_len = 256;
        status = ZwQueryValueKey(param_handle, &value_name, KeyValuePartialInformation, buf, buf_len, &buf_len);
        if(NT_SUCCESS(status))
          wcstombs(scsi_device_manufacturer, (PWCHAR)kpv->Data, min(kpv->DataLength, 8));
        else
          RtlStringCbCopyA(scsi_device_manufacturer, 8, "XEN     ");

        RtlInitUnicodeString(&value_name, L"Disk_Model");
        buf_len = 256;
        status = ZwQueryValueKey(param_handle, &value_name, KeyValuePartialInformation, buf, buf_len, &buf_len);
        if(NT_SUCCESS(status))
          wcstombs(scsi_disk_model, (PWCHAR)kpv->Data, min(kpv->DataLength, 16));
        else
          RtlStringCbCopyA(scsi_disk_model, 16, "PV DISK          ");

        RtlInitUnicodeString(&value_name, L"CDROM_Model");
        buf_len = 256;
        status = ZwQueryValueKey(param_handle, &value_name, KeyValuePartialInformation, buf, buf_len, &buf_len);
        if(NT_SUCCESS(status))
          wcstombs(scsi_cdrom_model, (PWCHAR)kpv->Data, min(kpv->DataLength, 16));
        else
          RtlStringCbCopyA(scsi_cdrom_model, 16, "PV CDROM        ");
        ZwClose(param_handle);
      }
      ZwClose(service_handle);
    }  
    RtlZeroMemory(&VHwInitializationData, sizeof(VIRTUAL_HW_INITIALIZATION_DATA));
    VHwInitializationData.HwInitializationDataSize = sizeof(VIRTUAL_HW_INITIALIZATION_DATA);
    VHwInitializationData.AdapterInterfaceType = Internal; //PNPBus; /* maybe should be internal? */
    VHwInitializationData.DeviceExtensionSize = FIELD_OFFSET(XENVBD_DEVICE_DATA, aligned_buffer_data) + UNALIGNED_BUFFER_DATA_SIZE;
    VHwInitializationData.SpecificLuExtensionSize = 0;
    VHwInitializationData.SrbExtensionSize = sizeof(srb_list_entry_t);
    VHwInitializationData.NumberOfAccessRanges = 1;
    VHwInitializationData.MapBuffers = STOR_MAP_ALL_BUFFERS;
    //VHwInitializationData.NeedPhysicalAddresses  = TRUE;
    VHwInitializationData.TaggedQueuing = TRUE;
    VHwInitializationData.AutoRequestSense = TRUE;
    VHwInitializationData.MultipleRequestPerLu = TRUE;
    VHwInitializationData.ReceiveEvent = TRUE;
    VHwInitializationData.PortVersionFlags = 0;
    VHwInitializationData.HwInitialize = XenVbd_HwStorInitialize;
    VHwInitializationData.HwStartIo = XenVbd_HwStorStartIo;
    VHwInitializationData.HwFindAdapter = XenVbd_VirtualHwStorFindAdapter;
    VHwInitializationData.HwResetBus = XenVbd_HwStorResetBus;
    VHwInitializationData.HwAdapterControl = XenVbd_HwStorAdapterControl;
    status = StorPortInitialize(DriverObject, RegistryPath, (PHW_INITIALIZATION_DATA)&VHwInitializationData, NULL);
  }
  else
  {
    RtlZeroMemory(&HwInitializationData, sizeof(HW_INITIALIZATION_DATA));
    HwInitializationData.HwInitializationDataSize = sizeof(HW_INITIALIZATION_DATA);
    HwInitializationData.AdapterInterfaceType = Internal; //PNPBus; /* not Internal */
    HwInitializationData.DeviceExtensionSize = FIELD_OFFSET(XENVBD_DEVICE_DATA, aligned_buffer_data) + UNALIGNED_BUFFER_DATA_SIZE_DUMP_MODE;
    HwInitializationData.SrbExtensionSize = sizeof(srb_list_entry_t);
    HwInitializationData.NumberOfAccessRanges = 1;
    HwInitializationData.MapBuffers = STOR_MAP_NON_READ_WRITE_BUFFERS;
    HwInitializationData.NeedPhysicalAddresses  = TRUE;
    HwInitializationData.TaggedQueuing = FALSE;
    HwInitializationData.AutoRequestSense = TRUE;
    HwInitializationData.MultipleRequestPerLu = FALSE;
    HwInitializationData.ReceiveEvent = TRUE;
    HwInitializationData.HwInitialize = XenVbd_HwStorInitialize;
    HwInitializationData.HwStartIo = XenVbd_HwStorStartIo;
    HwInitializationData.HwFindAdapter = XenVbd_HwStorFindAdapter;
    HwInitializationData.HwResetBus = XenVbd_HwStorResetBus;
    HwInitializationData.HwAdapterControl = XenVbd_HwStorAdapterControl;
    HwInitializationData.HwInterrupt = XenVbd_HwStorInterrupt;
    status = StorPortInitialize(DriverObject, RegistryPath, &HwInitializationData, NULL);
  }
  
  if(!NT_SUCCESS(status))
  {
    KdPrint((__DRIVER_NAME " ScsiPortInitialize failed with status 0x%08x\n", status));
  }

  FUNCTION_EXIT();

  return status;
}
