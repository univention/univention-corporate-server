/* 
 * libdefs.h
 * Copyright (C) 2002, AVM GmbH. All rights reserved.
 * 
 * This Software is  free software. You can redistribute and/or
 * modify such free software under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 * 
 * The free software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public
 * License along with this Software; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA, or see
 * http://www.opensource.org/licenses/lgpl-license.html
 * 
 * Contact: AVM GmbH, Alt-Moabit 95, 10559 Berlin, Germany, email: info@avm.de
 */

#ifndef __have_libdefs_h__
#define __have_libdefs_h__

#include <linux/time.h>
#include <stdarg.h>
#include "defs.h"
#include "attr.h"

#if defined (DRIVER_TYPE_DSL_RAP)
#include "common.h"
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
typedef enum {

	timer_end	= 0,
	timer_restart	= 1,
	timer_renew	= 2
} restart_t;

#if defined (__fcpcmcia__)
typedef __attr2 restart_t (* timerfunc_t) (unsigned long);	/* FIXME */
#else
typedef restart_t (__attr2 * timerfunc_t) (unsigned long);
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
typedef struct __data {

	unsigned	num;
	char *		buffer;
} appldata_t;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
typedef struct __lib {

	void (__attr * init) (unsigned, void (__attr2 *) (void *, unsigned),
					void (__attr2 *) (void *), 
					void (__attr2 *) (void)); 
	
	char * (__attr * params) (void);
	
	int (__attr * get_message) (unsigned char *);
	void (__attr * put_message) (unsigned char *);
	
	unsigned char * (__attr * get_data_block) (unsigned, 
						unsigned long, unsigned);
	void (__attr * free_data_block) (unsigned, unsigned char *);
	
	int (__attr * new_ncci) (unsigned, unsigned long, unsigned, unsigned);
	void (__attr * free_ncci) (unsigned, unsigned long);
	
	unsigned (__attr * block_size) (unsigned);
	unsigned (__attr * window_size) (unsigned);
	unsigned (__attr * card) (void);
	
	void * (__attr * appl_data) (unsigned);
#if defined (DRIVER_TYPE_DSL_RAP)
	unsigned (__attr * appl_attr) (unsigned);
#endif
	appldata_t * (__attr * appl_1st_data) (appldata_t *);
	appldata_t * (__attr * appl_next_data) (appldata_t *);
	
	void * (__attr * malloc) (unsigned);
	void (__attr * free) (void *);
#if defined (DRIVER_TYPE_DSL) && !defined (DRIVER_TYPE_DSL_USB)
	void * (__attr * malloc2) (unsigned);
#endif

#if defined (DRIVER_TYPE_DSL_RAP)
	void (__attr * delay) (unsigned);
#endif
	unsigned long (__attr * msec) (void);
	unsigned long long (__attr * msec64) (void);
	
	int (__attr * timer_new) (unsigned);
	void (__attr * timer_delete) (void);
	int (__attr * timer_start) (unsigned, unsigned long, 
					unsigned long, timerfunc_t);
	int (__attr * timer_stop) (unsigned);
	void (__attr * timer_poll) (void);
#if defined (DRIVER_TYPE_DSL)
	int (__attr * get_time) (struct timeval *);
#endif

#if defined (DRIVER_TYPE_DSL_TM) || defined (DRIVER_TYPE_DSL_USB)
	void (__attr * dprintf) (char *, ...);
#endif
#if defined (DRIVER_TYPE_DSL_RAP)
	void (__attr * printf) (char *, va_list);
	void (__attr * putf) (char *, va_list);
#else
	void (__attr * printf) (char *, va_list);
#endif
	void (__attr * puts) (char *);
	void (__attr * putl) (long);
	void (__attr * puti) (int);
	void (__attr * putc) (char);
	void (__attr * putnl) (void);
	
	void (__attr * _enter_critical) (const char *, int);
	void (__attr * _leave_critical) (const char *, int);
	void (__attr * enter_critical) (void);
	void (__attr * leave_critical) (void);
	void (__attr * enter_cache_sensitive_code) (void);
	void (__attr * leave_cache_sensitive_code) (void);

#if defined (DRIVER_TYPE_DSL_RAP)
	void (__attr * xfer_req) (dif_require_p, unsigned);
#endif

	char *		name;
	unsigned	udata;
	void *		pdata;
} lib_interface_t, * lib_interface_p;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
typedef struct __f {
	
	unsigned	nfuncs;
	void	     (__attr * sched_ctrl) (unsigned);
	void         (__attr * wakeup_ctrl) (unsigned);
	void         (__attr * version_ind) (char *);
	unsigned     (__attr * sched_suspend) (unsigned long);
	unsigned     (__attr * sched_resume) (void);
	unsigned     (__attr * ctrl_remove) (void);
	unsigned     (__attr * ctrl_add) (void);
} functions_t, * functions_p;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
typedef struct __cb {

	unsigned (__attr2 * cm_start) (void);
	char * (__attr2 * cm_init) (unsigned, unsigned);
	int (__attr2 * cm_activate) (void);
	int (__attr2 * cm_exit) (void);
	unsigned (__attr2 * cm_handle_events) (void);
	int (__attr2 * cm_schedule) (void);
	void (__attr2 * cm_timer_irq_control) (unsigned);
	void (__attr2 * cm_register_ca_functions) (functions_p);
#if !defined (DRIVER_TYPE_DSL_RAP)
	unsigned (__attr2 * check_controller) (unsigned, unsigned *);
#endif

#if defined (DRIVER_TYPE_INTERN)
	void * (__attr2 * lib_heap_init) (void *, unsigned);
	void (__attr2 * lib_heap_exit) (void *);
	void * (__attr2 * lib_heap_alloc) (void *, unsigned);
	void (__attr2 * lib_heap_free) (void *, void *);
#endif
	
#if defined (DRIVER_TYPE_DSL_TM)
	int (__attr2 * cc_debugging_needed) (void);
	unsigned (__attr2 * cc_num_link_buffer) (int);
	unsigned (__attr2 * cc_link_version) (void);
	void (__attr2 * cc_compress_code) (void);
	int (__attr2 * cc_status) (unsigned, void *, void *);
	int (__attr2 * cc_run) (void);
#endif
	
#if defined (DRIVER_TYPE_DSL_RAP)
	int (__attr2 * cc_debugging_needed) (void);
#if !defined (DRIVER_TYPE_USB)
	void (__attr2 * cc_init_debug) (void *, unsigned);
	void (__attr2 * cc_init_dma) (dma_list_t, unsigned, 
						dma_list_t, unsigned);
#endif
	unsigned (__attr2 * cc_num_link_buffer) (int);
	unsigned (__attr2 * cc_link_version) (void);
#if !defined (DRIVER_TYPE_USB)
	unsigned (__attr2 * cc_timer_offset) (void);
	unsigned (__attr2 * cc_pc_ack_offset) (void);
	unsigned (__attr2 * cc_buffer_params) (unsigned *, ioaddr_p *, 
						unsigned *, unsigned *);
#endif
	void (__attr2 * cc_compress_code) (void);
	int (__attr2 * cc_status) (unsigned, void *, void *);
	int (__attr2 * cc_run) (void);
#endif

} lib_callback_t, * lib_callback_p;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#endif

