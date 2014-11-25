/*
  Copyright (C) Andrzej Hajda 2009-2013
  Contact: andrzej.hajda@wp.pl
  License: GNU General Public License version 3
*/

#include <talloc.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <core/ntstatus.h>
#include <core/werror.h>
#include <util/data_blob.h>
#include <util/time.h>
#include <smb_cliraw.h>
#include <util/debug.h>

#include "async.h"

static int async_read(struct async_context *c);

static void list_enqueue(struct data_list *l, const void *data, int size)
{
	struct list_item *li = talloc_size(0, sizeof(struct list_item) + size);
	memcpy(li->data, data, size);
	li->size = size;
	li->next = 0;
	if (l->end)
		l->end->next = li;
	else
		l->begin = li;
	l->end = li;
}

static void list_dequeue(struct data_list *l)
{
	struct list_item *li = l->begin;
	if (!li)
		return;
	l->begin = li->next;
	if (!l->begin)
		l->end = 0;
	talloc_free(li);
}

static void async_read_recv(struct smbcli_request *req)
{
	struct async_context *c = req->async.private_data;
	NTSTATUS status;

	status = smb_raw_read_recv(req, c->io_read);
	c->rreq = NULL;
	if (!NT_STATUS_IS_OK(status)) {
		DEBUG(1, ("ERROR: smb_raw_read_recv - %s\n", nt_errstr(status)));
		if (c->cb_error)
			c->cb_error(c->cb_ctx, ASYNC_READ_RECV, status);
		return;
	}

	if (c->cb_read)
		c->cb_read(c->cb_ctx, c->buffer, c->io_read->readx.out.nread);

	async_read(c);
}

static void async_write_recv(struct smbcli_request *req)
{
	struct async_context *c = req->async.private_data;
	NTSTATUS status;

	status = smb_raw_write_recv(req, c->io_write);
	c->wreq = NULL;
	if (!NT_STATUS_IS_OK(status)) {
		DEBUG(1, ("ERROR: smb_raw_write_recv - %s\n", nt_errstr(status)));
		talloc_free(c->io_write);
		c->io_write = 0;
		if (c->cb_error)
			c->cb_error(c->cb_ctx, ASYNC_WRITE_RECV, status);
		return;
	}

	if (c->cb_write)
		c->cb_write(c->cb_ctx);

	if (c->wq.begin) {
		async_write(c, c->wq.begin->data, c->wq.begin->size);
		list_dequeue(&c->wq);
	}
}

static void async_open_recv(struct smbcli_request *req)
{
	struct async_context *c = req->async.private_data;
	NTSTATUS status;

	DEBUG(1, ("IN: async_open_recv\n"));
	status = smb_raw_open_recv(req, c, c->io_open);
	c->rreq = NULL;
	if (NT_STATUS_IS_OK(status))
		c->fd = c->io_open->ntcreatex.out.file.fnum;
	talloc_free(c->io_open);
	c->io_open = 0;
	if (!NT_STATUS_IS_OK(status)) {
		DEBUG(1, ("ERROR: smb_raw_open_recv - %s\n", nt_errstr(status)));
		if (c->cb_error)
			c->cb_error(c->cb_ctx, ASYNC_OPEN_RECV, status);
		return;
	}
	if (c->cb_open)
		c->cb_open(c->cb_ctx);
	async_read(c);
}

static void async_close_recv(struct smbcli_request *req)
{
	struct async_context *c = req->async.private_data;

	smbcli_request_simple_recv(req);
	talloc_free(c->io_close);
	c->io_close = 0;
	if (c->io_open) {
		talloc_free(c->io_open);
		c->io_open = 0;
	}
	if (c->io_read) {
		talloc_free(c->io_read);
		c->io_read = 0;
	}
	if (c->io_write) {
		talloc_free(c->io_write);
		c->io_write = 0;
	}
	if (c->cb_close)
		c->cb_close(c->cb_ctx);
}

static int async_read(struct async_context *c)
{
	if (!c->io_read) {
		c->io_read = talloc(c->tree, union smb_read);
		c->io_read->readx.level = RAW_READ_READX;
		c->io_read->readx.in.file.fnum = c->fd;
		c->io_read->readx.in.offset = 0;
		c->io_read->readx.in.mincnt = sizeof(c->buffer);
		c->io_read->readx.in.maxcnt = sizeof(c->buffer);
		c->io_read->readx.in.remaining = 0;
		c->io_read->readx.in.read_for_execute = false;
		c->io_read->readx.out.data = (uint8_t *)c->buffer;
	}
	c->rreq = smb_raw_read_send(c->tree, c->io_read);
	if (!c->rreq) {
		if (c->cb_error)
			c->cb_error(c->cb_ctx, ASYNC_READ, NT_STATUS_NO_MEMORY);
		return 0;
	}
	c->rreq->transport->options.request_timeout = 0;
	c->rreq->async.fn = async_read_recv;
	c->rreq->async.private_data = c;
	return 1;
}

int async_open(struct async_context *c, const char *fn, int open_mode)
{
	DEBUG(1, ("IN: async_open(%s, %d)\n", fn, open_mode));
	c->io_open = talloc_zero(c, union smb_open);
	if (!c->io_open)
		goto failed;
	c->io_open->ntcreatex.level = RAW_OPEN_NTCREATEX;
	c->io_open->ntcreatex.in.flags = 0;
	c->io_open->ntcreatex.in.root_fid.fnum = 0;
	c->io_open->ntcreatex.in.access_mask =
		SEC_STD_READ_CONTROL |
		SEC_FILE_WRITE_ATTRIBUTE |
		SEC_FILE_WRITE_EA |
		SEC_FILE_READ_DATA |
		SEC_FILE_WRITE_DATA;
	c->io_open->ntcreatex.in.open_disposition = NTCREATEX_DISP_OPEN;
	c->io_open->ntcreatex.in.impersonation    = NTCREATEX_IMPERSONATION_IMPERSONATION;
	c->io_open->ntcreatex.in.create_options = NTCREATEX_OPTIONS_NON_DIRECTORY_FILE | NTCREATEX_OPTIONS_WRITE_THROUGH;
	c->io_open->ntcreatex.in.security_flags = 0;
	c->io_open->ntcreatex.in.fname = fn;
	c->rreq = smb_raw_open_send(c->tree, c->io_open);
	if (!c->rreq)
		goto failed;
	c->rreq->async.fn = async_open_recv;
	c->rreq->async.private_data = c;
	return 1;

  failed:
	DEBUG(1, ("ERROR: async_open\n"));
	talloc_free(c);
	return 0;
}

int async_write(struct async_context *c, const void *buf, int len)
{
	if (c->wreq) {
		list_enqueue(&c->wq, buf, len);
		return 0;
	}
	if (!c->io_write) {
		c->io_write = talloc_zero(c, union smb_write);
		if (!c->io_write)
			goto failed;
		c->io_write->write.level = RAW_WRITE_WRITE;
		c->io_write->write.in.remaining = 0;
		c->io_write->write.in.file.fnum = c->fd;
		c->io_write->write.in.offset = 0;
	}
	c->io_write->write.in.count = len;
	c->io_write->write.in.data = buf;
	struct smbcli_request *req = smb_raw_write_send(c->tree, c->io_write);
	if (!req)
		goto failed;
	req->async.fn = async_write_recv;
	req->async.private_data = c;
	return 1;
  failed:
	DEBUG(1, ("ERROR: async_write\n"));
	talloc_free(c->io_write);
	c->io_write = 0;
	return 0;
}

int async_close(struct async_context *c)
{
	if (c->rreq)
		smbcli_request_destroy(c->rreq);
	if (c->wreq)
		smbcli_request_destroy(c->wreq);
	c->rreq = c->wreq = NULL;
	c->io_close = talloc_zero(c, union smb_close);
	if (!c->io_close)
		goto failed;
	c->io_close->close.level = RAW_CLOSE_CLOSE;
	c->io_close->close.in.file.fnum = c->fd;
	c->io_close->close.in.write_time = 0;
	struct smbcli_request *req = smb_raw_close_send(c->tree, c->io_close);
	if (!req)
		goto failed;
	req->async.fn = async_close_recv;
	req->async.private_data = c;
	return 1;
  failed:
	DEBUG(1, ("ERROR: async_close\n"));
	talloc_free(c->io_close);
	c->io_close = 0;
	return 0;
}
