/***************************************************************************
 * 
 * File:    getpid.c
 * 
 * Purpose: Find the pid of a process, given its name
 * 
 * Date:    Thu Mar 23 23:21:32 2000
 * 
 * Copyright (c) 2000 Todd A. Sabin, all rights reserved
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


#include <windows.h>
#include <winnt.h>

#include <stdlib.h>

typedef unsigned long NTSTATUS;

typedef struct {
    USHORT Length;
    USHORT MaxLen;
    USHORT *Buffer;
} UNICODE_STRING;


NTSTATUS (__stdcall *NtQuerySystemInformation)(
		IN ULONG SysInfoClass,
                IN OUT PVOID SystemInformation,
                IN ULONG SystemInformationLength,
                OUT PULONG RetLen
                );

LONG (__stdcall *RtlCompareUnicodeString)(
		IN UNICODE_STRING *,
                IN UNICODE_STRING *,
                IN ULONG CaseInsensitve
                );

struct process_info {
    ULONG NextEntryDelta;
    ULONG ThreadCount;
    ULONG Reserved1[6];
    LARGE_INTEGER CreateTime;
    LARGE_INTEGER UserTime;
    LARGE_INTEGER KernelTime;
    UNICODE_STRING ProcessName;
    ULONG BasePriority;
    ULONG ProcessId;
    // etc.
};

//
// Find the pid of LSASS.EXE
//
int
find_pid (DWORD *ppid)
{
    HINSTANCE hNtDll;
    NTSTATUS rc;
    ULONG ulNeed = 0;
    void *buf = NULL;
    size_t len = 0;
    int ret = 0;

    hNtDll = LoadLibrary ("NTDLL");
    if (!hNtDll)
        return 0;

    NtQuerySystemInformation = (void*)GetProcAddress (hNtDll, "NtQuerySystemInformation");
    if (!NtQuerySystemInformation)
        return 0;

    RtlCompareUnicodeString = (void*)GetProcAddress (hNtDll, "RtlCompareUnicodeString");
    if (!RtlCompareUnicodeString)
        return 0;

    do {
        len += 2000;
        buf = realloc (buf, len);
        if (!buf)
            return 0;
        rc = NtQuerySystemInformation (5, buf, len, &ulNeed);
    } while (rc == 0xc0000004);  // STATUS_INFO_LEN_MISMATCH

    if (rc <0) {
        free (buf);
        return 0;
    }

    //
    // Ok, now slog through the data looking for our guy.
    //
    {
        struct process_info *p = (struct process_info *)buf;
        int done = 0;
        UNICODE_STRING lsass = { 18, 20, L"LSASS.EXE" };

        while (!done) {
            if ((p->ProcessName.Buffer != 0)
                && (RtlCompareUnicodeString (&lsass, &p->ProcessName, 1) == 0)) {
                    *ppid = p->ProcessId;
                    ret = 1;
                    goto exit;
            }
            done = p->NextEntryDelta == 0;
            p = (struct process_info *)(((char *)p) + p->NextEntryDelta);
        }
    }

 exit:
    free (buf);
    FreeLibrary (hNtDll);

    return ret;
}
