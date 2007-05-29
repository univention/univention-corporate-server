/*
 * Univention Auto Mount
 *	main part of the autofs tools
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

#ifdef linux
/* For pread()/pwrite() */
#define _XOPEN_SOURCE 500
#endif

#include <fuse.h>
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <dirent.h>
#include <errno.h>
#include <sys/statfs.h>
#include <sys/mount.h>
#include <sys/time.h>
#include <signal.h>
#include <pthread.h>
#include <time.h>

#include <sys/ioctl.h>
#include <linux/cdrom.h>
//#define _DEBUG_
#define UMOUNT_TIMEOUT 200000
#define REMOUNT_TIMEOUT 200000
#ifdef _DEBUG_
#define DEBUG(args...) do { fprintf ( stderr, "[%d] %s ", getpid(), device); fprintf ( stderr, args ); } while(0)
#else
#define DEBUG(args...)
#endif

static int autofs_statfs(struct fuse_statfs_compat1 *fst);

struct timeval last_access_tv;

char *device = 0;
char *filesystem = 0;
char *mountpoint = 0;
char *external_mountpoint = 0;
char *external_mountoptions = 0;
int autofs_mountoptions = 0;
char *mountdata = 0;
int mounted = 0;
int helper_return = 0;
pthread_t helper_thread;

pthread_mutex_t mount_mutex = PTHREAD_MUTEX_INITIALIZER;

struct fuse_statfs_compat1 statfs_cache;
pthread_mutex_t statfs_mutex = PTHREAD_MUTEX_INITIALIZER;

int is_cdrom = 0;

static void do_statfs(void)
{
	int rv;
	struct statfs st;

	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, "/");

	DEBUG("statfs: real\n");

	pthread_mutex_lock(&statfs_mutex);

	rv = statfs(realpath, &st);
	if (!rv) {
		statfs_cache.block_size = st.f_bsize;
		statfs_cache.blocks = st.f_blocks;
		statfs_cache.blocks_free = st.f_bavail;
		statfs_cache.files = st.f_files;
		statfs_cache.files_free = st.f_ffree;
		statfs_cache.namelen = st.f_namelen;
	}

	pthread_mutex_unlock(&statfs_mutex);
}

static void do_fake_statfs(void)
{
	DEBUG("statfs: faked\n");

	pthread_mutex_lock(&statfs_mutex);

	statfs_cache.block_size = 4096;
	statfs_cache.blocks = 1;
	statfs_cache.blocks_free = 0;
	statfs_cache.files = 1;
	statfs_cache.files_free = 0;
	statfs_cache.namelen = 260;

	pthread_mutex_unlock(&statfs_mutex);
}

int __inline__ medium_available(void)
{
	int fd = -1;
	int res = 0;
	int retval = 0;
	static pthread_mutex_t ioctl_mutex = PTHREAD_MUTEX_INITIALIZER;

	if (!is_cdrom)
		return 1;

	pthread_mutex_lock(&ioctl_mutex);

	if ((fd = open(device, O_RDONLY | O_NONBLOCK)) == -1) {
		retval = 1;
		goto theend;
	}
	res = ioctl(fd, CDROM_DRIVE_STATUS, CDSL_CURRENT);
	close(fd);
	if (res == -1) {
		retval = 1;
		goto theend;
	}

	retval = res == 4;
	if (retval == 0) {
		do_fake_statfs();
	}

      theend:
	pthread_mutex_unlock(&ioctl_mutex);
	DEBUG("medium_available %d\n", retval);
	return retval;
}


int __inline__ media_changed(void)
{
	int fd = -1;
	static int last_changed = 0;
	int changed, status;
	int retval;
	static pthread_mutex_t ioctl_mutex = PTHREAD_MUTEX_INITIALIZER;

	if (!is_cdrom)
		return 0;

	pthread_mutex_lock(&ioctl_mutex);

	if ((fd = open(device, O_RDONLY | O_NONBLOCK)) == -1) {
		retval = 1;
		goto theend;
	}

	changed = ioctl(fd, CDROM_MEDIA_CHANGED, CDSL_CURRENT);
	status = ioctl(fd, CDROM_DRIVE_STATUS, CDSL_CURRENT);

	close(fd);

	DEBUG("media_changed ioctls: changed: %d, status: %d\n", changed,
	      status);
	if (changed == -1 || status == -1) {
		retval = 1;
		goto theend;
	}

	if (last_changed != changed || (changed == 1 && status == 4)) {
		last_changed = changed;
		retval = 1;
		goto theend;
	}

	retval = 0;;

      theend:
	pthread_mutex_unlock(&ioctl_mutex);
	DEBUG("mediachanged: retval=%d\n", retval);
	return retval;
}

void timeout_handler(void){
  // increase last_access_tv

  struct timeval tv;
  gettimeofday(&tv, 0);

  memcpy(&last_access_tv, &tv, sizeof(struct timeval));
}

void do_umount(void)
{				/* doumount */
  DEBUG("check if umount needed\n");
	if (mounted) {
		DEBUG("umount\n");
		if (umount(mountpoint) == 0) {
		  mounted = 0;
		  DEBUG("umount success on mountpoint\n");
		}
		else {
		  if (umount(device) == 0) {
		    mounted = 0;
		    DEBUG("umount success on mountpoint\n");
		  }
		}
	}
}

void umount_timeout_handler(void)
{
  // loops in his own thread until umount was successful
  struct timeval tv;

  while (mounted == 1)
    {
      DEBUG("check if umount may necessary\n");
      gettimeofday(&tv, 0);
      pthread_mutex_lock(&mount_mutex);

      if ((tv.tv_sec == last_access_tv.tv_sec && tv.tv_usec - last_access_tv.tv_usec > UMOUNT_TIMEOUT) ||
	  (tv.tv_sec - last_access_tv.tv_sec == 1 && abs(last_access_tv.tv_usec - tv.tv_usec) > UMOUNT_TIMEOUT) ||
	  tv.tv_sec - last_access_tv.tv_sec > 1)
	{
	  DEBUG("call do_umount\n");
	  do_umount();
	  pthread_mutex_unlock(&mount_mutex);
	}
      else
	{
	  pthread_mutex_unlock(&mount_mutex);
	  DEBUG("call sleep\n");
	  usleep(UMOUNT_TIMEOUT);
	}
    }
  pthread_exit(0);
}

int __inline__ do_mount(void)
{
  // needs to be called with given pthread_mutex_lock(&mount_mutex)
	static int last_mount_succ = 1;
	static struct timeval last_mount_tv;
	int res;

	if (mounted) {
		res = 0;
		DEBUG("already mounted\n");
		goto theend;
	}
	if (!medium_available()) {
		errno = ENOMEDIUM;
		res = -1;
		DEBUG("no medium\n");
		goto theend;
	}

	if (last_mount_succ == 0) {
		struct timeval tv;
		DEBUG("last mount was not successful\n");
		gettimeofday(&tv, 0);
		DEBUG("now: %ld %ld; last_mount: %ld %ld\n", tv.tv_sec,
		      tv.tv_usec, last_mount_tv.tv_sec,
		      last_mount_tv.tv_usec);
		if ((tv.tv_sec == last_mount_tv.tv_sec
				&& tv.tv_usec - last_mount_tv.tv_usec > REMOUNT_TIMEOUT) ||
				(tv.tv_sec - last_mount_tv.tv_sec == 1 &&
				abs(last_mount_tv.tv_usec - tv.tv_usec) > REMOUNT_TIMEOUT) ||
				tv.tv_sec - last_mount_tv.tv_sec > 1) {
			DEBUG("mounting again\n");
		} else {
			DEBUG("not mounting\n");
			errno = ENOENT;
			res = -1;
			memcpy(&last_mount_tv, &tv,
			       sizeof(struct timeval));
			goto theend;
		}
	}

	DEBUG("mounting\n");
	res = mount(device, mountpoint, filesystem, autofs_mountoptions, mountdata);
	if (res != 0 && autofs_mountoptions == 0) {
	  DEBUG("mounting failed, second attempt\n");
	  res = mount(device, mountpoint, filesystem,
		      MS_RDONLY | MS_NOSUID | MS_NODEV, mountdata);
	}
	if (res == 0) {
		do_statfs();
		mounted = 1;
		last_mount_succ = 1;
		pthread_create(&helper_thread, NULL, umount_timeout_handler, NULL);
		helper_return = pthread_detach(helper_thread);
		DEBUG("helper thread detached\n");
	} else {
		do_fake_statfs();
		gettimeofday(&last_mount_tv, 0);
		last_mount_succ = 0;
	}

      theend:
	DEBUG("mount finished\n");
	return res;
}

#define MOUNT if ( (res=do_mount())==-1 ) return res;

static int autofs_getattr(const char *path, struct stat *stbuf)
{
	int res;
	static pthread_mutex_t cache_mutex = PTHREAD_MUTEX_INITIALIZER;
	static char cache_path[PATH_MAX] = "";
	static struct stat cache_buf;

	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("getattr %s -> %s (cached)\n", path, cache_path);

	pthread_mutex_lock(&cache_mutex);

	if (!media_changed() && strcmp(path, cache_path) == 0) {
		DEBUG("getattr using cache\n");
		memcpy(stbuf, &cache_buf, sizeof(struct stat));
		pthread_mutex_unlock(&cache_mutex);
		return 0;
	}

	pthread_mutex_lock(&mount_mutex);
	res = do_mount();
	if (res == -1 && strcmp(path, "/") != 0) {
		pthread_mutex_unlock(&cache_mutex);
		timeout_handler();
		pthread_mutex_unlock(&mount_mutex);
		return -ENOENT;
	}

	if (lstat(realpath, stbuf) == -1) {
		pthread_mutex_unlock(&cache_mutex);
		timeout_handler();
		pthread_mutex_unlock(&mount_mutex);
		return -errno;
	}

	if (res == -1) {	/* implies "/" if we get here */
		stbuf->st_atime = stbuf->st_mtime = stbuf->st_ctime = 0;
		stbuf->st_blocks = 14;
		stbuf->st_size = 7168;
		stbuf->st_nlink = 4;
	}

	strncpy(cache_path, path, PATH_MAX);
	memcpy(&cache_buf, stbuf, sizeof(struct stat));
	pthread_mutex_unlock(&cache_mutex);

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_readlink(const char *path, char *buf, size_t size)
{
	int res;

	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("readlink %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = readlink(realpath, buf, size - 1);
	if (res == -1) {
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	buf[res] = '\0';
	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}


static int autofs_getdir(const char *path, fuse_dirh_t h,
			 fuse_dirfil_t filler)
{
	DIR *dp;
	struct dirent *de;

	int res = 0;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("getdir %s\n", path);

	pthread_mutex_lock(&mount_mutex);
	res = do_mount();
	if (res == -1 && strcmp(path, "/") != 0)
	  {
	    timeout_handler();
	    pthread_mutex_unlock(&mount_mutex);
	    return -errno;
	  }

	dp = opendir(realpath);
	if (dp == NULL){
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	while ((de = readdir(dp)) != NULL) {
		res = filler(h, de->d_name, de->d_type);
		if (res != 0)
			break;
	}

	closedir(dp);
	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return res;
}

static int autofs_mknod(const char *path, mode_t mode, dev_t rdev)
{
	int res;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("mknod %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = mknod(realpath, mode, rdev);
	if (res == -1) {
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}
	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_mkdir(const char *path, mode_t mode)
{
	int res;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("mkdir %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = mkdir(realpath, mode);
	if (res == -1){
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_unlink(const char *path)
{
	int res;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("unlink %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = unlink(realpath);
	if (res == -1) {
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_rmdir(const char *path)
{
	int res;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("getattr %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = rmdir(realpath);
	if (res == -1) {
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_symlink(const char *from, const char *to)
{
	int res;
	char realfrom[PATH_MAX];
	char realto[PATH_MAX];
	snprintf(realfrom, PATH_MAX, "%s%s", mountpoint, from);
	snprintf(realto, PATH_MAX, "%s%s", mountpoint, to);

	DEBUG("symlink %s -> %s\n", from, to);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = symlink(realfrom, realto);
	if (res == -1){
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_rename(const char *from, const char *to)
{
	int res;
	char realfrom[PATH_MAX];
	char realto[PATH_MAX];
	snprintf(realfrom, PATH_MAX, "%s%s", mountpoint, from);
	snprintf(realto, PATH_MAX, "%s%s", mountpoint, to);

	DEBUG("rename %s -> %s\n", from, to);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = rename(realfrom, realto);
	if (res == -1){
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_link(const char *from, const char *to)
{
	int res;
	char realfrom[PATH_MAX];
	char realto[PATH_MAX];
	snprintf(realfrom, PATH_MAX, "%s%s", mountpoint, from);
	snprintf(realto, PATH_MAX, "%s%s", mountpoint, to);

	DEBUG("link %s -> %s\n", from, to);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = link(realfrom, realto);
	if (res == -1) {
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_chmod(const char *path, mode_t mode)
{
	int res;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("chmod %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = chmod(realpath, mode);
	if (res == -1){
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_chown(const char *path, uid_t uid, gid_t gid)
{
	int res;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("chown %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = lchown(realpath, uid, gid);
	if (res == -1){
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_truncate(const char *path, off_t size)
{
	int res;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("truncate %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = truncate(realpath, size);
	if (res == -1){
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_utime(const char *path, struct utimbuf *buf)
{
	int res;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("utime %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = utime(realpath, buf);
	if (res == -1){
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}


static int autofs_open(const char *path, int flags)
{
	int res;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("open %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT res = open(realpath, flags);
	if (res == -1){
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	close(res);
	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return 0;
}

static int autofs_read(const char *path, char *buf, size_t size,
		       off_t offset)
{
	int fd;
	int res;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("read %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT fd = open(realpath, O_RDONLY);
	if (fd == -1){
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	res = pread(fd, buf, size, offset);
	if (res == -1)
		res = -errno;
	close(fd);

	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return res;
}

static int autofs_write(const char *path, const char *buf, size_t size,
			off_t offset)
{
	int fd;
	int res;
	char realpath[PATH_MAX];
	snprintf(realpath, PATH_MAX, "%s%s", mountpoint, path);

	DEBUG("write %s\n", path);
	pthread_mutex_lock(&mount_mutex);
	MOUNT fd = open(realpath, O_WRONLY);
	if (fd == -1){
	  timeout_handler();
	  pthread_mutex_unlock(&mount_mutex);
	  return -errno;
	}

	res = pwrite(fd, buf, size, offset);
	if (res == -1)
		res = -errno;

	close(fd);
	timeout_handler();
	pthread_mutex_unlock(&mount_mutex);
	return res;
}

static int autofs_statfs(struct fuse_statfs_compat1 *fst)
{
	DEBUG("statfs\n");

	pthread_mutex_lock(&mount_mutex);
	if (is_cdrom && medium_available())
		do_statfs();

	pthread_mutex_lock(&statfs_mutex);
	memcpy(fst, &statfs_cache, sizeof(struct fuse_statfs_compat1));
	pthread_mutex_unlock(&statfs_mutex);
	pthread_mutex_unlock(&mount_mutex);

	return 0;
}

static struct fuse_operations_compat1 autofs_oper = {
	getattr:autofs_getattr,
	readlink:autofs_readlink,
	getdir:autofs_getdir,
	mknod:autofs_mknod,
	mkdir:autofs_mkdir,
	symlink:autofs_symlink,
	unlink:autofs_unlink,
	rmdir:autofs_rmdir,
	rename:autofs_rename,
	link:autofs_link,
	chmod:autofs_chmod,
	chown:autofs_chown,
	truncate:autofs_truncate,
	utime:autofs_utime,
	open:autofs_open,
	read:autofs_read,
	write:autofs_write,
	statfs:autofs_statfs,
};

void usage(void)
{
	fprintf(stderr, "autofs dev mountpoint tempmointpoint fs ro|rw mount-options external_mountoptions\n");
	exit(1);
}


int main(int argc, char *argv[])
{
	int fd;

	if (argc != 8) {
	  usage();
	}
	if (argv[1] == NULL)
		usage();
	device = argv[1];
	if (argv[2] == NULL)
		usage();
	external_mountpoint = argv[2];
	if (argv[3] == NULL)
		usage();
	mountpoint = argv[3];
	if (argv[4] == NULL)
		usage();
	filesystem = argv[4];
	if (argv[5] == NULL)
		usage();
	if (strcmp(argv[5], "ro") == 0) {
		autofs_mountoptions = MS_RDONLY | MS_NOSUID | MS_NODEV;
	} else if (strcmp(argv[5], "rw") == 0) {
		autofs_mountoptions = 0;
	}
	mountdata = argv[6];
	external_mountoptions = argv[7];
	umount(mountpoint);
	umount(device);
	do_fake_statfs();

	if ((fd = open(device, O_RDONLY | O_NONBLOCK)) != -1 &&
	    ioctl(fd, CDROM_DRIVE_STATUS, CDSL_CURRENT) != -1) {
		DEBUG("device %s is cd drive\n", device);
		is_cdrom = 1;
	} else {
		DEBUG("device %s is not a cd drive\n", device);
	}
	if (fd != -1)
		close(fd);

	//char* external_mountptions=0
	//external_mountptions="-o"

	int fuse_argc = 4;
	char *fuse_argv[] = { "autofs", "-o", external_mountoptions, external_mountpoint, 0 };
	fuse_main_compat1(fuse_argc, fuse_argv, &autofs_oper);
	return 0;
}
