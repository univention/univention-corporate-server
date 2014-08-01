/*
PV Drivers for Windows Xen HVM Domains
Copyright (C) 2007 James Harper
Inspired by amdvopt by Travis Betak

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

#if defined(_X86_)

/* Is LOCK MOV CR0 available? */
#define CPUID_ALTMOVCR8	(1UL << 4)
/* Task priority register address */
#define LAPIC_TASKPRI 0xFFFE0080
#define TPR_BYTES   0x80, 0x00, 0xfe, 0xff

extern VOID MoveTprToEax(VOID);
extern VOID MoveTprToEcx(VOID);
extern VOID MoveTprToEdx(VOID);
extern VOID MoveTprToEsi(VOID);
extern VOID PushTpr(VOID);
extern VOID MoveEaxToTpr(VOID);
extern VOID MoveEbxToTpr(VOID);
extern VOID MoveEcxToTpr(VOID);
extern VOID MoveEdxToTpr(VOID);
extern VOID MoveEsiToTpr(VOID);
extern VOID MoveConstToTpr(ULONG new_tpr_value);
extern VOID MoveZeroToTpr(VOID);

static PHYSICAL_ADDRESS lapic_page[MAX_VIRT_CPUS];
static volatile PVOID lapic[MAX_VIRT_CPUS];
static ULONG tpr_cache[MAX_VIRT_CPUS];
#define PATCH_METHOD_LOCK_MOVE_CR0 1
#define PATCH_METHOD_MAPPED_VLAPIC 2
#define PATCH_METHOD_CACHED_TPR    3
static ULONG patch_method;

static ULONG
SaveTprProcValue(ULONG cpu, ULONG value)
{
  switch (patch_method)
  {
  case PATCH_METHOD_LOCK_MOVE_CR0:
  case PATCH_METHOD_CACHED_TPR:
    tpr_cache[cpu] = value;
    break;
  case PATCH_METHOD_MAPPED_VLAPIC:
    /* no need to save here */
    break;
  }
  return value;
}

static ULONG
SaveTpr()
{
  switch (patch_method)
  {
  case PATCH_METHOD_LOCK_MOVE_CR0:
  case PATCH_METHOD_CACHED_TPR:
    return SaveTprProcValue(KeGetCurrentProcessorNumber(), *(PULONG)LAPIC_TASKPRI);
  case PATCH_METHOD_MAPPED_VLAPIC:
    /* no need to save here */
    break;
  }
  return 0;
}

/* called with interrupts disabled (via CLI) from an arbitrary location inside HAL.DLL */
static __inline LONG
ApicHighestVector(PULONG bitmap)
{
  int i;
  ULONG bit;
  ULONG value;
  for (i = 0; i < 8; i++)
  {
    value = bitmap[(7 - i) * 4];
    if (value)
    {
      _BitScanReverse(&bit, value);
      return ((7 - i) << 5) | bit;
    }
  }
  return -1;
}

/* called with interrupts disabled (via CLI) from an arbitrary location inside HAL.DLL */
VOID
WriteTpr(ULONG new_tpr_value)
{
  LONG ISR;
  LONG IRR;
  ULONG cpu = KeGetCurrentProcessorNumber();
  
  switch (patch_method)
  {
  case PATCH_METHOD_LOCK_MOVE_CR0:
    tpr_cache[cpu] = new_tpr_value;
    __asm {
      mov eax, new_tpr_value;
      shr	eax, 4;
      lock mov cr0, eax; /* this is actually mov cr8, eax */
    }
    break;
  case PATCH_METHOD_CACHED_TPR:
    if (new_tpr_value != tpr_cache[cpu])
    {
      *(PULONG)LAPIC_TASKPRI = new_tpr_value;
      tpr_cache[cpu] = new_tpr_value;
    }
    break;
  case PATCH_METHOD_MAPPED_VLAPIC:
    /* need to set the new tpr value and then check for pending interrupts to avoid a race */
    *(PULONG)((PUCHAR)lapic[cpu] + 0x80) = new_tpr_value & 0xff;
    KeMemoryBarrier();
    IRR = ApicHighestVector((PULONG)((PUCHAR)lapic[cpu] + 0x200));
    if (IRR == -1)
      return;
    ISR = ApicHighestVector((PULONG)((PUCHAR)lapic[cpu] + 0x100));
    if (ISR == -1)
      ISR = 0;
    if ((ULONG)(IRR >> 4) > max((ULONG)(ISR >> 4), ((new_tpr_value & 0xf0) >> 4)))
      *(PULONG)LAPIC_TASKPRI = new_tpr_value;
    break;
  }
}

/* called with interrupts disabled (via CLI) from an arbitrary location inside HAL.DLL */
ULONG
ReadTpr()
{
  switch (patch_method)
  {
  case PATCH_METHOD_LOCK_MOVE_CR0:
  case PATCH_METHOD_CACHED_TPR:
    return tpr_cache[KeGetCurrentProcessorNumber()];
  case PATCH_METHOD_MAPPED_VLAPIC:
    return *(PULONG)((PUCHAR)lapic[KeGetCurrentProcessorNumber()] + 0x80);
  default:
    return 0;
  }
}

static __inline VOID
InsertCallRel32(PUCHAR address, ULONG target)
{
  *address = 0xE8; /* call near */
  *(PULONG)(address + 1) = (ULONG)target - ((ULONG)address + 5);
}

#define PATCH_SIZE 10

typedef struct {
  ULONG patch_type;
  ULONG match_size;
  ULONG function;
  UCHAR bytes[PATCH_SIZE];
} patch_t;

#define PATCH_NONE  0
#define PATCH_1B4   1 /* 1 byte opcode with 4 bytes of data  - replace with call function */
#define PATCH_2B4   2 /* 2 byte opcode with 4 bytes of data - replace with nop + call function*/
#define PATCH_2B5   3 /* 2 byte opcode with 1 + 4 bytes of data - replace with nop + nop + call function */
#define PATCH_2B8   4 /* 2 byte opcode with 4 + 4 bytes of data - replace with push const + call function*/

static patch_t patches[] =
{
  { PATCH_1B4,  5, (ULONG)MoveTprToEax,   { 0xa1, TPR_BYTES } },
  { PATCH_2B4,  6, (ULONG)MoveTprToEcx,   { 0x8b, 0x0d, TPR_BYTES } },
  { PATCH_2B4,  6, (ULONG)MoveTprToEdx,   { 0x8b, 0x15, TPR_BYTES } },
  { PATCH_2B4,  6, (ULONG)MoveTprToEsi,   { 0x8b, 0x35, TPR_BYTES } },
  { PATCH_2B4,  6, (ULONG)PushTpr,        { 0xff, 0x35, TPR_BYTES } },
  { PATCH_1B4,  5, (ULONG)MoveEaxToTpr,   { 0xa3, TPR_BYTES } },
  { PATCH_2B4,  6, (ULONG)MoveEbxToTpr,   { 0x89, 0x1D, TPR_BYTES } },
  { PATCH_2B4,  6, (ULONG)MoveEcxToTpr,   { 0x89, 0x0D, TPR_BYTES } },
  { PATCH_2B4,  6, (ULONG)MoveEdxToTpr,   { 0x89, 0x15, TPR_BYTES } },
  { PATCH_2B4,  6, (ULONG)MoveEsiToTpr,   { 0x89, 0x35, TPR_BYTES } },
  { PATCH_2B8,  6, (ULONG)MoveConstToTpr, { 0xC7, 0x05, TPR_BYTES } }, /* + another 4 bytes of const */
  { PATCH_2B5,  7, (ULONG)MoveZeroToTpr,  { 0x83, 0x25, TPR_BYTES, 0 } },
  { PATCH_NONE, 0, 0,                     { 0 } }
};

static BOOLEAN
XenPci_TestAndPatchInstruction(PVOID address)
{
  PUCHAR instruction = address;
  ULONG i;
  /* don't declare patches[] on the stack - windows gets grumpy if we allocate too much space on the stack at HIGH_LEVEL */
  
  for (i = 0; patches[i].patch_type != PATCH_NONE; i++)
  {
    if (memcmp(address, patches[i].bytes, patches[i].match_size) == 0)
      break;
  }

  switch (patches[i].patch_type)
  {
  case PATCH_1B4:
    InsertCallRel32(instruction + 0, patches[i].function);
    break;
  case PATCH_2B4:
    *(instruction + 0) = 0x90; /* nop */
    InsertCallRel32(instruction + 1, patches[i].function);
    break;
  case PATCH_2B8:
    *(instruction + 0) = 0x68; /* push value */
    *(PULONG)(instruction + 1) = *(PULONG)(instruction + 6);
    InsertCallRel32(instruction + 5, patches[i].function);
    break;
  case PATCH_2B5:
    *(instruction + 0) = 0x90; /* nop */
    *(instruction + 1) = 0x90; /* nop */
    InsertCallRel32(instruction + 2, patches[i].function);
    break;
  default:
    return FALSE;
  }
  return TRUE;
}

typedef struct {
  PVOID base;
  ULONG length;
} patch_info_t;

static PVOID patch_positions[256];
static PVOID potential_patch_positions[256];

static VOID
XenPci_DoPatchKernel0(PVOID context)
{
  patch_info_t *pi = context;
  ULONG i;
  ULONG high_level_tpr;
  ULONG patch_position_index = 0;
  ULONG potential_patch_position_index = 0;

  FUNCTION_ENTER();

  high_level_tpr = SaveTpr();
  /* we know all the other CPUs are at HIGH_LEVEL so set them all to the same as cpu 0 */
  for (i = 1; i < MAX_VIRT_CPUS; i++)
    SaveTprProcValue(i, high_level_tpr);

  /* we can't use KdPrint while patching as it may involve the TPR while we are patching it */
  for (i = 0; i < pi->length; i++)
  {
    if (XenPci_TestAndPatchInstruction((PUCHAR)pi->base + i))
    {
      patch_positions[patch_position_index++] = (PUCHAR)pi->base + i;
    }
    else if (*(PULONG)((PUCHAR)pi->base + i) == LAPIC_TASKPRI)
    {
      potential_patch_positions[potential_patch_position_index++] = (PUCHAR)pi->base + i;
    }
  }

  for (i = 0; i < patch_position_index; i++)
    KdPrint((__DRIVER_NAME "     Patch added at %p\n", patch_positions[i]));

  for (i = 0; i < potential_patch_position_index; i++)
    KdPrint((__DRIVER_NAME "     Unpatch TPR address found at %p\n", potential_patch_positions[i]));

  FUNCTION_EXIT();
}

static VOID
XenPci_DoPatchKernelN(PVOID context)
{
  UNREFERENCED_PARAMETER(context);
  
  FUNCTION_ENTER();

  FUNCTION_EXIT();
}

static BOOLEAN
IsMoveCr8Supported()
{
  DWORD32 cpuid_output[4];
  
  __cpuid(cpuid_output, 0x80000001UL);
  if (cpuid_output[2] & CPUID_ALTMOVCR8)
    return TRUE;
  else
    return FALSE;
}

static ULONG
MapVlapic(PXENPCI_DEVICE_DATA xpdd)
{
  struct xen_add_to_physmap xatp;
  ULONG rc = EINVAL;
  ULONG ActiveProcessorCount;
  int i;

  FUNCTION_ENTER();
  
#if (NTDDI_VERSION >= NTDDI_WINXP)
  ActiveProcessorCount = (ULONG)KeNumberProcessors;
#else
  ActiveProcessorCount = (ULONG)*KeNumberProcessors;
#endif

  for (i = 0; i < (int)ActiveProcessorCount; i++)
  {
    KdPrint((__DRIVER_NAME "     mapping lapic for cpu = %d\n", i));

    lapic_page[i] = XenPci_AllocMMIO(xpdd, PAGE_SIZE);
    lapic[i] = MmMapIoSpace(lapic_page[i], PAGE_SIZE, MmCached);

    xatp.domid = DOMID_SELF;
    xatp.idx = i;
    xatp.space = XENMAPSPACE_vlapic;
    xatp.gpfn = (xen_pfn_t)(lapic_page[i].QuadPart >> PAGE_SHIFT);
    KdPrint((__DRIVER_NAME "     gpfn = %x\n", xatp.gpfn));
    rc = HYPERVISOR_memory_op(xpdd, XENMEM_add_to_physmap, &xatp);
    KdPrint((__DRIVER_NAME "     hypervisor memory op (XENMAPSPACE_vlapic_regs) ret = %d\n", rc));
    if (rc != 0)
    {
      FUNCTION_EXIT();
      return rc;
    }
  }
  FUNCTION_EXIT();

  return rc;
}

VOID
XenPci_PatchKernel(PXENPCI_DEVICE_DATA xpdd, PVOID base, ULONG length)
{
  patch_info_t patch_info;
  ULONG rc;
#if (NTDDI_VERSION >= NTDDI_WINXP)
  RTL_OSVERSIONINFOEXW version_info;
#endif

  FUNCTION_ENTER();

/* if we're compiled for 2000 then assume we need patching */
#if (NTDDI_VERSION >= NTDDI_WINXP)
  version_info.dwOSVersionInfoSize = sizeof(RTL_OSVERSIONINFOEXW);

  RtlGetVersion((PRTL_OSVERSIONINFOW)&version_info);
  if (version_info.dwMajorVersion >= 6)
  {
    KdPrint((__DRIVER_NAME "     Vista or newer - no need for patch\n"));
    return;
  }
  if (version_info.dwMajorVersion == 5
      && version_info.dwMinorVersion > 2)
  {
    KdPrint((__DRIVER_NAME "     Windows 2003 sp2 or newer - no need for patch\n"));
    return;
  }
  if (version_info.dwMajorVersion == 5
      && version_info.dwMinorVersion == 2
      && version_info.wServicePackMajor >= 2)
  {
    KdPrint((__DRIVER_NAME "     Windows 2003 sp2 or newer - no need for patch\n"));
    return;
  }
#endif
  if (IsMoveCr8Supported())
  {
    KdPrint((__DRIVER_NAME "     Using LOCK MOVE CR0 TPR patch\n"));
    patch_method = PATCH_METHOD_LOCK_MOVE_CR0;
  }
  else
  {
    rc = MapVlapic(xpdd);
    if (rc == EACCES)
    {
      KdPrint((__DRIVER_NAME "     Xen already using VMX LAPIC acceleration. No patch required\n"));
      return;
    }
    if (!rc)
    {
      KdPrint((__DRIVER_NAME "     Using mapped vLAPIC TPR patch\n"));
      patch_method = PATCH_METHOD_MAPPED_VLAPIC;
    }
    else
    {
      KdPrint((__DRIVER_NAME "     Using cached TPR patch\n"));
      patch_method = PATCH_METHOD_CACHED_TPR;
    }
  }
  patch_info.base = base;
  patch_info.length = length;
    
  XenPci_HighSync(XenPci_DoPatchKernel0, XenPci_DoPatchKernelN, &patch_info);
  
  xpdd->removable = FALSE;
  
  FUNCTION_EXIT();
}

#else

VOID
XenPci_PatchKernel(PXENPCI_DEVICE_DATA xpdd, PVOID base, ULONG length)
{
  UNREFERENCED_PARAMETER(xpdd);
  UNREFERENCED_PARAMETER(base);
  UNREFERENCED_PARAMETER(length);
}

#endif
