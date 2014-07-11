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

#pragma warning(disable: 4127)

#pragma warning(disable : 4200) // zero-sized array

#if !defined(_XENCACHE_H_)
#define _XENCACHE_H_

#define __DRIVER_NAME "XenCache"

#define XENCACHE_POOL_TAG (ULONG)'XenC'

#include <fltkernel.h>
#define NTSTRSAFE_LIB
#include <ntstrsafe.h>
#include <xen_windows.h>

typedef struct _pagefile_context_t pagefile_context_t;
typedef struct _global_context_t global_context_t;

struct _global_context_t {
  KSPIN_LOCK lock;
  pagefile_context_t *pagefile_head;
  ULONGLONG error_count;
};
  
struct _pagefile_context_t {
  pagefile_context_t *next;
  global_context_t *global;
  PFILE_OBJECT file_object;
  LONG pool_id;

  ULONGLONG put_success_count;
  ULONGLONG put_fail_count;
  ULONGLONG get_success_count;
  ULONGLONG get_fail_count;
  ULONGLONG error_count;
};

#endif
