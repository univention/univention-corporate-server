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

#define XENVBD_CONTROL_SIG         "XENGPLPV"
#define XENVBD_CONTROL_START       0
#define XENVBD_CONTROL_STOP        1
#define XENVBD_CONTROL_EVENT       2


#define MAX_SHADOW_ENTRIES  64
#define SHADOW_ENTRIES min(MAX_SHADOW_ENTRIES, BLK_RING_SIZE)

struct {
  /* filter data */
  PVOID xvfd;
  PDEVICE_OBJECT pdo;
  ULONG backend_state;
  KEVENT backend_event;

  /* shared data */
  ULONG device_state;
  XN_HANDLE handle;
  evtchn_port_t event_channel;
  blkif_front_ring_t ring;
  blkif_sring_t *sring;
  grant_ref_t sring_gref; 
  UCHAR last_sense_key;
  UCHAR last_additional_sense_code;
  UCHAR last_additional_sense_code_qualifier;
  BOOLEAN cac;
  XENVBD_DEVICETYPE device_type;
  XENVBD_DEVICEMODE device_mode;
  ULONG bytes_per_sector; /* 512 for disk, 2048 for CDROM) */
  ULONG hw_bytes_per_sector; /* underlying hardware format, eg 4K */
  ULONGLONG total_sectors;
  ULONGLONG new_total_sectors;
  ULONG feature_flush_cache;
  ULONG feature_discard;
  ULONG feature_barrier;
  CHAR serial_number[64];

  /* miniport data */
  PVOID xvsd;
  blkif_shadow_t shadows[MAX_SHADOW_ENTRIES];
  USHORT shadow_free_list[MAX_SHADOW_ENTRIES];
  USHORT shadow_free;
  //USHORT shadow_min_free;
  ULONG grant_tag;
  LIST_ENTRY srb_list;
  BOOLEAN aligned_buffer_in_use;
  ULONG aligned_buffer_size;
  PVOID aligned_buffer;
} typedef XENVBD_DEVICE_DATA, *PXENVBD_DEVICE_DATA;
