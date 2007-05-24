/*
   Unix SMB/CIFS implementation.
   Samba utility functions
   Copyright (C) Andrew Tridgell 1992-1998
   Copyright (C) Jeremy Allison 2001
   Copyright (C) Simo Sorce 2001

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
*/

#include "includes.h"

void *smb_xmalloc(size_t size)
{
  void *p;
  if (size == 0) {
    fprintf ( stderr, "malloc called with zero size.\n" );
    exit (1);
  }
  if ((p = malloc(size)) == NULL) {
    fprintf ( stderr, "malloc failed.\n" );
    exit (1);
  }
  return p;
}

char *smb_xstrdup(const char *s)
{
        char *s1 = strdup(s);
        if (!s1) {
	  fprintf ( stderr, "strdup failed.\n" );
	  exit (1);
	}
        return s1;
}

void *memdup(const void *p, size_t size)
{
        void *p2;
        if (size == 0)
                return NULL;
        p2 = malloc(size);
        if (!p2)
                return NULL;
        memcpy(p2, p, size);
        return p2;
}
