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

#if !defined(_XENPCI_H_)
#define _XENPCI_H_

#define __attribute__(arg) /* empty */
#define EISCONN 127

#include <ntddk.h>

#include <wdf.h>
#include <initguid.h>
#include <wdmguid.h>
#include <errno.h>
#define NTSTRSAFE_LIB
#include <ntstrsafe.h>

#include <liblfds.h>

#define __DRIVER_NAME "XenPCI"

#include <xen_windows.h>
#include <memory.h>
#include <grant_table.h>
#include <event_channel.h>
#include <hvm/params.h>
#include <hvm/hvm_op.h>
#include <sched.h>
#include <io/xenbus.h>
#include <io/xs_wire.h>

#include <xen_public.h>

//{C828ABE9-14CA-4445-BAA6-82C2376C6518}
DEFINE_GUID( GUID_XENPCI_DEVCLASS, 0xC828ABE9, 0x14CA, 0x4445, 0xBA, 0xA6, 0x82, 0xC2, 0x37, 0x6C, 0x65, 0x18);

#define XENPCI_POOL_TAG (ULONG) 'XenP'

#define NR_RESERVED_ENTRIES 8
#define NR_GRANT_FRAMES 32
#define NR_GRANT_ENTRIES (NR_GRANT_FRAMES * PAGE_SIZE / sizeof(grant_entry_t))

#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))

#define EVT_ACTION_TYPE_EMPTY   0
#define EVT_ACTION_TYPE_NORMAL  1
#define EVT_ACTION_TYPE_DPC     2
//#define EVT_ACTION_TYPE_IRQ     3
//#define EVT_ACTION_TYPE_SUSPEND 4
#define EVT_ACTION_TYPE_NEW     9 /* setup of event is in progress */

#define EVT_ACTION_FLAGS_DEFAULT    0 /* no special flags */
#define EVT_ACTION_FLAGS_NO_SUSPEND 1 /* should not be fired on EVT_ACTION_TYPE_SUSPEND event */

#define XEN_PV_PRODUCT_NUMBER   0x0002
#define XEN_PV_PRODUCT_BUILD    0x00000001

#define BALLOON_UNITS_KB (1 * 1024) /* 1MB */
#define BALLOON_UNIT_PAGES ((BALLOON_UNITS_KB << 10) >> PAGE_SHIFT)

extern PVOID hypercall_stubs;
extern ULONG qemu_protocol_version;
extern USHORT xen_version_major;
extern USHORT xen_version_minor;

typedef struct _ev_action_t {
  PVOID xpdd;
  //evtchn_port_t port;
  PXN_EVENT_CALLBACK ServiceRoutine;
  PVOID ServiceContext;
  CHAR description[128];
  ULONG type; /* EVT_ACTION_TYPE_* */
  ULONG flags; /* EVT_ACTION_FLAGS_* */
  KDPC Dpc;
  ULONG vector;
  ULONG count;
} ev_action_t;

typedef struct _XENBUS_WATCH_RING
{
  char Path[128];
  char Token[10];
} XENBUS_WATCH_RING;

typedef struct xsd_sockmsg xsd_sockmsg_t;

typedef struct _XENBUS_WATCH_ENTRY {
  char Path[128];
  PXN_WATCH_CALLBACK ServiceRoutine;
  PVOID ServiceContext;
  int Count;
  int Active;
} XENBUS_WATCH_ENTRY, *PXENBUS_WATCH_ENTRY;

/* number of events is 1024 on 32 bits and 4096 on 64 bits */
#define NR_EVENTS (sizeof(xen_ulong_t) * 8 * sizeof(xen_ulong_t) * 8)
#define WATCH_RING_SIZE 128
#define NR_XB_REQS 32
#define MAX_WATCH_ENTRIES 128

#define CHILD_STATE_EMPTY 0
#define CHILD_STATE_DELETED 1
#define CHILD_STATE_ADDED 2

#define SUSPEND_STATE_NONE      0 /* no suspend in progress */
#define SUSPEND_STATE_SCHEDULED 1 /* suspend scheduled */
#define SUSPEND_STATE_HIGH_IRQL 2 /* all processors are at high IRQL and spinning */
#define SUSPEND_STATE_RESUMING  3 /* we are the other side of the suspend and things are starting to get back to normal */

/* we take some grant refs out and put them aside so that we dont get corrupted by hibernate */
#define HIBER_GREF_COUNT 128

typedef struct {
  ULONG generation;
  ULONG tag;
} grant_tag_t;

typedef struct {  
  WDFDEVICE wdf_device;
  
  BOOLEAN tpr_patched;

  WDFINTERRUPT interrupt;
  ULONG irq_number;
  ULONG irq_vector;
  KIRQL irq_level;
  KINTERRUPT_MODE irq_mode;
  KAFFINITY irq_affinity;
  
  PHYSICAL_ADDRESS shared_info_area_unmapped;
  shared_info_t *shared_info_area;
  xen_ulong_t evtchn_pending_pvt[MAX_VIRT_CPUS][sizeof(xen_ulong_t) * 8];
  xen_ulong_t evtchn_pending_suspend[sizeof(xen_ulong_t) * 8];
  //evtchn_port_t pdo_event_channel;
  //KEVENT pdo_suspend_event;
  BOOLEAN interrupts_masked;
  
  PHYSICAL_ADDRESS platform_mmio_addr;
  ULONG platform_mmio_orig_len;
  ULONG platform_mmio_len;
  ULONG platform_mmio_alloc;
  USHORT platform_mmio_flags;
  
  ULONG platform_ioport_addr;
  ULONG platform_ioport_len;

  evtchn_port_t xenbus_event;

  /* grant related */
  struct stack_state *gnttbl_ss;
  struct stack_state *gnttbl_ss_copy;
  grant_ref_t hiber_grefs[HIBER_GREF_COUNT];
  PMDL gnttbl_mdl;
  grant_entry_t *gnttbl_table;
  grant_entry_t *gnttbl_table_copy;
  #if DBG
  ULONG gnttbl_generation; /* incremented once per save or hibernate */
  grant_tag_t *gnttbl_tag;
  grant_tag_t *gnttbl_tag_copy;
  #endif
  ULONG grant_frames;

  ev_action_t ev_actions[NR_EVENTS];
//  unsigned long bound_ports[NR_EVENTS/(8*sizeof(unsigned long))];

  BOOLEAN xb_state;
  
  struct xenstore_domain_interface *xen_store_interface;

  PKTHREAD balloon_thread;
  KEVENT balloon_event;
  BOOLEAN balloon_shutdown;
  //ULONG initial_memory_kb;
  ULONG current_memory_kb;
  ULONG target_memory_kb;
  
  /* xenbus related */
  XENBUS_WATCH_ENTRY XenBus_WatchEntries[MAX_WATCH_ENTRIES];
  KSPIN_LOCK xb_ring_spinlock;
  FAST_MUTEX xb_watch_mutex;
  FAST_MUTEX xb_request_mutex;
  KEVENT xb_request_complete_event;
  struct xsd_sockmsg *xb_reply;
  struct xsd_sockmsg *xb_msg;
  ULONG xb_msg_offset;
  
  WDFCHILDLIST child_list;
  
  FAST_MUTEX suspend_mutex;
  
  ULONG suspend_evtchn;
  int suspend_state;
  
  UNICODE_STRING legacy_interface_name;
  UNICODE_STRING interface_name;
  BOOLEAN interface_open;

  BOOLEAN removable;
  
  BOOLEAN hibernated;
  
  WDFQUEUE io_queue;

  //WDFCOLLECTION veto_devices;
  LIST_ENTRY veto_list;

#if 0
  KSPIN_LOCK mmio_freelist_lock;
  PPFN_NUMBER mmio_freelist_base;
  ULONG mmio_freelist_free;
#endif

} XENPCI_DEVICE_DATA, *PXENPCI_DEVICE_DATA;

WDF_DECLARE_CONTEXT_TYPE_WITH_NAME(XENPCI_DEVICE_DATA, GetXpdd)

typedef struct {
  UCHAR front_target;
  UCHAR back_expected;
  UCHAR wait; /* units = 100ms */
} XENPCI_STATE_MAP_ELEMENT, *PXENPCI_STATE_MAP_ELEMENT;

typedef struct {  
  WDFDEVICE wdf_device;
  WDFDEVICE wdf_device_bus_fdo;
  PXENPCI_DEVICE_DATA xpdd;
  BOOLEAN reported_missing;
  char path[128];
  char device[128];
  ULONG index;
  ULONG irq_number;
  ULONG irq_vector;
  KIRQL irq_level;
  char backend_path[128];
  domid_t backend_id;
  KEVENT backend_state_event;
  ULONG backend_state;
  PXN_DEVICE_CALLBACK device_callback;
  PVOID device_callback_context;
  FAST_MUTEX backend_state_mutex;
  ULONG frontend_state;
  BOOLEAN restart_on_resume;
  BOOLEAN backend_initiated_remove;
  BOOLEAN do_not_enumerate;
  
  XENPCI_STATE_MAP_ELEMENT xb_pre_connect_map[5];
  XENPCI_STATE_MAP_ELEMENT xb_post_connect_map[5];
  XENPCI_STATE_MAP_ELEMENT xb_shutdown_map[5];
  
  BOOLEAN hiber_usage_kludge;
} XENPCI_PDO_DEVICE_DATA, *PXENPCI_PDO_DEVICE_DATA;

WDF_DECLARE_CONTEXT_TYPE_WITH_NAME(XENPCI_PDO_DEVICE_DATA, GetXppdd)

typedef struct {
  WDF_CHILD_IDENTIFICATION_DESCRIPTION_HEADER header;
  CHAR path[128];
  CHAR device[128];
  ULONG index;
} XENPCI_PDO_IDENTIFICATION_DESCRIPTION, *PXENPCI_PDO_IDENTIFICATION_DESCRIPTION;

#define XEN_INTERFACE_VERSION 1

//#define DEVICE_INTERFACE_TYPE_LEGACY 0
#define DEVICE_INTERFACE_TYPE_XENBUS 1
#define DEVICE_INTERFACE_TYPE_EVTCHN 2
#define DEVICE_INTERFACE_TYPE_GNTDEV 3

typedef struct {
  ULONG len;
  WDFQUEUE io_queue;
  union {
    struct xsd_sockmsg msg;
    UCHAR buffer[PAGE_SIZE];
  } u;
  LIST_ENTRY read_list_head;
  LIST_ENTRY watch_list_head;
} XENBUS_INTERFACE_DATA, *PXENBUS_INTERFACE_DATA;

typedef struct {
  ULONG dummy; /* fill this in with whatever is required */
} EVTCHN_INTERFACE_DATA, *PEVTCHN_INTERFACE_DATA;

typedef struct {
  ULONG dummy;  /* fill this in with whatever is required */
} GNTDEV_INTERFACE_DATA, *PGNTDEV_INTERFACE_DATA;

typedef struct {
  ULONG type;
  KSPIN_LOCK lock;
  WDFQUEUE io_queue;
  EVT_WDF_FILE_CLEANUP *EvtFileCleanup;
  EVT_WDF_FILE_CLOSE *EvtFileClose;
  union {
    XENBUS_INTERFACE_DATA xenbus;
    EVTCHN_INTERFACE_DATA evtchn;
    GNTDEV_INTERFACE_DATA gntdev;
  };
} XENPCI_DEVICE_INTERFACE_DATA, *PXENPCI_DEVICE_INTERFACE_DATA;

WDF_DECLARE_CONTEXT_TYPE_WITH_NAME(XENPCI_DEVICE_INTERFACE_DATA, GetXpdid)

static __inline VOID
XenPci_FreeMem(PVOID Ptr) {
  ExFreePoolWithTag(Ptr, XENPCI_POOL_TAG);
}

NTSTATUS XenBus_DeviceFileInit(WDFDEVICE device, PWDF_IO_QUEUE_CONFIG queue_config, WDFFILEOBJECT file_object);

EVT_WDF_DEVICE_FILE_CREATE XenPci_EvtDeviceFileCreate;
EVT_WDF_FILE_CLOSE XenPci_EvtFileClose;
EVT_WDF_FILE_CLEANUP XenPci_EvtFileCleanup;
EVT_WDF_IO_QUEUE_IO_DEFAULT XenPci_EvtIoDefault;

#if 0
#define HYPERVISOR_memory_op(xpdd, cmd, arg) _HYPERVISOR_memory_op(xpdd->hypercall_stubs, cmd, arg)
#define HYPERVISOR_xen_version(xpdd, cmd, arg) _HYPERVISOR_xen_version(xpdd->hypercall_stubs, cmd, arg)
#define HYPERVISOR_grant_table_op(xpdd, cmd, uop, count) _HYPERVISOR_grant_table_op(xpdd->hypercall_stubs, cmd, uop, count)
#define HYPERVISOR_hvm_op(xpdd, op, arg) _HYPERVISOR_hvm_op(xpdd->hypercall_stubs, op, arg)
#define HYPERVISOR_event_channel_op(xpdd, cmd, op) _HYPERVISOR_event_channel_op(xpdd->hypercall_stubs, cmd, op)
#define HYPERVISOR_sched_op(xpdd, cmd, arg) _HYPERVISOR_sched_op(xpdd->hypercall_stubs, cmd, arg)
#define HYPERVISOR_shutdown(xpdd, reason) _HYPERVISOR_shutdown(xpdd->hypercall_stubs, reason)

#define hvm_get_parameter(xvdd, hvm_param) _hvm_get_parameter(xvdd->hypercall_stubs, hvm_param);
#define hvm_set_parameter(xvdd, hvm_param, value) _hvm_set_parameter(xvdd->hypercall_stubs, hvm_param, value);
#define hvm_shutdown(xvdd, reason) _hvm_shutdown(xvdd->hypercall_stubs, reason);
#define HYPERVISOR_yield(xvdd) _HYPERVISOR_yield(xvdd->hypercall_stubs);
#endif

#include "hypercall.h"

#define XBT_NIL ((xenbus_transaction_t)0)

//VOID hvm_get_hypercall_stubs();
//VOID hvm_free_hypercall_stubs();

EVT_WDF_DEVICE_PREPARE_HARDWARE XenPci_EvtDevicePrepareHardware;
EVT_WDF_DEVICE_RELEASE_HARDWARE XenPci_EvtDeviceReleaseHardware;
EVT_WDF_DEVICE_D0_ENTRY XenPci_EvtDeviceD0Entry;
EVT_WDF_DEVICE_D0_ENTRY_POST_INTERRUPTS_ENABLED XenPci_EvtDeviceD0EntryPostInterruptsEnabled;
EVT_WDF_DEVICE_D0_EXIT XenPci_EvtDeviceD0Exit;
EVT_WDF_DEVICE_D0_EXIT_PRE_INTERRUPTS_DISABLED XenPci_EvtDeviceD0ExitPreInterruptsDisabled;
EVT_WDF_DEVICE_QUERY_REMOVE XenPci_EvtDeviceQueryRemove;
EVT_WDF_CHILD_LIST_CREATE_DEVICE XenPci_EvtChildListCreateDevice;
EVT_WDF_CHILD_LIST_SCAN_FOR_CHILDREN XenPci_EvtChildListScanForChildren;

VOID XenPci_HideQemuDevices();
extern WDFCOLLECTION qemu_hide_devices;
extern USHORT qemu_hide_flags_value;

VOID XenPci_BackendStateCallback(char *path, PVOID context);
NTSTATUS XenPci_SuspendPdo(WDFDEVICE device);
NTSTATUS XenPci_ResumePdo(WDFDEVICE device);


VOID XenPci_DumpPdoConfig(PDEVICE_OBJECT device_object);

typedef VOID (*PXENPCI_HIGHSYNC_FUNCTION)(PVOID context);

VOID XenPci_HighSync(PXENPCI_HIGHSYNC_FUNCTION function0, PXENPCI_HIGHSYNC_FUNCTION functionN, PVOID context);

VOID XenPci_PatchKernel(PXENPCI_DEVICE_DATA xpdd, PVOID base, ULONG length);

//NTSTATUS XenPci_HookDbgPrint();
//NTSTATUS XenPci_ReHookDbgPrint();
//NTSTATUS XenPci_UnHookDbgPrint();
//VOID XenPci_DumpModeHookDebugPrint();
#include <stdlib.h>

NTSTATUS
XenPci_DebugPrintV(PCHAR format, va_list args);
NTSTATUS
XenPci_DebugPrint(PCHAR format, ...);

struct xsd_sockmsg *XenBus_Raw(PXENPCI_DEVICE_DATA xpdd, struct xsd_sockmsg *msg);
char *XenBus_Read(PVOID Context, xenbus_transaction_t xbt, char *path, char **value);
char *XenBus_Write(PVOID Context, xenbus_transaction_t xbt, char *path, char *value);
char *XenBus_Printf(PVOID Context, xenbus_transaction_t xbt, char *path, char *fmt, ...);
char *XenBus_StartTransaction(PVOID Context, xenbus_transaction_t *xbt);
char *XenBus_EndTransaction(PVOID Context, xenbus_transaction_t t, int abort, int *retry);
char *XenBus_List(PVOID Context, xenbus_transaction_t xbt, char *prefix, char ***contents);
char *XenBus_AddWatch(PVOID Context, xenbus_transaction_t xbt, char *Path, PXN_WATCH_CALLBACK ServiceRoutine, PVOID ServiceContext);
char *XenBus_RemWatch(PVOID Context, xenbus_transaction_t xbt, char *Path, PXN_WATCH_CALLBACK ServiceRoutine, PVOID ServiceContext);
NTSTATUS XenBus_Init(PXENPCI_DEVICE_DATA xpdd);
NTSTATUS XenBus_Halt(PXENPCI_DEVICE_DATA xpdd);
NTSTATUS XenBus_Suspend(PXENPCI_DEVICE_DATA xpdd);
NTSTATUS XenBus_Resume(PXENPCI_DEVICE_DATA xpdd);

PHYSICAL_ADDRESS
XenPci_AllocMMIO(PXENPCI_DEVICE_DATA xpdd, ULONG len);

EVT_WDF_INTERRUPT_ISR EvtChn_EvtInterruptIsr;
EVT_WDF_INTERRUPT_ENABLE EvtChn_EvtInterruptEnable;
EVT_WDF_INTERRUPT_DISABLE EvtChn_EvtInterruptDisable;

NTSTATUS EvtChn_Init(PXENPCI_DEVICE_DATA xpdd);
NTSTATUS EvtChn_Suspend(PXENPCI_DEVICE_DATA xpdd);
NTSTATUS EvtChn_Resume(PXENPCI_DEVICE_DATA xpdd);

NTSTATUS EvtChn_Mask(PVOID context, evtchn_port_t port);
NTSTATUS EvtChn_Unmask(PVOID context, evtchn_port_t port);
NTSTATUS EvtChn_Bind(PVOID context, evtchn_port_t port, PXN_EVENT_CALLBACK ServiceRoutine, PVOID ServiceContext, ULONG flags);
NTSTATUS EvtChn_BindDpc(PVOID context, evtchn_port_t port, PXN_EVENT_CALLBACK ServiceRoutine, PVOID ServiceContext, ULONG flags);
NTSTATUS EvtChn_Unbind(PVOID context, evtchn_port_t port);
NTSTATUS EvtChn_Notify(PVOID context, evtchn_port_t port);
VOID EvtChn_Close(PVOID context, evtchn_port_t port);
evtchn_port_t EvtChn_AllocUnbound(PVOID context, domid_t domain);
evtchn_port_t EvtChn_GetEventPort(PVOID context, evtchn_port_t port);

VOID GntTbl_Init(PXENPCI_DEVICE_DATA xpdd);
VOID GntTbl_Suspend(PXENPCI_DEVICE_DATA xpdd);
VOID GntTbl_Resume(PXENPCI_DEVICE_DATA xpdd);
grant_ref_t GntTbl_GrantAccess(PVOID Context, domid_t domid, uint32_t, int readonly, grant_ref_t ref, ULONG tag);
BOOLEAN GntTbl_EndAccess(PVOID Context, grant_ref_t ref, BOOLEAN keepref, ULONG tag);
VOID GntTbl_PutRef(PVOID Context, grant_ref_t ref, ULONG tag);
grant_ref_t GntTbl_GetRef(PVOID Context, ULONG tag);

#endif
