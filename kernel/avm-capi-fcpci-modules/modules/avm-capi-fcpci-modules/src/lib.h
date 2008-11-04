/* 
 * lib.h
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

#ifndef __have_lib_h__
#define __have_lib_h__

#include "defs.h"
#include "libdefs.h"

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern lib_callback_t * get_library (void);
extern lib_callback_t * link_library (void *);
extern void free_library (void);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#if defined (DRIVER_TYPE_INTERN)
extern __attr void printl (char *, ...);
#endif

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern __attr void os_timer_poll (void);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern __attr2 void * lib_memcpy (void *, const void *, size_t);
extern __attr2 void * lib_memset (void *, int, size_t);
extern __attr2 int lib_memcmp (const void *, const void *, size_t);
extern __attr2 void * lib_memmove (void *, const void *, size_t);

extern __attr2 char * lib_strcpy (char *, const char *);
extern __attr2 char * lib_strncpy (char *, const char *, unsigned);
extern __attr2 char * lib_strcat (char *, const char *);
extern __attr2 int lib_strcmp (const char *, const char *);
extern __attr2 int lib_strncmp (const char *, const char *, unsigned);

extern __attr2 size_t lib_strlen (const char * s);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#endif
