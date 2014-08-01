/*
PV Drivers for Windows Xen HVM Domains
Copyright (C) 2009 Neocleus Inc., Amir Szekely (amir@neocleus.com)

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
*/

#include <windows.h>
#include <setupapi.h>

DWORD
__stdcall CoRequireReboot (
               IN     DI_FUNCTION               InstallFunction,
               IN     HDEVINFO                  DeviceInfoSet,
               IN     PSP_DEVINFO_DATA          DeviceInfoData,
               IN OUT PCOINSTALLER_CONTEXT_DATA Context
               )
{
	UNREFERENCED_PARAMETER(Context);

	OutputDebugString(TEXT("CoRequireReboot"));

	if (InstallFunction == DIF_INSTALLDEVICE)
	{
		SP_DEVINSTALL_PARAMS DevInstallParams;
		OutputDebugString(TEXT("  CoRequireReboot: DIF_INSTALLDEVICE"));
		DevInstallParams.cbSize = sizeof(SP_DEVINSTALL_PARAMS);
		
		if (SetupDiGetDeviceInstallParams(DeviceInfoSet, DeviceInfoData, &DevInstallParams))
		{
			OutputDebugString(TEXT("  CoRequireReboot: SetupDiGetDeviceInstallParams"));
			DevInstallParams.Flags |= DI_DONOTCALLCONFIGMG;
			DevInstallParams.Flags |= DI_NEEDREBOOT;
			if (SetupDiSetDeviceInstallParams(DeviceInfoSet, DeviceInfoData, &DevInstallParams))
			{
				OutputDebugString(TEXT("  CoRequireReboot: SetupDiSetDeviceInstallParams"));
			}
		}
	}

    return NO_ERROR;
}
