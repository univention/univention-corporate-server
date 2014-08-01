/* Code/license from Xen's include/asm/hypercall.h: */
/*
 * Copyright (c) 2002-2004, K A Fraser
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License version 2
 * as published by the Free Software Foundation; or, when distributed
 * separately from the Linux kernel or incorporated into other
 * software packages, subject to the following license:
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this source file (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy, modify,
 * merge, publish, distribute, sublicense, and/or sell copies of the Software,
 * and to permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 */
/* Also Copyright (C) 2008 Andy Grover */

#define __STR(x) #x
#define STR(x) __STR(x)

#define _hypercall2(type, name, a1, a2)                         \
({                                                              \
  long __res, __ign1, __ign2;                                   \
  asm volatile (                                                \
	  "mov %3,%%eax; "                                            \
	  "add $("STR(__HYPERVISOR_##name)" * 32),%%eax; "            \
  	"call *%%eax"                                               \
    : "=a" (__res), "=b" (__ign1), "=c" (__ign2)                \
    : "1" ((long)(a1)), "2" ((long)(a2)), "r" (xpdd->hypercall_stubs) \
    : "memory" );                                               \
  (type)__res;                                                  \
})

#define _hypercall3(type, name, a1, a2, a3)			                \
({								                                              \
	long __res, __ign1, __ign2, __ign3;			                      \
	asm volatile (						                                    \
	  "mov %4,%%eax; "                                            \
	  "add $("STR(__HYPERVISOR_##name)" * 32),%%eax; "            \
  	"call *%%eax"                                               \
		: "=a" (__res), "=b" (__ign1), "=c" (__ign2), 	            \
		"=d" (__ign3)					                                      \
		: "1" ((long)(a1)), "2" ((long)(a2)),		                    \
		"3" ((long)(a3)), "r" (xpdd->hypercall_stubs)		            \
		: "memory" );					                                      \
	(type)__res;						                                      \
})


static __inline void __cpuid(uint32_t output[4], uint32_t op)
{
  __asm__("cpuid"
          : "=a" (output[0]),
            "=b" (output[1]),
            "=c" (output[2]),
            "=d" (output[3])
          : "0" (op));
}

static __inline void __writemsr(uint32_t msr, uint64_t value)
{
  uint32_t hi, lo;
  hi = value >> 32;
  lo = value & 0xFFFFFFFF;

  __asm__ __volatile__("wrmsr"
                       : /* no outputs */
                       : "c" (msr), "a" (lo), "d" (hi));
}

static __inline int
HYPERVISOR_memory_op(PXENPCI_DEVICE_DATA xpdd, int cmd, void *arg)
{
  return _hypercall2(int, memory_op, cmd, arg);
}

static __inline int
HYPERVISOR_sched_op(PXENPCI_DEVICE_DATA xpdd, int cmd, void *arg)
{
  return _hypercall2(int, sched_op, cmd, arg);
}

static __inline int
HYPERVISOR_hvm_op(PXENPCI_DEVICE_DATA xpdd, int op, struct xen_hvm_param *arg)
{
  return _hypercall2(unsigned long, hvm_op, op, arg);
}

static __inline int
HYPERVISOR_event_channel_op(PXENPCI_DEVICE_DATA xpdd, int cmd, void *arg)
{
	return _hypercall2(int, event_channel_op, cmd, arg);
}
static inline int
HYPERVISOR_grant_table_op(
  PXENPCI_DEVICE_DATA xpdd,
  unsigned int cmd,
  void *uop,
  unsigned int count)
{
	return _hypercall3(int, grant_table_op, cmd, uop, count);
}

