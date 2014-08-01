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

#include "xenscsi.h"

/* Not really necessary but keeps PREfast happy */
DRIVER_INITIALIZE DriverEntry;

#ifdef ALLOC_PRAGMA
#pragma alloc_text (INIT, DriverEntry)
#endif

#pragma warning(disable: 4127)

static BOOLEAN dump_mode = FALSE;

static vscsiif_shadow_t *
get_shadow_from_freelist(PXENSCSI_DEVICE_DATA xsdd)
{
  if (xsdd->shadow_free == 0)
  {
    KdPrint((__DRIVER_NAME "     No more shadow entries\n"));    
    return NULL;
  }
  xsdd->shadow_free--;
  return &xsdd->shadows[xsdd->shadow_free_list[xsdd->shadow_free]];
}

static VOID
put_shadow_on_freelist(PXENSCSI_DEVICE_DATA xsdd, vscsiif_shadow_t *shadow)
{
  xsdd->shadow_free_list[xsdd->shadow_free] = (USHORT)shadow->req.rqid;
  shadow->Srb = NULL;
  xsdd->shadow_free++;
}

static grant_ref_t
get_grant_from_freelist(PXENSCSI_DEVICE_DATA xsdd)
{
  if (xsdd->grant_free == 0)
  {
    KdPrint((__DRIVER_NAME "     No more grant refs\n"));    
    return (grant_ref_t)0x0FFFFFFF;
  }
  xsdd->grant_free--;
  return xsdd->grant_free_list[xsdd->grant_free];
}

static VOID
put_grant_on_freelist(PXENSCSI_DEVICE_DATA xsdd, grant_ref_t grant)
{
  xsdd->grant_free_list[xsdd->grant_free] = grant;
  xsdd->grant_free++;
}

static VOID
XenScsi_CheckNewDevice(PVOID DeviceExtension)
{
  PXENSCSI_DEVICE_DATA xsdd = DeviceExtension;

  //FUNCTION_ENTER();
  
  if (InterlockedCompareExchange(&xsdd->shared_paused, SHARED_PAUSED_SCSIPORT_PAUSED, SHARED_PAUSED_PASSIVE_PAUSED) == SHARED_PAUSED_PASSIVE_PAUSED)
  {
    KdPrint((__DRIVER_NAME "     scsiport paused\n"));
    xsdd->scsiport_paused = TRUE;
  }
  if (InterlockedCompareExchange(&xsdd->shared_paused, SHARED_PAUSED_SCSIPORT_UNPAUSED, SHARED_PAUSED_PASSIVE_UNPAUSED) == SHARED_PAUSED_PASSIVE_UNPAUSED)
  {
    int i;
    KdPrint((__DRIVER_NAME "     scsiport unpaused\n"));
    xsdd->scsiport_paused = FALSE;
    for (i = 0; i < 8; i++)
    {  
      if (xsdd->bus_changes[i])
      {
        KdPrint((__DRIVER_NAME "     Sending BusChangeDetected for channel %d\n", i));
        ScsiPortNotification(BusChangeDetected, DeviceExtension, i);
      }
    }
    ScsiPortNotification(NextRequest, DeviceExtension);
  }
  if (xsdd->scsiport_paused) /* check more often if we are paused */
    ScsiPortNotification(RequestTimerCall, DeviceExtension, XenScsi_CheckNewDevice, 100 * 1000); /* 100ms second from the last check */
  else
    ScsiPortNotification(RequestTimerCall, DeviceExtension, XenScsi_CheckNewDevice, 1 * 1000 * 1000); /* 1 second from the last check */
  //FUNCTION_EXIT();
}

static BOOLEAN
XenScsi_HwScsiInterrupt(PVOID DeviceExtension)
{
  PXENSCSI_DEVICE_DATA xsdd = DeviceExtension;
  PSCSI_REQUEST_BLOCK Srb;
  RING_IDX i, rp;
  int j;
  vscsiif_response_t *rep;
  int more_to_do = TRUE;
  vscsiif_shadow_t *shadow;
  BOOLEAN last_interrupt = FALSE;

  XenScsi_CheckNewDevice(DeviceExtension);

  if (!dump_mode && !xsdd->vectors.EvtChn_AckEvent(xsdd->vectors.context, xsdd->event_channel, &last_interrupt))
  {
    return FALSE;
  }

  //FUNCTION_ENTER();
  
  while (more_to_do)
  {
    rp = xsdd->ring.sring->rsp_prod;
    KeMemoryBarrier();
    for (i = xsdd->ring.rsp_cons; i != rp; i++)
    {
      rep = RING_GET_RESPONSE(&xsdd->ring, i);
      shadow = &xsdd->shadows[rep->rqid];
      Srb = shadow->Srb;
      Srb->ScsiStatus = (UCHAR)rep->rslt;
      memset(Srb->SenseInfoBuffer, 0, Srb->SenseInfoBufferLength);
      if (rep->sense_len > 0 && Srb->SenseInfoBuffer != NULL)
      {
        memcpy(Srb->SenseInfoBuffer, rep->sense_buffer, min(Srb->SenseInfoBufferLength, rep->sense_len));
      }
      switch(rep->rslt)
      {
      case 0:
        //KdPrint((__DRIVER_NAME "     Xen Operation complete - result = 0x%08x, sense_len = %d, residual = %d\n", rep->rslt, rep->sense_len, rep->residual_len));
        Srb->SrbStatus = SRB_STATUS_SUCCESS;
        if (Srb->Cdb[0] == 0x03)
        {
          KdPrint((__DRIVER_NAME "     REQUEST_SENSE DataTransferLength = %d, residual = %d\n", Srb->DataTransferLength, rep->residual_len));
          //for (j = 0; j < Srb->DataTransferLength - rep->residual_len; j++)
          //  KdPrint((__DRIVER_NAME "     sense %02x: %02x\n", j, (ULONG)((PUCHAR)Srb->DataBuffer)[j]));
        }
        break;
      case 0x00010000: /* Device does not exist */
        KdPrint((__DRIVER_NAME "     Xen Operation error - cdb[0] = %02x, result = 0x%08x, sense_len = %d, residual = %d\n", (ULONG)Srb->Cdb[0], rep->rslt, rep->sense_len, rep->residual_len));
        Srb->SrbStatus = SRB_STATUS_NO_DEVICE;
        break;
      default:
        KdPrint((__DRIVER_NAME "     Xen Operation error - cdb[0] = %02x, result = 0x%08x, sense_len = %d, residual = %d\n", (ULONG)Srb->Cdb[0], rep->rslt, rep->sense_len, rep->residual_len));
        Srb->SrbStatus = SRB_STATUS_ERROR;

        //for (j = 0; j < Srb->SenseInfoBufferLength; j++)
        //  KdPrint((__DRIVER_NAME "     sense %02x: %02x\n", j, (ULONG)((PUCHAR)Srb->SenseInfoBuffer)[j]));

        if (rep->sense_len > 0 && !(Srb->SrbFlags & SRB_FLAGS_DISABLE_AUTOSENSE) && Srb->SenseInfoBuffer != NULL)
        {
          KdPrint((__DRIVER_NAME "     Doing autosense\n"));
          Srb->SrbStatus |= SRB_STATUS_AUTOSENSE_VALID;
        }
        else if (Srb->SrbFlags & SRB_FLAGS_DISABLE_AUTOSENSE)
        {
          PXENSCSI_LU_DATA lud = ScsiPortGetLogicalUnit(DeviceExtension, Srb->PathId, Srb->TargetId, Srb->Lun);
          KdPrint((__DRIVER_NAME "     Autosense disabled\n"));
          if (lud != NULL)
          {
            KdPrint((__DRIVER_NAME "     Saving sense data\n"));
            lud->sense_len = rep->sense_len;
            memcpy(lud->sense_buffer, Srb->SenseInfoBuffer, lud->sense_len);
          }
        }
      }

      /* work around a bug in scsiback that gives an incorrect result to REPORT_LUNS - fail it if the output is only 8 bytes */
      if (Srb->Cdb[0] == 0xa0 && Srb->SrbStatus == SRB_STATUS_SUCCESS &&
        Srb->DataTransferLength - rep->residual_len == 8)
      {
        /* SRB_STATUS_ERROR appears to be sufficient here - no need to worry about sense data or anything */
        KdPrint((__DRIVER_NAME "     Worked around bad REPORT_LUNS emulation for %d:%d:%d\n",
          Srb->PathId, Srb->TargetId, Srb->Lun));
        Srb->SrbStatus = SRB_STATUS_ERROR;
      }
      //remaining = Srb->DataTransferLength;
      for (j = 0; j < shadow->req.nr_segments; j++)
      {
        xsdd->vectors.GntTbl_EndAccess(xsdd->vectors.context, shadow->req.seg[j].gref, TRUE, (ULONG)'SCSI');
        put_grant_on_freelist(xsdd, shadow->req.seg[j].gref);
        shadow->req.seg[j].gref = 0;
      }

      if (Srb->SrbStatus == SRB_STATUS_SUCCESS && rep->residual_len)
      {
//        KdPrint((__DRIVER_NAME "     SRB_STATUS_DATA_OVERRUN DataTransferLength = %d, adjusted = %d\n",
//          Srb->DataTransferLength, Srb->DataTransferLength - rep->residual_len));
        Srb->DataTransferLength -= rep->residual_len;
        Srb->SrbStatus = SRB_STATUS_DATA_OVERRUN;
      }

      put_shadow_on_freelist(xsdd, shadow);
      ScsiPortNotification(RequestComplete, xsdd, Srb);
      if (!xsdd->scsiport_paused)
        ScsiPortNotification(NextRequest, DeviceExtension);
    }

    xsdd->ring.rsp_cons = i;
    if (i != xsdd->ring.req_prod_pvt)
    {
      RING_FINAL_CHECK_FOR_RESPONSES(&xsdd->ring, more_to_do);
    }
    else
    {
      xsdd->ring.sring->rsp_event = i + 1;
      more_to_do = FALSE;
    }
  }

  //FUNCTION_EXIT();
  
  return last_interrupt;
}

static VOID
XenScsi_ParseBackendDevice(scsi_dev_t *dev, PCHAR value)
{
  int i = 0;
  int j = 0;
  BOOLEAN scanning = TRUE;

  while (scanning)
  {
    if (value[i] == 0)
      scanning = FALSE;
    if (value[i] == ':' || value[i] == 0)
    {
       value[i] = 0;
       dev->host = dev->channel;
       dev->channel = dev->id;
       dev->id = dev->lun;
       dev->lun = (UCHAR)atoi(&value[j]);
       j = i + 1;
    }
    i++;
  }
  KdPrint((__DRIVER_NAME "     host = %d, channel = %d, id = %d, lun = %d\n",
    dev->host, dev->channel, dev->id, dev->lun));  
}

/* CALLED AT PASSIVE LEVEL */
/* If Initialize fails then the watch still gets called but the waits will never be acked... */
static VOID
XenScsi_DevWatch(PCHAR path, PVOID DeviceExtension)
{
  PXENSCSI_DEVICE_DATA xsdd = DeviceExtension;
  CHAR tmp_path[128];
  PCHAR msg;
  PCHAR *devices;
  PCHAR value;
  scsi_dev_t *dev;
  ULONG i;
  ULONG dev_no;
  ULONG state;
  LARGE_INTEGER wait_time;
  #if DBG
  ULONG oldpause;
  #endif

  UNREFERENCED_PARAMETER(path);
  
  /* this can only be called from a watch and so is always serialised */
  FUNCTION_ENTER();

  #if DBG
  oldpause =
  #endif
    InterlockedExchange(&xsdd->shared_paused, SHARED_PAUSED_PASSIVE_PAUSED);
  ASSERT(oldpause == SHARED_PAUSED_SCSIPORT_UNPAUSED);
  
  while (InterlockedCompareExchange(&xsdd->shared_paused, SHARED_PAUSED_SCSIPORT_PAUSED, SHARED_PAUSED_SCSIPORT_PAUSED) != SHARED_PAUSED_SCSIPORT_PAUSED)
  {
    KdPrint((__DRIVER_NAME "     Waiting for pause...\n"));
    wait_time.QuadPart = -100 * 1000 * 10; /* 100ms */
    KeDelayExecutionThread(KernelMode, FALSE, &wait_time);
  }
  
  KdPrint((__DRIVER_NAME "     Watch triggered on %s\n", path));
  RtlStringCbCopyA(tmp_path, ARRAY_SIZE(tmp_path), xsdd->vectors.backend_path);
  RtlStringCbCatA(tmp_path, ARRAY_SIZE(tmp_path), "/vscsi-devs");
  msg = xsdd->vectors.XenBus_List(xsdd->vectors.context, XBT_NIL, tmp_path, &devices);
  if (msg)
  {
    /* this is pretty fatal ... */
    KdPrint((__DRIVER_NAME "     cannot read - %s\n", msg));
    return;
  }
  for (dev = (scsi_dev_t *)xsdd->dev_list_head.Flink;
    dev != (scsi_dev_t *)&xsdd->dev_list_head;
    dev = (scsi_dev_t *)dev->entry.Flink)
  {
    dev->validated = FALSE;
  }
  
  for (i = 0; devices[i]; i++)
  {
    if (strncmp(devices[i], "dev-", 4) != 0)
    {
      XenPci_FreeMem(devices[i]);
      break; /* not a dev so we are not interested */
    }
    dev_no = atoi(devices[i] + 4);
    RtlStringCbCopyA(tmp_path, ARRAY_SIZE(tmp_path), xsdd->vectors.backend_path);
    RtlStringCbCatA(tmp_path, ARRAY_SIZE(tmp_path), "/vscsi-devs/");
    RtlStringCbCatA(tmp_path, ARRAY_SIZE(tmp_path), devices[i]);
    RtlStringCbCatA(tmp_path, ARRAY_SIZE(tmp_path), "/state");
    msg = xsdd->vectors.XenBus_Read(xsdd->vectors.context, XBT_NIL, tmp_path, &value);
    if (msg)
    {
      KdPrint((__DRIVER_NAME "     failed to read state for device %d\n", dev_no));
      state = 0;
    }
    else
      state = atoi(value);
    for (dev = (scsi_dev_t *)xsdd->dev_list_head.Flink;
      dev != (scsi_dev_t *)&xsdd->dev_list_head;
      dev = (scsi_dev_t * )dev->entry.Flink)
    {
      if (dev->dev_no == dev_no)
        break;
    }
    if (dev == (scsi_dev_t *)&xsdd->dev_list_head)
    {
      KdPrint((__DRIVER_NAME "     new dev %d\n", dev_no));
      dev = ExAllocatePoolWithTag(NonPagedPool, sizeof(scsi_dev_t), XENSCSI_POOL_TAG);
      dev->dev_no = dev_no;
      dev->state = state;
      dev->validated = TRUE;
      RtlStringCbCopyA(tmp_path, ARRAY_SIZE(tmp_path), xsdd->vectors.backend_path);
      RtlStringCbCatA(tmp_path, ARRAY_SIZE(tmp_path), "/vscsi-devs/");
      RtlStringCbCatA(tmp_path, ARRAY_SIZE(tmp_path), devices[i]);
      RtlStringCbCatA(tmp_path, ARRAY_SIZE(tmp_path), "/v-dev");
      msg = xsdd->vectors.XenBus_Read(xsdd->vectors.context, XBT_NIL, tmp_path, &value);
      if (msg)
      {
        KdPrint((__DRIVER_NAME "     failed to read v-dev for device %d\n", dev_no));
        continue;
      }
      else
      {
        XenScsi_ParseBackendDevice(dev, value);
        // should verify that the controller = this
      }
      RtlStringCbCopyA(tmp_path, ARRAY_SIZE(tmp_path), xsdd->vectors.path);
      RtlStringCbCatA(tmp_path, ARRAY_SIZE(tmp_path), "/vscsi-devs/");
      RtlStringCbCatA(tmp_path, ARRAY_SIZE(tmp_path), devices[i]);
      RtlStringCbCatA(tmp_path, ARRAY_SIZE(tmp_path), "/state");
      msg = xsdd->vectors.XenBus_Write(xsdd->vectors.context, XBT_NIL, tmp_path, "4");
      if (msg)
      {
        KdPrint((__DRIVER_NAME "     failed to write state %d to %s\n", 4, tmp_path));
        continue;
      }
      KdPrint((__DRIVER_NAME "     setting changes[%d]\n", dev->channel));
      xsdd->bus_changes[dev->channel] = 1;
      InsertTailList(&xsdd->dev_list_head, (PLIST_ENTRY)dev);
    }
    else
    {
      // need to manage state change
      // and write frontend state
      dev->state = state;
      dev->validated = TRUE;
      KdPrint((__DRIVER_NAME "     existing dev %d state = %d\n", dev_no, dev->state));
    }
    XenPci_FreeMem(devices[i]);
  }
  XenPci_FreeMem(devices);

  #if DBG
  oldpause =
  #endif
    InterlockedExchange(&xsdd->shared_paused, SHARED_PAUSED_PASSIVE_UNPAUSED);
  ASSERT(oldpause == SHARED_PAUSED_SCSIPORT_PAUSED);

  while (InterlockedCompareExchange(&xsdd->shared_paused, SHARED_PAUSED_SCSIPORT_UNPAUSED, SHARED_PAUSED_SCSIPORT_UNPAUSED) != SHARED_PAUSED_SCSIPORT_UNPAUSED)
  {
    KdPrint((__DRIVER_NAME "     Waiting for unpause...\n"));
    wait_time.QuadPart = -100 * 1000 * 10; /* 100ms */
    KeDelayExecutionThread(KernelMode, FALSE, &wait_time);
  }
  KdPrint((__DRIVER_NAME "     Unpaused\n"));

  FUNCTION_EXIT();
}

static ULONG
XenScsi_HwScsiFindAdapter(PVOID DeviceExtension, PVOID Reserved1, PVOID Reserved2, PCHAR ArgumentString, PPORT_CONFIGURATION_INFORMATION ConfigInfo, PUCHAR Reserved3)
{
  ULONG i;
  PXENSCSI_DEVICE_DATA xsdd = DeviceExtension;
  PACCESS_RANGE access_range;
  PUCHAR ptr;
  USHORT type;
  PCHAR setting, value, value2;
  vscsiif_sring_t *sring;
  CHAR path[128];

  UNREFERENCED_PARAMETER(Reserved1);
  UNREFERENCED_PARAMETER(Reserved2);
  UNREFERENCED_PARAMETER(ArgumentString);
  UNREFERENCED_PARAMETER(Reserved3);

  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));
  
  xsdd->scsiport_paused = TRUE; /* wait for initial scan */

  KdPrint((__DRIVER_NAME "     BusInterruptLevel = %d\n", ConfigInfo->BusInterruptLevel));
  KdPrint((__DRIVER_NAME "     BusInterruptVector = %03x\n", ConfigInfo->BusInterruptVector));

  if (!ConfigInfo->BusInterruptVector)
  {
    KdPrint((__DRIVER_NAME "     No Interrupt assigned\n"));
    return SP_RETURN_BAD_CONFIG;
  }

  if (ConfigInfo->NumberOfAccessRanges != 1)
  {
    KdPrint((__DRIVER_NAME "     NumberOfAccessRanges = %d\n", ConfigInfo->NumberOfAccessRanges));
    return SP_RETURN_BAD_CONFIG;
  }

  ptr = NULL;
  access_range = &((*(ConfigInfo->AccessRanges))[0]);
  KdPrint((__DRIVER_NAME "     RangeStart = %08x, RangeLength = %08x\n",
    access_range->RangeStart.LowPart, access_range->RangeLength));
  ptr = ScsiPortGetDeviceBase(
    DeviceExtension,
    ConfigInfo->AdapterInterfaceType,
    ConfigInfo->SystemIoBusNumber,
    access_range->RangeStart,
    access_range->RangeLength,
    !access_range->RangeInMemory);
  if (!ptr)
  {
    KdPrint((__DRIVER_NAME "     Unable to map range\n"));
    KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ "\n"));  
    return SP_RETURN_BAD_CONFIG;
  }
  sring = NULL;
  xsdd->event_channel = 0;
  while((type = GET_XEN_INIT_RSP(&ptr, &setting, &value, &value2)) != XEN_INIT_TYPE_END)
  {
    switch(type)
    {
    case XEN_INIT_TYPE_RING: /* frontend ring */
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_RING - %s = %p\n", setting, value));
      if (strcmp(setting, "ring-ref") == 0)
      {
        sring = (vscsiif_sring_t *)value;
        FRONT_RING_INIT(&xsdd->ring, sring, PAGE_SIZE);
      }
      break;
    //case XEN_INIT_TYPE_EVENT_CHANNEL: /* frontend event channel */
    case XEN_INIT_TYPE_EVENT_CHANNEL_IRQ: /* frontend event channel */
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_EVENT_CHANNEL - %s = %d\n", setting, PtrToUlong(value)));
      if (strcmp(setting, "event-channel") == 0)
      {
        xsdd->event_channel = PtrToUlong(value);
      }
      break;
    case XEN_INIT_TYPE_READ_STRING_BACK:
    case XEN_INIT_TYPE_READ_STRING_FRONT:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_READ_STRING - %s = %s\n", setting, value));
      break;
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
        memcpy(&xsdd->vectors, value, sizeof(XENPCI_VECTORS));
      break;
    case XEN_INIT_TYPE_GRANT_ENTRIES:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_GRANT_ENTRIES - %d\n", PtrToUlong(value)));
      xsdd->grant_entries = (USHORT)PtrToUlong(value);
      memcpy(&xsdd->grant_free_list, value2, sizeof(grant_ref_t) * xsdd->grant_entries);
      xsdd->grant_free = xsdd->grant_entries;
      break;
    default:
      KdPrint((__DRIVER_NAME "     XEN_INIT_TYPE_%d\n", type));
      break;
    }
  }

  if (sring == NULL || xsdd->event_channel == 0)
  {
    KdPrint((__DRIVER_NAME "     Missing settings\n"));
    KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ "\n"));
    return SP_RETURN_BAD_CONFIG;
  }
  
  ConfigInfo->ScatterGather = TRUE;
  ConfigInfo->NumberOfPhysicalBreaks = VSCSIIF_SG_TABLESIZE - 1;
  ConfigInfo->MaximumTransferLength = VSCSIIF_SG_TABLESIZE * PAGE_SIZE;
  ConfigInfo->CachesData = FALSE;
  ConfigInfo->NumberOfBuses = 4; //SCSI_MAXIMUM_BUSES; //8
  ConfigInfo->MaximumNumberOfTargets = 16;
  ConfigInfo->MaximumNumberOfLogicalUnits = SCSI_MAXIMUM_LOGICAL_UNITS; // 8
  ConfigInfo->BufferAccessScsiPortControlled = TRUE;
  if (ConfigInfo->Dma64BitAddresses == SCSI_DMA64_SYSTEM_SUPPORTED)
  {
    ConfigInfo->Master = TRUE;
    ConfigInfo->Dma64BitAddresses = SCSI_DMA64_MINIPORT_SUPPORTED;
    KdPrint((__DRIVER_NAME "     Dma64BitAddresses supported\n"));
  }
  else
  {
    ConfigInfo->Master = FALSE;
    KdPrint((__DRIVER_NAME "     Dma64BitAddresses not supported\n"));
  }
  ConfigInfo->InitiatorBusId[0] = 7;
  ConfigInfo->InitiatorBusId[1] = 7;
  ConfigInfo->InitiatorBusId[2] = 7;
  ConfigInfo->InitiatorBusId[3] = 7;
  xsdd->shadow_free = 0;
  memset(xsdd->shadows, 0, sizeof(vscsiif_shadow_t) * SHADOW_ENTRIES);
  for (i = 0; i < SHADOW_ENTRIES; i++)
  {
    xsdd->shadows[i].req.rqid = (USHORT)i;
    put_shadow_on_freelist(xsdd, &xsdd->shadows[i]);
  }

  if (!dump_mode)
  {
    InitializeListHead(&xsdd->dev_list_head);
    /* should do something if we haven't enumerated in a certain time */
    RtlStringCbCopyA(path, ARRAY_SIZE(path), xsdd->vectors.backend_path);
    RtlStringCbCatA(path, ARRAY_SIZE(path), "/vscsi-devs");
    xsdd->vectors.XenBus_AddWatch(xsdd->vectors.context, XBT_NIL, path,
      XenScsi_DevWatch, xsdd);
  }
  FUNCTION_EXIT();

  return SP_RETURN_FOUND;
}

static BOOLEAN
XenScsi_HwScsiInitialize(PVOID DeviceExtension)
{
  PXENSCSI_DEVICE_DATA xsdd = DeviceExtension;
  UNREFERENCED_PARAMETER(DeviceExtension);

  FUNCTION_ENTER();
  xsdd->shared_paused = SHARED_PAUSED_SCSIPORT_UNPAUSED;
  ScsiPortNotification(RequestTimerCall, DeviceExtension, XenScsi_CheckNewDevice, 1 * 1000 * 1000); /* 1 second */
  
  FUNCTION_EXIT();

  return TRUE;
}

static VOID
XenScsi_PutSrbOnRing(PXENSCSI_DEVICE_DATA xsdd, PSCSI_REQUEST_BLOCK Srb)
{
  PHYSICAL_ADDRESS physical_address;
  ULONG remaining;
  PUCHAR ptr;
  //ULONG i;
  PFN_NUMBER pfn;
  vscsiif_shadow_t *shadow;
  int notify;

  //FUNCTION_ENTER();

  shadow = get_shadow_from_freelist(xsdd);
  ASSERT(shadow);
  shadow->Srb = Srb;
  shadow->req.act = VSCSIIF_ACT_SCSI_CDB;
  memset(shadow->req.cmnd, 0, VSCSIIF_MAX_COMMAND_SIZE);
  memcpy(shadow->req.cmnd, Srb->Cdb, min(Srb->CdbLength, VSCSIIF_MAX_COMMAND_SIZE));
  shadow->req.cmd_len = min(Srb->CdbLength, VSCSIIF_MAX_COMMAND_SIZE);
  shadow->req.timeout_per_command = (USHORT)Srb->TimeOutValue;
  shadow->req.channel = (USHORT)Srb->PathId;
  shadow->req.id = (USHORT)Srb->TargetId;
  shadow->req.lun = (USHORT)Srb->Lun;
  if (Srb->DataTransferLength && (Srb->SrbFlags & SRB_FLAGS_DATA_IN) && (Srb->SrbFlags & SRB_FLAGS_DATA_OUT))
  {
    //KdPrint((__DRIVER_NAME "     Cmd = %02x, Length = %d, DMA_BIDIRECTIONAL\n", Srb->Cdb[0], Srb->DataTransferLength));
    shadow->req.sc_data_direction = DMA_BIDIRECTIONAL;
  }
  else if (Srb->DataTransferLength && (Srb->SrbFlags & SRB_FLAGS_DATA_IN))
  {
    //KdPrint((__DRIVER_NAME "     Cmd = %02x, Length = %d, DMA_FROM_DEVICE\n", Srb->Cdb[0], Srb->DataTransferLength));
    shadow->req.sc_data_direction = DMA_FROM_DEVICE;
  }
  else if (Srb->DataTransferLength && (Srb->SrbFlags & SRB_FLAGS_DATA_OUT))
  {
    //KdPrint((__DRIVER_NAME "     Cmd = %02x, Length = %d, DMA_TO_DEVICE\n", Srb->Cdb[0], Srb->DataTransferLength));
    shadow->req.sc_data_direction = DMA_TO_DEVICE;
  }
  else
  {
    //KdPrint((__DRIVER_NAME "     Cmd = %02x, Length = %d, DMA_NONE\n", Srb->Cdb[0], Srb->DataTransferLength));
    shadow->req.sc_data_direction = DMA_NONE;
  }

  remaining = Srb->DataTransferLength;
  shadow->req.seg[0].offset = 0;
  shadow->req.seg[0].length = 0;
  shadow->req.nr_segments = 0;

  for (ptr = Srb->DataBuffer, shadow->req.nr_segments = 0; remaining != 0; shadow->req.nr_segments++)
  {
    if (shadow->req.nr_segments >= VSCSIIF_SG_TABLESIZE)
    {
      KdPrint((__DRIVER_NAME "     too many segments (length = %d, remaining = %d)\n", Srb->DataTransferLength, remaining));
    }
    physical_address = MmGetPhysicalAddress(ptr);
    pfn = (ULONG)(physical_address.QuadPart >> PAGE_SHIFT);
    shadow->req.seg[shadow->req.nr_segments].gref = get_grant_from_freelist(xsdd);
    if (shadow->req.seg[shadow->req.nr_segments].gref == 0x0FFFFFFF)
    {
      return; /* better than crashing... */
    }
    xsdd->vectors.GntTbl_GrantAccess(xsdd->vectors.context, 0, (ULONG)pfn, shadow->req.seg[shadow->req.nr_segments].gref, (ULONG)'SCSI');
    shadow->req.seg[shadow->req.nr_segments].offset = (USHORT)(physical_address.LowPart & (PAGE_SIZE - 1));
    shadow->req.seg[shadow->req.nr_segments].length = (USHORT)min(PAGE_SIZE - (ULONG)shadow->req.seg[shadow->req.nr_segments].offset, remaining);
    remaining -= (ULONG)shadow->req.seg[shadow->req.nr_segments].length;
    ptr += shadow->req.seg[shadow->req.nr_segments].length;
    //KdPrint((__DRIVER_NAME "     Page = %d, Offset = %d, Length = %d, Remaining = %d\n", shadow->req.nr_segments, shadow->req.seg[shadow->req.nr_segments].offset, shadow->req.seg[shadow->req.nr_segments].length, remaining));
  }
  *RING_GET_REQUEST(&xsdd->ring, xsdd->ring.req_prod_pvt) = shadow->req;
  xsdd->ring.req_prod_pvt++;
  RING_PUSH_REQUESTS_AND_CHECK_NOTIFY(&xsdd->ring, notify);
  if (notify)
  {
    //KdPrint((__DRIVER_NAME "     Notifying %d\n", xsdd->event_channel));
    xsdd->vectors.EvtChn_Notify(xsdd->vectors.context, xsdd->event_channel);
  }

  //FUNCTION_EXIT();
}

static BOOLEAN
XenScsi_HwScsiStartIo(PVOID DeviceExtension, PSCSI_REQUEST_BLOCK Srb)
{
  PXENSCSI_DEVICE_DATA xsdd = DeviceExtension;
  scsi_dev_t *dev;

  //FUNCTION_ENTER();
  
  XenScsi_CheckNewDevice(DeviceExtension);

  if (xsdd->scsiport_paused)
  {
    KdPrint((__DRIVER_NAME "     Busy\n"));
    Srb->SrbStatus = SRB_STATUS_BUSY;
    ScsiPortNotification(RequestComplete, DeviceExtension, Srb);
    //FUNCTION_EXIT();
    return TRUE;
  }

  for (dev = (scsi_dev_t *)xsdd->dev_list_head.Flink;
    dev != (scsi_dev_t *)&xsdd->dev_list_head;
    dev = (scsi_dev_t * )dev->entry.Flink)
  {
    if (dev->channel == Srb->PathId && dev->id == Srb->TargetId && dev->lun == Srb->Lun)
      break;
  }
  if (dev == (scsi_dev_t *)&xsdd->dev_list_head)
  {
    Srb->SrbStatus = SRB_STATUS_NO_DEVICE;
    ScsiPortNotification(RequestComplete, DeviceExtension, Srb);
    //KdPrint((__DRIVER_NAME "     Out of bounds\n"));
    ScsiPortNotification(NextRequest, DeviceExtension);
    //FUNCTION_EXIT();
    return TRUE;
  }

  switch (Srb->Function)
  {
  case SRB_FUNCTION_EXECUTE_SCSI:
    switch (Srb->Cdb[0])
    {
    case 0x03: { /* REQUEST_SENSE*/
      /* but what about when we allow multiple requests per lu? */
      PXENSCSI_LU_DATA lud = ScsiPortGetLogicalUnit(DeviceExtension, Srb->PathId, Srb->TargetId, Srb->Lun);
      if (lud != NULL && lud->sense_len)
      {
        int i;
        KdPrint((__DRIVER_NAME "     Emulating REQUEST_SENSE (lu data = %p)\n", lud));
        memcpy(Srb->DataBuffer, lud->sense_buffer, min(lud->sense_len, Srb->DataTransferLength));
        if (lud->sense_len > Srb->DataTransferLength)
        {
          KdPrint((__DRIVER_NAME "     Sense overrun Srb->DataTransferLength = %d, lud->sense_len = %d\n", Srb->DataTransferLength, lud->sense_len));
          Srb->DataTransferLength = lud->sense_len;
          Srb->SrbStatus = SRB_STATUS_DATA_OVERRUN;
        }
        else
        {
          Srb->SrbStatus = SRB_STATUS_SUCCESS;
        }
        for (i = 0; i < min(lud->sense_len, 8); i++)
          KdPrint((__DRIVER_NAME "     sense %02x: %02x\n", i, (ULONG)((PUCHAR)lud->sense_buffer)[i]));
        lud->sense_len = 0;
        ScsiPortNotification(RequestComplete, DeviceExtension, Srb);
        ScsiPortNotification(NextRequest, DeviceExtension);
        break;
      }
      else
      {
        KdPrint((__DRIVER_NAME "     Issuing REQUEST_SENSE (lud = %p)\n", lud));
      }
      // fall through
    }
    default:
      XenScsi_PutSrbOnRing(xsdd, Srb);
      Srb->SrbStatus = SRB_STATUS_PENDING;
      break;
    }
    break;
  case SRB_FUNCTION_IO_CONTROL:
    KdPrint((__DRIVER_NAME "     SRB_FUNCTION_IO_CONTROL\n"));
    Srb->SrbStatus = SRB_STATUS_INVALID_REQUEST;
    ScsiPortNotification(RequestComplete, DeviceExtension, Srb);
    ScsiPortNotification(NextRequest, DeviceExtension);
    break;
  case SRB_FUNCTION_FLUSH:
    KdPrint((__DRIVER_NAME "     SRB_FUNCTION_FLUSH\n"));
    Srb->SrbStatus = SRB_STATUS_INVALID_REQUEST;
    ScsiPortNotification(RequestComplete, DeviceExtension, Srb);
    ScsiPortNotification(NextRequest, DeviceExtension);
    break;
  default:
    KdPrint((__DRIVER_NAME "     Unhandled Srb->Function = %08X\n", Srb->Function));
    Srb->SrbStatus = SRB_STATUS_INVALID_REQUEST;
    ScsiPortNotification(RequestComplete, DeviceExtension, Srb);
    ScsiPortNotification(NextRequest, DeviceExtension);
    break;
  }

  //FUNCTION_EXIT();
  return TRUE;
}

static BOOLEAN
XenScsi_HwScsiResetBus(PVOID DeviceExtension, ULONG PathId)
{
  UNREFERENCED_PARAMETER(DeviceExtension);
  UNREFERENCED_PARAMETER(PathId);


  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));
  ScsiPortNotification(NextRequest, DeviceExtension);
  FUNCTION_EXIT();

  return TRUE;
}

static SCSI_ADAPTER_CONTROL_STATUS
XenScsi_HwScsiAdapterControl(PVOID DeviceExtension, SCSI_ADAPTER_CONTROL_TYPE ControlType, PVOID Parameters)
{
  SCSI_ADAPTER_CONTROL_STATUS Status = ScsiAdapterControlSuccess;
  PSCSI_SUPPORTED_CONTROL_TYPE_LIST SupportedControlTypeList;
  //KIRQL OldIrql;

  UNREFERENCED_PARAMETER(DeviceExtension);

  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));

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
    break;
  case ScsiRestartAdapter:
    KdPrint((__DRIVER_NAME "     ScsiRestartAdapter\n"));
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
  ULONG Status;
  HW_INITIALIZATION_DATA HwInitializationData;
  PVOID driver_extension;
  PUCHAR ptr;

  FUNCTION_ENTER();

  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));

  IoAllocateDriverObjectExtension(DriverObject, UlongToPtr(XEN_INIT_DRIVER_EXTENSION_MAGIC), PAGE_SIZE, &driver_extension);
  ptr = driver_extension;
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_RING, "ring-ref", NULL, NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_EVENT_CHANNEL_IRQ, "event-channel", NULL, NULL);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_GRANT_ENTRIES, UlongToPtr((ULONG)'SCSI'), UlongToPtr(144), NULL);
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
  //__ADD_XEN_INIT_UCHAR(&ptr, XenbusStateInitWait); //ialising);
  //__ADD_XEN_INIT_UCHAR(&ptr, XenbusStateInitWait);
  //__ADD_XEN_INIT_UCHAR(&ptr, 50);
  __ADD_XEN_INIT_UCHAR(&ptr, 0);
  ADD_XEN_INIT_REQ(&ptr, XEN_INIT_TYPE_END, NULL, NULL, NULL);
  /* RegistryPath == NULL when we are invoked as a crash dump driver */
  if (!RegistryPath)
  {
    dump_mode = TRUE;
  }

  RtlZeroMemory(&HwInitializationData, sizeof(HW_INITIALIZATION_DATA));

  HwInitializationData.HwInitializationDataSize = sizeof(HW_INITIALIZATION_DATA);
  HwInitializationData.AdapterInterfaceType = PNPBus;
  HwInitializationData.DeviceExtensionSize = sizeof(XENSCSI_DEVICE_DATA);
  HwInitializationData.SpecificLuExtensionSize = sizeof(XENSCSI_LU_DATA);
  HwInitializationData.SrbExtensionSize = 0;
  HwInitializationData.NumberOfAccessRanges = 1;
  HwInitializationData.MapBuffers = TRUE;
  HwInitializationData.NeedPhysicalAddresses = FALSE;
  HwInitializationData.TaggedQueuing = TRUE;
  HwInitializationData.AutoRequestSense = TRUE;
  HwInitializationData.MultipleRequestPerLu = TRUE;

  HwInitializationData.HwInitialize = XenScsi_HwScsiInitialize;
  HwInitializationData.HwStartIo = XenScsi_HwScsiStartIo;
  HwInitializationData.HwInterrupt = XenScsi_HwScsiInterrupt;
  HwInitializationData.HwFindAdapter = XenScsi_HwScsiFindAdapter;
  HwInitializationData.HwResetBus = XenScsi_HwScsiResetBus;
  HwInitializationData.HwAdapterControl = XenScsi_HwScsiAdapterControl;

  Status = ScsiPortInitialize(DriverObject, RegistryPath, &HwInitializationData, NULL);
  
  if(!NT_SUCCESS(Status))
  {
    KdPrint((__DRIVER_NAME " ScsiPortInitialize failed with status 0x%08x\n", Status));
  }

  FUNCTION_EXIT();

  return Status;
}
