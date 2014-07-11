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

#define SCSIOP_UNMAP 0x42
#define VPD_BLOCK_LIMITS 0xB0

#define XENVBD_POOL_TAG (ULONG) 'XVBD'

#define DEVICE_STATE_DISCONNECTED  0 /* -> INITIALISING */
#define DEVICE_STATE_INITIALISING  1 /* -> INACTIVE | ACTIVE */
#define DEVICE_STATE_INACTIVE      2
#define DEVICE_STATE_ACTIVE        3 /* -> DISCONNECTING */
#define DEVICE_STATE_DISCONNECTING 4 /* -> DISCONNECTED */

#define SCSI_DEVICE_MANUFACTURER "XEN     "
#define SCSI_DISK_MODEL          "PV DISK          "
#define SCSI_CDROM_MODEL         "PV CDROM         "

typedef enum {
  XENVBD_DEVICETYPE_UNKNOWN,
  XENVBD_DEVICETYPE_DISK,
  XENVBD_DEVICETYPE_CDROM,
  XENVBD_DEVICETYPE_CONTROLLER // Not yet used
} XENVBD_DEVICETYPE;

typedef enum {
  XENVBD_DEVICEMODE_UNKNOWN,
  XENVBD_DEVICEMODE_READ,
  XENVBD_DEVICEMODE_WRITE
} XENVBD_DEVICEMODE;

typedef struct {
  LIST_ENTRY list_entry;
  PSCSI_REQUEST_BLOCK srb;
  ULONG length; /* cached srb length */
  ULONG offset; /* current srb offset */
  ULONG outstanding_requests; /* number of requests sent to xen for this srb */
  BOOLEAN error; /* true if any sub requests have returned an error */
} srb_list_entry_t;

typedef struct {
  blkif_request_t req;
  srb_list_entry_t *srb_list_entry;
  PSCSI_REQUEST_BLOCK srb;
  PVOID system_address;
  ULONG length;
  BOOLEAN aligned_buffer_in_use;
  BOOLEAN reset;
  #if DBG && NTDDI_VERSION >= NTDDI_WINXP
  LARGE_INTEGER ring_submit_time;
  #endif
} blkif_shadow_t;
