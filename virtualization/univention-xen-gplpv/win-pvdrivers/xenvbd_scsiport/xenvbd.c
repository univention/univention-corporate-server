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

#include "xenvbd.h"

#pragma warning(disable: 4127)

/* Not really necessary but keeps PREfast happy */
DRIVER_INITIALIZE DriverEntry;
static IO_WORKITEM_ROUTINE XenVbd_DisconnectWorkItem;

static VOID XenVbd_ProcessSrbList(PXENVBD_DEVICE_DATA xvdd);
static BOOLEAN XenVbd_ResetBus(PXENVBD_DEVICE_DATA xvdd, ULONG PathId);
static VOID XenVbd_CompleteDisconnect(PXENVBD_DEVICE_DATA xvdd);

static BOOLEAN dump_mode = FALSE;
#define DUMP_MODE_ERROR_LIMIT 64
static ULONG dump_mode_errors = 0;

#define StorPortAcquireSpinLock(...) {}
#define StorPortReleaseSpinLock(...) {}

static ULONG
SxxxPortGetSystemAddress(PVOID device_extension, PSCSI_REQUEST_BLOCK srb, PVOID *system_address) {
  UNREFERENCED_PARAMETER(device_extension);
  *system_address = (PUCHAR)srb->DataBuffer;
  return STATUS_SUCCESS;
}

static PHYSICAL_ADDRESS
SxxxPortGetPhysicalAddress(PVOID device_extension, PSCSI_REQUEST_BLOCK srb, PVOID virtual_address, ULONG *length) {
  UNREFERENCED_PARAMETER(device_extension);
  UNREFERENCED_PARAMETER(srb);
  UNREFERENCED_PARAMETER(length);
  return MmGetPhysicalAddress(virtual_address);
}

#define SxxxPortNotification(NotificationType, DeviceExtension, ...) XenVbd_Notification##NotificationType(DeviceExtension, __VA_ARGS__)

static VOID
XenVbd_NotificationRequestComplete(PXENVBD_DEVICE_DATA xvdd, PSCSI_REQUEST_BLOCK srb) {
  PXENVBD_SCSIPORT_DATA xvsd = (PXENVBD_SCSIPORT_DATA)xvdd->xvsd;
  srb_list_entry_t *srb_entry = srb->SrbExtension;
  if (srb_entry->outstanding_requests != 0) {
    FUNCTION_MSG("srb outstanding_requests = %d\n", srb_entry->outstanding_requests);
  }
  xvsd->outstanding--;
  ScsiPortNotification(RequestComplete, xvsd, srb);
}

VOID
XenVbd_NotificationNextLuRequest(PXENVBD_DEVICE_DATA xvdd, UCHAR PathId, UCHAR TargetId, UCHAR Lun) {
  ScsiPortNotification(NextLuRequest, xvdd->xvsd, PathId, TargetId, Lun);
}

VOID
XenVbd_NotificationNextRequest(PXENVBD_DEVICE_DATA xvdd) {
  ScsiPortNotification(NextRequest, xvdd->xvsd);
}


VOID
XenVbd_NotificationBusChangeDetected(PXENVBD_DEVICE_DATA xvdd, UCHAR PathId) {
  ScsiPortNotification(BusChangeDetected, xvdd->xvsd, PathId);
}

#include "..\xenvbd_common\common_miniport.h"


/* called in non-dump & dump mode */
static ULONG
XenVbd_HwScsiFindAdapter(PVOID DeviceExtension, PVOID HwContext, PVOID BusInformation, PCHAR ArgumentString, PPORT_CONFIGURATION_INFORMATION ConfigInfo, PBOOLEAN Again) {
  PXENVBD_SCSIPORT_DATA xvsd = (PXENVBD_SCSIPORT_DATA)DeviceExtension;
  PXENVBD_DEVICE_DATA xvdd;
  PACCESS_RANGE access_range;

  UNREFERENCED_PARAMETER(HwContext);
  UNREFERENCED_PARAMETER(BusInformation);
  UNREFERENCED_PARAMETER(ArgumentString);

  FUNCTION_ENTER(); 
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
  FUNCTION_MSG("xvsd = %p\n", xvsd);

  if (ConfigInfo->NumberOfAccessRanges != 1) {
    FUNCTION_MSG("NumberOfAccessRanges wrong\n");
    FUNCTION_EXIT();
    return SP_RETURN_BAD_CONFIG;
  }
  if (XnGetVersion() != 1) {
    FUNCTION_MSG("Wrong XnGetVersion\n");
    FUNCTION_EXIT();
    return SP_RETURN_BAD_CONFIG;
  }
  RtlZeroMemory(xvsd, FIELD_OFFSET(XENVBD_SCSIPORT_DATA, aligned_buffer_data));

  access_range = &((*(ConfigInfo->AccessRanges))[0]);

  if (!dump_mode) {
    xvdd = (PXENVBD_DEVICE_DATA)(ULONG_PTR)access_range->RangeStart.QuadPart;
    xvsd->xvdd = xvdd;
    xvdd->xvsd = xvsd;
    xvdd->aligned_buffer = (PVOID)((ULONG_PTR)((PUCHAR)xvsd->aligned_buffer_data + PAGE_SIZE - 1) & ~(PAGE_SIZE - 1));
    /* save hypercall_stubs for crash dump */
    xvsd->hypercall_stubs = XnGetHypercallStubs();
  } else {
    /* make a copy of xvdd and use that copy */
    xvdd = (PXENVBD_DEVICE_DATA)xvsd->aligned_buffer_data;
    memcpy(xvdd, (PVOID)(ULONG_PTR)access_range->RangeStart.QuadPart, sizeof(XENVBD_DEVICE_DATA));
    /* make sure original xvdd is set to DISCONNECTED or resume will not work */
    ((PXENVBD_DEVICE_DATA)(ULONG_PTR)access_range->RangeStart.QuadPart)->device_state = DEVICE_STATE_DISCONNECTED;
    xvsd->xvdd = xvdd;
    xvdd->xvsd = xvsd;
    xvdd->aligned_buffer = (PVOID)((ULONG_PTR)((PUCHAR)xvsd->aligned_buffer_data + sizeof(XENVBD_DEVICE_DATA) + PAGE_SIZE - 1) & ~(PAGE_SIZE - 1));
    /* restore hypercall_stubs into dump_xenpci */
    XnSetHypercallStubs(xvsd->hypercall_stubs);
    if (xvsd->xvdd->device_state != DEVICE_STATE_ACTIVE) {
      /* if we are not connected to the ring when we start dump mode then there is nothing we can do */
      FUNCTION_MSG("Cannot connect backend in dump mode - state = %d\n", xvsd->xvdd->device_state);
      return SP_RETURN_ERROR;
    }
  }
  FUNCTION_MSG("aligned_buffer_data = %p\n", xvsd->aligned_buffer_data);
  FUNCTION_MSG("aligned_buffer = %p\n", xvdd->aligned_buffer);

  InitializeListHead(&xvdd->srb_list);
  xvdd->aligned_buffer_in_use = FALSE;
  /* align the buffer to PAGE_SIZE */

  ConfigInfo->MaximumTransferLength = 4 * 1024 * 1024; //BLKIF_MAX_SEGMENTS_PER_REQUEST * PAGE_SIZE;
  ConfigInfo->NumberOfPhysicalBreaks = ConfigInfo->MaximumTransferLength >> PAGE_SHIFT; //BLKIF_MAX_SEGMENTS_PER_REQUEST - 1;
  FUNCTION_MSG("ConfigInfo->MaximumTransferLength = %d\n", ConfigInfo->MaximumTransferLength);
  FUNCTION_MSG("ConfigInfo->NumberOfPhysicalBreaks = %d\n", ConfigInfo->NumberOfPhysicalBreaks);
  if (!dump_mode) {
    xvdd->aligned_buffer_size = BLKIF_MAX_SEGMENTS_PER_REQUEST * PAGE_SIZE;
  } else {
    xvdd->aligned_buffer_size = DUMP_MODE_UNALIGNED_PAGES * PAGE_SIZE;
  }

  FUNCTION_MSG("MultipleRequestPerLu = %d\n", ConfigInfo->MultipleRequestPerLu);
  FUNCTION_MSG("TaggedQueuing = %d\n", ConfigInfo->TaggedQueuing);
  FUNCTION_MSG("AutoRequestSense  = %d\n", ConfigInfo->AutoRequestSense);
  ConfigInfo->CachesData = FALSE;
  ConfigInfo->MapBuffers = TRUE;
  ConfigInfo->AlignmentMask = 0;
  ConfigInfo->NumberOfBuses = 1;
  ConfigInfo->InitiatorBusId[0] = 1;
  ConfigInfo->MaximumNumberOfLogicalUnits = 1;
  ConfigInfo->MaximumNumberOfTargets = 2;
  FUNCTION_MSG("MapBuffers = %d\n", ConfigInfo->MapBuffers);
  FUNCTION_MSG("NeedPhysicalAddresses = %d\n", ConfigInfo->NeedPhysicalAddresses);
  if (ConfigInfo->Dma64BitAddresses == SCSI_DMA64_SYSTEM_SUPPORTED) {
    FUNCTION_MSG("Dma64BitAddresses supported\n");
    ConfigInfo->Dma64BitAddresses = SCSI_DMA64_MINIPORT_SUPPORTED;
    ConfigInfo->ScatterGather = TRUE;
    ConfigInfo->Master = TRUE;
  } else {
    FUNCTION_MSG("Dma64BitAddresses not supported\n");
    ConfigInfo->ScatterGather = FALSE;
    ConfigInfo->Master = FALSE;
  }
  *Again = FALSE;

  FUNCTION_EXIT();

  return SP_RETURN_FOUND;
}

/* Called at PASSIVE_LEVEL for non-dump mode */
static BOOLEAN
XenVbd_HwScsiInitialize(PVOID DeviceExtension) {
  PXENVBD_SCSIPORT_DATA xvsd = (PXENVBD_SCSIPORT_DATA)DeviceExtension;
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)xvsd->xvdd;
  ULONG i;
  
  FUNCTION_ENTER();
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
  FUNCTION_MSG("dump_mode = %d\n", dump_mode);
  
  xvdd->shadow_free = 0;
  memset(xvdd->shadows, 0, sizeof(blkif_shadow_t) * SHADOW_ENTRIES);
  for (i = 0; i < SHADOW_ENTRIES; i++) {
    xvdd->shadows[i].req.id = i;
    /* make sure leftover real requests's are never confused with dump mode requests */
    if (dump_mode)
      xvdd->shadows[i].req.id |= SHADOW_ID_DUMP_FLAG;
    put_shadow_on_freelist(xvdd, &xvdd->shadows[i]);
  }

  if (!dump_mode) {
    /* nothing */
  } else {
    xvdd->grant_tag = (ULONG)'DUMP';
  }
  
  FUNCTION_EXIT();

  return TRUE;
}

/* this is only used during hiber and dump */
static BOOLEAN
XenVbd_HwScsiInterrupt(PVOID DeviceExtension)
{
  PXENVBD_SCSIPORT_DATA xvsd = DeviceExtension;
  XenVbd_HandleEvent(xvsd->xvdd);
  //SxxxPortNotification(NextLuRequest, xvdd, 0, 0, 0);
  return TRUE;
}

static BOOLEAN
XenVbd_HwScsiResetBus(PVOID DeviceExtension, ULONG PathId)
{
  PXENVBD_SCSIPORT_DATA xvsd = DeviceExtension;
  return XenVbd_ResetBus(xvsd->xvdd, PathId);
}

static VOID
XenVbd_CompleteDisconnect(PXENVBD_DEVICE_DATA xvdd) {
  PXENVBD_SCSIPORT_DATA xvsd = (PXENVBD_SCSIPORT_DATA)xvdd->xvsd;
  PSCSI_REQUEST_BLOCK srb;
  
  if (xvsd->stop_srb) {
    srb = xvsd->stop_srb;
    xvsd->stop_srb = NULL;
    ScsiPortNotification(RequestComplete, xvsd, srb);
  }
}

static VOID
XenVbd_HwScsiTimer(PVOID DeviceExtension) {
  PXENVBD_SCSIPORT_DATA xvsd = DeviceExtension;
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)xvsd->xvdd;

  //FUNCTION_MSG("HwScsiTimer\n");
  XenVbd_HandleEvent(xvdd);
  if (xvsd->outstanding) {
    ScsiPortNotification(RequestTimerCall, xvsd, XenVbd_HwScsiTimer, 100000);
  } else {
    ScsiPortNotification(RequestTimerCall, xvsd, XenVbd_HwScsiTimer, 0);
  }
}

static BOOLEAN
XenVbd_HwScsiStartIo(PVOID DeviceExtension, PSCSI_REQUEST_BLOCK srb) {
  PXENVBD_SCSIPORT_DATA xvsd = DeviceExtension;
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)xvsd->xvdd;
  PSRB_IO_CONTROL sic;

  if ((LONG)xvsd->outstanding < 0) {
    FUNCTION_MSG("HwScsiStartIo outstanding = %d\n", xvsd->outstanding);
  }
  if (srb->PathId != 0 || srb->TargetId != 0 || srb->Lun != 0) {
    FUNCTION_MSG("HwScsiStartIo (Out of bounds - PathId = %d, TargetId = %d, Lun = %d)\n", srb->PathId, srb->TargetId, srb->Lun);
    srb->SrbStatus = SRB_STATUS_NO_DEVICE;
    ScsiPortNotification(RequestComplete, xvsd, srb);
  } else if (srb->Function == SRB_FUNCTION_IO_CONTROL && memcmp(((PSRB_IO_CONTROL)srb->DataBuffer)->Signature, XENVBD_CONTROL_SIG, 8) == 0) {
    sic = srb->DataBuffer;
    switch(sic->ControlCode) {
    case XENVBD_CONTROL_EVENT:
      srb->SrbStatus = SRB_STATUS_SUCCESS;
      ScsiPortNotification(RequestComplete, xvsd, srb);
      break;
    case XENVBD_CONTROL_STOP:
      if (xvdd->shadow_free == SHADOW_ENTRIES) {
        srb->SrbStatus = SRB_STATUS_SUCCESS;
        ScsiPortNotification(RequestComplete, xvsd, srb);
        FUNCTION_MSG("CONTROL_STOP done\n");
      } else {
        xvsd->stop_srb = srb;
        FUNCTION_MSG("CONTROL_STOP pended\n");
      }
      break;
    case XENVBD_CONTROL_START:
      // we might need to reload a few things here...
      ScsiPortNotification(RequestComplete, xvsd, srb);
      break;
    default:
      FUNCTION_MSG("XENVBD_CONTROL_%d\n", sic->ControlCode);
      srb->SrbStatus = SRB_STATUS_ERROR;
      ScsiPortNotification(RequestComplete, xvsd, srb);
      break;
    }
  } else if (xvdd->device_state == DEVICE_STATE_INACTIVE) {
    FUNCTION_MSG("HwScsiStartIo Inactive Device (in StartIo)\n");
    srb->SrbStatus = SRB_STATUS_NO_DEVICE;
    ScsiPortNotification(RequestComplete, xvsd, srb);
  } else {
    xvsd->outstanding++;
    XenVbd_PutSrbOnList(xvdd, srb);
  }
  /* HandleEvent also puts queued SRB's on the ring */
  XenVbd_HandleEvent(xvdd);
  /* need 2 spare slots - 1 for EVENT and 1 for STOP/START */
  if (xvsd->outstanding < 30) {
    ScsiPortNotification(NextLuRequest, xvsd, 0, 0, 0);
  } else {
    ScsiPortNotification(NextRequest, xvsd);
  }
  /* if there was an error returned by an SRB then the queue will freeze. Queue a timer to resolve this */
  if (xvsd->outstanding) {
    ScsiPortNotification(RequestTimerCall, xvsd, XenVbd_HwScsiTimer, 100000);
  } else {
    ScsiPortNotification(RequestTimerCall, xvsd, XenVbd_HwScsiTimer, 0);
  }
  return TRUE;
}

static SCSI_ADAPTER_CONTROL_STATUS
XenVbd_HwScsiAdapterControl(PVOID DeviceExtension, SCSI_ADAPTER_CONTROL_TYPE ControlType, PVOID Parameters) {
  PXENVBD_SCSIPORT_DATA xvsd = DeviceExtension;
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)xvsd->xvdd;
  SCSI_ADAPTER_CONTROL_STATUS Status = ScsiAdapterControlSuccess;
  PSCSI_SUPPORTED_CONTROL_TYPE_LIST SupportedControlTypeList;

  FUNCTION_ENTER();
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
  FUNCTION_MSG("xvsd = %p\n", xvsd);

  switch (ControlType) {
  case ScsiQuerySupportedControlTypes:
    SupportedControlTypeList = (PSCSI_SUPPORTED_CONTROL_TYPE_LIST)Parameters;
    FUNCTION_MSG("ScsiQuerySupportedControlTypes (Max = %d)\n", SupportedControlTypeList->MaxControlType);
    SupportedControlTypeList->SupportedTypeList[ScsiQuerySupportedControlTypes] = TRUE;
    SupportedControlTypeList->SupportedTypeList[ScsiStopAdapter] = TRUE;
    SupportedControlTypeList->SupportedTypeList[ScsiRestartAdapter] = TRUE;
    break;
  case ScsiStopAdapter:
    FUNCTION_MSG("ScsiStopAdapter\n");
    if (xvdd->device_state == DEVICE_STATE_INACTIVE) {
      FUNCTION_MSG("inactive - nothing to do\n");
      break;
    }
    XN_ASSERT(IsListEmpty(&xvdd->srb_list));
    XN_ASSERT(xvdd->shadow_free == SHADOW_ENTRIES);
    break;
  case ScsiRestartAdapter:
    FUNCTION_MSG("ScsiRestartAdapter\n");
    if (xvdd->device_state == DEVICE_STATE_INACTIVE) {
      FUNCTION_MSG("inactive - nothing to do\n");
      break;
    }
    /* increase the tag every time we stop/start to track where the gref's came from */
    xvdd->grant_tag++;
    break;
  case ScsiSetBootConfig:
    FUNCTION_MSG("ScsiSetBootConfig\n");
    break;
  case ScsiSetRunningConfig:
    FUNCTION_MSG("ScsiSetRunningConfig\n");
    break;
  default:
    FUNCTION_MSG("UNKNOWN\n");
    break;
  }

  FUNCTION_EXIT();
  
  return Status;
}

NTSTATUS
DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath) {
  ULONG status;
  HW_INITIALIZATION_DATA HwInitializationData;
  
  /* RegistryPath == NULL when we are invoked as a crash dump driver */
  if (!RegistryPath) {
    dump_mode = TRUE;
    XnPrintDump();
  }

  FUNCTION_ENTER();
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
  FUNCTION_MSG("DriverObject = %p, RegistryPath = %p\n", DriverObject, RegistryPath);
  
  RtlZeroMemory(&HwInitializationData, sizeof(HW_INITIALIZATION_DATA));
  HwInitializationData.HwInitializationDataSize = sizeof(HW_INITIALIZATION_DATA);
  HwInitializationData.AdapterInterfaceType = PNPBus; /* not Internal */
  HwInitializationData.SrbExtensionSize = sizeof(srb_list_entry_t);
  HwInitializationData.NumberOfAccessRanges = 1;
  HwInitializationData.MapBuffers = TRUE;
  HwInitializationData.NeedPhysicalAddresses  = FALSE;
  HwInitializationData.TaggedQueuing = TRUE;
  HwInitializationData.AutoRequestSense = TRUE;
  HwInitializationData.MultipleRequestPerLu = TRUE;
  HwInitializationData.ReceiveEvent = FALSE;
  HwInitializationData.HwInitialize = XenVbd_HwScsiInitialize;
  HwInitializationData.HwStartIo = XenVbd_HwScsiStartIo;
  HwInitializationData.HwFindAdapter = XenVbd_HwScsiFindAdapter;
  HwInitializationData.HwResetBus = XenVbd_HwScsiResetBus;
  HwInitializationData.HwAdapterControl = XenVbd_HwScsiAdapterControl;
  if (!dump_mode) {
    HwInitializationData.DeviceExtensionSize = FIELD_OFFSET(XENVBD_SCSIPORT_DATA, aligned_buffer_data) + UNALIGNED_BUFFER_DATA_SIZE;
  } else {
    HwInitializationData.HwInterrupt = XenVbd_HwScsiInterrupt;
    HwInitializationData.DeviceExtensionSize = FIELD_OFFSET(XENVBD_SCSIPORT_DATA, aligned_buffer_data) + sizeof(XENVBD_DEVICE_DATA) + UNALIGNED_BUFFER_DATA_SIZE_DUMP_MODE;
  }
  status = ScsiPortInitialize(DriverObject, RegistryPath, &HwInitializationData, NULL);
  
  if(!NT_SUCCESS(status)) {
    FUNCTION_MSG("ScsiPortInitialize failed with status 0x%08x\n", status);
  }

  FUNCTION_EXIT();

  return status;
}
