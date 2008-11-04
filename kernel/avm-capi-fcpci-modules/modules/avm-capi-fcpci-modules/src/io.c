/* 
 * io.c
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

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
unsigned char InpByte (unsigned port) {

	return inb (port);
} /* InpByte */

void OutpByte (unsigned port, unsigned char data) { 

	outb (data, port); 
} /* OutpByte */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
unsigned long InpDWord (unsigned port) { 

	return inl (port); 
} /* InpDWord */

void OutpDWord (unsigned port, unsigned long data) { 

	outl (data, port); 
} /* OutpDWord */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void InpByteBlock (unsigned port, unsigned char * buffer, unsigned length) {

	insb (port, buffer, length);
} /* InpByteBlock */

void OutpByteBlock (unsigned port, unsigned char * buffer, unsigned length) {

	outsb (port, buffer, length);
} /* OutpByteBlock */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/
void InpDWordBlock (unsigned port, unsigned char * buffer, unsigned length) {

	insl (port, buffer, (length + 3) / 4);
} /* InpDWordBlock */

void OutpDWordBlock (unsigned port, unsigned char * buffer, unsigned length) {

	outsl (port, buffer, (length + 3) / 4);
} /* OutpDWordBlock */

/*---------------------------------------------------------------------------*\
\*---------------------------------------------------------------------------*/

