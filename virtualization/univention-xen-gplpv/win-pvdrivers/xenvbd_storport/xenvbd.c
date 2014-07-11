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
static IO_WORKITEM_ROUTINE XenVbd_ConnectWorkItem;

static VOID XenVbd_HandleEventDpc(PSTOR_DPC dpc, PVOID DeviceExtension, PVOID arg1, PVOID arg2);
static VOID XenVbd_HandleEventDIRQL(PVOID DeviceExtension);
static VOID XenVbd_ProcessSrbList(PXENVBD_DEVICE_DATA xvdd);
static VOID XenVbd_DeviceCallback(PVOID context, ULONG callback_type, PVOID value);
static VOID XenVbd_StopRing(PXENVBD_DEVICE_DATA xvdd, BOOLEAN suspend);
static VOID XenVbd_StartRing(PXENVBD_DEVICE_DATA xvdd, BOOLEAN suspend);
static VOID XenVbd_CompleteDisconnect(PXENVBD_DEVICE_DATA xvdd);

#define SxxxPortNotification(...) StorPortNotification(__VA_ARGS__)
#define SxxxPortGetSystemAddress(xvdd, srb, system_address) StorPortGetSystemAddress(xvdd, srb, system_address)
#define SxxxPortGetPhysicalAddress(xvdd, srb, virtual_address, length) StorPortGetPhysicalAddress(xvdd, srb, virtual_address, length)

static BOOLEAN dump_mode = FALSE;
#define DUMP_MODE_ERROR_LIMIT 64
static ULONG dump_mode_errors = 0;

#include "..\xenvbd_common\common_miniport.h"
#include "..\xenvbd_common\common_xen.h"

static VOID
XenVbd_StopRing(PXENVBD_DEVICE_DATA xvdd, BOOLEAN suspend) {
  NTSTATUS status;
  STOR_LOCK_HANDLE lock_handle;

  UNREFERENCED_PARAMETER(suspend);

  StorPortAcquireSpinLock(xvdd, StartIoLock, NULL, &lock_handle);
  xvdd->device_state = DEVICE_STATE_DISCONNECTING;
  if (xvdd->shadow_free == SHADOW_ENTRIES) {
    FUNCTION_MSG("Ring already empty\n");
    /* nothing on the ring - okay to disconnect now */
    StorPortReleaseSpinLock(xvdd, &lock_handle);
    status = XnWriteInt32(xvdd->handle, XN_BASE_FRONTEND, "state", XenbusStateClosing);
  } else {
    FUNCTION_MSG("Ring not empty - shadow_free = %d\n", xvdd->shadow_free);
    /* ring is busy. workitem will set XenbusStateClosing when its empty */
    StorPortReleaseSpinLock(xvdd, &lock_handle);
  }
}

static VOID
XenVbd_StartRing(PXENVBD_DEVICE_DATA xvdd, BOOLEAN suspend) {
  STOR_LOCK_HANDLE lock_handle;

  UNREFERENCED_PARAMETER(suspend);

  StorPortAcquireSpinLock(xvdd, StartIoLock, NULL, &lock_handle);
  XenVbd_ProcessSrbList(xvdd);
  StorPortReleaseSpinLock(xvdd, &lock_handle);
}

static VOID
XenVbd_DisconnectWorkItem(PDEVICE_OBJECT device_object, PVOID context) {
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)context;
  ULONG status;
  
  UNREFERENCED_PARAMETER(device_object);
  FUNCTION_ENTER();
  status = XnWriteInt32(xvdd->handle, XN_BASE_FRONTEND, "state", XenbusStateClosing);
  FUNCTION_EXIT();
}

static VOID
XenVbd_ConnectWorkItem(PDEVICE_OBJECT device_object, PVOID context) {
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)context;

  UNREFERENCED_PARAMETER(device_object);
  FUNCTION_ENTER();
  XenVbd_Connect(xvdd, TRUE);
  FUNCTION_EXIT();
}

static VOID
XenVbd_CompleteDisconnect(PXENVBD_DEVICE_DATA xvdd) {
  IoQueueWorkItem(xvdd->disconnect_workitem, XenVbd_DisconnectWorkItem, DelayedWorkQueue, xvdd);
}

/* called in non-dump mode */
static ULONG
XenVbd_VirtualHwStorFindAdapter(PVOID DeviceExtension, PVOID HwContext, PVOID BusInformation, PVOID LowerDevice, PCHAR ArgumentString, PPORT_CONFIGURATION_INFORMATION ConfigInfo, PBOOLEAN Again)
{
  NTSTATUS status;
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)DeviceExtension;

  //UNREFERENCED_PARAMETER(HwContext);
  UNREFERENCED_PARAMETER(BusInformation);
  UNREFERENCED_PARAMETER(LowerDevice);
  UNREFERENCED_PARAMETER(ArgumentString);

  FUNCTION_ENTER(); 
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
  FUNCTION_MSG("xvdd = %p\n", xvdd);

  if (XnGetVersion() != 1) {
    FUNCTION_MSG("Wrong XnGetVersion\n");
    FUNCTION_EXIT();
    return SP_RETURN_BAD_CONFIG;
  }

  RtlZeroMemory(xvdd, sizeof(XENVBD_DEVICE_DATA));
  InitializeListHead(&xvdd->srb_list);
  KeInitializeEvent(&xvdd->device_state_event, SynchronizationEvent, FALSE);
  KeInitializeEvent(&xvdd->backend_event, SynchronizationEvent, FALSE);
  xvdd->pdo = (PDEVICE_OBJECT)HwContext; // TODO: maybe should get PDO from FDO below? HwContext isn't really documented
  xvdd->fdo = (PDEVICE_OBJECT)BusInformation;
  xvdd->disconnect_workitem = IoAllocateWorkItem(xvdd->fdo);
  xvdd->connect_workitem = IoAllocateWorkItem(xvdd->fdo);
  xvdd->aligned_buffer_in_use = FALSE;
  /* align the buffer to PAGE_SIZE */
  xvdd->aligned_buffer = (PVOID)((ULONG_PTR)((PUCHAR)xvdd->aligned_buffer_data + PAGE_SIZE - 1) & ~(PAGE_SIZE - 1));
  FUNCTION_MSG("aligned_buffer_data = %p\n", xvdd->aligned_buffer_data);
  FUNCTION_MSG("aligned_buffer = %p\n", xvdd->aligned_buffer);

  StorPortInitializeDpc(DeviceExtension, &xvdd->dpc, XenVbd_HandleEventDpc);
  xvdd->grant_tag = (ULONG)'XVBD';

  /* save hypercall_stubs for crash dump */
  xvdd->hypercall_stubs = XnGetHypercallStubs();

  ConfigInfo->MaximumTransferLength = 4 * 1024 * 1024; //BLKIF_MAX_SEGMENTS_PER_REQUEST * PAGE_SIZE;
  ConfigInfo->NumberOfPhysicalBreaks = ConfigInfo->MaximumTransferLength >> PAGE_SHIFT; //BLKIF_MAX_SEGMENTS_PER_REQUEST - 1;
  FUNCTION_MSG("ConfigInfo->MaximumTransferLength = %d\n", ConfigInfo->MaximumTransferLength);
  FUNCTION_MSG("ConfigInfo->NumberOfPhysicalBreaks = %d\n", ConfigInfo->NumberOfPhysicalBreaks);
  ConfigInfo->VirtualDevice = TRUE;
  xvdd->aligned_buffer_size = BLKIF_MAX_SEGMENTS_PER_REQUEST * PAGE_SIZE;
  status = XenVbd_Connect(DeviceExtension, FALSE);
 
  FUNCTION_MSG("ConfigInfo->VirtualDevice = %d\n", ConfigInfo->VirtualDevice);
  ConfigInfo->ScatterGather = TRUE;
  ConfigInfo->Master = TRUE;
  ConfigInfo->CachesData = FALSE;
  ConfigInfo->MapBuffers = STOR_MAP_ALL_BUFFERS;
  FUNCTION_MSG("ConfigInfo->NeedPhysicalAddresses = %d\n", ConfigInfo->NeedPhysicalAddresses);
  ConfigInfo->SynchronizationModel = StorSynchronizeFullDuplex;
  ConfigInfo->AlignmentMask = 0;
  ConfigInfo->NumberOfBuses = 1;
  ConfigInfo->InitiatorBusId[0] = 1;
  ConfigInfo->MaximumNumberOfLogicalUnits = 1;
  ConfigInfo->MaximumNumberOfTargets = 2;
  if (ConfigInfo->Dma64BitAddresses == SCSI_DMA64_SYSTEM_SUPPORTED) {
    ConfigInfo->Dma64BitAddresses = SCSI_DMA64_MINIPORT_SUPPORTED;
    FUNCTION_MSG("Dma64BitAddresses supported\n");
  } else {
    FUNCTION_MSG("Dma64BitAddresses not supported\n");
  }
  *Again = FALSE;

  FUNCTION_EXIT();

  return SP_RETURN_FOUND;
}

/* called in dump mode */
static ULONG
XenVbd_HwStorFindAdapter(PVOID DeviceExtension, PVOID HwContext, PVOID BusInformation, PCHAR ArgumentString, PPORT_CONFIGURATION_INFORMATION ConfigInfo, PBOOLEAN Again)
{
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)DeviceExtension;

  UNREFERENCED_PARAMETER(HwContext);
  UNREFERENCED_PARAMETER(BusInformation);
  UNREFERENCED_PARAMETER(ArgumentString);
  
  FUNCTION_ENTER();
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
  FUNCTION_MSG("xvdd = %p\n", xvdd);
  FUNCTION_MSG("ArgumentString = %s\n", ArgumentString);

  memcpy(xvdd, ConfigInfo->Reserved, FIELD_OFFSET(XENVBD_DEVICE_DATA, aligned_buffer_data));
  if (xvdd->device_state != DEVICE_STATE_ACTIVE) {
    return SP_RETURN_ERROR;
  }
  /* restore hypercall_stubs into dump_xenpci */
  XnSetHypercallStubs(xvdd->hypercall_stubs);
  /* make sure original xvdd is set to DISCONNECTED or resume will not work */
  ((PXENVBD_DEVICE_DATA)ConfigInfo->Reserved)->device_state = DEVICE_STATE_DISCONNECTED;
  InitializeListHead(&xvdd->srb_list);
  xvdd->aligned_buffer_in_use = FALSE;
  /* align the buffer to PAGE_SIZE */
  xvdd->aligned_buffer = (PVOID)((ULONG_PTR)((PUCHAR)xvdd->aligned_buffer_data + PAGE_SIZE - 1) & ~(PAGE_SIZE - 1));
  xvdd->aligned_buffer_size = DUMP_MODE_UNALIGNED_PAGES * PAGE_SIZE;
  xvdd->grant_tag = (ULONG)'DUMP';
  FUNCTION_MSG("aligned_buffer_data = %p\n", xvdd->aligned_buffer_data);
  FUNCTION_MSG("aligned_buffer = %p\n", xvdd->aligned_buffer);

  ConfigInfo->MaximumTransferLength = 4 * 1024 * 1024;
  ConfigInfo->NumberOfPhysicalBreaks = ConfigInfo->MaximumTransferLength >> PAGE_SHIFT;
  FUNCTION_MSG("ConfigInfo->MaximumTransferLength = %d\n", ConfigInfo->MaximumTransferLength);
  FUNCTION_MSG("ConfigInfo->NumberOfPhysicalBreaks = %d\n", ConfigInfo->NumberOfPhysicalBreaks);
  ConfigInfo->VirtualDevice = FALSE;
  ConfigInfo->ScatterGather = TRUE;
  ConfigInfo->Master = TRUE;
  ConfigInfo->CachesData = FALSE;
  ConfigInfo->MapBuffers = STOR_MAP_NON_READ_WRITE_BUFFERS;
  ConfigInfo->SynchronizationModel = StorSynchronizeFullDuplex;
  ConfigInfo->AlignmentMask = 0;
  ConfigInfo->NumberOfBuses = 1;
  ConfigInfo->InitiatorBusId[0] = 1;
  ConfigInfo->MaximumNumberOfLogicalUnits = 1;
  ConfigInfo->MaximumNumberOfTargets = 2;
  ConfigInfo->VirtualDevice = FALSE;
  if (ConfigInfo->Dma64BitAddresses == SCSI_DMA64_SYSTEM_SUPPORTED) {
    ConfigInfo->Dma64BitAddresses = SCSI_DMA64_MINIPORT_SUPPORTED;
    FUNCTION_MSG("Dma64BitAddresses supported\n");
  } else {
    FUNCTION_MSG("Dma64BitAddresses not supported\n");
  }
  *Again = FALSE;

  FUNCTION_EXIT();

  return SP_RETURN_FOUND;
}

/* Called at PASSIVE_LEVEL for non-dump mode */
static BOOLEAN
XenVbd_HwStorInitialize(PVOID DeviceExtension)
{
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)DeviceExtension;
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

  FUNCTION_EXIT();

  return TRUE;
}

static VOID
XenVbd_HandleEventDpc(PSTOR_DPC dpc, PVOID DeviceExtension, PVOID arg1, PVOID arg2) {
  STOR_LOCK_HANDLE lock_handle;
  UNREFERENCED_PARAMETER(dpc);
  UNREFERENCED_PARAMETER(arg1);
  UNREFERENCED_PARAMETER(arg2);
  
  StorPortAcquireSpinLock(DeviceExtension, StartIoLock, NULL, &lock_handle);
  XenVbd_HandleEvent(DeviceExtension);
  StorPortReleaseSpinLock(DeviceExtension, &lock_handle);
}

static VOID
XenVbd_HandleEventDIRQL(PVOID DeviceExtension) {
  PXENVBD_DEVICE_DATA xvdd = DeviceExtension;
  //if (dump_mode) FUNCTION_ENTER();
  StorPortIssueDpc(DeviceExtension, &xvdd->dpc, NULL, NULL);
  //if (dump_mode) FUNCTION_EXIT();
  return;
}

/* this is only used during hiber and dump */
static BOOLEAN
XenVbd_HwStorInterrupt(PVOID DeviceExtension)
{
  //FUNCTION_ENTER();
  XenVbd_HandleEvent(DeviceExtension);
  //FUNCTION_EXIT();
  return TRUE;
}

static BOOLEAN
XenVbd_HwStorResetBus(PVOID DeviceExtension, ULONG PathId)
{
  PXENVBD_DEVICE_DATA xvdd = DeviceExtension;
  return XenVbd_ResetBus(xvdd, PathId);
}

static BOOLEAN
XenVbd_HwStorStartIo(PVOID DeviceExtension, PSCSI_REQUEST_BLOCK srb)
{
  PXENVBD_DEVICE_DATA xvdd = DeviceExtension;
  STOR_LOCK_HANDLE lock_handle;

  //if (dump_mode) FUNCTION_ENTER();
  //if (dump_mode) FUNCTION_MSG("srb = %p\n", srb);
  
  StorPortAcquireSpinLock(DeviceExtension, StartIoLock, NULL, &lock_handle);
  
  if (xvdd->device_state == DEVICE_STATE_INACTIVE) {
    FUNCTION_MSG("HwStorStartIo Inactive Device (in StartIo)\n");
    srb->SrbStatus = SRB_STATUS_NO_DEVICE;
    StorPortNotification(RequestComplete, DeviceExtension, srb);
    StorPortReleaseSpinLock (DeviceExtension, &lock_handle);
    return TRUE;
  }

  if (srb->PathId != 0 || srb->TargetId != 0 || srb->Lun != 0)
  {
    FUNCTION_MSG("HwStorStartIo (Out of bounds - PathId = %d, TargetId = %d, Lun = %d)\n", srb->PathId, srb->TargetId, srb->Lun);
    srb->SrbStatus = SRB_STATUS_NO_DEVICE;
    StorPortNotification(RequestComplete, DeviceExtension, srb);
    StorPortReleaseSpinLock (DeviceExtension, &lock_handle);
    return TRUE;
  }
  XenVbd_PutSrbOnList(xvdd, srb);

  /* HandleEvent also puts queued SRB's on the ring */
  XenVbd_HandleEvent(xvdd);
  StorPortReleaseSpinLock (DeviceExtension, &lock_handle);
  //if (dump_mode) FUNCTION_EXIT();
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
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
  FUNCTION_MSG("ControlType = %d\n", ControlType);

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
    if (xvdd->power_action != StorPowerActionHibernate) {
      /* if hibernate then device_state will be set on our behalf in the hibernate FindAdapter */
      xvdd->device_state = DEVICE_STATE_DISCONNECTED;
      //XenVbd_Disconnect(??);
    }
    break;
  case ScsiRestartAdapter:
    FUNCTION_MSG("ScsiRestartAdapter\n");
    if (xvdd->device_state == DEVICE_STATE_INACTIVE) {
      FUNCTION_MSG("inactive - nothing to do\n");
      break;
    }
    /* increase the tag every time we stop/start to track where the gref's came from */
    xvdd->grant_tag++;
    IoQueueWorkItem(xvdd->connect_workitem, XenVbd_ConnectWorkItem, DelayedWorkQueue, xvdd);
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

//BOOLEAN dump_mode_hooked = FALSE;

NTSTATUS
DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath) {
  ULONG status;
  VIRTUAL_HW_INITIALIZATION_DATA VHwInitializationData;
  HW_INITIALIZATION_DATA HwInitializationData;

  FUNCTION_ENTER();
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
  FUNCTION_MSG("DriverObject = %p, RegistryPath = %p\n", DriverObject, RegistryPath);

  /* RegistryPath == NULL when we are invoked as a crash dump driver */
  if (!RegistryPath) {
    dump_mode = TRUE;
    XnPrintDump();
  }

  if (!dump_mode) {
    RtlZeroMemory(&VHwInitializationData, sizeof(VIRTUAL_HW_INITIALIZATION_DATA));
    VHwInitializationData.HwInitializationDataSize = sizeof(VIRTUAL_HW_INITIALIZATION_DATA);
    VHwInitializationData.AdapterInterfaceType = Internal;
    VHwInitializationData.DeviceExtensionSize = FIELD_OFFSET(XENVBD_DEVICE_DATA, aligned_buffer_data) + UNALIGNED_BUFFER_DATA_SIZE;
    VHwInitializationData.SpecificLuExtensionSize = 0;
    VHwInitializationData.SrbExtensionSize = sizeof(srb_list_entry_t);
    VHwInitializationData.NumberOfAccessRanges = 0;
    VHwInitializationData.MapBuffers = STOR_MAP_ALL_BUFFERS;
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
  } else {
    RtlZeroMemory(&HwInitializationData, sizeof(HW_INITIALIZATION_DATA));
    HwInitializationData.HwInitializationDataSize = sizeof(HW_INITIALIZATION_DATA);
    HwInitializationData.AdapterInterfaceType = Internal;
    HwInitializationData.DeviceExtensionSize = FIELD_OFFSET(XENVBD_DEVICE_DATA, aligned_buffer_data) + UNALIGNED_BUFFER_DATA_SIZE_DUMP_MODE;
    HwInitializationData.SrbExtensionSize = sizeof(srb_list_entry_t);
    HwInitializationData.NumberOfAccessRanges = 0;
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
  
  if(!NT_SUCCESS(status)) {
    FUNCTION_MSG("ScsiPortInitialize failed with status 0x%08x\n", status);
  }

  FUNCTION_EXIT();

  return status;
}
