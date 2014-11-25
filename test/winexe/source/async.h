/*
  Copyright (C) Andrzej Hajda 2009-2013
  Contact: andrzej.hajda@wp.pl
  License: GNU General Public License version 3
*/

enum { ASYNC_OPEN, ASYNC_OPEN_RECV, ASYNC_READ, ASYNC_READ_RECV,
       ASYNC_WRITE, ASYNC_WRITE_RECV, ASYNC_CLOSE, ASYNC_CLOSE_RECV };

typedef void (*async_cb_open) (void *ctx);
typedef void (*async_cb_read) (void *ctx, const char *data, int len);
typedef void (*async_cb_write) (void *ctx);
typedef void (*async_cb_close) (void *ctx);
typedef void (*async_cb_error) (void *ctx, int func, NTSTATUS status);

struct list_item {
	struct list_item *next;
	int size;
	char data[0];
};

struct data_list {
	struct list_item *begin;
	struct list_item *end;
};

struct async_context {
/* Public - must be initialized by client */
	struct smbcli_tree *tree;
	void *cb_ctx;
	async_cb_open cb_open;
	async_cb_read cb_read;
	async_cb_write cb_write;
	async_cb_close cb_close;
	async_cb_error cb_error;
/* Private - internal usage, initialize to zeros */
	int fd;
	union smb_open *io_open;
	union smb_read *io_read;
	union smb_write *io_write;
	union smb_close *io_close;
	struct smbcli_request *rreq;
	struct smbcli_request *wreq;
	struct data_list wq;
	char buffer[256];
};

int async_open(struct async_context *c, const char *fn, int open_mode);
int async_write(struct async_context *c, const void *buf, int len);
int async_close(struct async_context *c);
