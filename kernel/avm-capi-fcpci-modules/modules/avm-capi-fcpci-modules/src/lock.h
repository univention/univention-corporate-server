/* 
 * lock.h
 * Copyright (C) 2004, AVM GmbH. All rights reserved.
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

#ifndef __have_lock_h__
#define __have_lock_h__

typedef struct __lock *		lock_t;

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
extern int lock_init (lock_t *);
extern void lock_exit (lock_t *);

extern void lock (lock_t);
extern void unlock (lock_t);

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
#endif

