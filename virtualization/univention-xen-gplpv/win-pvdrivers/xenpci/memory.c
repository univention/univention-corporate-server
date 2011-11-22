#include "xenpci.h"

/* must be called at <= DISPATCH_LEVEL if hypercall_stubs == NULL */

#define XEN_SIGNATURE_LOWER 0x40000000
#define XEN_SIGNATURE_UPPER 0x4000FFFF

PVOID
hvm_get_hypercall_stubs()
{
  PVOID hypercall_stubs;
  ULONG base;
  DWORD32 cpuid_output[4];
  char xensig[13];
  ULONG i;
  ULONG pages;
  ULONG msr;

  for (base = XEN_SIGNATURE_LOWER; base < XEN_SIGNATURE_UPPER; base += 0x100)
  {
    __cpuid(cpuid_output, base);
    *(ULONG*)(xensig + 0) = cpuid_output[1];
    *(ULONG*)(xensig + 4) = cpuid_output[2];
    *(ULONG*)(xensig + 8) = cpuid_output[3];
    xensig[12] = '\0';
    KdPrint((__DRIVER_NAME "     base = 0x%08x, Xen Signature = %s, EAX = 0x%08x\n", base, xensig, cpuid_output[0]));
    if (!strncmp("XenVMMXenVMM", xensig, 12) && ((cpuid_output[0] - base) >= 2))
      break;
  }
  if (base > XEN_SIGNATURE_UPPER)
  {
    KdPrint((__DRIVER_NAME "     Cannot find Xen signature\n"));
    return NULL;
  }

  __cpuid(cpuid_output, base + 2);
  pages = cpuid_output[0];
  msr = cpuid_output[1];

  hypercall_stubs = ExAllocatePoolWithTag(NonPagedPool, pages * PAGE_SIZE, XENPCI_POOL_TAG);
  KdPrint((__DRIVER_NAME "     Hypercall area at %p\n", hypercall_stubs));

  if (!hypercall_stubs)
    return NULL;
  for (i = 0; i < pages; i++) {
    ULONGLONG pfn;
    pfn = (MmGetPhysicalAddress((PUCHAR)hypercall_stubs + i * PAGE_SIZE).QuadPart >> PAGE_SHIFT);
    //KdPrint((__DRIVER_NAME "     pfn = %16lX\n", pfn));
    __writemsr(msr, (pfn << PAGE_SHIFT) + i);
  }
  return hypercall_stubs;
}

VOID
hvm_free_hypercall_stubs(PVOID hypercall_stubs)
{
  ExFreePoolWithTag(hypercall_stubs, XENPCI_POOL_TAG);
}
