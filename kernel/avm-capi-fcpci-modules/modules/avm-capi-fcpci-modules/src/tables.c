/* 
 * tables.c
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

#include <linux/skbuff.h>
#include <linux/netdevice.h>
#include <linux/list.h>
#include <linux/capi.h>
#include <linux/kernelcapi.h>
#include <linux/isdn/capicmd.h>
#include <linux/isdn/capiutil.h>
#include <linux/isdn/capilli.h>
#include "defs.h"
#include "main.h"
#include "lib.h"
#include "driver.h"
#include "tools.h"
#include "queue.h"
#include "tables.h"

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static appl_t * create_appl (
	appltab_t *	tab, 
	unsigned	id, 
	unsigned	ncount, 
	unsigned	bcount, 
	unsigned	bsize
) {
	appl_t *	appp;

	if (NULL == (appp = (appl_t *) hcalloc (sizeof (appl_t)))) {
		ERROR("Not enough memory for application record.\n");
		return NULL;
	}
	appp->id         = id;
	appp->ncci_count = ncount;
	appp->blk_count  = bcount;
	appp->blk_size   = bsize;
	lock (tab->lock);
	appp->succ       = tab->appl_root;
	tab->appl_root = appp;
	if (NULL != appp->succ) {
		appp->succ->pred = appp;
	}
	tab->appl_count++;
	unlock (tab->lock);
	return appp;
} /* create_appl */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void remove_appl (appltab_t * tab, appl_t * appp) {
	ncci_t *	nccip;
	ncci_t *	tmp;

	assert (appp);
	lock (tab->lock);
	if (appp->pred != NULL) {
		appp->pred->succ = appp->succ;
	} else {
		tab->appl_root = appp->succ;
	}
	if (appp->succ != NULL) {
		appp->succ->pred = appp->pred;
	}
	if (appp->data != NULL) {
		hfree (appp->data);
		appp->data = NULL;
	}
	nccip = appp->root;
	tab->appl_count--;
	unlock (tab->lock);
	while (nccip != NULL) {
		tmp = nccip->succ;
		remove_ncci (tab, appp, nccip);
		nccip = tmp;
	}
	capilib_release_appl (&tab->ncci_head, appp->id);
	hfree (appp);
} /* remove_appl */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static appl_t * search_appl (appltab_t * tab, unsigned id) {
	appl_t * appp;

	lock (tab->lock);
	appp = tab->appl_root;
	while (appp != NULL) {
		if (appp->id == id) {
			break;
		}
		appp = appp->succ;
	}
	unlock (tab->lock);
	info (appp);
	return appp;
} /* search_appl */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static ncci_t * locate_ncci (appltab_t * tab, appl_t * appp, NCCI_t ncci) {
	ncci_t *	tmp;

	assert (tab != NULL);
	assert (appp != NULL);
	lock (tab->lock);
	tmp = appp->root;
	while ((tmp != NULL) && (tmp->ncci != ncci)) {
		tmp = tmp->succ;
	}
	unlock (tab->lock);
	info (tmp);
	return tmp;
} /* locate_ncci */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static appl_t * get_appl (appltab_t * tab, unsigned ix) {
	appl_t *	appp = NULL;

	assert (ix < tab->appl_count);
	lock (tab->lock);
	if (ix < tab->appl_count) {
		appp = tab->appl_root;
		while (ix > 0) {
			appp = appp->succ;
			--ix;
		}
	}
	unlock (tab->lock);
	return appp;
} /* get_appl */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
appl_t * next_appl (appltab_t * tab, appl_t * appp) {

	UNUSED_ARG (tab);
	assert (appp != NULL);
	return appp->succ;
} /* next_appl */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
appl_t * first_appl (appltab_t * tab) {

	return tab->appl_root;
} /* first_appl */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int appl_alive (appltab_t * tab, unsigned appl) {
	appl_t *	appp;
	int		res = FALSE;
	
	if (NULL != (appp = search_appl (tab, appl))) {
		res = !appp->dying;
	}
	return res;
} /* appl_alive */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void table_init (appltab_t ** tab) {

	if (NULL != (*tab = (appltab_t *) hmalloc (sizeof (appltab_t)))) {
		(*tab)->appl_root  = NULL;
		(*tab)->appl_count = 0;
		(void) lock_init (&(*tab)->lock);
		INIT_LIST_HEAD(&(*tab)->ncci_head);
	}
} /* table_init */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void table_exit (appltab_t ** tab) {
	appl_t *	appp;
	appl_t *	tmp;
    
	assert (*tab);
	appp = (*tab)->appl_root;
	while (appp != NULL) {
		tmp = appp->succ;
		remove_appl (*tab, appp);
		if (appp->data != NULL) {
			hfree (appp->data);
		}
		appp = tmp;
	}
	lock_exit (&(*tab)->lock);
	hfree (*tab);
	*tab = NULL;
} /* table_exit */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static capiinfo_t handle_message (
	appltab_t *		tab,
	queue_t *		q,
	struct sk_buff *	msg
) {
	unsigned		appl;
	appl_t *		appp;
	capiinfo_t		ci = CAPI_NOERROR;

	assert (tab != NULL);
	assert (q != NULL);
	assert (msg != NULL);
	appl = CAPIMSG_APPID (msg->data);
	if (NULL == (appp = search_appl (tab, appl))) {
		ERROR("Unknown application id! (%u)\n", appl);
		ci = CAPI_ILLAPPNR;
		goto done;
	}
	switch (CAPIMSG_CMD(msg->data)) {

	case CAPI_DATA_B3_REQ:
		ci = capilib_data_b3_req (
			&tab->ncci_head, 
			appl, 
			CAPIMSG_NCCI(msg->data),
			CAPIMSG_MSGID(msg->data)
		);
		break;

	case 0xFE80:
		appp->dying = TRUE;
	default:
		break;
		
	}
	if (ci == CAPI_NOERROR) {
		if (0 == queue_put (q, msg)) {
			ERROR("Message queue overflow!\n");
			ci = CAPI_SENDQUEUEFULL;
		}
	}
done:
	return ci;
} /* handle_message */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
capiinfo_t handle_data_conf (appltab_t * tab, queue_t * q, unsigned char * m) {
	unsigned	appl, hand;
	NCCI_t		ncci;
	
	assert (tab != NULL);
	assert (q != NULL);
	assert (m != NULL);
	assert (CAPIMSG_CMD(m) == CAPI_DATA_B3_CONF);
	appl = CAPIMSG_APPID(m);
	ncci = CAPIMSG_NCCI(m);
	hand = CAPIMSG_U16(m, 12);
	queue_conf (q, appl, ncci, hand);
	capilib_data_b3_conf (&tab->ncci_head, appl, ncci, CAPIMSG_MSGID(m));
	return CAPI_NOERROR;
} /* handle_data_conf */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static ncci_t * create_ncci (	
	appltab_t *		tab, 
	appl_t *		appp, 
	NCCI_t			ncci, 
	unsigned		wsize, 
	unsigned		bsize
) {
	ncci_t *		tmp;
	unsigned char **	data;

	if (NULL == (tmp = (ncci_t *) hmalloc (sizeof (ncci_t)))) {
		ERROR("Failed to allocate NCCI record.\n");
		return NULL;
	}
	data = (unsigned char **) hcalloc (sizeof (unsigned char *) 
							* appp->blk_count);
	if (NULL == data) {
		ERROR("Failed to allocate data buffer directory.\n");
		hfree (tmp);
		return NULL;
	}
	LOG("New NCCI(%x), window size %u...\n", ncci, wsize);
	capilib_new_ncci (&tab->ncci_head, appp->id, ncci, wsize);
	tmp->ncci     = ncci;
	tmp->appl     = appp->id;
	tmp->win_size = wsize;
	tmp->blk_size = bsize;
	tmp->data     = data;
	tmp->pred     = NULL;
	lock (tab->lock);
	tmp->succ     = appp->root;
	appp->root    = tmp;
	if (NULL != tmp->succ) {
		tmp->succ->pred = tmp;
	}
	appp->nncci++;
	unlock (tab->lock);
	return tmp;
} /* create_ncci */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void remove_ncci (appltab_t * tab, appl_t * appp, ncci_t * nccip) {
	unsigned	i;

	assert (appp);
	assert (nccip);
	if (nccip != NULL) {
		LOG("Remove NCCI(%x), appl %u...\n", nccip->ncci, appp->id);
		capilib_free_ncci (&tab->ncci_head, appp->id, nccip->ncci);
		lock (tab->lock);
		for (i = 0; i < appp->blk_count; i++) {
			if (nccip->data[i] != NULL) {
				hfree (nccip->data[i]);
			}
		}
		hfree (nccip->data);
		if (nccip->succ != NULL) {
			nccip->succ->pred = nccip->pred;
		}
		if (nccip->pred != NULL) {
			nccip->pred->succ = nccip->succ;
		} else {
			appp->root = nccip->succ;
		}
		hfree (nccip);
		appp->nncci--;
		unlock (tab->lock);
	}
} /* remove_ncci */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static unsigned char * ncci_data_buffer (
	appltab_t *	tab,
	appl_t *	appp,
	NCCI_t		ncci,
	unsigned	index
) {
	ncci_t *	nccip;

	assert (tab != NULL);
	assert (appp != NULL);
        if (NULL == (nccip = locate_ncci (tab, appp, ncci))) {
                LOG("Data buffer request failed. NCCI not found.\n");
                return NULL;
        }
        lock (tab->lock);
        if (index >= appp->blk_count) {
                unlock (tab->lock);
                LOG("Data buffer index out of range.\n");
                return NULL;
        }
        if (nccip->data[index] == NULL) {
                if (NULL == (nccip->data[index] = (unsigned char *) hmalloc (appp->blk_size))) {
                        ERROR("Not enough memory for data buffer.\n");
                }
        }
        unlock (tab->lock);
        return nccip->data[index];
} /* ncci_data_buffer */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static struct sk_buff * make_0xfe_request (unsigned appl) {
	unsigned char		req[8];
	struct sk_buff *	skb;

	if (NULL == (skb = alloc_skb (8, GFP_ATOMIC))) {
		ERROR("Unable to allocate message buffer.\n");
	} else {    
		req[0] = 8;
		req[1] = 0;
		req[2] = appl & 0xFF;
		req[3] = (appl >> 8) & 0xFF;
		req[4] = 0xFE;
		req[5] = 0x80;
		lib_memcpy (skb_put (skb, sizeof (req)), &req, sizeof (req));
	}
	return skb;
} /* make_0xfe_request */

/*---------------------------------------------------------------------------*\
\*-S-------------------------------------------------------------------------*/
void * __stack data_by_id (unsigned appl_id) {
	appl_t * appp;

	assert (capi_card != NULL);
	appp = search_appl (capi_card->appls, appl_id);
	return (appp != NULL) ? appp->data : NULL;
} /* data_by_id */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (DRIVER_TYPE_DSL_RAP)
unsigned __stack attr_by_id (unsigned appl_id) {
	appl_t * appp;

	appp = search_appl (capi_card->appls, appl_id);	
	return (appp != NULL) ? appp->attr : 0;
} /* attr_by_id */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void * __stack first_data (int * res) {
	appl_t * appp;

	assert (capi_card != NULL);
	assert (res != NULL);
	appp = first_appl (capi_card->appls);
	*res = (appp != NULL) ? 0 : -1;
	return (appp != NULL) ? appp->data  : NULL;
} /* first_data */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void * __stack next_data (int * res) {
	appl_t * appp;

	assert (capi_card != NULL);
	assert (res != NULL);
	if (NULL != (appp = get_appl (capi_card->appls, *res))) {
		appp = next_appl (capi_card->appls, appp);
	}
	*res = (appp != NULL) ? 1 + *res : -1;
	return (appp != NULL) ? appp->data  : NULL;
} /* next_data */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int __stack appl_profile (unsigned appl_id, unsigned * bs, unsigned * bc) {
	appl_t * appp;

	assert (capi_card != NULL);
	appp = search_appl (capi_card->appls, appl_id);
	if (NULL == appp) {
		return 0;
	}
	if (bs) { 
		*bs = appp->blk_size; 
	}
	if (bc) { 
		*bc = appp->blk_count; 
	}
	return 1;
} /* appl_profile */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void __stack new_ncci (
	unsigned	appl_id, 
	__u32		ncci,
	unsigned	winsize,
	unsigned	blksize
) {
	appl_t *	appp;
	ncci_t *	nccip;

	assert (capi_card != NULL);
	MLOG("NEW NCCI(appl:%u,ncci:%lX)\n", appl_id, ncci);
	if (NULL == (appp = search_appl (capi_card->appls, appl_id))) {
		ERROR("Unknown application id #%u\n", appl_id);
		return;
	}
	nccip = create_ncci (
			capi_card->appls, 
			appp, 
			(NCCI_t) ncci, 
			winsize, 
			blksize
			);
	if (NULL == nccip) {
		LOG("Cannot handle new NCCI...\n");
		return;
	}
} /* new_ncci */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void __stack free_ncci (unsigned appl_id, __u32 ncci) {
	appl_t *	appp;
	ncci_t *	nccip;

	assert (capi_card != NULL);
	appp = search_appl (capi_card->appls, appl_id);
	if (NULL == appp) {
		ERROR("Unknown application id #%u\n", appl_id);
		return;
	}
	if (0xFFFFFFFF == ncci) {		/* 2nd phase RELEASE */
		dec_use_count ();
		capi_card->count--;
		MLOG("FREE APPL(appl:%u)\n", appl_id);
		remove_appl (capi_card->appls, appp);
	} else if (NULL != (nccip = locate_ncci (capi_card->appls, appp, ncci))) {
		MLOG("FREE NCCI(appl:%u,ncci:%lX)\n", appl_id, ncci);
		remove_ncci (capi_card->appls, appp, nccip);
	} else {
		ERROR("Attempt to free unknown NCCI.\n");
	}
} /* free_ncci */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
unsigned char * __stack data_block (
	unsigned	appl_id,
	__u32		ncci,
	unsigned	handle
) {
	appl_t *	appp;
 
	assert (capi_card != NULL);
	appp = search_appl (capi_card->appls, appl_id);
	if (NULL == appp) {
		ERROR("Unknown application id #%u\n", appl_id);
		return NULL;
	}
	return ncci_data_buffer (capi_card->appls, appp, ncci, handle);
} /* data_block */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void __kcapi release_appl (struct capi_ctr * ctrl, u16 appl) {
	card_t *		card;
	appl_t *		appp;
	struct sk_buff *	skb;
	capiinfo_t		res;
	
	MLOG("RELEASE(appl:%u)\n", appl);
	assert (ctrl != NULL);
	card = GET_CARD(ctrl);
#if defined (DRIVER_TYPE_DSL)
	if (ctrl->cnr != card->ctrl2) {
		return;
	}
#endif
	info (capi_card->rel_func != NULL);
	if (capi_card->rel_func != NULL) {
		appp = search_appl (capi_card->appls, appl);
		assert (appp != NULL);
		(*capi_card->rel_func) (appp->data);
	}
	skb = make_0xfe_request (appl);
	res = handle_message (card->appls, card->queue, skb);
	info (res == CAPI_NOERROR);
	kick_scheduler ();
} /* release_appl */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
u16 __kcapi send_msg (struct capi_ctr * ctrl, struct sk_buff * skb) {
	card_t *	card;
	capiinfo_t	ci;

	assert (ctrl != NULL);
	assert (skb != NULL);
	assert (skb->list == NULL);
	card = GET_CARD(ctrl);
	ci = handle_message (card->appls, card->queue, skb);
	kick_scheduler ();
	return ci;
} /* send_msg */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void __kcapi register_appl (
	struct capi_ctr *	ctrl, 
	u16			appl, 
	capi_register_params *	args
) {
	card_t *		card;
	appl_t *		appp;
	void *			ptr;
	unsigned		nc;

	MLOG("REGISTER(appl:%u)\n", appl);
	assert (ctrl != NULL);
	assert (ctrl->driverdata != NULL);
	assert (args != NULL);
	card = GET_CARD(ctrl);
#if defined (DRIVER_TYPE_DSL)
	if (ctrl->cnr != card->ctrl2) {
		return;
	}
#endif
	if ((int) args->level3cnt < 0) {
		nc = nbchans (ctrl) * -((int) args->level3cnt);
	} else {
		nc = args->level3cnt;
	}
	if (0 == nc) {
		nc = nbchans (ctrl);
	}
	appp = create_appl (
			card->appls, 
			appl, 
			nc, 
			args->datablkcnt, 
			args->datablklen
			);
	if (NULL == appp) {
		LOG("Unable to create application record.\n");
		return;
	}
	ptr = hcalloc (card->length);
	if (NULL == ptr) {
		ERROR("Not enough memory for application data.\n");
		remove_appl (card->appls, appp);
	} else {
		inc_use_count ();
		lock (card->appls->lock);
		card->count++;
		appp->data = ptr;
		unlock (card->appls->lock);
		(*card->reg_func) (ptr, appl);
	}
} /* register_appl */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/

