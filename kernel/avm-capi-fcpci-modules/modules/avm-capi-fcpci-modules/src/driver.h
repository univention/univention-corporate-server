/* 
 * driver.h
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

#ifndef __have_driver_h__
#define __have_driver_h__

#include <linux/config.h>
#include <linux/skbuff.h>
#include <linux/capi.h>
#include <linux/list.h>
#include <linux/isdn/capilli.h>
#include "tables.h"
#include "queue.h"
#include "libdefs.h"

#if defined (CONFIG_ISAPNP)
# include <linux/isapnp.h>
#endif

typedef struct __card {

	unsigned						base;
	unsigned						irq;
	unsigned						info;
	unsigned						data;
	char *							version;
	char *							string[8];
	unsigned						count;
	appltab_t *						appls;
	queue_t *						queue;
	unsigned						length;
	int							running;
	void (__attr2 * reg_func) (void *, unsigned);
	void (__attr2 * rel_func) (void *);
	void (__attr2 * dwn_func) (void);
	struct capi_ctr						ctrl;
#if defined (__fcpci__)
	struct pci_dev *					dev;
#elif defined (__fcpnp__)
	struct pnp_dev *					dev;
#endif
} card_t;

extern card_t *			capi_card;
extern lib_callback_t *		capi_lib;
extern struct capi_ctr *	capi_controller;

#define	GET_CARD(ctrl)		(card_t *) (ctrl)->driverdata

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern void remove_ctrl (struct capi_ctr *); 
extern int add_card (struct capi_driver *, capicardparams *); 

extern int nbchans (struct capi_ctr *);

extern int msg2stack (unsigned char *);
extern void msg2capi (unsigned char *);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern void enter_critical (void);
extern void leave_critical (void);

extern void kick_scheduler (void);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern void init (unsigned, void (__attr2 *) (void *, unsigned),
			    void (__attr2 *) (void *), 
			    void (__attr2 *) (void));

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcpcmcia__)
extern int fcpcmcia_addcard (unsigned, unsigned);
extern int fcpcmcia_delcard (unsigned, unsigned);
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern int driver_init (void);
extern void driver_exit (void);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#endif

