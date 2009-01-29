/* 
 * fcpcmcia_cs.c based on...
 */

/* $Id: avm_cs.c,v 1.4.6.3 2001/09/23 22:24:33 kai Exp $
 *
 * A PCMCIA client driver for AVM B1/M1/M2
 *
 * Copyright 1999 by Carsten Paeth <calle@calle.de>
 *
 * This software may be used and distributed according to the terms
 * of the GNU General Public License, incorporated herein by reference.
 *
 */

#include <linux/module.h>
#include <linux/moduleparam.h>
#include <linux/kernel.h>
#include <linux/sched.h>
#include <linux/ptrace.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/tty.h>
#include <linux/serial.h>
#include <linux/major.h>
#include <asm/io.h>
#include <asm/system.h>

#include <pcmcia/version.h>
#include <pcmcia/cs_types.h>
#include <pcmcia/cs.h>
#include <pcmcia/cistpl.h>
#include <pcmcia/ciscode.h>
#include <pcmcia/ds.h>
#include <pcmcia/cisreg.h>

#include <linux/skbuff.h>
#include <linux/capi.h>
#include <linux/b1lli.h>
#include <linux/b1pcmcia.h>

#include <stdarg.h>

#include <linux/version.h>

#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,10)
#define PCMCIA_IRQ_INFO2
#endif

/*====================================================================*/
MODULE_LICENSE("GPL");

/*====================================================================*/
#define	MODNAME		"fcpcmcia_cs"

#if !defined (NDEBUG)
# define assert(x)      (!(x)?cs_msg(1,"%s(%d): assert (%s) failed\n",__FILE__,__LINE__,#x):((void)0))
# define info(x)        (!(x)?cs_msg(1,"%s(%d): info (%s) failed\n",__FILE__,__LINE__,#x):((void)0))
# define LOG(f,x...)    cs_msg(0,f,##x)
#else
# define assert(x)
# define info(x)
# define LOG(f,x...)
#endif

#define ERROR(f,x...)   cs_msg(1,f,##x)
#define NOTE(f,x...)    cs_msg(0,f,##x)

static void cs_msg(int error, const char * f, ...) 
{
    va_list args;
    char sbuf[128];

    va_start(args,f);
    vsnprintf(sbuf,sizeof(sbuf),f,args);
    va_end(args);
    printk("%s%s%s: %s",(error?KERN_ERR:KERN_INFO),MODNAME,(error?" ERROR":""),sbuf);
} /* msg */

/*====================================================================*/

#if defined (PCMCIA_IRQ_INFO2)
/* Parameters that can be set with 'insmod' */

/* This means pick from 15, 12, 11, 10, 9, 7, 5, 4, and 3 */
static int default_irq_list[10] = { 15, 12, 11, 10, 9, 7, 5, 4, 3, -1 };
static int irq_list_count       = -1;
static int irq_list[10];

module_param_array (irq_list, int, irq_list_count, 0);

MODULE_PARM_DESC (irq_list, "List of IRQ numbers");
#endif

/*====================================================================*/

/*
   Entry points into the card driver.
*/

extern int fcpcmcia_addcard (unsigned int, unsigned);
extern int fcpcmcia_delcard (unsigned int, unsigned);

/*
   The event() function is this driver's Card Services event handler.
   It will be called by Card Services when an appropriate card status
   event is received.  The config() and release() entry points are
   used to configure or release a socket, in response to card insertion
   and ejection events.  They are invoked from the skeleton event
   handler.
*/

static void cs_config(dev_link_t *);
static void cs_release(dev_link_t *);
static int cs_event(event_t event, int priority, event_callback_args_t *);

/*
   The attach() and detach() entry points are used to create and destroy
   "instances" of the driver, where each instance represents everything
   needed to manage one actual PCMCIA card.
*/

static dev_link_t * cs_attach(void);
static void cs_detach(dev_link_t *);

/*
   The dev_info variable is the "key" that is used to match up this
   device driver with appropriate cards, through the card configuration
   database.
*/

static dev_info_t dev_info = "fcpcmcia_cs";

/*
   A linked list of "instances" of the skeleton device.  Each actual
   PCMCIA card corresponds to one device instance, and is described
   by one dev_link_t structure (defined in ds.h).

   You may not want to use a linked list for this -- for example, the
   memory card driver uses an array of dev_link_t pointers, where minor
   device numbers are used to derive the corresponding array index.
*/

static dev_link_t *dev_list = NULL;

/*
   A dev_link_t structure has fields for most things that are needed
   to keep track of a socket, but there will usually be some device
   specific information that also needs to be kept track of.  The
   'priv' pointer in a dev_link_t structure can be used to point to
   a device-specific private data structure, like this.

   A driver needs to provide a dev_node_t structure for each device
   on a card.  In some cases, there is only one device per card (for
   example, ethernet cards, modems).  In other cases, there may be
   many actual or logical devices (SCSI adapters, memory cards with
   multiple partitions).  The dev_node_t structures need to be kept
   in a linked list starting at the 'dev' field of a dev_link_t
   structure.  We allocate them in the card's private data structure,
   because they generally can't be allocated dynamically.
*/
   
typedef struct local_info_t {
    dev_node_t	node;
} local_info_t;

/*======================================================================

    cs_attach() creates an "instance" of the driver, allocating
    local data structures for one device.  The device is registered
    with Card Services.

    The dev_link structure is initialized, but we don't actually
    configure the card at this point -- we wait until we receive a
    card insertion event.
    
======================================================================*/

static dev_link_t *cs_attach(void)
{
    client_reg_t client_reg;
    dev_link_t *link;
    local_info_t *local;
    int ret;
#if defined (PCMCIA_IRQ_INFO2)
    int i;
#endif
    
    NOTE("Attaching device...\n");

    /* Initialize the dev_link_t structure */
    link = kmalloc(sizeof(struct dev_link_t), GFP_KERNEL);
    if (!link)
        goto err;
    memset(link, 0, sizeof(struct dev_link_t));

    /* The io structure describes IO port mapping */
    link->io.NumPorts1 = 16;
    link->io.Attributes1 = IO_DATA_PATH_WIDTH_8;
    link->io.NumPorts2 = 0;

    /* Interrupt setup */
    link->irq.Attributes = IRQ_TYPE_DYNAMIC_SHARING|IRQ_FIRST_SHARED;

#if defined (PCMCIA_IRQ_INFO2)
    link->irq.IRQInfo1 = IRQ_INFO2_VALID|IRQ_LEVEL_ID;
    if (irq_list_count > 0) {
	for (i = 0; (i < irq_list_count) && (irq_list[i] > 0); i++)
	    link->irq.IRQInfo2 |= 1 << irq_list[i];
    } else {
	for (i = 0; (i < irq_list_count) && (default_irq_list[i] > 0); i++)
	    link->irq.IRQInfo2 |= 1 << default_irq_list[i];
    }
#else
    link->irq.IRQInfo1 = IRQ_LEVEL_ID;
#endif
    
    /* General socket configuration */
    link->conf.Attributes = CONF_ENABLE_IRQ;
    link->conf.Vcc = 50;
    link->conf.IntType = INT_MEMORY_AND_IO;
    link->conf.ConfigIndex = 1;
    link->conf.Present = PRESENT_OPTION;

    /* Allocate space for private device-specific data */
    local = kmalloc(sizeof(local_info_t), GFP_KERNEL);
    if (!local)
        goto err_kfree;
    memset(local, 0, sizeof(local_info_t));
    link->priv = local;
    
    /* Register with Card Services */
    link->next = dev_list;
    dev_list = link;
    client_reg.dev_info = &dev_info;
    client_reg.Attributes = INFO_IO_CLIENT | INFO_CARD_SHARE;
    client_reg.EventMask =
	CS_EVENT_CARD_INSERTION | CS_EVENT_CARD_REMOVAL |
	CS_EVENT_RESET_PHYSICAL | CS_EVENT_CARD_RESET |
	CS_EVENT_PM_SUSPEND | CS_EVENT_PM_RESUME;
    client_reg.event_handler = &cs_event;
    client_reg.Version = 0x0210;
    client_reg.event_callback_args.client_data = link;
    ret = pcmcia_register_client(&link->handle, &client_reg);
    if (ret != 0) {
	cs_error(link->handle, RegisterClient, ret);
	cs_detach(link);
	goto err;
    }
    return link;

 err_kfree:
    kfree(link);
 err:
    return NULL;
} /* cs_attach */

/*======================================================================

    This deletes a driver "instance".  The device is de-registered
    with Card Services.  If it has been released, all local data
    structures are freed.  Otherwise, the structures will be freed
    when the device is released.

======================================================================*/

static void cs_detach(dev_link_t *link)
{
    dev_link_t **linkp;

    NOTE("Detaching device...\n");

    /* Locate device structure */
    for (linkp = &dev_list; *linkp; linkp = &(*linkp)->next)
	if (*linkp == link) break;
    if (*linkp == NULL)
	return;

    /*
       If the device is currently configured and active, we won't
       actually delete it yet.  Instead, it is marked so that when
       the release() function is called, that will trigger a proper
       detach().
    */
    if (link->state & DEV_CONFIG) {
	link->state |= DEV_STALE_LINK;
	return;
    }

    /* Break the link with Card Services */
    if (link->handle)
	pcmcia_deregister_client(link->handle);
    
    /* Unlink device structure, free pieces */
    *linkp = link->next;
    if (link->priv) {
	kfree(link->priv);
    }
    kfree(link);
    
} /* cs_detach */

/*======================================================================

    cs_config() is scheduled to run after a CARD_INSERTION event
    is received, to configure the PCMCIA socket, and to make the
    ethernet device available to the system.
    
======================================================================*/

static int get_tuple(client_handle_t handle, tuple_t *tuple, cisparse_t *parse)
{
    int i = pcmcia_get_tuple_data(handle, tuple);
    if (i != CS_SUCCESS) return i;
    return pcmcia_parse_tuple(handle, tuple, parse);
}

static int first_tuple(client_handle_t handle, tuple_t *tuple,
		     cisparse_t *parse)
{
    int i = pcmcia_get_first_tuple(handle, tuple);
    if (i != CS_SUCCESS) return i;
    return get_tuple(handle, tuple, parse);
}

static int next_tuple(client_handle_t handle, tuple_t *tuple,
		     cisparse_t *parse)
{
    int i = pcmcia_get_next_tuple(handle, tuple);
    if (i != CS_SUCCESS) return i;
    return get_tuple(handle, tuple, parse);
}

static void cs_config(dev_link_t *link)
{
    client_handle_t handle;
    tuple_t tuple;
    cisparse_t parse;
    cistpl_cftable_entry_t *cf = &parse.cftable_entry;
    local_info_t *dev;
    int i;
    u_char buf[64];
    char devname[128];
    handle = link->handle;
    dev = link->priv;

    /*
       This reads the card's CONFIG tuple to find its configuration
       registers.
    */
    do {
	tuple.DesiredTuple = CISTPL_CONFIG;
	i = pcmcia_get_first_tuple(handle, &tuple);
	if (i != CS_SUCCESS) break;
	tuple.TupleData = buf;
	tuple.TupleDataMax = 64;
	tuple.TupleOffset = 0;
	i = pcmcia_get_tuple_data(handle, &tuple);
	if (i != CS_SUCCESS) break;
	i = pcmcia_parse_tuple(handle, &tuple, &parse);
	if (i != CS_SUCCESS) break;
	link->conf.ConfigBase = parse.config.base;
    } while (0);
    if (i != CS_SUCCESS) {
	cs_error(link->handle, ParseTuple, i);
	link->state &= ~DEV_CONFIG_PENDING;
	return;
    }
    
    /* Configure card */
    link->state |= DEV_CONFIG;

    do {

	tuple.Attributes = 0;
	tuple.TupleData = buf;
	tuple.TupleDataMax = 254;
	tuple.TupleOffset = 0;
	tuple.DesiredTuple = CISTPL_VERS_1;

	devname[0] = 0;
	if( !first_tuple(handle, &tuple, &parse) && parse.version_1.ns > 1 ) {
	    strlcpy(devname,parse.version_1.str + parse.version_1.ofs[1], 
			sizeof(devname));
	}
	/*
         * find IO port
         */
	tuple.TupleData = (cisdata_t *)buf;
	tuple.TupleOffset = 0; tuple.TupleDataMax = 255;
	tuple.Attributes = 0;
	tuple.DesiredTuple = CISTPL_CFTABLE_ENTRY;
	i = first_tuple(handle, &tuple, &parse);
	while (i == CS_SUCCESS) {
	    if (cf->io.nwin > 0) {
		link->conf.ConfigIndex = cf->index;
		link->io.BasePort1 = cf->io.win[0].base;
		link->io.NumPorts1 = cf->io.win[0].len;
		link->io.NumPorts2 = 0;
                NOTE("testing i/o %#x-%#x\n",
			link->io.BasePort1,
		        link->io.BasePort1+link->io.NumPorts1-1);
		i = pcmcia_request_io(link->handle, &link->io);
		if (i == CS_SUCCESS) goto found_port;
	    }
	    i = next_tuple(handle, &tuple, &parse);
	}

found_port:
	if (i != CS_SUCCESS) {
	    cs_error(link->handle, RequestIO, i);
	    break;
	}
	
	/*
	 * allocate an interrupt line
	 */
	i = pcmcia_request_irq(link->handle, &link->irq);
	if (i != CS_SUCCESS) {
	    cs_error(link->handle, RequestIRQ, i);
	    pcmcia_release_io(link->handle, &link->io);
	    break;
	}
	
	/*
         * configure the PCMCIA socket
	  */
	i = pcmcia_request_configuration(link->handle, &link->conf);
	if (i != CS_SUCCESS) {
	    cs_error(link->handle, RequestConfiguration, i);
	    pcmcia_release_io(link->handle, &link->io);
	    pcmcia_release_irq(link->handle, &link->irq);
	    break;
	}

    } while (0);

    /* At this point, the dev_node_t structure(s) should be
       initialized and arranged in a linked list at link->dev. */

    strcpy(dev->node.dev_name, "A1");
    dev->node.major = 64;
    dev->node.minor = 0;
    link->dev = &dev->node;
    
    link->state &= ~DEV_CONFIG_PENDING;
    /* If any step failed, release any partially configured state */
    if (i != 0) {
        ERROR("Failed to setup controller, releasing link...\n");
	cs_release(link);
	return;
    }
    NOTE("Ready to call card driver for '%s'...\n", devname);

    if ((i = fcpcmcia_addcard(link->io.BasePort1, link->irq.AssignedIRQ)) < 0) {
        ERROR(
		"Failed to add AVM-%s-Controller at i/o %x, irq %d\n",
		dev->node.dev_name, 
		link->io.BasePort1, 
		link->irq.AssignedIRQ
	);
	cs_release(link);
	return;
    }
    dev->node.minor = i;

    NOTE(
	"Card driver for '%s' has been set up: i/o %x, irq %d\n", 
	devname, 
	link->io.BasePort1, 
	link->irq.AssignedIRQ
    );
} /* cs_config */

/*======================================================================

    After a card is removed, cs_release() will unregister the net
    device, and release the PCMCIA configuration.  If the device is
    still open, this will be postponed until it is closed.
    
======================================================================*/

static void cs_release(dev_link_t *link)
{
    fcpcmcia_delcard(link->io.BasePort1, link->irq.AssignedIRQ);

    /* Unlink the device chain */
    link->dev = NULL;
    
    /* Don't bother checking to see if these succeed or not */
    pcmcia_release_configuration(link->handle);
    pcmcia_release_io(link->handle, &link->io);
    pcmcia_release_irq(link->handle, &link->irq);
    link->state &= ~DEV_CONFIG;
    
    if (link->state & DEV_STALE_LINK)
	cs_detach(link);
    
} /* cs_release */

/*======================================================================

    The card status event handler.  Mostly, this schedules other
    stuff to run after an event is received.  A CARD_REMOVAL event
    also sets some flags to discourage the net drivers from trying
    to talk to the card any more.

    When a CARD_REMOVAL event is received, we immediately set a flag
    to block future accesses to this device.  All the functions that
    actually access the device should check this flag to make sure
    the card is still present.
    
======================================================================*/

static int cs_event(event_t event, int priority, event_callback_args_t *args)
{
    dev_link_t *link = args->client_data;

    LOG("Card service event: %x\n", event);
    switch (event) {
    case CS_EVENT_CARD_REMOVAL:
	link->state &= ~DEV_PRESENT;
	if (link->state & DEV_CONFIG)
		cs_release(link);
	break;
    case CS_EVENT_CARD_INSERTION:
	link->state |= DEV_PRESENT | DEV_CONFIG_PENDING;
	cs_config(link);
	break;
    case CS_EVENT_PM_SUSPEND:
	link->state |= DEV_SUSPEND;
	/* Fall through... */
    case CS_EVENT_RESET_PHYSICAL:
	if (link->state & DEV_CONFIG)
	    pcmcia_release_configuration(link->handle);
	break;
    case CS_EVENT_PM_RESUME:
	link->state &= ~DEV_SUSPEND;
	/* Fall through... */
    case CS_EVENT_CARD_RESET:
	if (link->state & DEV_CONFIG)
	    pcmcia_request_configuration(link->handle, &link->conf);
	break;
    }
    return 0;
} /* cs_event */

static struct pcmcia_driver cs_driver = {
//	.owner = THIS_MODULE,
	.drv	= {
		.name	= "fcpcmcia_cs",
	},
	.attach	= cs_attach,
	.detach	= cs_detach,
};

static int __init cs_init(void)
{
	return pcmcia_register_driver(&cs_driver);
}

static void __exit cs_exit(void)
{
	pcmcia_unregister_driver(&cs_driver);

	/* XXX: this really needs to move into generic code.. */
	while (dev_list != NULL) {
		if (dev_list->state & DEV_CONFIG)
			cs_release(dev_list);
		cs_detach(dev_list);
	}
}

module_init(cs_init);
module_exit(cs_exit);
