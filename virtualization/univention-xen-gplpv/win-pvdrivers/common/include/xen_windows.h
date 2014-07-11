#if !defined(_XEN_WINDOWS_H_)
#define _XEN_WINDOWS_H_

#include "gplpv_version.h"

#include <ntverp.h>
#pragma warning( disable : 4201 ) // nonstandard extension used : nameless struct/union
#pragma warning( disable : 4214 ) // nonstandard extension used : bit field types other than int
#pragma warning( disable : 4505 ) // 'XenDbgPrint' : unreferenced local function has been removed

#define __XEN_INTERFACE_VERSION__ 0x00030205
#if defined(_AMD64_)
  #define __x86_64__
#elif defined(_IA64_)
  #define __ia64__
#elif defined(_X86_)
  #define __i386__
#else
  #error Unknown architecture
#endif

typedef INT8 int8_t;
typedef UINT8 uint8_t;
typedef INT16 int16_t;
typedef UINT16 uint16_t;
typedef INT32 int32_t;
typedef UINT32 uint32_t;
typedef UINT64 uint64_t;

#include <xen.h>
#include <grant_table.h>
#include <event_channel.h>
#include <xen_guids.h>

#define _PAGE_PRESENT  0x001UL
#define _PAGE_RW       0x002UL
#define _PAGE_USER     0x004UL
#define _PAGE_PWT      0x008UL
#define _PAGE_PCD      0x010UL
#define _PAGE_ACCESSED 0x020UL
#define _PAGE_DIRTY    0x040UL
#define _PAGE_PAT      0x080UL
#define _PAGE_PSE      0x080UL
#define _PAGE_GLOBAL   0x100UL

#define L1_PROT (_PAGE_PRESENT|_PAGE_RW|_PAGE_ACCESSED)

#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))

typedef unsigned long xenbus_transaction_t;

#define XBT_NIL ((xenbus_transaction_t)0)

#define SPLITSTRING_POOL_TAG (ULONG) 'SSPT'

#define wmb() KeMemoryBarrier()
#define mb() KeMemoryBarrier()

static __inline char **
SplitString(char *String, char Split, int MaxParts, int *Count) {
  char **RetVal;
  char *first;
  char *last;

  *Count = 0;

  RetVal = (char **)ExAllocatePoolWithTag(NonPagedPool, (MaxParts + 1) * sizeof(char *), SPLITSTRING_POOL_TAG);
  last = String;
  do {
    if (*Count == MaxParts)
      break;
    first = last;
    for (last = first; *last != '\0' && *last != Split; last++);
    RetVal[*Count] = (char *)ExAllocatePoolWithTag(NonPagedPool, last - first + 1, SPLITSTRING_POOL_TAG);
    RtlStringCbCopyNA(RetVal[*Count], last - first + 1, first, last - first);
    RetVal[*Count][last - first] = 0;
    (*Count)++;
    if (*last == Split)
      last++;
  } while (*last != 0);
  RetVal[*Count] = NULL;
  return RetVal;
}

static __inline VOID
FreeSplitString(char **Bits, int Count) {
  int i;

  for (i = 0; i < Count; i++)
    ExFreePoolWithTag(Bits[i], SPLITSTRING_POOL_TAG);
  ExFreePoolWithTag(Bits, SPLITSTRING_POOL_TAG);
}

#define ALLOCATE_PAGES_POOL_TAG (ULONG) 'APPT'

static PMDL
AllocatePagesExtra(int Pages, int ExtraSize)
{
  PMDL Mdl;
  PVOID Buf;

  Buf = ExAllocatePoolWithTag(NonPagedPool, Pages * PAGE_SIZE, ALLOCATE_PAGES_POOL_TAG);
  if (Buf == NULL) {
    KdPrint((__DRIVER_NAME "     AllocatePages Failed at ExAllocatePoolWithTag\n"));
    return NULL;
  }
  Mdl = (PMDL)ExAllocatePoolWithTag(NonPagedPool, MmSizeOfMdl(Buf, Pages * PAGE_SIZE) + ExtraSize, ALLOCATE_PAGES_POOL_TAG);
  if (Mdl == NULL) {
    ExFreePoolWithTag(Buf, ALLOCATE_PAGES_POOL_TAG);
    KdPrint((__DRIVER_NAME "     AllocatePages Failed at IoAllocateMdl\n"));
    return NULL;
  }
  
  MmInitializeMdl(Mdl, Buf, Pages * PAGE_SIZE);
  MmBuildMdlForNonPagedPool(Mdl);
  
  return Mdl;
}

static __inline PMDL
AllocatePages(int Pages) {
  return AllocatePagesExtra(Pages, 0);
}

static __inline PMDL
AllocatePage() {
  return AllocatePagesExtra(1, 0);
}

static __inline PMDL
AllocateUncachedPage() {
  PMDL mdl;
  PVOID buf;

  buf = MmAllocateNonCachedMemory(PAGE_SIZE);
  mdl = IoAllocateMdl(buf, PAGE_SIZE, FALSE, FALSE, NULL);
  MmBuildMdlForNonPagedPool(mdl);

  return mdl;
}  

static __inline VOID
FreeUncachedPage(PMDL mdl) {
  PVOID buf = MmGetMdlVirtualAddress(mdl);

  IoFreeMdl(mdl);
  MmFreeNonCachedMemory(buf, PAGE_SIZE);
}

static __inline VOID
FreePages(PMDL Mdl) {
  PVOID Buf = MmGetMdlVirtualAddress(Mdl);
  ExFreePoolWithTag(Mdl, ALLOCATE_PAGES_POOL_TAG);
  ExFreePoolWithTag(Buf, ALLOCATE_PAGES_POOL_TAG);
}

#define XEN_IOPORT_BASE 0x10

/*
define these as pointers so that the READ_PORT* functions complain if
the wrong width is used with the wrong defined port
*/

#define XEN_IOPORT_MAGIC        ((PUSHORT)UlongToPtr(XEN_IOPORT_BASE + 0))
#define XEN_IOPORT_LOG          ((PUCHAR)UlongToPtr(XEN_IOPORT_BASE + 2))
#define XEN_IOPORT_VERSION      ((PUCHAR)UlongToPtr(XEN_IOPORT_BASE + 2))
#define XEN_IOPORT_PRODUCT      ((PUSHORT)UlongToPtr(XEN_IOPORT_BASE + 2))
#define XEN_IOPORT_BUILD        ((PULONG)UlongToPtr(XEN_IOPORT_BASE + 0))
#define XEN_IOPORT_DEVICE_MASK  ((PUSHORT)UlongToPtr(XEN_IOPORT_BASE + 0))

#define QEMU_UNPLUG_ALL_IDE_DISKS 1
#define QEMU_UNPLUG_ALL_NICS 2
#define QEMU_UNPLUG_AUX_IDE_DISKS 4

#if DBG
#define FUNCTION_ENTER()       XnDebugPrint(__DRIVER_NAME " --> %s\n", __FUNCTION__)
#define FUNCTION_EXIT()        XnDebugPrint(__DRIVER_NAME " <-- %s\n", __FUNCTION__)
#define FUNCTION_EXIT_STATUS(_status) XnDebugPrint(__DRIVER_NAME " <-- %s, status = %08x\n", __FUNCTION__, _status)
#define FUNCTION_MSG(...) XnDebugPrint(__DRIVER_NAME "     " __VA_ARGS__)
#else
#define FUNCTION_ENTER()
#define FUNCTION_EXIT()
#define FUNCTION_EXIT_STATUS(_status)
#define FUNCTION_MSG(...)
#endif

#define INVALID_GRANT_REF 0xFFFFFFFF

#define XN_BASE_FRONTEND 1 /* path is relative to frontend device */
#define XN_BASE_BACKEND  2 /* path is relative to backend device */
#define XN_BASE_GLOBAL   3 /* path is relative to root of xenstore */

#define XN_DEVICE_CALLBACK_BACKEND_STATE 1 /* backend state change callback */
#define XN_DEVICE_CALLBACK_SUSPEND       2
#define XN_DEVICE_CALLBACK_RESUME        3

typedef PVOID XN_HANDLE;

typedef VOID
(*PXN_WATCH_CALLBACK)(PVOID context, char *path);

typedef VOID
(*PXN_EVENT_CALLBACK)(PVOID context);

typedef VOID
(*PXN_DEVICE_CALLBACK)(PVOID context, ULONG callback_type, PVOID value);

ULONG
XnGetVersion();

XN_HANDLE
XnOpenDevice(PDEVICE_OBJECT pdo, PXN_DEVICE_CALLBACK callback, PVOID context);

VOID
XnCloseDevice(XN_HANDLE handle);

#define XN_VALUE_TYPE_QEMU_HIDE_FLAGS 1
#define XN_VALUE_TYPE_QEMU_FILTER     2 /* true if qemu devices hidden by device filter, not by qemu */

VOID
XnGetValue(XN_HANDLE handle, ULONG value_type, PVOID value);

NTSTATUS
XnReadInt32(XN_HANDLE handle, ULONG base, PCHAR path, ULONG *value);

NTSTATUS
XnWriteInt32(XN_HANDLE handle, ULONG base, PCHAR path, ULONG value);

NTSTATUS
XnReadInt64(XN_HANDLE handle, ULONG base, PCHAR path, ULONGLONG *value);

NTSTATUS
XnWriteInt64(XN_HANDLE handle, ULONG base, PCHAR path, ULONGLONG value);

NTSTATUS
XnReadString(XN_HANDLE handle, ULONG base, PCHAR path, PCHAR *value);

NTSTATUS
XnWriteString(XN_HANDLE handle, ULONG base, PCHAR path, PCHAR value);

NTSTATUS
XnFreeString(XN_HANDLE handle, PCHAR string);

NTSTATUS
XnNotify(XN_HANDLE handle, evtchn_port_t port);

grant_ref_t
XnGrantAccess(XN_HANDLE handle, uint32_t frame, int readonly, grant_ref_t ref, ULONG tag);

BOOLEAN
XnEndAccess(XN_HANDLE handle, grant_ref_t ref, BOOLEAN keepref, ULONG tag);

grant_ref_t
XnAllocateGrant(XN_HANDLE handle, ULONG tag);

VOID
XnFreeGrant(XN_HANDLE handle, grant_ref_t ref, ULONG tag);

NTSTATUS
XnBindEvent(XN_HANDLE handle, evtchn_port_t *port, PXN_EVENT_CALLBACK callback, PVOID context);

NTSTATUS
XnUnbindEvent(XN_HANDLE handle, evtchn_port_t port);

ULONG
XnTmemOp(struct tmem_op *tmem_op);

#ifndef XENPCI_POOL_TAG
#define XENPCI_POOL_TAG (ULONG) 'XenP'
#endif

static __inline VOID
XnFreeMem(XN_HANDLE handle, PVOID Ptr) {
  UNREFERENCED_PARAMETER(handle);
  ExFreePoolWithTag(Ptr, XENPCI_POOL_TAG);
}

PVOID
XnGetHypercallStubs();

VOID
XnSetHypercallStubs(PVOID _hypercall_stubs);

NTSTATUS
XnDebugPrint(PCHAR format, ...);

VOID
XnPrintDump();

#if DBG
#define XN_ASSERT(expr) \
if (!(expr)) { \
  XnDebugPrint("ASSERT(%s) %s:%d\n", #expr, __FILE__, __LINE__); \
  ASSERT(expr); \
}
#else
#define XN_ASSERT(expr)
#endif

#endif