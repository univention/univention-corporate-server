/* 
 * lib.c
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

#include <asm/param.h>
#include <asm/io.h>
#include <linux/mm.h>
#include <linux/kernel.h>
#include <linux/wait.h>
#include <linux/sched.h>
#include <stdarg.h>
#include "main.h"
#include "driver.h"
#include "queue.h" 
#include "defs.h"
#include "tools.h"
#include "libstub.h"
#include "lib.h"

#if defined (DRIVER_TYPE_DSL_RAP)
#include "devif.h"
#endif

#define	PRINTF_BUFFER_SIZE	1024
#define	TEN_MSECS		(HZ/100)
#define JIFF2MSEC		(1000/HZ)

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static unsigned long long	j64 = 0;
static unsigned long		j32 = 0;

static DECLARE_WAIT_QUEUE_HEAD(delay);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (LOG_STACK_MSG)
#include <linux/isdn/capicmd.h>
#include <linux/isdn/capiutil.h>

#define	VEC_BITLEN		(sizeof(unsigned)*8)
#define	VEC_LENGTH		(256/VEC_BITLEN)
#define	VEC_MSGIDX(c)		(((c)&255)/VEC_BITLEN)
#define	VEC_MSGMSK(c)		(1<<(((c)&255)%VEC_BITLEN))

static unsigned			log_set[VEC_LENGTH] = { 0, } ;

#define	LOG_TRACE_MSG(c)	log_set[VEC_MSGIDX(c)]|=VEC_MSGMSK(c)
#define	LOG_MSG_TRACED(m)	(0!=(log_set[VEC_MSGIDX(CAPIMSG_COMMAND(m))] \
					&VEC_MSGMSK(CAPIMSG_COMMAND(m))))

static void dump_message (unsigned char * m, const char * logo) {
	unsigned short	len;
	
	len = CAPIMSG_LEN(m);
	LOG(
		"CAPIMSG - L:%u A:%04x C:%02x S:%02x N:%04x\n",
		len,
		CAPIMSG_APPID(m),
		CAPIMSG_COMMAND(m),
		CAPIMSG_SUBCOMMAND(m),
		CAPIMSG_MSGID(m)
	);
#if defined (LOG_STACK_MSG_DUMP)
#if !defined (TOOLS_MEM_DUMP)
#error Function memdump() required!
#endif
	if (len > 8) {
		memdump (m + 8, len - 8, 8, logo);
	}
#endif
} /* dump_message */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void os__enter_critical (const char * f, int l) { 

	UNUSED_ARG(f); 
	UNUSED_ARG(l);
	enter_critical (); 
} /* os__enter_critical */

static __attr void os__leave_critical (const char * f, int l) {

	UNUSED_ARG(f); 
	UNUSED_ARG(l);
	leave_critical ();
} /* os__leave_critical */

static __attr void os_enter_critical (void) { 
	
	enter_critical (); 
} /* os_enter_critical */

static __attr void os_leave_critical (void) { 
	
	leave_critical (); 
} /* os_leave_critical */ 

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void os_enter_cache_sensitive_code (void) { /* NOP */ }

static __attr void os_leave_cache_sensitive_code (void) { /* NOP */ }

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void os_init (unsigned len, void (__attr2 * reg) (void *, unsigned),
                            		  void (__attr2 * rel) (void *), 
					  void (__attr2 * dwn) (void)) 
{
	init (len, reg, rel, dwn);
} /* os_init */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr char * os_params (void) {
#if defined (DRIVER_TYPE_DSL)
	static char	parmbuf[128];
	size_t		parmlen = 0;
	size_t		n;
	int		i	= 0;
	
	static struct {
	  char *	name;
	  short *	var;
	} 		X[] = {
		{ "ATMVCC",	&VCC },
		{ "ATMVPI",	&VPI },
		{ "ATMVCI",	&VCI },
		{ NULL,		NULL }
	} ;

#define	GUARD(n)	if ((parmlen + (n)) >= sizeof (parmbuf)) {	\
				LOG("Parameter buffer overflow!\n");	\
				return NULL;				\
			}
	
	NOTE("Using VCC/VPI/VCI = 0x%x/0x%x/0x%x\n", VCC, VPI, VCI);
	while (X[i].name != NULL) {
		GUARD(1);
		parmbuf[parmlen++] = ':';
		n = lib_strlen (X[i].name);
		GUARD(n + 1)
		lib_memcpy (&parmbuf[parmlen], X[i].name, n);
		parmlen += n;
		parmbuf[parmlen++] = (char) 0;
		GUARD (7);
		n = snprintf (&parmbuf[parmlen], 7, "\\x%04x", *X[i].var);
		assert (n == 6);
		parmlen += n;
		parmbuf[parmlen++] = (char) 0;
		++i;
	}
	GUARD (1);
	parmbuf[parmlen++] = (char) 0;
	
#undef GUARD

	return parmbuf;
#else
	return NULL;
#endif
} /* os_params */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr int os_get_message (unsigned char * msg) {
	int res;

	assert (msg != NULL);
	res = msg2stack (msg); 
#if defined (LOG_STACK_MSG)
	if ((res != 0) && LOG_MSG_TRACED(msg)) {
		dump_message (msg, "GET_MESSAGE");
	}
#endif
	return res;
} /* os_get_message */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void os_put_message (unsigned char * msg) {

	assert (msg != NULL);
#if defined (LOG_STACK_MSG)
	if (LOG_MSG_TRACED(msg)) {
		dump_message (msg, "PUT_MESSAGE");
	}
#endif
	msg2capi (msg);
} /* os_put_message */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr unsigned char * os_get_data_block (
	unsigned	appl, 
	unsigned long	ncci, 
	unsigned	index
) {
	char * res;

	res = data_block (appl, ncci, index);
	return res;
} /* os_get_data_block */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void os_free_data_block (unsigned appl, unsigned char * data) {

	UNUSED_ARG(appl); 
	UNUSED_ARG(data);
} /* os_free_data_block */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr int os_new_ncci (
	unsigned	appl,
	unsigned long	ncci, 
	unsigned	win_size,
	unsigned	blk_size
) {
	
	new_ncci (appl, ncci, win_size, blk_size); 
	return 1;
} /* os_new_ncci */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void os_free_ncci (unsigned appl, unsigned long ncci) {

	free_ncci (appl, ncci);
} /* os_free_ncci */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr unsigned os_block_size (unsigned appl) {
	unsigned bs, dummy;

	appl_profile (appl, &bs, &dummy);
	return bs;
} /* os_block_size */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr unsigned os_window_size (unsigned appl) {
	unsigned bc, dummy;

	appl_profile (appl, &dummy, &bc);
	return bc;
} /* os_window_size */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr unsigned os_card (void) {

	return 0;
} /* os_card */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void * os_appl_data (unsigned appl) {
	void * res;

	res = data_by_id (appl);
	return res;
} /* os_appl_data */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (DRIVER_TYPE_DSL_RAP)
static __attr unsigned os_appl_attr (unsigned appl) {
	unsigned res;

	res = attr_by_id (appl);
	return res;
} /* os_appl_attr */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr appldata_t * os_appl_1st_data (appldata_t * s) {
	int		num;
	void *		data;
	static char	e[10]; 

	lib_memset (&e, 0, 10);
	data = first_data (&num);
	s->num    = num;
	s->buffer = (NULL == data) ? e : data;
	return s;
} /* os_appl_1st_data */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr appldata_t * os_appl_next_data (appldata_t * s) {
	int		num;
	void *		data;
	static char	e[10]; 

	lib_memset (&e, 0, 10);
	if ((num = s->num) < 0) {	
		return NULL;
	}
	data = next_data (&num);
	s->num    = num;
	s->buffer = (NULL == data) ? e : data;
	return s;
} /* os_appl_next_data */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void * os_malloc (unsigned len) {
	void * res;

	res = hcalloc (len); 
	return res;
} /* os_malloc */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (DRIVER_TYPE_DSL) && !defined (DRIVER_TYPE_DSL_USB)
static __attr void * os_malloc2 (unsigned len) {
	void * res;

	res = hcalloc_kernel (len); 
	return res;
} /* os_malloc2 */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void os_free (void * p) {

	assert (p != NULL);
	hfree (p);
} /* os_free */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (DRIVER_TYPE_DSL_RAP) || defined (DRIVER_TYPE_DSL_USB)
static __attr void os_delay (unsigned msec) {

	assert (!in_interrupt ());
	info (msec > 9);
	msec = (msec > 9) ? (msec / 10) * TEN_MSECS : TEN_MSECS;
	wait_event_interruptible_timeout (delay, 0, msec);
} /* os_delay */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void update_j64 (void) {
	static int	run1 = 1;
	unsigned long	j;
	long long	diff;

	j = jiffies;
	if (run1) {
		j32 = j;
		run1 = 0;
	}
	if ((diff = j - j32) < 0) {
		diff = -diff;
	}
	assert (diff >= 0);
	j32 = j;
	j64 += diff;
} /* update_j64 */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr unsigned long long os_msec64 (void) {
	unsigned long	tmp;

	update_j64 ();
	tmp = j64 * JIFF2MSEC;
	return tmp;
} /* os_msec64 */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr unsigned long os_msec (void) {
	unsigned long	tmp;

	update_j64 ();
	tmp = ((unsigned long) j64) * JIFF2MSEC;
	return tmp;
} /* os_msec */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
typedef struct {

	unsigned long	lstart;
	unsigned long	start;
	unsigned long	tics;
	unsigned long	arg;
	timerfunc_t	func;
} timer_rec_t;

#if defined (DRIVER_TYPE_INTERN)

# define TIC_PER_SEC		250
# define TIC_PER_MSEC		4

# define MSEC			avm_time_base
# define START(x)		(((x)+TIC_PER_MSEC)/TIC_PER_MSEC)

#elif defined (DRIVER_TYPE_DSL) || defined (DRIVER_TYPE_USB)

# define MSEC			os_msec()
# define START(x)		((x)+1)

#endif

static volatile timer_rec_t *	timer = 0;
static unsigned			timer_count = 0;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr int os_timer_new (unsigned ntimers) {
	unsigned size;

	assert (ntimers > 0); 
	timer_count = ntimers;
	size = sizeof (timer_rec_t) * ntimers;
	timer = (timer_rec_t *) hcalloc (size);
	info (timer != NULL);
	if (NULL == timer) {
		timer_count = 0;
	} 
	return timer == NULL;
} /* os_timer_new */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void os_timer_delete (void) {
	
	hfree ((void *) timer);
	timer = NULL;
	timer_count = 0;
} /* os_timer_delete */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr int os_timer_start (
	unsigned	index,
	unsigned long	timeout,
	unsigned long	arg,
	timerfunc_t	func
) {
	assert (index < timer_count);
	if (index >= timer_count) {
		return 1;
	}
	enter_critical ();
	timer[index].start = MSEC;
	timer[index].tics  = START(timeout);
	timer[index].arg   = arg;
	timer[index].func  = func;
	leave_critical ();
	return 0;
} /* os_timer_start */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr int os_timer_stop (unsigned index) {

	assert (index < timer_count);
	if (index >= timer_count) {
		return 1;
	}
	enter_critical ();
	timer[index].func = NULL;
	leave_critical ();
	return 0;
} /* os_timer_stop */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void __attr os_timer_poll (void) {
	unsigned  	i;
	unsigned long	msec;
	restart_t 	flag;

	if (NULL == timer) {
		return;
	}
	enter_critical ();
	msec = MSEC;
	for (i = 0; i < timer_count; i++) {
		if (timer[i].func != 0) {
			if ((msec - timer[i].start) >= timer[i].tics) {
				leave_critical ();
				assert (timer[i].func != NULL);
				flag = (*timer[i].func) (timer[i].arg);
				enter_critical ();
				if (timer_restart == flag) {
					timer[i].start = MSEC;
				} else {
					timer[i].func = 0;
				}
			}
		}
	}
	leave_critical ();
} /* os_timer_poll */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (DRIVER_TYPE_DSL)
static __attr int os_gettimeofday (struct timeval * tv) {

	if (NULL != tv) {
		do_gettimeofday (tv);
	}
	return 0;
} /* os_gettimeofday */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static int	nl_needed = 0;

static __attr void os_printf (char * s, va_list args) {
#if !defined (NDEBUG)
	char	buffer[PRINTF_BUFFER_SIZE];
	char *	bufptr = buffer;
	int	count;

	if (nl_needed) {
		nl_needed = 0;
		printk ("\n");
	}	
	count = vsnprintf (bufptr, sizeof (buffer), s, args);
	if ('\n' == buffer[0]) {
		bufptr++;
	}
	if ('\n' != buffer[count - 1]) {
		assert (count < (int) (sizeof (buffer) - 2));
		buffer[count++] = '\n';
		buffer[count]   = (char) 0;
	}
	NOTE(bufptr);
#else
	s = s;
	args = args;
#endif
} /* os_printf */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void os_puts (char * str) { 

	NOTE(str);
} /* os_puts */
 
static __attr void os_putl (long l) { 

	nl_needed = 1; 
	NOTE("%ld", l); 
}  /* os_putl */

static __attr void os_puti (int i) { 

	nl_needed = 1; 
	NOTE("%d", i); 
} /* os_puti */

static __attr void os_putnl (void) { 

	nl_needed = 0; 
	NOTE("\n"); 
}  /* os_putnl */

static __attr void os_putc (char c) {
	char buffer[10];
    
	nl_needed = 1;
	if ((31 < c) && (c < 127)) {
	        snprintf (buffer, 10, "'%c' (0x%02x)", c, (unsigned char) c);
	} else {
		snprintf (buffer, 10, "0x%02x", (unsigned char) c);
	}
	NOTE("%s", buffer);
} /* os_putc */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (DRIVER_TYPE_DSL_TM) || defined (DRIVER_TYPE_DSL_USB)

static __attr void os_debug_printf (char * fmt, ...) {
	va_list	args;
	char	buffer [PRINTF_BUFFER_SIZE];

	va_start (args, fmt);
	vsnprintf (buffer, sizeof (buffer), fmt, args);
	printk (KERN_INFO TARGET ": %s", buffer);
	va_end (args);
} /* os_debug_printf */

#elif defined (DRIVER_TYPE_DSL_RAP)

static __attr void os_debug_printf (char * fmt, va_list args) {
	char	buffer [PRINTF_BUFFER_SIZE];

	vsnprintf (buffer, sizeof (buffer), fmt, args);
	printk (KERN_INFO TARGET ": %s", buffer);
} /* os_debug_printf */

#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if !defined (DRIVER_TYPE_DSL)
void __attr printl (char * fmt, ...) {
	
	/* FIXME */
	
	va_list	args;
	char	buffer [PRINTF_BUFFER_SIZE];

	va_start (args, fmt);
	vsnprintf (buffer, sizeof (buffer), fmt, args);
	printk ("%s", buffer);
	va_end (args);
} /* printl */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static lib_callback_t *	lib	= NULL;
static lib_interface_t	libif	= {

	.init =				&os_init,
	.params =			&os_params,
	.get_message =			&os_get_message,
	.put_message =			&os_put_message,
	.get_data_block =		&os_get_data_block,
	.free_data_block =		&os_free_data_block,
	.new_ncci =			&os_new_ncci,
	.free_ncci =			&os_free_ncci,
	.block_size =			&os_block_size,
	.window_size =			&os_window_size,
	.card =				&os_card,
	.appl_data =			&os_appl_data,
#if defined (DRIVER_TYPE_DSL_RAP)
	.appl_attr =			&os_appl_attr,
#endif
	.appl_1st_data =		&os_appl_1st_data,
	.appl_next_data =		&os_appl_next_data,
	.malloc =			&os_malloc,
	.free =				&os_free,
#if defined (DRIVER_TYPE_DSL) && !defined (DRIVER_TYPE_DSL_USB)
	.malloc2 =			&os_malloc2,
#endif
#if defined (DRIVER_TYPE_DSL_RAP) || defined (DRIVER_TYPE_DSL_USB)
	.delay =			&os_delay,
#endif
	.msec =				&os_msec,	
	.msec64 =			&os_msec64,
	.timer_new =			&os_timer_new,
	.timer_delete =			&os_timer_delete,
	.timer_start =			&os_timer_start,
	.timer_stop =			&os_timer_stop,
	.timer_poll =			&os_timer_poll,
#if defined (DRIVER_TYPE_DSL)
	.get_time =			&os_gettimeofday,
#endif
#if defined (DRIVER_TYPE_DSL_TM) || defined (DRIVER_TYPE_DSL_USB)
	.dprintf =			&os_debug_printf,
#endif
#if defined (DRIVER_TYPE_DSL_RAP)
	.printf =			&os_debug_printf,
	.putf =				&os_printf,
#else
	.printf =			&os_printf,
#endif
	.puts =				&os_puts,
	.putl =				&os_putl,
	.puti =				&os_puti,
	.putc =				&os_putc,
	.putnl =			&os_putnl,
	._enter_critical =		&os__enter_critical,
	._leave_critical =		&os__leave_critical,
	.enter_critical =		&os_enter_critical,
	.leave_critical =		&os_leave_critical,
	.enter_cache_sensitive_code =	&os_enter_cache_sensitive_code,	
	.leave_cache_sensitive_code =	&os_leave_cache_sensitive_code,

#if defined (DRIVER_TYPE_DSL_RAP)
	.xfer_req =			&dif_xfer_requirements,
#endif

	.name =				TARGET,
	.udata =			0,
	.pdata =			NULL
} ;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
lib_callback_t * get_library (void) {

	return lib;
} /* get_library */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
lib_callback_t * link_library (void * context) {

#if defined (LOG_STACK_MSG)
	LOG_TRACE_MSG(CAPI_DATA_B3);
#endif
	LOG("Interface exchange... (%d)\n", sizeof (lib_interface_t));
#if defined (DRIVER_TYPE_DSL)
	return (lib = avm_lib_attach (&libif, context));
#else
	return (lib = avm_lib_attach (&libif));
#endif
} /* link_library */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void free_library (void) {

	if (lib != NULL) {
		lib = NULL;
		avm_lib_detach (&libif);
	}
} /* free_library */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/

