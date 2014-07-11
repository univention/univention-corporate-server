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

static NTSTATUS
XenVbd_Connect(PXENVBD_DEVICE_DATA xvdd, BOOLEAN suspend) {
  BOOLEAN qemu_hide_filter = FALSE;
  ULONG qemu_hide_flags_value = 0;
  PCHAR device_type;
  //BOOLEAN active = FALSE;
  NTSTATUS status;
  PCHAR mode;
  PCHAR uuid;
  PFN_NUMBER pfn;

  FUNCTION_ENTER();
  
  if (xvdd->device_state != DEVICE_STATE_DISCONNECTED) {
    FUNCTION_MSG("state not DEVICE_STATE_DISCONNECTED, is %d instead\n", xvdd->device_state);
    FUNCTION_EXIT();
    return STATUS_SUCCESS;
  }
  if (!suspend) {
    xvdd->backend_state = XenbusStateUnknown;
    if ((xvdd->handle = XnOpenDevice(xvdd->pdo, XenVbd_DeviceCallback, xvdd)) == NULL) {
      FUNCTION_MSG("Failed to open\n");
      return STATUS_UNSUCCESSFUL;
    }
  }
  xvdd->sring = (blkif_sring_t *)ExAllocatePoolWithTag(NonPagedPool, PAGE_SIZE, XENVBD_POOL_TAG);
  if (!xvdd->sring) {
    FUNCTION_MSG("Failed to allocate sring\n");
    return STATUS_UNSUCCESSFUL;
  }
  pfn = (PFN_NUMBER)(MmGetPhysicalAddress(xvdd->sring).QuadPart >> PAGE_SHIFT);
  xvdd->sring_gref = XnGrantAccess(xvdd->handle, (ULONG)pfn, FALSE, INVALID_GRANT_REF, xvdd->grant_tag);
  SHARED_RING_INIT(xvdd->sring);
  FRONT_RING_INIT(&xvdd->ring, xvdd->sring, PAGE_SIZE);

  while (xvdd->backend_state != XenbusStateInitialising &&
    xvdd->backend_state != XenbusStateInitWait &&
    xvdd->backend_state != XenbusStateInitialised &&
    xvdd->backend_state != XenbusStateConnected) {
    FUNCTION_MSG("waiting for XenbusStateInitXxx/XenbusStateConnected, backend_state = %d\n", xvdd->backend_state);
    KeWaitForSingleObject(&xvdd->backend_event, Executive, KernelMode, FALSE, NULL);
  }
  XnGetValue(xvdd->handle, XN_VALUE_TYPE_QEMU_HIDE_FLAGS, &qemu_hide_flags_value);
  XnGetValue(xvdd->handle, XN_VALUE_TYPE_QEMU_FILTER, &qemu_hide_filter);
  status = XnReadString(xvdd->handle, XN_BASE_FRONTEND, "device-type", &device_type);
  if (strcmp(device_type, "disk") == 0) {
    FUNCTION_MSG("device-type = Disk\n");    
    xvdd->device_type = XENVBD_DEVICETYPE_DISK;
  } else if (strcmp(device_type, "cdrom") == 0) {
    FUNCTION_MSG("device-type = CDROM\n");    
    xvdd->device_type = XENVBD_DEVICETYPE_CDROM;
  } else {
    FUNCTION_MSG("device-type = %s (This probably won't work!)\n", device_type);
    xvdd->device_type = XENVBD_DEVICETYPE_UNKNOWN;
  }
  XnFreeMem(xvdd->handle, device_type);
  if (!(((qemu_hide_flags_value & QEMU_UNPLUG_ALL_IDE_DISKS) && xvdd->device_type != XENVBD_DEVICETYPE_CDROM) || qemu_hide_filter)) {
    /* we never set backend state active if we are inactive */
    FUNCTION_MSG("Inactive\n");
    XnCloseDevice(xvdd->handle);
    xvdd->device_state = DEVICE_STATE_INACTIVE;
    return STATUS_SUCCESS;
  }
  status = XnBindEvent(xvdd->handle, &xvdd->event_channel, XenVbd_HandleEventDIRQL, xvdd);
  status = XnWriteInt32(xvdd->handle, XN_BASE_FRONTEND, "event-channel", xvdd->event_channel);
  status = XnWriteInt32(xvdd->handle, XN_BASE_FRONTEND, "ring-ref", xvdd->sring_gref);
  status = XnWriteString(xvdd->handle, XN_BASE_FRONTEND, "protocol", ABI_PROTOCOL);
  status = XnWriteInt32(xvdd->handle, XN_BASE_FRONTEND, "state", XenbusStateInitialised);

  while (xvdd->backend_state != XenbusStateConnected) {
    FUNCTION_MSG("waiting for XenbusStateConnected, backend_state = %d\n", xvdd->backend_state);
    KeWaitForSingleObject(&xvdd->backend_event, Executive, KernelMode, FALSE, NULL);
  }

  // TODO: some of this stuff should be read on first connect only, then only verified on resume
  xvdd->new_total_sectors = (ULONGLONG)-1L;
  status = XnReadInt64(xvdd->handle, XN_BASE_BACKEND, "sectors", &xvdd->total_sectors);
  status = XnReadInt32(xvdd->handle, XN_BASE_BACKEND, "sector-size", &xvdd->hw_bytes_per_sector);
  if (xvdd->device_type == XENVBD_DEVICETYPE_CDROM) {
    /* CD/DVD drives must have bytes_per_sector = 2048. */
    xvdd->bytes_per_sector = 2048;
    xvdd->hw_bytes_per_sector = 2048;
  } else {
    xvdd->bytes_per_sector = 512;
  }
  /* for some reason total_sectors is measured in 512 byte sectors always, so correct this to be in bytes_per_sectors */
  xvdd->total_sectors /= xvdd->bytes_per_sector / 512;
  status = XnReadInt32(xvdd->handle, XN_BASE_BACKEND, "feature-barrier", &xvdd->feature_barrier);
  status = XnReadInt32(xvdd->handle, XN_BASE_BACKEND, "feature-discard", &xvdd->feature_discard);
  status = XnReadInt32(xvdd->handle, XN_BASE_BACKEND, "feature-flush-cache", &xvdd->feature_flush_cache);
  status = XnReadString(xvdd->handle, XN_BASE_BACKEND, "mode", &mode);
  if (strncmp(mode, "r", 1) == 0) {
    FUNCTION_MSG("mode = r\n");
    xvdd->device_mode = XENVBD_DEVICEMODE_READ;
  } else if (strncmp(mode, "w", 1) == 0) {
    FUNCTION_MSG("mode = w\n");    
    xvdd->device_mode = XENVBD_DEVICEMODE_WRITE;
  } else {
    FUNCTION_MSG("mode = unknown\n");
    xvdd->device_mode = XENVBD_DEVICEMODE_UNKNOWN;
  }
  XnFreeMem(xvdd->handle, mode);

  // read device-type
  status = XnReadString(xvdd->handle, XN_BASE_FRONTEND, "device-type", &device_type);
  if (strcmp(device_type, "disk") == 0) {
    FUNCTION_MSG("device-type = Disk\n");    
    xvdd->device_type = XENVBD_DEVICETYPE_DISK;
  } else if (strcmp(device_type, "cdrom") == 0) {
    FUNCTION_MSG("device-type = CDROM\n");    
    xvdd->device_type = XENVBD_DEVICETYPE_CDROM;
  } else {
    FUNCTION_MSG("device-type = %s (This probably won't work!)\n", device_type);
    xvdd->device_type = XENVBD_DEVICETYPE_UNKNOWN;
  }

  status = XnReadString(xvdd->handle, XN_BASE_FRONTEND, "device-type", &uuid);
  if (status == STATUS_SUCCESS) {
    RtlStringCbCopyA(xvdd->serial_number, ARRAY_SIZE(xvdd->serial_number), uuid);
    XnFreeMem(xvdd->handle, uuid);
  } else {
    RtlStringCbCopyA(xvdd->serial_number, ARRAY_SIZE(xvdd->serial_number), "        ");
  }  

  XnFreeMem(xvdd->handle, device_type);
  status = XnWriteInt32(xvdd->handle, XN_BASE_FRONTEND, "state", XenbusStateConnected);

  if (xvdd->device_type == XENVBD_DEVICETYPE_UNKNOWN
      || xvdd->sring == NULL
      || xvdd->event_channel == 0
      || xvdd->total_sectors == 0
      || xvdd->hw_bytes_per_sector == 0) {
    FUNCTION_MSG("Missing settings\n");
    // TODO: fail how?
  }

  xvdd->device_state = DEVICE_STATE_ACTIVE;
  XenVbd_StartRing(xvdd, suspend);
  FUNCTION_EXIT();
  return STATUS_SUCCESS;
}

static NTSTATUS
XenVbd_Disconnect(PVOID DeviceExtension, BOOLEAN suspend) {
  NTSTATUS status;
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)DeviceExtension;

  if (xvdd->device_state == DEVICE_STATE_INACTIVE) {
    /* state stays INACTIVE */
    return STATUS_SUCCESS;
  } 

  if (xvdd->device_state != DEVICE_STATE_ACTIVE) {
    FUNCTION_MSG("state not DEVICE_STATE_ACTIVE, is %d instead\n", xvdd->device_state);
    FUNCTION_EXIT();
    return STATUS_SUCCESS;
  }

  /* StopRing must set XenbusStateClosing when ring is paused */
  XenVbd_StopRing(xvdd, suspend);
  
  while (xvdd->backend_state != XenbusStateClosing) {
    FUNCTION_MSG("waiting for XenbusStateClosing, backend_state = %d\n", xvdd->backend_state);
    KeWaitForSingleObject(&xvdd->backend_event, Executive, KernelMode, FALSE, NULL);
  }
  status = XnWriteInt32(xvdd->handle, XN_BASE_FRONTEND, "state", XenbusStateClosed);
  while (xvdd->backend_state != XenbusStateClosed) {
    FUNCTION_MSG("waiting for XenbusStateClosed, backend_state = %d\n", xvdd->backend_state);
    KeWaitForSingleObject(&xvdd->backend_event, Executive, KernelMode, FALSE, NULL);
  }
  XnUnbindEvent(xvdd->handle, xvdd->event_channel);
  XnEndAccess(xvdd->handle, xvdd->sring_gref, FALSE, xvdd->grant_tag);
  ExFreePoolWithTag(xvdd->sring, XENVBD_POOL_TAG);

  if (!suspend) {
    XnCloseDevice(xvdd->handle);
  }
  xvdd->device_state = DEVICE_STATE_DISCONNECTED;
  return STATUS_SUCCESS;
}


static VOID
XenVbd_DeviceCallback(PVOID context, ULONG callback_type, PVOID value) {
  PXENVBD_DEVICE_DATA xvdd = (PXENVBD_DEVICE_DATA)context;
  ULONG state;
 
  FUNCTION_ENTER();

  switch (callback_type) {
  case XN_DEVICE_CALLBACK_BACKEND_STATE:
    state = (ULONG)(ULONG_PTR)value;
    if (state == xvdd->backend_state) {
      FUNCTION_MSG("same state %d\n", state);
      /* could be rewriting same state because of size change */
      if (xvdd->backend_state == XenbusStateConnected) {
        /* just set the new value - it will be noticed sooner or later */
        XnReadInt64(xvdd->handle, XN_BASE_BACKEND, "sectors", &xvdd->new_total_sectors);
      }
      FUNCTION_EXIT();
    }
    FUNCTION_MSG("XenBusState = %d -> %d\n", xvdd->backend_state, state);
    xvdd->backend_state = state;
    KeMemoryBarrier();
    KeSetEvent(&xvdd->backend_event, 0, FALSE);
    break;
  case XN_DEVICE_CALLBACK_SUSPEND:
    FUNCTION_MSG("XN_DEVICE_CALLBACK_SUSPEND\n");
    XenVbd_Disconnect(xvdd, TRUE);
    break;
  case XN_DEVICE_CALLBACK_RESUME:
    FUNCTION_MSG("XN_DEVICE_CALLBACK_RESUME\n");
    XenVbd_Connect(xvdd, TRUE);
    break;
  }
  FUNCTION_EXIT();
}
