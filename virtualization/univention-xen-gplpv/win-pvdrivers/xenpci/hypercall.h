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

#if defined(_X86_)
  #if defined(__MINGW32__)
    #include "hypercall_x86_mingw.h"
  #else
    #include "hypercall_x86.h"
  #endif
#elif defined(_AMD64_)
  #include "hypercall_amd64.h"
#elif defined(__ia64__)
  #include "hypercall_ia64.h"
#endif

static __inline ULONGLONG
_hvm_get_parameter(PVOID hypercall_stubs, int hvm_param)
{
  struct xen_hvm_param a;
  int retval;

  FUNCTION_ENTER();
  a.domid = DOMID_SELF;
  a.index = hvm_param;
  retval = _HYPERVISOR_hvm_op(hypercall_stubs, HVMOP_get_param, &a);
  KdPrint((__DRIVER_NAME " HYPERVISOR_hvm_op retval = %d\n", retval));
  FUNCTION_EXIT();
  return a.value;
}

static __inline ULONGLONG
_hvm_set_parameter(PVOID hypercall_stubs, int hvm_param, ULONGLONG value)
{
  struct xen_hvm_param a;
  int retval;

  FUNCTION_ENTER();
  a.domid = DOMID_SELF;
  a.index = hvm_param;
  a.value = value;
  retval = _HYPERVISOR_hvm_op(hypercall_stubs, HVMOP_set_param, &a);
  KdPrint((__DRIVER_NAME " HYPERVISOR_hvm_op retval = %d\n", retval));
  FUNCTION_EXIT();
  return retval;
}

static __inline int
_hvm_shutdown(PVOID hypercall_stubs, unsigned int reason)
{
  struct sched_shutdown ss;
  int retval;

  FUNCTION_ENTER();
  ss.reason = reason;
  retval = _HYPERVISOR_sched_op(hypercall_stubs, SCHEDOP_shutdown, &ss);
  FUNCTION_EXIT();
  return retval;
}

static __inline VOID
_HYPERVISOR_yield(PVOID hypercall_stubs)
{
  _HYPERVISOR_sched_op(hypercall_stubs, SCHEDOP_yield, NULL);
}
