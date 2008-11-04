/* 
 * defs.h
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

#ifndef __have_defs_h__
#define __have_defs_h__

#ifndef LINUX_VERSION_CODE
# include <linux/version.h>
#endif

#ifndef TRUE
# define TRUE	(1==1)
# define FALSE	(1==0)
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (__fcclassic__)
# define PRODUCT_LOGO		"AVM FRITZ!Card Classic"
# define INTERFACE		"isa"
#elif defined (__fcpnp__)
# define PRODUCT_LOGO		"AVM FRITZ!Card PnP"
# define INTERFACE		"pnp"
#elif defined (__fcpcmcia__)
# define PRODUCT_LOGO		"AVM FRITZ!Card PCMCIA"
# define INTERFACE		"pcmcia"
#elif defined (__fcpci__)
# define PRODUCT_LOGO		"AVM FRITZ!Card PCI"
# define INTERFACE		"pci"
#else
# error You have to define a card identifier...
#endif

#define SHORT_LOGO		"fritz-" INTERFACE
#define DRIVER_LOGO		PRODUCT_LOGO " driver"
#define	DRIVER_TYPE_INTERN
#define	DRIVER_TYPE_ISDN
#define	DRIVER_REV		"0.7.2"

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (OSDEBUG) && defined (NDEBUG)
# undef NDEBUG
#endif

#define	UNUSED_ARG(x)	(x)=(x)

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#define	TOOLS_SUB_ALLOC

#define	KB			1024
#define	MIN_LIB_HEAP_SIZE	(64 * KB)
#define	MAX_LIB_HEAP_SIZE	(600 * KB)

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (CONFIG_ISAPNP_MODULE) && !defined (CONFIG_ISAPNP)
#define CONFIG_ISAPNP
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#endif

