/* 
 * tools.h
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

#ifndef __have_tools_h__
#define __have_tools_h__

#include <asm/atomic.h>
#include <linux/types.h>
#include <linux/spinlock.h>
#include <stdarg.h>
#include "defs.h"

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#define	__kcapi
#define	__stack

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (DRIVER_TYPE_USB)
#if defined (info)
#undef info
#endif
#endif

#ifndef NDEBUG

extern void message (const char *, ...);

# define assert(x)	(!(x)?message("%s(%d): assert (%s) failed\n", \
                                        __FILE__, __LINE__, #x):((void)0))
# define info(x)	(!(x)?message("%s(%d): info (%s) failed\n", \
					__FILE__, __LINE__, #x):((void)0))
# define LOG(f,x...)	message (f, ##x)
#else
# define assert(x)
# define info(x)
# define LOG(f,x...)
#endif

#if defined (LOG_MESSAGES)
# define MLOG		LOG
#else
# define MLOG(f, a...)	
#endif

#define ERROR(f,x...)	lprintf (KERN_ERR, f, ##x)
#define NOTE(f,x...)	lprintf (KERN_INFO, f, ##x)

extern void lprintf  (const char *, const char *, ...);
extern void vlprintf (const char *, const char *, va_list);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#ifndef atomic_xchg
static inline unsigned long atomic_xchg (
	volatile atomic_t *	v, 
	unsigned		value
) {
	return __xchg (value, &v->counter, sizeof (unsigned));
} /* atomic_xchg */
#endif
/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#ifndef NDEBUG
extern unsigned hallocated (void);
extern int hvalid (void *);
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern void * hmalloc (unsigned);
extern void * hcalloc (unsigned);
extern void * hmalloc_kernel (unsigned);
extern void * hcalloc_kernel (unsigned);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern void hfree (void *);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (TOOLS_NOMEM_HANDLER)
typedef void (* nomem_handler_t) (unsigned);

extern nomem_handler_t hset_handler (nomem_handler_t);
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (TOOLS_SUB_ALLOC)
extern unsigned libheap_init (unsigned);
extern void libheap_exit (void);
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (TOOLS_PTR_QUEUE)
typedef struct __q ptr_queue_t, * ptr_queue_p;

extern ptr_queue_p q_make (unsigned);
extern void q_remove (ptr_queue_p *);
extern void q_reset (ptr_queue_p);

extern int q_attach_mem (ptr_queue_p, unsigned, unsigned);

extern int q_dequeue (ptr_queue_p, void **);
extern int q_peek (ptr_queue_p, void **);
extern int q_enqueue (ptr_queue_p, void *);
extern int q_enqueue_mem (ptr_queue_p, void *, unsigned);

extern unsigned q_get_count (ptr_queue_p);
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (TOOLS_MEM_DUMP)
extern void memdump (const void *, unsigned, unsigned, const char *);
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if !defined (NDEBUG) && defined (LOG_TIMER)

#include <linux/time.h>

typedef struct {

	const char *	name;
	struct timeval	t;
	struct timeval	d;
} dbg_timer;

#define	PRINT_TIMER(x)		log ( \
					"Timer '%s': %ld s, %ld µs\n", \
					(x)->name, \
					(x)->t.tv_sec, (x)->t.tv_usec \
				)
#define	PRINT_TIME_MSG(s,x)	log ( \
					"%s: %ld s, %ld µs\n", \
					s, (x)->t.tv_sec, (x)->t.tv_usec \
				)

#define	WATCH_DECL(id)		dbg_timer	id##_timer
#define	WATCH_START(id)		start_watch (&id##_timer)
#define	WATCH_STOP(id)		stop_watch (&id##_timer); \
				PRINT_TIME_MSG(#id,&id##_timer)
	
/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern int timers_start (void);
extern void timers_stop (void);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern void setup_timer (dbg_timer *, long, long);
extern int check_timer (dbg_timer *);
extern int check_timer_cb (dbg_timer *, void (*) (dbg_timer *, struct timeval *));
extern void touch_timer (dbg_timer *);

extern void start_watch (dbg_timer *);
extern void stop_watch (dbg_timer *);
#else
#define	PRINT_TIMER(t)
#define	WATCH_DECL(name)
#define	WATCH_START(name)
#define	WATCH_STOP(name)
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#endif
