#ifndef HYPERCALL_X86_H
#define HYPERCALL_X86_H
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

static __inline int
_HYPERVISOR_memory_op(PVOID hypercall_stubs, int cmd, void *arg)
{
  long __res;
  __asm {
    mov ebx, cmd
    mov ecx, arg
    mov eax, hypercall_stubs
    add eax, (__HYPERVISOR_memory_op * 32)
    call eax
    mov [__res], eax
  }
  return __res;
}

static __inline int
_HYPERVISOR_sched_op(PVOID hypercall_stubs, int cmd, void *arg)
{
  long __res;
  __asm {
    mov ebx, cmd
    mov ecx, arg
    mov eax, hypercall_stubs
    add eax, (__HYPERVISOR_sched_op * 32)
    call eax
    mov [__res], eax
  }
  return __res;
}

static __inline int
_HYPERVISOR_xen_version(PVOID hypercall_stubs, int cmd, void *arg)
{
  long __res;
  __asm {
    mov ebx, cmd
    mov ecx, arg
    mov eax, hypercall_stubs
    add eax, (__HYPERVISOR_xen_version * 32)
    call eax
    mov [__res], eax
  }
  return __res;
}

static __inline int
_HYPERVISOR_grant_table_op(PVOID hypercall_stubs, int cmd, void *uop, unsigned int count)
{
  long __res;
  __asm {
    mov ebx, cmd
    mov ecx, uop
    mov edx, count
    mov eax, hypercall_stubs
    add eax, (__HYPERVISOR_grant_table_op * 32)
    call eax
    mov [__res], eax
  }
  return __res;
}

static __inline int
_HYPERVISOR_hvm_op(PVOID hypercall_stubs, int op, struct xen_hvm_param *arg)
{
  long __res;
  __asm {
    mov ebx, op
    mov ecx, arg
    mov eax, hypercall_stubs
    add eax, (__HYPERVISOR_hvm_op * 32)
    call eax
    mov [__res], eax
  }
  return __res;
}

static __inline int
_HYPERVISOR_event_channel_op(PVOID hypercall_stubs, int cmd, void *op)
{
  long __res;
  __asm {
    mov ebx, cmd
    mov ecx, op
    mov eax, hypercall_stubs
    add eax, (__HYPERVISOR_event_channel_op * 32)
    call eax
    mov [__res], eax
  }
  return __res;
}

#endif
