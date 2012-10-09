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

#include "xenpci.h"
#include <stdlib.h>
#include <aux_klib.h>

#define SYSRQ_PATH "control/sysrq"
#define SHUTDOWN_PATH "control/shutdown"
#define BALLOON_PATH "memory/target"

extern PMDL balloon_mdl_head;

/* Not really necessary but keeps PREfast happy */
static EVT_WDF_WORKITEM XenPci_SuspendResume;
#if (VER_PRODUCTBUILD >= 7600)
static KSTART_ROUTINE XenPci_BalloonThreadProc;
#endif

static VOID
XenPci_MapHalThenPatchKernel(PXENPCI_DEVICE_DATA xpdd)
{
  NTSTATUS status;
  PAUX_MODULE_EXTENDED_INFO amei;
  ULONG module_info_buffer_size;
  ULONG i;
   
  FUNCTION_ENTER();

  amei = NULL;
  /* buffer size could change between requesting and allocating - need to loop until we are successful */
  while ((status = AuxKlibQueryModuleInformation(&module_info_buffer_size, sizeof(AUX_MODULE_EXTENDED_INFO), amei)) == STATUS_BUFFER_TOO_SMALL || amei == NULL)
  {
    if (amei != NULL)
      ExFreePoolWithTag(amei, XENPCI_POOL_TAG);
    amei = ExAllocatePoolWithTag(NonPagedPool, module_info_buffer_size, XENPCI_POOL_TAG);
  }
  
  KdPrint((__DRIVER_NAME "     AuxKlibQueryModuleInformation = %d\n", status));
  for (i = 0; i < module_info_buffer_size / sizeof(AUX_MODULE_EXTENDED_INFO); i++)
  {
    if (strcmp((PCHAR)amei[i].FullPathName + amei[i].FileNameOffset, "hal.dll") == 0)
    {
      KdPrint((__DRIVER_NAME "     hal.dll found at %p - %p\n", 
        amei[i].BasicInfo.ImageBase,
        ((PUCHAR)amei[i].BasicInfo.ImageBase) + amei[i].ImageSize));
      XenPci_PatchKernel(xpdd, amei[i].BasicInfo.ImageBase, amei[i].ImageSize);
    }
  }
  ExFreePoolWithTag(amei, XENPCI_POOL_TAG);
  FUNCTION_EXIT();
}

/*
 * Alloc MMIO from the device's MMIO region. There is no corresponding free() fn
 */
PHYSICAL_ADDRESS
XenPci_AllocMMIO(PXENPCI_DEVICE_DATA xpdd, ULONG len)
{
  PHYSICAL_ADDRESS addr;

  len = (len + PAGE_SIZE - 1) & ~(PAGE_SIZE - 1);

  addr = xpdd->platform_mmio_addr;
  addr.QuadPart += xpdd->platform_mmio_alloc;
  xpdd->platform_mmio_alloc += len;

  NT_ASSERT(xpdd->platform_mmio_alloc <= xpdd->platform_mmio_len);

  return addr;
}

extern ULONG tpr_patch_requested;

NTSTATUS
XenPci_EvtDeviceQueryRemove(WDFDEVICE device)
{
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(device);
  NTSTATUS status;
  
  FUNCTION_ENTER();
  if (xpdd->removable)
    status = STATUS_SUCCESS;
  else
    status = STATUS_UNSUCCESSFUL;
  FUNCTION_EXIT();
  return status;
}

static NTSTATUS
XenPci_Init(PXENPCI_DEVICE_DATA xpdd)
{
  struct xen_add_to_physmap xatp;
  int ret;

  FUNCTION_ENTER();

  if (!xpdd->hypercall_stubs)
  {
    NT_ASSERT(KeGetCurrentIrql() <= DISPATCH_LEVEL);
    xpdd->hypercall_stubs = hvm_get_hypercall_stubs();
  }
  if (!xpdd->hypercall_stubs)
    return STATUS_UNSUCCESSFUL;

  if (!xpdd->shared_info_area)
  {
    NT_ASSERT(KeGetCurrentIrql() <= DISPATCH_LEVEL);
    /* this should be safe as this part will never be called on resume where IRQL == HIGH_LEVEL */
    xpdd->shared_info_area_unmapped = XenPci_AllocMMIO(xpdd, PAGE_SIZE);
    xpdd->shared_info_area = MmMapIoSpace(xpdd->shared_info_area_unmapped,
      PAGE_SIZE, MmNonCached);
  }
  KdPrint((__DRIVER_NAME "     shared_info_area_unmapped.QuadPart = %lx\n", xpdd->shared_info_area_unmapped.QuadPart));
  xatp.domid = DOMID_SELF;
  xatp.idx = 0;
  xatp.space = XENMAPSPACE_shared_info;
  xatp.gpfn = (xen_pfn_t)(xpdd->shared_info_area_unmapped.QuadPart >> PAGE_SHIFT);
  KdPrint((__DRIVER_NAME "     gpfn = %x\n", xatp.gpfn));
  ret = HYPERVISOR_memory_op(xpdd, XENMEM_add_to_physmap, &xatp);
  KdPrint((__DRIVER_NAME "     hypervisor memory op (XENMAPSPACE_shared_info) ret = %d\n", ret));

  FUNCTION_EXIT();

  return STATUS_SUCCESS;
}

static NTSTATUS
XenPci_Resume(PXENPCI_DEVICE_DATA xpdd)
{
  return XenPci_Init(xpdd);
}

static VOID
XenPci_SysrqHandler(char *path, PVOID context)
{
  PXENPCI_DEVICE_DATA xpdd = context;
  char *value;
  char letter;
  char *res;

  UNREFERENCED_PARAMETER(path);

  FUNCTION_ENTER();

  XenBus_Read(xpdd, XBT_NIL, SYSRQ_PATH, &value);

  KdPrint((__DRIVER_NAME "     SysRq Value = %s\n", value));

  if (value != NULL && strlen(value) != 0)
  {
    letter = *value;
    res = XenBus_Write(xpdd, XBT_NIL, SYSRQ_PATH, "");
    if (res)
    {
      KdPrint(("Error writing sysrq path\n"));
      XenPci_FreeMem(res);
      return;
    }
  }
  else
  {
    letter = 0;
  }

  if (value != NULL)
  {
    XenPci_FreeMem(value);
  }

  switch (letter)
  {
  case 0:
    break;
  case 'B': /* cause a bug check */
    #pragma warning(suppress:28159)
    KeBugCheckEx(('X' << 16)|('E' << 8)|('N'), 0x00000001, 0x00000000, 0x00000000, 0x00000000);
    break;
  case 'A': /* cause an assert */
    NT_ASSERT(1 == 0);
    break;
  default:
    KdPrint(("     Unhandled sysrq letter %c\n", letter));
    break;
  }

  FUNCTION_EXIT();
}

#if 0
static VOID
XenPci_PrintPendingInterrupts()
{
  PULONG bitmap = (PULONG)0xFFFE0200;
  int i;
  int j;
  ULONG value;
  
  for (i = 0; i < 8; i++)
  {
    value = bitmap[(7 - i) * 4];
    if (value)
    {
      for (j = 0; j < 32; j++)
      {
        if ((value >> j) & 1)
          KdPrint(("     Interrupt pending on pin %d\n", ((7 - i) << 5) | j));
      }
    }
  }
}
#endif

static VOID
XenPci_BalloonThreadProc(PVOID StartContext)
{
  PXENPCI_DEVICE_DATA xpdd = StartContext;
  ULONG new_target_kb = xpdd->current_memory_kb;
  LARGE_INTEGER timeout;
  PLARGE_INTEGER ptimeout;
  PMDL head;
  PMDL mdl;      
  struct xen_memory_reservation reservation;
  xen_pfn_t *pfns;
  int i;
  ULONG ret;
  int pfn_count;
  int timeout_ms = 1000;
  DECLARE_CONST_UNICODE_STRING(low_mem_name, L"\\KernelObjects\\LowMemoryCondition");
  //DECLARE_CONST_UNICODE_STRING(high_commit_name, L"\\KernelObjects\\HighCommitCondition");
  //DECLARE_CONST_UNICODE_STRING(max_commit_name, L"\\KernelObjects\\MaximumCommitCondition");
  PKEVENT low_mem_event;
  //PKEVENT high_commit_event;
  //PKEVENT max_commit_event;
  HANDLE low_mem_handle;
  //HANDLE high_commit_handle;
  //HANDLE max_commit_handle;
  
  FUNCTION_ENTER();
  
  head = balloon_mdl_head;
  balloon_mdl_head = NULL;

  low_mem_event = IoCreateNotificationEvent((PUNICODE_STRING)&low_mem_name, &low_mem_handle);
  //high_commit_event = IoCreateNotificationEvent((PUNICODE_STRING)&high_commit_name, &high_commit_handle);
  //max_commit_event = IoCreateNotificationEvent((PUNICODE_STRING)&max_commit_name, &max_commit_handle);

  KdPrint((__DRIVER_NAME "     low_mem_event = %p, state = %d\n", low_mem_event, low_mem_event?KeReadStateEvent(low_mem_event):(ULONG)-1));
  //KdPrint((__DRIVER_NAME "     high_commit_event = %p, state = %d\n", high_commit_event, high_commit_event?KeReadStateEvent(high_commit_event):(ULONG)-1));
  //KdPrint((__DRIVER_NAME "     max_commit_event = %p, state = %d\n", max_commit_event, max_commit_event?KeReadStateEvent(max_commit_event):(ULONG)-1));
  
  for(;;)
  {
    /* back off exponentially if we have adjustments to make, or wait for event if we don't */
    if (xpdd->current_memory_kb != new_target_kb)
    {
      timeout.QuadPart = WDF_REL_TIMEOUT_IN_MS(timeout_ms);
      ptimeout = &timeout;
      timeout_ms <<= 1;
      if (timeout_ms > 60000)
        timeout_ms = 60000;
    }
    else
    {
      ptimeout = NULL;
      timeout_ms = 1000;
    }
    KeWaitForSingleObject(&xpdd->balloon_event, Executive, KernelMode, FALSE, ptimeout);
    if (xpdd->balloon_shutdown)
      PsTerminateSystemThread(0);
    KdPrint((__DRIVER_NAME "     Got balloon event, current = %d, target = %d\n", xpdd->current_memory_kb, xpdd->target_memory_kb));
    /* not really worried about races here, but cache target so we only read it once */
    new_target_kb = xpdd->target_memory_kb;
    // perform some sanity checks on target_memory
    // make sure target <= initial
    // make sure target > some % of initial
    
    if (xpdd->current_memory_kb == new_target_kb)
    {
      KdPrint((__DRIVER_NAME "     No change to memory\n"));
      continue;
    }
    else if (xpdd->current_memory_kb < new_target_kb)
    {
      KdPrint((__DRIVER_NAME "     Trying to take %d MB from Xen\n", new_target_kb - xpdd->current_memory_kb));
      while ((mdl = head) != NULL && xpdd->current_memory_kb < new_target_kb)
      {
        pfn_count = ADDRESS_AND_SIZE_TO_SPAN_PAGES(MmGetMdlVirtualAddress(mdl), MmGetMdlByteCount(mdl));
        pfns = ExAllocatePoolWithTag(NonPagedPool, pfn_count * sizeof(xen_pfn_t), XENPCI_POOL_TAG);
        /* sizeof(xen_pfn_t) may not be the same as PPFN_NUMBER */
        for (i = 0; i < pfn_count; i++)
          pfns[i] = (xen_pfn_t)(MmGetMdlPfnArray(mdl)[i]);
        reservation.address_bits = 0;
        reservation.extent_order = 0;
        reservation.domid = DOMID_SELF;
        reservation.nr_extents = pfn_count;
        #pragma warning(disable: 4127) /* conditional expression is constant */
        set_xen_guest_handle(reservation.extent_start, pfns);
        
        //KdPrint((__DRIVER_NAME "     Calling HYPERVISOR_memory_op(XENMEM_populate_physmap) - pfn_count = %d\n", pfn_count));
        ret = HYPERVISOR_memory_op(xpdd, XENMEM_populate_physmap, &reservation);
        //KdPrint((__DRIVER_NAME "     populated %d pages\n", ret));
        if (ret < (ULONG)pfn_count)
        {
          if (ret > 0)
          {
            /* We hit the Xen hard limit: reprobe. */
            reservation.nr_extents = ret;
            ret = HYPERVISOR_memory_op(xpdd, XENMEM_decrease_reservation, &reservation);
            KdPrint((__DRIVER_NAME "     decreased %d pages (xen is out of pages)\n", ret));
          }
          ExFreePoolWithTag(pfns, XENPCI_POOL_TAG);
          break;
        }
        ExFreePoolWithTag(pfns, XENPCI_POOL_TAG);
        head = mdl->Next;
        mdl->Next = NULL;        
        MmFreePagesFromMdl(mdl);
        ExFreePool(mdl);
        xpdd->current_memory_kb += BALLOON_UNITS_KB;
      }
    }
    else
    {
      KdPrint((__DRIVER_NAME "     Trying to give %d MB to Xen\n", xpdd->current_memory_kb - new_target_kb));
      while (xpdd->current_memory_kb > new_target_kb)
      {
        PHYSICAL_ADDRESS alloc_low;
        PHYSICAL_ADDRESS alloc_high;
        PHYSICAL_ADDRESS alloc_skip;
        alloc_low.QuadPart = 0;
        alloc_high.QuadPart = 0xFFFFFFFFFFFFFFFFULL;
        alloc_skip.QuadPart = 0;

        if (low_mem_event && KeReadStateEvent(low_mem_event))
        {
          KdPrint((__DRIVER_NAME "     Low memory condition exists. Waiting.\n"));
          //KdPrint((__DRIVER_NAME "     low_mem_event = %p, state = %d\n", low_mem_event, low_mem_event?KeReadStateEvent(low_mem_event):(ULONG)-1));
          //KdPrint((__DRIVER_NAME "     high_commit_event = %p, state = %d\n", high_commit_event, high_commit_event?KeReadStateEvent(high_commit_event):(ULONG)-1));
          //KdPrint((__DRIVER_NAME "     max_commit_event = %p, state = %d\n", max_commit_event, max_commit_event?KeReadStateEvent(max_commit_event):(ULONG)-1));
          break;
        }

        #if (NTDDI_VERSION >= NTDDI_WS03SP1)
        /* our contract says that we must zero pages before returning to xen, so we can't use MM_DONT_ZERO_ALLOCATION */
        mdl = MmAllocatePagesForMdlEx(alloc_low, alloc_high, alloc_skip, BALLOON_UNITS_KB * 1024, MmCached, 0);
        #else
        mdl = MmAllocatePagesForMdl(alloc_low, alloc_high, alloc_skip, BALLOON_UNITS_KB * 1024);
        #endif
        if (!mdl)
        {
          KdPrint((__DRIVER_NAME "     Allocation failed - try again soon\n"));
          break;
        }
        else
        {
          int i;
          ULONG ret;
          int pfn_count = ADDRESS_AND_SIZE_TO_SPAN_PAGES(MmGetMdlVirtualAddress(mdl), MmGetMdlByteCount(mdl));
          if (pfn_count != BALLOON_UNIT_PAGES)
          {
            /* we could probably do this better but it will only happen in low memory conditions... */
            KdPrint((__DRIVER_NAME "     wanted %d pages got %d pages\n", BALLOON_UNIT_PAGES, pfn_count));
            MmFreePagesFromMdl(mdl);
            ExFreePool(mdl);
            break;
          }
          pfns = ExAllocatePoolWithTag(NonPagedPool, pfn_count * sizeof(xen_pfn_t), XENPCI_POOL_TAG);
          /* sizeof(xen_pfn_t) may not be the same as PPFN_NUMBER */
          for (i = 0; i < pfn_count; i++)
            pfns[i] = (xen_pfn_t)(MmGetMdlPfnArray(mdl)[i]);
          reservation.address_bits = 0;
          reservation.extent_order = 0;
          reservation.domid = DOMID_SELF;
          reservation.nr_extents = pfn_count;
          #pragma warning(disable: 4127) /* conditional expression is constant */
          set_xen_guest_handle(reservation.extent_start, pfns);
          
          //KdPrint((__DRIVER_NAME "     Calling HYPERVISOR_memory_op(XENMEM_decrease_reservation) - pfn_count = %d\n", pfn_count));
          ret = HYPERVISOR_memory_op(xpdd, XENMEM_decrease_reservation, &reservation);
          ExFreePoolWithTag(pfns, XENPCI_POOL_TAG);
          //KdPrint((__DRIVER_NAME "     decreased %d pages\n", ret));
          if (head)
          {
            mdl->Next = head;
            head = mdl;
          }
          else
          {
            head = mdl;
          }
          xpdd->current_memory_kb -= BALLOON_UNITS_KB;
        }
      }
    }
    KdPrint((__DRIVER_NAME "     Memory = %d, Balloon Target = %d\n", xpdd->current_memory_kb, new_target_kb));
  }
  //FUNCTION_EXIT();
}

static VOID
XenPci_BalloonHandler(char *Path, PVOID Data)
{
  WDFDEVICE device = Data;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(device);
  char *value;
  xenbus_transaction_t xbt;
  int retry;

  UNREFERENCED_PARAMETER(Path);

  FUNCTION_ENTER();

  XenBus_StartTransaction(xpdd, &xbt);

  XenBus_Read(xpdd, XBT_NIL, BALLOON_PATH, &value);
  
  if (value == NULL)
  {
    KdPrint((__DRIVER_NAME "     Failed to read value\n"));
    XenBus_EndTransaction(xpdd, xbt, 0, &retry);
    FUNCTION_EXIT();
    return;
  }

  if (atoi(value) > 0)
    xpdd->target_memory_kb = atoi(value);

  KdPrint((__DRIVER_NAME "     target memory value = %d (%s)\n", xpdd->target_memory_kb, value));

  XenBus_EndTransaction(xpdd, xbt, 0, &retry);

  XenPci_FreeMem(value);

  KeSetEvent(&xpdd->balloon_event, IO_NO_INCREMENT, FALSE);
  
  FUNCTION_EXIT();
}

static VOID
XenPci_Suspend0(PVOID context)
{
  PXENPCI_DEVICE_DATA xpdd = context;
  ULONG cancelled;
  ULONGLONG sysenter_cs, sysenter_esp, sysenter_eip;
  
  FUNCTION_ENTER();

  GntTbl_Suspend(xpdd);

  sysenter_cs = __readmsr(0x174);
  sysenter_esp = __readmsr(0x175);
  sysenter_eip = __readmsr(0x176);
  
  cancelled = hvm_shutdown(xpdd, SHUTDOWN_suspend);

  if (__readmsr(0x174) != sysenter_cs)
  {
    KdPrint((__DRIVER_NAME "     sysenter_cs not restored. Fixing.\n"));
    __writemsr(0x174, sysenter_cs);
  }
  if (__readmsr(0x175) != sysenter_esp)
  {
    KdPrint((__DRIVER_NAME "     sysenter_esp not restored. Fixing.\n"));
    __writemsr(0x175, sysenter_esp);
  }
  if (__readmsr(0x176) != sysenter_eip)
  {
      KdPrint((__DRIVER_NAME "     sysenter_eip not restored. Fixing.\n"));
    __writemsr(0x176, sysenter_eip);
  }

  KdPrint((__DRIVER_NAME "     back from suspend, cancelled = %d\n", cancelled));

  if (qemu_hide_flags_value)
  {
    XenPci_HideQemuDevices();
  }

  XenPci_Resume(xpdd);
  GntTbl_Resume(xpdd);
  EvtChn_Resume(xpdd); /* this enables interrupts again too */

  FUNCTION_EXIT();
}

static VOID
XenPci_SuspendN(PVOID context)
{
  UNREFERENCED_PARAMETER(context);
  
  FUNCTION_ENTER();
  KdPrint((__DRIVER_NAME "     doing nothing on cpu N\n"));
  FUNCTION_EXIT();
}

static VOID
XenPci_SuspendEvtDpc(PVOID context);
static NTSTATUS
XenPci_ConnectSuspendEvt(PXENPCI_DEVICE_DATA xpdd);

/* called at PASSIVE_LEVEL */
static NTSTATUS
XenPci_ConnectSuspendEvt(PXENPCI_DEVICE_DATA xpdd)
{
  CHAR path[128];

  xpdd->suspend_evtchn = EvtChn_AllocUnbound(xpdd, 0);
  KdPrint((__DRIVER_NAME "     suspend event channel = %d\n", xpdd->suspend_evtchn));
  RtlStringCbPrintfA(path, ARRAY_SIZE(path), "device/suspend/event-channel");
  XenBus_Printf(xpdd, XBT_NIL, path, "%d", xpdd->suspend_evtchn);
  EvtChn_BindDpc(xpdd, xpdd->suspend_evtchn, XenPci_SuspendEvtDpc, xpdd->wdf_device, EVT_ACTION_FLAGS_NO_SUSPEND);
  
  return STATUS_SUCCESS;
}

/* Called at PASSIVE_LEVEL */
static VOID
XenPci_SuspendResume(WDFWORKITEM workitem)
{
  NTSTATUS status;
  //KAFFINITY ActiveProcessorMask = 0; // this is for Vista+
  WDFDEVICE device = WdfWorkItemGetParentObject(workitem);
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(device);
  WDFCHILDLIST child_list = WdfFdoGetDefaultChildList(device);
  WDF_CHILD_LIST_ITERATOR child_iterator;
  WDFDEVICE child_device;

  FUNCTION_ENTER();

  if (xpdd->suspend_state == SUSPEND_STATE_NONE)
  {
    xpdd->suspend_state = SUSPEND_STATE_SCHEDULED;
    KeMemoryBarrier();

    WDF_CHILD_LIST_ITERATOR_INIT(&child_iterator, WdfRetrievePresentChildren);
    WdfChildListBeginIteration(child_list, &child_iterator);
    while ((status = WdfChildListRetrieveNextDevice(child_list, &child_iterator, &child_device, NULL)) == STATUS_SUCCESS)
    {
      KdPrint((__DRIVER_NAME "     Suspending child\n"));
      XenPci_Pdo_Suspend(child_device);
    }
    WdfChildListEndIteration(child_list, &child_iterator);

    XenBus_Suspend(xpdd);
    EvtChn_Suspend(xpdd);
    XenPci_HighSync(XenPci_Suspend0, XenPci_SuspendN, xpdd);

    xpdd->suspend_state = SUSPEND_STATE_RESUMING;
    XenBus_Resume(xpdd);

    XenPci_ConnectSuspendEvt(xpdd);

    WdfChildListBeginIteration(child_list, &child_iterator);
    while ((status = WdfChildListRetrieveNextDevice(child_list, &child_iterator, &child_device, NULL)) == STATUS_SUCCESS)
    {
      KdPrint((__DRIVER_NAME "     Resuming child\n"));
      XenPci_Pdo_Resume(child_device);
    }
    WdfChildListEndIteration(child_list, &child_iterator);

    xpdd->suspend_state = SUSPEND_STATE_NONE;
  }
  FUNCTION_EXIT();
}

/* called at DISPATCH_LEVEL */
static VOID
XenPci_SuspendEvtDpc(PVOID context)
{
  NTSTATUS status;
  WDFDEVICE device = context;
  //KIRQL old_irql;
  WDF_OBJECT_ATTRIBUTES attributes;
  WDF_WORKITEM_CONFIG workitem_config;
  WDFWORKITEM workitem;

  KdPrint((__DRIVER_NAME "     Suspend detected via Dpc\n"));
  WDF_WORKITEM_CONFIG_INIT(&workitem_config, XenPci_SuspendResume);
  WDF_OBJECT_ATTRIBUTES_INIT(&attributes);
  attributes.ParentObject = device;
  status = WdfWorkItemCreate(&workitem_config, &attributes, &workitem);
  if (status != STATUS_SUCCESS) {
    /* how should we fail here */
    FUNCTION_MSG("WdfWorkItemCreate failed\n");
    return;
  }
  WdfWorkItemEnqueue(workitem);
}

static void
XenPci_ShutdownHandler(char *path, PVOID context)
{
  NTSTATUS status;
  WDFDEVICE device = context;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(device);
  char *res;
  char *value;
  //KIRQL old_irql;
  WDF_OBJECT_ATTRIBUTES attributes;
  WDF_WORKITEM_CONFIG workitem_config;
  WDFWORKITEM workitem;

  UNREFERENCED_PARAMETER(path);

  FUNCTION_ENTER();

  res = XenBus_Read(xpdd, XBT_NIL, SHUTDOWN_PATH, &value);
  if (res)
  {
    KdPrint(("Error reading shutdown path - %s\n", res));
    XenPci_FreeMem(res);
    FUNCTION_EXIT();
    return;
  }

  KdPrint((__DRIVER_NAME "     Shutdown value = %s\n", value));

  if (strlen(value) && strcmp(value, "suspend") == 0)
  {
    {
      KdPrint((__DRIVER_NAME "     Suspend detected\n"));
      /* we have to queue this as a work item as we stop the xenbus thread, which we are currently running in! */
      WDF_WORKITEM_CONFIG_INIT(&workitem_config, XenPci_SuspendResume);
      WDF_OBJECT_ATTRIBUTES_INIT(&attributes);
      attributes.ParentObject = device;
      status = WdfWorkItemCreate(&workitem_config, &attributes, &workitem);
      // TODO: check status here
      WdfWorkItemEnqueue(workitem);
    }
  }

  XenPci_FreeMem(value);

  FUNCTION_EXIT();
}

static VOID
XenPci_DeviceWatchHandler(char *path, PVOID context)
{
  char **bits;
  int count;
  char *err;
  char *value;
  PXENPCI_DEVICE_DATA xpdd = context;

  FUNCTION_ENTER();

  bits = SplitString(path, '/', 4, &count);
  if (count == 3)
  {
    err = XenBus_Read(xpdd, XBT_NIL, path, &value);
    if (err)
    {
      /* obviously path no longer exists, in which case the removal is being taken care of elsewhere and we shouldn't invalidate now */
      XenPci_FreeMem(err);
    }
    else
    {
      XenPci_FreeMem(value);
      /* we probably have to be a bit smarter here and do nothing if xenpci isn't running yet */
      KdPrint((__DRIVER_NAME "     Rescanning child list\n"));
      XenPci_EvtChildListScanForChildren(xpdd->child_list);
    }
  }
  FreeSplitString(bits, count);

  FUNCTION_EXIT();
}

NTSTATUS
XenPci_EvtDevicePrepareHardware (WDFDEVICE device, WDFCMRESLIST resources_raw, WDFCMRESLIST resources_translated)
{
  NTSTATUS status = STATUS_SUCCESS;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(device);
  PCM_PARTIAL_RESOURCE_DESCRIPTOR raw_descriptor, translated_descriptor;
  ULONG i;

  FUNCTION_ENTER();
  
  NT_ASSERT(WdfCmResourceListGetCount(resources_raw) == WdfCmResourceListGetCount(resources_translated));
  
  for (i = 0; i < WdfCmResourceListGetCount(resources_raw); i++)
  {
    raw_descriptor = WdfCmResourceListGetDescriptor(resources_raw, i);
    translated_descriptor = WdfCmResourceListGetDescriptor(resources_translated, i);
    switch (raw_descriptor->Type) {
    case CmResourceTypePort:
      KdPrint((__DRIVER_NAME "     IoPort Address(%x) Length: %d\n", translated_descriptor->u.Port.Start.LowPart, translated_descriptor->u.Port.Length));
      xpdd->platform_ioport_addr = translated_descriptor->u.Port.Start.LowPart;
      xpdd->platform_ioport_len = translated_descriptor->u.Port.Length;
      break;
    case CmResourceTypeMemory:
      KdPrint((__DRIVER_NAME "     Memory mapped CSR:(%x:%x) Length:(%d)\n", translated_descriptor->u.Memory.Start.LowPart, translated_descriptor->u.Memory.Start.HighPart, translated_descriptor->u.Memory.Length));
      KdPrint((__DRIVER_NAME "     Memory flags = %04X\n", translated_descriptor->Flags));
#if 0      
      mmio_freelist_free = 0;
      for (j = 0; j < translated_descriptor->u.Memory.Length >> PAGE_SHIFT; j++)
        put_mmio_on_freelist((xpdd->platform_mmio_addr >> PAGE_SHIFT) + j);
#endif
      xpdd->platform_mmio_addr = translated_descriptor->u.Memory.Start;
      xpdd->platform_mmio_len = translated_descriptor->u.Memory.Length;
      xpdd->platform_mmio_flags = translated_descriptor->Flags;
      break;
    case CmResourceTypeInterrupt:
	    xpdd->irq_level = (KIRQL)translated_descriptor->u.Interrupt.Level;
  	  xpdd->irq_vector = translated_descriptor->u.Interrupt.Vector;
	    xpdd->irq_affinity = translated_descriptor->u.Interrupt.Affinity;
      xpdd->irq_mode = (translated_descriptor->Flags & CM_RESOURCE_INTERRUPT_LATCHED)?Latched:LevelSensitive;
      xpdd->irq_number = raw_descriptor->u.Interrupt.Vector;      
      KdPrint((__DRIVER_NAME "     irq_number = %03x\n", raw_descriptor->u.Interrupt.Vector));
      KdPrint((__DRIVER_NAME "     irq_vector = %03x\n", translated_descriptor->u.Interrupt.Vector));
      KdPrint((__DRIVER_NAME "     irq_level = %03x\n", translated_descriptor->u.Interrupt.Level));
      KdPrint((__DRIVER_NAME "     irq_mode = %s\n", (xpdd->irq_mode == Latched)?"Latched":"LevelSensitive"));
      switch(translated_descriptor->ShareDisposition)
      {
      case CmResourceShareDeviceExclusive:
        KdPrint((__DRIVER_NAME "     ShareDisposition = CmResourceShareDeviceExclusive\n"));
        break;
      case CmResourceShareDriverExclusive:
        KdPrint((__DRIVER_NAME "     ShareDisposition = CmResourceShareDriverExclusive\n"));
        break;
      case CmResourceShareShared:
        KdPrint((__DRIVER_NAME "     ShareDisposition = CmResourceShareShared\n"));
        break;
      default:
        KdPrint((__DRIVER_NAME "     ShareDisposition = %d\n", translated_descriptor->ShareDisposition));
        break;
      }
      break;
    case CmResourceTypeDevicePrivate:
      KdPrint((__DRIVER_NAME "     Private Data: 0x%02x 0x%02x 0x%02x\n", translated_descriptor->u.DevicePrivate.Data[0], translated_descriptor->u.DevicePrivate.Data[1], translated_descriptor->u.DevicePrivate.Data[2]));
      break;
    default:
      KdPrint((__DRIVER_NAME "     Unhandled resource type (0x%x)\n", translated_descriptor->Type));
      break;
    }
  }

  FUNCTION_EXIT();
  
  return status;
}

NTSTATUS
XenPci_EvtDeviceD0Entry(WDFDEVICE device, WDF_POWER_DEVICE_STATE previous_state)
{
  NTSTATUS status = STATUS_SUCCESS;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(device);

  FUNCTION_ENTER();

  xpdd->hibernated = FALSE;
  switch (previous_state)
  {
  case WdfPowerDeviceD0:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD1\n"));
    break;
  case WdfPowerDeviceD1:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD1\n"));
    break;
  case WdfPowerDeviceD2:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD2\n"));
    break;
  case WdfPowerDeviceD3:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD3\n"));
    break;
  case WdfPowerDeviceD3Final:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD3Final\n"));
    break;
  case WdfPowerDevicePrepareForHibernation:
    KdPrint((__DRIVER_NAME "     WdfPowerDevicePrepareForHibernation\n"));
    break;  
  default:
    KdPrint((__DRIVER_NAME "     Unknown WdfPowerDevice state %d\n", previous_state));
    break;  
  }

  if (previous_state == WdfPowerDevicePrepareForHibernation && qemu_hide_flags_value)
  {
    XenPci_HideQemuDevices();
  }
  
  if (previous_state == WdfPowerDeviceD3Final)
  {
    XenPci_Init(xpdd);
    if (tpr_patch_requested && !xpdd->tpr_patched)
    {
      XenPci_MapHalThenPatchKernel(xpdd);
      xpdd->tpr_patched = TRUE;
      xpdd->removable = FALSE;
    }
    GntTbl_Init(xpdd);
    EvtChn_Init(xpdd);

  // use the memory_op(unsigned int op, void *arg) hypercall to adjust memory
  // use XENMEM_increase_reservation and XENMEM_decrease_reservation
  }
  else
  {
    XenPci_Resume(xpdd);
    GntTbl_Resume(xpdd);
    EvtChn_Resume(xpdd);
  }

  FUNCTION_EXIT();

  return status;
}

NTSTATUS
XenPci_EvtDeviceD0EntryPostInterruptsEnabled(WDFDEVICE device, WDF_POWER_DEVICE_STATE previous_state)
{
  NTSTATUS status = STATUS_SUCCESS;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(device);
  PCHAR response;
  char *value;
  HANDLE thread_handle;

  UNREFERENCED_PARAMETER(previous_state);

  FUNCTION_ENTER();

  if (previous_state == WdfPowerDeviceD3Final)
  {  
    XenBus_Init(xpdd);

    XenPci_ConnectSuspendEvt(xpdd);
    
    response = XenBus_AddWatch(xpdd, XBT_NIL, SYSRQ_PATH, XenPci_SysrqHandler, xpdd);
    
    response = XenBus_AddWatch(xpdd, XBT_NIL, SHUTDOWN_PATH, XenPci_ShutdownHandler, device);

    response = XenBus_AddWatch(xpdd, XBT_NIL, "device", XenPci_DeviceWatchHandler, xpdd);

    if (!xpdd->initial_memory_kb)
    {
      XenBus_Read(xpdd, XBT_NIL, BALLOON_PATH, &value);
      if (atoi(value) > 0)
      {
        xpdd->initial_memory_kb = atoi(value);
        xpdd->current_memory_kb = xpdd->initial_memory_kb;
        xpdd->target_memory_kb = xpdd->initial_memory_kb;
      }
      KdPrint((__DRIVER_NAME "     Initial Memory Value = %d (%s)\n", xpdd->initial_memory_kb, value));
      KeInitializeEvent(&xpdd->balloon_event, SynchronizationEvent, FALSE);
      xpdd->balloon_shutdown = FALSE;
      status = PsCreateSystemThread(&thread_handle, THREAD_ALL_ACCESS, NULL, NULL, NULL, XenPci_BalloonThreadProc, xpdd);
      if (!NT_SUCCESS(status))
      {
        KdPrint((__DRIVER_NAME "     Could not start balloon thread\n"));
        return status;
      }
      status = ObReferenceObjectByHandle(thread_handle, THREAD_ALL_ACCESS, NULL, KernelMode, &xpdd->balloon_thread, NULL);
      ZwClose(thread_handle);
    }
    response = XenBus_AddWatch(xpdd, XBT_NIL, BALLOON_PATH, XenPci_BalloonHandler, device);
  }
  else
  {
    XenBus_Resume(xpdd);
    XenPci_ConnectSuspendEvt(xpdd);
  }
  FUNCTION_EXIT();
  
  return status;
}

NTSTATUS
XenPci_EvtDeviceD0ExitPreInterruptsDisabled(WDFDEVICE device, WDF_POWER_DEVICE_STATE target_state)
{
  NTSTATUS status = STATUS_SUCCESS;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(device);
  LARGE_INTEGER timeout;
  
  FUNCTION_ENTER();
  
  switch (target_state)
  {
  case WdfPowerDeviceD0:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD1\n"));
    break;
  case WdfPowerDeviceD1:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD1\n"));
    break;
  case WdfPowerDeviceD2:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD2\n"));
    break;
  case WdfPowerDeviceD3:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD3\n"));
    break;
  case WdfPowerDeviceD3Final:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD3Final\n"));
    break;
  case WdfPowerDevicePrepareForHibernation:
    KdPrint((__DRIVER_NAME "     WdfPowerDevicePrepareForHibernation\n"));
    break;
  default:
    KdPrint((__DRIVER_NAME "     Unknown WdfPowerDevice state %d\n", target_state));
    break;  
  }

  if (target_state == WdfPowerDeviceD3Final)
  {
    KdPrint((__DRIVER_NAME "     Shutting down threads\n"));

    xpdd->balloon_shutdown = TRUE;
    KeSetEvent(&xpdd->balloon_event, IO_NO_INCREMENT, FALSE);
  
    timeout.QuadPart = (LONGLONG)-1 * 1000 * 1000 * 10;
    while ((status = KeWaitForSingleObject(xpdd->balloon_thread, Executive, KernelMode, FALSE, &timeout)) != STATUS_SUCCESS)
    {
      timeout.QuadPart = (LONGLONG)-1 * 1000 * 1000 * 10;
      KdPrint((__DRIVER_NAME "     Waiting for balloon thread to stop\n"));
    }
    ObDereferenceObject(xpdd->balloon_thread);

    XenBus_Halt(xpdd);
  }
  else
  {
    XenBus_Suspend(xpdd);
  }
  
  FUNCTION_EXIT();
  
  return status;
}

NTSTATUS
XenPci_EvtDeviceD0Exit(WDFDEVICE device, WDF_POWER_DEVICE_STATE target_state)
{
  NTSTATUS status = STATUS_SUCCESS;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(device);
  
  FUNCTION_ENTER();

  switch (target_state)
  {
  case WdfPowerDeviceD0:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD1\n"));
    break;
  case WdfPowerDeviceD1:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD1\n"));
    break;
  case WdfPowerDeviceD2:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD2\n"));
    break;
  case WdfPowerDeviceD3:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD3\n"));
    break;
  case WdfPowerDeviceD3Final:
    KdPrint((__DRIVER_NAME "     WdfPowerDeviceD3Final\n"));
    break;
  case WdfPowerDevicePrepareForHibernation:
    KdPrint((__DRIVER_NAME "     WdfPowerDevicePrepareForHibernation\n"));
    xpdd->hibernated = TRUE;
    break;  
  default:
    KdPrint((__DRIVER_NAME "     Unknown WdfPowerDevice state %d\n", target_state));
    break;  
  }
  
  if (target_state == WdfPowerDeviceD3Final)
  {
    /* we don't really support exit here */
  }
  else
  {
    EvtChn_Suspend(xpdd);
    GntTbl_Suspend(xpdd);
    
  }

  FUNCTION_EXIT();
  
  return status;
}

NTSTATUS
XenPci_EvtDeviceReleaseHardware(WDFDEVICE device, WDFCMRESLIST resources_translated)
{
  NTSTATUS status = STATUS_SUCCESS;
  
  UNREFERENCED_PARAMETER(device);
  UNREFERENCED_PARAMETER(resources_translated);
  
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  
  return status;
}

/* Called at PASSIVE_LEVEL but with pagefile unavailable */
/* Can be called concurrently, but KMDF takes care of concurrent calls to WdfChildListXxx */
VOID
XenPci_EvtChildListScanForChildren(WDFCHILDLIST child_list)
{
  NTSTATUS status;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(WdfChildListGetDevice(child_list));
  char *msg;
  char **devices;
  char **instances;
  ULONG i, j;
  CHAR path[128];
  XENPCI_PDO_IDENTIFICATION_DESCRIPTION child_description;
  PVOID entry;
  WDFDEVICE child_device;
  WDF_CHILD_RETRIEVE_INFO retrieve_info;
  
  FUNCTION_ENTER();

  WdfChildListBeginScan(child_list);

  msg = XenBus_List(xpdd, XBT_NIL, "device", &devices);
  if (!msg)
  {
    for (i = 0; devices[i]; i++)
    {
      /* make sure the key is not in the veto list */
      for (entry = xpdd->veto_list.Flink; entry != &xpdd->veto_list; entry = ((PLIST_ENTRY)entry)->Flink)
      {
        if (!strcmp(devices[i], (PCHAR)entry + sizeof(LIST_ENTRY)))
          break;
      }
      if (entry != &xpdd->veto_list)
      {
        XenPci_FreeMem(devices[i]);
        continue;
      }
    
      RtlStringCbPrintfA(path, ARRAY_SIZE(path), "device/%s", devices[i]);
      msg = XenBus_List(xpdd, XBT_NIL, path, &instances);
      if (!msg)
      {
        for (j = 0; instances[j]; j++)
        {
          /* the device comparison is done as a memory compare so zero-ing the structure is important */
          RtlZeroMemory(&child_description, sizeof(child_description));
          WDF_CHILD_IDENTIFICATION_DESCRIPTION_HEADER_INIT(&child_description.header, sizeof(child_description));
          RtlStringCbPrintfA(path, ARRAY_SIZE(path), "device/%s/%s", devices[i], instances[j]);
          KdPrint((__DRIVER_NAME "     Found path = %s\n", path));
          RtlStringCbCopyA(child_description.path, ARRAY_SIZE(child_description.path), path);
          RtlStringCbCopyA(child_description.device, ARRAY_SIZE(child_description.device), devices[i]);
          child_description.index = atoi(instances[j]);
          WDF_CHILD_RETRIEVE_INFO_INIT(&retrieve_info, &child_description.header);
          child_device = WdfChildListRetrievePdo(child_list, &retrieve_info);
          if (child_device)
          {
            PXENPCI_PDO_DEVICE_DATA xppdd = GetXppdd(child_device);
            char *err;
            char *value;
            char backend_state_path[128];
            
            if (xppdd->do_not_enumerate)
            {
              RtlStringCbPrintfA(backend_state_path, ARRAY_SIZE(path), "%s/state", xppdd->backend_path);
            
              err = XenBus_Read(xpdd, XBT_NIL, backend_state_path, &value);
              if (err)
              {
                XenPci_FreeMem(err);
                xppdd->backend_state = XenbusStateUnknown;
              }
              else
              {
                xppdd->backend_state = atoi(value);
                XenPci_FreeMem(value);
              }
              if (xppdd->backend_state == XenbusStateClosing || xppdd->backend_state == XenbusStateClosed)
              {
                KdPrint((__DRIVER_NAME "     Surprise removing %s due to backend initiated remove\n", path));
                XenPci_FreeMem(instances[j]);
                continue;
              }
              else
              {
                /* I guess we are being added again ... */
                xppdd->backend_initiated_remove = FALSE;
                xppdd->do_not_enumerate = FALSE;
              }
            }
          }
          status = WdfChildListAddOrUpdateChildDescriptionAsPresent(child_list, &child_description.header, NULL);
          if (!NT_SUCCESS(status))
          {
            KdPrint((__DRIVER_NAME "     WdfChildListAddOrUpdateChildDescriptionAsPresent failed with status 0x%08x\n", status));
          }
          XenPci_FreeMem(instances[j]);
        }
        XenPci_FreeMem(instances);
      }
      else
      {
        // wtf do we do here???
        KdPrint((__DRIVER_NAME "     Failed to list %s tree\n", devices[i]));
      }
      XenPci_FreeMem(devices[i]);
    }
    XenPci_FreeMem(devices);
  }
  else
  {
    // wtf do we do here???
    KdPrint((__DRIVER_NAME "     Failed to list device tree\n"));
  }

  WdfChildListEndScan(child_list);

  FUNCTION_EXIT();
}
