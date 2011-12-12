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

extern int _hypercall2(VOID *address, xen_ulong_t a1, xen_ulong_t a2);
extern int _hypercall3(VOID *address, xen_ulong_t a1, xen_ulong_t a2, xen_ulong_t a3);

static __inline int
_HYPERVISOR_memory_op(PVOID hypercall_stubs, int cmd, void *arg)
{
  PCHAR memory_op_func = hypercall_stubs;
  memory_op_func += __HYPERVISOR_memory_op * 32;
  return _hypercall2(memory_op_func, (xen_ulong_t)cmd, (xen_ulong_t)arg);
}

static __inline int
_HYPERVISOR_xen_version(PVOID hypercall_stubs, int cmd, void *arg)
{
  PCHAR xen_version_func = hypercall_stubs;
  xen_version_func += __HYPERVISOR_xen_version * 32;
  return _hypercall2(xen_version_func, (xen_ulong_t)cmd, (xen_ulong_t)arg);
}

static __inline int
_HYPERVISOR_grant_table_op(PVOID hypercall_stubs, int cmd, void *uop, unsigned int count)
{
  PCHAR grant_table_op_func = hypercall_stubs;
  grant_table_op_func += __HYPERVISOR_grant_table_op * 32;
  return _hypercall3(grant_table_op_func, (xen_ulong_t)cmd, (xen_ulong_t)uop, (xen_ulong_t)count);
}

static __inline int
_HYPERVISOR_hvm_op(PVOID hypercall_stubs, int op, struct xen_hvm_param *arg)
{
  PCHAR hvm_op_func = hypercall_stubs;
  hvm_op_func += __HYPERVISOR_hvm_op * 32;
  return _hypercall2(hvm_op_func, (xen_ulong_t)op, (xen_ulong_t)arg);
}

static __inline int
_HYPERVISOR_event_channel_op(PVOID hypercall_stubs, int cmd, void *op)
{
  PCHAR event_channel_op_func = hypercall_stubs;
  event_channel_op_func += __HYPERVISOR_event_channel_op * 32;
  return _hypercall2(event_channel_op_func, (xen_ulong_t)cmd, (xen_ulong_t)op);
}

static __inline int
_HYPERVISOR_sched_op(PVOID hypercall_stubs, int cmd, void *arg)
{
  PCHAR sched_op_func = hypercall_stubs;
  sched_op_func += __HYPERVISOR_sched_op * 32;
  return _hypercall2(sched_op_func, (xen_ulong_t)cmd, (xen_ulong_t)arg);
}

static __inline int
_HYPERVISOR_shutdown(PVOID hypercall_stubs, unsigned int reason)
{
  struct sched_shutdown ss;
  int retval;

  KdPrint((__DRIVER_NAME " --> " __FUNCTION__ "\n"));
  
  ss.reason = reason;
  retval = _HYPERVISOR_sched_op(hypercall_stubs, SCHEDOP_shutdown, &ss);
  
  KdPrint((__DRIVER_NAME " <-- " __FUNCTION__ "\n"));

  return retval;
}