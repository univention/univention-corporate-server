/*
 * Univention Directory Listener
 *  header information for network.c
 *
 * SPDX-FileCopyrightText: 2004-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _NETWORK_H_
#define _NETWORK_H_

#include <sys/types.h>

#define NOTIFIER_TIMEOUT 120

typedef unsigned long NotifierID;

struct _NotifierEntry {
	NotifierID id;
	char *dn;
	char command; /* 'd'elete, 'm'odify, 'a'dd, mod'r'dn */
} typedef NotifierEntry;

struct _NotifierMessage {
	int id;
	char *result;
	struct _NotifierMessage *next;
} typedef NotifierMessage;

struct _NotifierClient {
	char *server;
	int protocol;
	int starttls;
	int fd;
	NotifierMessage *messages;
	int last_msgid;
	char *buf;
} typedef NotifierClient;

void notifier_entry_free(NotifierEntry *entry);
int notifier_client_new(NotifierClient *client, const char *server, int starttls);
void notifier_client_destroy(NotifierClient *client);
int notifier_wait(NotifierClient *client, time_t timeout);

int notifier_recv_result(NotifierClient *client, time_t timeout);
NotifierMessage *notifier_get_msg(NotifierClient *client, int msgid);

int notifier_get_dn(NotifierClient *client, NotifierID id);
int notifier_resend_get_dn(NotifierClient *client, int msgid, NotifierID id);
int notifier_get_dn_result(NotifierClient *client, int msgid, NotifierEntry *entry);
int notifier_alive_s(NotifierClient *client);
int notifier_get_id_s(NotifierClient *client, NotifierID *id);
int notifier_get_schema_id_s(NotifierClient *client, NotifierID *id);

#endif /* _NETWORK_H_ */
