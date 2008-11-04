/* 
 * tables.h
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

#ifndef __have_tables_h__
#define __have_tables_h__

#include <asm/types.h>
#include <linux/skbuff.h>
#include <linux/list.h>
#include <linux/capi.h>
#include "lock.h"
#include "queue.h"

typedef u16	capiinfo_t;

typedef struct __ncci {		/* tables.c only */

	NCCI_t			ncci;
	unsigned		appl;
	unsigned		win_size;
	unsigned		blk_size;
	unsigned char **	data;
	struct __ncci *		pred;
	struct __ncci *		succ;
} ncci_t;

typedef struct __appl {

	unsigned		id;
	unsigned		dying;
	void *			data;
	unsigned		attr;
	unsigned		blk_size;
	unsigned		blk_count;
	unsigned		ncci_count;
	unsigned		nncci;
	ncci_t *		root;
	struct __appl *		pred;
	struct __appl *		succ;
} appl_t;

typedef struct __appltab {

	appl_t *		appl_root;
	unsigned		appl_count;
	lock_t			lock;
	struct list_head	ncci_head;
} appltab_t;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern void table_init (appltab_t ** tab);
extern void table_exit (appltab_t ** tab);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern appl_t * first_appl (appltab_t *);
extern appl_t * next_appl (appltab_t *, appl_t *);

extern int appl_alive (appltab_t *, unsigned);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern capiinfo_t handle_data_conf (appltab_t *, queue_t *, unsigned char *);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern void remove_ncci (appltab_t *, appl_t *, ncci_t *);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern void * data_by_id (unsigned);
#if defined (DRIVER_TYPE_DSL_RAP)
extern unsigned attr_by_id (unsigned);
#endif
extern void * first_data (int *);
extern void * next_data (int *);
extern int appl_profile (unsigned, unsigned *, unsigned *);

extern void new_ncci (unsigned, __u32, unsigned, unsigned);
extern void free_ncci (unsigned, __u32);

extern unsigned char * data_block (unsigned, __u32, unsigned);

extern void release_appl (struct capi_ctr *, u16);
extern u16 send_msg (struct capi_ctr *, struct sk_buff *);
extern void register_appl (struct capi_ctr *, u16, capi_register_params *);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#endif
