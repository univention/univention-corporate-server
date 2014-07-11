/*
PV Drivers for Windows Xen HVM Domains
Copyright (C) 2009 James Harper

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
#include <io/ring.h>

#pragma warning(disable : 4200) // zero-sized array
#pragma warning(disable: 4127) // conditional expression is constant

#define MAP_TYPE_INVALID  0
#define MAP_TYPE_VIRTUAL  1
#define MAP_TYPE_MDL      2
#define MAP_TYPE_REMAPPED 3


#if 0
kd> dt _ADAPTER_OBJECT 81e96b08 -v
hal!_ADAPTER_OBJECT
struct _ADAPTER_OBJECT, 26 elements, 0x64 bytes
   +0x000 DmaHeader        : struct _DMA_ADAPTER, 3 elements, 0x8 bytes
   +0x008 MasterAdapter    : (null) 
   +0x00c MapRegistersPerChannel : 0x80001
   +0x010 AdapterBaseVa    : (null) 
   +0x014 MapRegisterBase  : (null) 
   +0x018 NumberOfMapRegisters : 0
   +0x01c CommittedMapRegisters : 0
   +0x020 CurrentWcb       : (null) 
   +0x024 ChannelWaitQueue : struct _KDEVICE_QUEUE, 5 elements, 0x14 bytes
   +0x038 RegisterWaitQueue : (null) 
   +0x03c AdapterQueue     : struct _LIST_ENTRY, 2 elements, 0x8 bytes
 [ 0x0 - 0x0 ]
   +0x044 SpinLock         : 0
   +0x048 MapRegisters     : (null) 
   +0x04c PagePort         : (null) 
   +0x050 ChannelNumber    : 0xff ''
   +0x051 AdapterNumber    : 0 ''
   +0x052 DmaPortAddress   : 0
   +0x054 AdapterMode      : 0 ''
   +0x055 NeedsMapRegisters : 0 ''
   +0x056 MasterDevice     : 0x1 ''
   +0x057 Width16Bits      : 0 ''
   +0x058 ScatterGather    : 0x1 ''
   +0x059 IgnoreCount      : 0 ''
   +0x05a Dma32BitAddresses : 0x1 ''
   +0x05b Dma64BitAddresses : 0 ''
   +0x05c AdapterList      : struct _LIST_ENTRY, 2 elements, 0x8 bytes
 [ 0x806e1250 - 0x81f1b474 ]
#endif

/* need to confirm that this is the same for AMD64 too */
typedef struct {
  DMA_ADAPTER DmaHeader;
  PVOID MasterAdapter;
  ULONG MapRegistersPerChannel;
  PVOID AdapterBaseVa;
  PVOID MapRegisterBase;
  ULONG NumberOfMapRegisters;
  ULONG CommittedMapRegisters;
  PVOID CurrentWcb;
  KDEVICE_QUEUE ChannelWaitQueue;
  PKDEVICE_QUEUE RegisterWaitQueue;
  LIST_ENTRY AdapterQueue;
  KSPIN_LOCK SpinLock;
  PVOID MapRegisters;
  PVOID PagePort;
  UCHAR ChannelNumber;
  UCHAR AdapterNumber;
  USHORT DmaPortAddress;
  UCHAR AdapterMode;
  BOOLEAN NeedsMapRegisters;
  BOOLEAN MasterDevice;
  UCHAR Width16Bits;
  BOOLEAN ScatterGather;
  BOOLEAN IgnoreCount;
  BOOLEAN Dma32BitAddresses;
  BOOLEAN Dma64BitAddresses;
#if (NTDDI_VERSION >= NTDDI_WS03)
  BOOLEAN LegacyAdapter;
#endif
  LIST_ENTRY AdapterList;
} X_ADAPTER_OBJECT;

typedef struct {
  ULONG map_type;
  PVOID aligned_buffer;
  ULONG copy_length;
  PMDL mdl;
  PVOID currentva;
  BOOLEAN allocated_by_me;
} sg_extra_t;

typedef struct {
  ULONG map_type;
  PVOID aligned_buffer;
  PVOID unaligned_buffer;
  ULONG copy_length;
  grant_ref_t gref;
  PHYSICAL_ADDRESS logical;
} map_register_t;

typedef struct {
  PDEVICE_OBJECT device_object;
  ULONG total_map_registers;
  PDRIVER_CONTROL execution_routine;
  PIRP current_irp;
  PVOID context;
  ULONG count;
  map_register_t regs[1];
} map_register_base_t;  
  
typedef struct {
  X_ADAPTER_OBJECT adapter_object;
  PXENPCI_PDO_DEVICE_DATA xppdd;
  dma_driver_extension_t *dma_extension;
  PDRIVER_OBJECT dma_extension_driver; /* to deference it */
  map_register_base_t *map_register_base;
  map_register_base_t *queued_map_register_base;  
  KSPIN_LOCK lock;
} xen_dma_adapter_t;

BOOLEAN
XenPci_BIS_TranslateBusAddress(PVOID context, PHYSICAL_ADDRESS bus_address, ULONG length, PULONG address_space, PPHYSICAL_ADDRESS translated_address)
{
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(length);
  /* actually this isn't right - should look up the gref for the physical address and work backwards from that */
  FUNCTION_ENTER();
  if (*address_space != 0)
  {
    KdPrint((__DRIVER_NAME "      Cannot map I/O space\n"));
    FUNCTION_EXIT();
    return FALSE;
  }
  *translated_address = bus_address;
  FUNCTION_EXIT();
  return TRUE;
}

static VOID
XenPci_DOP_PutDmaAdapter(PDMA_ADAPTER dma_adapter)
{
  xen_dma_adapter_t *xen_dma_adapter = (xen_dma_adapter_t *)dma_adapter;
  
  FUNCTION_ENTER();

  ASSERT(!xen_dma_adapter->map_register_base);
  ASSERT(!xen_dma_adapter->queued_map_register_base);
  if (xen_dma_adapter->dma_extension)
    ObDereferenceObject(xen_dma_adapter->dma_extension_driver);
  ExFreePoolWithTag(xen_dma_adapter->adapter_object.DmaHeader.DmaOperations, XENPCI_POOL_TAG);
  ExFreePoolWithTag(xen_dma_adapter, XENPCI_POOL_TAG);
  
  FUNCTION_EXIT();

  return;
}

static PVOID
XenPci_DOP_AllocateCommonBuffer(
  PDMA_ADAPTER DmaAdapter,
  ULONG Length,
  PPHYSICAL_ADDRESS LogicalAddress,
  BOOLEAN CacheEnabled
)
{
  xen_dma_adapter_t *xen_dma_adapter = (xen_dma_adapter_t *)DmaAdapter;
  PXENPCI_DEVICE_DATA xpdd;
  PVOID buffer;
  PFN_NUMBER pfn;
  grant_ref_t gref;
  
  UNREFERENCED_PARAMETER(CacheEnabled);
  
  FUNCTION_ENTER();
  //KdPrint((__DRIVER_NAME "     Length = %d\n", Length));
  
  xpdd = GetXpdd(xen_dma_adapter->xppdd->wdf_device_bus_fdo);

  buffer = ExAllocatePoolWithTag(NonPagedPool, Length, XENPCI_POOL_TAG);
  //KdPrint((__DRIVER_NAME "     buffer = %p\n", buffer));

  ASSERT(buffer); /* lazy */

  pfn = (PFN_NUMBER)(MmGetPhysicalAddress(buffer).QuadPart >> PAGE_SHIFT);
  //KdPrint((__DRIVER_NAME "     pfn = %08x\n", (ULONG)pfn));
  ASSERT(pfn); /* lazy */
  
  gref = (grant_ref_t)GntTbl_GrantAccess(xpdd, 0, (ULONG)pfn, FALSE, INVALID_GRANT_REF);
  //KdPrint((__DRIVER_NAME "     gref = %08x\n", (ULONG)gref));
  ASSERT(gref != INVALID_GRANT_REF); /* lazy */

  LogicalAddress->QuadPart = (gref << PAGE_SHIFT) | (PtrToUlong(buffer) & (PAGE_SIZE - 1));
  KdPrint((__DRIVER_NAME "     logical = %08x%08x\n", LogicalAddress->HighPart, LogicalAddress->LowPart));
  
  FUNCTION_EXIT();
  
  return buffer;
}

static VOID
XenPci_DOP_FreeCommonBuffer(
  PDMA_ADAPTER dma_adapter,
  ULONG length,
  PHYSICAL_ADDRESS logical_address,
  PVOID virtual_address,
  BOOLEAN cache_enabled
)
{
  xen_dma_adapter_t *xen_dma_adapter = (xen_dma_adapter_t *)dma_adapter;
  PXENPCI_DEVICE_DATA xpdd;
  grant_ref_t gref;

  UNREFERENCED_PARAMETER(dma_adapter);
  UNREFERENCED_PARAMETER(length);
  UNREFERENCED_PARAMETER(cache_enabled);

//  FUNCTION_ENTER();

  xpdd = GetXpdd(xen_dma_adapter->xppdd->wdf_device_bus_fdo);
  gref = (grant_ref_t)(logical_address.QuadPart >> PAGE_SHIFT);
  //KdPrint((__DRIVER_NAME "     F Releasing Grant Ref %d\n", gref));
  GntTbl_EndAccess(xpdd, gref, FALSE);
  //KdPrint((__DRIVER_NAME "     F Released Grant Ref\n"));
  ExFreePoolWithTag(virtual_address, XENPCI_POOL_TAG);

//  FUNCTION_EXIT();
}

static VOID
XenPci_ExecuteMapRegisterDma(
  PDMA_ADAPTER dma_adapter,
  map_register_base_t *map_register_base)
{
  IO_ALLOCATION_ACTION action;

  UNREFERENCED_PARAMETER(dma_adapter);
  
  action = map_register_base->execution_routine(map_register_base->device_object, map_register_base->current_irp, map_register_base, map_register_base->context);
  
  switch (action)
  {
  case KeepObject:
    KdPrint((__DRIVER_NAME "     KeepObject\n"));
    ASSERT(FALSE);
    break;
  case DeallocateObject:
    KdPrint((__DRIVER_NAME "     DeallocateObject\n"));
    ASSERT(FALSE);
    break;
  case DeallocateObjectKeepRegisters:
    //KdPrint((__DRIVER_NAME "     DeallocateObjectKeepRegisters\n"));
    break;
  default:
    KdPrint((__DRIVER_NAME "     Unknown action %d\n", action));
    ASSERT(FALSE);
    break;
  }
  return;
}

static NTSTATUS
XenPci_DOP_AllocateAdapterChannel(
    IN PDMA_ADAPTER dma_adapter,
    IN PDEVICE_OBJECT device_object,
    IN ULONG NumberOfMapRegisters,
    IN PDRIVER_CONTROL ExecutionRoutine,
    IN PVOID Context
    )
{
  xen_dma_adapter_t *xen_dma_adapter = (xen_dma_adapter_t *)dma_adapter;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xen_dma_adapter->xppdd->wdf_device_bus_fdo);
  ULONG i;
  map_register_base_t *map_register_base;
  
  UNREFERENCED_PARAMETER(dma_adapter);
  
  //FUNCTION_ENTER();
  
  ASSERT(!xen_dma_adapter->queued_map_register_base);

  map_register_base = ExAllocatePoolWithTag(NonPagedPool, 
    FIELD_OFFSET(map_register_base_t, regs) + NumberOfMapRegisters * sizeof(map_register_t), XENPCI_POOL_TAG);
  if (!map_register_base)
  {
    KdPrint((__DRIVER_NAME "     Cannot allocate memory for map_register_base\n"));
    //FUNCTION_EXIT();
    return STATUS_INSUFFICIENT_RESOURCES;
  }
  //KdPrint((__DRIVER_NAME "     Alloc %p\n", map_register_base));
  /* we should also allocate a single page of memory here for remap purposes as once we allocate the map registers there is no failure allowed */
  map_register_base->device_object = device_object;
  map_register_base->current_irp = device_object->CurrentIrp;
  map_register_base->total_map_registers = NumberOfMapRegisters;
  map_register_base->execution_routine = ExecutionRoutine;
  map_register_base->context = Context;  
  map_register_base->count = 0;
  
  for (i = 0; i < NumberOfMapRegisters; i++)
  {
    map_register_base->regs[i].gref = GntTbl_GetRef(xpdd);
    if (map_register_base->regs[i].gref == INVALID_GRANT_REF)
    {
      KdPrint((__DRIVER_NAME "     Not enough gref's for AdapterChannel list\n"));
      /* go back through the list and free the ones we allocated */
      NumberOfMapRegisters = i;
      for (i = 0; i < NumberOfMapRegisters; i++)
      {
        GntTbl_PutRef(xpdd, map_register_base->regs[i].gref);
      }
      //KdPrint((__DRIVER_NAME "     B Free %p\n", map_register_base));
      ExFreePoolWithTag(map_register_base, XENPCI_POOL_TAG);
      return STATUS_INSUFFICIENT_RESOURCES;
    }
    map_register_base->regs[i].map_type = MAP_TYPE_INVALID;
    map_register_base->regs[i].aligned_buffer = NULL;
    map_register_base->regs[i].unaligned_buffer = NULL;
    map_register_base->regs[i].copy_length = 0;
  }
  
  KeAcquireSpinLockAtDpcLevel(&xen_dma_adapter->lock);
  if (xen_dma_adapter->map_register_base)
  {
    xen_dma_adapter->queued_map_register_base = map_register_base;
    KeReleaseSpinLockFromDpcLevel(&xen_dma_adapter->lock);
  }
  else
  {
    xen_dma_adapter->map_register_base = map_register_base;
    KeReleaseSpinLockFromDpcLevel(&xen_dma_adapter->lock);
    XenPci_ExecuteMapRegisterDma(dma_adapter, map_register_base);
  }

  //FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static BOOLEAN
XenPci_DOP_FlushAdapterBuffers(
  PDMA_ADAPTER dma_adapter,
  PMDL mdl,
  PVOID MapRegisterBase,
  PVOID CurrentVa,
  ULONG Length,
  BOOLEAN write_to_device)
{
  xen_dma_adapter_t *xen_dma_adapter = (xen_dma_adapter_t *)dma_adapter;
  //PXENPCI_DEVICE_DATA xpdd = GetXpdd(xen_dma_adapter->xppdd->wdf_device_bus_fdo);
  map_register_base_t *map_register_base = MapRegisterBase;
  map_register_t *map_register;
  ULONG i;
  
  UNREFERENCED_PARAMETER(xen_dma_adapter);
  UNREFERENCED_PARAMETER(mdl);
  UNREFERENCED_PARAMETER(CurrentVa);
  UNREFERENCED_PARAMETER(Length);

  //FUNCTION_ENTER();
  
  ASSERT(xen_dma_adapter->map_register_base);
  ASSERT(xen_dma_adapter->map_register_base == map_register_base);
  
  for (i = 0; i < map_register_base->count; i++)
  {
    map_register = &map_register_base->regs[i];
    if (map_register->map_type == MAP_TYPE_REMAPPED && !write_to_device)
      memcpy(map_register->unaligned_buffer, map_register->aligned_buffer, map_register->copy_length);
  }
  //FUNCTION_EXIT();
  
  return TRUE;
}

static VOID
XenPci_DOP_FreeAdapterChannel(
    IN PDMA_ADAPTER  DmaAdapter
    )
{
  UNREFERENCED_PARAMETER(DmaAdapter);

  FUNCTION_ENTER();
  FUNCTION_EXIT();
}

static VOID
XenPci_DOP_FreeMapRegisters(
  PDMA_ADAPTER dma_adapter,
  PVOID MapRegisterBase,
  ULONG NumberOfMapRegisters)
{
  xen_dma_adapter_t *xen_dma_adapter = (xen_dma_adapter_t *)dma_adapter;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xen_dma_adapter->xppdd->wdf_device_bus_fdo);
  map_register_base_t *map_register_base = MapRegisterBase;
  map_register_t *map_register;
  ULONG i;

  UNREFERENCED_PARAMETER(NumberOfMapRegisters);
  
  //FUNCTION_ENTER();

  if (!map_register_base)
  {
    /* i'm not sure if this is ideal here, but NDIS definitely does it */
    return;
  }

  ASSERT(xen_dma_adapter->map_register_base == map_register_base);  
  ASSERT(map_register_base->total_map_registers == NumberOfMapRegisters);

  for (i = 0; i < map_register_base->total_map_registers; i++)
  {
    map_register = &map_register_base->regs[i];
    GntTbl_EndAccess(xpdd, map_register->gref, FALSE);
    switch (map_register->map_type)
    {
    case MAP_TYPE_INVALID:
      break;
    case MAP_TYPE_REMAPPED:
      ExFreePoolWithTag(map_register->aligned_buffer, XENPCI_POOL_TAG);
      break;
    case MAP_TYPE_MDL:
      break;
    case MAP_TYPE_VIRTUAL:
      break;
    }
  }
  ExFreePoolWithTag(map_register_base, XENPCI_POOL_TAG);

  KeAcquireSpinLockAtDpcLevel(&xen_dma_adapter->lock);
  if (xen_dma_adapter->queued_map_register_base)
  {
    xen_dma_adapter->map_register_base = xen_dma_adapter->queued_map_register_base;
    xen_dma_adapter->queued_map_register_base = NULL;
    KeReleaseSpinLockFromDpcLevel(&xen_dma_adapter->lock);
    XenPci_ExecuteMapRegisterDma(dma_adapter, xen_dma_adapter->map_register_base);
  }
  else
  {
    xen_dma_adapter->map_register_base = NULL;
    KeReleaseSpinLockFromDpcLevel(&xen_dma_adapter->lock);
  }
  
  //FUNCTION_EXIT();
}

static PHYSICAL_ADDRESS
XenPci_DOP_MapTransfer(
    PDMA_ADAPTER dma_adapter,
    PMDL mdl,
    PVOID MapRegisterBase,
    PVOID CurrentVa,
    PULONG Length,
    BOOLEAN WriteToDevice)
{
  xen_dma_adapter_t *xen_dma_adapter = (xen_dma_adapter_t *)dma_adapter;
  PXENPCI_DEVICE_DATA xpdd = GetXpdd(xen_dma_adapter->xppdd->wdf_device_bus_fdo);
  map_register_base_t *map_register_base = MapRegisterBase;
  map_register_t *map_register = &map_register_base->regs[map_register_base->count];
  PDEVICE_OBJECT device_object = map_register_base->device_object;
  ULONG page_offset;
  PFN_NUMBER pfn;
  //grant_ref_t gref;
  PUCHAR ptr;
  ULONG mdl_offset;
  ULONG pfn_index;

  //FUNCTION_ENTER();

  //KdPrint((__DRIVER_NAME "     Mdl = %p, MapRegisterBase = %p, MdlVa = %p, CurrentVa = %p, Length = %d\n",
  //  mdl, MapRegisterBase, MmGetMdlVirtualAddress(mdl), CurrentVa, *Length));

  ASSERT(mdl);
  ASSERT(map_register_base);
  ASSERT(xen_dma_adapter->map_register_base == map_register_base);  
  ASSERT(map_register_base->count < map_register_base->total_map_registers);
  
  if (xen_dma_adapter->dma_extension)
  {
    if (xen_dma_adapter->dma_extension->need_virtual_address && xen_dma_adapter->dma_extension->need_virtual_address(device_object->CurrentIrp))
    {
      map_register->map_type = MAP_TYPE_VIRTUAL;
    }
    else
    {
      if (xen_dma_adapter->dma_extension->get_alignment)
      {
        ULONG alignment = xen_dma_adapter->dma_extension->get_alignment(device_object->CurrentIrp);
        if ((MmGetMdlByteOffset(mdl) & (alignment - 1)) || (MmGetMdlByteCount(mdl) & (alignment - 1)))
        {
          map_register->map_type = MAP_TYPE_REMAPPED;
        }
        else
        {
          map_register->map_type = MAP_TYPE_MDL;
        }
      }
      else
      {
        map_register->map_type = MAP_TYPE_MDL;
      }
    }
  }
  else
  {
    map_register->map_type = MAP_TYPE_MDL;
  }

  switch (map_register->map_type)
  {
  case MAP_TYPE_MDL:
    //KdPrint((__DRIVER_NAME "     MAP_TYPE_MDL\n"));
    mdl_offset = (ULONG)((UINT_PTR)CurrentVa - (UINT_PTR)MmGetMdlVirtualAddress(mdl));
    page_offset = PtrToUlong(CurrentVa) & (PAGE_SIZE - 1);
    *Length = min(*Length, PAGE_SIZE - page_offset);
    pfn_index = (ULONG)(((UINT_PTR)CurrentVa >> PAGE_SHIFT) - ((UINT_PTR)MmGetMdlVirtualAddress(mdl) >> PAGE_SHIFT));
    //KdPrint((__DRIVER_NAME "     mdl_offset = %d, page_offset = %d, length = %d, pfn_index = %d\n",
    //  mdl_offset, page_offset, *Length, pfn_index));
    pfn = MmGetMdlPfnArray(mdl)[pfn_index];
    //KdPrint((__DRIVER_NAME "     B Requesting Grant Ref\n"));
    
    //ASSERT(map_register->gref != INVALID_GRANT_REF);
    GntTbl_GrantAccess(xpdd, 0, (ULONG)pfn, FALSE, map_register->gref);
    //KdPrint((__DRIVER_NAME "     B Got Grant Ref %d\n", gref));
    map_register->logical.QuadPart = ((LONGLONG)map_register->gref << PAGE_SHIFT) | page_offset;
    map_register_base->count++;
    break;
  case MAP_TYPE_REMAPPED:
    //KdPrint((__DRIVER_NAME "     MAP_TYPE_REMAPPED (MapTransfer)\n"));
    //KdPrint((__DRIVER_NAME "     Mdl = %p, MapRegisterBase = %p, MdlVa = %p, CurrentVa = %p, Length = %d\n",
    //  mdl, MapRegisterBase, MmGetMdlVirtualAddress(mdl), CurrentVa, *Length));
    mdl_offset = (ULONG)((UINT_PTR)CurrentVa - (UINT_PTR)MmGetMdlVirtualAddress(mdl));
    *Length = min(*Length, PAGE_SIZE);
    map_register->aligned_buffer = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENPCI_POOL_TAG);
    ASSERT(map_register->aligned_buffer);
    map_register->unaligned_buffer = MmGetSystemAddressForMdlSafe(mdl, NormalPagePriority);
    ASSERT(map_register->unaligned_buffer); /* lazy */
    map_register->unaligned_buffer = (PUCHAR)map_register->unaligned_buffer + mdl_offset;
    map_register->copy_length = *Length;
    if (WriteToDevice)
      memcpy(map_register->aligned_buffer, map_register->unaligned_buffer, map_register->copy_length);
    pfn = (PFN_NUMBER)(MmGetPhysicalAddress(map_register->aligned_buffer).QuadPart >> PAGE_SHIFT);
    //KdPrint((__DRIVER_NAME "     C Requesting Grant Ref\n"));
    GntTbl_GrantAccess(xpdd, 0, (ULONG)pfn, FALSE, map_register->gref);
    //KdPrint((__DRIVER_NAME "     C Got Grant Ref %d\n", gref));
    map_register->logical.QuadPart = ((LONGLONG)map_register->gref << PAGE_SHIFT);
    map_register_base->count++;
    break;
  case MAP_TYPE_VIRTUAL:
    //KdPrint((__DRIVER_NAME "     MAP_TYPE_VIRTUAL\n"));
    ptr = MmGetSystemAddressForMdlSafe(mdl, NormalPagePriority);
    ASSERT(ptr); /* lazy */
    map_register->logical.QuadPart = (ULONGLONG)ptr;
    map_register_base->count++;
    break;
  default:
    ASSERT(FALSE);
    break;
  }
  
  //KdPrint((__DRIVER_NAME "     logical = %08x:%08x\n", map_register->logical.HighPart, map_register->logical.LowPart));
  //FUNCTION_EXIT();
  return map_register->logical;
}

static ULONG
XenPci_DOP_GetDmaAlignment(
  PDMA_ADAPTER DmaAdapter)
{
  UNREFERENCED_PARAMETER(DmaAdapter);

  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return 0;
}

static ULONG
XenPci_DOP_ReadDmaCounter(
  PDMA_ADAPTER DmaAdapter)
{
  UNREFERENCED_PARAMETER(DmaAdapter);

  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return 0;
}

static VOID
XenPci_DOP_PutScatterGatherList(
    IN PDMA_ADAPTER DmaAdapter,
    IN PSCATTER_GATHER_LIST sg_list,
    IN BOOLEAN WriteToDevice
    )
{
  xen_dma_adapter_t *xen_dma_adapter;
  PXENPCI_DEVICE_DATA xpdd;
  ULONG i;
  sg_extra_t *sg_extra;
  PMDL curr_mdl;
  ULONG offset;
  BOOLEAN active;

  UNREFERENCED_PARAMETER(WriteToDevice);
  
  //FUNCTION_ENTER();

  xen_dma_adapter = (xen_dma_adapter_t *)DmaAdapter;
  ASSERT(xen_dma_adapter);
  xpdd = GetXpdd(xen_dma_adapter->xppdd->wdf_device_bus_fdo);
  
  sg_extra = (sg_extra_t *)((PUCHAR)sg_list + FIELD_OFFSET(SCATTER_GATHER_LIST, Elements) +
    (sizeof(SCATTER_GATHER_ELEMENT)) * sg_list->NumberOfElements);

  switch (sg_extra->map_type)
  {
  case MAP_TYPE_REMAPPED:
    for (i = 0; i < sg_list->NumberOfElements; i++)
    {
      grant_ref_t gref;
      gref = (grant_ref_t)(sg_list->Elements[i].Address.QuadPart >> PAGE_SHIFT);
      GntTbl_EndAccess(xpdd, gref, FALSE);
      sg_list->Elements[i].Address.QuadPart = -1;
    }
    ASSERT(sg_extra->mdl);
    if (!WriteToDevice)
    {
      for (curr_mdl = sg_extra->mdl, offset = 0, active = FALSE; curr_mdl && offset < sg_extra->copy_length; curr_mdl = curr_mdl->Next)
      {
        PVOID mdl_start_va = MmGetMdlVirtualAddress(curr_mdl);
        ULONG mdl_byte_count = MmGetMdlByteCount(curr_mdl);
        ULONG mdl_offset = 0;
        /* need to use <= va + len - 1 to avoid ptr wraparound */
        if ((UINT_PTR)sg_extra->currentva >= (UINT_PTR)mdl_start_va && (UINT_PTR)sg_extra->currentva <= (UINT_PTR)mdl_start_va + mdl_byte_count - 1)
        {
          active = TRUE;
          mdl_byte_count -= (ULONG)((UINT_PTR)sg_extra->currentva - (UINT_PTR)mdl_start_va);
          if (offset + mdl_byte_count > sg_extra->copy_length)
            mdl_byte_count = sg_extra->copy_length - offset;
          mdl_offset = (ULONG)((UINT_PTR)sg_extra->currentva - (UINT_PTR)mdl_start_va);
          mdl_start_va = sg_extra->currentva;
        }
        if (active)
        {
          PVOID unaligned_buffer;
          unaligned_buffer = MmGetSystemAddressForMdlSafe(curr_mdl, NormalPagePriority);
          ASSERT(unaligned_buffer); /* lazy */
          memcpy((PUCHAR)unaligned_buffer + mdl_offset, (PUCHAR)sg_extra->aligned_buffer + offset, mdl_byte_count);
          offset += mdl_byte_count;
        }
      }
      ASSERT(offset == sg_extra->copy_length);
    }
    ExFreePoolWithTag(sg_extra->aligned_buffer, XENPCI_POOL_TAG);
    break;
  case MAP_TYPE_MDL:
    for (i = 0; i < sg_list->NumberOfElements; i++)
    {
      grant_ref_t gref;
      gref = (grant_ref_t)(sg_list->Elements[i].Address.QuadPart >> PAGE_SHIFT);
      GntTbl_EndAccess(xpdd, gref, FALSE);
      sg_list->Elements[i].Address.QuadPart = -1;
    }
    break;
  case MAP_TYPE_VIRTUAL:
    break;
  }
  if (sg_extra->allocated_by_me)
    ExFreePoolWithTag(sg_list, XENPCI_POOL_TAG);
  //FUNCTION_EXIT();
}

static NTSTATUS
XenPci_DOP_CalculateScatterGatherList(
  PDMA_ADAPTER DmaAdapter,
  PMDL Mdl,
  PVOID CurrentVa,
  ULONG Length,
  PULONG ScatterGatherListSize,
  PULONG NumberOfMapRegisters
  )
{
  xen_dma_adapter_t *xen_dma_adapter;
  ULONG elements;
  PMDL curr_mdl;
  
  UNREFERENCED_PARAMETER(CurrentVa);
    
  //FUNCTION_ENTER();
  
  //KdPrint((__DRIVER_NAME "     Mdl = %p\n", Mdl));
  //KdPrint((__DRIVER_NAME "     CurrentVa = %p\n", CurrentVa));
  //KdPrint((__DRIVER_NAME "     Length = %d\n", Length));

  xen_dma_adapter = (xen_dma_adapter_t *)DmaAdapter;

  if (Mdl)
  {
    //if (CurrentVa != MmGetMdlVirtualAddress(Mdl))
    //{
    //  KdPrint((__DRIVER_NAME "     CurrentVa (%p) != MdlVa (%p)\n", CurrentVa, MmGetMdlVirtualAddress(Mdl)));
    //

    //KdPrint((__DRIVER_NAME "     CurrentVa = %p, MdlVa = %p\n", CurrentVa, MmGetMdlVirtualAddress(Mdl)));

    for (curr_mdl = Mdl, elements = 0; curr_mdl; curr_mdl = curr_mdl->Next)
    {
      //KdPrint((__DRIVER_NAME "     curr_mdlVa = %p, curr_mdl size = %d\n", MmGetMdlVirtualAddress(curr_mdl), MmGetMdlByteCount(curr_mdl)));
      elements += ADDRESS_AND_SIZE_TO_SPAN_PAGES(MmGetMdlVirtualAddress(curr_mdl), MmGetMdlByteCount(curr_mdl));
    }
  }
  else
  {
    elements = ADDRESS_AND_SIZE_TO_SPAN_PAGES(0, Length); // + 1;
  }

  if (elements > xen_dma_adapter->adapter_object.MapRegistersPerChannel)
  {
    //KdPrint((__DRIVER_NAME "     elements = %d - too many\n", elements));
    if (NumberOfMapRegisters)
      *NumberOfMapRegisters = 0;
    *ScatterGatherListSize = 0;
    
    return STATUS_INSUFFICIENT_RESOURCES;
  }
  
  *ScatterGatherListSize = FIELD_OFFSET(SCATTER_GATHER_LIST, Elements)
    + sizeof(SCATTER_GATHER_ELEMENT) * elements
    + sizeof(sg_extra_t);
  if (NumberOfMapRegisters)
    *NumberOfMapRegisters = elements;

  //KdPrint((__DRIVER_NAME "     ScatterGatherListSize = %d, NumberOfMapRegisters = %d\n", *ScatterGatherListSize, elements));

  //FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static NTSTATUS
XenPci_DOP_BuildScatterGatherListButDontExecute(
  IN PDMA_ADAPTER DmaAdapter,
  IN PDEVICE_OBJECT DeviceObject,
  IN PMDL Mdl,
  IN PVOID CurrentVa,
  IN ULONG Length,
  IN BOOLEAN WriteToDevice,
  IN PVOID ScatterGatherBuffer,
  IN ULONG ScatterGatherBufferLength,
  BOOLEAN allocated_by_me)
{
  ULONG i;
  PSCATTER_GATHER_LIST sglist = ScatterGatherBuffer;
  PUCHAR ptr;
  ULONG remaining = Length;
  ULONG total_remaining;
  xen_dma_adapter_t *xen_dma_adapter;
  PXENPCI_DEVICE_DATA xpdd;
  sg_extra_t *sg_extra;
  PMDL curr_mdl;
  ULONG map_type;
  ULONG sg_element;
  ULONG offset;
  PFN_NUMBER pfn;
  grant_ref_t gref;
  BOOLEAN active;
  PVOID mdl_start_va;
  ULONG mdl_byte_count;
  ULONG mdl_offset;
  ULONG remapped_bytes = 0;
  
  //FUNCTION_ENTER();
  
  if (!ScatterGatherBuffer)
  {
    KdPrint((__DRIVER_NAME "     NULL ScatterGatherBuffer\n"));
    return STATUS_INVALID_PARAMETER;
  }
  //if (MmGetMdlVirtualAddress(Mdl) != CurrentVa)
  //{
  //  KdPrint((__DRIVER_NAME "     MmGetMdlVirtualAddress = %p, CurrentVa = %p, Length = %d\n", MmGetMdlVirtualAddress(Mdl), CurrentVa, Length));
  //}

  xen_dma_adapter = (xen_dma_adapter_t *)DmaAdapter;
  xpdd = GetXpdd(xen_dma_adapter->xppdd->wdf_device_bus_fdo);

  ASSERT(Mdl);
  
  if (xen_dma_adapter->dma_extension)
  {
    if (xen_dma_adapter->dma_extension->need_virtual_address && xen_dma_adapter->dma_extension->need_virtual_address(DeviceObject->CurrentIrp))
    {
      ASSERT(!Mdl->Next); /* can only virtual a single buffer */
      //ASSERT(MmGetMdlVirtualAddress(Mdl) == CurrentVa);
      map_type = MAP_TYPE_VIRTUAL;
      sglist->NumberOfElements = 1;
    }
    else
    {
      if (xen_dma_adapter->dma_extension->get_alignment)
      {
        ULONG alignment = xen_dma_adapter->dma_extension->get_alignment(DeviceObject->CurrentIrp);

        map_type = MAP_TYPE_MDL;
        sglist->NumberOfElements = 0;
        for (curr_mdl = Mdl, remapped_bytes = 0, active = FALSE; remapped_bytes < Length && curr_mdl; curr_mdl = curr_mdl->Next)
        {
          mdl_start_va = MmGetMdlVirtualAddress(curr_mdl);
          mdl_byte_count = MmGetMdlByteCount(curr_mdl);
          /* need to use <= va + len - 1 to avoid ptr wraparound */
          if ((UINT_PTR)CurrentVa >= (UINT_PTR)mdl_start_va && (UINT_PTR)CurrentVa <= (UINT_PTR)mdl_start_va + mdl_byte_count - 1)
          {
            active = TRUE;
            mdl_byte_count -= (ULONG)((UINT_PTR)CurrentVa - (UINT_PTR)mdl_start_va);
            if (remapped_bytes + mdl_byte_count > Length)
              mdl_byte_count = Length - remapped_bytes;
            mdl_start_va = CurrentVa;
          }
          if (active)
          {
            if (((UINT_PTR)mdl_start_va & (alignment - 1)) || (mdl_byte_count & (alignment - 1)))
              map_type = MAP_TYPE_REMAPPED;
            remapped_bytes += mdl_byte_count;
            if (remapped_bytes > Length)
              remapped_bytes = Length;
          }
        }
        if (remapped_bytes != Length)
        {
          KdPrint((__DRIVER_NAME "     remapped_bytes = %d, Length = %d\n", remapped_bytes, Length));
        }
        //ASSERT(remapped_bytes == Length);
        sglist->NumberOfElements += ADDRESS_AND_SIZE_TO_SPAN_PAGES(NULL, remapped_bytes);
      }
      else
      {
        map_type = MAP_TYPE_MDL;
      }
    }
  }
  else
  {
    map_type = MAP_TYPE_MDL;
  }
  if (map_type == MAP_TYPE_MDL)
  {    
    for (curr_mdl = Mdl, sglist->NumberOfElements = 0, total_remaining = Length, active = FALSE; total_remaining > 0; curr_mdl = curr_mdl->Next)
    {
      ASSERT(curr_mdl);
      mdl_start_va = MmGetMdlVirtualAddress(curr_mdl);
      mdl_byte_count = MmGetMdlByteCount(curr_mdl);
      /* need to use <= va + len - 1 to avoid ptr wraparound */
      if ((UINT_PTR)CurrentVa >= (UINT_PTR)mdl_start_va && (UINT_PTR)CurrentVa <= (UINT_PTR)mdl_start_va + mdl_byte_count - 1)
      {
        active = TRUE;
        mdl_byte_count -= (ULONG)((UINT_PTR)CurrentVa - (UINT_PTR)mdl_start_va);
        mdl_start_va = CurrentVa;
      }
      mdl_byte_count = min(mdl_byte_count, total_remaining);
      if (active && mdl_byte_count)
      {
        sglist->NumberOfElements += ADDRESS_AND_SIZE_TO_SPAN_PAGES(
          mdl_start_va, mdl_byte_count);
        total_remaining -= mdl_byte_count;
      }
    }
  }
  if (ScatterGatherBufferLength < FIELD_OFFSET(SCATTER_GATHER_LIST, Elements) +
    sizeof(SCATTER_GATHER_ELEMENT) * sglist->NumberOfElements + sizeof(sg_extra_t))
  {
    //KdPrint((__DRIVER_NAME "     STATUS_BUFFER_TOO_SMALL (%d < %d)\n", ScatterGatherBufferLength, FIELD_OFFSET(SCATTER_GATHER_LIST, Elements) +
    //  sizeof(SCATTER_GATHER_ELEMENT) * sglist->NumberOfElements + sizeof(sg_extra_t)));
    return STATUS_BUFFER_TOO_SMALL;
  }

  if (map_type != MAP_TYPE_VIRTUAL)
  {
    for (sg_element = 0; sg_element < sglist->NumberOfElements; sg_element++)
    {
      gref = GntTbl_GetRef(xpdd);
      if (gref == INVALID_GRANT_REF)
      {
        KdPrint((__DRIVER_NAME "     Not enough gref's for SG list\n"));
        /* go back through the list and free the ones we allocated */
        sglist->NumberOfElements = sg_element;
        for (sg_element = 0; sg_element < sglist->NumberOfElements; sg_element++)
        {
          gref = (grant_ref_t)(sglist->Elements[sg_element].Address.QuadPart >> PAGE_SHIFT);
          GntTbl_PutRef(xpdd, gref);
        }
        return STATUS_INSUFFICIENT_RESOURCES;
      }
      sglist->Elements[sg_element].Address.QuadPart = ((LONGLONG)gref << PAGE_SHIFT);
    }
  }
  
  sg_extra = (sg_extra_t *)((PUCHAR)sglist + FIELD_OFFSET(SCATTER_GATHER_LIST, Elements) +
    (sizeof(SCATTER_GATHER_ELEMENT)) * sglist->NumberOfElements);

  sg_extra->allocated_by_me = allocated_by_me;
  
  sg_extra->map_type = map_type;
  switch (map_type)
  {
  case MAP_TYPE_MDL:
    //KdPrint((__DRIVER_NAME "     MAP_TYPE_MDL - %p\n", MmGetMdlVirtualAddress(Mdl)));
    total_remaining = Length;
    for (sg_element = 0, curr_mdl = Mdl, active = FALSE; total_remaining > 0; curr_mdl = curr_mdl->Next)
    {
      ASSERT(curr_mdl);
      mdl_start_va = MmGetMdlVirtualAddress(curr_mdl);
      mdl_byte_count = MmGetMdlByteCount(curr_mdl);
      /* need to use <= va + len - 1 to avoid ptr wraparound */
      if ((UINT_PTR)CurrentVa >= (UINT_PTR)mdl_start_va && (UINT_PTR)CurrentVa <= (UINT_PTR)mdl_start_va + mdl_byte_count - 1)
      {
        active = TRUE;
        mdl_byte_count -= (ULONG)((UINT_PTR)CurrentVa - (UINT_PTR)mdl_start_va);
        mdl_start_va = CurrentVa;
      }
      if (active && mdl_byte_count)
      {
        ULONG pfn_offset;
        remaining = min(mdl_byte_count, total_remaining);
        offset = (ULONG)((UINT_PTR)mdl_start_va & (PAGE_SIZE - 1));
        pfn_offset = (ULONG)(((UINT_PTR)mdl_start_va >> PAGE_SHIFT) - ((UINT_PTR)MmGetMdlVirtualAddress(curr_mdl) >> PAGE_SHIFT));
        //for (i = 0; i < ADDRESS_AND_SIZE_TO_SPAN_PAGES(mdl_start_va, mdl_byte_count); i++)
        for (i = 0; remaining > 0; i++)
        {
          pfn = MmGetMdlPfnArray(curr_mdl)[pfn_offset + i];
          //ASSERT((grant_ref_t)(sglist->Elements[sg_element].Address.QuadPart >> PAGE_SHIFT) != INVALID_GRANT_REF);
          if ((grant_ref_t)(sglist->Elements[sg_element].Address.QuadPart >> PAGE_SHIFT) == INVALID_GRANT_REF)
            KdPrint((__DRIVER_NAME "     GGG\n"));

          GntTbl_GrantAccess(xpdd, 0, (ULONG)pfn, FALSE,
            (grant_ref_t)(sglist->Elements[sg_element].Address.QuadPart >> PAGE_SHIFT));
          sglist->Elements[sg_element].Address.QuadPart |= (LONGLONG)offset;
          sglist->Elements[sg_element].Length = min(min(PAGE_SIZE - offset, remaining), total_remaining);
          total_remaining -= sglist->Elements[sg_element].Length;
          remaining -= sglist->Elements[sg_element].Length;
          offset = 0;
          sg_element++;
        }
      }
    }
    if (sg_element != sglist->NumberOfElements)
    {
      KdPrint((__DRIVER_NAME "     sg_element = %d, sglist->NumberOfElements = %d\n", sg_element, sglist->NumberOfElements));
      KdPrint((__DRIVER_NAME "     CurrentVa = %p, Length = %d\n", CurrentVa, Length));
for (curr_mdl = Mdl; curr_mdl; curr_mdl = curr_mdl->Next)
{
  KdPrint((__DRIVER_NAME "     Mdl = %p, VirtualAddress = %p, ByteCount = %d\n", Mdl, MmGetMdlVirtualAddress(curr_mdl), MmGetMdlByteCount(curr_mdl)));
}
    }
    ASSERT(sg_element == sglist->NumberOfElements);
    break;
  case MAP_TYPE_REMAPPED:
    sg_extra->aligned_buffer = ExAllocatePoolWithTag(NonPagedPool, max(remapped_bytes, PAGE_SIZE), XENPCI_POOL_TAG);
    if (!sg_extra->aligned_buffer)
    {
      KdPrint((__DRIVER_NAME "     MAP_TYPE_REMAPPED buffer allocation failed - requested va = %p, length = %d\n", MmGetMdlVirtualAddress(Mdl), remapped_bytes));
      return STATUS_INSUFFICIENT_RESOURCES;
    }
//KdPrint((__DRIVER_NAME "     MAP_TYPE_REMAPPED - %p, %d\n", sg_extra->aligned_buffer, remapped_bytes));
//KdPrint((__DRIVER_NAME "     CurrentVa = %p, Length = %d\n", CurrentVa, Length));
//for (curr_mdl = Mdl; curr_mdl; curr_mdl = curr_mdl->Next)
//{
//  KdPrint((__DRIVER_NAME "     Mdl = %p, VirtualAddress = %p, ByteCount = %d\n", Mdl, MmGetMdlVirtualAddress(curr_mdl), MmGetMdlByteCount(curr_mdl)));
//}
    sg_extra->mdl = Mdl;
    sg_extra->currentva = CurrentVa;
    sg_extra->copy_length = remapped_bytes;

    if (WriteToDevice)
    {
      for (curr_mdl = Mdl, offset = 0, active = FALSE; curr_mdl && offset < Length; curr_mdl = curr_mdl->Next)
      {
        mdl_start_va = MmGetMdlVirtualAddress(curr_mdl);
        mdl_byte_count = MmGetMdlByteCount(curr_mdl);
        mdl_offset = 0;
        /* need to use <= va + len - 1 to avoid ptr wraparound */
        if ((UINT_PTR)CurrentVa >= (UINT_PTR)mdl_start_va && (UINT_PTR)CurrentVa <= (UINT_PTR)mdl_start_va + mdl_byte_count - 1)
        {
          active = TRUE;
          mdl_byte_count -= (ULONG)((UINT_PTR)CurrentVa - (UINT_PTR)mdl_start_va);
          if (offset + mdl_byte_count > Length)
            mdl_byte_count = Length - offset;            
          mdl_offset = (ULONG)((UINT_PTR)CurrentVa - (UINT_PTR)mdl_start_va);
          mdl_start_va = CurrentVa;
        }
        if (active)
        {
          PVOID unaligned_buffer;
          unaligned_buffer = (PUCHAR)MmGetSystemAddressForMdlSafe(curr_mdl, NormalPagePriority);
          ASSERT(unaligned_buffer); /* lazy */
          memcpy((PUCHAR)sg_extra->aligned_buffer + offset, (PUCHAR)unaligned_buffer + mdl_offset, mdl_byte_count);
          offset += mdl_byte_count;
        }
      }
    }
    for (sg_element = 0, remaining = remapped_bytes; 
      sg_element < ADDRESS_AND_SIZE_TO_SPAN_PAGES(sg_extra->aligned_buffer, remapped_bytes); sg_element++)
    {
      pfn = (PFN_NUMBER)(MmGetPhysicalAddress((PUCHAR)sg_extra->aligned_buffer + (sg_element << PAGE_SHIFT)).QuadPart >> PAGE_SHIFT);
      //ASSERT((grant_ref_t)(sglist->Elements[sg_element].Address.QuadPart >> PAGE_SHIFT) != INVALID_GRANT_REF);
      if ((grant_ref_t)(sglist->Elements[sg_element].Address.QuadPart >> PAGE_SHIFT) == INVALID_GRANT_REF)
        KdPrint((__DRIVER_NAME "     HHH\n"));
      GntTbl_GrantAccess(xpdd, 0, (ULONG)pfn, FALSE,
        (grant_ref_t)(sglist->Elements[sg_element].Address.QuadPart >> PAGE_SHIFT));
      sglist->Elements[sg_element].Length = min(PAGE_SIZE, remaining);
      remaining -= sglist->Elements[sg_element].Length;
    }
    break;
  case MAP_TYPE_VIRTUAL:
    ptr = MmGetSystemAddressForMdlSafe(Mdl, NormalPagePriority);
    ASSERT(ptr); /* lazy */
    sglist->Elements[0].Address.QuadPart = (ULONGLONG)ptr + ((UINT_PTR)CurrentVa - (UINT_PTR)MmGetMdlVirtualAddress(Mdl));
    sglist->Elements[0].Length = Length;
    //KdPrint((__DRIVER_NAME "     MAP_TYPE_VIRTUAL - %08x\n", sglist->Elements[0].Address.LowPart));
    break;
  default:
    KdPrint((__DRIVER_NAME "     map_type = %d\n", map_type));
    break;
  }
  //FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static NTSTATUS
XenPci_DOP_BuildScatterGatherList(
  IN PDMA_ADAPTER DmaAdapter,
  IN PDEVICE_OBJECT DeviceObject,
  IN PMDL Mdl,
  IN PVOID CurrentVa,
  IN ULONG Length,
  IN PDRIVER_LIST_CONTROL ExecutionRoutine,
  IN PVOID Context,
  IN BOOLEAN WriteToDevice,
  IN PVOID ScatterGatherBuffer,
  IN ULONG ScatterGatherBufferLength)
{
  NTSTATUS status;
  
  status = XenPci_DOP_BuildScatterGatherListButDontExecute(DmaAdapter, DeviceObject, Mdl, CurrentVa, Length, WriteToDevice, ScatterGatherBuffer, ScatterGatherBufferLength, FALSE);
  
  if (NT_SUCCESS(status))
    ExecutionRoutine(DeviceObject, DeviceObject->CurrentIrp, ScatterGatherBuffer, Context);

  //FUNCTION_EXIT();
  
  return status;
}

static NTSTATUS
XenPci_DOP_GetScatterGatherList(
  PDMA_ADAPTER DmaAdapter,
  PDEVICE_OBJECT DeviceObject,
  PMDL Mdl,
  PVOID CurrentVa,
  ULONG Length,
  PDRIVER_LIST_CONTROL ExecutionRoutine,
  PVOID Context,
  BOOLEAN WriteToDevice)
{
  NTSTATUS status;
  ULONG list_size;
  ULONG map_registers;
  PSCATTER_GATHER_LIST sg_list;
  
  //FUNCTION_ENTER();

  status = XenPci_DOP_CalculateScatterGatherList(DmaAdapter, Mdl, CurrentVa, Length, &list_size, &map_registers);
  if (!NT_SUCCESS(status))
  {
    //FUNCTION_EXIT();
    return status;
  }

  sg_list = ExAllocatePoolWithTag(NonPagedPool, list_size, XENPCI_POOL_TAG);
  if (!sg_list)
  {
    KdPrint((__DRIVER_NAME "     Cannot allocate memory for sg_list\n"));
    //FUNCTION_EXIT();
    return STATUS_INSUFFICIENT_RESOURCES;
  }
    
  status = XenPci_DOP_BuildScatterGatherListButDontExecute(DmaAdapter, DeviceObject, Mdl, CurrentVa, Length, WriteToDevice, sg_list, list_size, TRUE);
  
  if (NT_SUCCESS(status))
  {
    /* sg_list is free'd via PutScatterGatherList later */
    ExecutionRoutine(DeviceObject, DeviceObject->CurrentIrp, sg_list, Context);
  }
  else
    ExFreePoolWithTag(sg_list, XENPCI_POOL_TAG);
  
  //FUNCTION_EXIT();
  
  return status;
}

static NTSTATUS
XenPci_DOP_BuildMdlFromScatterGatherList(
  PDMA_ADAPTER DmaAdapter,
  PSCATTER_GATHER_LIST ScatterGather,
  PMDL OriginalMdl,
  PMDL *TargetMdl)
{
  NTSTATUS status = STATUS_SUCCESS;
  UNREFERENCED_PARAMETER(DmaAdapter);
  UNREFERENCED_PARAMETER(ScatterGather);
  UNREFERENCED_PARAMETER(OriginalMdl);
  UNREFERENCED_PARAMETER(TargetMdl);

  FUNCTION_ENTER();
  
  if (OriginalMdl)
  {
    *TargetMdl = OriginalMdl;
  }
  else
  {
    *TargetMdl = NULL;
    status = STATUS_INVALID_PARAMETER;
  }
  
  FUNCTION_EXIT();
  
  return status;
}

PDMA_ADAPTER
XenPci_BIS_GetDmaAdapter(PVOID context, PDEVICE_DESCRIPTION device_description, PULONG number_of_map_registers)
{
  xen_dma_adapter_t *xen_dma_adapter;
  PDEVICE_OBJECT curr, prev;
  PDRIVER_OBJECT fdo_driver_object;
  PVOID fdo_driver_extension;
  
  UNREFERENCED_PARAMETER(device_description);
  
  FUNCTION_ENTER();

  KdPrint((__DRIVER_NAME "     IRQL = %d\n", KeGetCurrentIrql()));
  KdPrint((__DRIVER_NAME "     Device Description = %p:\n", device_description));
  KdPrint((__DRIVER_NAME "      Version  = %d\n", device_description->Version));
  KdPrint((__DRIVER_NAME "      Master = %d\n", device_description->Master));
  KdPrint((__DRIVER_NAME "      ScatterGather = %d\n", device_description->ScatterGather));
  KdPrint((__DRIVER_NAME "      DemandMode = %d\n", device_description->DemandMode));
  KdPrint((__DRIVER_NAME "      AutoInitialize = %d\n", device_description->AutoInitialize));
  KdPrint((__DRIVER_NAME "      Dma32BitAddresses = %d\n", device_description->Dma32BitAddresses));
  KdPrint((__DRIVER_NAME "      IgnoreCount = %d\n", device_description->IgnoreCount));
  KdPrint((__DRIVER_NAME "      Dma64BitAddresses = %d\n", device_description->Dma64BitAddresses));
  KdPrint((__DRIVER_NAME "      BusNumber = %d\n", device_description->BusNumber));
  KdPrint((__DRIVER_NAME "      DmaChannel = %d\n", device_description->DmaChannel));
  KdPrint((__DRIVER_NAME "      InterfaceType = %d\n", device_description->InterfaceType));
  KdPrint((__DRIVER_NAME "      DmaWidth = %d\n", device_description->DmaWidth));
  KdPrint((__DRIVER_NAME "      DmaSpeed = %d\n", device_description->DmaSpeed));
  KdPrint((__DRIVER_NAME "      MaximumLength = %d\n", device_description->MaximumLength));
  KdPrint((__DRIVER_NAME "      DmaPort = %d\n", device_description->DmaPort));
  
  if (!device_description->Master)
    return NULL;
/*
we have to allocate PAGE_SIZE bytes here because Windows thinks this is
actually an ADAPTER_OBJECT, and then the verifier crashes because
Windows accessed beyond the end of the structure :(
*/
  xen_dma_adapter = ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENPCI_POOL_TAG);
  ASSERT(xen_dma_adapter);
  RtlZeroMemory(xen_dma_adapter, PAGE_SIZE);
  
  switch(device_description->Version)
  {
  case DEVICE_DESCRIPTION_VERSION1:
    xen_dma_adapter->adapter_object.DmaHeader.Version = 1;
    break;
  case DEVICE_DESCRIPTION_VERSION: /* ignore what the docs say here - DEVICE_DESCRIPTION_VERSION appears to mean the latest version */
  case DEVICE_DESCRIPTION_VERSION2:
    xen_dma_adapter->adapter_object.DmaHeader.Version = 2;
    break;
  default:
    KdPrint((__DRIVER_NAME "     Unsupported device description version %d\n", device_description->Version));
    ExFreePoolWithTag(xen_dma_adapter, XENPCI_POOL_TAG);
    return NULL;
  }
    
  xen_dma_adapter->xppdd = context;
  xen_dma_adapter->dma_extension = NULL;

  KdPrint((__DRIVER_NAME "     About to call IoGetAttachedDeviceReference\n"));
  curr = IoGetAttachedDeviceReference(WdfDeviceWdmGetDeviceObject(xen_dma_adapter->xppdd->wdf_device));
  KdPrint((__DRIVER_NAME "     Before start of loop - curr = %p\n", curr));
  while (curr != NULL)
  {
    fdo_driver_object = curr->DriverObject;
    if (fdo_driver_object)
    {
      ObReferenceObject(fdo_driver_object);
      fdo_driver_extension = IoGetDriverObjectExtension(fdo_driver_object, UlongToPtr(XEN_DMA_DRIVER_EXTENSION_MAGIC));
      if (fdo_driver_extension)
      {
        xen_dma_adapter->dma_extension_driver = fdo_driver_object; /* so we can dereference it on putdmaadapter */
        xen_dma_adapter->dma_extension = (dma_driver_extension_t *)fdo_driver_extension;
        ObDereferenceObject(curr);
        break;
      }
      else
      {
        ObDereferenceObject(fdo_driver_object);
      }
    }
    prev = curr;
    curr = IoGetLowerDeviceObject(curr);
    ObDereferenceObject(prev);
  }
  KdPrint((__DRIVER_NAME "     End of loop\n"));

  xen_dma_adapter->adapter_object.DmaHeader.Size = sizeof(DMA_ADAPTER); //sizeof(X_ADAPTER_OBJECT); //xen_dma_adapter_t);
  xen_dma_adapter->adapter_object.MasterAdapter = NULL;
  if (xen_dma_adapter->dma_extension && xen_dma_adapter->dma_extension->max_sg_elements)
  {
    xen_dma_adapter->adapter_object.MapRegistersPerChannel = xen_dma_adapter->dma_extension->max_sg_elements;
  }
  else
  {
    xen_dma_adapter->adapter_object.MapRegistersPerChannel = 256;
  }
  xen_dma_adapter->adapter_object.AdapterBaseVa = NULL;
  xen_dma_adapter->adapter_object.MapRegisterBase = NULL;
  xen_dma_adapter->adapter_object.NumberOfMapRegisters = 0;
  xen_dma_adapter->adapter_object.CommittedMapRegisters = 0;
  xen_dma_adapter->adapter_object.CurrentWcb = NULL;
  KeInitializeDeviceQueue(&xen_dma_adapter->adapter_object.ChannelWaitQueue);
  xen_dma_adapter->adapter_object.RegisterWaitQueue = NULL;
  InitializeListHead(&xen_dma_adapter->adapter_object.AdapterQueue);
  KeInitializeSpinLock(&xen_dma_adapter->adapter_object.SpinLock);
  xen_dma_adapter->adapter_object.MapRegisters = NULL;
  xen_dma_adapter->adapter_object.PagePort = NULL;
  xen_dma_adapter->adapter_object.ChannelNumber = 0xff;
  xen_dma_adapter->adapter_object.AdapterNumber = 0;
  xen_dma_adapter->adapter_object.DmaPortAddress = 0;
  xen_dma_adapter->adapter_object.AdapterMode = 0;
  xen_dma_adapter->adapter_object.NeedsMapRegisters = FALSE; /* when true this causes a crash in the crash dump path */
  xen_dma_adapter->adapter_object.MasterDevice = 1;
  xen_dma_adapter->adapter_object.Width16Bits = 0;
  xen_dma_adapter->adapter_object.ScatterGather = device_description->ScatterGather;
  xen_dma_adapter->adapter_object.IgnoreCount = device_description->IgnoreCount;
  xen_dma_adapter->adapter_object.Dma32BitAddresses = device_description->Dma32BitAddresses;
  xen_dma_adapter->adapter_object.Dma64BitAddresses = device_description->Dma64BitAddresses;
  InitializeListHead(&xen_dma_adapter->adapter_object.AdapterList);  
  
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations = ExAllocatePoolWithTag(NonPagedPool, sizeof(DMA_OPERATIONS), XENPCI_POOL_TAG);
  ASSERT(xen_dma_adapter->adapter_object.DmaHeader.DmaOperations);
  if (xen_dma_adapter->adapter_object.DmaHeader.Version == 1)
  {
    xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->Size = FIELD_OFFSET(DMA_OPERATIONS, CalculateScatterGatherList);
  }
  else
  {
    xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->Size = sizeof(DMA_OPERATIONS);
  }
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->PutDmaAdapter = XenPci_DOP_PutDmaAdapter;
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->AllocateCommonBuffer = XenPci_DOP_AllocateCommonBuffer;
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->FreeCommonBuffer = XenPci_DOP_FreeCommonBuffer;
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->AllocateAdapterChannel = XenPci_DOP_AllocateAdapterChannel;
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->FlushAdapterBuffers = XenPci_DOP_FlushAdapterBuffers;
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->FreeAdapterChannel = XenPci_DOP_FreeAdapterChannel;
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->FreeMapRegisters = XenPci_DOP_FreeMapRegisters;
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->MapTransfer = XenPci_DOP_MapTransfer;
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->GetDmaAlignment = XenPci_DOP_GetDmaAlignment;
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->ReadDmaCounter = XenPci_DOP_ReadDmaCounter;
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->GetScatterGatherList = XenPci_DOP_GetScatterGatherList;
  xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->PutScatterGatherList = XenPci_DOP_PutScatterGatherList;
  if (xen_dma_adapter->adapter_object.DmaHeader.Version == 2)
  {
    xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->CalculateScatterGatherList = XenPci_DOP_CalculateScatterGatherList;
    xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->BuildScatterGatherList = XenPci_DOP_BuildScatterGatherList;
    xen_dma_adapter->adapter_object.DmaHeader.DmaOperations->BuildMdlFromScatterGatherList = XenPci_DOP_BuildMdlFromScatterGatherList;
  }

  *number_of_map_registers = xen_dma_adapter->adapter_object.MapRegistersPerChannel; //1024; /* why not... */

  KeInitializeSpinLock(&xen_dma_adapter->lock);
  xen_dma_adapter->map_register_base = NULL;
  xen_dma_adapter->queued_map_register_base = NULL;

  FUNCTION_EXIT();

  if (KD_DEBUGGER_ENABLED)
    KdBreakPoint();
  
  return &xen_dma_adapter->adapter_object.DmaHeader;
}

ULONG
XenPci_BIS_SetBusData(PVOID context, ULONG data_type, PVOID buffer, ULONG offset, ULONG length)
{
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(data_type);
  UNREFERENCED_PARAMETER(buffer);
  UNREFERENCED_PARAMETER(offset);
  UNREFERENCED_PARAMETER(length);
  
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return 0;
}

ULONG
XenPci_BIS_GetBusData(PVOID context, ULONG data_type, PVOID buffer, ULONG offset, ULONG length)
{
  UNREFERENCED_PARAMETER(context);
  UNREFERENCED_PARAMETER(data_type);
  UNREFERENCED_PARAMETER(buffer);
  UNREFERENCED_PARAMETER(offset);
  UNREFERENCED_PARAMETER(length);
  
  FUNCTION_ENTER();
  FUNCTION_EXIT();
  return 0;
}
