/***************************************************************************
 * File:    getsetpw.c
 *
 * Purpose: Either dump the name/password hashes of all user accounts to a 
 *          file (dump mode), or read the contents of a file and set the
 *          password back
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

#include <windows.h>
#include <winnt.h>
#include "ntsecapi.h"
#include "copypwd.h"
#include <stdio.h>
#include <stdarg.h>
#include <Lmaccess.h>
#include <Lmapibuf.h>


static HINSTANCE hSamsrv;

typedef DWORD HUSER;
typedef DWORD HSAM;
typedef DWORD HDOMAIN;
typedef DWORD HUSER;

typedef struct _sam_user_info 
{
    DWORD rid;
    LSA_UNICODE_STRING name;
} SAM_USER_INFO;

typedef struct _sam_user_enum 
{
    DWORD count;
    SAM_USER_INFO *users;
} SAM_USER_ENUM;

//
// Samsrv functions
//
typedef NTSTATUS (WINAPI *SamIConnect_t) (DWORD, HSAM*, DWORD, DWORD);
typedef NTSTATUS (WINAPI *SamrOpenDomain_t) (HSAM, DWORD dwAccess, PSID, HDOMAIN*);
typedef NTSTATUS (WINAPI *SamrOpenUser_t) (HDOMAIN, DWORD dwAccess, DWORD, HUSER*);
typedef NTSTATUS (WINAPI *SamrEnumerateUsersInDomain_t) (HDOMAIN, DWORD*, DWORD, SAM_USER_ENUM**, DWORD, PVOID);
typedef NTSTATUS (WINAPI *SamrQueryInformationUser_t) (HUSER, DWORD, PVOID);
typedef HLOCAL   (WINAPI *SamIFree_SAMPR_USER_INFO_BUFFER_t) (PVOID, DWORD);
typedef HLOCAL   (WINAPI *SamIFree_SAMPR_ENUMERATION_BUUFER_t) (SAM_USER_ENUM*);
typedef NTSTATUS (WINAPI *SamrCloseHandle_t) (DWORD*);
typedef NTSTATUS (WINAPI *SamrSetInformationUser_t) (HUSER, DWORD, PVOID);
  
#define SAM_USER_INFO_PASSWORD_OWFS 0x12

//  Samsrv function pointers
static SamIConnect_t pSamIConnect;
static SamrOpenDomain_t pSamrOpenDomain;
static SamrOpenUser_t pSamrOpenUser;
static SamrQueryInformationUser_t pSamrQueryInformationUser;
static SamrSetInformationUser_t pSamrSetInformationUser;
static SamrEnumerateUsersInDomain_t pSamrEnumerateUsersInDomain;
static SamIFree_SAMPR_USER_INFO_BUFFER_t pSamIFree_SAMPR_USER_INFO_BUFFER;
static SamIFree_SAMPR_ENUMERATION_BUUFER_t pSamIFree_SAMPR_ENUMERATION_BUFFER;
static SamrCloseHandle_t pSamrCloseHandle;


#include <windows.h>
#include <winnt.h>

#include <stdlib.h>

typedef unsigned long NTSTATUS;




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

// Load DLLs and GetProcAddresses
BOOL LoadFunctions (void)
{
    hSamsrv = LoadLibrary ("samsrv.dll");

    pSamIConnect = (SamIConnect_t) GetProcAddress (hSamsrv, "SamIConnect");
    pSamrOpenDomain = (SamrOpenDomain_t) GetProcAddress (hSamsrv, "SamrOpenDomain");
    pSamrOpenUser = (SamrOpenUser_t) GetProcAddress (hSamsrv, "SamrOpenUser");
    pSamrQueryInformationUser = (SamrQueryInformationUser_t) GetProcAddress (hSamsrv, "SamrQueryInformationUser");
	pSamrSetInformationUser = (SamrSetInformationUser_t) GetProcAddress (hSamsrv, "SamrSetInformationUser");
    pSamrEnumerateUsersInDomain = (SamrEnumerateUsersInDomain_t) GetProcAddress (hSamsrv, "SamrEnumerateUsersInDomain");
    pSamIFree_SAMPR_USER_INFO_BUFFER = (SamIFree_SAMPR_USER_INFO_BUFFER_t) GetProcAddress (hSamsrv, "SamIFree_SAMPR_USER_INFO_BUFFER");
    pSamIFree_SAMPR_ENUMERATION_BUFFER = (SamIFree_SAMPR_ENUMERATION_BUUFER_t) GetProcAddress (hSamsrv, "SamIFree_SAMPR_ENUMERATION_BUFFER");
    pSamrCloseHandle = (SamrCloseHandle_t) GetProcAddress (hSamsrv, "SamrCloseHandle");

    return ((pSamIConnect != NULL)
            && (pSamrOpenDomain != NULL)
            && (pSamrOpenUser != NULL)
            && (pSamrQueryInformationUser != NULL)
			&& (pSamrSetInformationUser != NULL)
            && (pSamrEnumerateUsersInDomain != NULL)
            && (pSamIFree_SAMPR_USER_INFO_BUFFER != NULL)
            && (pSamIFree_SAMPR_ENUMERATION_BUFFER != NULL)
            && (pSamrCloseHandle != NULL));
}

// Some older versions of _snprintf may not null-terminate the string.
static my_snprintf (char *buf, size_t len, const char *format, ...)
{
    va_list args;
    va_start (args, format);
    _vsnprintf (buf, len-1, format, args);
    va_end (args);
    buf[len-1] = 0;
}
#undef _snprintf
#define _snprintf my_snprintf

// Send text down the pipe
void SendText (HANDLE hPipe, char *szText)
{
    char szBuffer[1000];
    DWORD dwWritten;

    if (!WriteFile (hPipe, szText, strlen (szText), &dwWritten, NULL))
    {
        _snprintf (szBuffer, sizeof (szBuffer), "WriteFile failed: %d\nText: %s", GetLastError (), szText);
        OutputDebugString (szBuffer);
    }
}

// Print out info for one user
void DumpInfo (HANDLE hPipe, LPCTSTR lpszName, PVOID pData)
{
    // Should really just check buffer size instead of this __try
    __try
    {
        PBYTE p = (PBYTE) pData;
        char szBuffer[1000];

        _snprintf (szBuffer, sizeof (szBuffer), "%s:"
                   "%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x"
                   "%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x\n",
                   lpszName,
				   p[0],  p[1],  p[2],  p[3],  p[4],  p[5],  p[6],  p[7],
                   p[8],  p[9],  p[10], p[11], p[12], p[13], p[14], p[15],
                   p[16], p[17], p[18], p[19], p[20], p[21], p[22], p[23],
                   p[24], p[25], p[26], p[27], p[28], p[29], p[30], p[31]);
        SendText (hPipe, szBuffer);
    }
    __except (EXCEPTION_EXECUTE_HANDLER)
    {
    }
}

// Set the passwords for accounts in input file
int __declspec(dllexport) SetPass (char *szPipeName, char *szCurrentDirectory)
{
	HSAM hSam = 0;
	HUSER hUser = 0;
	HDOMAIN hDomain = 0;
	POLICY_ACCOUNT_DOMAIN_INFO* pDomainInfo;
	LSA_HANDLE lsaHandle = 0;
	PLSA_UNICODE_STRING pSystemName = NULL;
	LSA_OBJECT_ATTRIBUTES objAttrib;
	HANDLE hPipe;
	FILE* stream;
	NTSTATUS rc;
	CHAR szBuffer[300];
    CHAR data[1024];
	CHAR pwd[32];
	CHAR user[256];
	WCHAR wuser[256];
	CHAR hash[256];
	CHAR InputFile[MAX_PATH+1];
	CHAR PwdByte[3];
	CHAR* pos;
	CHAR* stopstring;
	DWORD NetErr, RID, LineCount;
	PUSER_INFO_3 ui3;
	int delim = ':';
	int i, intTemp, HashIndex;
	int theRc = 1; // set to fail initially

	// Open the output pipe
    hPipe = CreateFile (szPipeName, GENERIC_WRITE, 0, NULL, 
                        OPEN_EXISTING, FILE_FLAG_WRITE_THROUGH, NULL);
    if (hPipe == INVALID_HANDLE_VALUE)
    {
        _snprintf (szBuffer, sizeof (szBuffer), "Failed to open output pipe(%s): %d\n",
                   szPipeName, GetLastError ());
        OutputDebugString (szBuffer);
        goto exit;
    }

    if (!LoadFunctions ())
    {
        SendText (hPipe, "Failed to load functions\n");
        goto exit;
    }

    // Open the Policy database
    memset (&objAttrib, 0, sizeof (objAttrib));
    objAttrib.Length = sizeof (objAttrib);

    rc = LsaOpenPolicy (pSystemName, &objAttrib, POLICY_ALL_ACCESS, &lsaHandle);
    if (rc < 0)
    {
        _snprintf (szBuffer, sizeof (szBuffer), "LsaOpenPolicy failed : 0x%08X", rc);
        SendText (hPipe, szBuffer);
        OutputDebugString (szBuffer);
        goto exit;
    }

    rc = LsaQueryInformationPolicy (lsaHandle, PolicyAccountDomainInformation, &pDomainInfo);
    if (rc < 0)
    {
        _snprintf (szBuffer, sizeof (szBuffer), "LsaQueryInformationPolicy failed : 0x%08X", rc);
        SendText (hPipe, szBuffer);
        OutputDebugString (szBuffer);
        goto exit;
    }

    // Connect to the SAM database
    rc = pSamIConnect (0, &hSam, MAXIMUM_ALLOWED, 1);
    if (rc < 0)
    {
        _snprintf (szBuffer, sizeof (szBuffer), "SamConnect failed : 0x%08X", rc);
        SendText (hPipe, szBuffer);
        OutputDebugString (szBuffer);
        goto exit;
    }

    rc = pSamrOpenDomain (hSam, 0xf07ff, pDomainInfo->DomainSid, &hDomain);
    if (rc < 0)
    {
        _snprintf (szBuffer, sizeof (szBuffer), "SamOpenDomain failed : 0x%08X\n", rc);
        SendText (hPipe, szBuffer);
        OutputDebugString (szBuffer);
        hDomain = 0;
        goto exit;
    }

	// todo: it would be cool to setup an .INI file to get file name and other settings
	// 'we' might do this one day if this turns out to be something popular, or if we
	// have other settings and options that we need.
	strcpy(InputFile, szCurrentDirectory);
	strcat(InputFile, "\\copypwd.txt");

	LineCount = 0;
	if ((stream = fopen(InputFile, "r")) != NULL)
	{
		while (1)
		{
			ZeroMemory(data, sizeof (data));
			if (fgets(data, sizeof(data), stream) == NULL)
				break;

			LineCount++;
			
			// find where the ":" is in the data for parsing out the user/password
			pos = strchr (data, delim);
		    if (pos == NULL )
			{
				_snprintf (szBuffer, sizeof (szBuffer), "Unable to parse line from input file : Line # %d\n", LineCount);
				SendText (hPipe, szBuffer);
				OutputDebugString (szBuffer);
				goto exit;
			}

			// initialize everything to zeros
			ZeroMemory(pwd, sizeof (pwd));
			ZeroMemory(user, sizeof (user));
			ZeroMemory(hash, sizeof (hash));
			ZeroMemory(wuser, sizeof (wuser));

			// first, copy the username out of the data
			strncpy(user, data, pos - data);
			// convert username to Unicode
			MultiByteToWideChar(CP_ACP, 0, user, -1, wuser, sizeof (wuser));
			// then, copy the password hash out
			strcpy(hash, pos + 1);

			// now, lookup the user on the local computer
			NetErr = NetUserGetInfo(NULL, wuser, 3, (LPBYTE*) &ui3);
			if (NetErr)
			{
				_snprintf (szBuffer, sizeof (szBuffer), "Unable to retrieve user information for %S : Error = %d\n", wuser, NetErr);
				SendText (hPipe, szBuffer);
				OutputDebugString (szBuffer);
				goto exit;
			}
			// save RID for later
			RID = ui3->usri3_user_id;
			// free memory from NetUserGetInfo call
			NetApiBufferFree(ui3);

			// now we convert the password hash back into binary; yes, there is probably a better
			// and fancier way to do this, but I wanted to be clear and safe
			HashIndex = 0;
			for (i=0; i < 32; i++)
			{
				PwdByte[0] = hash[HashIndex];
				PwdByte[1] = hash[HashIndex + 1];
				PwdByte[2] = '\0';
				intTemp = strtoul(PwdByte, &stopstring, 16); //base 16 (hex) 
				pwd[i] = intTemp;
				HashIndex = HashIndex + 2;
			}
						
			// now get the target user, based on the RID of the user
			rc = pSamrOpenUser (hDomain, MAXIMUM_ALLOWED, RID, &hUser);
			if (rc < 0)
            {
				_snprintf (szBuffer, sizeof (szBuffer), "SamrOpenUser for %S failed : 0x%08X\n", wuser, rc);
                SendText (hPipe, szBuffer);
                OutputDebugString (szBuffer);
                goto exit;
            }

			// and finally put the hash back into the user
			rc = pSamrSetInformationUser (hUser, SAM_USER_INFO_PASSWORD_OWFS, pwd);
			pSamrCloseHandle (&hUser);
			if (rc < 0)
			{
				_snprintf (szBuffer, sizeof (szBuffer), "SamrSetInformationUser for %S failed : 0x%08X\n", wuser, rc);
				SendText (hPipe, szBuffer);
				OutputDebugString (szBuffer);
			}
			else
			{
				// WARNING: THIS DOES NOT WORK !  In our testing, trying to set this flag
				// resulted in a reboot of the server.
				//ui3->usri3_password_expired = 0; // 1 will force a password change
				//NetErr = NetUserSetInfo(NULL, wuser, 3, (LPBYTE) &ui3, NULL);
				_snprintf (szBuffer, sizeof (szBuffer), "Set password for user %S\n", wuser);
				SendText (hPipe, szBuffer);
				OutputDebugString (szBuffer);
			}
		}	
		fclose(stream);
	}
	else
	{
		_snprintf (szBuffer, sizeof (szBuffer), "Unable to open input file %s", InputFile);
        SendText (hPipe, szBuffer);
        OutputDebugString (szBuffer);
		goto exit;
	}

	theRc = 0;

exit:
	if (hDomain)
        pSamrCloseHandle (&hDomain);
    if (hSam)
        pSamrCloseHandle (&hSam);
    if (lsaHandle)
        LsaClose (lsaHandle);
    if (hPipe)
    {
        FlushFileBuffers (hPipe);
        CloseHandle (hPipe);
    }
    if (hSamsrv)
        FreeLibrary (hSamsrv);

    return theRc;
}


// Dump the SAM contents to a file.
int __declspec(dllexport) DumpSam (char *szPipeName, char *szCurrentDirectory)
{
    int i;
    HANDLE hPipe;
    LSA_OBJECT_ATTRIBUTES objAttrib;
    LSA_HANDLE lsaHandle = 0;
    PLSA_UNICODE_STRING pSystemName = NULL;
    POLICY_ACCOUNT_DOMAIN_INFO* pDomainInfo;
    NTSTATUS rc, enum_rc;
    TCHAR szBuffer[300];
    HSAM hSam = 0;
    HDOMAIN hDomain = 0;
    HUSER hUser = 0;
	DWORD dwEnum = 0;
    DWORD dwNumRet;
    SAM_USER_ENUM *pEnum = NULL;
	PVOID pUserInfo = 0;
    CHAR data[1024];
	FILE* stream;
	CHAR InputFile[MAX_PATH+1];
	DWORD rid;

    int theRc = 1; // set to fail initially
	struct _iobuf * fp;

	// Open the output pipe
    hPipe = CreateFile (szPipeName, GENERIC_WRITE, 0, NULL, 
                        OPEN_EXISTING, FILE_FLAG_WRITE_THROUGH, NULL);
    if (hPipe == INVALID_HANDLE_VALUE)
    {
		_snprintf (szBuffer, sizeof (szBuffer), "Failed to open output pipe(%s): %d\n",
                   szPipeName, GetLastError ());
        OutputDebugString (szBuffer);
        goto exit;
    }
	
    

    if (!LoadFunctions ())
    {
        SendText (hPipe, "Failed to load functions\n");
        goto exit;
    }

	// Open the Policy database
    memset (&objAttrib, 0, sizeof (objAttrib));
    objAttrib.Length = sizeof (objAttrib);

    rc = LsaOpenPolicy (pSystemName, &objAttrib, POLICY_ALL_ACCESS, &lsaHandle);
    if (rc < 0)
    {
	    _snprintf (szBuffer, sizeof (szBuffer), "LsaOpenPolicy failed : 0x%08X", rc);
        SendText (hPipe, szBuffer);
        OutputDebugString (szBuffer);
        goto exit;
    }

    rc = LsaQueryInformationPolicy (lsaHandle, PolicyAccountDomainInformation, &pDomainInfo);
    if (rc < 0)
    {
        _snprintf (szBuffer, sizeof (szBuffer), "LsaQueryInformationPolicy failed : 0x%08X", rc);
        SendText (hPipe, szBuffer);
        OutputDebugString (szBuffer);
        goto exit;
    }

    // Connect to the SAM database
    rc = pSamIConnect (0, &hSam, MAXIMUM_ALLOWED, 1);
    if (rc < 0)
    {
        _snprintf (szBuffer, sizeof (szBuffer), "SamConnect failed : 0x%08X", rc);
        SendText (hPipe, szBuffer);
        OutputDebugString (szBuffer);
        goto exit;
    }

    rc = pSamrOpenDomain (hSam, 0xf07ff, pDomainInfo->DomainSid, &hDomain);
    if (rc < 0)
    {
        _snprintf (szBuffer, sizeof (szBuffer), "SamOpenDomain failed : 0x%08X\n", rc);
        SendText (hPipe, szBuffer);
        OutputDebugString (szBuffer);
        hDomain = 0;
        goto exit;
    }

	strcpy(InputFile, szCurrentDirectory);
	strcat(InputFile, "\\copypwd.in.txt");

	if ((stream = fopen(InputFile, "r")) != NULL) 
	{
		CHAR szUserName[256];
		wchar_t wBuff[256];
		DWORD dwSize;

		ZeroMemory(data, sizeof (data));
		/* read the RID */
		if (fgets(data, sizeof(data), stream) == NULL) {
			theRc=3;
			goto exit;
		}

		rid = strtoul ( data, NULL, 10 );
		// Open the user (by Rid)
		rc = pSamrOpenUser (hDomain, MAXIMUM_ALLOWED, rid, &hUser);
		if (rc < 0)
		{
	
			_snprintf (szBuffer, sizeof (szBuffer), 
					   "SamrOpenUser(0x%x) failed : 0x%08X\n",
					   rid, rc);
			SendText (hPipe, szBuffer);
			OutputDebugString (szBuffer);
			theRc=1;
			goto exit;
		}

		// Get the password OWFs
		rc = pSamrQueryInformationUser (hUser, SAM_USER_INFO_PASSWORD_OWFS, &pUserInfo);
		if (rc < 0)
		{
			_snprintf (szBuffer, sizeof (szBuffer), "SamrQueryInformationUser failed : 0x%08X\n", rc);
			SendText (hPipe, szBuffer);
			OutputDebugString (szBuffer);
			pSamrCloseHandle (&hUser);
			hUser = 0;
			theRc=2;
			goto exit;
		}

                DumpInfo (hPipe, data, pUserInfo);

                // Free stuff
                pSamIFree_SAMPR_USER_INFO_BUFFER (pUserInfo, SAM_USER_INFO_PASSWORD_OWFS);
                pUserInfo = 0;
                pSamrCloseHandle (&hUser);
                hUser = 0;
                
            
		fclose(stream);
	}


    theRc = 0;

exit:
	// Clean up
    if (hUser)
        pSamrCloseHandle (&hUser);
    if (hDomain)
        pSamrCloseHandle (&hDomain);
    if (hSam)
        pSamrCloseHandle (&hSam);
    if (lsaHandle)
        LsaClose (lsaHandle);
    if (hPipe)
    {
        FlushFileBuffers (hPipe);
        CloseHandle (hPipe);
    }
    if (hSamsrv)
        FreeLibrary (hSamsrv);

    return theRc;
}

