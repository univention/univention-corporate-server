/*
 * Univention Client Login
 *  this file is part of the Univention thin client tools
 *
 * Copyright (C) 2004, 2005, 2006 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include "protocol.h"
//int write_to_pipe ( int to_fd, int timeout, const void* buffer, int len );
// CCONV
int write_buf_to_pipe ( int to_fd, int timeout, const void* buffer, int len );
//int write_buf_to_pipe ( int to_fd, int timeout, char* buffer, int len );
int write_to_pipe ( int to_fd, int timeout, struct raw_message_t* buffer , int len);
int read_from_pipe ( int from_fd, int timeout, struct raw_message_t* buffer, int buflen );
int read_cmd_from_pipe ( int from_fd, int timeout, struct raw_message_t* buffer, int buflen );
int read_data_from_pipe ( int from_fd, int timeout, struct raw_message_t* buffer, int buflen );
int write_to_script_pipe ( int to_fd, int timeout, char * buffer );
int read_from_script_pipe ( int from_fd, int timeout, char * buffer, int buflen );
