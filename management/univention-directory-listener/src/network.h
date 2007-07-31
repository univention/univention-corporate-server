/*
 * Univention Directory Listener
 *  header information for network.c
 *
 * Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

#ifndef _NETWORK_H_
#define _NETWORK_H_

#include <sys/types.h>

#define NOTIFIER_TIMEOUT 120

typedef unsigned long NotifierID;

struct _NotifierEntry {
	NotifierID	 id;
	char		*dn;
	char		 command; /* 'd'elete, 'm'odify, 'a'dd */
} typedef NotifierEntry;

struct _NotifierMessage {
	int			 id;
	char			*result;
	struct _NotifierMessage	*next;
} typedef NotifierMessage;

struct _NotifierClient {
	char		*server;
	int		 protocol;
	int		 starttls;
	int		 fd;
	NotifierMessage	*messages;
	int		 last_msgid;
	char		*buf;
} typedef NotifierClient;

void		  notifier_entry_free	    (NotifierEntry	*entry);
int		  notifier_client_new	    (NotifierClient	*client,
					     const char		*server,
					     int		 starttls);
void		  notifier_client_destroy   (NotifierClient	*client);
int		  notifier_wait		    (NotifierClient	*client,
					     time_t		 timeout);

int		  notifier_recv_result	    (NotifierClient	*client,
					     time_t		 timeout);
NotifierMessage*  notifier_get_msg	    (NotifierClient	*client,
					     int		 msgid);

int		  notifier_get_dn	    (NotifierClient	*client,
					     NotifierID		 id);
int		  notifier_resend_get_dn    (NotifierClient	*client,
					     int		 msgid,
					     NotifierID		 id);
int		  notifier_get_dn_result    (NotifierClient	*client,
					     int		msgid,
					     NotifierEntry	*entry);
int		  notifier_alive_s	    (NotifierClient	*client);
int		  notifier_get_id_s	    (NotifierClient	*client,
					     NotifierID		*id);
int		  notifier_get_schema_id_s  (NotifierClient	*client,
					     NotifierID		*id);

#endif /* _NETWORK_H_ */
