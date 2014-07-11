/*
PV Drivers for Windows Xen HVM Domains
Copyright (C) 2013 James Harper

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

#include "xencache.h"

#define TMEM_CONTROL               0
#define TMEM_NEW_POOL              1
#define TMEM_DESTROY_POOL          2
#define TMEM_NEW_PAGE              3
#define TMEM_PUT_PAGE              4
#define TMEM_GET_PAGE              5
#define TMEM_FLUSH_PAGE            6
#define TMEM_FLUSH_OBJECT          7
#define TMEM_READ                  8
#define TMEM_WRITE                 9
#define TMEM_XCHG                 10

/* Bits for HYPERVISOR_tmem_op(TMEM_NEW_POOL) */
#define TMEM_POOL_PERSIST          1
#define TMEM_POOL_SHARED           2
#define TMEM_POOL_PAGESIZE_SHIFT   4
#define TMEM_VERSION_SHIFT        24

/* flags for tmem_ops.new_pool */
#define TMEM_POOL_PERSIST          1
#define TMEM_POOL_SHARED           2

PFLT_FILTER filter_handle;
global_context_t global_context;

DRIVER_INITIALIZE DriverEntry;

NTSTATUS XenCache_FilterUnload(FLT_FILTER_UNLOAD_FLAGS flags);
NTSTATUS XenCache_InstanceSetup(PCFLT_RELATED_OBJECTS flt_objects, FLT_INSTANCE_SETUP_FLAGS flags, DEVICE_TYPE volume_device_type, FLT_FILESYSTEM_TYPE volume_filesystem_type);
NTSTATUS XenCache_InstanceQueryTeardown(PCFLT_RELATED_OBJECTS flt_objects, FLT_INSTANCE_QUERY_TEARDOWN_FLAGS flags);
VOID XenCache_InstanceTeardownStart(PCFLT_RELATED_OBJECTS flt_objects, FLT_INSTANCE_QUERY_TEARDOWN_FLAGS reason);
VOID XenCache_InstanceTeardownComplete(PCFLT_RELATED_OBJECTS flt_objects, FLT_INSTANCE_QUERY_TEARDOWN_FLAGS reason);

FLT_PREOP_CALLBACK_STATUS XenCache_Pre_CLOSE(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID *completion_context);
FLT_POSTOP_CALLBACK_STATUS XenCache_Pst_CLOSE(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID completion_context, FLT_POST_OPERATION_FLAGS flags);
FLT_PREOP_CALLBACK_STATUS XenCache_Pre_CLEANUP(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID *completion_context);
FLT_POSTOP_CALLBACK_STATUS XenCache_Pst_CLEANUP(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID completion_context, FLT_POST_OPERATION_FLAGS flags);
FLT_PREOP_CALLBACK_STATUS XenCache_Pre_READ(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID *completion_context);
FLT_PREOP_CALLBACK_STATUS XenCache_Pre_WRITE(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID *completion_context);

FLT_OPERATION_REGISTRATION filter_callbacks[] = {
  { IRP_MJ_CLOSE, 0, XenCache_Pre_CLOSE, XenCache_Pst_CLOSE },
  { IRP_MJ_CLEANUP, 0, XenCache_Pre_CLEANUP, XenCache_Pst_CLEANUP },
  { IRP_MJ_READ, 0, XenCache_Pre_READ, NULL },
  { IRP_MJ_WRITE, 0, XenCache_Pre_WRITE, NULL },
  { IRP_MJ_OPERATION_END }
};

FLT_REGISTRATION filter_registration = {
  sizeof(FLT_REGISTRATION),
  FLT_REGISTRATION_VERSION,
  0, // flags
  NULL, // context_callbacks,
  filter_callbacks,
  XenCache_FilterUnload,
  XenCache_InstanceSetup,
  XenCache_InstanceQueryTeardown,
  XenCache_InstanceTeardownStart,
  XenCache_InstanceTeardownComplete,
  NULL, // XenCache_GenerateFileName,
  NULL, // XenCache_NormalizeNameComponentn,
  NULL, // XenCache_NormalizeContextCleanup,
#if FLT_MGR_LONGHORN
  NULL, // XenCache_TransactionNotification,
  NULL, // XenCache_NormalizeNameComponentEx,
#endif
};

NTSTATUS
DriverEntry(PDRIVER_OBJECT driver_object, PUNICODE_STRING registry_path) {
  NTSTATUS status;

  UNREFERENCED_PARAMETER(registry_path);
  
  FUNCTION_ENTER();

  RtlZeroMemory(&global_context, sizeof(global_context_t));
  KeInitializeSpinLock(&global_context.lock);
  
  status = FltRegisterFilter(driver_object, &filter_registration, &filter_handle);
  FUNCTION_MSG("FltRegisterFilter = %08x\n", status);
  
  if (!NT_SUCCESS(status)) {
    FUNCTION_EXIT();
    return status;
  }
  status = FltStartFiltering(filter_handle);
  FUNCTION_MSG("FltStartFiltering = %08x\n", status);
  if (!NT_SUCCESS(status)) {
    FltUnregisterFilter(filter_handle);
  }
  
  FUNCTION_EXIT();

  return status;
}

NTSTATUS
XenCache_FilterUnload(FLT_FILTER_UNLOAD_FLAGS flags) {
  UNREFERENCED_PARAMETER(flags);
  FUNCTION_ENTER();
  FltUnregisterFilter(filter_handle);
  RtlZeroMemory(&global_context, sizeof(global_context_t));
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

NTSTATUS
XenCache_InstanceSetup(PCFLT_RELATED_OBJECTS flt_objects, FLT_INSTANCE_SETUP_FLAGS flags, DEVICE_TYPE volume_device_type, FLT_FILESYSTEM_TYPE volume_filesystem_type) {
  FUNCTION_ENTER();
  if (volume_device_type != FILE_DEVICE_DISK_FILE_SYSTEM) {
    FUNCTION_MSG("is not disk\n");
    FUNCTION_EXIT();
    return STATUS_FLT_DO_NOT_ATTACH;
  }
  if (volume_filesystem_type != FLT_FSTYPE_NTFS) {
    FUNCTION_MSG("is not NTFS\n");
    FUNCTION_EXIT();
    return STATUS_FLT_DO_NOT_ATTACH;
  }    
  FUNCTION_MSG("flt_objects = %p\n", flt_objects);
  FUNCTION_MSG("flags = %08x\n", flags);
  FUNCTION_MSG("volume_device_type = %08x\n", volume_device_type);
  FUNCTION_MSG("volume_filesystem_type = %08x\n", volume_filesystem_type);
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

NTSTATUS
XenCache_InstanceQueryTeardown(PCFLT_RELATED_OBJECTS flt_objects, FLT_INSTANCE_QUERY_TEARDOWN_FLAGS flags) {
  FUNCTION_ENTER();
  FUNCTION_MSG("flt_objects = %p\n", flt_objects);
  FUNCTION_MSG("flags = %08x\n", flags);
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

VOID
XenCache_InstanceTeardownStart(PCFLT_RELATED_OBJECTS flt_objects, FLT_INSTANCE_QUERY_TEARDOWN_FLAGS reason) {
  FUNCTION_ENTER();
  FUNCTION_MSG("flt_objects = %p\n", flt_objects);
  FUNCTION_MSG("reason = %08x\n", reason);
  FUNCTION_EXIT();
}

VOID
XenCache_InstanceTeardownComplete(PCFLT_RELATED_OBJECTS flt_objects, FLT_INSTANCE_QUERY_TEARDOWN_FLAGS reason) {
  FUNCTION_ENTER();
  FUNCTION_MSG("flt_objects = %p\n", flt_objects);
  FUNCTION_MSG("reason = %08x\n", reason);
  FUNCTION_EXIT();
}

FLT_PREOP_CALLBACK_STATUS
XenCache_Pre_CLOSE(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID *completion_context) {
  UNREFERENCED_PARAMETER(data);
  UNREFERENCED_PARAMETER(flt_objects);
  UNREFERENCED_PARAMETER(completion_context);
  if (FsRtlIsPagingFile(flt_objects->FileObject)) {
    FUNCTION_ENTER();
    FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
    FUNCTION_MSG("FileObject = %p\n", flt_objects->FileObject);
    FUNCTION_MSG("FileName = %S\n", flt_objects->FileObject->FileName.Buffer);
    FUNCTION_MSG("IsPagingFile = %d\n", FsRtlIsPagingFile(flt_objects->FileObject));
    FUNCTION_EXIT();
  }
#if 0
  FUNCTION_ENTER();
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
  FUNCTION_MSG("FileObject = %p\n", flt_objects->FileObject);
  FUNCTION_MSG("FileName = %S\n", flt_objects->FileObject->FileName.Buffer);
  FUNCTION_MSG("IsPagingFile = %d\n", FsRtlIsPagingFile(flt_objects->FileObject));
  FUNCTION_EXIT();
#endif
  return FLT_PREOP_SUCCESS_WITH_CALLBACK;
}

FLT_POSTOP_CALLBACK_STATUS
XenCache_Pst_CLOSE(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID completion_context, FLT_POST_OPERATION_FLAGS flags) {
  UNREFERENCED_PARAMETER(data);
  UNREFERENCED_PARAMETER(flt_objects);
  UNREFERENCED_PARAMETER(completion_context);
  UNREFERENCED_PARAMETER(flags);
  if (FsRtlIsPagingFile(flt_objects->FileObject)) {
    FUNCTION_ENTER();
    FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
    FUNCTION_MSG("FileObject = %p\n", flt_objects->FileObject);
    FUNCTION_MSG("FileName = %S\n", flt_objects->FileObject->FileName.Buffer);
    FUNCTION_MSG("IsPagingFile = %d\n", FsRtlIsPagingFile(flt_objects->FileObject));
    FUNCTION_EXIT();
  }
#if 0
  FUNCTION_ENTER();
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
  FUNCTION_MSG("FileObject = %p\n", flt_objects->FileObject);
  FUNCTION_MSG("FileName = %S\n", flt_objects->FileObject->FileName.Buffer);
  FUNCTION_MSG("IsPagingFile = %d\n", FsRtlIsPagingFile(flt_objects->FileObject));
  FUNCTION_EXIT();
#endif
  return FLT_POSTOP_FINISHED_PROCESSING;
}

FLT_PREOP_CALLBACK_STATUS
XenCache_Pre_CLEANUP(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID *completion_context) {
  UNREFERENCED_PARAMETER(data);
  UNREFERENCED_PARAMETER(flt_objects);
  UNREFERENCED_PARAMETER(completion_context);
  if (FsRtlIsPagingFile(flt_objects->FileObject)) {
    FUNCTION_ENTER();
    FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
    FUNCTION_MSG("FileObject = %p\n", flt_objects->FileObject);
    FUNCTION_MSG("FileName = %S\n", flt_objects->FileObject->FileName.Buffer);
    FUNCTION_MSG("IsPagingFile = %d\n", FsRtlIsPagingFile(flt_objects->FileObject));
    FUNCTION_EXIT();
  }
#if 0
  FUNCTION_ENTER();
  FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
  FUNCTION_MSG("FileObject = %p\n", flt_objects->FileObject);
  FUNCTION_MSG("FileName = %S\n", flt_objects->FileObject->FileName.Buffer);
  FUNCTION_MSG("IsPagingFile = %d\n", FsRtlIsPagingFile(flt_objects->FileObject));
  FUNCTION_EXIT();
#endif
  return FLT_PREOP_SUCCESS_WITH_CALLBACK;
}

FLT_POSTOP_CALLBACK_STATUS
XenCache_Pst_CLEANUP(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID completion_context, FLT_POST_OPERATION_FLAGS flags) {
  UNREFERENCED_PARAMETER(data);
  UNREFERENCED_PARAMETER(flt_objects);
  UNREFERENCED_PARAMETER(completion_context);
  UNREFERENCED_PARAMETER(flags);
  if (FsRtlIsPagingFile(flt_objects->FileObject)) {
    FUNCTION_ENTER();
    FUNCTION_MSG("IRQL = %d\n", KeGetCurrentIrql());
    FUNCTION_MSG("FileObject = %p\n", flt_objects->FileObject);
    FUNCTION_MSG("FileName = %S\n", flt_objects->FileObject->FileName.Buffer);
    FUNCTION_MSG("IsPagingFile = %d\n", FsRtlIsPagingFile(flt_objects->FileObject));
    FUNCTION_EXIT();
  }
  return FLT_POSTOP_FINISHED_PROCESSING;
}

FLT_PREOP_CALLBACK_STATUS
XenCache_Pre_WRITE(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID *completion_context) {
  pagefile_context_t *context;
  int i;
  KIRQL old_irql;
  LONG rc;
  struct tmem_op tmem_op;

  UNREFERENCED_PARAMETER(data);
  UNREFERENCED_PARAMETER(flt_objects);
  UNREFERENCED_PARAMETER(completion_context);

  if (global_context.error_count) {
    return FLT_PREOP_SUCCESS_NO_CALLBACK;
  }
  if (!FsRtlIsPagingFile(flt_objects->FileObject)) {
    return FLT_PREOP_SUCCESS_NO_CALLBACK;
  }

  if (!(data->Flags & FLTFL_CALLBACK_DATA_IRP_OPERATION)) {
    return FLT_PREOP_SUCCESS_NO_CALLBACK;
  }

  KeAcquireSpinLock(&global_context.lock, &old_irql);
  for (context = global_context.pagefile_head; context; context = context->next) {
    if (context->file_object == flt_objects->FileObject)
      break;
  }
  if (!context) {
    context = ExAllocatePoolWithTag(NonPagedPool, sizeof(pagefile_context_t), XENCACHE_POOL_TAG);
    if (!context) {
      FUNCTION_MSG("Failed to allocate context\n");
      /* should probably detach this instance here */
      KeReleaseSpinLock(&global_context.lock, old_irql);
      FUNCTION_EXIT();
      return FLT_PREOP_SUCCESS_NO_CALLBACK;
    }
    RtlZeroMemory(context, sizeof(pagefile_context_t));
    context->file_object = flt_objects->FileObject;
    context->next = global_context.pagefile_head;
    tmem_op.cmd = TMEM_NEW_POOL;
    tmem_op.pool_id = 0; /* this doesn't actually get used for private */
    tmem_op.u.new.flags = (TMEM_SPEC_VERSION << TMEM_VERSION_SHIFT); /* private, not shared */
    context->pool_id = XnTmemOp(&tmem_op);
    FUNCTION_MSG("pool_id = %d\n", context->pool_id);
    if (context->pool_id < 0) {
      ExFreePoolWithTag(context, XENCACHE_POOL_TAG);
      global_context.error_count++;
      KeReleaseSpinLock(&global_context.lock, old_irql);
      /* should actually unload here */
      return FLT_PREOP_SUCCESS_NO_CALLBACK;
    }
    global_context.pagefile_head = context;
  }

  for (i = 0; i < (int)data->Iopb->Parameters.Write.Length >> PAGE_SHIFT; i++) {
    ULONG page = (ULONG)(data->Iopb->Parameters.Write.ByteOffset.QuadPart >> PAGE_SHIFT) + i;
    
    tmem_op.cmd = TMEM_PUT_PAGE;
    tmem_op.pool_id = context->pool_id;
    tmem_op.u.gen.oid[0] = 0;
    tmem_op.u.gen.oid[1] = 0;
    tmem_op.u.gen.oid[2] = 0;
    tmem_op.u.gen.index = page;
    tmem_op.u.gen.tmem_offset = 0;
    tmem_op.u.gen.pfn_offset = 0;
    tmem_op.u.gen.len = 0;
    set_xen_guest_handle(tmem_op.u.gen.gmfn, (void *)MmGetMdlPfnArray(data->Iopb->Parameters.Write.MdlAddress)[i]);
    rc = XnTmemOp(&tmem_op);
    if (rc == 1) {
      context->put_success_count++;
    } else if (rc == 0) {
      context->put_fail_count++;
    } else {
      FUNCTION_MSG("TMEM_PUT_PAGE = %d\n", rc);
      context->put_fail_count++;
      context->error_count++;
    }
  }
  KeReleaseSpinLock(&global_context.lock, old_irql);
  if (((context->put_success_count + context->put_fail_count + context->get_success_count + context->get_fail_count) & 0xff) == 0) {
    FUNCTION_MSG("   put_success_count = %I64d\n", context->put_success_count);
    FUNCTION_MSG("   put_fail_count    = %I64d\n", context->put_fail_count);
    FUNCTION_MSG("   get_success_count = %I64d\n", context->get_success_count);
    FUNCTION_MSG("   get_fail_count    = %I64d\n", context->get_fail_count);
    FUNCTION_MSG("   error_count    = %I64d\n", context->error_count);
  }
  return FLT_PREOP_SUCCESS_NO_CALLBACK;
}

FLT_PREOP_CALLBACK_STATUS
XenCache_Pre_READ(PFLT_CALLBACK_DATA data, PCFLT_RELATED_OBJECTS flt_objects, PVOID *completion_context) {
  NTSTATUS status;
  pagefile_context_t *context;
  KIRQL old_irql;
  int i;
  LONG rc;
  struct tmem_op tmem_op;
  
  UNREFERENCED_PARAMETER(data);
  UNREFERENCED_PARAMETER(flt_objects);
  UNREFERENCED_PARAMETER(completion_context);

  if (!FsRtlIsPagingFile(flt_objects->FileObject)) {
    return FLT_PREOP_SUCCESS_NO_CALLBACK;
  }
  KeAcquireSpinLock(&global_context.lock, &old_irql);
  for (context = global_context.pagefile_head; context; context = context->next) {
    if (context->file_object == flt_objects->FileObject)
      break;
  }
  if (!context) {
    /* no need to create context if op is a READ - either something is wrong or we were just loaded */
    //FUNCTION_MSG("Failed to find context\n");
    KeReleaseSpinLock(&global_context.lock, old_irql);
    return FLT_PREOP_SUCCESS_NO_CALLBACK;
  }    
  if (!(data->Flags & FLTFL_CALLBACK_DATA_IRP_OPERATION)) {
    KeReleaseSpinLock(&global_context.lock, old_irql);
    return FLT_PREOP_SUCCESS_NO_CALLBACK;
  }

  status = FLT_PREOP_COMPLETE;
  for (i = 0; i < (int)data->Iopb->Parameters.Read.Length / 4096; i++) {
    ULONG page = (ULONG)(data->Iopb->Parameters.Read.ByteOffset.QuadPart >> PAGE_SHIFT) + i;
    
    tmem_op.cmd = TMEM_GET_PAGE;
    tmem_op.pool_id = context->pool_id;
    tmem_op.u.gen.oid[0] = 0;
    tmem_op.u.gen.oid[1] = 0;
    tmem_op.u.gen.oid[2] = 0;
    tmem_op.u.gen.index = page;
    tmem_op.u.gen.tmem_offset = 0;
    tmem_op.u.gen.pfn_offset = 0;
    tmem_op.u.gen.len = 0;
    set_xen_guest_handle(tmem_op.u.gen.gmfn, (void *)MmGetMdlPfnArray(data->Iopb->Parameters.Read.MdlAddress)[i]);
    rc = XnTmemOp(&tmem_op);
    if (rc == 1) {
      context->get_success_count++;
    } else if (rc == 0) {
      status = FLT_PREOP_SUCCESS_NO_CALLBACK;
      context->get_fail_count++;
    } else {
      FUNCTION_MSG("TMEM_GET_PAGE = %d\n", rc);
      status = FLT_PREOP_SUCCESS_NO_CALLBACK;
      context->get_fail_count++;
      context->error_count++;
    }
  }
  
  if (((context->put_success_count + context->put_fail_count + context->get_success_count + context->get_fail_count) & 0xff) == 0) {
    FUNCTION_MSG("   put_success_count = %I64d\n", context->put_success_count);
    FUNCTION_MSG("   put_fail_count    = %I64d\n", context->put_fail_count);
    FUNCTION_MSG("   get_success_count = %I64d\n", context->get_success_count);
    FUNCTION_MSG("   get_fail_count    = %I64d\n", context->get_fail_count);
    FUNCTION_MSG("   error_count    = %I64d\n", context->error_count);
  }
  KeReleaseSpinLock(&global_context.lock, old_irql);

  if (status == FLT_PREOP_COMPLETE) {
    data->IoStatus.Status = STATUS_SUCCESS;
    data->IoStatus.Information = data->Iopb->Parameters.Read.Length;
  }
  return status;
}
