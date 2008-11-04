/* 
 * tools.c
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

#include <linux/slab.h>
#include <linux/string.h>
#include <linux/vmalloc.h>
#include <linux/kernel.h>
#include "defs.h"
#include "libdefs.h"
#include "driver.h"
#include "lib.h"
#include "lock.h"
#include "tools.h"

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
struct __lock {

	unsigned long		flags;
	spinlock_t		lock;
} ; 

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (TOOLS_PTR_QUEUE)
struct __q {

	unsigned	head, tail, mask;
	unsigned	size, free;
	unsigned	bnum, blen;
	void **		item;
	char *		bptr;
} ;
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
typedef struct __hdr {

	unsigned	type;
#if !defined (NDEBUG)
#if defined (TOOLS_FREE_CATCH)
	unsigned	nfree;
#endif
	unsigned	size;
	unsigned	tag;
#endif
} header_t;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#define KMALLOC_LIMIT	131072

#define	TYPE_NONE	'?'
#define TYPE_KMALLOCED	'k'
#define	TYPE_VMALLOCED	'v'
#define TYPE_SMALLOCED	's'

#define	ALLOC_NORMAL	0
#define	ALLOC_SPECIAL	1

#if !defined (NDEBUG)
#define	PATCH(n)	sizeof(header_t)+sizeof(unsigned)+((n)?(n):1)
#else
#define	PATCH(n)	sizeof(header_t)+((n)?(n):1)
#endif

static void *		halloc (unsigned, int, int);

#define __ALLOC(s,p)	halloc((s),(p),ALLOC_NORMAL)

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (TOOLS_NOMEM_HANDLER)
static nomem_handler_t	handler		= NULL;
#endif

#if defined (TOOLS_SUB_ALLOC)
static void *		lib_heap_base	= NULL;
static unsigned		lib_heap_size	= 0;
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if !defined (NDEBUG)
#include <asm/atomic.h>
#include <linux/spinlock.h>

#define	FENCE_TAG	0xDEADBEEF
#define	FENCE1_OK(h,m)	((h)->tag==FENCE_TAG)
#define	FENCE2_OK(h,m)	(*(unsigned *)(((char *) m)+(h)->size)==FENCE_TAG)

static unsigned		alloc_count	= 0;
static spinlock_t	track_lock	= SPIN_LOCK_UNLOCKED;

#if !defined (NDEBUG) && defined (LOG_TIMER)
static struct timeval	zero_time;
#endif
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if !defined (NDEBUG)
static inline void track_alloc (header_t * hdr) {
	unsigned long	flags;

#if defined (LOG_ALLOC)
	LOG("ALLOC: %p, %u, type %c\n", hdr + 1, hdr->size, hdr->type);
#endif
	spin_lock_irqsave (&track_lock, flags);
	alloc_count += hdr->size;
	/* <<< */
	spin_unlock_irqrestore (&track_lock, flags);
} /* track_alloc */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if !defined (NDEBUG)
static inline void track_free (header_t * hdr) {
	unsigned long	flags;

#if defined (LOG_ALLOC)
	LOG("FREE: %p, %u, type %c\n", hdr + 1, hdr->size, hdr->type);
#endif
	spin_lock_irqsave (&track_lock, flags);
	info (alloc_count >= hdr->size);
	alloc_count -= hdr->size;
	/* <<< */
	spin_unlock_irqrestore (&track_lock, flags);
} /* track_free */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (TOOLS_SUB_ALLOC)
unsigned libheap_init (unsigned heap_size) {
	void *	heap_base = NULL;

	assert (lib_heap_base == NULL);
	assert (heap_size > MIN_LIB_HEAP_SIZE);
	do {
		heap_base = halloc (heap_size, GFP_ATOMIC, ALLOC_SPECIAL);
		info (heap_base != NULL);
		if (NULL != heap_base) {
			lib_heap_base = heap_base;
			lib_heap_size = heap_size;
			(*capi_lib->lib_heap_init) (heap_base, heap_size);
			return heap_size;
		}
		heap_size /= 2;
	} while (heap_size > 0);
	return 0;
} /* libheap_init */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (TOOLS_SUB_ALLOC)
void libheap_exit (void) {

	assert (lib_heap_base != NULL);
	(*capi_lib->lib_heap_exit) (lib_heap_base);
	hfree (lib_heap_base);
	lib_heap_base = NULL;
	lib_heap_size = 0;
} /* libheap_exit */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (TOOLS_NOMEM_HANDLER)
nomem_handler_t hset_handler (nomem_handler_t hndf) {
	nomem_handler_t	oldf = handler;
	
	handler = hndf;
	return oldf;
} /* hset_handler */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if !defined (NDEBUG)
unsigned hallocated (void) {
    
	return alloc_count;
} /* hallocated */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if !defined (NDEBUG)
int hvalid (void * mem) {
	header_t *	hdr;
	int		flag = TRUE;

	if (mem != NULL) {
		hdr  = ((header_t *) mem) - 1;
		flag = FENCE1_OK(hdr, mem) && FENCE2_OK(hdr, mem);
	} 
	return flag;
} /* hvalid */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void * hmalloc (unsigned size) {

	return __ALLOC(size, GFP_ATOMIC);
} /* hmalloc */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void * hcalloc (unsigned size) {
	void * mem;

	mem = __ALLOC(size, GFP_ATOMIC);
	if ((mem != NULL) && (size != 0)) {
		lib_memset (mem, 0, size);
	}
	return mem;
} /* hcalloc */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void * hmalloc_kernel (unsigned size) {

	return __ALLOC(size, GFP_KERNEL);
} /* hmalloc */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void * hcalloc_kernel (unsigned size) {
	void * mem;

	mem = __ALLOC(size, GFP_KERNEL);
	if ((mem != NULL) && (size != 0)) {
		lib_memset (mem, 0, size);
	}
	return mem;
} /* hcalloc */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void * halloc (unsigned size, int prio, int mode) {
	unsigned	n, type;
	void *		mem;
	header_t *	hdr;

	/* Allocate */
	n = PATCH(size);
	if (n <= KMALLOC_LIMIT) {
		hdr  = kmalloc (n, prio);
		type = TYPE_KMALLOCED;
	} else {
#if defined (TOOLS_SUB_ALLOC)
		if (ALLOC_NORMAL == mode) {
			info (lib_heap_base != NULL);
			assert (capi_lib->lib_heap_alloc != NULL);
			hdr  = (* capi_lib->lib_heap_alloc) (lib_heap_base, n);
			type = TYPE_SMALLOCED;
		} else {
			assert (ALLOC_SPECIAL == mode);
			hdr  = vmalloc (n);
			type = TYPE_VMALLOCED;
		}
#else
		hdr  = vmalloc (n);
		type = TYPE_VMALLOCED;
#endif
	}

	/* Accounting & debugging */
	info (hdr != NULL);
	if (NULL == hdr) {
		LOG(
			"Memory request (%u/%u bytes) failed.\n", 
			size, 
			PATCH(size)
		);
		mem = NULL;
#if defined (TOOLS_NOMEM_HANDLER)
		if (handler != NULL) {
			(*handler) (size);
		}
#endif
	} else {
		mem = (void *) (hdr + 1);
		hdr->type = type;
#if !defined (NDEBUG)
		hdr->size = size ? size : 1;
		hdr->tag = FENCE_TAG;
#if defined (TOOLS_FREE_CATCH)
		hdr->nfree = 0;
#endif
		* (unsigned *) (((char *) mem) + size) = FENCE_TAG;
		track_alloc (hdr);
#endif
	}
	return mem;
} /* halloc */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void hfree (void * mem) {
	header_t *	hdr;

	info (mem != NULL);
	if (mem != NULL) {

		/* Accounting & checking */
		hdr = ((header_t *) mem) - 1;
#if !defined (NDEBUG)
		if (!(FENCE1_OK(hdr, mem) && FENCE2_OK(hdr, mem))) {
			LOG(
				"FENCE VIOLATED (%u bytes @ %p)!\n", 
				hdr->size, 
				mem
			);
		}
		track_free (hdr);
#endif

		/* Release */
#if !defined (TOOLS_FREE_CATCH)
		switch (hdr->type) {

		default:
			assert (0);
			break;
		case TYPE_KMALLOCED:
			kfree (hdr);
			break;
		case TYPE_VMALLOCED:
			vfree (hdr);
			break;
#if defined (TOOLS_SUB_ALLOC)
		case TYPE_SMALLOCED:
			assert (capi_lib->lib_heap_free != NULL);
			info (lib_heap_base != NULL);
			(* capi_lib->lib_heap_free) (lib_heap_base, hdr);
			break;
#endif
		}
#else
		if (hdr->nfree != 0) {
			ERROR(
				"ALREADY FREED (%u bytes @ %p)!\n",
				hdr->size,
				mem
			);
		}
		hdr->nfree++;
		/* Memory leak! */
#endif
	}
} /* hfree */

/*---------------------------------------------------------------------------*\
\*-T-------------------------------------------------------------------------*/

#if !defined (NDEBUG) && defined (LOG_TIMER)

#include <linux/time.h>

void setup_timer (dbg_timer * t, long dsec, long dusec) {
	
	assert (t != NULL);
	lib_memset (&t->t, 0, sizeof (t->t));
	t->d.tv_sec  = dsec;
	t->d.tv_usec = dusec;
} /* setup_timer */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int check_timer (dbg_timer * t) {
	int		res = 1;
	struct timeval	now;
	struct timeval	delta;
	
	assert (t != NULL);
	do_gettimeofday (&now);
	timeval_less (now, zero_time, &delta);
	now = delta;
	timeval_less (now, t->t, &delta);
	if ((delta.tv_sec > t->d.tv_sec) 
	|| ((delta.tv_sec == t->d.tv_sec) && (delta.tv_usec > t->d.tv_usec))
	) {
		note (
			"Timer '%s' exceeded: %ld s, %ld µs\n", 
			t->name,
			delta.tv_sec,
			delta.tv_usec
		);
		res = 0;
	} 
	return res;
} /* check_timer */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int check_timer_cb (dbg_timer * t, void (* callback) (dbg_timer *, struct timeval *)) {
	int		res = 1;
	struct timeval	now;
	struct timeval	delta;
	
	assert (t != NULL);
	do_gettimeofday (&now);
	timeval_less (now, zero_time, &delta);
	now = delta;
	timeval_less (now, t->t, &delta);
	if ((delta.tv_sec > t->d.tv_sec) 
	|| ((delta.tv_sec == t->d.tv_sec) && (delta.tv_usec > t->d.tv_usec))
	) {
		if (callback != NULL) {
			(*callback) (t, &delta);
		}
		res = 0;
	} 
	return res;
} /* check_timer_cb */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void touch_timer (dbg_timer * t) {
	struct timeval	temp, delta;
	
	assert (t != NULL);
	do_gettimeofday (&temp);
	timeval_less (temp, zero_time, &delta);
	t->t = delta;
} /* touch_timer */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void start_watch (dbg_timer * w) {
	struct timeval	temp, delta;
	
	assert (w != NULL);
	do_gettimeofday (&temp);
	timeval_less (temp, zero_time, &delta);
	w->t = delta;
} /* start_watch */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void stop_watch (dbg_timer * w) {
	struct timeval	temp, delta;
	
	assert (w != NULL);
	do_gettimeofday (&temp);
	timeval_less (temp, zero_time, &delta);
	temp = delta;
	timeval_less (temp, w->t, &delta);
	w->t = delta;
} /* stop_watch */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int timers_start (void) {

	do_gettimeofday (&zero_time);
	return 1;
} /* timers_start */
     
/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void timers_stop (void) {

} /* timers_stop */

#endif /* !NDEBUG && LOG_TIMER */

/*---------------------------------------------------------------------------*\
\*-M-------------------------------------------------------------------------*/
void vlprintf (const char * level, const char * fmt, va_list args) {
	static char line[1024];

	vsnprintf (line, sizeof (line), fmt, args);
	printk ("%s%s: %s", level, TARGET, line); 
} /* vlprintf */
 
/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void lprintf (const char * level, const char * fmt, ...) {
	va_list args;

	va_start (args, fmt);
	vlprintf (level, fmt, args);
	va_end (args);
} /* lprintf */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void message (const char * fmt, ...) {
	va_list args;

	va_start (args, fmt);
	vlprintf (KERN_INFO, fmt, args);
	va_end (args);
} /* message */

/*---------------------------------------------------------------------------*\
\*-L-------------------------------------------------------------------------*/
int lock_init (lock_t * plock) {
	lock_t	tmp;

	assert (plock != NULL);
	if (NULL == (tmp = (lock_t) hcalloc (sizeof (struct __lock)))) {
		ERROR("Could not allocate lock structure!!!\n");
		return 0;
	}
	tmp->lock = SPIN_LOCK_UNLOCKED;
	*plock = tmp;
	return 1;
} /* lock_init */
	
/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void lock_exit (lock_t * plock) {

	assert (plock != NULL);
	assert (*plock != NULL);
	assert (!spin_is_locked (&(*plock)->lock));
	hfree (*plock);
	*plock = NULL;
} /* lock_exit */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void lock (lock_t lp) {
	unsigned long	local_flags;

	assert (lp != NULL);
	spin_lock_irqsave (&lp->lock, local_flags);
	lp->flags = local_flags;
} /* lock */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void unlock (lock_t lp) {
	
	assert (lp != NULL);
	spin_unlock_irqrestore (&lp->lock, lp->flags);
} /* unlock */

/*---------------------------------------------------------------------------*\
\*-Q-------------------------------------------------------------------------*/
#if defined (TOOLS_PTR_QUEUE)
ptr_queue_p q_make (unsigned max) {
	ptr_queue_p	qp;
	unsigned	mask = 1;
	
	if (NULL == (qp = (ptr_queue_p) hmalloc (sizeof (ptr_queue_t)))) {
		return NULL;
	}
	if (NULL == (qp->item = (void **) hmalloc (max * sizeof (void *)))) {
		hfree (qp);
		return NULL;
	}
	qp->bptr = NULL;
	while (mask < max) {
		mask <<= 1;
	}
	assert (mask == max);
	--mask;
	qp->head = 0;
	qp->tail = 0;
	qp->mask = mask;
	qp->size = max;
	qp->free = max;
	return qp;
} /* q_make */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void q_remove (ptr_queue_p * qpp) {
	ptr_queue_p	qp;
	
	assert (qpp != NULL);
	qp = *qpp;
	assert (qp != NULL);
	assert (qp->item != NULL);
	if (qp->bptr != NULL) {
		hfree (qp->bptr);
	}
	hfree (qp->item);
	hfree (qp);
	*qpp = NULL;
} /* q_remove */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void q_reset (ptr_queue_p qp) {

	assert (qp != NULL);
	qp->head = qp->tail = 0;
	qp->free = qp->size;
} /* q_reset */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int q_attach_mem (ptr_queue_p qp, unsigned n, unsigned len) {
	void *		buf;

	assert (qp != NULL);
	assert (qp->bptr == 0);
	assert ((n * len) != 0);
	if (NULL == (buf = hmalloc (n * len))) {
		return FALSE;
	} 
	qp->bnum = n;
	qp->blen = len;
	qp->bptr = buf;
	return TRUE;
} /* q_attach_mem */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int q_enqueue (ptr_queue_p qp, void * p) {

	assert (qp != NULL);
	if (qp->free == 0) {
		return FALSE;
	}
	assert (qp->head < qp->size);
	qp->item[qp->head++] = p;
	qp->head &= qp->mask;
	assert (qp->head < qp->size);
	qp->free--;
	return TRUE;
} /* q_enqueue */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int q_enqueue_mem (ptr_queue_p qp, void * m, unsigned len) {
	unsigned	ix;
	char *		mp;
	
	assert (qp != NULL);
	assert (qp->bptr != NULL);
	assert (qp->blen >= len);
	if (qp->free == 0) {
		return FALSE;
	}
	assert (qp->head < qp->size);
	ix = qp->head++;
	qp->head &= qp->mask;
	qp->item[ix] = mp = &qp->bptr[ix * len];
	assert (mp != NULL);
	lib_memcpy (mp, m, len);
	assert (qp->head < qp->size);
	qp->free--;
	return TRUE;
} /* q_enqueue_mem */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int q_dequeue (ptr_queue_p qp, void ** pp) {

	assert (qp != NULL);
	if (qp->free == qp->size) {
		return FALSE;
	}
	assert (qp->tail < qp->size);
	assert (pp != NULL);
	*pp = qp->item[qp->tail++];
	qp->tail &= qp->mask;
	assert (qp->tail < qp->size);
	qp->free++;
	return TRUE;
} /* q_dequeue */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int q_peek (ptr_queue_p qp, void ** pp) {

	assert (qp != NULL);
	if (qp->free == qp->size) {
		return FALSE;
	}
	assert (qp->tail < qp->size);
	assert (pp != NULL);
	*pp = qp->item[qp->tail];
	return TRUE;
} /* q_peek */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
unsigned q_get_count (ptr_queue_p qp) {

	assert (qp != NULL);
	return qp->size - qp->free;
} /* q_get_count */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (TOOLS_MEM_DUMP)
void memdump (
	const void *	mem,
	unsigned	len,
	unsigned	start,
	const char *	msg
) {
        unsigned        max, min, idx;
        unsigned char * data = (unsigned char *) mem;
        char            hex[50], chr[20];

	lprintf (KERN_INFO, "Memory dump %s:\n", msg);
        min = 0;
        while (min < len) {
                max = ((min + 16) > len ? len : min + 16);
                idx = 0;
                while ((min + idx) < max) {
                        snprintf (hex + 3 * idx, 4, "%02x ", *data);
                        snprintf (chr + idx, 2, "%c", ((' ' <= *data) &&
                                        (*data <= '~')) ? *data : '.');
                        ++idx;
                        ++data;
                }
                while (idx < 16) {
                        lib_strcpy (hex + 3 * idx++, "   ");
                }
                lprintf (KERN_INFO, "%08x: %s  %s\n", min + start, hex, chr);
                min = max;
        }
} /* memdump */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#ifndef NDEBUG
__attr void _OSassert (void * exp, void * file, unsigned line) {

	message ("assert (%s) in %s(%u)\n", exp, file, line);
} /* _OSassert */

__attr void _OSinfo (void * exp, void * file, unsigned line) {

	message ("info (%s) in %s(%u)\n", exp, file, line);
} /* _OSinfo */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/

