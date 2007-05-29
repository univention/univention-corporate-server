/*
 * Univention Auto Mount
 *	stat test tool
 *
 * Copyright (C) 2002, 2003, 2004, 2005, 2006 Univention GmbH
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

#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/vfs.h>
#include <unistd.h>

#define DEVICE "/tmp/devices/floppy"

void stat_debug(const char* path)
{
	struct stat stbuf;

	printf("stat %s\n", path);
	if(stat(path, &stbuf) == -1) {
		perror("");
		return;
	}
	printf("\tst_dev: %d\n", stbuf.st_dev);
	printf("\tst_ino: %d\n", stbuf.st_ino);
	printf("\tst_mode: %o\n", stbuf.st_mode);
	printf("\tst_nlink: %d\n", stbuf.st_nlink);
	printf("\tst_uid: %d\n", stbuf.st_uid);
	printf("\tst_gid: %d\n", stbuf.st_gid);
	printf("\tst_rdev: %d\n", stbuf.st_rdev);
	printf("\tst_size: %d\n", stbuf.st_size);
	printf("\tst_blksize: %d\n", stbuf.st_blksize);
	printf("\tst_blocks: %d\n", stbuf.st_blocks);
	printf("\tatime: %d\n", stbuf.st_atime);
	printf("\tmtime: %d\n", stbuf.st_mtime);
	printf("\tctime: %d\n", stbuf.st_ctime);
}

void statfs_debug(const char* path)
{
	struct statfs stfs_buf;

	printf("stafs %s\n", path);
	if(statfs(path, &stfs_buf) == -1) {
		perror("");
		return;
	}
	printf("\tf_type: %d\n", stfs_buf.f_type);
	printf("\tf_bsize: %d\n", stfs_buf.f_bsize);
	printf("\tf_blocks: %d\n", stfs_buf.f_blocks);
	printf("\tf_bfree: %d\n", stfs_buf.f_bfree);
	printf("\tf_bavail: %d\n", stfs_buf.f_bavail);
	printf("\tf_files: %d\n", stfs_buf.f_files);
	printf("\tf_ffree: %d\n", stfs_buf.f_ffree);
	printf("\tf_fsid: %d\n", stfs_buf.f_fsid);
	printf("\tf_namelen: %d\n", stfs_buf.f_namelen);
}

int main(int argc, char* argv[])
{
	stat_debug(argv[1]);
	//statfs_debug(argv[1]);
	return 0;
}
