/*
 * thinmount.c: - setuid wrapper for ltspfs, similar to lbmount from LTSP
 *
 * (c) 2007 Univention GmbH
 *
 * This software is distributed under the terms and conditions of the
 * GNU General Public License. See file GPL for the full text of the license.
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <pwd.h>
#include <mntent.h>
#include <limits.h>
#include <errno.h>
#include <getopt.h>

static char *mountprog = "/usr/bin/ltspfs";

int
fusemount (const char *path1, const char *path2)
{
  int status;
  pid_t child;
  char *null_env[] = { NULL };

  child = fork ();

  if (child == 0)
    {
      seteuid(0);
      execle (mountprog, mountprog, path1, path2, NULL, null_env);
    }
  else if (child > 0)
    {
      if (waitpid (child, &status, 0) < 0)
        {
          perror ("Error: wait() call failed");
          exit (1);
        }
    }
  else if (child < 0)
    {
      perror ("Error: fork() failed");
      exit (1);
    }

}

int
main (int argc, char **argv)
{
  int umount = 0;
  struct passwd *pwent;
  char *mountpoint = NULL;      /* the path to mount the block device into, e.g. /media/mallory/sda */
  char *blockdev = NULL;        /* the thin client device to be mounted, e.g. 10.200.3.65:/var/run/drives/ltspfs */
  char mediamount[PATH_MAX];    /* fully pathed mountpoint in /media */

  if (argc < 3)
    {
      fprintf (stderr, "Usage:\n");
      fprintf (stderr, "univention-ltspmount-wrapper <THINCLIENT_BLOCKDEVICE> <SERVER_MOUNTPOINT> :\n");
      fprintf (stderr, "Example:\n");
      fprintf (stderr, "univention-ltspmount-wrapper 192.168.40.20:/var/run/drives/usbdisk-sda1 /media/thinclients/thin04/usb:\n");
      exit (1);
    }      

  blockdev = strdup (argv[1]);
  if (!blockdev)
    {
      fprintf (stderr, "Error: couldn't get block device name");
      exit (1);
    }

  mountpoint = strdup (argv[2]);
  if (!mountpoint)
    {
      fprintf (stderr, "Error: couldn't get mountpoint");
      exit (1);
    }

  if (mkdir (mountpoint, 0777) != 0)
    {
      perror("Error: Couldn't create mount point. Please check permissions. fusermount needs a user-writable mount point.");
    }


  // This should likely be tightened to groups:fuse privileges later
  if (chmod (mountpoint, 0777) != 0)
    {
      perror("Error: Failed to modify permissions. fusermount needs a user-writable mount point.");
    }

  return fusemount (blockdev, mountpoint);
}
