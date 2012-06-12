/*
   Unix SMB/CIFS implementation.
   Password and authentication handling
   Copyright (C) Andrew Tridgell        1992-1998
   Copyright (C) Luke Kenneth Caseson Leighton  1998-1999
   Copyright (C) Jeremy Allison         1996-2001
   Copyright (C) Gerald (Jerry) Carter      2000

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

static void generate_random_sid(DOM_SID *sid)
{
  int i;
  uchar raw_sid_data[12];

  memset((char *)sid, '\0', sizeof(*sid));
  sid->sid_rev_num = 1;
  sid->id_auth[5] = 5;
  sid->num_auths = 0;
  sid->sub_auths[sid->num_auths++] = 21;

  generate_random_buffer(raw_sid_data, 12, True);
  for (i = 0; i < 3; i++)
    sid->sub_auths[sid->num_auths++] = IVAL(raw_sid_data, i*4);
}

char *sid_to_string(fstring sidstr_out, const DOM_SID *sid)
{
  char subauth[16];
  int i;
  uint32 ia;

  if (!sid) {
    strcpy(sidstr_out, "(NULL SID)");
    return sidstr_out;
  }

  /*
   * BIG NOTE: this function only does SIDS where the identauth is not >= 2^32
   * in a range of 2^48.
   */
  ia = (sid->id_auth[5]) +
    (sid->id_auth[4] << 8 ) +
    (sid->id_auth[3] << 16) +
    (sid->id_auth[2] << 24);

  sprintf(sidstr_out, "S-%u-%lu", (unsigned int)sid->sid_rev_num, (unsigned long)ia);

  for (i = 0; i < sid->num_auths; i++) {
    sprintf(subauth, "-%lu", (unsigned long)sid->sub_auths[i]);
    strcat(sidstr_out, subauth);
  }

  return sidstr_out;
}


int main ( int argc, char * argv[] ) {
  DOM_SID sid;
  fstring sid_str;
  int index_options;
  int help_flag=0;
  char help_text[] = "univention-newsid: Generates a new SID\n\n"
  "Syntax:\n"
  "\tunivention-newsid [options]\n\n"
  "Options:\n"
  "\t-h | --help:\n"
  "\tprint this usage message and exit program\n\n";
 
  
  if(argc >= 1) {
    for(index_options=1;index_options<argc;index_options++) {        
      if (strcmp(argv[index_options],"--help")==0 || strcmp(argv[index_options],"-h")==0) {
        help_flag=1;
      } else {
        fprintf(stdout, "illegal option: %s\n",argv[index_options]);
        help_flag=1;
      }
    }
  }

  if(help_flag==1) {
    fprintf(stdout,"%s",help_text);
    exit(0);
  }
  
 
  generate_random_sid( &sid );
  sid_to_string ( sid_str, &sid );

  fprintf ( stdout, "%s\n", sid_str );

  exit (0);
}
