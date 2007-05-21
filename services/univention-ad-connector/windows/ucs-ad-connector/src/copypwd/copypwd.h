/***************************************************************************
 * 
 * File:    copypwd.h
 * 
 * Purpose: common definitions
 * 
 * Date:    January 4, 2002
 *
 * (C) Todd Sabin 1997,1998,2000  All rights reserved.
 * (C) SystemTools Software, Inc. All rights reserved.  http://www.systemtools.com
 * 
 * This program is a minor modification of the original work of Todd Sabin's
 * "pwdump2" utility, and as such is subject to redistribution and modification
 * terms only under the terms of the GNU license agreement.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 * 
 ***************************************************************************/

#ifndef PWDUMP2_H
#define PWDUMP2_H

#define DUMP_PIPE_SIZE 1024

typedef HINSTANCE (WINAPI *pLoadLib_t) (CHAR *);
typedef HINSTANCE (WINAPI *pGetProcAddr_t) (HINSTANCE, CHAR *);
typedef HINSTANCE (WINAPI *pFreeLib_t) (HINSTANCE);
typedef int (*pDumpSam_t) (CHAR *, CHAR *);

typedef struct _remote_info {
    pLoadLib_t      pLoadLibrary;
    pGetProcAddr_t pGetProcAddress;
    pFreeLib_t     pFreeLibrary;
    CHAR  szDllName[MAX_PATH+1];
    CHAR  szProcName[MAX_PATH+1];
    CHAR  szPipeName[MAX_PATH+1];
	CHAR  szCurrentDirectory[MAX_PATH+1];
} REMOTE_INFO;

#endif
