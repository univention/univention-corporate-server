/* 
 * driver.c
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

#include <asm/io.h>
#include <asm/irq.h>
#include <asm/atomic.h>
#include <asm/system.h>
#include <linux/version.h>
#include <linux/ioport.h>
#include <linux/sched.h>
#include <linux/interrupt.h>
#include <linux/spinlock.h>
#include <linux/netdevice.h>
#include <linux/skbuff.h>
#include <linux/kernel.h>
#include <linux/smp.h>
#include <linux/ctype.h>
#include <linux/string.h>
#include <linux/list.h>
#include <linux/capi.h>
#include <linux/isdn/capilli.h>
#include <linux/isdn/capiutil.h>
#include <linux/isdn/capicmd.h>
#include <stdarg.h>
#include "main.h"
#include "tables.h"
#include "queue.h"
#include "tools.h"
#include "defs.h"
#include "lib.h"
#include "driver.h"

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcclassic__) 
# define	IO_RANGE		32
#elif defined (__fcpcmcia__)
# define	CARD_ID			1
# define	ID_OFFSET		6
# define	IO_RANGE		8
#elif defined (__fcpnp__)
# include <linux/pnp.h>

# define	AVM_VENDOR_ID		ISAPNP_VENDOR('A','V','M')
# define	AVM_DEVICE_ID		ISAPNP_DEVICE(0x0900)
# define	PNP_NO_CARD		2
# define	PNP_ERROR		1
# define	PNP_OK			0
# define	CARD_ID			9
# define	ID_OFFSET		0
# define	IO_RANGE		32
#elif defined (__fcpci__)
# include <linux/pci.h>

# define	AVM_VENDOR_ID		0x1244
# define	AVM_DEVICE_ID		0x0A00
# define	AVM_DEVICE_ID2		0x0E00
# define	PCI_NO_RESOURCE		4
# define	PCI_NO_PCI_KERN		3
# define	PCI_NO_CARD		2
# define	PCI_NO_PCI		1
# define	PCI_OK			0
# define	CARD_ID			10
# define	CARD_ID2		14
# define	ID_OFFSET		0
# define	IO_RANGE		32
#else
# error You must define a card identifier...
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
card_t *			capi_card		= NULL;
lib_callback_t *		capi_lib		= NULL;
struct capi_ctr *		capi_controller		= NULL;

static atomic_t			timer_irq_enabled	= ATOMIC_INIT (0);
static atomic_t			dont_sched		= ATOMIC_INIT (1);
static atomic_t			crit_level		= ATOMIC_INIT (0);
static unsigned long		crit_flags;
static atomic_t			scheduler_enabled	= ATOMIC_INIT (0);
static atomic_t			scheduler_id		= ATOMIC_INIT (-1);
static spinlock_t		sched_lock		= SPIN_LOCK_UNLOCKED;
#if !defined (__fcclassic__)
static int			card_id			= 0;
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void scheduler (unsigned long data);
static irqreturn_t irq_handler (int irq, void * args);

static DECLARE_TASKLET_DISABLED (scheduler_tasklet, scheduler, 0);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static __attr void scheduler_control (unsigned);

static functions_t	cafuncs = {
	
	1,	/* 7 */
	scheduler_control,
#if 0
	wakeup_control,
	version_callback,
	scheduler_suspend,
	scheduler_resume,
	controller_remove,
	controller_add
#else
	NULL,
#endif
} ;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__LP64__)
#define _CAPIMSG_U64(m, off)	\
	((u64)m[off]|((u64)m[(off)+1]<<8)|((u64)m[(off)+2]<<16)|((u64)m[(off)+3]<<24) \
	|((u64)m[(off)+4]<<32)|((u64)m[(off)+5]<<40)|((u64)m[(off)+6]<<48)|((u64)m[(off)+7]<<56))

static void _capimsg_setu64(void *m, int off, __u64 val)
{
	((__u8 *)m)[off] = val & 0xff;
	((__u8 *)m)[off+1] = (val >> 8) & 0xff;
	((__u8 *)m)[off+2] = (val >> 16) & 0xff;
	((__u8 *)m)[off+3] = (val >> 24) & 0xff;
	((__u8 *)m)[off+4] = (val >> 32) & 0xff;
	((__u8 *)m)[off+5] = (val >> 40) & 0xff;
	((__u8 *)m)[off+6] = (val >> 48) & 0xff;
	((__u8 *)m)[off+7] = (val >> 56) & 0xff;
}
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void scan_version (card_t * card, const char * ver) {
	int	vlen, i;
	char *	vstr;

	assert (ver != NULL);
	vlen = (unsigned char) ver[0];
	card->version = vstr = (char *) hmalloc (vlen);
	if (NULL == card->version) {
		LOG("Could not allocate version buffer.\n");
		return;
	}
	lib_memcpy (card->version, ver + 1, vlen);
	i = 0;
	for (i = 0; i < 8; i++) {
		card->string[i] = vstr + 1;
		vstr += 1 + *vstr;
	} 
#ifdef NDEBUG
	NOTE("Stack version %s\n", card->string[0]);
#endif
	LOG("Library version:    %s\n", card->string[0]);
	LOG("Card type:          %s\n", card->string[1]);
	LOG("Capabilities:       %s\n", card->string[4]);
	LOG("D-channel protocol: %s\n", card->string[5]);
} /* scan_version */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void copy_version (struct capi_ctr * ctrl) {
	char *		tmp;
	card_t *	card;

	assert (ctrl != NULL);
	card = (card_t *) ctrl->driverdata;
	assert (card != NULL);
	if (NULL == (tmp = card->string[3])) {
		ERROR("Do not have version information...\n");
		return;
	}
	lib_strncpy (ctrl->serial, tmp, CAPI_SERIAL_LEN);
	lib_memcpy (&ctrl->profile, card->string[6], sizeof (capi_profile));
	strncpy (ctrl->manu, "AVM GmbH", CAPI_MANUFACTURER_LEN);
	ctrl->version.majorversion = 2;
	ctrl->version.minorversion = 0;
	tmp = card->string[0];
	ctrl->version.majormanuversion = (((tmp[0] - '0') & 15) << 4)
					+ ((tmp[2] - '0') & 15);
	ctrl->version.minormanuversion = ((tmp[3] - '0') << 4)
					+ (tmp[5] - '0') * 10
					+ ((tmp[6] - '0') & 15);
} /* copy_version */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void kill_version (card_t * card) {
	int	i;

	for (i = 0; i < 8; i++) {
		card->string[i] = NULL;
	}
	if (card->version != NULL) {
		hfree (card->version);
		card->version = NULL;
	}
} /* kill_version */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void pprintf (char * page, int * len, const char * fmt, ...) {
	va_list args;

	va_start (args, fmt);
	*len += vsprintf (page + *len, fmt, args);
	va_end (args);
} /* pprintf */

/*---------------------------------------------------------------------------*\
\*-C-------------------------------------------------------------------------*/
static inline int in_critical (void) {
	
	return (atomic_read (&crit_level) > 0);
} /* in_critical */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void enter_critical (void) {
	unsigned long	flags;
	
	if (!atomic_read (&crit_level)) {
		local_irq_save (flags);
		crit_flags = flags;
	}
	atomic_inc (&crit_level);
} /* enter_critical */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void leave_critical (void) {
	unsigned long	flags;
	
	assert (in_critical ());
	atomic_dec (&crit_level);
	if (!atomic_read (&crit_level)) {
		flags = crit_flags;
		local_irq_restore (flags);
	}
} /* leave_critical */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static inline void enable_scheduler (void) {

	LOG("Enabling scheduler...\n");
	tasklet_enable (&scheduler_tasklet);
	atomic_set (&scheduler_enabled, 1);
} /* enable_scheduler */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static inline void disable_scheduler (void) {

	LOG("Disabling scheduler...\n");
	atomic_set (&scheduler_enabled, 0);
	tasklet_disable (&scheduler_tasklet);
} /* disable_scheduler */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void kick_scheduler (void) {

	assert (atomic_read (&scheduler_enabled));
	if (atomic_dec_and_test (&dont_sched)) {
		tasklet_schedule (&scheduler_tasklet);
	} else {
		atomic_set (&dont_sched, 0);
	}
} /* kick_scheduler */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static int params_ok (card_t * card) {
	int  chk;

	assert (card != NULL);
	if (0 == card->irq) {
		ERROR(
			"IRQ not assigned by BIOS. Please check BIOS"
			"settings/manual for a proper PnP/PCI-Support.\n"
		);
		return FALSE;
	}
	if (0 == card->base) {
		ERROR("Base address has not been set.\n");
		return FALSE;
	}
#if defined (__fcclassic__)
	switch (card->base) {

	case 0x200: case 0x240: case 0x300: case 0x340:
		LOG("Base address valid.\n");
		break;
	default:
		LOG("Invalid base address.\n");
		return FALSE;
	}
#endif
	assert (capi_lib != NULL);
	assert (capi_lib->check_controller != NULL);
	if (!(chk = (*capi_lib->check_controller) (card->base, &card->info))) {
		return TRUE;
	} else {
		LOG("Controller check failed.\n");
		return FALSE;
	}
} /* params_ok */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/ 
static int install_card (card_t * card) {
	int			result	= 4711;
#if !defined (__fcpcmcia__)
	struct resource *	rsc	= NULL;
	
	assert (card != NULL);
	if (NULL == (rsc = request_region (card->base, IO_RANGE, TARGET))) {
		LOG(
			"I/O range 0x%04x-0x%04x not available!\n",
			card->base, 
			card->base + IO_RANGE - 1
		);
		return FALSE;
	} else {
		LOG(
			"I/O range 0x%04x-0x%04x assigned to " TARGET " driver.\n",
			card->base, 
			card->base + IO_RANGE - 1
		);
	}
#else
	assert (card != NULL);
#endif
#if !defined (__fcclassic__) 
	card_id = inb (card->base + ID_OFFSET);
#if defined (__fcpci__)
	if ((CARD_ID != card_id) && (CARD_ID2 != card_id)) 
#else
	if (CARD_ID != card_id) 
#endif
	{
		release_region (card->base, IO_RANGE);
		ERROR("Card identification test failed.\n");
		return FALSE;
	}
#endif
	card->data = (unsigned) &irq_handler;
	tasklet_init (&scheduler_tasklet, scheduler, 0);
	disable_scheduler ();
	result = request_irq (
			card->irq, 
			&irq_handler, 
#if defined (__fcpci__) || defined (__fcpcmcia__)
#if (LINUX_VERSION_CODE < KERNEL_VERSION(2,6,24))
			SA_INTERRUPT | SA_SHIRQ, 
#else
			IRQF_DISABLED | IRQF_SHARED,
#endif
#else
#if (LINUX_VERSION_CODE < KERNEL_VERSION(2,6,24))
			SA_INTERRUPT, 
#else
			IRQF_DISABLED,
#endif
#endif
			TARGET, 
			card
			);
	if (result) {
		release_region (card->base, IO_RANGE);
		ERROR("Could not install irq handler.\n");
		return FALSE;
	} else {
		LOG("IRQ #%d assigned to " TARGET " driver.\n", card->irq);
	}
	return TRUE;
} /* install_card */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void remove_card (card_t * card) {

	LOG("Releasing IRQ #%d...\n", card->irq);
	free_irq (card->irq, card);
	card->irq = 0;
	LOG(
		"Releasing I/O range 0x%04x-0x%04x...\n", 
		card->base, 
		card->base + IO_RANGE - 1
	);
#if !defined (__fcpcmcia__)
	release_region (card->base, IO_RANGE);
#endif
} /* remove_card */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static int start (card_t * card) {
	unsigned long	flags;
	char *		version;

	card->count = 0;
	table_init (&card->appls);
	queue_init (&card->queue);
	(*capi_lib->cm_register_ca_functions) (&cafuncs);
	(*capi_lib->cm_start) ();
	version = (*capi_lib->cm_init) (card->base, card->irq);
	scan_version (card, version);
	if (!install_card (card)) {
		(*capi_lib->cm_exit) ();
		return FALSE;
	}
	local_irq_save (flags);
	if ((*capi_lib->cm_activate) ()) {
		local_irq_restore (flags);
		LOG("Activate failed.\n");
		remove_card (card);
		return FALSE;
	}
	(*capi_lib->cm_handle_events) ();
	local_irq_restore (flags);
	enable_scheduler ();
	kick_scheduler ();
	return (card->running = TRUE); 
} /* start */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void stop (card_t * card) {

	disable_scheduler ();
	LOG("Killing scheduler...\n");
	tasklet_kill (&scheduler_tasklet);
#if defined (__fcpcmcia__) 
	if (card->running) (*capi_lib->cm_exit) ();
#else
	(*capi_lib->cm_exit) ();
#endif
	card->running = FALSE;
	remove_card (card);
	queue_exit (&card->queue);
	table_exit (&card->appls);
	kill_version (card);
} /* stop */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static int __kcapi load_ware (struct capi_ctr * ctrl, capiloaddata * ware) {

	UNUSED_ARG (ctrl);
	UNUSED_ARG (ware);
	ERROR("No firmware required!\n");
	return -EIO;
} /* load_ware */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static char * __kcapi proc_info (struct capi_ctr * ctrl) {
	card_t *	card;
	static char	text[80];

	assert (ctrl != NULL);
	card = (card_t *) ctrl->driverdata;
	assert (card != NULL);
	snprintf (
		text, 
		sizeof (text),
		"%s %s 0x%04x %u",
		card->version ? card->string[1] : "A1",
		card->version ? card->string[0] : "-",
		card->base, card->irq
	);
	return text;
} /* proc_info */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static int __kcapi ctr_info (
	char *			page, 
	char **			start, 
	off_t			ofs,
	int			count, 
	int *			eof,
	struct capi_ctr *	ctrl
) {
	card_t *		card;
	char *			temp;
	unsigned char		flag;
	int			len = 0;

	assert (ctrl != NULL);
	card = (card_t *) ctrl->driverdata;
	assert (card != NULL);
	pprintf (page, &len, "%-16s %s\n", "name", SHORT_LOGO);
	pprintf (page, &len, "%-16s 0x%04x\n", "io", card->base);
	pprintf (page, &len, "%-16s %d\n", "irq", card->irq);
	temp = card->version ? card->string[1] : "A1";
	pprintf (page, &len, "%-16s %s\n", "type", temp);
	temp = card->version ? card->string[0] : "-";
#if defined (__fcclassic__) || defined (__fcpcmcia__)
	pprintf (page, &len, "%-16s 0x%04x\n", "revision", card->info);
#elif defined (__fcpci__)
	pprintf (page, &len, "%-16s %d\n", "class", card_id);
#endif
	pprintf (page, &len, "%-16s %s\n", "ver_driver", temp);
	pprintf (page, &len, "%-16s %s\n", "ver_cardtype", SHORT_LOGO);

	flag = ((unsigned char *) (ctrl->profile.manu))[3];
	if (flag) {
		pprintf(page, &len, "%-16s%s%s%s%s%s%s%s\n", "protocol",
			(flag & 0x01) ? " DSS1" : "",
			(flag & 0x02) ? " CT1" : "",
			(flag & 0x04) ? " VN3" : "",
			(flag & 0x08) ? " NI1" : "",
			(flag & 0x10) ? " AUSTEL" : "",
			(flag & 0x20) ? " ESS" : "",
			(flag & 0x40) ? " 1TR6" : ""
		);
	}
	flag = ((unsigned char *) (ctrl->profile.manu))[5];
	if (flag) {
		pprintf(page, &len, "%-16s%s%s%s%s\n", "linetype",
			(flag & 0x01) ? " point to point" : "",
			(flag & 0x02) ? " point to multipoint" : "",
			(flag & 0x08) ? " leased line without D-channel" : "",
			(flag & 0x04) ? " leased line with D-channel" : ""
		);
	}
	if (len < ofs) {
		return 0;
	}
	*eof = 1;
	*start = page - ofs;
	return ((count < len - ofs) ? count : len - ofs);
} /* ctr_info */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void __kcapi reset_ctrl (struct capi_ctr * ctrl) {
	card_t *	card;
	appl_t *	appp;

	assert (ctrl != NULL);
	card = (card_t *) ctrl->driverdata;
	if (0 != card->count) {
		NOTE( "Removing registered applications!\n");
		info (card->appls);
		if (card->appls != NULL) {
			appp = first_appl (card->appls);
			while (appp != NULL) {
				free_ncci (appp->id, (unsigned) -1);
				appp = next_appl (card->appls, appp);
			}
		}
	}
	stop (card);
	capi_ctr_reseted (ctrl);
#if defined (__fcpnp__)
	pnp_disable_dev (card->dev);
#endif
} /* reset_ctrl */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int __kcapi add_card (struct capi_driver * drv, capicardparams * args) {
	card_t *		card;
	struct capi_ctr *	ctrl;
	char *			msg;
	int			res = 0;
	
	UNUSED_ARG(drv);
	if (NULL != capi_controller) {
		ERROR("Cannot handle two controllers!\n");
 		return -EBUSY;
	}
	if (NULL == (capi_card = card = (card_t *) hcalloc (sizeof (card_t)))) {
		ERROR("Card object allocation failed.\n");
		return -EIO;
	}
	card->base = args->port;
	card->irq = args->irq;

	capi_controller = ctrl = &card->ctrl;
	ctrl->driver_name = TARGET;
	ctrl->driverdata = (void *) card;
	ctrl->owner = THIS_MODULE;
	snprintf (ctrl->name, 32, "%s-%04x-%02u", TARGET, card->base, card->irq);

	if (!params_ok (card)) {
		msg = "Invalid parameters!";
		res = -EINVAL;
	msg_exit:
		ERROR("Error: %s\n", msg);
		hfree (card);
		capi_card = NULL;
		return res;
	}

	inc_use_count ();
	if (!start (card)) {
		dec_use_count ();
		msg = "Initialization failed.";
		res = -EIO;
		goto msg_exit;
	}
	copy_version (capi_controller);

	ctrl->load_firmware =	load_ware;
	ctrl->reset_ctr =	reset_ctrl;
	ctrl->register_appl =	register_appl;
	ctrl->release_appl =	release_appl;
	ctrl->send_message =	send_msg;
	ctrl->procinfo =	proc_info;
	ctrl->ctr_read_proc =	ctr_info;
	if (0 != (res = attach_capi_ctr (ctrl))) {
		dec_use_count ();
		stop (card);
		msg = "Could not attach controller.";
		res = -EBUSY;
		goto msg_exit;
	}
	capi_ctr_ready (ctrl);
	return 0;
} /* add_card */ 

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void __kcapi remove_ctrl (struct capi_ctr * ctrl) {
	card_t *	card;
	
	assert (ctrl != NULL);
	card = (card_t *) ctrl->driverdata;
	assert (card != NULL);
	assert (ctrl == &card->ctrl);

	info (!card->running);
	if (card->running) {
		LOG("Remove without reset!\n");
		reset_ctrl (ctrl);
	}
	assert (card->irq == 0);
	LOG("Detaching controller...\n");
	detach_capi_ctr (ctrl);
	dec_use_count ();
	ctrl->driverdata = NULL;
#if defined (__fcpnp__)
	pnp_device_detach (card->dev);
#endif
	hfree (card);
	capi_card = NULL;
} /* remove_ctrl */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int nbchans (struct capi_ctr * ctrl) {
	card_t *	card;
	unsigned char *	prf;
	int		temp = 2;
    
	assert (ctrl != NULL);
	card = (card_t *) ctrl->driverdata;
	prf = (unsigned char *) card->string[6];
	if (prf != NULL) {
		temp = prf[2] + 256 * prf[3];
	}
	return temp;
} /* nbchans */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int msg2stack (unsigned char * msg) {
	unsigned		mlen, appl, hand;
	__u32			ncci;
	unsigned char *		mptr;
	struct sk_buff *	skb;

	assert (capi_card != NULL);
	assert (msg != NULL);
	if (NULL != (skb = queue_get (capi_card->queue))) {
		mptr = (unsigned char *) skb->data;
		mlen = CAPIMSG_LEN(mptr); 
		appl = CAPIMSG_APPID(mptr);

		MLOG(
			"PUT_MESSAGE(appl:%u,cmd:%X,subcmd:%X)\n", 
			appl, 
			CAPIMSG_COMMAND(mptr), 
			CAPIMSG_SUBCOMMAND(mptr)
		);

		if (CAPIMSG_CMD(mptr) == CAPI_DATA_B3_REQ) {
			hand = CAPIMSG_U16(mptr, 18);
			ncci = CAPIMSG_NCCI(mptr);
#ifdef __LP64__
			if (mlen < 30) {
				_capimsg_setu64(msg, 22, (__u64)(mptr + mlen));
				capimsg_setu16(mptr, 0, 30);
			}
			else {
				_capimsg_setu64(mptr, 22, (__u64)(mptr + mlen));
			}
#else
			capimsg_setu32(mptr, 12, (__u32)(mptr + mlen));
#endif
			lib_memcpy (msg, mptr, mlen);
			queue_park (capi_card->queue, skb, appl, ncci, hand);
		} else {
			lib_memcpy (msg, mptr, mlen);
			assert (skb->list == NULL);
			dev_kfree_skb_any (skb);
		}
	}
	return (skb != NULL);
} /* msg2stack */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void msg2capi (unsigned char * msg) {
	unsigned		mlen, appl, dlen;
#ifndef __LP64__
	__u32			dummy;
#endif
	unsigned char *		dptr;
	struct sk_buff *	skb;

	assert (capi_card != NULL);
	assert (msg != NULL);
	mlen = CAPIMSG_LEN(msg);
	appl = CAPIMSG_APPID(msg);

	MLOG(
		"GET_MESSAGE(appl:%u,cmd:%X,subcmd:%X)\n", 
		appl, 
		CAPIMSG_COMMAND(msg), 
		CAPIMSG_SUBCOMMAND(msg)
	);

	if (CAPIMSG_CMD(msg) == CAPI_DATA_B3_CONF) {
		handle_data_conf (capi_card->appls, capi_card->queue, msg);
	}
	if (!appl_alive (capi_card->appls, appl)) {
		LOG("Message to dying appl #%u!\n", appl);
		return;
	}
	if (CAPIMSG_CMD(msg) == CAPI_DATA_B3_IND) {
		dlen = CAPIMSG_DATALEN(msg);
		skb = alloc_skb (
			mlen + dlen + ((mlen < 30) ? (30 - mlen) : 0), 
			GFP_ATOMIC
		); 
		if (NULL == skb) {
			ERROR("Unable to allocate skb. Message lost.\n");
			return;
		}
		/* Messages are expected to come with 32 bit data pointers. 
		 * The kernel CAPI works with extended (64 bit ready) message 
		 * formats so that the incoming message needs to be fixed, 
		 * i.e. the length gets adjusted and the required 64 bit data 
		 * pointer is added.
		 */
#ifdef __LP64__
		dptr = (unsigned char *) _CAPIMSG_U64(msg, 22);
		lib_memcpy (skb_put (skb, mlen), msg, mlen);
#else
		dptr = (unsigned char *) CAPIMSG_U32(msg, 12);
		if (mlen < 30) {
			msg[0] = 30;
			dummy  = 0;	
			lib_memcpy (skb_put (skb, mlen), msg, mlen);
			lib_memcpy (skb_put (skb, 4), &dummy, 4);	
			lib_memcpy (skb_put (skb, 4), &dummy, 4);
		} else {
			lib_memcpy (skb_put (skb, mlen), msg, mlen);
		}
#endif
		lib_memcpy (skb_put (skb, dlen), dptr, dlen); 
	} else {
		if (NULL == (skb = alloc_skb (mlen, GFP_ATOMIC))) {
			ERROR("Unable to allocate skb. Message lost.\n");
			return;
		}
		lib_memcpy (skb_put (skb, mlen), msg, mlen);
	}
	assert (capi_controller != NULL);
	capi_ctr_handle_message (capi_controller, appl, skb);
} /* msg2capi */

/*---------------------------------------------------------------------------*\
\*-S-------------------------------------------------------------------------*/ 
static __attr void __stack scheduler_control (unsigned ena) {
	int	enabled = (int) ena;
	int	changed;

	enter_critical ();
	changed = (atomic_read (&timer_irq_enabled) != enabled);
	if (changed) {
		atomic_set (&timer_irq_enabled, enabled);
		(*capi_lib->cm_timer_irq_control) (enabled);
	}
	leave_critical ();
} /* scheduler_control */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void scheduler (unsigned long data) {
	
	UNUSED_ARG (data);
	atomic_set (&scheduler_id, smp_processor_id ());
	if (spin_trylock (&sched_lock)) {
		while (!atomic_read (&dont_sched)) {
			atomic_set (&dont_sched, 1);
			os_timer_poll ();
			if ((*capi_lib->cm_schedule) ()) {
				scheduler_control (TRUE); 
			}
		}
		spin_unlock (&sched_lock);
	}
	atomic_set (&scheduler_id, -1);
} /* scheduler */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static irqreturn_t irq_handler (int irq, void * args) {
	int	res	= IRQ_NONE;
	
	UNUSED_ARG (irq);
	if (args != NULL) {
		assert (capi_lib->cm_handle_events != NULL);
		if (atomic_read (&scheduler_id) == smp_processor_id ()) {
			res = IRQ_RETVAL ((*capi_lib->cm_handle_events) ());
		} else {
			spin_lock (&sched_lock);
			res = IRQ_RETVAL ((*capi_lib->cm_handle_events) ());
			spin_unlock (&sched_lock);
		}
		if (res == IRQ_HANDLED) {			
			atomic_set (&dont_sched, 0);
			if (atomic_read (&scheduler_enabled)) {
				tasklet_schedule (&scheduler_tasklet);
			}
		}
	}
	return res;
} /* irq_handler */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void __stack init (unsigned len, void (__attr2 * reg) (void *, unsigned),
                        	 void (__attr2 * rel) (void *), 
				 void (__attr2 * dwn) (void)) {

	assert (reg != NULL);
	assert (rel != NULL);
	assert (dwn != NULL);

	capi_card->length   = len;
	capi_card->reg_func = reg;
	capi_card->rel_func = rel;
	capi_card->dwn_func = dwn;
} /* init */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcpcmcia__)
int fcpcmcia_addcard (unsigned int port, unsigned irq) {
	capicardparams args;

	NOTE("CS addcard: io %x, irq %u\n", port, irq);
	args.port = port;
	args.irq  = irq;
	return add_card (&fritz_capi_driver, &args);
} /* fcpcmcia_addcard */

int fcpcmcia_delcard (unsigned int port, unsigned irq) {

	NOTE("CS delcard: io %x, irq %u\n", port, irq);
	if (NULL != capi_controller) { 
		reset_ctrl (capi_controller);
		remove_ctrl (capi_controller);
	}
	return 0; 
} /* fcpcmcia_delcard */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
int fritz_driver_init (void) {

	return (NULL != (capi_lib = link_library (NULL)));
} /* fritz_driver_init */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void driver_exit (void) {

	assert (capi_lib != NULL);
	free_library ();
	capi_lib = NULL;
} /* driver_exit */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/

