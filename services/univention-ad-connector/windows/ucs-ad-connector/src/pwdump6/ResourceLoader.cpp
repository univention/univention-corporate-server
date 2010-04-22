/******************************************************************************
pwdump6 - by fizzgig and the foofus.net group
Copyright (C) 2008 by fizzgig
http://www.foofus.net

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
******************************************************************************/
#include "resourceloader.h"

bool ResourceLoader::FileExists(char* szFile)
{
	try
	{
		std::fstream fin;
		fin.open(szFile, std::ios::in);
		if(fin.is_open())
		{
			fin.close();
			return true;
		}

		fin.close();
		return false;
	}
	catch(...)
	{
		return false;
	}
}

ResourceLoader::ResourceLoader(void)
{
	hRes = NULL;
	hResMem = NULL;
	dwResourceSize = 0;
	pData = NULL;
	szTempFilename = NULL;
}

ResourceLoader::~ResourceLoader(void)
{
	if (hResMem != NULL)
		FreeResource(hResMem);

	if (szTempFilename != NULL)
	{
		// Try to delete the file - failure is ok
		DeleteFile(szTempFilename);
		delete [] szTempFilename;
	}
}

bool ResourceLoader::UnpackResource(int nResourceID, char* szFilename)
{
	hRes = FindResource(NULL, MAKEINTRESOURCE(nResourceID), "bin");
	if (hRes == NULL)
	{
		printf("Unable to find resource %d in the executable\n", nResourceID);
		return false;;
	}
	hResMem = LoadResource(NULL, hRes);
	if (hResMem == NULL)
	{
		printf("Unable to load resource from the executable\n");
		return false;;
	}
	
	pData = (char*)LockResource(hResMem);
	if (pData == NULL)
	{
		printf("Unable to lock resource, exiting\n");
		return false;;
	}

	dwResourceSize = SizeofResource(NULL, hRes);

	// Copy the filename so we can delete it later
	size_t nLen = strlen(szFilename);
	szTempFilename = new char[nLen + 1];
	memset(szTempFilename, 0, nLen + 1);
	strncpy(szTempFilename, szFilename, nLen);

	if (!FileExists(szTempFilename))
	{
		std::ofstream outputFile(szTempFilename, std::ios::binary);
		outputFile.write((const char*)pData, dwResourceSize);
		outputFile.close();
	}
	else
	{
		printf("%s already exists, using existing file\n", szTempFilename);
	}

	return true;
}

