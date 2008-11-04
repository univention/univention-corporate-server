/* 
 * queue.c
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

#include <linux/spinlock.h>
#include <linux/netdevice.h>
#include "defs.h"
#include "driver.h"
#include "tools.h"
#include "tables.h"
#include "queue.h"

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#define	MAKE_KEY(a,n,h)	(((tag_t)(a)<<48)+((tag_t)(n)<<16)+((tag_t)(h)))
#define	IS_EMPTY(q)	((q)->get==NULL)

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static qitem_t *	free_list = NULL;

static inline qitem_t * alloc_item (void) {
	qitem_t *	item;
	
	if (free_list != NULL) {
		item = free_list;
		free_list = item->succ;
	} else {
		item = (qitem_t *) hmalloc (sizeof (qitem_t));
	}
	info (item != NULL);
	return item;
} /* alloc_item */

static inline void free_item (qitem_t * item) {
	
	assert (item != NULL);
	item->succ = free_list;
	free_list = item;
} /* free_item */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void queue_init (queue_t ** q) { 
    
	if (NULL == (*q = (queue_t *) hmalloc (sizeof (queue_t)))) {
		ERROR("Not enough memory for queue struct.\n");
	} else {
		(*q)->noconf = (*q)->put = (*q)->get = NULL;
		lock_init (&(*q)->lock);
	}
	assert (free_list == NULL);
} /* queue_init */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void queue_exit (queue_t ** q) { 
	qitem_t * item;
    
	assert (q != NULL);
	assert (*q != NULL);
	while ((*q)->get != NULL) {
		item = (*q)->get->succ;
		assert ((*q)->get->msg->list == NULL);
		kfree_skb ((*q)->get->msg);
		hfree ((*q)->get);
		(*q)->get = item;
	}
	while ((*q)->noconf != NULL) {
		item = (*q)->noconf->succ;
		assert ((*q)->noconf->msg->list == NULL);
		kfree_skb ((*q)->noconf->msg);
		hfree ((*q)->noconf);
		(*q)->noconf = item;
	}
	while (free_list != NULL) {
		item = free_list->succ;
		hfree (free_list);
		free_list = item;
	}
	lock_exit (&(*q)->lock);
	hfree (*q);
	*q = NULL;
} /* queue_exit */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static int enqueue (queue_t * q, struct sk_buff * msg) {
	qitem_t * item;

	assert (q != NULL);
	assert (msg != NULL);
	assert (msg->list == NULL);
	if (NULL == (item = alloc_item ())) {
		ERROR("Not enough memory for queue item.\n");
		ERROR("Message lost.\n");
		return 0;
	}
	item->succ = NULL;
	item->msg  = msg;
	item->key  = 0;
	assert (q != NULL);
	if (q->get != NULL) {
		q->put->succ = item;
	} else {
		q->get = item;
	}
	q->put = item;
	return 1;
} /* enqueue */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static struct sk_buff * dequeue (queue_t * q) {
	struct sk_buff * res;
	qitem_t *        item;
	qitem_t *        tmp;

	assert (q != NULL);
	assert (q->get != NULL);
	res = q->get->msg;
	item = q->get->succ;
	tmp = q->get;
	q->get = item;
	free_item (tmp);
	assert (res->list == NULL);
	return res;
} /* dequeue */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int queue_put (queue_t * q, struct sk_buff * msg) {
	int res;
	
	assert (q != NULL);
	lock (q->lock);
	res = enqueue (q, msg);
	unlock (q->lock);
	return res;
} /* queue_put */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
struct sk_buff * queue_get (queue_t * q) {
	struct sk_buff * tmp = NULL;

	assert (q != NULL);
	lock (q->lock);
	if (!IS_EMPTY(q)) {
		tmp = dequeue (q);
	}
	unlock (q->lock);
	return tmp;
} /* queue_get */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int queue_is_empty (queue_t * q) { 

	assert (q != NULL);
	return IS_EMPTY(q) ? TRUE : FALSE; 
} /* queue_is_empty */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void queue_park (
	queue_t *		q, 
	struct sk_buff *	msg,
	unsigned		appl,
	NCCI_t			ncci,
	unsigned		hand
) {
	qitem_t *		item;

	assert (q != NULL);
	assert (msg != NULL);
	lock (q->lock);
	item = alloc_item ();
	unlock (q->lock);
	if (NULL == item) {
		ERROR("Not enough memory for queue item.\n");
		return;
	}
	item->key  = MAKE_KEY (appl, ncci, hand);
	item->msg  = msg;
	item->pred = NULL;
	lock (q->lock);
	item->succ = q->noconf;
	if (q->noconf != NULL) {
		q->noconf->pred = item;
	}
	q->noconf = item;
	unlock (q->lock);
} /* queue_park */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void queue_conf (queue_t * q, unsigned appl, NCCI_t ncci, unsigned hand) {
	qitem_t *		item;
	tag_t			key = MAKE_KEY (appl, ncci, hand);
	struct sk_buff *	tmp = NULL;

	assert (q != NULL);
	lock (q->lock);
	item = q->noconf;
	while ((item != NULL) && (item->key != key)) {
		item = item->succ;
	}
	if (item != NULL) {
		if (item->succ != NULL) {
			item->succ->pred = item->pred;
		}
		if (item->pred != NULL) {
			item->pred->succ = item->succ;
		} else {
			q->noconf = item->succ;
		}
		assert (item->msg);
		tmp = item->msg;
		free_item (item);
	} else {
		LOG("Tried to confirm unknown data b3 message.\n");
	}
	unlock (q->lock);
	if (tmp != NULL) {
		assert (tmp->list == NULL);
		kfree_skb (tmp);
	}
} /* queue_conf */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/

