/* 
 * main.c
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

#include <stdarg.h>
#include <asm/uaccess.h>

#include <linux/version.h>
#include <linux/kernel.h>
#include <linux/module.h>
#include <linux/init.h>
#include <linux/string.h>
#include <linux/skbuff.h>
#include <linux/errno.h>
#include <linux/capi.h>
#include <linux/ctype.h>
#include <linux/isdn/capilli.h>

#if defined (__fcpci__)
#include <linux/pci.h>
#elif defined (__fcpnp__)
#include <linux/isapnp.h>
#elif defined (__fcclassic__)
#include <linux/moduleparam.h>
#endif

#include "driver.h"
#include "tools.h"
#include "lib.h"
#include "defs.h"

MODULE_LICENSE ("Proprietary");
MODULE_DESCRIPTION ("CAPI4Linux: Driver for " PRODUCT_LOGO);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static char *	REVCONST	= "$Revision: $";
static char	REVISION[32];
static int	mod_count	= 0;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
struct capi_driver fritz_capi_driver = {

	.name			= TARGET,
	.revision		= DRIVER_REV,
#if defined (__fcclassic__)
	.add_card		= add_card,
#endif
} ;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcclassic__)

short int	io		= 0;
short int	irq		= 0;

module_param (io, short, 0);
module_param (irq, short, 0);

MODULE_PARM_DESC(io, "I/O address: 0x200, 0x240, 0x300, or 0x340");
MODULE_PARM_DESC(irq, "IRQ number");

#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcpci__)

#define	PCI_DEVICE_ID_FRITZ1	0x0A00
#define	PCI_DEVICE_ID_FRITZ2	0x0E00

static struct pci_device_id fcpci_id_table[] = {
	{ PCI_VENDOR_ID_AVM, PCI_DEVICE_ID_FRITZ1, 
		PCI_ANY_ID, PCI_ANY_ID, 0, 0, 0 },
	{ PCI_VENDOR_ID_AVM, PCI_DEVICE_ID_FRITZ2, 
		PCI_ANY_ID, PCI_ANY_ID, 0, 0, 0 },
	{ /* Terminating entry */ }
} ;

MODULE_DEVICE_TABLE (pci, fcpci_id_table);

#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcpnp__)

static struct pnp_device_id fcpnp_id_table[] = {
	{ .id = "AVM0900", .driver_data = 0 },
	{ .id = "" }
} ;

MODULE_DEVICE_TABLE (pnp, fcpnp_id_table);

#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcpcmcia__)

EXPORT_SYMBOL (fcpcmcia_addcard);
EXPORT_SYMBOL (fcpcmcia_delcard);

#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#ifndef NDEBUG
static void base_address (void) {

	LOG("Base address: %p\n", base_address);
	LOG("Compile time: %s\n", __TIME__);
} /* base_address */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void inc_use_count (void) {
	
	++mod_count; 
} /* inc_use_count */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void dec_use_count (void) {
	
	assert (mod_count > 0); 
	--mod_count; 
} /* dec_use_count */

/*---------------------------------------------------------------------------*\
 * I S A
\*---------------------------------------------------------------------------*/
#if defined (__fcclassic__)

static int __devinit isa_start (
	unsigned short		io_arg,
	unsigned short		irq_arg
) {
	struct capicardparams	pars;
	int			res = 0;

	pars.irq = irq_arg;
	pars.port = io_arg;
	NOTE(PRODUCT_LOGO " expected @ port 0x%04x, irq %u\n", io_arg, irq_arg);

	NOTE("Loading...\n");
	if (0 != (res = add_card (&fritz_capi_driver, &pars))) {
		ERROR("Not loaded.\n");
	} else {
		NOTE("Loaded.\n");
	}
	return res;
} /* isa_start */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcclassic__)

static void isa_stop (void) {

	LOG("Stopping controller...\n");
	remove_ctrl (capi_controller);
} /* isa_stop */
#endif

/*---------------------------------------------------------------------------*\
 * P N P
\*---------------------------------------------------------------------------*/
#if defined (__fcpnp__)

static int __devinit fritz_probe (
	struct pnp_dev *		dev,
	const struct pnp_device_id *	id
) {
	struct capicardparams		pars;
	int				res = -ENODEV;
	
	assert (dev != NULL);
	UNUSED_ARG (id);
	pars.irq = pnp_irq (dev, 0);
	pars.port = pnp_port_start (dev, 0);
	assert (32 == pnp_port_len (dev, 0));
	NOTE(PRODUCT_LOGO " found: port 0x%04x, irq %u\n", pars.port, pars.irq);

	NOTE("Loading...\n");
	if (!fritz_driver_init ()) {
		ERROR("Error: Driver library not available.\n");
		ERROR("Not loaded.\n");
		return res;
	}
	if (0 != (res = add_card (&fritz_capi_driver, &pars))) {
		ERROR("Not loaded.\n");
		return res;
	}	
	assert (capi_card != NULL);
	capi_card->dev = dev;
	pnp_set_drvdata (dev, capi_card);

	libheap_init (MAX_LIB_HEAP_SIZE);
	NOTE("Loaded.\n");
	return 0;
} /* fritz_probe */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcpnp__)

static void __devexit fritz_remove (struct pnp_dev * dev) {
	card_t *	card;
	
	card = (card_t *) pnp_get_drvdata (dev);
	assert (card != NULL);

	NOTE("Removing...\n");
	remove_ctrl (&card->ctrl);
	NOTE("Removed.\n");
	libheap_exit ();
	driver_exit ();
#ifndef NDEBUG
	if (hallocated() != 0) {
		ERROR("%u bytes leaked.\n", hallocated());
	}
#endif
} /* fritz_remove */
#endif

/*---------------------------------------------------------------------------*\
 * P C I
\*---------------------------------------------------------------------------*/
#if defined (__fcpci__)

static int __devinit fritz_probe (
	struct pci_dev *		dev,
	const struct pci_device_id *	id
) {
	struct capicardparams		pars;
	int				res = 0;
	
	assert (dev != NULL);
	UNUSED_ARG (id);
	if (pci_enable_device (dev) < 0) {
		ERROR("Error: Failed to enable " PRODUCT_LOGO "!\n");
		return -ENODEV;
	}
	pars.irq = dev->irq;
	pars.port = pci_resource_start (dev, 1);
	NOTE (PRODUCT_LOGO " found: port 0x%04x, irq %u\n", pars.port, pars.irq);

	NOTE("Loading...\n");
	if (!fritz_driver_init ()) {
		ERROR("Error: Driver library not available.\n");
		ERROR("Not loaded.\n");
		return -EBUSY;
	}
	if (0 != (res = add_card (&fritz_capi_driver, &pars))) {
		ERROR("Not loaded.\n");
		return res;
	}	
	assert (capi_card != NULL);
	capi_card->dev = dev;
	pci_set_drvdata (dev, capi_card);

	libheap_init (MAX_LIB_HEAP_SIZE);
	NOTE("Loaded.\n");
	return 0;
} /* fritz_probe */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcpci__)

static void __devexit fritz_remove (struct pci_dev * dev) {
	card_t *	card;
	
	card = (card_t *) pci_get_drvdata (dev);
	assert (card != NULL);

	NOTE("Removing...\n");
	remove_ctrl (&card->ctrl);
	NOTE("Removed.\n");
	libheap_exit ();
	driver_exit ();
#ifndef NDEBUG
	if (hallocated() != 0) {
		ERROR("%u bytes leaked.\n", hallocated());
	}
#endif
} /* fritz_remove */
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcpci__)

static struct pci_driver	fcpci_driver = {

	.name		= TARGET,
	.id_table	= fcpci_id_table,
	.probe		= fritz_probe,
	.remove		= __devexit_p(fritz_remove),
} ;

#elif defined (__fcpnp__)

static struct pnp_driver	fcpnp_driver = {

	.name		= TARGET,
	.id_table	= fcpnp_id_table,
	.probe		= fritz_probe,
	.remove		= __devexit_p(fritz_remove),
} ;

#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static int __init fritz_init (void) {
	char *	tmp;
#if defined (__fcpci__) || defined (__fcpnp__)
	int	err;
#endif
	
#ifndef NDEBUG
	base_address ();
#endif
	if ((NULL != (tmp = strchr (REVCONST, ':'))) && isdigit (*(tmp + 2))) {
		lib_strncpy (REVISION, tmp + 1, sizeof (REVISION));
		tmp = strchr (REVISION, '$');
		*tmp = 0;
	} else {
		lib_strncpy (REVISION, DRIVER_REV, sizeof (REVISION));
	}
	NOTE("%s, revision %s\n", DRIVER_LOGO, REVISION);
        NOTE("(%s built on %s at %s)\n", TARGET, __DATE__, __TIME__);
		
#ifdef __LP64__
	NOTE("-- 64 bit CAPI driver --\n");
#else
	NOTE("-- 32 bit CAPI driver --\n");
#endif

#if defined (__fcpci__)	
	if (0 == (err = pci_register_driver (&fcpci_driver))) {
		LOG("PCI driver registered.\n");
		register_capi_driver (&fritz_capi_driver);
		LOG("CAPI driver registered.\n");
	}
	return err;
#elif defined (__fcpnp__)
	if (0 == (err = pnp_register_driver (&fcpnp_driver))) {
		LOG("PnP driver registered.\n");
		register_capi_driver (&fritz_capi_driver);
		LOG("CAPI driver registered.\n");
	}
	return err;
#elif defined (__fcpcmcia__) || defined (__fcclassic__)
	if (!fritz_driver_init ()) {
		ERROR("Error: Driver library not available.\n");
		ERROR("Not loaded.\n");
		return -EBUSY;
	}
	register_capi_driver (&fritz_capi_driver);
	LOG("CAPI driver registered.\n");
	libheap_init (MAX_LIB_HEAP_SIZE);
#if defined (__fcclassic__)
	if ((io != 0) && (irq != 0)) {
		return isa_start (io, irq);
	} else if ((io + irq) != 0) {
		NOTE("Warning: Missing parameter!\n");
		NOTE("Waiting for capiinit...\n");
	}
#endif	
	return 0;
#endif
} /* fritz_init */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
static void __exit fritz_exit (void) {

#if defined (__fcclassic__)
	isa_stop ();
	libheap_exit ();
#endif
	unregister_capi_driver (&fritz_capi_driver);
	LOG("CAPI driver unregistered.\n");
#if defined (__fcpci__)
	pci_unregister_driver (&fcpci_driver);
	LOG("PCI driver unregistered.\n");
#elif defined (__fcpnp__)
	pnp_unregister_driver (&fcpnp_driver);
	LOG("PnP driver unregistered.\n");
#endif
	assert (mod_count == 0);
} /* fritz_exit */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
module_init (fritz_init);
module_exit (fritz_exit);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
