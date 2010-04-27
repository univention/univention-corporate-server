/*
Copyright ©2008 foofus.net

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

#ifndef _LSASSTHREADSTUB_H_
#define _LSASSTHREADSTUB_H_

#include <windows.h>

#ifdef __cplusplus
extern "C"
{
#endif

typedef HINSTANCE (WINAPI *pLoadLibFunc)(char* );
typedef HINSTANCE (WINAPI *pGetProcAddrFunc)(HINSTANCE, char*);
typedef HINSTANCE (WINAPI *pFreeLibFunc)(HINSTANCE);
typedef	VOID (WINAPI *pOutputDebugStringFunc)(LPCSTR lpOutputString);

typedef int (*pGetHashFunc)(LPCTSTR, char*, BYTE*, DWORD, BOOL);

struct ThreadData
{
    pLoadLibFunc pLoadLibrary;
    pGetProcAddrFunc pGetProcAddress;
    pFreeLibFunc pFreeLibrary;
	pOutputDebugStringFunc pOutputDebugString;
    char szDllName[MAX_PATH];
    char szFuncName[16];
	char szPipeName[50];
	char szCurrentDirectory[MAX_PATH];
	DWORD dwKeyLength;
	BOOL bSkipHistories;
	BYTE byteKey[50];
};

SIZE_T GetLsaThreadFuncSize();
PVOID GetLsaThreadFuncPtr();


#ifdef __cplusplus
}
#endif

#endif
