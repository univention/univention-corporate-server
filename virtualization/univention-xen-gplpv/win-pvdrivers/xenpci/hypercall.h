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

#include "xenpci.h"

#if defined(_X86_)
  #include "hypercall_x86.h"
#elif defined(_AMD64_)
  #include "hypercall_amd64.h"
#endif

static __inline ULONGLONG
hvm_get_parameter(int hvm_param)
{
  struct xen_hvm_param a;
  int retval;

  a.domid = DOMID_SELF;
  a.index = hvm_param;
  retval = HYPERVISOR_hvm_op(HVMOP_get_param, &a);
  return a.value;
}

static __inline ULONGLONG
hvm_set_parameter(int hvm_param, ULONGLONG value)
{
  struct xen_hvm_param a;
  int retval;

  a.domid = DOMID_SELF;
  a.index = hvm_param;
  a.value = value;
  retval = HYPERVISOR_hvm_op(HVMOP_set_param, &a);
  return retval;
}

static __inline int
hvm_shutdown(unsigned int reason)
{
  struct sched_shutdown ss;
  int retval;

  FUNCTION_ENTER();
  ss.reason = reason;
  retval = HYPERVISOR_sched_op(SCHEDOP_shutdown, &ss);
  FUNCTION_EXIT();
  return retval;
}

static __inline VOID
HYPERVISOR_yield() {
  HYPERVISOR_sched_op(SCHEDOP_yield, NULL);
}
