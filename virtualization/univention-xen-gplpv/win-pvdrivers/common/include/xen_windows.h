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
#elif defined(__MINGW32__)
  /* __i386__ already defined */
#elif defined(_X86_)
  #define __i386__
#else
  #error Unknown architecture
#endif

#ifdef __MINGW32__
typedef signed char int8_t;
typedef unsigned char uint8_t;
typedef signed short int16_t;
typedef unsigned short uint16_t;
typedef signed int int32_t;
typedef unsigned int uint32_t;
typedef unsigned long long uint64_t;
#else
typedef INT8 int8_t;
typedef UINT8 uint8_t;
typedef INT16 int16_t;
typedef UINT16 uint16_t;
typedef INT32 int32_t;
typedef UINT32 uint32_t;
typedef UINT64 uint64_t;
#endif

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

#define IOCTL_XEN_RECONFIGURE CTL_CODE(0x8000, 0x800, METHOD_NEITHER, 0)

static __inline char **
SplitString(char *String, char Split, int MaxParts, int *Count)
{
  char **RetVal;
  char *first;
  char *last;

  //KdPrint((__DRIVER_NAME "     a\n"));

  *Count = 0;

  RetVal = (char **)ExAllocatePoolWithTag(NonPagedPool, (MaxParts + 1) * sizeof(char *), SPLITSTRING_POOL_TAG);
  last = String;
  do
  {
    if (*Count == MaxParts)
      break;
    //KdPrint((__DRIVER_NAME "     b - count = %d\n", *Count));
    first = last;
    for (last = first; *last != '\0' && *last != Split; last++);
    RetVal[*Count] = (char *)ExAllocatePoolWithTag(NonPagedPool, last - first + 1, SPLITSTRING_POOL_TAG);
    //KdPrint((__DRIVER_NAME "     c - count = %d\n", *Count));
    RtlStringCbCopyNA(RetVal[*Count], last - first + 1, first, last - first);
    RetVal[*Count][last - first] = 0;
    //KdPrint((__DRIVER_NAME "     d - count = %d\n", *Count));
    (*Count)++;
    //KdPrint((__DRIVER_NAME "     e - count = %d\n", *Count));
    if (*last == Split)
      last++;
  } while (*last != 0);
  //KdPrint((__DRIVER_NAME "     f - count = %d\n", *Count));
  RetVal[*Count] = NULL;
  return RetVal;
}

static __inline VOID
FreeSplitString(char **Bits, int Count)
{
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
  if (Buf == NULL)
  {
    KdPrint((__DRIVER_NAME "     AllocatePages Failed at ExAllocatePoolWithTag\n"));
    return NULL;
  }
//  KdPrint((__DRIVER_NAME " --- AllocatePages IRQL = %d, Buf = %p\n", KeGetCurrentIrql(), Buf));
  Mdl = (PMDL)ExAllocatePoolWithTag(NonPagedPool, MmSizeOfMdl(Buf, Pages * PAGE_SIZE) + ExtraSize, ALLOCATE_PAGES_POOL_TAG);
  if (Mdl == NULL)
  {
    // free the memory here
    KdPrint((__DRIVER_NAME "     AllocatePages Failed at IoAllocateMdl\n"));
    return NULL;
  }
  
  MmInitializeMdl(Mdl, Buf, Pages * PAGE_SIZE);
  MmBuildMdlForNonPagedPool(Mdl);
  
  return Mdl;
}

static __inline PMDL
AllocatePages(int Pages)
{
  return AllocatePagesExtra(Pages, 0);
}

static __inline PMDL
AllocatePage()
{
  return AllocatePagesExtra(1, 0);
}

static __inline PMDL
AllocateUncachedPage()
{
  PMDL mdl;
  PVOID buf;

  buf = MmAllocateNonCachedMemory(PAGE_SIZE);
  mdl = IoAllocateMdl(buf, PAGE_SIZE, FALSE, FALSE, NULL);
  MmBuildMdlForNonPagedPool(mdl);

  return mdl;
}  

static __inline VOID
FreeUncachedPage(PMDL mdl)
{
  PVOID buf = MmGetMdlVirtualAddress(mdl);

  IoFreeMdl(mdl);
  MmFreeNonCachedMemory(buf, PAGE_SIZE);
}

static __inline VOID
FreePages(PMDL Mdl)
{
  PVOID Buf = MmGetMdlVirtualAddress(Mdl);
//  KdPrint((__DRIVER_NAME " --- FreePages IRQL = %d, Buf = %p\n", KeGetCurrentIrql(), Buf));
//  IoFreeMdl(Mdl);
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

#define FUNCTION_ENTER()       KdPrint((__DRIVER_NAME " --> %s\n", __FUNCTION__))
#define FUNCTION_EXIT()        KdPrint((__DRIVER_NAME " <-- %s\n", __FUNCTION__))
#define FUNCTION_EXIT_STATUS(_status) KdPrint((__DRIVER_NAME " <-- %s, status = %08x\n", __FUNCTION__, _status))
#define FUNCTION_MSG(...) KdPrint((__DRIVER_NAME "     " __VA_ARGS__))

#define INVALID_GRANT_REF 0xFFFFFFFF

typedef PHYSICAL_ADDRESS
(*PXEN_ALLOCMMIO)(PVOID Context, ULONG Length);

typedef void
(*PXEN_FREEMEM)(PVOID Ptr);

typedef VOID
(*PXEN_EVTCHN_SERVICE_ROUTINE)(PVOID Context);

typedef NTSTATUS
(*PXEN_EVTCHN_BIND)(PVOID Context, evtchn_port_t Port, PXEN_EVTCHN_SERVICE_ROUTINE ServiceRoutine, PVOID ServiceContext);

typedef NTSTATUS
(*PXEN_EVTCHN_UNBIND)(PVOID Context, evtchn_port_t Port);

typedef NTSTATUS
(*PXEN_EVTCHN_MASK)(PVOID Context, evtchn_port_t Port);

typedef NTSTATUS
(*PXEN_EVTCHN_UNMASK)(PVOID Context, evtchn_port_t Port);

typedef NTSTATUS
(*PXEN_EVTCHN_NOTIFY)(PVOID Context, evtchn_port_t Port);

typedef evtchn_port_t
(*PXEN_EVTCHN_ALLOCUNBOUND)(PVOID Context, domid_t Domain);

typedef BOOLEAN
(*PXEN_EVTCHN_ACK_EVENT)(PVOID context, evtchn_port_t port, BOOLEAN *last_interrupt);

typedef BOOLEAN
(*PXEN_EVTCHN_SYNC_ROUTINE)(PVOID sync_context);

typedef BOOLEAN
(*PXEN_EVTCHN_SYNC)(PVOID Context, PXEN_EVTCHN_SYNC_ROUTINE sync_routine, PVOID sync_context);

typedef grant_ref_t
(*PXEN_GNTTBL_GRANTACCESS)(PVOID Context, uint32_t frame, int readonly, grant_ref_t ref, ULONG tag);

typedef BOOLEAN
(*PXEN_GNTTBL_ENDACCESS)(PVOID Context, grant_ref_t ref, BOOLEAN keepref, ULONG tag);

typedef VOID
(*PXEN_GNTTBL_PUTREF)(PVOID Context, grant_ref_t ref, ULONG tag);

typedef grant_ref_t
(*PXEN_GNTTBL_GETREF)(PVOID Context, ULONG tag);


typedef VOID
(*PXENBUS_WATCH_CALLBACK)(char *Path, PVOID ServiceContext);

typedef char *
(*PXEN_XENBUS_READ)(PVOID Context, xenbus_transaction_t xbt, char *path, char **value);

typedef char *
(*PXEN_XENBUS_WRITE)(PVOID Context, xenbus_transaction_t xbt, char *path, char *value);

typedef char *
(*PXEN_XENBUS_PRINTF)(PVOID Context, xenbus_transaction_t xbt, char *path, char *fmt, ...);

typedef char *
(*PXEN_XENBUS_STARTTRANSACTION)(PVOID Context, xenbus_transaction_t *xbt);

typedef char *
(*PXEN_XENBUS_ENDTRANSACTION)(PVOID Context, xenbus_transaction_t t, int abort, int *retry);

typedef char *
(*PXEN_XENBUS_LIST)(PVOID Context, xenbus_transaction_t xbt, char *prefix, char ***contents);

typedef char *
(*PXEN_XENBUS_ADDWATCH)(PVOID Context, xenbus_transaction_t xbt, char *Path, PXENBUS_WATCH_CALLBACK ServiceRoutine, PVOID ServiceContext);

typedef char *
(*PXEN_XENBUS_REMWATCH)(PVOID Context, xenbus_transaction_t xbt, char *Path, PXENBUS_WATCH_CALLBACK ServiceRoutine, PVOID ServiceContext);

typedef NTSTATUS
(*PXEN_XENPCI_XEN_CONFIG_DEVICE)(PVOID Context);

typedef NTSTATUS
(*PXEN_XENPCI_XEN_SHUTDOWN_DEVICE)(PVOID Context);

#ifndef XENPCI_POOL_TAG
#define XENPCI_POOL_TAG (ULONG) 'XenP'
#endif

static __inline VOID
XenPci_FreeMem(PVOID Ptr)
{
  ExFreePoolWithTag(Ptr, XENPCI_POOL_TAG);
}

#define XEN_DATA_MAGIC (ULONG)'XV02'

typedef struct {
  ULONG magic;
  USHORT length;

  PVOID context;
  PXEN_EVTCHN_BIND EvtChn_Bind;
  PXEN_EVTCHN_BIND EvtChn_BindDpc;
  PXEN_EVTCHN_UNBIND EvtChn_Unbind;
  PXEN_EVTCHN_MASK EvtChn_Mask;
  PXEN_EVTCHN_UNMASK EvtChn_Unmask;
  PXEN_EVTCHN_NOTIFY EvtChn_Notify;
  PXEN_EVTCHN_ACK_EVENT EvtChn_AckEvent;
  PXEN_EVTCHN_SYNC EvtChn_Sync;

  PXEN_GNTTBL_GETREF GntTbl_GetRef;
  PXEN_GNTTBL_PUTREF GntTbl_PutRef;
  PXEN_GNTTBL_GRANTACCESS GntTbl_GrantAccess;
  PXEN_GNTTBL_ENDACCESS GntTbl_EndAccess;

  PXEN_XENPCI_XEN_CONFIG_DEVICE XenPci_XenConfigDevice;
  PXEN_XENPCI_XEN_SHUTDOWN_DEVICE XenPci_XenShutdownDevice;

  CHAR path[128];
  CHAR backend_path[128];

  PXEN_XENBUS_READ XenBus_Read;
  PXEN_XENBUS_WRITE XenBus_Write;
  PXEN_XENBUS_PRINTF XenBus_Printf;
  PXEN_XENBUS_STARTTRANSACTION XenBus_StartTransaction;
  PXEN_XENBUS_ENDTRANSACTION XenBus_EndTransaction;
  PXEN_XENBUS_LIST XenBus_List;
  PXEN_XENBUS_ADDWATCH XenBus_AddWatch;
  PXEN_XENBUS_REMWATCH XenBus_RemWatch;

} XENPCI_VECTORS, *PXENPCI_VECTORS;

/*
suspend_resume_state_xxx values
pdo will assert a value, and fdo will assert when complete
*/
#define SR_STATE_RUNNING            0 /* normal working state */
#define SR_STATE_SUSPENDING         1 /* suspend has started */
#define SR_STATE_RESUMING           2 /* resume has started */

#define XEN_DEVICE_STATE_MAGIC ((ULONG)'XDST')

typedef struct {
  ULONG magic;
  USHORT length;

  ULONG suspend_resume_state_pdo; /* only the PDO can touch this */
  ULONG suspend_resume_state_fdo; /* only the FDO can touch this */
  evtchn_port_t pdo_event_channel;
} XENPCI_DEVICE_STATE, *PXENPCI_DEVICE_STATE;

#define XEN_INIT_DRIVER_EXTENSION_MAGIC ((ULONG)'XCFG')
#define XEN_DMA_DRIVER_EXTENSION_MAGIC ((ULONG)'XDMA')

#define XEN_INIT_TYPE_END                       0
#define XEN_INIT_TYPE_WRITE_STRING              1
#define XEN_INIT_TYPE_RING                      2
#define XEN_INIT_TYPE_EVENT_CHANNEL             3
#define XEN_INIT_TYPE_EVENT_CHANNEL_IRQ         4
#define XEN_INIT_TYPE_READ_STRING_FRONT         5
#define XEN_INIT_TYPE_READ_STRING_BACK          6
#define XEN_INIT_TYPE_VECTORS                   7
#define XEN_INIT_TYPE_GRANT_ENTRIES             8
#define XEN_INIT_TYPE_STATE_PTR                 11
#define XEN_INIT_TYPE_QEMU_PROTOCOL_VERSION     13
#define XEN_INIT_TYPE_EVENT_CHANNEL_DPC         16
#define XEN_INIT_TYPE_QEMU_HIDE_FLAGS           17 /* qemu hide flags */
#define XEN_INIT_TYPE_QEMU_HIDE_FILTER          18 /* qemu device hidden by class filter */
/*
 state maps consist of 3 bytes: (maximum of 4 x 3 bytes)
  front - state to set frontend to
  back - state to expect from backend
  wait - time in 100ms intervals to wait for backend
 a single 0 byte terminates the list
*/
#define XEN_INIT_TYPE_XB_STATE_MAP_PRE_CONNECT  19
#define XEN_INIT_TYPE_XB_STATE_MAP_POST_CONNECT 20
#define XEN_INIT_TYPE_XB_STATE_MAP_SHUTDOWN     21

static __inline VOID
__ADD_XEN_INIT_UCHAR(PUCHAR *ptr, UCHAR val)
{
//  KdPrint((__DRIVER_NAME "     ADD_XEN_INIT_UCHAR *ptr = %p, val = %d\n", *ptr, val));
  *(PUCHAR)(*ptr) = val;
  *ptr += sizeof(UCHAR);
}

static __inline VOID
__ADD_XEN_INIT_USHORT(PUCHAR *ptr, USHORT val)
{
//  KdPrint((__DRIVER_NAME "     ADD_XEN_INIT_USHORT *ptr = %p, val = %d\n", *ptr, val));
  *(PUSHORT)(*ptr) = val;
  *ptr += sizeof(USHORT);
}

static __inline VOID
__ADD_XEN_INIT_ULONG(PUCHAR *ptr, ULONG val)
{
//  KdPrint((__DRIVER_NAME "     ADD_XEN_INIT_ULONG *ptr = %p, val = %d\n", *ptr, val));
  *(PULONG)(*ptr) = val;
  *ptr += sizeof(ULONG);
}

static __inline VOID
__ADD_XEN_INIT_PTR(PUCHAR *ptr, PVOID val)
{
//  KdPrint((__DRIVER_NAME "     ADD_XEN_INIT_PTR *ptr = %p, val = %p\n", *ptr, val));
  *(PVOID *)(*ptr) = val;
  *ptr += sizeof(PVOID);
}

static __inline VOID
__ADD_XEN_INIT_STRING(PUCHAR *ptr, PCHAR val)
{
//  KdPrint((__DRIVER_NAME "     ADD_XEN_INIT_STRING *ptr = %p, val = %s\n", *ptr, val));
  size_t max_string_size = PAGE_SIZE - (PtrToUlong(*ptr) & (PAGE_SIZE - 1));
  RtlStringCbCopyA((PCHAR)*ptr, max_string_size, val);
  *ptr += min(strlen(val) + 1, max_string_size);
}

static __inline UCHAR
__GET_XEN_INIT_UCHAR(PUCHAR *ptr)
{
  UCHAR retval;
  retval = **ptr;
//  KdPrint((__DRIVER_NAME "     GET_XEN_INIT_UCHAR *ptr = %p, retval = %d\n", *ptr, retval));
  *ptr += sizeof(UCHAR);
  return retval;
}

static __inline USHORT
__GET_XEN_INIT_USHORT(PUCHAR *ptr)
{
  USHORT retval;
  retval = *(PUSHORT)*ptr;
//  KdPrint((__DRIVER_NAME "     GET_XEN_INIT_USHORT *ptr = %p, retval = %d\n", *ptr, retval));
  *ptr += sizeof(USHORT);
  return retval;
}

static __inline ULONG
__GET_XEN_INIT_ULONG(PUCHAR *ptr)
{
  ULONG retval;
  retval = *(PLONG)*ptr;
//  KdPrint((__DRIVER_NAME "     GET_XEN_INIT_ULONG *ptr = %p, retval = %d\n", *ptr, retval));
  *ptr += sizeof(ULONG);
  return retval;
}

static __inline PCHAR
__GET_XEN_INIT_STRING(PUCHAR *ptr)
{
  PCHAR retval;
  retval = (PCHAR)*ptr;
//  KdPrint((__DRIVER_NAME "     GET_XEN_INIT_STRING *ptr = %p, retval = %s\n", *ptr, retval));
  *ptr += strlen((PCHAR)*ptr) + 1;
  return retval;
}

static __inline PVOID
__GET_XEN_INIT_PTR(PUCHAR *ptr)
{
  PVOID retval;
  retval = *(PVOID *)(*ptr);
//  KdPrint((__DRIVER_NAME "     GET_XEN_INIT_PTR *ptr = %p, retval = %p\n", *ptr, retval));
  *ptr += sizeof(PVOID);
  return retval;
}

static __inline VOID
ADD_XEN_INIT_REQ(PUCHAR *ptr, UCHAR type, PVOID p1, PVOID p2, PVOID p3)
{
  __ADD_XEN_INIT_UCHAR(ptr, type);
  switch (type)
  {
  case XEN_INIT_TYPE_END:
  case XEN_INIT_TYPE_VECTORS:
  case XEN_INIT_TYPE_STATE_PTR:
  case XEN_INIT_TYPE_QEMU_PROTOCOL_VERSION:
  case XEN_INIT_TYPE_QEMU_HIDE_FLAGS:
  case XEN_INIT_TYPE_QEMU_HIDE_FILTER:
  case XEN_INIT_TYPE_XB_STATE_MAP_PRE_CONNECT:
  case XEN_INIT_TYPE_XB_STATE_MAP_POST_CONNECT:
  case XEN_INIT_TYPE_XB_STATE_MAP_SHUTDOWN:
    break;
  case XEN_INIT_TYPE_WRITE_STRING:
    __ADD_XEN_INIT_STRING(ptr, (PCHAR) p1);
    __ADD_XEN_INIT_STRING(ptr, (PCHAR) p2);
    break;
  case XEN_INIT_TYPE_RING:
  case XEN_INIT_TYPE_EVENT_CHANNEL_IRQ:
  case XEN_INIT_TYPE_READ_STRING_FRONT:
  case XEN_INIT_TYPE_READ_STRING_BACK:
    __ADD_XEN_INIT_STRING(ptr, (PCHAR) p1);
    break;
  case XEN_INIT_TYPE_EVENT_CHANNEL:
  case XEN_INIT_TYPE_EVENT_CHANNEL_DPC:
    __ADD_XEN_INIT_STRING(ptr, (PCHAR) p1);
    __ADD_XEN_INIT_PTR(ptr, p2);
    __ADD_XEN_INIT_PTR(ptr, p3);
    break;
  case XEN_INIT_TYPE_GRANT_ENTRIES:
    __ADD_XEN_INIT_ULONG(ptr, PtrToUlong(p1));
    __ADD_XEN_INIT_ULONG(ptr, PtrToUlong(p2));
    break;
//  case XEN_INIT_TYPE_COPY_PTR:
//    __ADD_XEN_INIT_STRING(ptr, p1);
//    __ADD_XEN_INIT_PTR(ptr, p2);
//    break;
  }
}

static __inline UCHAR
GET_XEN_INIT_REQ(PUCHAR *ptr, PVOID *p1, PVOID *p2, PVOID *p3)
{
  UCHAR retval;

  retval = __GET_XEN_INIT_UCHAR(ptr);
  switch (retval)
  {
  case XEN_INIT_TYPE_END:
  case XEN_INIT_TYPE_VECTORS:
  case XEN_INIT_TYPE_STATE_PTR:
  case XEN_INIT_TYPE_QEMU_PROTOCOL_VERSION:
  case XEN_INIT_TYPE_XB_STATE_MAP_PRE_CONNECT:
  case XEN_INIT_TYPE_XB_STATE_MAP_POST_CONNECT:
  case XEN_INIT_TYPE_XB_STATE_MAP_SHUTDOWN:
    *p1 = NULL;
    *p2 = NULL;
    break;
  case XEN_INIT_TYPE_WRITE_STRING:
    *p1 = __GET_XEN_INIT_STRING(ptr);
    *p2 = __GET_XEN_INIT_STRING(ptr);
    break;
  case XEN_INIT_TYPE_RING:
  case XEN_INIT_TYPE_EVENT_CHANNEL_IRQ:
  case XEN_INIT_TYPE_READ_STRING_FRONT:
  case XEN_INIT_TYPE_READ_STRING_BACK:
    *p1 = __GET_XEN_INIT_STRING(ptr);
    *p2 = NULL;
    break;
  case XEN_INIT_TYPE_EVENT_CHANNEL:
  case XEN_INIT_TYPE_EVENT_CHANNEL_DPC:
    *p1 = __GET_XEN_INIT_STRING(ptr);
    *p2 = __GET_XEN_INIT_PTR(ptr);
    *p3 = __GET_XEN_INIT_PTR(ptr);
    break;
  case XEN_INIT_TYPE_GRANT_ENTRIES:
    *p1 = UlongToPtr(__GET_XEN_INIT_ULONG(ptr));
    *p2 = UlongToPtr(__GET_XEN_INIT_ULONG(ptr));
    break;
  }
  return retval;
}

static __inline VOID
ADD_XEN_INIT_RSP(PUCHAR *ptr, UCHAR type, PVOID p1, PVOID p2, PVOID p3)
{
  UNREFERENCED_PARAMETER(p3);

  __ADD_XEN_INIT_UCHAR(ptr, type);
  switch (type)
  {
  case XEN_INIT_TYPE_END:
  case XEN_INIT_TYPE_WRITE_STRING: /* this shouldn't happen */
  case XEN_INIT_TYPE_QEMU_HIDE_FILTER:
    break;
  case XEN_INIT_TYPE_RING:
    __ADD_XEN_INIT_STRING(ptr, (PCHAR) p1);
    __ADD_XEN_INIT_PTR(ptr, p2);
    break;
  case XEN_INIT_TYPE_EVENT_CHANNEL:
  case XEN_INIT_TYPE_EVENT_CHANNEL_DPC:
  case XEN_INIT_TYPE_EVENT_CHANNEL_IRQ:
    __ADD_XEN_INIT_STRING(ptr, (PCHAR) p1);
    __ADD_XEN_INIT_ULONG(ptr, PtrToUlong(p2));
    break;
  case XEN_INIT_TYPE_READ_STRING_FRONT:
  case XEN_INIT_TYPE_READ_STRING_BACK:
    __ADD_XEN_INIT_STRING(ptr, (PCHAR) p1);
    __ADD_XEN_INIT_STRING(ptr, (PCHAR) p2);
    break;
  case XEN_INIT_TYPE_VECTORS:
    //__ADD_XEN_INIT_ULONG(ptr, PtrToUlong(p1));
    memcpy(*ptr, p2, sizeof(XENPCI_VECTORS));
    *ptr += sizeof(XENPCI_VECTORS);
    break;
  case XEN_INIT_TYPE_GRANT_ENTRIES:
    __ADD_XEN_INIT_ULONG(ptr, PtrToUlong(p1));
    __ADD_XEN_INIT_ULONG(ptr, PtrToUlong(p2));
    memcpy(*ptr, p3, PtrToUlong(p2) * sizeof(grant_entry_t));
    *ptr += PtrToUlong(p2) * sizeof(grant_entry_t);
    break;
  case XEN_INIT_TYPE_QEMU_HIDE_FLAGS:
    __ADD_XEN_INIT_ULONG(ptr, PtrToUlong(p2));
    break;
  case XEN_INIT_TYPE_STATE_PTR:
    __ADD_XEN_INIT_PTR(ptr, p2);
    break;
  case XEN_INIT_TYPE_QEMU_PROTOCOL_VERSION:
    __ADD_XEN_INIT_ULONG(ptr, PtrToUlong(p2));
    break;
  }
}

static __inline UCHAR
GET_XEN_INIT_RSP(PUCHAR *ptr, PVOID *p1, PVOID *p2, PVOID *p3)
{
  UCHAR retval;

  UNREFERENCED_PARAMETER(p3);

  retval = __GET_XEN_INIT_UCHAR(ptr);
  switch (retval)
  {
  case XEN_INIT_TYPE_END:
  case XEN_INIT_TYPE_QEMU_HIDE_FILTER:
    *p1 = NULL;
    *p2 = NULL;
    break;
  case XEN_INIT_TYPE_WRITE_STRING:
    // this shouldn't happen - no response here
    break;
  case XEN_INIT_TYPE_RING:
    *p1 = __GET_XEN_INIT_STRING(ptr);
    *p2 = __GET_XEN_INIT_PTR(ptr);
    break;
  case XEN_INIT_TYPE_EVENT_CHANNEL:
  case XEN_INIT_TYPE_EVENT_CHANNEL_DPC:
  case XEN_INIT_TYPE_EVENT_CHANNEL_IRQ:
    *p1 = __GET_XEN_INIT_STRING(ptr);
    *p2 = UlongToPtr(__GET_XEN_INIT_ULONG(ptr));
    break;
  case XEN_INIT_TYPE_READ_STRING_FRONT:
    *p1 = __GET_XEN_INIT_STRING(ptr);
    *p2 = __GET_XEN_INIT_STRING(ptr);
    break;
  case XEN_INIT_TYPE_READ_STRING_BACK:
    *p1 = __GET_XEN_INIT_STRING(ptr);
    *p2 = __GET_XEN_INIT_STRING(ptr);
    break;
  case XEN_INIT_TYPE_VECTORS:
    *p1 = NULL;
    *p2 = *ptr;
    *ptr += ((PXENPCI_VECTORS)*p2)->length;
    break;
  case XEN_INIT_TYPE_GRANT_ENTRIES:
    *p1 = UlongToPtr(__GET_XEN_INIT_ULONG(ptr));
    *p2 = UlongToPtr(__GET_XEN_INIT_ULONG(ptr));
    *p3 = *ptr;
    *ptr += PtrToUlong(*p2) * sizeof(grant_ref_t);
    break;
  case XEN_INIT_TYPE_STATE_PTR:
    *p2 = __GET_XEN_INIT_PTR(ptr);
    break;
  case XEN_INIT_TYPE_QEMU_HIDE_FLAGS:
    *p2 = UlongToPtr(__GET_XEN_INIT_ULONG(ptr));
    break;
  case XEN_INIT_TYPE_QEMU_PROTOCOL_VERSION:
    *p2 = UlongToPtr(__GET_XEN_INIT_ULONG(ptr));
    break;
  }
  return retval;
}

typedef BOOLEAN
(*PXEN_DMA_NEED_VIRTUAL_ADDRESS)(PIRP irp);

typedef ULONG
(*PXEN_DMA_GET_ALIGNMENT)(PIRP irp);

typedef struct {
  PXEN_DMA_NEED_VIRTUAL_ADDRESS need_virtual_address;
  PXEN_DMA_GET_ALIGNMENT get_alignment;
  ULONG max_sg_elements;
} dma_driver_extension_t;

#endif
