/* $Copyright$
 *  Copyright (C) Fujitsu Siemens Computers GmbH 2001, 2002, 2004, 2005, 2006, 2007
 *  All rights reserved
 */
#ident "$Header$"
#ifndef WITHOUT_INCLUDES
#ifndef _SMBUS_INCLUDE_H
	#define _SMBUS_INCLUDE_H
	#ifndef LINUX_VERSION_CODE
		#include <linux/version.h>
	#endif	// LINUX_VERSION_CODE
	#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,00)
		#ifndef		KERNEL26
			#define	KERNEL26		 1
		#endif		// KERNEL26
		#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,16)
			#ifndef		KERNEL2616
				#define	KERNEL2616		 1
			#endif		// KERNEL2616
		#endif	// LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,16)
	#else
		// Since, we do not support kernle versions less than 2.4.00, so
		// we assume here kernel version 2.4.xx
		#ifndef		KERNEL24
			#define	KERNEL24		 1
		#endif		// KERNEL24
		#ifndef		__KERNEL__
			#define	__KERNEL__		 1
		#endif		// __KERNEL__
		#ifndef MODULE_SUB
			#define MODULE
		#endif
		#include <linux/modversions.h>
	#endif		// LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,00)
	#include <linux/module.h>
	#include <linux/vmalloc.h>
	#include <linux/types.h>
	#include <linux/kernel.h>
	#include <linux/sched.h>
	#include <linux/slab.h>
	#include <linux/mm.h>
	#include <linux/string.h>
	#include <linux/errno.h>
	#include <linux/ioctl.h>
	#include <linux/delay.h>
	#include <linux/pci.h>
	#include <linux/pm.h>
	#include <asm/io.h>					// inb_p
	#include <asm/uaccess.h>			// put_user
	#ifdef	KERNEL24
		#include <linux/wrapper.h>
		#include <linux/pc_keyb.h>
	#endif	// KERNEL24
	#if defined(__x86_64__) && !defined(KERNEL2616)
		#include <asm/ioctl32.h>
	#endif	// defined(__x86_64__) && !defined(KERNEL2616)
	#include <linux/spinlock.h>
	#include <asm/semaphore.h>
	#include <linux/mc146818rtc.h>
	#include <linux/smp.h>
	// -------------------------------------------------------------------------
	// On kernel version 2.6 and kernel version from 2.6.16 (e.g.SLES10),
	// we have to adjust some defines
	#ifdef KERNEL26
		#define mem_map_reserve(p)		set_bit(PG_reserved, &((p)->flags))
		#define mem_map_unreserve(p)	clear_bit(PG_reserved, &((p)->flags))
		#define KBD_CNTL_REG			0x64	// Controller command register (W)
	#endif  // KERNEL26
	#ifdef	KERNEL2616
		#ifndef		USE_SYMBOL_IF_FOR_MODULE_INTERACTION
			#define	USE_SYMBOL_IF_FOR_MODULE_INTERACTION	 1
		#endif		// USE_SYMBOL_IF_FOR_MODULE_INTERACTION
		#ifndef		USE_REMAP_PFN_RANGE
			#define	USE_REMAP_PFN_RANGE						 1
		#endif		// USE_REMAP_PFN_RANGE
	#endif	// KERNEL2616
	#ifdef	KERNEL2616
		#define DRIVER_PARAMETER(param,str,type,perm)	module_param(param, type, perm)
	#else
		#define DRIVER_PARAMETER(param,str,type,perm)	MODULE_PARM(param, str)
	#endif	// KERNEL2616
	#if defined(__x86_64__)
		#ifdef KERNEL2616
			#ifndef		USE_COMPAT_IOCTL
				#define	USE_COMPAT_IOCTL						 1
			#endif		// USE_COMPAT_IOCTL
		#else
			#ifndef		USE_REGISTER_IOCTL32_CONVERSION
				#define	USE_REGISTER_IOCTL32_CONVERSION			 1
			#endif		// USE_REGISTER_IOCTL32_CONVERSION
		#endif // KERNEL2616
	#endif // defined(__x86_64__)
	// -------------------------------------------------------------------------
	#ifndef MODULE_INFO
		#define	MODULE_INFO(tag, string)			// dummy on kernel 2.4.xx
	#endif // MODULE_INFO
	MODULE_LICENSE("GPL");
	MODULE_AUTHOR("Fujitsu Siemens Computers GmbH");
	MODULE_INFO(supported, "yes");
	MODULE_DESCRIPTION("allow access to BIOS, SMBUS, and cpuid / msr registers");
	MODULE_INFO(device, "/dev/pci/smbus");
	MODULE_SUPPORTED_DEVICE("/dev/pci/smbus");
#endif // _SMBUS_INCLUDE_H
#endif  // WITHOUT_INCLUDES
#ident "$Header: $"
#ident "$Header$"
#ident "$Header: $"
typedef char CHAR;
typedef short SHORT;
typedef int BOOL;
typedef int INT;
typedef int LONG32;
typedef long LONG;
typedef float FLOAT;
typedef double DOUBLE;
typedef long long LONGLONG;
typedef unsigned char BYTE;
typedef unsigned char UCHAR;
typedef unsigned short WORD;
typedef unsigned short USHORT;
typedef unsigned int DWORD;
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef unsigned long long DWORDLONG;
typedef unsigned long long QWORD;
typedef unsigned long long DWORD64;
typedef unsigned long long ULONGLONG;
typedef size_t SIZE_T;
typedef ssize_t SSIZE_T;
typedef void VOID;
typedef signed int INT_PTR, *PINT_PTR;
typedef unsigned int UINT_PTR, *PUINT_PTR;
typedef signed long LONG_PTR, *PLONG_PTR;
typedef unsigned long ULONG_PTR, *PULONG_PTR;
typedef ULONG_PTR DWORD_PTR, *PDWORD_PTR;
typedef CHAR *PCHAR;
typedef SHORT *PSHORT;
typedef FLOAT *PFLOAT;
typedef DOUBLE *PDOUBLE;
typedef UCHAR *PUCHAR;
typedef USHORT *PUSHORT;
typedef UINT *PUINT;
typedef ULONG *PULONG;
typedef CHAR *PSTR;
typedef const CHAR *PCSTR;
typedef CHAR *PTSTR;
typedef CHAR *PSZ;
typedef CHAR *LPSZ;
typedef CHAR *LPSTR;
typedef CHAR *LPTSTR;
typedef const CHAR *LPCSTR;
typedef const CHAR *LPCTSTR;
typedef BOOL *PBOOL;
typedef BOOL *LPBOOL;
typedef BYTE *PBYTE;
typedef BYTE *LPBYTE;
typedef INT *PINT;
typedef INT *LPINT;
typedef WORD *PWORD;
typedef WORD *LPWORD;
typedef LONG *PLONG;
typedef LONG *LPLONG;
typedef DWORD *PDWORD;
typedef DWORD *LPDWORD;
typedef DWORDLONG *PDWORDLONG;
typedef DWORDLONG *LPDWORDLONG;
typedef VOID *PVOID;
typedef VOID *LPVOID;
typedef const VOID *LPCVOID;
typedef WORD *LPWSTR;
typedef const WORD *LPCWSTR;
#pragma pack (1)
typedef union _LARGE_INTEGER {
        struct {
                DWORD LowPart;
                DWORD HighPart;
        } u;
        DWORD64 QuadPart;
} LARGE_INTEGER;
#pragma pack ()
#ident "$Header: snismdrv.h 1.2 99/12/22 $"
#pragma pack (1)
typedef struct _DMI_20_HEADER{
    UCHAR Type;
    UCHAR Length;
    USHORT Handle;
} DMI_20_HEADER, * LPDMI_20_HEADER;
typedef struct _DMI_20_HEADER_SUBTYPE{
    UCHAR Type;
    UCHAR Length;
    USHORT Handle;
    UCHAR SubType;
} DMI_20_HEADER_SUBTYPE, * LPDMI_20_HEADER_SUBTYPE;
typedef struct _DmiStructList
{
        LPDMI_20_HEADER pDmiStruct;
    struct _DmiStructList* Next;
} DMI_STRUCT_LIST, *PDMI_STRUCT_LIST;
typedef struct _DmiTypeList
{
        PDMI_STRUCT_LIST pStructList;
        BYTE NrOfStruct;
        BYTE Alignment[sizeof(BYTE *) - sizeof(BYTE)];
} DMI_TYPE_LIST, *PDMI_TYPE_LIST;
typedef struct _DmiRevision
{
        BYTE Major;
        BYTE Minor;
} DMI_REVISION, *PDMI_REVISION;
typedef struct _PHOENIX_DMI_TABLE_ENTRY {
    USHORT Size;
    USHORT Handle;
    ULONG Procedure;
} PHOENIX_DMI_TABLE_ENTRY, * LPPHOENIX_DMI_TABLE_ENTRY;
typedef struct _PHOENIX_DMI_HEADER{
    UCHAR Signature [10];
    UCHAR Revision;
    PHOENIX_DMI_TABLE_ENTRY Entry[1];
} PHOENIX_DMI_HEADER, * LPPHOENIX_DMI_HEADER;
typedef struct _DMI_IEPS{
    UCHAR _DMI_Anchor_String[5];
    UCHAR IEPS_Checksum;
    USHORT SMBIOS_Struct_Table_Length;
    ULONG SMBIOS_Struct_Table_Addr;
    USHORT StructureNumber;
    UCHAR SMBIOS_BCD_Revision;
} DMI_IEPS, * LPDMI_IEPS;
typedef struct _DMI_21_EPS{
    UCHAR _SM_Anchor_String[4];
    UCHAR EPS_Checksum;
    UCHAR EPS_Length;
    UCHAR SMBIOS_Major_Version;
    UCHAR SMBIOS_Minor_Version;
    USHORT StructureSizeMax;
    UCHAR EPS_Revision;
    UCHAR reserved[5];
    UCHAR _DMI_Anchor_String[5];
    UCHAR IEPS_Checksum;
    USHORT SMBIOS_Struct_Table_Length;
    ULONG SMBIOS_Struct_Table_Addr;
    USHORT StructureNumber;
    UCHAR SMBIOS_BCD_Revision;
} DMI_21_EPS, * LPDMI_21_EPS;
typedef struct BIOSInformation {
        DMI_20_HEADER DmiHeader;
        BYTE vendor;
        BYTE version;
        USHORT startingAddress;
        BYTE releaseDate;
        BYTE romSize;
        BYTE Characteristics[8];
        BYTE ExtensionBytes[2];
        BYTE SystemBiosMajorRelease;
        BYTE SystemBiosMinorRelease;
        BYTE EmbeddedControllerFirmwareMajorRelease;
        BYTE EmbeddedControllerFirmwareMinorRelease;
} BIOS_INFO, * PBIOS_INFO;
typedef struct SystemInformation {
        DMI_20_HEADER DmiHeader;
        BYTE vendor;
        BYTE name;
        BYTE version;
        BYTE SerialNr;
        BYTE UUID[16];
        BYTE wakeup;
} DMI_SYS_INFO, * PDMI_SYS_INFO;
typedef struct BOARDInformation {
        DMI_20_HEADER DmiHeader;
    BYTE MfgStrNr;
        BYTE ProdStrNr;
        BYTE VerStrNr;
        BYTE SerNumStrNr;
} BOARDINFO, * PBOARDINFO;
typedef struct sysEnclosure {
        DMI_20_HEADER DmiHeader;
        BYTE manufacturer;
        BYTE type;
        BYTE version;
        BYTE serialNumber;
        BYTE assetTagNr;
        BYTE BootupState;
        BYTE PowerSupplyState;
        BYTE ThermalState;
        BYTE SecurityStatus;
        DWORD OEMDefined;
} SYS_ENCLOSURE, * PSYS_ENCLOSURE;
typedef struct _cpu_id_low
{
        UCHAR CpuStep:4;
        UCHAR CpuModel:4;
        UCHAR CpuFamily:4;
        UCHAR CpuType:2;
        UCHAR Rsvd1:2;
        UCHAR CpuExtModel:4;
        UCHAR CpuExtFamily:8;
        UCHAR Rsvd2:4;
}CPU_ID_LOW,*P_CPU_ID_LOW;
typedef struct processorInformation {
        DMI_20_HEADER DmiHeader;
        BYTE socketDesignation;
        BYTE type;
        BYTE family;
        BYTE manufacturer;
        ULONG low_ID;
        ULONG high_ID;
        BYTE version;
        BYTE voltage;
        USHORT externalClock;
        USHORT maxSpeed;
        USHORT currentSpeed;
        BYTE status;
        BYTE upgrade;
        WORD CacheHandleL1;
        WORD CacheHandleL2;
        WORD CacheHandleL3;
        BYTE SerialNumber;
        BYTE AssetTag;
        BYTE PartNumber;
        BYTE CoreCount;
        BYTE CoreEnabled;
        BYTE ThreadCount;
        WORD Characteristics;
        WORD Family2;
} DMI_CPU_INFO, * PDMI_CPU_INFO;
typedef struct memModuleInformation {
        DMI_20_HEADER DmiHeader;
        BYTE socketDesignation;
        BYTE bankConnections;
        BYTE currentSpeed;
        WORD memoryType;
        BYTE installedSize;
        BYTE enabledSize;
        BYTE errorStatus;
} MEMMODULE_INFO, * PMEMMODULE_INFO;
typedef struct cacheInformation {
        DMI_20_HEADER DmiHeader;
        BYTE socketDesignation;
        WORD configuration;
        WORD maxSize;
        WORD installedSize;
        WORD supportedSRamType;
        WORD currentSRamType;
        BYTE cacheSpeed;
        BYTE errorCorrectionType;
        BYTE systemCacheType;
        BYTE associativity;
} DMI_CACHE_INFO, * PDMI_CACHE_INFO;
typedef struct PortConnector {
        DMI_20_HEADER DmiHeader;
        BYTE IntRefDesignator;
        BYTE IntConnectorType;
        BYTE ExtRefDesignator;
        BYTE ExtConnectorType;
        BYTE PortType;
} PORT_CONNECTOR, *PPORT_CONNECTOR;
typedef struct slotInformation
{
        DMI_20_HEADER DmiHeader;
        BYTE slotDesignation;
    BYTE slotType;
        BYTE slotDataBusWidth;
        BYTE currentUsage;
        BYTE slotLength;
        WORD slotId;
        BYTE slotCharacteristics1;
        BYTE slotCharacteristics2;
} SYSTEM_SLOTS, *PSYSTEM_SLOTS;
typedef struct _DeviceParam {
        BYTE DeviceType;
        BYTE DeviceString;
} DEVICE_PARAM, * PDEVICE_PARM;
typedef struct OnboardDevice {
        DMI_20_HEADER DmiHeader;
        DEVICE_PARAM Device[1];
} ONBOARD_DEVICE_INFO, * PONBOARD_DEVICE_INFO;
typedef struct OemStringInformation {
        DMI_20_HEADER DmiHeader;
        BYTE NrOfStrings;
} OEMSTRING_INFO, * POEMSTRING_INFO;
typedef struct SystemConfig {
        DMI_20_HEADER DmiHeader;
        BYTE NrOfStrings;
} SYSTEM_CONFIG, * PSYSTEM_CONFIG;
typedef struct BIOSLanguage {
        DMI_20_HEADER DmiHeader;
        BYTE NrLanguages;
        BYTE Flags;
        BYTE Reserved[15];
        BYTE CurrentLanguage;
} BIOS_LANGUAGE, * PBIOS_LANGUAGE;
typedef struct memarrayInformation {
        DMI_20_HEADER DmiHeader;
        BYTE Location;
        BYTE Use;
        BYTE ErrorCorrection;
        DWORD MaxCapacity;
        WORD MemErrorInfoHandle;
        WORD NumberMemDevices;
} MEMARRAY_INFO, * PMEMARRAY_INFO;
typedef struct memdeviceInformation {
        DMI_20_HEADER DmiHeader;
        WORD MemArrayHandle;
        WORD MemErrorInfoHandle;
        WORD TotalWidth;
        WORD DataWidth;
        WORD DevSize;
        BYTE FormFactor;
        BYTE DeviceSet;
        BYTE DeviceLocator;
        BYTE BankLocator;
        BYTE MemType;
        WORD TypeDetail;
        WORD Speed;
        BYTE Manufacturer;
        BYTE SerialNumber;
        BYTE AssetTag;
        BYTE PartNumber;
} MEMDEVICE_INFO, * PMEMDEVICE_INFO;
typedef struct MemArrayMap {
        DMI_20_HEADER DmiHeader;
        DWORD StartAddress;
        DWORD EndAddress;
        WORD MemArrayHandle;
        BYTE PartitionWidth;
} MEM_ARRAY_MAP, *PMEM_ARRAY_MAP;
typedef struct memmapaddrInformation {
        DMI_20_HEADER DmiHeader;
        DWORD StartAddress;
        DWORD EndAddress;
        WORD MemDeviceHandle;
        WORD MemArrayHandle;
        BYTE PartitionRowPosition;
        BYTE InterleavePosition;
        BYTE InterleaveDataDepth;
} MEMMAPADDR_INFO, * PMEMMAPADDR_INFO;
typedef struct IPMIInformation {
        DMI_20_HEADER DmiHeader;
        UCHAR InterfaceType;
        UCHAR IPMIRevision;
        UCHAR I2CAddress;
        UCHAR NVDevAddress;
        LARGE_INTEGER IO_BaseAddress;
        UCHAR BaseAddrModifier_IntInfo;
        UCHAR IntNumber;
} IPMI_INFO, * PIPMI_INFO;
typedef struct OMFboardId
{
        DMI_20_HEADER DmiHeader;
        USHORT boardHwConfig;
        ULONG boardId;
        USHORT boardHwGS;
        USHORT boardVariante;
        USHORT chassisId;
} OMF_BOARD_ID, * POMF_BOARD_ID;
typedef struct _Board_Var{
        UCHAR VarId;
        UCHAR WgsId;
}BOARD_VAR, *PBOARD_VAR;
typedef struct _Board_Id {
        WORD BoardNr;
        UCHAR OemSubId:4;
        UCHAR Reserved:4;
        UCHAR SubId:3;
        UCHAR Variant:5;
}BOARD_ID, *PBOARD_ID;
typedef struct OMFboardId2
{
        DMI_20_HEADER DmiHeader;
        USHORT boardHwConfig;
        union{
                BOARD_ID boardInfo;
                ULONG boardId;
        }B_ID;
        USHORT boardHwGS;
        union{
                BOARD_VAR bVar;
                USHORT boardVariante;
        }B_V;
        USHORT chassisId;
} OMF_BOARD_ID2, * POMF_BOARD_ID2;
typedef struct OMFBIOSId {
        DMI_20_HEADER DmiHeader;
        ULONG OMFbiosId;
        ULONG OMFGtAllowedBiosId;
} OMF_BIOS_ID, * POMF_BIOS_ID;
typedef struct PortConfig {
        DMI_20_HEADER DmiHeader;
        BYTE SerialPort;
        BYTE ParallelPort;
} PORT_CONFIG, *PPORT_CONFIG;
typedef struct _SYSMON_DATA
{
    DMI_20_HEADER DmiHeader;
        BYTE SubType;
        BYTE HardwareId;
        BYTE AccessMethod[1];
} SYSMON_DATA, *LPSYSMON_DATA;
typedef struct BIOSIdentification {
        DMI_20_HEADER DmiHeader;
        ULONG MagicBIOSIdentifier;
} BIOS_IDENTIFICATION, * PBIOS_IDENTIFICATION;
typedef union Bios_188Id
{
        DWORD BiosId;
        CHAR BiosChar[4];
} BIOS_188ID, *PBIOS_188ID;
typedef struct _MEMMODULE_ADDONS
{
    DMI_20_HEADER DmiHeader;
        BYTE SubType;
        BYTE SubStruct[1];
} MEMMODULE_ADDONS, *LPMEMMODULE_ADDONS;
typedef struct _LOGICAL_CPU_ADDONS
{
        BYTE APICId;
        WORD Handle;
} LOG_CPU_ADDONS, *LPLOG_CPU_ADDONS;
typedef struct _CPU_ADDONS
{
    DMI_20_HEADER DmiHeader;
        BYTE SubType;
        BYTE CPURecordSize;
        LOG_CPU_ADDONS LogCPUAddons[1];
} CPU_ADDONS, *LPCPU_ADDONS;
typedef struct sysBoardConfig {
        DMI_20_HEADER DmiHeader;
        BYTE subType;
        BYTE nr_systemCabinetId;
        BYTE nr_manufactMonth;
        BYTE nr_systemPartNumber;
        BYTE nr_systemDescription;
        BYTE nr_systemBoardPartNummber;
        BYTE nr_systemBoardDescription;
        BYTE nr_systemBoardStep;
        BYTE nr_biosVersAndRev;
} SYSTEMBOARD_CONFIG, * PSYSTEMBOARD_CONFIG;
typedef struct _ANY_ACCESS_METHODE{
    DMI_20_HEADER DmiHeader;
        UCHAR SubType;
        UCHAR HardwareId;
} ANY_ACCESS_METHODE, * LPANY_ACCESS_METHODE;
typedef struct _ACCESS_METHODE_TULIP{
    DMI_20_HEADER DmiHeader;
        UCHAR SubType;
        UCHAR HardwareId;
    ULONG StartAddressOfData;
    UCHAR MaxGPNVSize;
    UCHAR FeatureControlRegister;
    UCHAR Tulip45Reg;
    UCHAR Tulip49Reg;
    UCHAR Tulip4BReg;
} ACCESS_METHODE_TULIP, * LPACCESS_METHODE_TULIP;
typedef struct _ACCESS_METHODE_SIO{
    DMI_20_HEADER DmiHeader;
        UCHAR SubType;
        UCHAR HardwareId;
    ULONG StartAddressOfData;
    UCHAR MaxGPNVSize;
    UCHAR ANDMask;
    UCHAR ORMask;
    USHORT SIOIndexReg;
    USHORT SIODataReg;
} ACCESS_METHODE_SIO, * LPACCESS_METHODE_SIO;
typedef struct _ACCESS_ERROR_LOG{
    BYTE LogMedia;
    WORD OffsetInMedia;
    BYTE NrOfEntries;
    BYTE SizeOfLogEntry;
    BYTE TotalSize;
} ACCESS_ERROR_LOG, * LPACCESS_ERROR_LOG;
typedef struct _MUX_I2C_HEADER{
    BYTE DeviceAddress;
    BYTE MuxChannel;
    BYTE NrChannel;
        BYTE RegisterIdx;
} MUX_I2C_HEADER , *LPMUX_I2C_HEADER;
typedef struct _CHL_MASK{
        BYTE AndMask;
        BYTE OrMask;
} CHL_MASK, *LPCHL_MASK;
typedef struct _ACCESS_MUX_I2C{
    MUX_I2C_HEADER MuxHeader;
        CHL_MASK ChlMask[1];
} ACCESS_MUX_I2C, * LPACCESS_MUX_I2C;
typedef struct _ACCESS_MUX_SMBUS{
    BYTE DeviceId;
    BYTE DeviceAddress;
    BYTE MuxChannel;
} ACCESS_MUX_SMBUS, * LPACCESS_MUX_SMBUS;
typedef struct _ACCESS_MUX_ID_PROM{
    BYTE IdPromClass;
    BYTE DeviceAddress;
    BYTE MuxChannel;
} ACCESS_MUX_ID_PROM, * LPACCESS_MUX_ID_PROM;
typedef union _ACCESS_ADDRESS
{
        struct
        {
                WORD IndexAddr;
                WORD DataAddr;
        } Io;
        DWORD PhysicalAddress32;
        WORD GPNVHandle;
} ACCESS_ADDRESS;
typedef struct _ACCESS_MEDIA
{
        BYTE Access;
        ACCESS_ADDRESS Address;
} ACCESS_MEDIA, *LPACCESS_MEDIA;
typedef struct _ACCESSMETHOD_PIIX_GPIO
{
        ULONG BitMask;
} ACCESSMETHOD_PIIX_GPIO, *PACCESSMETHOD_PIIX_GPIO;
typedef struct _ACCESSMETHOD_PIIX_GPIO_LOW
{
        ULONG BitMask;
} ACCESSMETHOD_PIIX_GPIO_LOW, *PACCESSMETHOD_PIIX_GPIO_LOW;
typedef struct _ACCESSMETHOD_PIIX_SMBUS
{
        UCHAR DeviceId;
        UCHAR DeviceAddress;
} ACCESSMETHOD_PIIX_SMBUS, *PACCESSMETHOD_PIIX_SMBUS;
typedef struct _ACCESSMETHOD_DMI_BIOS
{
        UCHAR Reserved1;
        UCHAR Reserved2;
} ACCESSMETHOD_DMI_BIOS, *PACCESSMETHOD_DMI_BIOS;
typedef struct _ACCESSMETHOD_EINSCHALTTIMER
{
        UCHAR Manufacturer;
} ACCESSMETHOD_EINSCHALTTIMER, *PACCESSMETHOD_EINSCHALTTIMER;
typedef struct _ACCESSMETHOD_SIO
{
        ULONG ManufacturingInfo_PhStartAddress;
        UCHAR MaxGPNVSize;
        UCHAR ANDMask;
        UCHAR ORMask;
        USHORT InrexRegister;
        USHORT DataRegister;
} ACCESSMETHOD_SIO, *PACCESSMETHOD_SIO;
typedef struct _ACCESSMETHOD_NAUTILUS_ISA
{
        UCHAR IndexAddress;
        UCHAR DataAddress;
        ULONG Multiplier;
        ULONG Offset;
} ACCESSMETHOD_NAUTILUS_ISA, *PACCESSMETHOD_NAUTILUS_ISA;
typedef union _DEV_PAR
{
        DWORD EntityParam;
        struct _MUL_OFF
        {
                WORD Multiplier;
                WORD Offset;
        } EnCalc;
        struct _REF_VOLTAGE
        {
                WORD RefVoltage;
                WORD Fixed;
        } EnRefVolt;
        struct _FANS
        {
                UCHAR Minimum;
                UCHAR Maximum;
                UCHAR Percentage;
                UCHAR Ripple;
        } EnFan;
        struct _VOLT_LIMITS
        {
                UCHAR LimitMin;
                UCHAR Reserved1;
                UCHAR LimitMax;
                UCHAR Reserved2;
        } EnVolt;
        struct _THRESHOLD
        {
                WORD LowThresh;
                WORD HighThresh;
        } EnThreshold;
        struct _TEMP_LIMITS
        {
                UCHAR LowWarning;
                UCHAR LowCritical;
                UCHAR HighWarning;
                UCHAR HighCritical;
        } EnTemp;
} DEV_PAR, *PDEV_PAR;
typedef struct _ACCESSMETHOD_CALC
{
        UCHAR EntityId;
        DEV_PAR DevPar;
} ACCESSMETHOD_CALC, *PACCESSMETHOD_CALC;
typedef struct _ACCESS_METHOD
{
        union{
                ACCESSMETHOD_CALC Calc;
                ACCESSMETHOD_NAUTILUS_ISA Isa;
                ACCESSMETHOD_SIO Sio;
                ACCESSMETHOD_EINSCHALTTIMER PwrOn;
                ACCESSMETHOD_DMI_BIOS DmiBios;
                ACCESSMETHOD_PIIX_SMBUS SmBus;
                ACCESSMETHOD_PIIX_GPIO_LOW GpioLow;
                ACCESSMETHOD_PIIX_GPIO Gpio;
                ACCESS_MEDIA Media;
                ACCESS_ERROR_LOG ErrLog;
                ACCESS_MUX_SMBUS MuxSmbus;
                ACCESS_MUX_ID_PROM MuxIdProm;
                ACCESS_MUX_I2C MuxI2C;
        }Access;
}ACCESS_METHOD, *PACCESS_METHOD;
typedef struct _MA_MEM_RECORD
{
        WORD MemDeviceHandle;
        BYTE HotSpareStatus;
} MA_MEM_RECORD, *PMA_MEM_RECORD;
typedef struct _MA_ADD_DEVICE_PROPERTIES
{
        BYTE MemRecordSize;
        MA_MEM_RECORD MemoryRecord[1];
} MA_ADD_DEVICE_PROPERTIES, *PMA_ADD_DEVICE_PROPERTIES;
typedef struct _MA_SCRUBBING_PROPERTIES
{
        BYTE NrScrubbingRuns;
} MA_SCRUBBING_PROPERTIES, *PMA_SCRUBBING_PROPERTIES;
#pragma pack ()
#pragma pack(1)
typedef struct _DMI_DATA
{
    UCHAR Type;
    UCHAR Length;
    USHORT Handle;
    UCHAR SubType;
    UCHAR HardwareId;
    UCHAR AccessMethod[128];
} DMI_DATA, *PDMI_DATA;
typedef struct _SYSMON_EXTENSION
{
    UCHAR SubType;
    UCHAR HardwareId;
    union
    {
        ACCESSMETHOD_PIIX_GPIO AccessGPIO;
        ACCESSMETHOD_PIIX_GPIO_LOW AccessGPIOLow;
        ACCESSMETHOD_PIIX_SMBUS AccessSMBus;
        ACCESSMETHOD_NAUTILUS_ISA AccessNautilusISA;
        ACCESSMETHOD_CALC AccessAsic[43];
        ACCESSMETHOD_EINSCHALTTIMER AccessOnTimer;
        ACCESSMETHOD_SIO AccessSuperIO;
        ACCESSMETHOD_DMI_BIOS AccessDMIBios;
    }
      access
      ;
} SYSMON_EXTENSION, *PSYSMON_EXTENSION;
#pragma pack()
typedef struct _DEVICE_EXTENSION
{
    ULONG ulDeviceNumber;
    ULONG ulOpenCount;
    ULONG SupportedHardware;
    BOOL bSupportPIIX4;
    BOOL bSupportICH;
    BOOL bSupportNautilusISA;
    BOOL bSupportNautilus;
    BOOL bSupportPegasus;
    BOOL bSupportPoseidon;
    BOOL bSupportPoseidonII;
    BOOL bSupportHydra;
    BOOL bSupportWinBond;
    BOOL bSupportKeelung;
    BOOL bSupportSMAsic;
    ULONG ulPIIX4_ICH_BusNumber_F0;
    ULONG ulPIIX4_ICH_SlotNumber_F0;
    ULONG ulPIIX4_ICH_BusNumber_F2;
    ULONG ulPIIX4_ICH_SlotNumber_F2;
    ULONG ulPIIX4_ICH_BusNumber_F3;
    ULONG ulPIIX4_ICH_SlotNumber_F3;
    ULONG ulPIIX4_ICH_GPIPort;
    ULONG ulPIIX4_ICH_GPOPort;
    ULONG ulPIIX4_ICH_PortSC;
    ULONG ulPIIX4_ICH_GPIUseSelectPort;
    ULONG ulPIIX4_ICH_GPE1_STSPort;
    ULONG ulPIIX4_ICH_TCO2_STSPort;
    ULONG ulSMBus_BaseAddress;
    ULONG ulSMBus_MaxRetry;
    ULONG ulSMBus_Sleep;
    ULONG ulSMBus_TimeOut;
    SYSMON_EXTENSION SystemMonitoringData[35];
    LONG FanSleep;
    LONG FanFaultSleep;
    UCHAR MinFanSpeed_SV;
    UCHAR MaxFanSpeed_SV;
    UCHAR FanPuls_SV;
    UCHAR FanAging_SV;
    UCHAR Fan_CPU_A_Max_Ref;
    UCHAR Fan_CPU_B_Max_Ref;
    UCHAR Fan_AUX_Max_Ref;
    UCHAR Fan_SV_Max_Ref;
    UCHAR Fan_SV2_Max_Ref;
    UCHAR Fan_System_Max_Ref;
    UCHAR MinVoltage5;
    UCHAR MaxVoltage5;
    UCHAR MinVoltage12;
    UCHAR MaxVoltage12;
    UCHAR MinVoltageBatt;
    UCHAR MaxVoltageBatt;
    UCHAR ucCPUAvailable[4];
    UCHAR ucNrCPU;
    ULONG SetValue;
    ULONG SWWatchdogPresetTime;
    UCHAR SWWatchdogTimeBase;
    BOOL SWWatchdogAlert;
    BOOL bSupportRedundantPS;
    UCHAR RedundantPSStatus;
    ULONG NrPowersupplies;
    ULONG ObjectId;
    char SVString[255];
    BOOL bSupportMonitorSV;
    BOOL bSupportFanOffNFull;
    USHORT usSVStringNMAX;
    USHORT usSVStringNMIN;
    UCHAR ucSVStringREF;
    UCHAR ucSVStringFANPULS;
    char RiserString[255];
    BOOL bSupportTempSens;
    UCHAR RiserCabinet;
    USHORT usDMICabinetID;
    char GeometryString[255];
    BOOL bMonitorSVInitiallySwitchedOn;
} DEVICE_EXTENSION, *PDEVICE_EXTENSION;
typedef struct _RET_VALUE_STRUCT
{
    DWORD Value;
    DWORD Multiplier;
    DWORD Offset;
    DWORD RefVoltage;
}RET_VALUE_STRUCT;
typedef struct _MAXSPEED_STRUCT
{
    DWORD MaxSpeed;
    DWORD RefMaxSpeed;
}RET_MAXSPEED;
typedef struct _RET_VOLTAGE_STRUCT
{
    DWORD Voltage;
    DWORD Multiplier;
    DWORD Offset;
    DWORD RefVoltage;
    DWORD MinVoltage;
    DWORD MaxVoltage;
}RET_VOLTAGE_STRUCT;
typedef struct _RET_FAN_STRUCT
{
    DWORD Supported;
    DWORD MinSpeed;
    DWORD MaxSpeed;
    DWORD Ripple;
    DWORD Percentage;
}RET_FAN_STRUCT, *PRET_FAN_STRUCT;
typedef struct _RET_TEMP_STRUCT
{
    DWORD Temperature;
    DWORD Multiplier;
    DWORD Offset;
    DWORD RefVoltage;
    DWORD LowWarning;
    DWORD LowCritical;
    DWORD HighWarning;
    DWORD HighCritical;
}RET_TEMP_STRUCT, *PRET_TEMP_STRUCT;
#pragma pack (1)
typedef struct _SmbiHeader
{
        DWORD sig0;
        DWORD sig1;
        BYTE version;
        BYTE revision;
        DWORD CMD_Pointer;
        WORD CMD_size;
        DWORD Result_Pointer;
        WORD Result_size;
        DWORD SMB_command32;
        DWORD SMB_command32near;
        DWORD SMB_command16;
} SMBI_HEADER, *P_SMBI_HEADER;
typedef struct _SmbiHeader_64
{
        DWORD sig0;
        DWORD sig1;
        BYTE version;
        BYTE revision;
        DWORD CMD_Pointer;
        WORD CMD_size;
        DWORD Result_Pointer;
        WORD Result_size;
        DWORD SMB_command32;
        DWORD SMB_command32near;
        DWORD SMB_command16;
        DWORDLONG SMB_command64;
        DWORDLONG SMB_command64near;
} SMBI_HEADER_64, *P_SMBI_HEADER_64;
typedef union _SmbiSignature
{
        DWORD Signature;
        BYTE SigChar[4];
} SMBI_USIG, *P_SMBI_USIG;
typedef struct
{
        BYTE Second;
        BYTE Minute;
        BYTE Hour;
        BYTE DayOfMonth;
        BYTE Month;
        BYTE Year;
        BYTE Century;
} AUTOPOWER, *P_AUTOPOWER;
typedef struct
{
        BYTE Channel;
        BYTE Address;
        BYTE Offset;
        union
        {
                BYTE Data_Byte;
                WORD Data_Word;
        } u;
} SMBUS, *P_SMBUS;
typedef struct
{
        BYTE Day;
        BYTE Month;
        BYTE Year;
        BYTE Century;
} BATTINST, *P_BATTINST;
typedef struct
{
        BYTE Generic_Index;
        BYTE FanCtrlBytes[3];
} GENIFV2, *P_GENIFV2;
typedef struct
{
        BYTE Version;
        BYTE NrOfMaxEntries;
        BYTE NrOfEntries;
} EVENTLOGHDR, *P_EVENTLOGHDR;
typedef struct
{
        WORD row_address;
        BYTE row_number;
        WORD column_address;
        BYTE ECC_Syndrome;
} SBEDETAILS, *P_SBEDETAILS;
typedef struct
{
        BYTE device_id;
        BYTE reg_offset;
} SMBUSERROR, *P_SMBUSERROR;
typedef struct
{
        BYTE Type;
        BYTE SubType;
        BYTE _Century;
        BYTE _Year;
        BYTE _Month;
        BYTE _Day;
        BYTE _Hour;
        BYTE _Minute;
        BYTE _Second;
        union
        {
                SBEDETAILS SBE;
                SMBUSERROR SMBusError;
        } details;
} EVENTRECORDV1, *P_EVENTRECORDV1;
typedef struct
{
        WORD RecordId;
        BYTE RecodType;
        BYTE _Year;
        BYTE _Month;
        BYTE _Day;
        BYTE _Hour;
        BYTE _Minute;
        BYTE _Second;
        BYTE EvMRev;
        BYTE SensorType;
        BYTE SensorNr;
        BYTE EventDir;
        BYTE EventData_1;
        BYTE EventData_2;
        BYTE EventData_3;
} EVENTRECORDV2, *P_EVENTRECORDV2;
typedef struct
{
        BYTE Time;
        BYTE Active;
} WATCHDOG, *P_WATCHDOG;
typedef struct
{
        BYTE MaxNumber;
        BYTE Status[4];
} CPU, *P_CPU;
typedef struct
{
        BYTE InformationMap;
        WORD Voltage;
        WORD Temperature;
        WORD FanSpeed;
} CPUINFO, *P_CPUINFO;
typedef struct
{
        BYTE NrSupported;
        WORD Type[1];
} QUERYFAN, *P_QUERYFAN;
typedef struct
{
        BYTE NrSupported;
        BYTE Type[1];
} QUERYTYPE, *P_QUERYTYPE;
typedef struct
{
        BYTE _Y;
        BYTE _X;
} VOLTAGES, *P_VOLTAGES;
typedef struct
{
        BYTE low_Y;
        BYTE low_X;
        BYTE high_Y;
        BYTE high_X;
} VOLTTHRESHOLDS, *P_VOLTTHRESHOLDS;
typedef struct
{
        union
        {
                BYTE NrMaxSupported;
                BYTE Generic_Index;
                BYTE SensorReading[2];
                VOLTAGES voltages;
                VOLTTHRESHOLDS voltThresholds;
                BYTE Intrusion[2];
                BYTE QueryBytes[4];
                WORD QueryWords[2];
                DWORD QueryDWord[1];
        } g;
} SMBIV2, *P_SMBIV2;
typedef struct CMD_PACKET {
        BYTE OpCode;
        BYTE SubOpCode;
        union
        {
                BYTE SetBoot_Boot_Device;
                BYTE SetBoot_Diagnostic_Device;
                AUTOPOWER AutoPower;
                BYTE Set_ACLR;
                BYTE WatchDog_Time;
                BYTE Retry_Counter;
                BYTE Critical_Flag;
                BYTE Delay_Time;
                BYTE Voltage_No;
                SMBUS SMBus;
                BYTE CPU_Instance;
                BYTE FAN_Instance;
                BYTE DevInstance;
                BATTINST BattInstallDate;
                GENIFV2 V2InterFace;
                BYTE Data[254];
        } u;
} COMMAND_PACKET, *P_COMMAND_PACKET;
typedef struct RESULT_PACKET {
        BYTE Status;
        BYTE Len;
        union{
                EVENTLOGHDR EventLogHdr;
                EVENTRECORDV1 EventLogEntry;
                EVENTRECORDV2 EventRecord;
                WATCHDOG WatchDog;
                BYTE Get_ACLR;
                BYTE Retry_Counter;
                BYTE Delay_Time;
                BYTE SMBus_Data_Byte;
                WORD SMBus_Data_Word;
                BYTE GetBoot_Boot_Device;
                BYTE GetBoot_Diagnostic_Device;
                BYTE Critical_Flag;
                CPU Cpu;
                CPUINFO CpuInfo;
                QUERYFAN QueryFan;
                QUERYTYPE QueryType;
                BATTINST BattInstallDate;
                WORD Voltage;
                SMBIV2 SmbiV2;
                BYTE Data[254];
        } u;
} RESLT_PACKET, *P_RESLT_PACKET;
#pragma pack ()
typedef DWORD BAPI_SIGNUM;
typedef VOID ( *BIOSAPI)(ULONG InBuffer, ULONG OutBuffer, ULONG ControlBuffer);
#pragma pack (1)
typedef union _BAPI_SIGN
{
        BYTE SignByte[sizeof(DWORD)];
        DWORD SignDword;
} BAPI_SIGN, *PBAPI_SIGN;
typedef struct _BIOS_API_HEADER
{
        DWORD Signature;
        BYTE Length;
        BYTE Checksum;
        BYTE Version;
        BYTE Reserved;
        WORD BIOS_16_Offset;
        DWORD BIOS_16_Base;
        WORD BIOS_32_Offset;
        DWORD BIOS_32_Base;
        WORD BIOS_64_Offset;
        DWORD BIOS_64_Base;
} BIOS_API_HEADER, *P_BIOS_API_HEADER;
typedef struct _BIOS_API_HEADER_64
{
        DWORD Signature;
        BYTE Length;
        BYTE Checksum;
        BYTE Version;
        BYTE Reserved;
        WORD BIOS_16_Offset;
        DWORD BIOS_16_Base;
        WORD BIOS_32_Offset;
        DWORD BIOS_32_Base;
        WORD BIOS_64_Offset;
        DWORD BIOS_64_Base;
} BIOS_API_HEADER_64, *P_BIOS_API_HEADER_64;
typedef struct _BAPI_CTRL_IN
{
        WORD Length;
        DWORD Signature;
        DWORD ServiceCode;
        BYTE Reserved[6];
        BYTE ScratchPad[1008];
} BAPI_CTRL_IN, *P_BAPI_CTRL_IN;
typedef struct _BAPI_CTRL_OUT
{
        WORD Length;
        DWORD Signature;
        DWORD ActionCode;
        BYTE GeneralStatus;
        WORD ErrorCode;
        BYTE Reserved[3];
        BYTE ScratchPad[1008];
} BAPI_CTRL_OUT, *P_BAPI_CTRL_OUT;
typedef struct _NV_FUNC_CTRL
{
        WORD FunctionControl;
        BYTE Reserved[4];
} NV_FUNC_CTRL, *P_NV_FUNC_CTRL;
typedef struct _NV_IDPROM_CTRL
{
        BYTE Class;
        BYTE Device;
        WORD StartAddress;
        WORD NrOfBytes;
} NV_IDPROM_CTRL, *P_NV_IDPROM_CTRL;
typedef struct _BAPI_CTRL_NV_IN
{
        WORD Length;
        DWORD Signature;
        DWORD ServiceCode;
        union
        {
                NV_FUNC_CTRL NvFuncCtrl;
                NV_IDPROM_CTRL NvIdpromCtrl;
        };
        BYTE ScratchPad[1008];
} BAPI_CTRL_NV_IN, *P_BAPI_CTRL_NV_IN;
typedef union _BIOS_API_CONTROL
{
        BAPI_CTRL_IN In;
        BAPI_CTRL_NV_IN NvIn;
        BAPI_CTRL_OUT Out;
} BIOS_API_CONTROL, *PBIOS_API_CONTROL;
typedef struct _BAPI_BUF_SNIBS_IN
{
        DWORD Reserved;
} BAPI_BUF_SNIBS_IN, *P_BAPI_BUF_SNIBS_IN;
typedef struct _BAPI_BUF_SNIFU_IN
{
        WORD Reserved;
        struct
        {
                DWORD Address;
                DWORD Length;
        }Segment;
}BAPI_BUF_SNIFU_IN, *P_BAPI_BUF_SNIFU_IN;
typedef struct _BAPI_BUF_SNIFA_IN
{
        DWORD Empty;
}BAPI_BUF_SNIFA_IN, *P_BAPI_BUF_SNIFA_IN;
typedef struct _BAPI_BUF_SNISM_IN
{
        DWORD Parameter;
}BAPI_BUF_SNISM_IN, *P_BAPI_BUF_SNISM_IN;
typedef struct _BAPI_BUF_SNION_IN
{
        BYTE Seconds;
        BYTE Minutes;
        BYTE Hours;
        BYTE Day;
        BYTE Month;
        BYTE Year;
        BYTE Century;
        BYTE DayOfWeek;
}BAPI_BUF_SNION_IN, *P_BAPI_BUF_SNION_IN;
typedef struct _BAPI_BUF_SNIME_IN
{
        DWORD Signature;
        WORD NrOfModules;
        WORD TotalErrors;
        WORD ErrorModule[6];
        BYTE Reserved[26];
}BAPI_BUF_SNIME_IN, *P_BAPI_BUF_SNIME_IN;
typedef struct _SNINV_TOKEN_IN
{
        union
        {
                WORD Value;
                BYTE Data[46];
        };
}SNINV_TOKEN_IN, *P_SNINV_TOKEN_IN;
typedef struct _SNINV_IDPROM_IN
{
        BYTE Data[46];
}SNINV_IDPROM_IN, *P_SNINV_IDPROM_IN;
typedef struct _BAPI_BUF_SNINV_IN
{
        union
        {
                SNINV_TOKEN_IN Token;
                SNINV_IDPROM_IN IdProm;
        };
}BAPI_BUF_SNINV_IN, *P_BAPI_BUF_SNINV_IN;
typedef struct _BAPI_BUF_SNIBS_OUT
{
        DWORD BufSize;
        BYTE Reserved[26];
}BAPI_BUF_SNIBS_OUT, *P_BAPI_BUF_SNIBS_OUT;
typedef struct _BAPI_BUF_SNIFU_OUT
{
        DWORD Empty;
}BAPI_BUF_SNIFU_OUT, *P_BAPI_BUF_SNIFU_OUT;
typedef struct _BAPI_BUF_SNIFA_OUT
{
        WORD Reserved;
        struct
        {
                DWORD Address;
                DWORD Length;
        }Segment[1];
}BAPI_BUF_SNIFA_OUT, *P_BAPI_BUF_SNIFA_OUT;
typedef struct _BAPI_BUF_SNISM_OUT
{
        DWORD Parameter;
}BAPI_BUF_SNISM_OUT, *P_BAPI_BUF_SNISM_OUT;
typedef struct _BAPI_BUF_SNION_OUT
{
        BYTE Seconds;
        BYTE Minutes;
        BYTE Hours;
        BYTE Day;
        BYTE Month;
        BYTE Year;
        BYTE Century;
        BYTE DayOfWeek;
}BAPI_BUF_SNION_OUT, *P_BAPI_BUF_SNION_OUT;
typedef struct _BAPI_BUF_SNIME_OUT
{
        DWORD Signature;
        WORD NrOfModules;
        WORD TotalErrors;
        WORD ErrorModule[6];
        BYTE Reserved[26];
}BAPI_BUF_SNIME_OUT, *P_BAPI_BUF_SNIME_OUT;
typedef struct _SNINV_TOKEN_OUT
{
        union
        {
                WORD Value;
                BYTE Data[46];
        };
}SNINV_TOKEN_OUT, *P_SNINV_TOKEN_OUT;
typedef struct _SNINV_TOKEN_PROPERTIES_OUT
{
        BYTE Media;
        BYTE BitArray;
        BYTE BuildCheckSum;
        BYTE CheckSum;
        WORD StartPos;
        BYTE Size;
}SNINV_TOKEN_PROP_OUT, *P_SNINV_TOKEN_PROP_OUT;
typedef struct _SNINV_SERVICE_CAP_OUT
{
        WORD Version;
        WORD Media;
        WORD Access;
}SNINV_SERVICE_CAP_OUT, *P_SNINV_SERVICE_CAP_OUT;
typedef struct _SNINV_MEDIA_PROP_OUT
{
        WORD MediaSize;
        BYTE MediaClass;
}SNINV_MEDIA_PROP_OUT, *P_SNINV_MEDIA_PROP_OUT;
typedef struct _SNINV_IDPROM_OUT
{
        BYTE Data[46];
}SNINV_IDPROM_OUT, *P_SNINV_IDPROM_OUT;
typedef struct _IDPROM_CLS_INFO
{
        BYTE IdPromCls;
        BYTE NrOfDevices;
        WORD IdPromSize;
}IDPROM_CLS_INFO, *P_IDPROM_CLS_INFO;
typedef struct _SNINV_IDPROM_CLS_OUT
{
        WORD NrOfClasses;
        BYTE SizeOfInfo;
        IDPROM_CLS_INFO IdPromInfo[1];
}SNINV_IDPROM_CLS_OUT, *P_SNINV_IDPROM_CLS_OUT;
typedef struct _BAPI_BUF_SNINV_OUT
{
        union
        {
                SNINV_TOKEN_OUT Token;
                SNINV_TOKEN_PROP_OUT TokenProperties;
                SNINV_SERVICE_CAP_OUT Capabilities;
                SNINV_MEDIA_PROP_OUT MediaProperties;
                SNINV_IDPROM_OUT IdProm;
                SNINV_IDPROM_CLS_OUT IdPromCls;
        };
}BAPI_BUF_SNINV_OUT, *P_BAPI_BUF_SNINV_OUT;
typedef union _BIOS_API_BUFFER
{
        struct
        {
                WORD Length;
                union
                {
                        BAPI_BUF_SNIBS_IN Snibs;
                        BAPI_BUF_SNIFU_IN Snifu;
                        BAPI_BUF_SNIFA_IN Snifa;
                        BAPI_BUF_SNISM_IN Snism;
                        BAPI_BUF_SNION_IN Snion;
                        BAPI_BUF_SNIME_IN Snime;
                        BAPI_BUF_SNINV_IN Sninv;
                }Svc;
        }In;
        struct
        {
                WORD Length;
                union
                {
                        BAPI_BUF_SNIBS_OUT Snibs;
                        BAPI_BUF_SNIFU_OUT Snifu;
                        BAPI_BUF_SNIFA_OUT Snifa;
                        BAPI_BUF_SNISM_OUT Snism;
                        BAPI_BUF_SNION_OUT Snion;
                        BAPI_BUF_SNIME_OUT Snime;
                        BAPI_BUF_SNINV_OUT Sninv;
                }Svc;
        } Out;
} BIOS_API_BUFFER, *PBIOS_API_BUFFER;
typedef struct _BAPI_QWORD
{
        DWORD LowPart;
        DWORD HighPart;
} BAPI_QWORD, *PBAPI_QWORD;
typedef struct _BAPI_EVENTS
{
        union
        {
                struct
                {
                        WORD Length;
                        DWORD Signature;
                        BAPI_QWORD Features;
                        BAPI_QWORD Events;
                } AsStruct;
                BYTE AsBytes[32];
        }Ev;
} BIOS_API_EVENTS, *P_BIOS_API_EVENTS;
typedef struct _BAPI_EVENTS_STRUCT
{
        P_BIOS_API_EVENTS pEventsIn;
        P_BIOS_API_EVENTS pEventsOut;
}BAPI_EVENTS_STRUCT, *PBAPI_EVENTS_STRUCT;
typedef struct _BAPI_MEMORY_ERRORS
{
        union
        {
                struct
                {
                        WORD Length;
                        DWORD Signature;
                        WORD NrOfModules;
                        WORD TotalErrors;
                        WORD ErrorModule[16];
                        BYTE Reserved[2];
                        DWORD Flags;
                        DWORD NrErrorDescriptors;
                        BAPI_QWORD ErrorDescriptors[12];
                } AsStruct;
                BYTE AsBytes[256];
        }Mem;
} BIOS_API_MEMERRS, *P_BIOS_API_MEMERRS;
typedef struct _BIOS_API
{
        BIOS_API_CONTROL Control;
        BIOS_API_BUFFER Buffer;
} BIOS_API, *PBIOS_API;
typedef struct _BAPI_STATIC_BUFFERS
{
        BIOS_API_CONTROL Control;
        BIOS_API_BUFFER Data;
        BIOS_API_EVENTS EventsIn;
        BIOS_API_EVENTS EventsOut;
        BIOS_API_MEMERRS MemoryErrors;
} BAPI_STATIC_BUF, *P_BAPI_STATIC_BUF;
#pragma pack ()
#pragma pack (1)
typedef struct _SMBUS_DATA
{
        DWORD Command;
        DWORD DeviceAddress;
        DWORD Data;
        DWORD ReturnStatus;
        DWORD64 pData;
        DWORD DataLen;
} SMBUS_DATA, *P_SMBUS_DATA;
typedef struct _SMBI_DATA
{
        DWORD64 pCmdBuffer;
        DWORD CmdBufferLength;
        DWORD Reserved1;
        DWORD64 pResBuffer;
        DWORD ResBufferLength;
} SMBI_DATA, *P_SMBI_DATA;
typedef struct _IoctlData_ReadSmbus
{
        DWORD DeviceAddress;
        DWORD StartOffset;
} IOCTLDATA_READ_SMBUS, *P_IOCTLDATA_READ_SMBUS;
typedef struct _IoctlData_WriteSmbus
{
        DWORD DeviceAddress;
        DWORD StartOffset;
        DWORD BytesToWrite;
        BYTE WriteData[256];
} IOCTLDATA_WRITE_SMBUS, *P_IOCTLDATA_WRITE_SMBUS;
typedef struct _Smbus_MuxDeviceAddess
{
        BYTE Address;
        BYTE Offset;
        BYTE Protocol;
        BYTE AndMask;
        BYTE OrMask;
    BYTE Reserved[3];
} SMBUS_MUX_ADDR, *P_SMBUS_MUX_ADDR;
typedef struct _IoctlData_Smbus_OpenDevice
{
        BYTE DeviceAddress;
        BYTE Reserved1[3];
        DWORD Reserved2;
        DWORD Reserved3;
        DWORD MuxesToProcess;
        DWORD64 pMuxAddr;
} IOCTLDATA_SMBUS_OPEN_DEVICE, *P_IOCTLDATA_SMBUS_OPEN_DEVICE;
typedef struct _IoctlData_Smbus_ReadDevice
{
        DWORD DeviceHandle;
        DWORD StartOffset;
} IOCTLDATA_SMBUS_READ_DEVICE, *P_IOCTLDATA_SMBUS_READ_DEVICE;
typedef struct _IoctlData_Smbus_WriteDevice
{
        DWORD Reserved1;
        DWORD StartOffset;
        DWORD Reserved2;
        DWORD BytesToProcess;
        DWORD64 pProcessData;
} IOCTLDATA_SMBUS_WRITE_DEVICE, *P_IOCTLDATA_SMBUS_WRITE_DEVICE;
typedef struct _SMBUS_DEVICE_DATA
{
        union {
                IOCTLDATA_SMBUS_OPEN_DEVICE Open;
                IOCTLDATA_SMBUS_WRITE_DEVICE Access;
        } u;
        DWORD DeviceHandle;
        BOOL Success;
} SMBUS_DEVICE_DATA, *P_SMBUS_DEVICE_DATA;
typedef struct _IoctlData_Smbus_MasterInfo
{
        WORD VendorId;
        WORD DeviceId;
        WORD BaseAddress;
} IOCTLDATA_SMBUS_MASTER_INFO, *P_IOCTLDATA_SMBUS_MASTER_INFO;
typedef struct _SmbiAddress
{
        DWORD OSType;
        DWORDLONG CmdBufAddr;
        DWORDLONG RespBufAddr;
        DWORDLONG SmbiCall;
} SMBI_ADDRESS, *P_SMBI_ADDRESS;
typedef struct _SmbiRwBuffer
{
        BYTE BufType;
        WORD NrOfBytes;
        BYTE Data[256];
} SMBI_RW_BUF, *P_SMBI_RW_BUF;
typedef struct _IoctlData_MapPhysicalMemory
{
        DWORD PhysicalAddressLow;
        DWORD PhysicalAddressHigh;
        DWORD Size;
} IOCTLDATA_MAP_PHYS_MEM, *P_IOCTLDATA_MAP_PHYS_MEM;
typedef struct _IoctlData_SmmiCmd
{
        WORD CmdResultCode;
        WORD Data;
} IOCTLDATA_SMMI_CMD, *P_IOCTLDATA_SMMI_CMD;
typedef struct _IoctlData_indexed_port_io
{
    BYTE IndexPort;
    BYTE IndexData;
    BYTE DataPort;
    BYTE DataData;
} IOCTLDATA_INDEXED_PORT_IO, *P_IOCTLDATA_INDEXED_PORT_IO;
typedef struct _IoctlData_generic_io
{
    DWORD Address;
        DWORD DataWidth;
    DWORD WriteData;
} IOCTLDATA_GEN_IO, *P_IOCTLDATA_GEN_IO;
typedef struct _IoctlData_PCI_get_conf_from_id
{
        WORD VendorId;
        WORD DeviceId;
        DWORD StartOffset;
} IOCTLDATA_PCI_GET_CONF_FROM_ID, *P_IOCTLDATA_PCI_GET_CONF_FROM_ID;
typedef struct _IoctlData_PCI_get_conf_from_loc
{
        DWORD Bus;
        DWORD Device;
        DWORD Function;
        DWORD StartOffset;
} IOCTLDATA_PCI_GET_CONF_FROM_LOC, *P_IOCTLDATA_PCI_GET_CONF_FROM_LOC;
typedef struct _IoctlData_PCI_return_conf_from_loc
{
        DWORD Bus;
        DWORD Device;
        DWORD Function;
        BYTE ConfigData[4];
} IOCTLDATA_PCI_RETURN_CONF_FROM_LOC, *P_IOCTLDATA_PCI_RETURN_CONF_FROM_LOC;
enum CPUERR_ERROR_TYPE
{
        CPUERR_TYPE_NO_ERROR,
        CPUERR_TYPE_UNCLASSIFIED,
        CPUERR_TYPE_MICROCODE_PARITY,
        CPUERR_TYPE_EXTERNAL,
        CPUERR_TYPE_FRC_ERROR,
        CPUERR_TYPE_INT_UNCLASSIFIED,
        CPUERR_TYPE_TLB_ERROR,
        CPUERR_TYPE_CACHE_ERROR,
        CPUERR_TYPE_BUS_ERROR
};
enum CPUERR_TRANSACTION_TYPE
{
        CPUERR_XTYPE_INSTRUCTION,
        CPUERR_XTYPE_DATA,
        CPUERR_XTYPE_GENERIC
};
enum CPUERR_CACHE_LEVEL
{
        CPUERR_CACHELEVEL_0,
        CPUERR_CACHELEVEL_1,
        CPUERR_CACHELEVEL_2,
        CPUERR_CACHELEVEL_GENERIC
};
enum CPUERR_REQUEST_TYPE
{
        CPUERR_REQTYPE_GENERIC_ERR,
        CPUERR_REQTYPE_GENERIC_RD,
        CPUERR_REQTYPE_GENERIC_WR,
        CPUERR_REQTYPE_DATA_RD,
        CPUERR_REQTYPE_DATA_WR,
        CPUERR_REQTYPE_FETCH,
        CPUERR_REQTYPE_PREFETCH,
        CPUERR_REQTYPE_EVICTION,
        CPUERR_REQTYPE_SNOOP
};
typedef struct _IoctlData_CorrCpuError
{
        BYTE ErrorType;
        BYTE Overflow;
        BYTE Uncorrectable;
        BYTE Bank;
        WORD ErrorCode;
        WORD Align1;
        DWORD AddressLow;
        DWORD AddressHigh;
        DWORD64 IA32MCiStatus;
        BYTE CacheLevel;
        BYTE RequestType;
        BYTE TransactionType;
        BYTE ParticipationLevel;
        BYTE Timeout;
        BYTE MemIo;
        BYTE LogicalCpuNumber;
        BYTE Align2;
} IOCTLDATA_CORR_CPU_ERROR, *P_IOCTLDATA_CORR_CPU_ERROR;
typedef struct _IoctlData_CpuApicId_BootCpu
{
        BYTE LocalApicId;
        BYTE IsBootCpu;
        BYTE LogicalCpuNumber;
        BYTE Align;
} IOCTLDATA_CPU_APICID_BOOT_CPU, *P_IOCTLDATA_CPU_APICID_BOOT_CPU;
typedef struct _CPU_ID_regs
{
        DWORD eax;
        DWORD ebx;
        DWORD ecx;
        DWORD edx;
} CPUIDRegs;
typedef union _CPU_ID_regs_IA64
{
        BYTE RawCpuId[40];
        struct _IA64regs {
                DWORD64 rg0;
                DWORD64 rg1;
                DWORD64 rg2;
                DWORD64 rg3;
                DWORD64 rg4;
        } IA64regs;
        struct _IA64Value {
                UCHAR Vendor[16];
                BYTE CpuId_Reg2_Reserved[8];
                BYTE CpuIdRegsSupported;
                BYTE CpuRevision;
                BYTE CpuModel;
                BYTE CpuFamily;
                BYTE CpuArchitectureRevicion;
                BYTE Cpu_Reg3_Reserved[3];
                BYTE CpuFeature;
                BYTE Cpu_Reg4_Reserved[7];
        } IA64Value;
} CPUIDRegsIA64;
typedef struct _IoctlData_Cpu_Info
{
        BYTE LogicalCpuNumber;
        BYTE Align[7];
        INT DenseCpuNr;
        INT SparseCpuNr;
        BOOL regs1Valid;
        BOOL regs2Valid;
        BOOL regs3Valid;
        BOOL regs4Valid;
        BOOL BrandStringValid;
        BOOL NrCoresAMDValid;
        BOOL MachineCheckArchitectureSupported;
        BOOL LocalApicSupported;
        BOOL PrimaryLogicalCpu;
        BYTE LocalApicIdInitial;
        BYTE Vendor;
        BYTE NrCores;
        BYTE NumberLogicalCpus;
        BYTE Unused2[8];
        CPUIDRegs regs0;
        CPUIDRegs regs1;
        CPUIDRegs regs2;
        CPUIDRegs regs3;
        CPUIDRegs regs4;
        CPUIDRegs MaxExtentions;
        CPUIDRegs BrandString1;
        CPUIDRegs BrandString2;
        CPUIDRegs BrandString3;
        CPUIDRegs NrCoresAMD;
        BOOL BootstrapCpu;
        BOOL ApicGlobalEnable;
        BOOL ApicIdValid;
        UINT ApicId;
        DWORD64 ApicBaseMsr;
        DWORD64 ApicBaseAddress;
        DWORD64 Unused3;
        DWORD64 Unused4;
        BOOL IsIA64Architecture;
        BOOL Unused5;
        CPUIDRegsIA64 IA64Data;
} IOCTLDATA_CPU_INFO, *P_IOCTLDATA_CPU_INFO;
#pragma pack ()
#ident "$Header$"
#ifdef __x86_64__
#define ASMX86(args...) asm(args)
#define ASMIA64(args...) do { } while(0)
#define PUSH_RDX "push %rdx"
#define PUSH_RAX "push %rax"
#define POP_RDX "pop  %rdx"
#define POP_RAX "pop  %rax"
#define PUSH_RRDI "push %%rdi"
#define PUSH_RRSI "push %%rsi"
#define PUSH_RRDX "push %%rdx"
#define PUSH_RRCX "push %%rcx"
#define POP_RRDI "pop  %rdi"
#define POP_RRSI "pop  %rsi"
#define POP_RRDX "pop  %rdx"
#define POP_RRCX "pop  %rcx"
#else
#ifdef _IA64_
#define ASMX86(args...) do { } while(0)
#define ASMIA64(args...) asm volatile (args)
#define CMOS_WRITE(d,p) do { } while(0)
#else
#define ASMX86(args...) asm(args)
#define ASMIA64(args...) do { } while(0)
#define PUSH_RDX "pushl %edx"
#define PUSH_RAX "pushl %eax"
#define POP_RDX "popl  %edx"
#define POP_RAX "popl  %eax"
#define PUSH_RRDI "push %%edi"
#define PUSH_RRSI "push %%esi"
#define PUSH_RRDX "push %%edx"
#define PUSH_RRCX "push %%ecx"
#define POP_RRDI "pop  %edi"
#define POP_RRSI "pop  %esi"
#define POP_RRDX "pop  %edx"
#define POP_RRCX "pop  %ecx"
#endif
#endif
#pragma pack(1)
typedef struct _Device_Address_Data
{
    IOCTLDATA_SMBUS_OPEN_DEVICE iod_open;
    SMBUS_MUX_ADDR muxdevadr[32];
} SMBUS_DEVICE_ADDRESS_DATA_ST;
#pragma pack()
extern PVOID OpenDevicesPersist[];
extern SMBUS_DEVICE_ADDRESS_DATA_ST SmBus_DAD_Buff [];
enum ChipsetType
{
        CS_UNKNOWN,
        CS_INTEL_PIIX4,
        CS_INTEL_ICH,
        CS_RCC_OSB4,
        CS_RCC_CSB5,
        CS_RCC_CSB6,
        CS_VIA_686A,
        CS_VIA_8233,
        CS_VIA_8237
};
extern DWORD smbus_ReadData(BYTE DeviceAddress, BYTE StartOffset, PBYTE pReturnBuffer, DWORD BytesToRead);
extern DWORD smbus_WriteData(BYTE DeviceAddress, BYTE StartOffset, PBYTE pWriteData, DWORD BytesToWrite);
extern DWORD smbus_ReadOneByte(BYTE DeviceAddress, PBYTE pReturnByte);
extern DWORD smbus_WriteOneByte(BYTE DeviceAddress, BYTE WriteData);
extern INT smbus_OpenDevice(PDWORD pDeviceHandle);
extern INT smbus_CloseDevice(DWORD DeviceHandle);
extern INT smbus_ReadDevice(DWORD DeviceHandle, BYTE Offset, DWORD BytesToRead, PBYTE pReturnBuffer, PDWORD pBytesRead);
extern INT smbus_WriteDevice (DWORD DeviceHandle, BYTE Offset, DWORD BytesToWrite, PBYTE pWriteBuffer);
extern BOOL smbus_ReadByte(BYTE DeviceAddress, BYTE Offset, PBYTE pData, BOOL NotUseOffset);
extern BOOL smbus_WriteByte(BYTE DeviceAddress, BYTE Offset, BYTE Data, BOOL NotUseOffset);
extern BOOL smbus_CheckHardwareType(DWORD *pulType);
extern void smbus_PowerDown(void);
typedef void (*SMBI_CMD_ROUTINE)(void);
extern void asus_PowerDown(char *CmdBuffer, char *ResultBuffer, SMBI_CMD_ROUTINE fSmbiExec);
extern BOOL smbus_ResetSMBusCtrl (void);
extern enum ChipsetType Chipset;
extern DWORD ulSMBusBaseAddress;
extern PVOID OpenDevices[];
typedef struct _cpu_id_regs
{
        DWORD eax;
        DWORD ebx;
        DWORD ecx;
        DWORD edx;
} CpuIdRegs;
typedef union _cpu_id_regs_IA64
{
        BYTE RawCpuId[40];
        struct _IA64_regs {
                DWORD64 rg0;
                DWORD64 rg1;
                DWORD64 rg2;
                DWORD64 rg3;
                DWORD64 rg4;
        } IA64regs;
        struct _IA64_Value {
                UCHAR Vendor[16];
                BYTE CpuId_Reg2_Reserved[8];
                BYTE CpuIdRegsSupported;
                BYTE CpuRevision;
                BYTE CpuModel;
                BYTE CpuFamily;
                BYTE CpuArchitectureRevicion;
                BYTE Cpu_Reg3_Reserved[3];
                BYTE CpuFeature;
                BYTE Cpu_Reg4_Reserved[7];
        } IA64Value;
} CpuIdRegsIA64;
typedef struct _cpu_info_
{
        INT DenseCpuNr;
        INT SparseCpuNr;
        BOOL regs1Valid;
        BOOL regs2Valid;
        BOOL regs3Valid;
        BOOL regs4Valid;
        BOOL BrandStringValid;
        BOOL NrCoresAMDValid;
        BOOL MachineCheckArchitectureSupported;
        BOOL LocalApicSupported;
        BOOL PrimaryLogicalCpu;
        BYTE LocalApicIdInitial;
        BYTE Vendor;
        BYTE NrCores;
        BYTE NumberLogicalCpus;
        BYTE Unused2[8];
        CpuIdRegs regs0;
        CpuIdRegs regs1;
        CpuIdRegs regs2;
        CpuIdRegs regs3;
        CpuIdRegs regs4;
        CpuIdRegs MaxExtentions;
        CpuIdRegs BrandString1;
        CpuIdRegs BrandString2;
        CpuIdRegs BrandString3;
        CpuIdRegs NrCoresAMD;
        BOOL BootstrapCpu;
        BOOL ApicGlobalEnable;
        BOOL ApicIdValid;
        UINT ApicId;
        DWORD64 ApicBaseMsr;
        DWORD64 ApicBaseAddress;
        DWORD64 Unused3;
        PDWORD ApicVirtualAddress;
        BOOL IsIA64Architecture;
        BOOL Unused5;
        CpuIdRegsIA64 IA64Data;
} CpuInfo;
typedef struct _cpu_error_info_
{
        void *pCpuError;
        INT DenseCpuNr;
        DWORD64 McgCap;
        DWORD64 McgStatus;
        INT NrErrorBanks;
        DWORD MsrAddrMCiStatus;
        DWORD MsrAddrMCiAddr;
        BOOL ErrorAvailable;
} CpuErrorInfo;
static int smbusArchMode = 0x00000000;
#ifdef DO_NOT_USE_OS_PM_POWER_OFF
#define DRIVER_POWEROFF_ROUTINE 0x00000002
#define DEFINE_SYMBOL_PM_POWER_OFF pm_power_off_t smbus_pm_power_off = NULL
#define PM_POWER_OFF smbus_pm_power_off
#else
#define DRIVER_POWEROFF_ROUTINE 0x00000001
#define DEFINE_SYMBOL_PM_POWER_OFF
#define PM_POWER_OFF pm_power_off
#endif
#ifdef USE_SYMBOL_IF_FOR_MODULE_INTERACTION
#define DRIVER_MODULE_INTERACTION 0x00000008
#define DRIVER_SYMBOL_IMPORT(type,symbol) extern type symbol
#define DRIVER_SYMBOL_EXPORT(symbol) EXPORT_SYMBOL(symbol)
#define DRIVER_INTER_MODULE_REGISTER(symbol) do { } while(0)
#define DRIVER_INTER_MODULE_REGISTER_P(symbol) do { } while(0)
#define DRIVER_INTER_MODULE_UNREGISTER(symbol) do { } while(0)
#define DRIVER_INTER_MODULE_GET(symbol) symbol_get(symbol)
#define DRIVER_INTER_MODULE_PUT(symbol) symbol_put(symbol)
#else
#define DRIVER_MODULE_INTERACTION 0x00000004
#define DRIVER_SYMBOL_IMPORT(type,symbol)
#define DRIVER_SYMBOL_EXPORT(symbol)
#define DRIVER_INTER_MODULE_REGISTER(symbol) inter_module_register( #symbol, THIS_MODULE, symbol )
#define DRIVER_INTER_MODULE_REGISTER_P(symbol) inter_module_register( #symbol, THIS_MODULE, &symbol )
#define DRIVER_INTER_MODULE_UNREGISTER(symbol) inter_module_unregister( #symbol )
#define DRIVER_INTER_MODULE_GET(symbol) inter_module_get( #symbol )
#define DRIVER_INTER_MODULE_PUT(symbol) inter_module_put( #symbol )
#endif
#ifdef USE_REMAP_PFN_RANGE
#define DRIVER_REMAP_RANGE_INTF 0x00000400
#define DRIVER_REMAP_RANGE(vma,va,pfn,vs,pr) remap_pfn_range((vma), (va), ((pfn) >> PAGE_SHIFT), (vs), (pr))
#else
#ifdef NEW_REMAP_INTF
#define DRIVER_REMAP_RANGE_INTF 0x00000200
#define DRIVER_REMAP_RANGE(vma,va,pa,vs,pr) remap_page_range((vma),(va),(pa),(vs),(pr))
#else
#define DRIVER_REMAP_RANGE_INTF 0x00000100
#define DRIVER_REMAP_RANGE(vma,va,pa,vs,pr) remap_page_range((va),(pa),(vs),(pr))
#endif
#endif
#ifndef KERNEL26
#define DRIVER_KERNEL_MODE 0x01000000
#define DRIVER_PCI_PRESENT(result) {result = pci_present();}
#define DRIVER_EXPORT_SYMBOLS EXPORT_NO_SYMBOLS
#define DRIVER_MOD_INC_USE_COUNT MOD_INC_USE_COUNT
#define DRIVER_MOD_DEC_USE_COUNT MOD_DEC_USE_COUNT
#define DRIVER_SET_OWNER do { } while(0)
#define DRIVER_SAVE_FLAGS(flags) save_flags(flags)
#define DRIVER_DISABLE_IRQ() cli()
#define DRIVER_FLAGS_RESTORE(flags) restore_flags(flags)
#define CPU_NUMBER_MAP(sparse) cpu_number_map((sparse))
#define SMP_NUM_CPUS smp_num_cpus
#define PREEMPT_ENABLE
#define PREEMPT_DISABLE
#else
#ifdef KERNEL2616
#define DRIVER_KERNEL_MODE (0x02000000 | 0x04000000)
#else
#define DRIVER_KERNEL_MODE 0x02000000
#endif
#define DRIVER_PCI_PRESENT(result) {result = 1;}
#define DRIVER_EXPORT_SYMBOLS
#define DRIVER_MOD_INC_USE_COUNT
#define DRIVER_MOD_DEC_USE_COUNT
#define DRIVER_SET_OWNER do {smbus_fops.owner = THIS_MODULE;} while (0)
#define DRIVER_SAVE_FLAGS(flags) local_save_flags(flags)
#define DRIVER_DISABLE_IRQ() local_irq_disable()
#define DRIVER_FLAGS_RESTORE(flags) local_irq_restore(flags)
#define CPU_NUMBER_MAP(sparse) (sparse)
#define SMP_NUM_CPUS num_online_cpus()
#define PREEMPT_ENABLE preempt_enable()
#define PREEMPT_DISABLE preempt_disable()
#endif
#define DRIVER_FOPS_WITHOUT_COMPAT .ioctl = smbus_ioctl, .mmap = smbus_mmap, .open = smbus_open, .release = smbus_release
#define DRIVER_FOPS_WITH_COMPAT .ioctl = smbus_ioctl, .compat_ioctl = smbus_ioctl_compat, .mmap = smbus_mmap, .open = smbus_open, .release = smbus_release
#ifdef __x86_64__
#define DRIVER_64BIT_MODE 0x20000000
#else
#define DRIVER_64BIT_MODE 0x40000000
#endif
#ifdef USE_REGISTER_IOCTL32_CONVERSION
#define DRIVER_IOCTL32_CONV 0x00000010
#define DRIVER_FOPS DRIVER_FOPS_WITHOUT_COMPAT
typedef int (*handler_ioctl32_t)(unsigned int fd, unsigned int cmd, unsigned long arg, struct file *file);
extern asmlinkage int sys_ioctl(unsigned int fd, unsigned int cmd, unsigned long arg);
#define REGISTER_IOCTL32_CONVERSION(ret,cmd) {ret = 0; ret = register_ioctl32_conversion((cmd), (handler_ioctl32_t)sys_ioctl);}
#define UNREGISTER_IOCTL32_CONVERSION(ret,cmd) {ret = 0; ret = unregister_ioctl32_conversion((cmd));}
#else
#ifdef USE_COMPAT_IOCTL
#define DRIVER_IOCTL32_CONV 0x00000020
#define DRIVER_FOPS DRIVER_FOPS_WITH_COMPAT
#define REGISTER_IOCTL32_CONVERSION(ret,cmd) {ret = 0;}
#define UNREGISTER_IOCTL32_CONVERSION(ret,cmd) {ret = 0;}
#else
#define DRIVER_IOCTL32_CONV 0
#define DRIVER_FOPS DRIVER_FOPS_WITHOUT_COMPAT
#define REGISTER_IOCTL32_CONVERSION(ret,cmd) {ret = 0;}
#define UNREGISTER_IOCTL32_CONVERSION(ret,cmd) {ret = 0;}
#endif
#endif
#ifdef __x86_64__
#ifdef PAGE_KERNEL_EXEC
#define SMBUS_PAGE_KERNEL_EXEC PAGE_KERNEL_EXEC
#else
#ifdef PAGE_KERNEL_EXECUTABLE
#define SMBUS_PAGE_KERNEL_EXEC PAGE_KERNEL_EXECUTABLE
#else
#define SMBUS_PAGE_KERNEL_EXEC PAGE_KERNEL
#endif
#endif
#define VMALLOC_EXEC(size) __vmalloc((size), GFP_KERNEL | __GFP_HIGHMEM, SMBUS_PAGE_KERNEL_EXEC)
#else
#define VMALLOC_EXEC(size) vmalloc((size))
#endif
DRIVER_EXPORT_SYMBOLS;
static unsigned long jiffies0 = 0;
static short smbusDebug = 0;
BOOL IsSmbusHwFound = 0;
BOOL IsSmbiHwFound = 0;
BOOL IsBapiHwFound = 0;
BOOL IsBusIoHwFound = 1;
BOOL IsCpuErrHwFound = 1;
BOOL IsCpuApicHwFound = 1;
BOOL IsCpuInfoHwFound = 1;
static short smbusPowerOff = 1;
typedef void (*pm_power_off_t) (void);
DEFINE_SYMBOL_PM_POWER_OFF;
static pm_power_off_t smbus_PowerOff_saved = NULL;
static BOOL smbus_OS_Poff_routine_changed = 0;
static void smbus_register_PowerOff_routine (void);
static void smbus_unregister_PowerOff_routine (void);
                void smbus_PowerOff (void);
static int smbus_register_ioctl32 (unsigned int cmd, char *name);
static int smbus_register_ioctl32_all (void);
static void smbus_unregister_ioctl32 (unsigned int cmd, char *name);
static void smbus_unregister_ioctl32_all (void);
typedef VOID (*BAPI_CMD_ROUTINE)(ULONG InBuffer, ULONG OutBuffer, ULONG ControlBuffer);
typedef VOID (*BAPI_CMD_ROUTINE_VOID)(void);
static BOOL FindAsusBuffers (ulong base, ulong offset, ulong size, char *signature, size_t SignatureSize);
                void smbus_CallBapi (ULONG InBuffer, ULONG OutBuffer, ULONG ControlBuffer, BAPI_CMD_ROUTINE_VOID BapiEx);
static BOOL FindBapiBuffers (ulong base, ulong offset, ulong size, DWORD signature);
static void DetectHardware (void);
                BOOL CheckForIntrusionSupport (void);
                BOOL CheckForCabinetIntrusion (void);
                BOOL smbus_ResetSMBusCtrl (void);
static void ReadFromIndexedPort (IOCTLDATA_INDEXED_PORT_IO *portio);
static void WriteToIndexedPort (IOCTLDATA_INDEXED_PORT_IO *portio);
static int smbus_open (struct inode *inode, struct file *file);
static int smbus_release (struct inode *inode, struct file *file);
static int smbus_mmap (struct file *file, struct vm_area_struct *vma);
                long smbus_ioctl_compat (struct file *file, unsigned int cmd, unsigned long arg);
static int smbus_ioctl (struct inode *inode, struct file *file, unsigned int cmd, unsigned long arg);
static void free_all (void);
static int smbus_DetermineEnvironment (void);
                int init_module (void);
                void cleanup_module (void);
static char *SMBUS_DEV = "smbus";
static int smbus_major = 0;
static DECLARE_MUTEX(smbus_mutex);
static CpuInfo smbus_cpuinfotable[128];
           void smbus_ReadCpuInfo_callback (void *pent);
static void smbus_do_ReadCpuInfo (CpuInfo *pentry);
           void smbus_ReadCpuInfo_callback_IA64 (void *pent);
static void smbus_do_ReadCpuInfo_IA64 (CpuInfo *pentry);
           void smbus_ReadApicId_callback (void *pent);
static void smbus_do_ReadApicId (CpuInfo *pentry);
static void smbus_FillCpuInfoTable (void);
static DWORD64 smbus_ReadMsr (DWORD address);
static void smbus_WriteMsr (DWORD address, DWORD64 data);
static void smbus_CpuId (DWORD address, CpuIdRegs *regs);
static void smbus_CpuId_IA64 (CpuIdRegsIA64 *regs);
           void smbus_GetCpuError_callback (void *pCpuErrInfo);
static void smbus_do_GetCpuError (CpuErrorInfo *pCpuErrInfo);
static void smbus_ReadCpuErrorInfo (CpuErrorInfo *pCpuErrInfo);
DRIVER_PARAMETER(smbusDebug, "h", short, S_IRUSR | S_IWUSR);
MODULE_PARM_DESC(smbusDebug, "    0 - debug off; , >0 - debug on)");
DRIVER_PARAMETER(smbusArchMode, "i", int, S_IRUSR);
MODULE_PARM_DESC(smbusPowerOff, " 0 - Power Off by OS; 1 - Power Off by this driver");
MODULE_PARM_DESC(smbusArchMode, " This bit field reflects the current architecture mode");
DRIVER_PARAMETER(smbusPowerOff, "h", short, S_IRUSR | S_IWUSR);
DRIVER_PARAMETER(IsSmbusHwFound, "i", int, S_IRUSR);
MODULE_PARM_DESC(IsSmbusHwFound, "   true if SMBUS  Hardware available)");
DRIVER_PARAMETER(IsBusIoHwFound, "i", int, S_IRUSR);
MODULE_PARM_DESC(IsBusIoHwFound, "   true if BUS IO Hardware available)");
DRIVER_PARAMETER(IsSmbiHwFound, "i", int, S_IRUSR);
MODULE_PARM_DESC(IsSmbiHwFound, "    true if SMBI   Firmware available)");
DRIVER_PARAMETER(IsBapiHwFound, "i", int, S_IRUSR);
MODULE_PARM_DESC(IsBapiHwFound, "    true if BAPI Firmware available)");
DRIVER_PARAMETER(IsCpuApicHwFound, "i", int, S_IRUSR);
MODULE_PARM_DESC(IsCpuApicHwFound, " true if CPU Apic Information available)");
DRIVER_PARAMETER(IsCpuErrHwFound, "i", int, S_IRUSR);
MODULE_PARM_DESC(IsCpuErrHwFound, "  true if CPU Error detection available)");
DRIVER_PARAMETER(IsCpuInfoHwFound, "i", int, S_IRUSR);
MODULE_PARM_DESC(IsCpuInfoHwFound, " true if CPU Information available)");
DRIVER_SYMBOL_IMPORT(pm_power_off_t ,copa_PowerOff);
DRIVER_SYMBOL_IMPORT(pm_power_off_t*,copa_PowerOff_saved);
DRIVER_SYMBOL_IMPORT(pm_power_off_t ,ipmi_PowerOff);
DRIVER_SYMBOL_IMPORT(pm_power_off_t*,ipmi_PowerOff_saved);
DRIVER_SYMBOL_EXPORT(smbus_PowerOff);
DRIVER_SYMBOL_EXPORT(smbus_PowerOff_saved);
static struct _SmBusIoBaseAddresses
{
        WORD VendorId;
        WORD DeviceId;
        BYTE AddressReg;
        BYTE Chipset;
        char *pChipName;
} SmBusIoBaseAddresses[] =
{
        { 0x8086, 0x7113, 0x90, CS_INTEL_PIIX4, "Intel PIIX4" },
        { 0x8086, 0x2413, 0x20, CS_INTEL_ICH, "Intel ICH" },
        { 0x8086, 0x2443, 0x20, CS_INTEL_ICH, "Intel ICH2" },
        { 0x8086, 0x2483, 0x20, CS_INTEL_ICH, "Intel ICH3" },
        { 0x8086, 0x24C3, 0x20, CS_INTEL_ICH, "Intel ICH4" },
        { 0x8086, 0x24D3, 0x20, CS_INTEL_ICH, "Intel ICH5" },
        { 0x8086, 0x266A, 0x20, CS_INTEL_ICH, "Intel ICH6" },
        { 0x8086, 0x27DA, 0x20, CS_INTEL_ICH, "Intel ICH7" },
        { 0x8086, 0x283E, 0x20, CS_INTEL_ICH, "Intel ICH8" },
        { 0x8086, 0x2930, 0x20, CS_INTEL_ICH, "Intel ICH9" },
        { 0x8086, 0x25A4, 0x20, CS_INTEL_ICH, "Intel ICHS" },
        { 0x1166, 0x0200, 0x90, CS_RCC_OSB4, "RCC OSB4" },
        { 0x1166, 0x0201, 0x90, CS_RCC_CSB5, "RCC CSB5" },
        { 0x1166, 0x0203, 0x90, CS_RCC_CSB6, "RCC CSB6" },
        { 0x1106, 0x3057, 0x90, CS_VIA_686A, "VIA 82C868A" },
        { 0x1106, 0x3074, 0xD0, CS_VIA_8233, "VIA 8233" },
        { 0x1106, 0x3227, 0xD0, CS_VIA_8237, "VIA 8237" },
        { 0, 0, 0, 0, "" }
};
enum ChipsetType Chipset = CS_UNKNOWN;
LPSTR pChipName = "UNKNOWN";
struct pci_dev *SmbusPcidev_p = NULL;
DWORD ulSMBusBaseAddress = 0;
PVOID OpenDevices[32] = {};
PVOID OpenDevicesPersist[32] = {};
SMBUS_DEVICE_ADDRESS_DATA_ST SmBus_DAD_Buff [32] = {};
static int SmBusDeviceIndex = -1;
static DWORD ulPIIX4_ICH_GPIPort = 0;
static DWORD ulPIIX4_ICH_GPOPort = 0;
static DWORD ulPIIX4_ICH_TCO2_STSPort = 0;
static DWORD ulPIIX4_ICH_GPIUseSelectPort = 0;
static SMBI_HEADER *m_pSmbiBase = NULL;
static SMBI_CMD_ROUTINE m_fSmbiExec = NULL;
static char *ulASUSCmdBuffer;
static char *ulASUSResultBuffer;
static void *pVirtMemorySMBI = NULL;
static BIOS_API_HEADER *m_pBapiBase = NULL;
static BAPI_CMD_ROUTINE m_fBapiExec = NULL;
static BAPI_STATIC_BUF *pBAPIStaticPage = NULL;
static void *pVirtMemoryBAPI = NULL;
static ULONG phys_BAPI_CB = 0;
static ULONG phys_BAPI_DB = 0;
static ULONG phys_BAPI_SP = 0;
static ULONG phys_BAPI_EvIn = 0;
static ULONG phys_BAPI_EvOut = 0;
static ULONG phys_BAPI_MemErr = 0;
static BOOL FindAsusBuffers(ulong base, ulong offset, ulong size, char *signature, size_t SignatureSize)
{
        int i;
        char *BaseAddress;
        if (smbusArchMode & 0x40000000)
        {
                m_pSmbiBase = NULL;
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "FindAsusBuffers: WARNING: WE DO NOT SUPPORT SMBI for IA64 mode  yet !!!\n", (int)(jiffies-jiffies0)); } while (0);
                return 0;
        }
        BaseAddress = (char *)phys_to_virt(base);
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "ASUSSearchAddress = 0x%p (0x%lx) [+0x%lx,0x%lx]\n", (int)(jiffies-jiffies0), BaseAddress, base, offset, size); } while (0);
        if (BaseAddress)
        {
                unsigned char *Address = BaseAddress + offset;
                for (i = 0; i < size; i++)
                {
                        char *p_work = (char *)(Address + i);
                        if (memcmp(p_work, signature, SignatureSize) == 0)
                        {
                                m_pSmbiBase = (SMBI_HEADER *)p_work;
                                break;
                        }
                }
                if (m_pSmbiBase != NULL)
                {
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "SMBIHeader           = 0x%p (0x%lx)\n", (int)(jiffies-jiffies0), m_pSmbiBase, ((char *)m_pSmbiBase - BaseAddress + base)); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "HeaderVersion        = 0x%02X\n", (int)(jiffies-jiffies0), m_pSmbiBase->version); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "HeaderRevision       = 0x%02X\n", (int)(jiffies-jiffies0), m_pSmbiBase->revision); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "CMD pointer          = 0x%08X\n", (int)(jiffies-jiffies0), m_pSmbiBase->CMD_Pointer); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "CMD size             = 0x%04X\n", (int)(jiffies-jiffies0), m_pSmbiBase->CMD_size); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "Result pointer       = 0x%08X\n", (int)(jiffies-jiffies0), m_pSmbiBase->Result_Pointer); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "Result size          = 0x%04X\n", (int)(jiffies-jiffies0), m_pSmbiBase->Result_size); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "SMBI command32       = 0x%08X\n", (int)(jiffies-jiffies0), m_pSmbiBase->SMB_command32); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "SMBI command32near   = 0x%08X\n", (int)(jiffies-jiffies0), m_pSmbiBase->SMB_command32near); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "SMBI command16       = 0x%08X\n", (int)(jiffies-jiffies0), m_pSmbiBase->SMB_command16); } while (0);
                        if(0x20 == m_pSmbiBase->version)
                        {
                                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "SMBI command64       = 0x%016LX\n", (int)(jiffies-jiffies0), ((P_SMBI_HEADER_64)m_pSmbiBase)->SMB_command64); } while (0);
                                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "SMBI command64near   = 0x%016LX\n", (int)(jiffies-jiffies0), ((P_SMBI_HEADER_64)m_pSmbiBase)->SMB_command64near); } while (0);
                        }
                        if (smbusArchMode & 0x20000000)
                        {
                                if (0x20 == m_pSmbiBase->version)
                                {
                                        m_fSmbiExec = (SMBI_CMD_ROUTINE)(BaseAddress + (((P_SMBI_HEADER_64)m_pSmbiBase)->SMB_command64near - base));
                                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "SMBI Exec 64-Bit     = 0x%p\n", (int)(jiffies-jiffies0), m_fSmbiExec); } while (0);
                                }
                                else
                                {
                                        printk(KERN_INFO "smbus(%d): " "init_module: WARNING: SMBI 64-Bit Service NOT available (%d) !\n", (int)(jiffies-jiffies0), 1);
                                        return 0;
                                }
                        }
                        else
                        {
                                m_fSmbiExec = (SMBI_CMD_ROUTINE)(BaseAddress + (m_pSmbiBase->SMB_command32near - base));
                                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "SMBI Exec 32-Bit     = 0x%p\n", (int)(jiffies-jiffies0), m_fSmbiExec); } while (0);
                        }
                        if (smbusArchMode & 0x20000000) {
                                if ((pVirtMemorySMBI = VMALLOC_EXEC(4096)) != NULL) {
                                        memcpy(pVirtMemorySMBI, (void *) m_fSmbiExec, 4096);
                                }
                                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "m_fSmbiExec (ori)    = 0x%p\n", (int)(jiffies-jiffies0), m_fSmbiExec); } while (0);
                                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "pVirtMemorySMBI      = 0x%p\n", (int)(jiffies-jiffies0), pVirtMemorySMBI); } while (0);
                                m_fSmbiExec = pVirtMemorySMBI;
                        }
                        if (m_fSmbiExec == NULL) {
                                m_pSmbiBase = NULL;
                                printk(KERN_INFO "smbus(%d): " "init_module: WARNING: SMBI 64-Bit Service NOT available (%d) !\n", (int)(jiffies-jiffies0), 2);
                                return 0;
                        }
                        ulASUSCmdBuffer = BaseAddress + (m_pSmbiBase->CMD_Pointer - base);
                        ulASUSResultBuffer = BaseAddress + (m_pSmbiBase->Result_Pointer - base);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "SMBI Command Buffer  = 0x%p\n", (int)(jiffies-jiffies0), ulASUSCmdBuffer); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "SMBI Result  Buffer  = 0x%p\n", (int)(jiffies-jiffies0), ulASUSResultBuffer); } while (0);
                        return 1;
                }
                else
                {
                        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "init_module: WARNING: SMBI Service NOT available (%d) !\n", (int)(jiffies-jiffies0), 2); } while (0);
                        return 0;
                }
        }
        else
        {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "init_module: WARNING: SMBI Service NOT available (%d) !\n", (int)(jiffies-jiffies0), 3); } while (0);
                return 0;
        }
        return 0;
}
void smbus_CallBapi(ULONG InBuffer, ULONG OutBuffer, ULONG ControlBuffer, BAPI_CMD_ROUTINE_VOID BapiEx)
{
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "CallBapi: InBuf=0x%016lX, OutBuf=0x%016lX, CntlBuf=0x%016lX, BapiEx=0x%p, *BapiEx=0x%p\n", (int)(jiffies-jiffies0), InBuffer, OutBuffer, ControlBuffer, BapiEx, *BapiEx); } while (0);
        ASMX86(PUSH_RRDX
                :
                : "d" (ControlBuffer));
        ASMX86(PUSH_RRSI
                :
                : "S" (OutBuffer));
        ASMX86(PUSH_RRDI
                :
                : "D" (InBuffer));
        (*BapiEx)();
        ASMX86(POP_RRDI);
        ASMX86(POP_RRSI);
        ASMX86(POP_RRDX);
}
static BOOL FindBapiBuffers(ulong base, ulong offset, ulong size, DWORD signature)
{
        int i;
        char *BaseAddress;
        ulong high_mem_phy;
        char *pVirtAddr1 = NULL;
        if (smbusArchMode & 0x40000000)
        {
                m_pBapiBase = NULL;
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "FindBapiBuffers: WARNING: WE DO NOT SUPPORT BAPI for IA64 mode yet !!!\n", (int)(jiffies-jiffies0)); } while (0);
                return 0;
        }
        high_mem_phy = (ulong)virt_to_phys(high_memory);
        pVirtAddr1 = (char *)phys_to_virt(base);
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "high_mem_phy = 0x%016lX, pVirtAddr1 = 0x%p\n", (int)(jiffies-jiffies0), high_mem_phy, pVirtAddr1); } while (0);
        BaseAddress = pVirtAddr1;
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "BAPISearchAddress = 0x%p (0x%lx) [+0x%lx,0x%lx]\n", (int)(jiffies-jiffies0), BaseAddress, base, offset, size); } while (0);
        if (BaseAddress != NULL)
        {
                unsigned char *Address = BaseAddress + offset;
                for (i = 0; i < size; i++)
                {
                        DWORD *p_work = (DWORD *)(Address + i);
                        if (*p_work == signature)
                        {
                                m_pBapiBase = (BIOS_API_HEADER *)p_work;
                                break;
                        }
                }
                if (m_pBapiBase != NULL)
                {
                        char Checksum = 0;
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "BAPIHeader     = 0x%p (0x%lx)\n", (int)(jiffies-jiffies0), m_pBapiBase, ((char *)m_pBapiBase - BaseAddress + base)); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "HeaderLength   = 0x%02X\n", (int)(jiffies-jiffies0), m_pBapiBase->Length); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "HeaderVersion  = 0x%02X\n", (int)(jiffies-jiffies0), m_pBapiBase->Version); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "HeaderReserved = 0x%02X\n", (int)(jiffies-jiffies0), m_pBapiBase->Reserved); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "BIOS_16_Offset = 0x%04X\n", (int)(jiffies-jiffies0), m_pBapiBase->BIOS_16_Offset); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "BIOS_16_Base   = 0x%08X\n", (int)(jiffies-jiffies0), m_pBapiBase->BIOS_16_Base); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "BIOS_32_Offset = 0x%04X\n", (int)(jiffies-jiffies0), m_pBapiBase->BIOS_32_Offset); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "BIOS_32_Base   = 0x%08X\n", (int)(jiffies-jiffies0), m_pBapiBase->BIOS_32_Base); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "BIOS_64_Offset = 0x%04X\n", (int)(jiffies-jiffies0), m_pBapiBase->BIOS_64_Offset); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "BIOS_64_Base   = 0x%08X\n", (int)(jiffies-jiffies0), m_pBapiBase->BIOS_64_Base); } while (0);
                        for (i = 0; i < m_pBapiBase->Length; i++)
                        {
                                Checksum += ((PBYTE)m_pBapiBase)[i];
                        }
                        if (Checksum != 0) {
                                printk(KERN_NOTICE "smbus(%d): " "WARNING: BAPI HeaderChecksum ERROR, chksum = 0x%02X\n", (int)(jiffies-jiffies0), Checksum);
                        }
                        if (smbusArchMode & 0x20000000) {
                                if ((m_pBapiBase->Version >= 0x01) &&
                                        (m_pBapiBase->Reserved == 0x00) &&
                                        (m_pBapiBase->Length == 0x1A)) {
                                         m_fBapiExec = (BAPI_CMD_ROUTINE)(BaseAddress + (m_pBapiBase->BIOS_64_Base + m_pBapiBase->BIOS_64_Offset - base));
                                } else {
                                        m_fBapiExec = NULL;
                                }
                        } else {
                                m_fBapiExec = (BAPI_CMD_ROUTINE)(BaseAddress + (m_pBapiBase->BIOS_32_Base + m_pBapiBase->BIOS_32_Offset - base));
                        }
                        if (m_fBapiExec == NULL) {
                                m_pBapiBase = NULL;
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "WARNING: BAPI Service NOT available (1)!\n", (int)(jiffies-jiffies0)); } while (0);
                                return 0;
                        }
                        if (smbusArchMode & 0x20000000) {
                                if ((pVirtMemoryBAPI = VMALLOC_EXEC(4096)) != NULL) {
                                        memcpy(pVirtMemoryBAPI, (void *) m_fBapiExec, 4096);
                                }
                                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "m_fBapiExec (ori)  = 0x%p\n", (int)(jiffies-jiffies0), m_fBapiExec); } while (0);
                                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "pVirtMemoryBAPI    = 0x%p\n", (int)(jiffies-jiffies0), pVirtMemoryBAPI); } while (0);
                                m_fBapiExec = pVirtMemoryBAPI;
                        }
                        if (m_fBapiExec == NULL) {
                                m_pBapiBase = NULL;
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "WARNING: BAPI Service NOT available (2) !\n", (int)(jiffies-jiffies0)); } while (0);
                                return 0;
                        }
                        pBAPIStaticPage = (BAPI_STATIC_BUF *)__get_free_page(GFP_KERNEL|GFP_DMA);
                        mem_map_reserve(virt_to_page(pBAPIStaticPage));
                        phys_BAPI_SP = virt_to_phys(pBAPIStaticPage);
                        phys_BAPI_CB = virt_to_phys(&pBAPIStaticPage->Control);
                        phys_BAPI_DB = virt_to_phys(&pBAPIStaticPage->Data);
                        phys_BAPI_EvIn = virt_to_phys(&pBAPIStaticPage->EventsIn);
                        phys_BAPI_EvOut = virt_to_phys(&pBAPIStaticPage->EventsOut);
                        phys_BAPI_MemErr = virt_to_phys(&pBAPIStaticPage->MemoryErrors);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "m_fBapiExec        = 0x%p\n", (int)(jiffies-jiffies0), m_fBapiExec); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "BAPIStaticPage     = 0x%p\n", (int)(jiffies-jiffies0), pBAPIStaticPage); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "phys_BAPI_Static   = 0x%0lx\n", (int)(jiffies-jiffies0), phys_BAPI_SP); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "phys_BAPI_Control  = 0x%0lx\n", (int)(jiffies-jiffies0), phys_BAPI_CB); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "phys_BAPI_Data     = 0x%0lx\n", (int)(jiffies-jiffies0), phys_BAPI_DB); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "pEventsIn          = 0x%p\n", (int)(jiffies-jiffies0), &pBAPIStaticPage->EventsIn); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "phys_BAPI_EvIn     = 0x%0lx\n", (int)(jiffies-jiffies0), phys_BAPI_EvIn); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "pEventsOut         = 0x%p\n", (int)(jiffies-jiffies0), &pBAPIStaticPage->EventsOut); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "phys_BAPI_EvOut    = 0x%0lx\n", (int)(jiffies-jiffies0), phys_BAPI_EvOut); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "pMemoryErrors      = 0x%p\n", (int)(jiffies-jiffies0), &pBAPIStaticPage->MemoryErrors); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "phys_BAPI_MemErr   = 0x%0lx\n", (int)(jiffies-jiffies0), phys_BAPI_MemErr); } while (0);
                        if ((phys_BAPI_SP > (ULONG)(0xFFFFFFFF - 0xFFFF)) ||
                            (phys_BAPI_CB > (ULONG)(0xFFFFFFFF - 0xFFFF)) ||
                                (phys_BAPI_DB > (ULONG)(0xFFFFFFFF - 0xFFFF)) ||
                                (phys_BAPI_EvIn > (ULONG)(0xFFFFFFFF - 0xFFFF)) ||
                                (phys_BAPI_EvOut > (ULONG)(0xFFFFFFFF - 0xFFFF)) ||
                                (phys_BAPI_MemErr > (ULONG)(0xFFFFFFFF - 0xFFFF)))
                        {
                                mem_map_unreserve(virt_to_page(pBAPIStaticPage));
                                free_page((ulong)pBAPIStaticPage);
                                pBAPIStaticPage = NULL;
                                phys_BAPI_SP = 0;
                                phys_BAPI_CB = 0;
                                phys_BAPI_DB = 0;
                                phys_BAPI_EvIn = 0;
                                phys_BAPI_EvOut = 0;
                                phys_BAPI_MemErr = 0;
                                m_pBapiBase = NULL;
                                printk(KERN_INFO "smbus(%d): " "init_module: WARNING: BAPI Service NOT available (%d) !\n", (int)(jiffies-jiffies0), 3);
                                return 0;
                        }
                        return 1;
                }
        }
        return 0;
}
static void DetectHardware(void)
{
        u32 addr;
        int i;
        struct pci_dev *g_smbusDev = NULL;
        char smbiSignature[] = {'S','M','B','I','A','S','U','S'};
        if (smbusArchMode & 0x40000000)
        {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "DetectHardware: WARNING: We support IA64 mode only for CPU-Info !!!\n", (int)(jiffies-jiffies0)); } while (0);
                Chipset = CS_UNKNOWN;
                smbusPowerOff = 0;
                IsSmbusHwFound = 0;
                IsSmbiHwFound = 0;
                IsBapiHwFound = 0;
                IsBusIoHwFound = 0;
                IsCpuErrHwFound = 0;
                IsCpuApicHwFound = 0;
                IsCpuInfoHwFound = 1;
                return;
        }
        i = 0;
        IsSmbusHwFound = 1;
        while ((SmBusIoBaseAddresses[i].VendorId != 0) && (SmBusIoBaseAddresses[i].DeviceId != 0))
        {
                g_smbusDev = pci_find_device(SmBusIoBaseAddresses[i].VendorId, SmBusIoBaseAddresses[i].DeviceId, NULL);
                if (g_smbusDev != NULL)
                {
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "## SM bus device found: %s\n", (int)(jiffies-jiffies0), SmBusIoBaseAddresses[i].pChipName); } while (0);
                        pci_read_config_dword(g_smbusDev, SmBusIoBaseAddresses[i].AddressReg, &addr);
                        ulSMBusBaseAddress = addr & 0x0000FFFC;
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "SMBusBaseAddress = 0x%04X\n", (int)(jiffies-jiffies0), ulSMBusBaseAddress); } while (0);
                        Chipset = SmBusIoBaseAddresses[i].Chipset;
                        pChipName = SmBusIoBaseAddresses[i].pChipName;
                        SmbusPcidev_p = g_smbusDev;
                        SmBusDeviceIndex = i;
                        break;
                }
                i++;
        }
        switch(Chipset)
        {
                case CS_UNKNOWN:
                        IsSmbusHwFound = 0;
                        break;
                case CS_INTEL_PIIX4:
                        pci_read_config_dword(g_smbusDev, 0x40, &addr);
                        ulPIIX4_ICH_GPIPort = (addr + 0x30) & 0xfffffffe;
                        ulPIIX4_ICH_GPOPort = (addr + 0x34) & 0xfffffffe;
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "PIIX4_ICH_GPIPort = 0x%x\n", (int)(jiffies-jiffies0), (int)ulPIIX4_ICH_GPIPort); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "PIIX4_ICH_GPOPort = 0x%x\n", (int)(jiffies-jiffies0), (int)ulPIIX4_ICH_GPOPort); } while (0);
                        break;
                case CS_INTEL_ICH:
                        if (SmBusIoBaseAddresses[i].DeviceId == 0x25A4)
                        {
                                IsSmbiHwFound = FindAsusBuffers(0xE0000, 0x10000, 0x10000, smbiSignature, sizeof(smbiSignature));
                        }
                        pci_read_config_dword(g_smbusDev, 0x40, &addr);
                        ulPIIX4_ICH_TCO2_STSPort = (addr + 0x60 + 0x06) & 0xfffffffe;
                        pci_read_config_dword(g_smbusDev, 0x58, &addr);
                        ulPIIX4_ICH_GPIUseSelectPort = (addr + 0x00) & 0xfffffffe;
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "PIIX4_ICH_TCO2_STSPort = 0x%x\n", (int)(jiffies-jiffies0), (int)ulPIIX4_ICH_TCO2_STSPort); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "PIIX4_ICH_GPIUseSelectPort = 0x%x\n", (int)(jiffies-jiffies0), (int)ulPIIX4_ICH_GPIUseSelectPort); } while (0);
                        break;
                case CS_RCC_OSB4:
                case CS_VIA_686A:
                        IsSmbiHwFound = FindAsusBuffers(0xE0000, 0x10000, 0x10000, smbiSignature, sizeof(smbiSignature));
                        break;
                default:
                        break;
        }
        IsBapiHwFound = FindBapiBuffers(0xE0000, 0x10000, 0x10000, (DWORD)0x4DC94253);
        if (!IsBapiHwFound && !IsSmbiHwFound)
        {
                IsSmbiHwFound = FindAsusBuffers(0xE0000, 0x10000, 0x10000, smbiSignature, sizeof(smbiSignature));
        }
        return;
}
BOOL CheckForIntrusionSupport(void)
{
        switch(Chipset)
        {
                case CS_INTEL_PIIX4:
                        return (ulPIIX4_ICH_GPIPort && ulPIIX4_ICH_GPOPort);
                case CS_INTEL_ICH:
                        return (ulPIIX4_ICH_GPIUseSelectPort && ulPIIX4_ICH_TCO2_STSPort);
                default:
                        break;
        }
        return 0;
}
BOOL CheckForCabinetIntrusion(void)
{
        BOOL bCabinetOpened = 0;
        BOOL bUseSel;
        UCHAR ucValue;
        DWORD ulValue;
        switch(Chipset)
        {
        case CS_INTEL_ICH:
                ulValue = inl_p(ulPIIX4_ICH_GPIUseSelectPort);
                bUseSel = 0;
                if (ulValue & 0x400)
                {
                        bUseSel = 1;
                        ulValue &= ~0x400;
                        outl_p(ulPIIX4_ICH_GPIUseSelectPort, ulValue);
                }
                ucValue = inb_p(ulPIIX4_ICH_TCO2_STSPort);
                if (ucValue & 0x01)
                {
                        bCabinetOpened = 1;
                        ucValue &= 0x01;
                        outb_p(ucValue, ulPIIX4_ICH_TCO2_STSPort);
                }
                if (bUseSel)
                {
                        ulValue = inl_p(ulPIIX4_ICH_GPIUseSelectPort);
                        ulValue |= 0x400;
                        outl_p(ulPIIX4_ICH_GPIUseSelectPort, ulValue );
                }
                return bCabinetOpened;
        case CS_INTEL_PIIX4:
                ulValue = inl_p(ulPIIX4_ICH_GPIPort);
                if (ulValue == 0) return 0;
                ulValue = inl_p(ulPIIX4_ICH_GPOPort);
                ulValue &= 0xFEFF;
                outl_p(ulPIIX4_ICH_GPOPort, ulValue);
                ulValue |= 0x0100;
                outl_p(ulPIIX4_ICH_GPOPort, ulValue);
                return 1;
        default:
                break;
        }
        return 0;
}
BOOL smbus_ResetSMBusCtrl(void)
{
        BOOL Success = 0;
        BYTE ConfigReg;
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ResetSMBusCtrl: RESET Chipset %s (%d)\n", (int)(jiffies-jiffies0), pChipName, Chipset); } while (0);
        switch(Chipset)
        {
        case CS_UNKNOWN:
                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ResetSMBusCtrl: NO CHIPSET DETECTED, chipset = %d\n", (int)(jiffies-jiffies0), Chipset); } while (0);
                break;
        case CS_RCC_CSB5:
                {
                        pci_read_config_byte(SmbusPcidev_p, 0x40, &ConfigReg);
                        ConfigReg |= 0x10;
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ResetSMBusCtrl: RESET REG %02X (%02X)\n", (int)(jiffies-jiffies0),0x40,ConfigReg); } while (0);
                        pci_write_config_byte(SmbusPcidev_p, 0x40, ConfigReg);
                        udelay(10);
                        pci_read_config_byte(SmbusPcidev_p, 0x40, &ConfigReg);
                        ConfigReg &= ~0x10;
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ResetSMBusCtrl: RELEASE RESET REG %02X (%02X)\n", (int)(jiffies-jiffies0),0x40,ConfigReg); } while (0);
                        pci_write_config_byte(SmbusPcidev_p, 0x40, ConfigReg);
                        udelay (10);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ResetSMBusCtrl: SET BASE ADDRESS %02X (%04X)\n", (int)(jiffies-jiffies0),0x90,ulSMBusBaseAddress); } while (0);
                        pci_write_config_dword(SmbusPcidev_p, 0x90, ulSMBusBaseAddress);
                        ConfigReg = 0x03;
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ResetSMBusCtrl: ENABLE REG %02X (%02X)\n", (int)(jiffies-jiffies0),0xD2,ConfigReg); } while (0);
                        pci_write_config_byte(SmbusPcidev_p, 0xD2, ConfigReg);
                        Success = 1;
                }
                break;
        default:
                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ResetSMBusCtrl: NO RESET FUNCTION FOR CHIPSET %d\n", (int)(jiffies-jiffies0),Chipset); } while (0);
                break;
        }
        return Success;
}
static void ReadFromIndexedPort(IOCTLDATA_INDEXED_PORT_IO *portio)
{
        outb_p(portio->IndexData, portio->IndexPort);
        portio->DataData = inb_p(portio->DataPort);
}
static void WriteToIndexedPort(IOCTLDATA_INDEXED_PORT_IO *portio)
{
        outb_p(portio->IndexData, portio->IndexPort);
        outb_p(portio->DataData, portio->DataPort);
}
static int smbus_open(struct inode *inode, struct file *file)
{
        do { if (smbusDebug & (1 << (0))) printk(KERN_DEBUG "smbus(%d):" "smbus_open(0x%p,0x%p)\n", (int)(jiffies-jiffies0), inode, file); } while (0);
        DRIVER_MOD_INC_USE_COUNT;
        return 0;
}
static int smbus_release(struct inode *inode, struct file *file)
{
        do { if (smbusDebug & (1 << (0))) printk(KERN_DEBUG "smbus(%d):" "smbus_release(0x%p,0x%p)\n", (int)(jiffies-jiffies0), inode, file); } while (0);
        DRIVER_MOD_DEC_USE_COUNT;
        return 0;
}
static int smbus_mmap(struct file *file, struct vm_area_struct *vma)
{
        int status;
        ulong start = (unsigned long)vma->vm_start;
        ulong size = (unsigned long)(vma->vm_end - vma->vm_start);
        do { if (smbusDebug & (1 << (0))) printk(KERN_DEBUG "smbus(%d):" "smbus_mmap(0x%p,0x%p) start 0x%lx, length %ld\n", (int)(jiffies-jiffies0), file, vma, start, size); } while (0);
        if (size < sizeof(BAPI_STATIC_BUF)) return -EINVAL;
        if (size > PAGE_SIZE) return -EINVAL;
        if (pBAPIStaticPage == NULL) return -ENODEV;
        status = DRIVER_REMAP_RANGE(vma, start, phys_BAPI_SP, size, vma->vm_page_prot);
        if (status != 0)
        {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_mmap: remap_page_range of 0x%lx failed: %d\n", (int)(jiffies-jiffies0), phys_BAPI_SP, status); } while (0);
                return -EAGAIN;
        }
        return 0;
}
long smbus_ioctl_compat(struct file *file, unsigned int cmd, unsigned long arg)
{
        return (long) smbus_ioctl(NULL, file, cmd, arg);
}
static int smbus_ioctl(struct inode *inode, struct file *file, unsigned int cmd, unsigned long arg)
{
        DWORD ulValue;
        unsigned int ioc_number = 0;
        unsigned int ioc_magic = 0;
        unsigned int ioc_size = 0;
        int err = 0;
        ioc_magic = _IOC_TYPE(cmd);
        ioc_size = _IOC_SIZE(cmd);
        ioc_number = _IOC_NR(cmd);
        do { if (smbusDebug & (1 << (0))) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: (%p,%p) IOCTL = 0x%08X, ioc_size = 0x%08X, arg = 0x%016lX\n", (int)(jiffies-jiffies0),(void *)inode, (void *)file, cmd, ioc_size, arg); } while (0);
        if (ioc_magic != 's') {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: CmdType != magic (0x%08X 0x%08X) !!!\n", (int)(jiffies-jiffies0), ioc_magic, 's'); } while (0);
                return -EINVAL;
        }
        if ((ioc_number < 0x00) || (ioc_number > 0x54)) {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: CmdNumber out of range (0x%08X [0x%08X 0x%08X]) !!! \n", (int)(jiffies-jiffies0), ioc_number, 0x00, 0x54); } while (0);
                return -EINVAL;
        }
        switch(ioc_number)
        {
                case 0x20:
                {
                        SMBI_HEADER *parg;
                        if (!IsSmbiHwFound || (m_pSmbiBase == NULL)) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBI not available ! m_pSmbiBase = 0x%p\n", (int)(jiffies-jiffies0), m_pSmbiBase); } while (0);
                                return -ENXIO;
                        }
                        parg = (SMBI_HEADER *) (unsigned long) arg;
                        if (parg == NULL) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: arg pointer is NULL !!! (0x%p) \n", (int)(jiffies-jiffies0), parg); } while (0);
                                return -EINVAL;
                        }
                        err = copy_to_user(parg, m_pSmbiBase, sizeof(SMBI_HEADER));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        return sizeof(SMBI_HEADER);
                }
                case 0x21:
                {
                        DWORD length;
                        SMBI_DATA smbi;
                        SMBI_DATA *parg;
                        BYTE *prequestdata;
                        BYTE *preplydata;
                        if (!IsSmbiHwFound || (m_pSmbiBase == NULL)) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBI not available ! m_pSmbiBase = 0x%p\n", (int)(jiffies-jiffies0), m_pSmbiBase); } while (0);
                                return -ENXIO;
                        }
                        parg = (SMBI_DATA *) (unsigned long) arg;
                        if (parg == NULL) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: arg pointer is NULL !!! (0x%p) \n", (int)(jiffies-jiffies0), parg); } while (0);
                                return -EINVAL;
                        }
                        err = copy_from_user(&smbi, (BYTE *)parg, sizeof(SMBI_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        prequestdata = (BYTE *)(unsigned long)(smbi.pCmdBuffer);
                        preplydata = (BYTE *)(unsigned long)(smbi.pResBuffer);
                        do { if (smbusDebug & (1 << (5))) printk(KERN_DEBUG "smbus(%d):" "SMBI cmd 0x%p(0x%08X) res 0x%p(0x%08X)\n", (int)(jiffies-jiffies0), prequestdata, smbi.CmdBufferLength, preplydata, smbi.ResBufferLength); } while (0);
                        if ((prequestdata == NULL) || (smbi.CmdBufferLength == 0)) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: invalid request len = 0x%08X, ptr = 0x%p\n", (int)(jiffies-jiffies0), smbi.CmdBufferLength, (BYTE *)prequestdata); } while (0);
                                return -EINVAL;
                        }
                        down(&smbus_mutex);
                        length = (smbi.CmdBufferLength < m_pSmbiBase->CMD_size) ? smbi.CmdBufferLength : m_pSmbiBase->CMD_size;
                        err = copy_from_user(ulASUSCmdBuffer, prequestdata, length);
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, prequestdata = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)prequestdata); } while (0);
                                up(&smbus_mutex);
                                return -EFAULT;
                        }
                        ASMX86(PUSH_RDX);
                        ASMX86(PUSH_RAX);
                        (*m_fSmbiExec)();
                        ASMX86(POP_RAX);
                        ASMX86(POP_RDX);
                        if ((preplydata == NULL) || (smbi.ResBufferLength == 0)) {
                                up(&smbus_mutex);
                                return 0;
                        }
                        length = ulASUSResultBuffer[1];
                        if (length > m_pSmbiBase->Result_size) length = m_pSmbiBase->Result_size;
                        if (length > smbi.ResBufferLength) length = smbi.ResBufferLength;
                        err = copy_to_user(preplydata, ulASUSResultBuffer, length);
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, preplydata = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)preplydata); } while (0);
                                up(&smbus_mutex);
                                return -EFAULT;
                        }
                        up(&smbus_mutex);
                        return 0;
                }
                case 0x10:
                {
                        BIOS_API_HEADER *parg;
                        if (!IsBapiHwFound || (m_pBapiBase == NULL)) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: BAPI not available ! m_pBapiBase = 0x%p\n", (int)(jiffies-jiffies0), m_pBapiBase); } while (0);
                                return -ENXIO;
                        }
                        parg = (BIOS_API_HEADER *) (unsigned long) arg;
                        if (parg == NULL) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: arg pointer is NULL !!! (0x%p) \n", (int)(jiffies-jiffies0), parg); } while (0);
                                return -EINVAL;
                        }
                        err = copy_to_user(parg, m_pBapiBase, sizeof(BIOS_API_HEADER));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        return sizeof(BIOS_API_HEADER);
                }
                case 0x11:
                {
                        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: obsolete BAPI-Ioctl -> ignoring ! (0x%p, 0x%p)\n", (int)(jiffies-jiffies0), m_pBapiBase, pBAPIStaticPage); } while (0);
                        return -EINVAL;
                }
                case 0x12:
                {
                        if (!IsBapiHwFound || (m_pBapiBase == NULL) || (pBAPIStaticPage == NULL)) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: BAPI not available ! (0x%p, 0x%p) \n", (int)(jiffies-jiffies0), m_pBapiBase, pBAPIStaticPage); } while (0);
                                return -ENXIO;
                        }
                        do { if (smbusDebug & (1 << (6))) printk(KERN_DEBUG "smbus(%d):" "BAPI-Cmd: inlen=0x%08X\n", (int)(jiffies-jiffies0), pBAPIStaticPage->Data.In.Length); } while (0);
                        down(&smbus_mutex);
                        smbus_CallBapi(phys_BAPI_DB, phys_BAPI_DB, phys_BAPI_CB, (BAPI_CMD_ROUTINE_VOID)m_fBapiExec);
                        up(&smbus_mutex);
                        do { if (smbusDebug & (1 << (6))) printk(KERN_DEBUG "smbus(%d):" "BAPI-Cmd: inlen=0x%08X\n", (int)(jiffies-jiffies0), pBAPIStaticPage->Data.Out.Length); } while (0);
                        return 0;
                }
                case 0x13:
                {
                        if (!IsBapiHwFound || (m_pBapiBase == NULL) || (pBAPIStaticPage == NULL)) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: BAPI not available ! (0x%p, 0x%p) \n", (int)(jiffies-jiffies0), m_pBapiBase, pBAPIStaticPage); } while (0);
                                return -ENXIO;
                        }
                        do { if (smbusDebug & (1 << (6))) printk(KERN_DEBUG "smbus(%d):" "BAPI-Ev: inlen=0x%08X\n", (int)(jiffies-jiffies0), pBAPIStaticPage->EventsIn.Ev.AsStruct.Length); } while (0);
                        down(&smbus_mutex);
                        smbus_CallBapi(phys_BAPI_EvIn, phys_BAPI_EvOut, phys_BAPI_CB, (BAPI_CMD_ROUTINE_VOID)m_fBapiExec);
                        up(&smbus_mutex);
                        do { if (smbusDebug & (1 << (6))) printk(KERN_DEBUG "smbus(%d):" "BAPI-Ev: outlen=0x%08X\n", (int)(jiffies-jiffies0), pBAPIStaticPage->EventsOut.Ev.AsStruct.Length); } while (0);
                        return 0;
                }
                case 0x14:
                {
                        if (!IsBapiHwFound || (m_pBapiBase == NULL) || (pBAPIStaticPage == NULL)) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: BAPI not available ! (0x%p, 0x%p) \n", (int)(jiffies-jiffies0), m_pBapiBase, pBAPIStaticPage); } while (0);
                                return -ENXIO;
                        }
                        do { if (smbusDebug & (1 << (6))) printk(KERN_DEBUG "smbus(%d):" "BAPI-MemErr: inlen=0x%08X\n", (int)(jiffies-jiffies0), pBAPIStaticPage->MemoryErrors.Mem.AsStruct.Length); } while (0);
                        down(&smbus_mutex);
                        smbus_CallBapi(phys_BAPI_MemErr, phys_BAPI_MemErr, phys_BAPI_CB, (BAPI_CMD_ROUTINE_VOID)m_fBapiExec);
                        up(&smbus_mutex);
                        do { if (smbusDebug & (1 << (6))) printk(KERN_DEBUG "smbus(%d):" "BAPI-MemErr: outlen=0x%08X\n", (int)(jiffies-jiffies0), pBAPIStaticPage->MemoryErrors.Mem.AsStruct.Length); } while (0);
                        return 0;
                }
                case 0x00:
                {
                        SMBUS_DATA smbus;
                        BYTE cByte;
                        SMBUS_DATA *parg;
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        parg = (SMBUS_DATA *) (unsigned long) arg;
                        if (parg == NULL) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: arg pointer is NULL !!! (0x%p) \n", (int)(jiffies-jiffies0), parg); } while (0);
                                return -EINVAL;
                        }
                        err = copy_from_user(&smbus, (BYTE *)parg, sizeof(SMBUS_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        do { if (smbusDebug & (1 << (9))) printk(KERN_DEBUG "smbus(%d):" "SMBUS dev 0x%08X off 0x%08X byte 0x%08X\n", (int)(jiffies-jiffies0), smbus.DeviceAddress, smbus.Command, (BYTE)smbus.Data); } while (0);
                        smbus.ReturnStatus = smbus_ReadByte((BYTE)(smbus.DeviceAddress), (BYTE)(smbus.Command), &cByte, 0);
                        smbus.Data = (DWORD)cByte;
                        err = copy_to_user(parg, &smbus, sizeof(SMBUS_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        return 0;
                }
                case 0x01:
                {
                        SMBUS_DATA smbus;
                        BYTE cByte;
                        SMBUS_DATA *parg;
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        parg = (SMBUS_DATA *) (unsigned long) arg;
                        if (parg == NULL) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: arg pointer is NULL !!! (0x%p) \n", (int)(jiffies-jiffies0), parg); } while (0);
                                return -EINVAL;
                        }
                        err = copy_from_user(&smbus, (BYTE *)parg, sizeof(SMBUS_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        cByte = (BYTE)(smbus.Data);
                        do { if (smbusDebug & (1 << (9))) printk(KERN_DEBUG "smbus(%d):" "SMBUS dev 0x%08X off 0x%08X\n", (int)(jiffies-jiffies0), smbus.DeviceAddress, smbus.Command); } while (0);
                        smbus.ReturnStatus = smbus_WriteByte((BYTE)(smbus.DeviceAddress), (BYTE)(smbus.Command), cByte, 0);
                        err = copy_to_user(parg, &smbus, sizeof(SMBUS_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        return 0;
                }
                case 0x02:
                {
                        SMBUS_DATA smbus;
                        BYTE SBuffer[sizeof(DWORD)];
                        PBYTE pBuffer = (BYTE *)SBuffer;
                        PBYTE pBAlloc = NULL;
                        DWORD iLength;
                        SMBUS_DATA *parg;
                        BYTE *pData;
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        parg = (SMBUS_DATA *) (unsigned long) arg;
                        if (parg == NULL) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: arg pointer is NULL !!! (0x%p) \n", (int)(jiffies-jiffies0), parg); } while (0);
                                return -EINVAL;
                        }
                        err = copy_from_user(&smbus, (BYTE *)arg, sizeof(SMBUS_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        pData = (BYTE *)(unsigned long)(smbus.pData);
                        do { if (smbusDebug & (1 << (9))) printk(KERN_DEBUG "smbus(%d):" "SMBUS dev 0x%08X off 0x%08X data 0x%p len %d\n", (int)(jiffies-jiffies0), smbus.DeviceAddress, smbus.Command, pData, smbus.DataLen); } while (0);
                        if ((pData == NULL) || (smbus.DataLen == 0) || (smbus.DataLen > 256)) return -EINVAL;
                        if (smbus.DataLen > sizeof SBuffer) {
                                pBAlloc = pBuffer = (PBYTE)kmalloc(smbus.DataLen, GFP_USER);
                                if (!pBAlloc) return -EAGAIN;
                        }
                        iLength = smbus_ReadData((BYTE)(smbus.DeviceAddress), (BYTE)(smbus.Command), pBuffer, smbus.DataLen);
                        smbus.ReturnStatus = (DWORD)(iLength == smbus.DataLen);
                        if (iLength > smbus.DataLen) iLength = smbus.DataLen;
                        if (iLength > 0) {
                                err = copy_to_user(pData, pBuffer, iLength);
                                if (err != 0) {
                                        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, pData = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)pData); } while (0);
                                        if (pBAlloc) kfree(pBAlloc);
                                        return -EFAULT;
                                }
                        }
                        smbus.DataLen = iLength;
                        err = copy_to_user(parg, &smbus, sizeof(SMBUS_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                if (pBAlloc) kfree(pBAlloc);
                                return -EFAULT;
                        }
                        if (pBAlloc) kfree(pBAlloc);
                        return 0;
                }
                case 0x03:
                {
                        SMBUS_DATA smbus;
                        BYTE SBuffer[sizeof(DWORD)];
                        PBYTE pBuffer = (BYTE *)SBuffer;
                        PBYTE pBAlloc = NULL;
                        DWORD iLength;
                        SMBUS_DATA *parg;
                        BYTE *pData;
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        parg = (SMBUS_DATA *) (unsigned long) arg;
                        if (parg == NULL) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: arg pointer is NULL !!! (0x%p) \n", (int)(jiffies-jiffies0), parg); } while (0);
                                return -EINVAL;
                        }
                        err = copy_from_user(&smbus, (BYTE *)arg, sizeof(SMBUS_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        pData = (BYTE *)(unsigned long)(smbus.pData);
                        if ((pData == NULL) || (smbus.DataLen == 0) || (smbus.DataLen > 256)) return -EINVAL;
                        do { if (smbusDebug & (1 << (9))) printk(KERN_DEBUG "smbus(%d):" "SMBUS dev 0x%08X off 0x%08X data 0x%p len %d\n", (int)(jiffies-jiffies0), smbus.DeviceAddress, smbus.Command, pData, smbus.DataLen); } while (0);
                        if (smbus.DataLen > sizeof SBuffer) {
                                pBAlloc = pBuffer = (PBYTE)kmalloc(smbus.DataLen, GFP_USER);
                                if (!pBAlloc) return -EAGAIN;
                        }
                        err = copy_from_user(pBuffer, (BYTE *)pData, smbus.DataLen);
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, pData = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)pData); } while (0);
                                if (pBAlloc) kfree(pBAlloc);
                                return -EFAULT;
                        }
                        iLength = smbus_WriteData((BYTE)(smbus.DeviceAddress), (BYTE)(smbus.Command), pBuffer, smbus.DataLen);
                        smbus.ReturnStatus = (DWORD)(iLength == smbus.DataLen);
                        if (iLength < smbus.DataLen) smbus.DataLen = iLength;
                        err = copy_to_user((BYTE *)parg, &smbus, sizeof(SMBUS_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                if (pBAlloc) kfree(pBAlloc);
                                return -EFAULT;
                        }
                        if (pBAlloc) kfree(pBAlloc);
                        return 0;
                }
                case 0x04:
                {
                        SMBUS_DEVICE_DATA smdev;
                        SMBUS_DEVICE_DATA *parg;
                        IOCTLDATA_SMBUS_OPEN_DEVICE *pMuxData = NULL;
                        SMBUS_MUX_ADDR *pUlMuxAddr;
                        SMBUS_MUX_ADDR *pMyMuxAddr;
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        parg = (SMBUS_DEVICE_DATA *) (unsigned long) arg;
                        if (parg == NULL) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: arg pointer is NULL !!! (0x%p) \n", (int)(jiffies-jiffies0), parg); } while (0);
                                return -EINVAL;
                        }
                        err = copy_from_user(&smdev, (BYTE *)parg, sizeof(SMBUS_DEVICE_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        pUlMuxAddr = (SMBUS_MUX_ADDR *)(unsigned long)(smdev.u.Open.pMuxAddr);
                        do { if (smbusDebug & (1 << (9))) printk(KERN_DEBUG "smbus(%d):" "SMDEV dev 0x%02x pmux 0x%p muxes %d\n", (int)(jiffies-jiffies0), smdev.u.Open.DeviceAddress, (BYTE *)pUlMuxAddr, smdev.u.Open.MuxesToProcess); } while (0);
                        if (smdev.u.Open.MuxesToProcess > 32) return -EINVAL;
                        if (pUlMuxAddr == NULL) smdev.u.Open.MuxesToProcess = 0;
                        if ((smdev.Success = (smbus_OpenDevice(&smdev.DeviceHandle) == 0)))
                        {
                                pMuxData = (IOCTLDATA_SMBUS_OPEN_DEVICE *)(OpenDevices[smdev.DeviceHandle]);
                                pMuxData->DeviceAddress = smdev.u.Open.DeviceAddress;
                                pMuxData->MuxesToProcess = smdev.u.Open.MuxesToProcess;
                                pMyMuxAddr = (SMBUS_MUX_ADDR *)(unsigned long)(pMuxData->pMuxAddr);
                                if (smdev.u.Open.MuxesToProcess > 0)
                                {
                                        err = copy_from_user(pMyMuxAddr, pUlMuxAddr, (smdev.u.Open.MuxesToProcess * sizeof(SMBUS_MUX_ADDR)));
                                        if (err != 0) {
                                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, pUlMuxAddr = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)pUlMuxAddr); } while (0);
                                                OpenDevices[smdev.DeviceHandle] = NULL;
                                                return -EFAULT;
                                        }
                                }
                        }
                        err = copy_to_user((BYTE *)parg, &smdev, sizeof(SMBUS_DEVICE_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                OpenDevices[smdev.DeviceHandle] = NULL;
                                return -EFAULT;
                        }
                        return 0;
                }
                case 0x05:
                {
                        SMBUS_DEVICE_DATA smdev;
                        SMBUS_DEVICE_DATA *parg;
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        parg = (SMBUS_DEVICE_DATA *) (unsigned long) arg;
                        if (parg == NULL) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: arg pointer is NULL !!! (0x%p) \n", (int)(jiffies-jiffies0), parg); } while (0);
                                return -EINVAL;
                        }
                        err = copy_from_user(&smdev, (BYTE *)parg, sizeof(SMBUS_DEVICE_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        do { if (smbusDebug & (1 << (9))) printk(KERN_DEBUG "smbus(%d):" "SMDEV handle %d \n", (int)(jiffies-jiffies0), smdev.DeviceHandle); } while (0);
                        smdev.Success = (smbus_CloseDevice(smdev.DeviceHandle) == 0);
                        err = copy_to_user(parg, &smdev, sizeof(SMBUS_DEVICE_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        return 0;
                }
                case 0x06:
                {
                        SMBUS_DEVICE_DATA smdev;
                        SMBUS_DEVICE_DATA *parg;
                        BYTE SBuffer[sizeof(DWORD)];
                        BYTE *pBuffer = SBuffer;
                        BYTE *pBAlloc = NULL;
                        DWORD iLength;
                        BYTE *pProcessData;
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        parg = (SMBUS_DEVICE_DATA *) (unsigned long) arg;
                        if (parg == NULL) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: arg pointer is NULL !!! (0x%p) \n", (int)(jiffies-jiffies0), parg); } while (0);
                                return -EINVAL;
                        }
                        err = copy_from_user(&smdev, (BYTE *)parg, sizeof(SMBUS_DEVICE_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        pProcessData = (BYTE *)(unsigned long)(smdev.u.Access.pProcessData);
                        do { if (smbusDebug & (1 << (9))) printk(KERN_DEBUG "smbus(%d):" "SMDEV handle %d off %d data 0x%p len %d\n", (int)(jiffies-jiffies0), smdev.DeviceHandle, smdev.u.Access.StartOffset, pProcessData, smdev.u.Access.BytesToProcess); } while (0);
                        if ((pProcessData == NULL) || (smdev.u.Access.BytesToProcess == 0) || (smdev.u.Access.BytesToProcess > 256)) return -EINVAL;
                        if (smdev.u.Access.BytesToProcess > sizeof SBuffer)
                        {
                                pBAlloc = pBuffer = (BYTE *)kmalloc(smdev.u.Access.BytesToProcess, GFP_USER);
                                if (!pBAlloc) return -EAGAIN;
                        }
                        smdev.Success = (smbus_ReadDevice(smdev.DeviceHandle, smdev.u.Access.StartOffset, smdev.u.Access.BytesToProcess, pBuffer, &iLength) == 0);
                        if (iLength > smdev.u.Access.BytesToProcess) iLength = smdev.u.Access.BytesToProcess;
                        if (iLength > 0) {
                                err = copy_to_user(pProcessData, pBuffer, iLength);
                                if (err != 0) {
                                        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, pProcessData = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)pProcessData); } while (0);
                                        if (pBAlloc) kfree(pBAlloc);
                                        return -EFAULT;
                                }
                        }
                        smdev.u.Access.BytesToProcess = iLength;
                        err = copy_to_user((BYTE *)parg, &smdev, sizeof(SMBUS_DEVICE_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                if (pBAlloc) kfree(pBAlloc);
                                return -EFAULT;
                        }
                        if (pBAlloc) kfree(pBAlloc);
                        return 0;
                }
                case 0x07:
                {
                        SMBUS_DEVICE_DATA smdev;
                        SMBUS_DEVICE_DATA *parg;
                        BYTE SBuffer[sizeof(DWORD)];
                        BYTE *pBuffer = SBuffer;
                        BYTE *pBAlloc = NULL;
                        BYTE *pProcessData;
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        parg = (SMBUS_DEVICE_DATA *) (unsigned long) arg;
                        if (parg == NULL) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: arg pointer is NULL !!! (0x%p) \n", (int)(jiffies-jiffies0), parg); } while (0);
                                return -EINVAL;
                        }
                        err = copy_from_user(&smdev, (BYTE *)parg, sizeof(SMBUS_DEVICE_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                return -EFAULT;
                        }
                        pProcessData = (BYTE *)(unsigned long)(smdev.u.Access.pProcessData);
                        do { if (smbusDebug & (1 << (9))) printk(KERN_DEBUG "smbus(%d):" "SMDEV handle %d off %d data 0x%p len %d\n", (int)(jiffies-jiffies0), smdev.DeviceHandle, smdev.u.Access.StartOffset, pProcessData, smdev.u.Access.BytesToProcess); } while (0);
                        if ((pProcessData == NULL) || (smdev.u.Access.BytesToProcess == 0) || (smdev.u.Access.BytesToProcess > 256)) return -EINVAL;
                        if (smdev.u.Access.BytesToProcess > sizeof SBuffer)
                        {
                                pBAlloc = pBuffer = (BYTE *) kmalloc(smdev.u.Access.BytesToProcess, GFP_USER);
                                if (!pBAlloc) return -EAGAIN;
                        }
                        err = copy_from_user(pBuffer, pProcessData, smdev.u.Access.BytesToProcess);
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_from_user failed err = 0x%08X, pProcessData = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)pProcessData); } while (0);
                                if (pBAlloc) kfree(pBAlloc);
                                return -EFAULT;
                        }
                        smdev.Success = (smbus_WriteDevice(smdev.DeviceHandle, smdev.u.Access.StartOffset, smdev.u.Access.BytesToProcess, pBuffer) == 0);
                        err = copy_to_user((BYTE *)parg, &smdev, sizeof(SMBUS_DEVICE_DATA));
                        if (err != 0) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg); } while (0);
                                if (pBAlloc) kfree(pBAlloc);
                                return -EFAULT;
                        }
                        if (pBAlloc) kfree(pBAlloc);
                        return 0;
                }
                case 0x31:
                {
                        IOCTLDATA_INDEXED_PORT_IO portio;
                        if (!IsBusIoHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        err = copy_from_user(&portio, (IOCTLDATA_INDEXED_PORT_IO *)arg, sizeof(IOCTLDATA_INDEXED_PORT_IO));
                        do { if (smbusDebug & (1 << (7))) printk(KERN_DEBUG "smbus(%d):" "PORTIO index 0x%02x=0x%02x data 0x%02x\n", (int)(jiffies-jiffies0), portio.IndexPort, portio.IndexData, portio.DataPort); } while (0);
                        ReadFromIndexedPort(&portio);
                        err = copy_to_user((IOCTLDATA_INDEXED_PORT_IO *)arg, &portio, sizeof(IOCTLDATA_INDEXED_PORT_IO));
                        return sizeof(IOCTLDATA_INDEXED_PORT_IO);
                }
                case 0x30:
                {
                        IOCTLDATA_INDEXED_PORT_IO portio;
                        if (!IsBusIoHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        err = copy_from_user(&portio, (IOCTLDATA_INDEXED_PORT_IO *)arg, sizeof(IOCTLDATA_INDEXED_PORT_IO));
                        do { if (smbusDebug & (1 << (7))) printk(KERN_DEBUG "smbus(%d):" "PORTIO index 0x%02x=0x%02x data 0x%02x=0x%02x\n", (int)(jiffies-jiffies0), portio.IndexPort, portio.IndexData, portio.DataPort, portio.DataData); } while (0);
                        WriteToIndexedPort(&portio);
                        err = copy_to_user((IOCTLDATA_INDEXED_PORT_IO *)arg, &portio, sizeof(IOCTLDATA_INDEXED_PORT_IO));
                        return 0;
                }
                case 0x32:
                {
                        IOCTLDATA_GEN_IO genio;
                        if (!IsBusIoHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        err = copy_from_user(&genio, (IOCTLDATA_GEN_IO *)arg, sizeof(IOCTLDATA_GEN_IO));
                        do { if (smbusDebug & (1 << (10))) printk(KERN_DEBUG "smbus(%d):" "GENIO [%d] of 0x%08x\n", (int)(jiffies-jiffies0), genio.DataWidth, genio.Address); } while (0);
                        if (genio.Address >= (1 << (sizeof(unsigned short) * 8))) return -EINVAL;
                        genio.WriteData = 0L;
                        switch(genio.DataWidth)
                        {
                                case sizeof(BYTE):
                                        genio.WriteData = (DWORD)inb((unsigned short)genio.Address);
                                        break;
                                case sizeof(WORD):
                                        genio.WriteData = (DWORD)inw((unsigned short)genio.Address);
                                        break;
                                case sizeof(DWORD):
                                        genio.WriteData = (DWORD)inl((unsigned short)genio.Address);
                                        break;
                                default:
                                        return -EINVAL;
                        }
                        err = copy_to_user((IOCTLDATA_GEN_IO *)arg, &genio, sizeof(IOCTLDATA_GEN_IO));
                        return 0;
                }
                case 0x33:
                {
                        IOCTLDATA_GEN_IO genio;
                        if (!IsBusIoHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        err = copy_from_user(&genio, (IOCTLDATA_GEN_IO *)arg, sizeof(IOCTLDATA_GEN_IO));
                        do { if (smbusDebug & (1 << (10))) printk(KERN_DEBUG "smbus(%d):" "GENIO [%d]0x%08x to 0x%08x\n", (int)(jiffies-jiffies0), genio.DataWidth, genio.WriteData, genio.Address); } while (0);
                        if (genio.Address >= (1 << (sizeof(unsigned short) * 8))) return -EINVAL;
                        switch(genio.DataWidth)
                        {
                                case sizeof(BYTE):
                                        if (genio.WriteData >= (1 << (sizeof(unsigned char) * 8))) return -EINVAL;
                                        outb((BYTE)genio.WriteData, (unsigned short)genio.Address);
                                        break;
                                case sizeof(WORD):
                                        if (genio.WriteData >= (1 << (sizeof(unsigned short) * 8))) return -EINVAL;
                                        outw((WORD)genio.WriteData, (unsigned short)genio.Address);
                                        break;
                                case sizeof(DWORD):
                                        outl((DWORD)genio.WriteData, (unsigned short)genio.Address);
                                        break;
                                default:
                                        return -EINVAL;
                        }
                        err = copy_to_user((IOCTLDATA_GEN_IO *)arg, &genio, sizeof(IOCTLDATA_GEN_IO));
                        return 0;
                }
                case 0x08:
                {
                        IOCTLDATA_SMBUS_MASTER_INFO MasterInfo;
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        if ((SmBusDeviceIndex == -1) || (ulSMBusBaseAddress == 0)) return -EIO;
                        MasterInfo.BaseAddress = (DWORD)ulSMBusBaseAddress;
                        MasterInfo.DeviceId = SmBusIoBaseAddresses[SmBusDeviceIndex].DeviceId;
                        MasterInfo.VendorId = SmBusIoBaseAddresses[SmBusDeviceIndex].VendorId;
                        err = copy_to_user((IOCTLDATA_SMBUS_MASTER_INFO *)arg, &MasterInfo, sizeof(IOCTLDATA_SMBUS_MASTER_INFO));
                        return 0;
                }
                case 0x09:
                {
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        do { if (smbusDebug & (1 << (9))) printk(KERN_DEBUG "smbus(%d):" "ScSmbusDevice IOCTL: Reset Master Device (0x%08X)\n", (int)(jiffies-jiffies0),ulValue); } while (0);
                        if (!smbus_ResetSMBusCtrl())
                        return -1;
                }
                case 0x50:
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        ulValue = CheckForIntrusionSupport();
                        err = copy_to_user((DWORD *)arg, &ulValue, sizeof(DWORD));
                        do { if (smbusDebug & (1 << (8))) printk(KERN_DEBUG "smbus(%d):" "INTRUSION support 0x%08X\n", (int)(jiffies-jiffies0), ulValue); } while (0);
                        return 0;
                case 0x51:
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        ulValue = CheckForCabinetIntrusion();
                        err = copy_to_user((DWORD *)arg, &ulValue, sizeof(DWORD));
                        do { if (smbusDebug & (1 << (8))) printk(KERN_DEBUG "smbus(%d):" "INTRUSION state 0x%08X\n", (int)(jiffies-jiffies0), ulValue); } while (0);
                        return 0;
                case 0x54:
                        if (smbusArchMode & 0x40000000)
                        {
                                return -ENXIO;
                        }
                        if (IsSmbiHwFound && m_pSmbiBase != NULL)
                        {
                                asus_PowerDown(ulASUSCmdBuffer, ulASUSResultBuffer, m_fSmbiExec);
                        }
                        else
                        {
                                smbus_PowerDown();
                        }
                        return -ENXIO;
                case 0x52:
                        if (!IsSmbusHwFound) {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: WARNING: SMBUS not available (IsSmbusHwFound = %d) !\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
                                return -ENXIO;
                        }
                        ulValue = 0x00;
                        if (m_pSmbiBase)
                        {
                                ulValue = 0x80;
                        }
                        else
                        {
                                (void)smbus_CheckHardwareType(&ulValue);
                        }
                        err = copy_to_user((DWORD *)arg, &ulValue, sizeof(DWORD));
                        return 0;
                case 0x40:
                {
                        INT cpunr;
                        CpuInfo *pentry;
                        CpuErrorInfo CpuErrInfo;
                        CpuErrorInfo *pCpuErrInfo = &CpuErrInfo;
                        IOCTLDATA_CORR_CPU_ERROR CpuError;
                        if (!IsCpuErrHwFound)
                        {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: IOCTL_DEVBUSIO_GET_CPU_ERROR not supported!\n", (int)(jiffies-jiffies0)); } while (0);
                                return -ENXIO;
                        }
                        err = copy_from_user(&CpuError, (IOCTLDATA_CORR_CPU_ERROR *)arg, sizeof(IOCTLDATA_CORR_CPU_ERROR));
                        cpunr = CpuError.LogicalCpuNumber;
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: IOCTL_DEVBUSIO_GET_CPU_ERROR for CPU %02d\n", (int)(jiffies-jiffies0), cpunr); } while (0);
                        if ((cpunr > SMP_NUM_CPUS) || (cpunr > 128))
                        {
                                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR !!! (geting cpu errors) invalid CPU Number = %d\n", (int)(jiffies-jiffies0), cpunr); } while (0);
                                return -EINVAL;
                        }
                        pentry = &smbus_cpuinfotable[cpunr];
                        if (pentry->MachineCheckArchitectureSupported)
                        {
                                memset (&CpuError, 0, sizeof(IOCTLDATA_CORR_CPU_ERROR));
                                CpuError.ErrorType = CPUERR_TYPE_NO_ERROR;
                                pCpuErrInfo->pCpuError = &CpuError;
                                pCpuErrInfo->DenseCpuNr = cpunr;
                                smbus_do_GetCpuError(pCpuErrInfo);
                                CpuError.LogicalCpuNumber = cpunr;
                                err = copy_to_user((IOCTLDATA_CORR_CPU_ERROR *)arg, &CpuError, sizeof(IOCTLDATA_CORR_CPU_ERROR));
                                return 0;
                        } else {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: Machine Check Architecure not supported!\n", (int)(jiffies-jiffies0)); } while (0);
                                return -ENXIO;
                        }
                        return 0;
                }
                case 0x41:
                {
                        INT cpunr;
                        CpuInfo *pentry;
                        IOCTLDATA_CPU_APICID_BOOT_CPU ApicInfo;
                        if (!IsCpuApicHwFound)
                        {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: IOCTL_DEVBUSIO_GET_CPU_LOCAL_APIC_ID not supported!\n", (int)(jiffies-jiffies0)); } while (0);
                                return -ENXIO;
                        }
                        err = copy_from_user(&ApicInfo, (IOCTLDATA_CPU_APICID_BOOT_CPU *)arg, sizeof(IOCTLDATA_CPU_APICID_BOOT_CPU));
                        cpunr = ApicInfo.LogicalCpuNumber;
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: IOCTL_DEVBUSIO_GET_CPU_LOCAL_APIC_ID for CPU %02d\n", (int)(jiffies-jiffies0), cpunr); } while (0);
                        if ((cpunr > SMP_NUM_CPUS) || (cpunr > 128))
                        {
                                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR !!! (geting local ApicId) invalid CPU Number = %d\n", (int)(jiffies-jiffies0), cpunr); } while (0);
                                return -EINVAL;
                        }
                        pentry = &smbus_cpuinfotable[cpunr];
                        if (pentry->LocalApicSupported) {
                                if (pentry->MachineCheckArchitectureSupported) {
                                        if (pentry->ApicGlobalEnable) {
                                                if (pentry->ApicIdValid) {
                                                        ApicInfo.LocalApicId = pentry->ApicId;
                                                        ApicInfo.IsBootCpu = pentry->BootstrapCpu;
                                                        err = copy_to_user((IOCTLDATA_CPU_APICID_BOOT_CPU *)arg, &ApicInfo, sizeof(IOCTLDATA_CPU_APICID_BOOT_CPU));
                                                        return 0;
                                                } else {
                                                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ## ERROR: APIC Id for CPU %d not available\n", (int)(jiffies-jiffies0), cpunr); } while (0);
                                                        return -ENXIO;
                                                }
                                        } else {
                                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ## Local APIC not enabled!\n", (int)(jiffies-jiffies0)); } while (0);
                                                return -ENXIO;
                                        }
                                } else {
                                        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ## Machine Check Architecture (MCA) not supported!\n", (int)(jiffies-jiffies0)); } while (0);
                                        return -ENXIO;
                                }
                        } else {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ## Local APIC not supported!\n", (int)(jiffies-jiffies0)); } while (0);
                                return -ENXIO;
                        }
                        return 0;
                }
                case 0x42:
                {
                        INT cpunr;
                        CpuInfo *pentry;
                        IOCTLDATA_CPU_INFO LocalData;
                        if (!IsCpuInfoHwFound)
                        {
                                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: IOCTL_DEVBUSIO_GET_CPU_INFO not supported!\n", (int)(jiffies-jiffies0)); } while (0);
                                return -ENXIO;
                        }
                        err = copy_from_user(&LocalData, (IOCTLDATA_CPU_INFO *)arg, sizeof(IOCTLDATA_CPU_INFO));
                        cpunr = LocalData.LogicalCpuNumber;
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: IOCTL_DEVBUSIO_GET_CPU_INFO for CPU %02d\n", (int)(jiffies-jiffies0), cpunr); } while (0);
                        if ((cpunr > SMP_NUM_CPUS) || (cpunr > 128))
                        {
                                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: ERROR !!! (geting CPU Info) invalid CPU Number = %d\n", (int)(jiffies-jiffies0), cpunr); } while (0);
                                return -EINVAL;
                        }
                        pentry = &smbus_cpuinfotable[cpunr];
                        LocalData.DenseCpuNr = pentry->DenseCpuNr;
                        LocalData.SparseCpuNr = pentry->SparseCpuNr;
                        LocalData.regs1Valid = pentry->regs1Valid;
                        LocalData.regs2Valid = pentry->regs2Valid;
                        LocalData.regs3Valid = pentry->regs3Valid;
                        LocalData.regs4Valid = pentry->regs4Valid;
                        LocalData.BrandStringValid = pentry->BrandStringValid;
                        LocalData.NrCoresAMDValid = pentry->NrCoresAMDValid;
                        LocalData.MachineCheckArchitectureSupported = pentry->MachineCheckArchitectureSupported;
                        LocalData.LocalApicSupported = pentry->LocalApicSupported;
                        LocalData.PrimaryLogicalCpu = pentry->PrimaryLogicalCpu;
                        LocalData.LocalApicIdInitial = pentry->LocalApicIdInitial;
                        LocalData.Vendor = pentry->Vendor;
                        LocalData.NrCores = pentry->NrCores;
                        LocalData.NumberLogicalCpus = pentry->NumberLogicalCpus;
                        LocalData.regs0.eax = pentry->regs0.eax;
                        LocalData.regs0.ebx = pentry->regs0.ebx;
                        LocalData.regs0.ecx = pentry->regs0.ecx;
                        LocalData.regs0.edx = pentry->regs0.edx;
                        LocalData.regs1.eax = pentry->regs1.eax;
                        LocalData.regs1.ebx = pentry->regs1.ebx;
                        LocalData.regs1.ecx = pentry->regs1.ecx;
                        LocalData.regs1.edx = pentry->regs1.edx;
                        LocalData.regs2.eax = pentry->regs2.eax;
                        LocalData.regs2.ebx = pentry->regs2.ebx;
                        LocalData.regs2.ecx = pentry->regs2.ecx;
                        LocalData.regs2.edx = pentry->regs2.edx;
                        LocalData.regs3.eax = pentry->regs3.eax;
                        LocalData.regs3.ebx = pentry->regs3.ebx;
                        LocalData.regs3.ecx = pentry->regs3.ecx;
                        LocalData.regs3.edx = pentry->regs3.edx;
                        LocalData.regs4.eax = pentry->regs4.eax;
                        LocalData.regs4.ebx = pentry->regs4.ebx;
                        LocalData.regs4.ecx = pentry->regs4.ecx;
                        LocalData.regs4.edx = pentry->regs4.edx;
                        LocalData.MaxExtentions.eax = pentry->MaxExtentions.eax;
                        LocalData.MaxExtentions.ebx = pentry->MaxExtentions.ebx;
                        LocalData.MaxExtentions.ecx = pentry->MaxExtentions.ecx;
                        LocalData.MaxExtentions.edx = pentry->MaxExtentions.edx;
                        LocalData.BrandString1.eax = pentry->BrandString1.eax;
                        LocalData.BrandString1.ebx = pentry->BrandString1.ebx;
                        LocalData.BrandString1.ecx = pentry->BrandString1.ecx;
                        LocalData.BrandString1.edx = pentry->BrandString1.edx;
                        LocalData.BrandString2.eax = pentry->BrandString2.eax;
                        LocalData.BrandString2.ebx = pentry->BrandString2.ebx;
                        LocalData.BrandString2.ecx = pentry->BrandString2.ecx;
                        LocalData.BrandString2.edx = pentry->BrandString2.edx;
                        LocalData.BrandString3.eax = pentry->BrandString3.eax;
                        LocalData.BrandString3.ebx = pentry->BrandString3.ebx;
                        LocalData.BrandString3.ecx = pentry->BrandString3.ecx;
                        LocalData.BrandString3.edx = pentry->BrandString3.edx;
                        LocalData.NrCoresAMD.eax = pentry->NrCoresAMD.eax;
                        LocalData.NrCoresAMD.ebx = pentry->NrCoresAMD.ebx;
                        LocalData.NrCoresAMD.ecx = pentry->NrCoresAMD.ecx;
                        LocalData.NrCoresAMD.edx = pentry->NrCoresAMD.edx;
                        LocalData.BootstrapCpu = pentry->BootstrapCpu;
                        LocalData.ApicGlobalEnable = pentry->ApicGlobalEnable;
                        LocalData.ApicIdValid = pentry->ApicIdValid;
                        LocalData.ApicId = pentry->ApicId;
                        LocalData.ApicBaseMsr = pentry->ApicBaseMsr;
                        LocalData.ApicBaseAddress = pentry->ApicBaseAddress;
                        LocalData.IsIA64Architecture = pentry->IsIA64Architecture;
                        LocalData.IA64Data.IA64regs.rg0 = pentry->IA64Data.IA64regs.rg0;
                        LocalData.IA64Data.IA64regs.rg1 = pentry->IA64Data.IA64regs.rg1;
                        LocalData.IA64Data.IA64regs.rg2 = pentry->IA64Data.IA64regs.rg2;
                        LocalData.IA64Data.IA64regs.rg3 = pentry->IA64Data.IA64regs.rg3;
                        LocalData.IA64Data.IA64regs.rg4 = pentry->IA64Data.IA64regs.rg4;
                        err = copy_to_user((IOCTLDATA_CPU_INFO *)arg, &LocalData, sizeof(IOCTLDATA_CPU_INFO));
                        return 0;
                }
        }
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ioctl: unsupported ioctl nr %d, size %d\n", (int)(jiffies-jiffies0), _IOC_NR(cmd), _IOC_SIZE(cmd)); } while (0);
        return -EINVAL;
}
static int smbus_DetermineEnvironment(void)
{
        char *pointer = NULL;
        if (smbusArchMode == 0x00000000) {
                smbusArchMode |= DRIVER_REMAP_RANGE_INTF;
                smbusArchMode |= DRIVER_KERNEL_MODE;
                smbusArchMode |= DRIVER_POWEROFF_ROUTINE;
                smbusArchMode |= DRIVER_MODULE_INTERACTION;
                smbusArchMode |= DRIVER_IOCTL32_CONV;
                if (sizeof(pointer) == 4) {
                        smbusArchMode |= 0x10000000;
                } else if (sizeof(pointer) == 8) {
                        smbusArchMode |= DRIVER_64BIT_MODE;
                } else {
                        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: unknown XX-Bit mode (%d)\n", (int)(jiffies-jiffies0),0); } while (0);
                        return -1;
                }
        } else {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: has been determined by insmod\n", (int)(jiffies-jiffies0)); } while (0);
        }
        if ( smbusArchMode & 0x10000000 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: IA32 (x86) mode is active, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x40000000 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: IA64 mode is active, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x20000000 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: __x86_64__ mode    is active, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x01000000 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: KERNEL 2.4    mode is active, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x02000000 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: KERNEL 2.6    mode is active, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x04000000 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: KERNEL 2.6.16 mode is active, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x00000100 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: OLD_REMAP_INTF     is active, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x00000200 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: NEW_REMAP_INTF     is active, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x00000400 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: PFN_REMAP_INTF     is active, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x00000010 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: IOCTL32_CONVERSION is active, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x00000020 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: IOCTL32_COMPAT     is active, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x00000001 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: OS pm_power_off       is used, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x00000002 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: My smbus_pm_power_off is used, (0x%08X)\n", (int)(jiffies-jiffies0),smbusArchMode); } while (0);
        if ( smbusArchMode & 0x00000004 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: inter_module_xxx() functions are used\n", (int)(jiffies-jiffies0)); } while (0);
        if ( smbusArchMode & 0x00000008 ) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "Environment: symbol_get/put()   functions are used\n", (int)(jiffies-jiffies0)); } while (0);
        return 0;
}
static int smbus_register_ioctl32 (unsigned int cmd, char *name)
{
        int ret = 0;
        REGISTER_IOCTL32_CONVERSION(ret, cmd);
        if (ret < 0) {
                printk(KERN_ERR "smbus(%d): " "smbus_register_ioctl32: unable to register %s, ret=%d\n", (int)(jiffies-jiffies0),name, ret);
                return ret;
        } else {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_ioctl32: successfully registered %s\n", (int)(jiffies-jiffies0),name); } while (0);
        }
        return 0;
}
static int smbus_register_ioctl32_all (void)
{
        int ret;
        if ( !(smbusArchMode & 0x00000010) ) return 0;
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_ioctl32_all: register ioctl32 commands (%d)\n", (int)(jiffies-jiffies0),0); } while (0);
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x00, SMBUS_DATA), "IOCTL_DEVSMBUS_READ_SMBUS_ONE_BYTE" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOW('s', 0x01, SMBUS_DATA), "IOCTL_DEVSMBUS_WRITE_SMBUS_ONE_BYTE" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x50, DWORD), "IOCTL_CHECK_INTRUSION_SUPPORT" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x51, DWORD), "IOCTL_GET_INTRUSION_STATE" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IO('s', 0x54), "IOCTL_POWER_OFF" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOW('s', 0x20, SMBI_HEADER), "IOCTL_DEVBIOS_SMBI_INFO" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOWR('s',0x21, SMBI_DATA), "IOCTL_DEVBIOS_SMBI_CMD" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x52, DWORD), "IOCTL_GET_CHIPID" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOW('s', 0x30, IOCTLDATA_INDEXED_PORT_IO), "IOCTL_DEVBUSIO_INDEXED_PORT_OUT" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x31, IOCTLDATA_INDEXED_PORT_IO), "IOCTL_DEVBUSIO_INDEXED_PORT_IN" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x10, BIOS_API_HEADER), "IOCTL_DEVBAPI_BAPI_INFO" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOWR('s',0x11 , DWORD), "IOCTL_DEVBAPI_BAPI_CMD" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOWR('s',0x12, DWORD), "IOCTL_DEVBAPI_BAPI_CMD_EX" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x02, SMBUS_DATA), "IOCTL_DEVSMBUS_READ_SMBUS_DATA" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x03, SMBUS_DATA), "IOCTL_DEVSMBUS_WRITE_SMBUS_DATA" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOWR('s',0x04, SMBUS_DEVICE_DATA), "IOCTL_DEVSMBUS_OPEN_DEVICE" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x05, SMBUS_DEVICE_DATA), "IOCTL_DEVSMBUS_CLOSE_DEVICE" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x06, SMBUS_DEVICE_DATA), "IOCTL_DEVSMBUS_READ_DEVICE" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOW('s', 0x07, SMBUS_DEVICE_DATA), "IOCTL_DEVSMBUS_WRITE_DEVICE" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOWR('s',0x13, DWORD), "IOCTL_DEVBAPI_BAPI_CONNECT_EVENTS" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOWR('s',0x14, DWORD), "IOCTL_DEVBAPI_BAPI_CONNECT_MEM_ERRS" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x32, IOCTLDATA_GEN_IO), "IOCTL_DEVBUSIO_GENERIC_PORT_IN" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOW('s', 0x33, IOCTLDATA_GEN_IO), "IOCTL_DEVBUSIO_GENERIC_PORT_OUT" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x08, IOCTLDATA_SMBUS_MASTER_INFO), "IOCTL_DEVSMBUS_MASTER_INFO" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IO('s', 0x09), "IOCTL_DEVSMBUS_RESET_MASTER" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x40, IOCTLDATA_CORR_CPU_ERROR), "IOCTL_DEVBUSIO_GET_CPU_ERROR" )) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x41,IOCTLDATA_CPU_APICID_BOOT_CPU),"IOCTL_DEVBUSIO_GET_CPU_LOCAL_APIC_ID")) < 0) return ret;
        if ((ret = smbus_register_ioctl32(_IOR('s', 0x42, IOCTLDATA_CPU_INFO), "IOCTL_DEVBUSIO_GET_CPU_INFO" )) < 0) return ret;
        return 0;
}
static void smbus_unregister_ioctl32 (unsigned int cmd, char *name)
{
        int ret = 0;
        UNREGISTER_IOCTL32_CONVERSION(ret, cmd);
        if (ret < 0) {
                printk(KERN_ERR "smbus(%d): " "smbus_unregister_ioctl32: unable to unregister %s, ret=%d\n", (int)(jiffies-jiffies0),name, ret);
        } else {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_unregister_ioctl32: successfully unregistered %s\n", (int)(jiffies-jiffies0),name); } while (0);
        }
        return;
}
static void smbus_unregister_ioctl32_all (void)
{
        if ( !(smbusArchMode & 0x00000010) ) return;
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_unregister_ioctl32_all: unregister ioctl32 commands (%d)\n", (int)(jiffies-jiffies0),0); } while (0);
        smbus_unregister_ioctl32(_IOR('s', 0x00, SMBUS_DATA), "IOCTL_DEVSMBUS_READ_SMBUS_ONE_BYTE" );
        smbus_unregister_ioctl32(_IOW('s', 0x01, SMBUS_DATA), "IOCTL_DEVSMBUS_WRITE_SMBUS_ONE_BYTE" );
        smbus_unregister_ioctl32(_IOR('s', 0x50, DWORD), "IOCTL_CHECK_INTRUSION_SUPPORT" );
        smbus_unregister_ioctl32(_IOR('s', 0x51, DWORD), "IOCTL_GET_INTRUSION_STATE" );
        smbus_unregister_ioctl32(_IO('s', 0x54), "IOCTL_POWER_OFF" );
        smbus_unregister_ioctl32(_IOW('s', 0x20, SMBI_HEADER), "IOCTL_DEVBIOS_SMBI_INFO" );
        smbus_unregister_ioctl32(_IOWR('s',0x21, SMBI_DATA), "IOCTL_DEVBIOS_SMBI_CMD" );
        smbus_unregister_ioctl32(_IOR('s', 0x52, DWORD), "IOCTL_GET_CHIPID" );
        smbus_unregister_ioctl32(_IOW('s', 0x30, IOCTLDATA_INDEXED_PORT_IO), "IOCTL_DEVBUSIO_INDEXED_PORT_OUT" );
        smbus_unregister_ioctl32(_IOR('s', 0x31, IOCTLDATA_INDEXED_PORT_IO), "IOCTL_DEVBUSIO_INDEXED_PORT_IN" );
        smbus_unregister_ioctl32(_IOR('s', 0x10, BIOS_API_HEADER), "IOCTL_DEVBAPI_BAPI_INFO" );
        smbus_unregister_ioctl32(_IOWR('s',0x11 , DWORD), "IOCTL_DEVBAPI_BAPI_CMD" );
        smbus_unregister_ioctl32(_IOWR('s',0x12, DWORD), "IOCTL_DEVBAPI_BAPI_CMD_EX" );
        smbus_unregister_ioctl32(_IOR('s', 0x02, SMBUS_DATA), "IOCTL_DEVSMBUS_READ_SMBUS_DATA" );
        smbus_unregister_ioctl32(_IOR('s', 0x03, SMBUS_DATA), "IOCTL_DEVSMBUS_WRITE_SMBUS_DATA" );
        smbus_unregister_ioctl32(_IOWR('s',0x04, SMBUS_DEVICE_DATA), "IOCTL_DEVSMBUS_OPEN_DEVICE" );
        smbus_unregister_ioctl32(_IOR('s', 0x05, SMBUS_DEVICE_DATA), "IOCTL_DEVSMBUS_CLOSE_DEVICE" );
        smbus_unregister_ioctl32(_IOR('s', 0x06, SMBUS_DEVICE_DATA), "IOCTL_DEVSMBUS_READ_DEVICE" );
        smbus_unregister_ioctl32(_IOW('s', 0x07, SMBUS_DEVICE_DATA), "IOCTL_DEVSMBUS_WRITE_DEVICE" );
        smbus_unregister_ioctl32(_IOWR('s',0x13, DWORD), "IOCTL_DEVBAPI_BAPI_CONNECT_EVENTS" );
        smbus_unregister_ioctl32(_IOWR('s',0x14, DWORD), "IOCTL_DEVBAPI_BAPI_CONNECT_MEM_ERRS" );
        smbus_unregister_ioctl32(_IOR('s', 0x32, IOCTLDATA_GEN_IO), "IOCTL_DEVBUSIO_GENERIC_PORT_IN" );
        smbus_unregister_ioctl32(_IOW('s', 0x33, IOCTLDATA_GEN_IO), "IOCTL_DEVBUSIO_GENERIC_PORT_OUT" );
        smbus_unregister_ioctl32(_IOR('s', 0x08, IOCTLDATA_SMBUS_MASTER_INFO), "IOCTL_DEVSMBUS_MASTER_INFO" );
        smbus_unregister_ioctl32(_IO('s', 0x09), "IOCTL_DEVSMBUS_RESET_MASTER" );
        smbus_unregister_ioctl32(_IOR('s', 0x40, IOCTLDATA_CORR_CPU_ERROR), "IOCTL_DEVBUSIO_GET_CPU_ERROR" );
        smbus_unregister_ioctl32(_IOR('s', 0x41,IOCTLDATA_CPU_APICID_BOOT_CPU),"IOCTL_DEVBUSIO_GET_CPU_LOCAL_APIC_ID");
        smbus_unregister_ioctl32(_IOR('s', 0x42, IOCTLDATA_CPU_INFO), "IOCTL_DEVBUSIO_GET_CPU_INFO" );
        return;
}
static void free_all(void)
{
        int i;
        if (pVirtMemorySMBI != NULL) {
                vfree(pVirtMemorySMBI);
                pVirtMemorySMBI = NULL;
                m_fSmbiExec = NULL;
        }
        if (pVirtMemoryBAPI != NULL) {
                vfree(pVirtMemoryBAPI);
                pVirtMemoryBAPI = NULL;
                m_fBapiExec = NULL;
        }
        if (pBAPIStaticPage != NULL) {
                mem_map_unreserve(virt_to_page(pBAPIStaticPage));
                free_page((ulong)pBAPIStaticPage);
                pBAPIStaticPage = NULL;
        }
        for (i = 0; i < 32; i++)
        {
                OpenDevices[i] = NULL;
        }
}
static struct file_operations smbus_fops =
{
        DRIVER_FOPS
};
int init_module(void)
{
        int ret;
        int result = 0;
        int i;
        jiffies0 = jiffies;
        if ((ret = smbus_DetermineEnvironment()) < 0) {
                printk(KERN_ERR "smbus(%d): " "init_module: unable to determine OS/HW environment (return = %d)\n", (int)(jiffies-jiffies0), ret);
                return -ENODEV;
        }
        DRIVER_PCI_PRESENT(result);
        if (result == 0) {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "init_module: ERROR: pcibios  is NOT present (%d)\n", (int)(jiffies-jiffies0), result); } while (0);
                return -ENODEV;
        }
        DetectHardware();
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "init_module: Found Hardware of Type 0x%x\n", (int)(jiffies-jiffies0), (int)Chipset); } while (0);
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "init_module: smbusPowerOff    = %d\n", (int)(jiffies-jiffies0), (int)smbusPowerOff); } while (0);
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "init_module: IsSmbusHwFound   = %d\n", (int)(jiffies-jiffies0), IsSmbusHwFound); } while (0);
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "init_module: IsSmbiHwFound    = %d\n", (int)(jiffies-jiffies0), IsSmbiHwFound); } while (0);
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "init_module: IsBapiHwFound    = %d\n", (int)(jiffies-jiffies0), IsBapiHwFound); } while (0);
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "init_module: IsBusIoHwFound   = %d\n", (int)(jiffies-jiffies0), IsBusIoHwFound); } while (0);
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "init_module: IsCpuErrHwFound  = %d\n", (int)(jiffies-jiffies0), IsCpuErrHwFound); } while (0);
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "init_module: IsCpuApicHwFound = %d\n", (int)(jiffies-jiffies0), IsCpuApicHwFound); } while (0);
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "init_module: IsCpuInfoHwFound = %d\n", (int)(jiffies-jiffies0), IsCpuInfoHwFound); } while (0);
        DRIVER_SET_OWNER;
        if((ret = register_chrdev(smbus_major, SMBUS_DEV, &smbus_fops)) < 0) {
                printk(KERN_ERR "smbus(%d): " "unable to get major %d  return = %d\n", (int)(jiffies-jiffies0), smbus_major, ret);
                free_all();
                return -EIO;
        }
        if (ret > 0) smbus_major = ret;
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "init_module: major device number = %d (0x%08x)\n", (int)(jiffies-jiffies0),smbus_major, smbus_major); } while (0);
        smbus_register_PowerOff_routine();
        DRIVER_INTER_MODULE_REGISTER(smbus_PowerOff);
        DRIVER_INTER_MODULE_REGISTER_P(smbus_PowerOff_saved);
        if ( smbusArchMode & 0x00000004 ) {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "init_module: smbus_PowerOff       function (inter_module) registered (%d)\n", (int)(jiffies-jiffies0),0); } while (0);
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "init_module: smbus_PowerOff_saved function (inter_module) registered (%d)\n", (int)(jiffies-jiffies0),0); } while (0);
        }
        if ((ret = smbus_register_ioctl32_all()) < 0) {
                printk(KERN_ERR "smbus(%d): " "init_module: smbus_register_ioctl32 failed, ret = %d\n", (int)(jiffies-jiffies0), ret);
                cleanup_module();
                return -EIO;
        }
        for (i=0; i<32; i++)
        {
                (SmBus_DAD_Buff[i]).iod_open.pMuxAddr = (DWORD64)(unsigned long)(&((SmBus_DAD_Buff[i]).muxdevadr[0]));
                OpenDevicesPersist[i] = &(SmBus_DAD_Buff[i]);
        }
        smbus_FillCpuInfoTable();
        return 0;
}
void cleanup_module(void)
{
        do { if (smbusDebug & (1 << (0))) printk(KERN_DEBUG "smbus(%d):" "cleanup_module entered (%d)\n", (int)(jiffies-jiffies0),0); } while (0);
        DRIVER_INTER_MODULE_UNREGISTER(smbus_PowerOff);
        DRIVER_INTER_MODULE_UNREGISTER(smbus_PowerOff_saved);
        if ( smbusArchMode & 0x00000004 ) {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "cleanup_module: smbus_PowerOff       function (inter_module) unregistered (%d)\n", (int)(jiffies-jiffies0),0); } while (0);
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "cleanup_module: smbus_PowerOff_saved function (inter_module) unregistered (%d)\n", (int)(jiffies-jiffies0),0); } while (0);
        }
        smbus_unregister_PowerOff_routine();
        smbus_unregister_ioctl32_all();
        free_all();
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,23)
	/* unregister_chrdev returns void now */
        unregister_chrdev(smbus_major, SMBUS_DEV);
#else
        int err;
        err = unregister_chrdev(smbus_major, SMBUS_DEV);
        if (err < 0) {
                printk(KERN_ERR "smbus(%d): " "unregister_chrdev(%i) failed! return = %d\n", (int)(jiffies-jiffies0), smbus_major, err);
        }
#endif
}
static void smbus_register_PowerOff_routine(void)
{
        pm_power_off_t tmp_POff_copa = NULL;
        pm_power_off_t tmp_POff_ipmi = NULL;
        pm_power_off_t *tmp_POff_copa_sav = NULL;
        pm_power_off_t *tmp_POff_ipmi_sav = NULL;
        DWORD tmp_smbus_poff_prio = 3;
        if (smbusPowerOff <= 0) {
                return;
        }
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: OS    PowerOff routine = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF); } while (0);
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: SMBUS PowerOff routine = 0x%016lX\n", (int)(jiffies-jiffies0), (long) smbus_PowerOff); } while (0);
        tmp_POff_copa = (pm_power_off_t) DRIVER_INTER_MODULE_GET(copa_PowerOff);
        tmp_POff_copa_sav = (pm_power_off_t *) DRIVER_INTER_MODULE_GET(copa_PowerOff_saved);
        tmp_POff_ipmi = (pm_power_off_t) DRIVER_INTER_MODULE_GET(ipmi_PowerOff);
        tmp_POff_ipmi_sav = (pm_power_off_t *) DRIVER_INTER_MODULE_GET(ipmi_PowerOff_saved);
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: tmp_POff_copa       = 0x%016lX\n", (int)(jiffies-jiffies0), (long) tmp_POff_copa); } while (0);
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: tmp_POff_copa_sav   = 0x%016lX\n", (int)(jiffies-jiffies0), (long) tmp_POff_copa_sav); } while (0);
        if (tmp_POff_copa_sav != NULL)
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: *tmp_POff_copa_sav  = 0x%016lX\n", (int)(jiffies-jiffies0), (long) *tmp_POff_copa_sav); } while (0);
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: tmp_POff_ipmi       = 0x%016lX\n", (int)(jiffies-jiffies0), (long) tmp_POff_ipmi); } while (0);
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: tmp_POff_ipmi_sav   = 0x%016lX\n", (int)(jiffies-jiffies0), (long) tmp_POff_ipmi_sav); } while (0);
        if (tmp_POff_ipmi_sav != NULL)
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: *tmp_POff_ipmi_sav  = 0x%016lX\n", (int)(jiffies-jiffies0), (long) *tmp_POff_ipmi_sav); } while (0);
        if (PM_POWER_OFF == NULL) {
                 smbus_PowerOff_saved = NULL;
                 PM_POWER_OFF = smbus_PowerOff;
                 smbus_OS_Poff_routine_changed = 1;
                 do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: SMBUS PowerOff routine inserted \n", (int)(jiffies-jiffies0)); } while (0);
                 do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: PM_POWER_OFF         = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF); } while (0);
                 do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: smbus_PowerOff_saved = 0x%016lX\n", (int)(jiffies-jiffies0), (long) smbus_PowerOff_saved); } while (0);
        } else if (PM_POWER_OFF == tmp_POff_copa) {
                if (tmp_smbus_poff_prio > 1) {
                        smbus_OS_Poff_routine_changed = 0;
                        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: COPA PowerOff routine has already been inserted -> Do nothing!\n", (int)(jiffies-jiffies0)); } while (0);
                } else {
                         smbus_PowerOff_saved = *tmp_POff_copa_sav;
                         PM_POWER_OFF = smbus_PowerOff;
                         smbus_OS_Poff_routine_changed = 1;
                         do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: COPA PowerOff routine replaced by SMBUS routine\n", (int)(jiffies-jiffies0)); } while (0);
                         do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: PM_POWER_OFF         = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF); } while (0);
                         do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: smbus_PowerOff_saved = 0x%016lX\n", (int)(jiffies-jiffies0), (long) smbus_PowerOff_saved); } while (0);
                }
        } else if (PM_POWER_OFF == tmp_POff_ipmi) {
                if (tmp_smbus_poff_prio > 2) {
                        smbus_OS_Poff_routine_changed = 0;
                        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: IPMI PowerOff routine has already been inserted -> Do nothing!\n", (int)(jiffies-jiffies0)); } while (0);
                } else {
                         smbus_PowerOff_saved = *tmp_POff_ipmi_sav;
                         PM_POWER_OFF = smbus_PowerOff;
                         smbus_OS_Poff_routine_changed = 1;
                         do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: IPMI PowerOff routine replaced by SMBUS routine\n", (int)(jiffies-jiffies0)); } while (0);
                         do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: PM_POWER_OFF         = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF); } while (0);
                         do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: smbus_PowerOff_saved = 0x%016lX\n", (int)(jiffies-jiffies0), (long) smbus_PowerOff_saved); } while (0);
                }
        } else {
                 smbus_PowerOff_saved = PM_POWER_OFF;
                 PM_POWER_OFF = smbus_PowerOff;
                 smbus_OS_Poff_routine_changed = 1;
                 do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: OS PowerOff routine replaced by SMBUS Power Off routine!\n", (int)(jiffies-jiffies0)); } while (0);
                 do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: PM_POWER_OFF         = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF); } while (0);
                 do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_register_PowerOff_routine: smbus_PowerOff_saved = 0x%016lX\n", (int)(jiffies-jiffies0), (long) smbus_PowerOff_saved); } while (0);
        }
        if (tmp_POff_copa) DRIVER_INTER_MODULE_PUT(copa_PowerOff);
        if (tmp_POff_copa_sav) DRIVER_INTER_MODULE_PUT(copa_PowerOff_saved);
        if (tmp_POff_ipmi) DRIVER_INTER_MODULE_PUT(ipmi_PowerOff);
        if (tmp_POff_ipmi_sav) DRIVER_INTER_MODULE_PUT(ipmi_PowerOff_saved);
}
static void smbus_unregister_PowerOff_routine(void)
{
        if (smbusPowerOff <= 0) {
                return;
        }
        if (smbus_OS_Poff_routine_changed && (PM_POWER_OFF == smbus_PowerOff)) {
                 PM_POWER_OFF = smbus_PowerOff_saved;
                 smbus_PowerOff_saved = NULL;
                 smbus_OS_Poff_routine_changed = 0;
                 do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_unregister_PowerOff_routine: SMBUS Power Off routine replaced by original routine !\n", (int)(jiffies-jiffies0)); } while (0);
                 do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_unregister_PowerOff_routine: PM_POWER_OFF       = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF); } while (0);
                 do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_unregister_PowerOff_routine: smbus_PowerOff_sav = 0x%016lX\n", (int)(jiffies-jiffies0), (long) smbus_PowerOff_saved); } while (0);
        }
}
void smbus_PowerOff (void)
{
        printk(KERN_INFO "smbus(%d): " "POWER OFF BY SMBUS ! (%d)\n", (int)(jiffies-jiffies0),0);
        if (smbus_PowerOff_saved != NULL) {
                (smbus_PowerOff_saved)();
        }
        if (smbus_ioctl(NULL, NULL, _IO('s', 0x54), 0) < 0) {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_PowerOff: ERROR: Power Off failed !!!\n", (int)(jiffies-jiffies0)); } while (0);
        }
}
void smbus_ReadCpuInfo_callback (void *pent)
{
        int sparse;
        int dense;
        CpuInfo *pentry = pent;
        sparse = smp_processor_id();
        dense = CPU_NUMBER_MAP(sparse);
        if (pentry->DenseCpuNr == dense)
        {
                pentry->SparseCpuNr = sparse;
                smbus_CpuId(0x00000000, &pentry->regs0);
                if (pentry->regs0.eax >= 0x00000001) {
                        smbus_CpuId(0x00000001, &pentry->regs1);
                        if (pentry->regs0.eax >= 0x00000002) {
                                smbus_CpuId(0x00000002, &pentry->regs2);
                                if (pentry->regs0.eax >= 0x00000003) {
                                        smbus_CpuId(0x00000003, &pentry->regs3);
                                        if (pentry->regs0.eax >= 0x00000004) {
                                                smbus_CpuId(0x00000004, &pentry->regs4);
                                        }
                                }
                        }
                }
                smbus_CpuId(0x80000000, &pentry->MaxExtentions);
                if (pentry->MaxExtentions.eax >= 0x80000004) {
                        smbus_CpuId(0x80000002, &pentry->BrandString1);
                        smbus_CpuId(0x80000003, &pentry->BrandString2);
                        smbus_CpuId(0x80000004, &pentry->BrandString3);
                        if (pentry->MaxExtentions.eax >= 0x80000008) {
                                smbus_CpuId(0x80000008, &pentry->NrCoresAMD);
                        }
                }
                pentry->ApicBaseMsr = smbus_ReadMsr(0x01B);
        }
        return;
}
static void smbus_do_ReadCpuInfo(CpuInfo *pentry)
{
        int sparse;
        int dense;
        PREEMPT_DISABLE;
        sparse = smp_processor_id();
        dense = CPU_NUMBER_MAP(sparse);
        if (pentry->DenseCpuNr == dense)
        {
                pentry->SparseCpuNr = sparse;
                smbus_CpuId(0x00000000, &pentry->regs0);
                if (pentry->regs0.eax >= 0x00000001) {
                        smbus_CpuId(0x00000001, &pentry->regs1);
                        if (pentry->regs0.eax >= 0x00000002) {
                                smbus_CpuId(0x00000002, &pentry->regs2);
                                if (pentry->regs0.eax >= 0x00000003) {
                                        smbus_CpuId(0x00000003, &pentry->regs3);
                                        if (pentry->regs0.eax >= 0x00000004) {
                                                smbus_CpuId(0x00000004, &pentry->regs4);
                                        }
                                }
                        }
                }
                smbus_CpuId(0x80000000, &pentry->MaxExtentions);
                if (pentry->MaxExtentions.eax >= 0x80000004) {
                        smbus_CpuId(0x80000002, &pentry->BrandString1);
                        smbus_CpuId(0x80000003, &pentry->BrandString2);
                        smbus_CpuId(0x80000004, &pentry->BrandString3);
                        if (pentry->MaxExtentions.eax >= 0x80000008) {
                                smbus_CpuId(0x80000008, &pentry->NrCoresAMD);
                        }
                }
                pentry->ApicBaseMsr = smbus_ReadMsr(0x01B);
        } else {
                smp_call_function(smbus_ReadCpuInfo_callback, (void *)pentry, 1, 1);
        }
        PREEMPT_ENABLE;
        return;
}
void smbus_ReadCpuInfo_callback_IA64 (void *pent)
{
        int sparse;
        int dense;
        CpuInfo *pentry = pent;
        sparse = smp_processor_id();
        dense = CPU_NUMBER_MAP(sparse);
        if (pentry->DenseCpuNr == dense)
        {
                pentry->SparseCpuNr = sparse;
                smbus_CpuId_IA64(&pentry->IA64Data);
        }
        return;
}
static void smbus_do_ReadCpuInfo_IA64(CpuInfo *pentry)
{
        int sparse;
        int dense;
        PREEMPT_DISABLE;
        sparse = smp_processor_id();
        dense = CPU_NUMBER_MAP(sparse);
        if (pentry->DenseCpuNr == dense)
        {
                pentry->SparseCpuNr = sparse;
                smbus_CpuId_IA64(&pentry->IA64Data);
        } else {
                smp_call_function(smbus_ReadCpuInfo_callback_IA64, (void *)pentry, 1, 1);
        }
        PREEMPT_ENABLE;
        return;
}
void smbus_ReadApicId_callback(void *pent)
{
        int sparse;
        int dense;
        CpuInfo *pentry = pent;
        sparse = smp_processor_id();
        dense = CPU_NUMBER_MAP(sparse);
        if (pentry->DenseCpuNr == dense)
        {
                pentry->ApicId = (BYTE)(readl(pentry->ApicVirtualAddress) >> 24);
        }
        return;
}
static void smbus_do_ReadApicId(CpuInfo *pentry)
{
        int sparse;
        int dense;
        PREEMPT_DISABLE;
        sparse = smp_processor_id();
        dense = CPU_NUMBER_MAP(sparse);
        if (pentry->DenseCpuNr == dense)
        {
                pentry->ApicId = (BYTE)(readl(pentry->ApicVirtualAddress) >> 24);
        } else {
                smp_call_function(smbus_ReadApicId_callback, (void *)pentry, 1, 1);
        }
        PREEMPT_ENABLE;
        return;
}
static void smbus_FillCpuInfoTable(void)
{
        int i;
        CpuInfo *pentry;
        ULONG physApicBaseAddress = 0;
        BOOL dounmap = 0;
        int sizeVendor;
        UCHAR Vendor[32];
        memset (&smbus_cpuinfotable, 0, sizeof(smbus_cpuinfotable));
        if (SMP_NUM_CPUS > 128) {
                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_FillCpuInfoTable: ERROR !!! current CPUs number exceeds the max. supported value (current = %d, max = %d)\n", (int)(jiffies-jiffies0), (int)SMP_NUM_CPUS, 128); } while (0);
                return;
        }
        for (i=0; i < SMP_NUM_CPUS; i++)
        {
                pentry = &smbus_cpuinfotable[i];
                pentry->DenseCpuNr = i;
                if (smbusArchMode & 0x40000000)
                {
                        smbus_do_ReadCpuInfo_IA64(pentry);
                        sizeVendor = sizeof(pentry->IA64Data.IA64Value.Vendor);
                        memcpy(Vendor, pentry->IA64Data.IA64Value.Vendor, sizeVendor);
                        Vendor[sizeVendor] = '\0';
                        pentry->IsIA64Architecture = 1;
                        pentry->regs1Valid = 1;
                        pentry->regs4Valid = 1;
                        if (pentry->IA64Data.IA64Value.CpuFamily == 0x20)
                        {
                                pentry->NrCores = 2;
                                pentry->NumberLogicalCpus = 4;
                                pentry->regs1.ebx = 0x40000;
                                pentry->regs1.edx = (1<<28);
                                pentry->regs4.eax = 0x04000000 | 0x4000;
                        }
                        else
                        {
                                pentry->NrCores = 1;
                                pentry->NumberLogicalCpus = 1;
                                pentry->regs1.ebx = 0x10000;
                                pentry->regs4.eax = 0x02000000 | 0x2000;
                        }
                }
                else
                {
                        smbus_do_ReadCpuInfo(pentry);
                        pentry->regs1Valid = !!(pentry->regs0.eax >= 0x00000001);
                        pentry->regs2Valid = !!(pentry->regs0.eax >= 0x00000002);
                        pentry->regs3Valid = 0;
                        pentry->regs4Valid = !!(pentry->regs0.eax >= 0x00000004);
                        pentry->BrandStringValid = !!(pentry->MaxExtentions.eax >= 0x80000004);
                        pentry->NrCoresAMDValid = !!(pentry->MaxExtentions.eax >= 0x80000008);
                        if (pentry->regs0.ebx == 0x756E6547) {
                                pentry->Vendor = 0x01;
                                if (pentry->regs4Valid) {
                                        pentry->NrCores = (BYTE) (1 + (((pentry->regs4.eax) >> 26) & 0x3F));
                                }
                        } else {
                                pentry->Vendor = 0x02;
                                if (pentry->NrCoresAMDValid) {
                                        pentry->NrCores = (BYTE) (1 + (((pentry->NrCoresAMD.ecx) >> 0) & 0xFF));
                                }
                        }
                        pentry->MachineCheckArchitectureSupported = !!(pentry->regs1.edx & (1<<14));
                        pentry->LocalApicSupported = !!(pentry->regs1.edx & (1<<9));
                        pentry->NumberLogicalCpus = (BYTE)((pentry->regs1.ebx) >> 16);
                        pentry->LocalApicIdInitial = (BYTE)((pentry->regs1.ebx) >> 24);
                        pentry->PrimaryLogicalCpu = !!(pentry->NumberLogicalCpus == 0 ||
                                                                                                                         pentry->NumberLogicalCpus == 1 ||
                                                                                                                         !(pentry->LocalApicIdInitial & 0x01));
                        pentry->ApicBaseAddress = ((((pentry->ApicBaseMsr))) & ((DWORD64)0xffffff)<<12);
                        pentry->BootstrapCpu = !!((BYTE)((((pentry->ApicBaseMsr)) >> 8) & 1));
                        pentry->ApicGlobalEnable = !!((BYTE)((((pentry->ApicBaseMsr)) >> 11) & 1));
                        pentry->ApicIdValid = 0;
                        if ((smbusArchMode & 0x10000000) &&
                                (((pentry->ApicBaseAddress + 0x00000020) >> 32) != 0))
                        {
                                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "CPU%02d: ERROR !!! APIC base address to high ! Cannot map it !\n", (int)(jiffies-jiffies0), pentry->DenseCpuNr); } while (0);
                        } else {
                                physApicBaseAddress = (ULONG)(pentry->ApicBaseAddress + 0x00000020);
                                if ((ULONG)(physApicBaseAddress + 0x10) < (ULONG)virt_to_phys(high_memory) ) {
                                        pentry->ApicVirtualAddress = phys_to_virt(physApicBaseAddress);
                                        dounmap = 0;
                                } else {
                                        pentry->ApicVirtualAddress = ioremap_nocache(physApicBaseAddress, 0x10);
                                        dounmap = 1;
                                }
                                if (pentry->ApicVirtualAddress == NULL)
                                {
                                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "CPU%02d: ERROR !!! No Virtual Pointer to local APIC Id\n", (int)(jiffies-jiffies0), pentry->DenseCpuNr); } while (0);
                                } else {
                                        smbus_do_ReadApicId(pentry);
                                        pentry->ApicIdValid = 1;
                                        if (dounmap) iounmap((void *)pentry->ApicVirtualAddress);
                                }
                        }
                }
        }
        for (i=0; i < SMP_NUM_CPUS; i++)
        {
                pentry = &smbus_cpuinfotable[i];
                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "CPU%02d: sparse CPU# = %02d, dense CPU# = %02d\n", (int)(jiffies-jiffies0), i, pentry->SparseCpuNr, pentry->DenseCpuNr); } while (0);
                if (smbusArchMode & 0x40000000)
                {
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       IsIA64Architecture     = %d\n", (int)(jiffies-jiffies0), pentry->IsIA64Architecture); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       Vendor                 = %s\n", (int)(jiffies-jiffies0), Vendor); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       IA64Data.IA64regs.rg0  = 0x%016LX\n", (int)(jiffies-jiffies0), pentry->IA64Data.IA64regs.rg0); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       IA64Data.IA64regs.rg1  = 0x%016LX\n", (int)(jiffies-jiffies0), pentry->IA64Data.IA64regs.rg1); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       IA64Data.IA64regs.rg2  = 0x%016LX\n", (int)(jiffies-jiffies0), pentry->IA64Data.IA64regs.rg2); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       IA64Data.IA64regs.rg3  = 0x%016LX\n", (int)(jiffies-jiffies0), pentry->IA64Data.IA64regs.rg3); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       IA64Data.IA64regs.rg4  = 0x%016LX\n", (int)(jiffies-jiffies0), pentry->IA64Data.IA64regs.rg4); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       regs1Valid             = %d\n", (int)(jiffies-jiffies0), pentry->regs1Valid); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       regs4Valid             = %d\n", (int)(jiffies-jiffies0), pentry->regs4Valid); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       PrimaryLogicalCpu      = %d\n", (int)(jiffies-jiffies0), pentry->PrimaryLogicalCpu); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       NrCores                = %d\n", (int)(jiffies-jiffies0), pentry->NrCores); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       NumberLogicalCpus      = %d\n", (int)(jiffies-jiffies0), pentry->NumberLogicalCpus); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       BootstrapCpu           = %d\n", (int)(jiffies-jiffies0), pentry->BootstrapCpu); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       Regs 1 (cpuid) EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs1.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs1.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs1.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs1.edx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       Regs 4 (cpuid) EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs4.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs4.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs4.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs4.edx); } while (0);
                }
                else
                {
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       regs1Valid             = %d\n", (int)(jiffies-jiffies0), pentry->regs1Valid); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       regs2Valid             = %d\n", (int)(jiffies-jiffies0), pentry->regs2Valid); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       regs3Valid             = %d\n", (int)(jiffies-jiffies0), pentry->regs3Valid); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       regs4Valid             = %d\n", (int)(jiffies-jiffies0), pentry->regs4Valid); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       BrandStringValid       = %d\n", (int)(jiffies-jiffies0), pentry->BrandStringValid); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       NrCoresAMDValid        = %d\n", (int)(jiffies-jiffies0), pentry->NrCoresAMDValid); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       CheckArchSupported     = %d\n", (int)(jiffies-jiffies0), pentry->MachineCheckArchitectureSupported); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       LocalApicSupported     = %d\n", (int)(jiffies-jiffies0), pentry->LocalApicSupported); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       PrimaryLogicalCpu      = %d\n", (int)(jiffies-jiffies0), pentry->PrimaryLogicalCpu); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       LocalApicIdInitial     = 0x%02X\n", (int)(jiffies-jiffies0), pentry->LocalApicIdInitial); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       Vendor                 = %d\n", (int)(jiffies-jiffies0), pentry->Vendor); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       NrCores                = %d\n", (int)(jiffies-jiffies0), pentry->NrCores); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       NumberLogicalCpus      = %d\n", (int)(jiffies-jiffies0), pentry->NumberLogicalCpus); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       Regs 0 (cpuid) EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs0.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs0.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs0.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs0.edx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       Regs 1 (cpuid) EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs1.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs1.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs1.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs1.edx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       Regs 2 (cpuid) EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs2.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs2.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs2.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs2.edx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       Regs 3 (cpuid) EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs3.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs3.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs3.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs3.edx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       Regs 4 (cpuid) EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs4.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs4.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs4.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->regs4.edx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       NrCoresAMD     EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->NrCoresAMD.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->NrCoresAMD.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->NrCoresAMD.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->NrCoresAMD.edx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       MaxExtentions  EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->MaxExtentions.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->MaxExtentions.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->MaxExtentions.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->MaxExtentions.edx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       BrandString1   EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString1.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString1.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString1.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString1.edx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       BrandString2   EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString2.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString2.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString2.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString2.edx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       BrandString3   EAX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString3.eax); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EBX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString3.ebx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      ECX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString3.ecx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "                      EDX     = 0x%08X\n", (int)(jiffies-jiffies0), pentry->BrandString3.edx); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       ApicBaseMsr register   = 0x%0lX\n", (int)(jiffies-jiffies0), (unsigned long)pentry->ApicBaseMsr); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       ApicBaseAddress        = 0x%0lX\n", (int)(jiffies-jiffies0), (unsigned long)pentry->ApicBaseAddress); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       MappedVirtualAddress   = 0x%p\n", (int)(jiffies-jiffies0), pentry->ApicVirtualAddress); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       BootstrapCpu           = %d\n", (int)(jiffies-jiffies0), pentry->BootstrapCpu); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       ApicGlobalEnable       = %d\n", (int)(jiffies-jiffies0), pentry->ApicGlobalEnable); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       ApicId is valid        = %d\n", (int)(jiffies-jiffies0), pentry->ApicIdValid); } while (0);
                        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "       ApicId from BaseAddr.  = 0x%02X\n", (int)(jiffies-jiffies0), pentry->ApicId); } while (0);
                }
        }
        return;
}
void smbus_GetCpuError_callback(void *pCpuErrInfo)
{
        int sparse;
        int dense;
        sparse = smp_processor_id();
        dense = CPU_NUMBER_MAP(sparse);
        if (((CpuErrorInfo *)pCpuErrInfo)->DenseCpuNr == dense)
        {
                smbus_ReadCpuErrorInfo((CpuErrorInfo *)pCpuErrInfo);
        }
        return;
}
static void smbus_do_GetCpuError(CpuErrorInfo *pCpuErrInfo)
{
        int sparse;
        int dense;
        PREEMPT_DISABLE;
        sparse = smp_processor_id();
        dense = CPU_NUMBER_MAP(sparse);
        if (pCpuErrInfo->DenseCpuNr == dense)
        {
                smbus_ReadCpuErrorInfo((CpuErrorInfo *)pCpuErrInfo);
        } else {
                smp_call_function(smbus_GetCpuError_callback, (void *)pCpuErrInfo, 1, 1);
        }
        PREEMPT_ENABLE;
        return;
}
static void smbus_ReadCpuErrorInfo(CpuErrorInfo *pCpuErrInfo)
{
        INT i;
        IOCTLDATA_CORR_CPU_ERROR *pError = (IOCTLDATA_CORR_CPU_ERROR *)(pCpuErrInfo->pCpuError);
        DWORD64 IA32_MCi_STATUS;
        DWORD64 IA32_MCi_ADDR;
        WORD MCAErrorCode;
        pCpuErrInfo->McgCap = smbus_ReadMsr (0x179);
        pCpuErrInfo->McgStatus = smbus_ReadMsr (0x17A);
        pCpuErrInfo->NrErrorBanks = ((BYTE)(((pCpuErrInfo->McgCap) >> 0) & 0xff));
        pCpuErrInfo->ErrorAvailable = 0;
        for (i=0; i < pCpuErrInfo->NrErrorBanks; i++)
        {
                pCpuErrInfo->MsrAddrMCiStatus = (0x401+((i)*4));
                pCpuErrInfo->MsrAddrMCiAddr = (0x402+((i)*4));
                IA32_MCi_STATUS = smbus_ReadMsr ((0x401+((i)*4)));
                if (((BYTE)(((IA32_MCi_STATUS) >> 63) & 1)))
                {
                        pCpuErrInfo->ErrorAvailable = 1;
                        pError->IA32MCiStatus = IA32_MCi_STATUS;
                        pError->Bank = i;
                        pError->ErrorCode = ((WORD)(((IA32_MCi_STATUS) >> 0) & 0xffff));
                        pError->Overflow = ((BYTE)(((IA32_MCi_STATUS) >> 62) & 1));
                        pError->Uncorrectable = ((BYTE)(((IA32_MCi_STATUS) >> 61) & 1));
                        MCAErrorCode = pError->ErrorCode;
                        if (((BYTE)(((IA32_MCi_STATUS) >> 58) & 1)))
                        {
                                IA32_MCi_ADDR = smbus_ReadMsr ((0x402+((i)*4)));
                                pError->AddressLow = (DWORD) (IA32_MCi_ADDR & 0xffffffff);
                                pError->AddressHigh = (DWORD) (IA32_MCi_ADDR >> 32);
                        } else {
                                pError->AddressLow = pError->AddressHigh = 0xffffffff;
                        }
                        pError->CacheLevel = (BYTE)((((MCAErrorCode) >> 0) & 0x3));
                        pError->RequestType = (BYTE)((((MCAErrorCode) >> 4) & 0xf));
                        pError->TransactionType = (BYTE)((((MCAErrorCode) >> 2) & 0x3));
                        pError->ParticipationLevel = (BYTE)((((MCAErrorCode) >> 9) & 0x3));
                        pError->Timeout = (BYTE)((((MCAErrorCode) >> 8) & 0x1));
                        pError->MemIo = (BYTE)((((MCAErrorCode) >> 2) & 0x3));
                        if ((((MCAErrorCode) & 0xff00) == 0x0100))
                        {
                                pError->ErrorType = CPUERR_TYPE_CACHE_ERROR;
                                smbus_WriteMsr ((0x401+((i)*4)), 0);
                        }
                        else if ((((MCAErrorCode) & 0xf800) == 0x0800))
                        {
                                pError->ErrorType = CPUERR_TYPE_BUS_ERROR;
                                smbus_WriteMsr ((0x401+((i)*4)), 0);
                        }
                        else if ((((MCAErrorCode) & 0xfff0) == 0x0010))
                        {
                                pError->ErrorType = CPUERR_TYPE_TLB_ERROR;
                                smbus_WriteMsr ((0x401+((i)*4)), 0);
                        }
                        else
                        {
                                pError->ErrorType = CPUERR_TYPE_UNCLASSIFIED;
                                smbus_WriteMsr ((0x401+((i)*4)), 0);
                        }
                        break;
                }
        }
        return;
}
static DWORD64 smbus_ReadMsr (DWORD address)
{
        volatile DWORD reg_eax;
        volatile DWORD reg_edx;
        ASMX86("rdmsr"
                : "=a" (reg_eax), "=d" (reg_edx)
                : "c" (address));
        return (((DWORD64)reg_edx << 32) | (DWORD64)reg_eax);
}
static void smbus_WriteMsr (DWORD address, DWORD64 data)
{
        volatile DWORD DataLow;
        volatile DWORD DataHigh;
        DataLow = (DWORD) (data & (DWORD64)0x0FFFFFFFF);
        DataHigh = (DWORD) (data >> 32);
        ASMX86("wrmsr"
                :
                : "c" (address), "a" (DataLow), "d" (DataHigh));
}
static void smbus_CpuId (DWORD address, CpuIdRegs *regs)
{
        ASMX86("cpuid"
                : "=a" (regs->eax), "=b" (regs->ebx), "=c" (regs->ecx), "=d" (regs->edx)
                : "a" (address));
}
static void smbus_CpuId_IA64 (CpuIdRegsIA64 *regs)
{
        DWORD index;
        DWORD64 result;
        result = 0;
        index = 0;
        ASMIA64("mov %0=cpuid[%r1]" : "=r"(result) : "rO"(index));
        regs->IA64regs.rg0 = result;
        index = 1;
        ASMIA64("mov %0=cpuid[%r1]" : "=r"(result) : "rO"(index));
        regs->IA64regs.rg1 = result;
        index = 2;
        ASMIA64("mov %0=cpuid[%r1]" : "=r"(result) : "rO"(index));
        regs->IA64regs.rg2 = result;
        index = 3;
        ASMIA64("mov %0=cpuid[%r1]" : "=r"(result) : "rO"(index));
        regs->IA64regs.rg3 = result;
        index = 4;
        ASMIA64("mov %0=cpuid[%r1]" : "=r"(result) : "rO"(index));
        regs->IA64regs.rg4 = result;
}
#ident "$Header$"
#ident "$Header$"
#ident "$Header: $"
#ident "$Header: snismdrv.h 1.2 99/12/22 $"
#ident "$Header$"
static INT smbus_SwitchMux(DWORD DeviceHandle, PBYTE pDeviceAddress);
static BOOL smbus_ClearStatus(void);
static BOOL smbus_WaitHostBusy(void);
static BOOL smbus_WaitCmdDone(void);
static void smbus_ReleaseBus(void);
BOOL CtrlReset = 0;
DWORD smbus_ReadData(BYTE DeviceAddress, BYTE StartOffset, PBYTE pReturnBuffer, DWORD BytesToRead)
{
    DWORD ReturnDataSize = 0;
    BYTE Data = 0;
    do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_ReadData: read %d SM bus data bytes from %02X:%02X\n", (int)(jiffies-jiffies0), BytesToRead, DeviceAddress, StartOffset); } while (0);
    if (Chipset == CS_UNKNOWN || 0 == BytesToRead || NULL == pReturnBuffer)
        return 0;
    if (smbus_ReadByte (DeviceAddress, StartOffset, &Data, 0))
    {
        PBYTE pData = (PBYTE)pReturnBuffer;
        DWORD Offset = StartOffset+1;
        *pData++ = Data;
        ReturnDataSize = 1;
        BytesToRead--;
        while (BytesToRead)
        {
            if (!(Offset < 256))
            {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "## FATAL ERROR: smbus_ReadData: Offset exceeds 255 while reading data!\n", (int)(jiffies-jiffies0)); } while (0);
                break;
            }
            if (!smbus_ReadByte (DeviceAddress, (BYTE)Offset, &Data, 1))
            {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ReadData: ERROR while reading data bytes, abort loop\n", (int)(jiffies-jiffies0)); } while (0);
                break;
            }
            *pData++ = Data;
            Offset++;
            ReturnDataSize++;
            BytesToRead--;
        }
    }
    do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_ReadData: %d bytes read from SM bus\n", (int)(jiffies-jiffies0), ReturnDataSize); } while (0);
    return ReturnDataSize;
}
DWORD smbus_WriteData(BYTE DeviceAddress, BYTE StartOffset, PBYTE pWriteData, DWORD BytesToWrite)
{
    DWORD WriteDataSize = 0;
    DWORD Offset = StartOffset;
    do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteData: write %d SM bus data bytes to %02X:%02X...\n", (int)(jiffies-jiffies0), BytesToWrite, DeviceAddress, StartOffset); } while (0);
    if (Chipset == CS_UNKNOWN || 0 == BytesToWrite || NULL == pWriteData)
        return WriteDataSize;
    while (BytesToWrite)
    {
        if (!(Offset < 256))
        {
            do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "## FATAL ERROR: smbus_WriteData: Offset exceeds 255 while writing data!\n", (int)(jiffies-jiffies0)); } while (0);
            break;
        }
        if (smbus_WriteByte (DeviceAddress, (BYTE)Offset, *pWriteData, 0))
        {
            WriteDataSize++;
            BytesToWrite--;
            Offset++;
            pWriteData++;
        }
        else
        {
            do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteData: ERROR while writing data bytes, abort loop\n", (int)(jiffies-jiffies0)); } while (0);
            break;
        }
    }
    if (0 == BytesToWrite)
        do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteData: %d bytes written to SM bus\n", (int)(jiffies-jiffies0), WriteDataSize); } while (0);
    else
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "## ERROR: smbus_WriteData: Failed to write data byte 0x%02X:0x%02X!\n", (int)(jiffies-jiffies0), DeviceAddress, Offset); } while (0);
    return WriteDataSize;
}
DWORD smbus_ReadOneByte(BYTE DeviceAddress, PBYTE pReturnByte)
{
    DWORD ReturnDataSize = 0;
    BYTE Data = 0;
    do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_ReadOneByte: read SM bus data byte from %02X\n", (int)(jiffies-jiffies0), DeviceAddress); } while (0);
    if (Chipset == CS_UNKNOWN || NULL == pReturnByte)
        return 0;
    if(smbus_ReadByte(DeviceAddress,0,&Data,1))
    {
        *pReturnByte = Data;
        ReturnDataSize++;
    }
    do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_ReadOneByte: %d byte read from SM bus\n", (int)(jiffies-jiffies0), ReturnDataSize); } while (0);
    return ReturnDataSize;
}
DWORD smbus_WriteOneByte(BYTE DeviceAddress, BYTE WriteData)
{
    DWORD WriteDataSize = 0;
    do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteOneByte: write SM bus data bytes to %02X\n", (int)(jiffies-jiffies0),DeviceAddress); } while (0);
    if (Chipset == CS_UNKNOWN)
        return 0;
    if (smbus_WriteByte (DeviceAddress, 0, WriteData, 1))
    {
        WriteDataSize++;
    }
    do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteOneByte: %d byte written to SM bus\n", (int)(jiffies-jiffies0), WriteDataSize); } while (0);
    return WriteDataSize;
}
INT smbus_OpenDevice(PDWORD pDeviceHandle)
{
    static spinlock_t smbus_handle_lock = SPIN_LOCK_UNLOCKED;
    DWORD Handle;
    INT Status = 0;
    BOOL Found = 0;
    if (!pDeviceHandle) return 1;
    *pDeviceHandle = (DWORD)-1;
    spin_lock(&smbus_handle_lock);
    do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_OpenDevice: create new entry\n", (int)(jiffies-jiffies0)); } while (0);
    for (Handle = 0; !Found && Handle < 32; Handle++)
    {
        if (OpenDevices[Handle] == NULL)
        {
            OpenDevices[Handle] = OpenDevicesPersist[Handle];
            *pDeviceHandle = Handle;
            Found = 1;
            do { if (smbusDebug & (1 << (4))) printk(KERN_DEBUG "smbus(%d):" "smbus_OpenDevice: new handle %04X assigned\n", (int)(jiffies-jiffies0), *pDeviceHandle); } while (0);
        }
    }
    if (Handle >= 32)
    {
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_OpenDevice: ## ERROR! OpenDevices table overflow!\n", (int)(jiffies-jiffies0)); } while (0);
        Status = 3;
    }
    spin_unlock(&smbus_handle_lock);
    return Status;
}
INT smbus_CloseDevice(DWORD DeviceHandle)
{
    do { if (smbusDebug & (1 << (4))) printk(KERN_DEBUG "smbus(%d):" "smbus_CloseDevice: close device handle %d\n", (int)(jiffies-jiffies0), DeviceHandle); } while (0);
    if (DeviceHandle >= 32)
    {
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_CloseDevice: ## ERROR! illegal device handle (%d)!\n", (int)(jiffies-jiffies0), DeviceHandle); } while (0);
        return 2;
    }
    else if (!OpenDevices[DeviceHandle])
    {
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_CloseDevice: ## ERROR! no device opened with handle %d!\n", (int)(jiffies-jiffies0), DeviceHandle); } while (0);
        return 2;
    }
    else
    {
        OpenDevices[DeviceHandle] = NULL;
        return 0;
    }
}
INT smbus_ReadDevice(DWORD DeviceHandle, BYTE Offset, DWORD BytesToRead, PBYTE pReturnBuffer, PDWORD pBytesRead)
{
    INT Status = 0;
    BYTE DeviceAddress;
    *pBytesRead = 0;
    Status = smbus_SwitchMux (DeviceHandle, &DeviceAddress);
    if (0 == Status)
    {
        *pBytesRead = smbus_ReadData (DeviceAddress, Offset, pReturnBuffer, BytesToRead);
        if (0 == *pBytesRead)
            Status = 1;
    }
    return Status;
}
INT smbus_WriteDevice (DWORD DeviceHandle, BYTE Offset, DWORD BytesToWrite, PBYTE pWriteBuffer)
{
    INT Status = 0;
    BYTE DeviceAddress;
    Status = smbus_SwitchMux (DeviceHandle, &DeviceAddress);
    if (0 == Status)
    {
        DWORD BytesWritten = smbus_WriteData (DeviceAddress, Offset, pWriteBuffer, BytesToWrite);
        if (BytesToWrite != BytesWritten)
            Status = 1;
    }
    return Status;
}
BOOL smbus_ReadByte(BYTE DeviceAddress, BYTE Offset, PBYTE pData, BOOL NotUseOffset)
{
    BYTE ControlCmd;
    BOOL Success = 0;
    DWORD RetryCnt;
    if (!ulSMBusBaseAddress || !pData) return 0;
    ControlCmd = NotUseOffset ? ((BYTE)(1<<2)) : ((BYTE)(2<<2));
    do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_ReadByte: read data byte from 0x%02X:0x%02X%s\n", (int)(jiffies-jiffies0), DeviceAddress, Offset, NotUseOffset ? " - without offset" : ""); } while (0);
    for (RetryCnt=0; !Success && RetryCnt < 3; RetryCnt++)
    {
        if (!smbus_WaitHostBusy())
        {
           do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "## ERROR: smbus_ReadByte: WaitHostBusy() failed!\n", (int)(jiffies-jiffies0)); } while (0);
        }
        else if (!smbus_ClearStatus())
        {
           do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "## ERROR: smbus_ReadByte: ClearStatus() failed!\n", (int)(jiffies-jiffies0)); } while (0);
        }
        else
        {
           do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ReadByte: reading data byte...\n", (int)(jiffies-jiffies0)); } while (0);
           outb_p(((DeviceAddress | ((BYTE)(1<<0)))), (int)(ulSMBusBaseAddress + (((BYTE)0x04))));
           if (!NotUseOffset)
               outb_p((Offset), (int)(ulSMBusBaseAddress + (((BYTE)0x03))));
           outb_p((ControlCmd | ((BYTE)(1<<6))), (int)(ulSMBusBaseAddress + (((BYTE)0x02))));
           Success = smbus_WaitCmdDone();
           if (Success)
           {
               *pData = inb_p((int)(ulSMBusBaseAddress + (((BYTE)0x05))));
               do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_ReadByte: data byte successfully read: 0x%02X!!\n", (int)(jiffies-jiffies0), *pData); } while (0);
           }
           else
           {
           do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "## WARNING: smbus_ReadByte: WaitCmdDone() failed!\n", (int)(jiffies-jiffies0)); } while (0);
               NotUseOffset = 0;
               if(0 != Offset)
                        ControlCmd = ((BYTE)(2<<2));
               do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "## RETRY\n", (int)(jiffies-jiffies0)); } while (0);
           }
        }
    smbus_ReleaseBus();
    }
    return Success;
}
BOOL smbus_WriteByte(BYTE DeviceAddress, BYTE Offset, BYTE Data, BOOL NotUseOffset)
{
    BYTE ControlCmd;
    BOOL Success = 0;
    DWORD RetryCnt;
    if (!ulSMBusBaseAddress) return 0;
    do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteByte: write data byte 0x%02X to 0x%02X:0x%02X%s\n", (int)(jiffies-jiffies0), Data, DeviceAddress, Offset, NotUseOffset ? " - without offset" : ""); } while (0);
    ControlCmd = NotUseOffset ? ((BYTE)(1<<2)) : ((BYTE)(2<<2));
    for (RetryCnt = 0; !Success && RetryCnt < 3; RetryCnt++)
    {
        if (RetryCnt)
            do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "## WARNING: smbus_WriteByte: RETRY %d!!!\n", (int)(jiffies-jiffies0),RetryCnt); } while (0);
        if (!smbus_WaitHostBusy())
        {
            do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "## ERROR: smbus_WriteByte: WaitHostBusy() failed!\n", (int)(jiffies-jiffies0)); } while (0);
        }
        else if (!smbus_ClearStatus())
        {
            do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "## ERROR: smbus_WriteByte: ClearStatus() failed!\n", (int)(jiffies-jiffies0)); } while (0);
        }
        else
        {
            do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteByte: writing data byte...\n", (int)(jiffies-jiffies0)); } while (0);
            outb_p(((DeviceAddress | ((BYTE)(0<<0)))), (int)(ulSMBusBaseAddress + (((BYTE)0x04))));
            if (!NotUseOffset)
            {
                do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteByte: Set Offset %02x\n", (int)(jiffies-jiffies0),Offset); } while (0);
                outb_p((Offset), (int)(ulSMBusBaseAddress + (((BYTE)0x03))));
            }
            else
            {
                do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteByte: Set (data) %02x\n", (int)(jiffies-jiffies0),Data); } while (0);
                outb_p((Data), (int)(ulSMBusBaseAddress + (((BYTE)0x03))));
            }
            do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteByte: Set Data   %02x\n", (int)(jiffies-jiffies0),Data); } while (0);
            outb_p((Data), (int)(ulSMBusBaseAddress + (((BYTE)0x05))));
            do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteByte: Set Cmd    %02x\n", (int)(jiffies-jiffies0), ControlCmd | ((BYTE)(1<<6))); } while (0);
            outb_p((ControlCmd | ((BYTE)(1<<6))), (int)(ulSMBusBaseAddress + (((BYTE)0x02))));
            do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteByte: START sleep\n", (int)(jiffies-jiffies0)); } while (0);
            set_current_state(TASK_UNINTERRUPTIBLE);
            schedule_timeout((10*HZ)/1000);
            do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteByte: STOP  sleep\n", (int)(jiffies-jiffies0)); } while (0);
            Success = smbus_WaitCmdDone();
            if (Success) do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_WriteByte: Data byte successfully written\n", (int)(jiffies-jiffies0)); } while (0);
            smbus_ReleaseBus();
        }
    }
    if(!Success)
    {
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "## ERROR: smbus_WriteByte: failed after retries!\n", (int)(jiffies-jiffies0)); } while (0);
    }
    return Success;
}
INT smbus_SwitchMux(DWORD DeviceHandle, PBYTE pDeviceAddress)
{
    INT Status = 0;
    BOOL Abort = 0;
    DWORD i;
    P_IOCTLDATA_SMBUS_OPEN_DEVICE pAddr;
    if (DeviceHandle >= 32)
    {
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_SwitchMux: ## ERROR! Illegal device handle (exceeds MAX_OPEN_DEVICES)!\n", (int)(jiffies-jiffies0)); } while (0);
        Status = 2;
    }
    else if ((pAddr = (P_IOCTLDATA_SMBUS_OPEN_DEVICE)OpenDevices[DeviceHandle]) == NULL)
    {
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_SwitchMux: ## ERROR! Illegal device handle (device not opened)!\n", (int)(jiffies-jiffies0)); } while (0);
        Status = 2;
    }
    else
    {
        *pDeviceAddress = pAddr->DeviceAddress;
        do { if (smbusDebug & (1 << (4))) printk(KERN_DEBUG "smbus(%d):" "smbus_SwitchMux: found DeviceAddress = 0x%02X\n", (int)(jiffies-jiffies0), *pDeviceAddress); } while (0);
        for (i = 0; !Abort && (i < 32) && (i < pAddr->MuxesToProcess); i++)
        {
            P_SMBUS_MUX_ADDR pMuxAddr = ((P_SMBUS_MUX_ADDR)(unsigned long)pAddr->pMuxAddr) + i;
            do { if (smbusDebug & (1 << (4))) printk(KERN_DEBUG "smbus(%d):" "                    MUX detected: Addr=0x%02X, Prot=%d, AndMask=0x%02X, OrMask=0x%02X\n", (int)(jiffies-jiffies0), pMuxAddr->Address, pMuxAddr->Protocol, pMuxAddr->AndMask, pMuxAddr->OrMask); } while (0);
            switch (pMuxAddr->Protocol)
            {
            case 0:
                {
                    BYTE MuxByte;
                    do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "                    MUX protocol is \"WriteByte\"\n", (int)(jiffies-jiffies0)); } while (0);
                    if (!smbus_ReadByte (pMuxAddr->Address, 0, &MuxByte, 1))
                        Abort = 1;
                    else
                    {
                        MuxByte = (MuxByte & pMuxAddr->AndMask) | pMuxAddr->OrMask;
                        if (!smbus_WriteByte (pMuxAddr->Address, 0, MuxByte, 1))
                            Abort = 1;
                    }
                    do { if (smbusDebug & (1 << (4))) printk(KERN_DEBUG "smbus(%d):" "smbus_SwitchMux: MUX at level %d (addr 0x%02X) switched\n", (int)(jiffies-jiffies0), i+1, pMuxAddr->Address); } while (0);
                }
                break;
            default:
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_SwitchMux: ## FATAL ERROR: Unsupported MUX protocol (%d)\n", (int)(jiffies-jiffies0), pMuxAddr->Protocol); } while (0);
                Abort = 1;
                break;
            }
        }
    }
    if (Abort)
        Status = 1;
    return Status;
}
BOOL smbus_ClearStatus(void)
{
    BYTE Status = inb_p((int)(ulSMBusBaseAddress + (((BYTE)0x00)))) & ~((BYTE)(1<<6));
    DWORD RetryCnt, WaitCnt;
    do { if (smbusDebug & (1 << (3))) printk(KERN_DEBUG "smbus(%d):" "smbus_ClearStatus: Status = 0x%02X\n", (int)(jiffies-jiffies0), Status); } while (0);
    Status &= ((((BYTE)(1<<2)) | ((BYTE)(1<<3)) | ((BYTE)(1<<4))) | ((BYTE)(1<<0)) | ((BYTE)(1<<1)));
    for (RetryCnt = 0; Status && (RetryCnt < 3); RetryCnt++)
    {
        if (RetryCnt)
            do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ClearStatus: ## WARNING: RETRY!!\n", (int)(jiffies-jiffies0)); } while (0);
        for (WaitCnt = 0; Status && WaitCnt < 100; WaitCnt++)
        {
            do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ClearStatus: Status not zero, reset it...\n", (int)(jiffies-jiffies0)); } while (0);
            outb_p(((((((BYTE)(1<<2)) | ((BYTE)(1<<3)) | ((BYTE)(1<<4))) | ((BYTE)(1<<0)) | ((BYTE)(1<<1))))), (int)(ulSMBusBaseAddress + (((BYTE)0x00))));
            udelay (10);
            Status = inb_p((int)(ulSMBusBaseAddress + (((BYTE)0x00))));
            do { if (smbusDebug & (1 << (3))) printk(KERN_DEBUG "smbus(%d):" "smbus_ClearStatus: Status after reset = 0x%02X\n", (int)(jiffies-jiffies0), Status); } while (0);
            Status &= ((((BYTE)(1<<2)) | ((BYTE)(1<<3)) | ((BYTE)(1<<4))) | ((BYTE)(1<<0)) | ((BYTE)(1<<1)));
            if (Status & ((BYTE)(1<<0)))
            {
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_ClearStatus: ## WARNING: BUSY while clearing status - send KILL command\n", (int)(jiffies-jiffies0)); } while (0);
                outb_p((((BYTE)(1<<1))), (int)(ulSMBusBaseAddress + (((BYTE)0x02))));
                set_current_state(TASK_UNINTERRUPTIBLE);
                schedule_timeout((100*HZ)/1000);
                outb_p((0), (int)(ulSMBusBaseAddress + (((BYTE)0x02))));
                break;
            }
            if (Status)
            {
                set_current_state(TASK_UNINTERRUPTIBLE);
                schedule_timeout((1*HZ)/1000);
            }
        }
    }
    return (Status == 0);
}
BOOL smbus_WaitHostBusy(void)
{
    BYTE Status;
    DWORD i;
    BYTE StatusMask = (Chipset == CS_INTEL_ICH) ? (((BYTE)(1<<6)) | ((BYTE)(1<<0)))
                                                 : ((BYTE)(1<<0));
    for (i = 0; i < 35; i++)
    {
        Status = inb_p((int)(ulSMBusBaseAddress + (((BYTE)0x00))));
        if (Status & StatusMask)
        {
            set_current_state(TASK_UNINTERRUPTIBLE);
            schedule_timeout((1*HZ)/1000);
        }
        else
        {
            return 1;
        }
    }
    do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_WaitHostBusy: ## ERROR: Timeout while waiting host busy, status=0x%02X!\n", (int)(jiffies-jiffies0), Status); } while (0);
    return 0;
}
BOOL smbus_WaitCmdDone(void)
{
    BOOL Done = 0;
    BOOL Success = 0;
    BYTE Status = 0;
    DWORD i;
    int k;
    do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_WaitCmdDone: waiting until command done...\n", (int)(jiffies-jiffies0)); } while (0);
    for (i = 0; !Done && i < ((1000/50)*35); i++)
    {
        do { if (smbusDebug & (1 << (3))) printk(KERN_DEBUG "smbus(%d):" "CSmbus::WaitCmdDone: sleep %d usec.\n", (int)(jiffies-jiffies0), 50); } while (0);
        udelay (50);
        Status = inb_p((int)(ulSMBusBaseAddress + (((BYTE)0x00))));
        do { if (smbusDebug & (1 << (3))) printk(KERN_DEBUG "smbus(%d):" "smbus_WaitCmdDone: Status = 0x%02X, retry count = %d\n", (int)(jiffies-jiffies0), Status, i); } while (0);
        if (Status & (((BYTE)(1<<1)) | ((BYTE)(1<<2)) | ((BYTE)(1<<3)) | ((BYTE)(1<<4))))
        {
            Done = 1;
            if (!(Status & (((BYTE)(1<<2)) | ((BYTE)(1<<3)) | ((BYTE)(1<<4)))))
                Success = 1;
            else
            {
                LPSTR pErrMsg;
                if (Status & ((BYTE)(1<<2)))
                    pErrMsg = "device error";
                else if (Status & ((BYTE)(1<<3)))
                    pErrMsg = "bus error";
                else if (Status & ((BYTE)(1<<4)))
                    pErrMsg = "kill";
                else
                {
                    pErrMsg = "## Unknown error ##";
                }
                do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_WaitCmdDone: SM BUS ERROR <<%s>>, status=0x%02X!\n", (int)(jiffies-jiffies0), pErrMsg, Status); } while (0);
                for (k=0;k<50;k++)
                {
                        if(Status & ((BYTE)(1<<0)))
                        {
                                Status = inb_p((int)(ulSMBusBaseAddress + (((BYTE)0x00))));
                                do { if (smbusDebug & (1 << (2))) printk(KERN_DEBUG "smbus(%d):" "CSmbus::WaitCmdDone: wait for Status not busy (%d 0x%02X)\n", (int)(jiffies-jiffies0),k,Status); } while (0);
                                udelay (5);
                        }
                        else break;
                }
            }
        }
    }
    if (!Done)
    {
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_WaitHostBusy: ## ERROR: timeout while waiting for transaction done (status=0x%02X)!\n", (int)(jiffies-jiffies0), Status); } while (0);
        CtrlReset = smbus_ResetSMBusCtrl();
    }
    return Success;
}
void smbus_ReleaseBus(void)
{
    if(CS_INTEL_ICH == Chipset)
    {
       outb_p((((BYTE)(1<<6))), (int)(ulSMBusBaseAddress + (((BYTE)0x00))));
       do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "\nCSmbus::ReleaseBus: Release ICH Semaphore\n", (int)(jiffies-jiffies0)); } while (0);
    }
}
BOOL smbus_CheckHardwareType(DWORD *pulType)
{
    UCHAR ucDeviceId1 = 0;
    UCHAR ucDeviceId2 = 0;
    UCHAR ucDeviceId3 = 0;
    UCHAR ucRevision = 0;
    unsigned char bSuccess = 0;
    *pulType = 0x00;
    bSuccess = smbus_ReadByte(0xE6, 0x00, &ucDeviceId1, 0);
    if (!bSuccess)
    {
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_CheckHardwareType : SMBus Read Operation failed!!\n", (int)(jiffies-jiffies0)); } while (0);
        return 0;
    }
    do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_CheckHardwareType : Device ID 1 = 0x%X\n", (int)(jiffies-jiffies0), ucDeviceId1); } while (0);
    bSuccess = smbus_ReadByte(0xE6, 0x01, &ucDeviceId2, 0);
    if (!bSuccess)
    {
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_CheckHardwareType : SMBus Read Operation failed!!!\n", (int)(jiffies-jiffies0)); } while (0);
        return 0;
    }
    do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_CheckHardwareType : Device ID 2 = 0x%X\n", (int)(jiffies-jiffies0), ucDeviceId2); } while (0);
    bSuccess = smbus_ReadByte(0xE6, 0x02, &ucDeviceId3, 0);
    if (!bSuccess)
    {
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_CheckHardwareType : SMBus Read Operation failed!!!!\n", (int)(jiffies-jiffies0)); } while (0);
        return 0;
    }
    do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_CheckHardwareType : Device ID 3 = 0x%X\n", (int)(jiffies-jiffies0), ucDeviceId3); } while (0);
    bSuccess = smbus_ReadByte(0xE6, 0x03, &ucRevision, 0);
    if (!bSuccess)
    {
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_CheckHardwareType : SMBus Read Operation failed!!!!\n", (int)(jiffies-jiffies0)); } while (0);
        return 0;
    }
    do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_CheckHardwareType : Revision ID = 0x%X\n", (int)(jiffies-jiffies0), ucRevision); } while (0);
    if ((ucDeviceId1 == 'S') &&
        (ucDeviceId2 == 'C') &&
        (ucDeviceId3 == 'Y'))
    {
        *pulType = 0x200;
        return 1;
    }
    if ((ucDeviceId1 == 'H') &&
        (ucDeviceId2 == 'Y') &&
        (ucDeviceId3 == 'D'))
    {
        *pulType = 0x40;
        return 1;
    }
    if ((ucDeviceId1 == 'P') &&
        (ucDeviceId2 == 'O') &&
        (ucDeviceId3 == 'S'))
    {
        *pulType = 0x20;
        return 1;
    }
    if ((ucDeviceId1 == 'P') &&
        (ucDeviceId2 == 'E') &&
        (ucDeviceId3 == 'G'))
    {
        if ( ucRevision >= 0x10 )
            *pulType = 0x10 | 0x08;
        else
            *pulType = 0x08;
        return 1;
    }
    if ((ucDeviceId1 == 'N') &&
        (ucDeviceId2 == 'T') &&
        (ucDeviceId3 == 'L'))
    {
        *pulType = 0x04;
        return 1;
    }
    return 0;
}
void smbus_PowerDown(void)
{
        BYTE ucMagic;
        ucMagic = *((BYTE *)phys_to_virt(0x00000416));
        if (ucMagic & 0x80)
        {
                do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "smbus_PowerDown : Bios Shutdown, magic 0x%02x\n", (int)(jiffies-jiffies0), ucMagic); } while (0);
                *((BYTE *)phys_to_virt(0x00000416)) = ucMagic & 0x7f;
                *((WORD *)phys_to_virt(0x00000472)) = 0x1234;
                CMOS_WRITE(0x00, 0x0f);
                outb_p(0xfe, KBD_CNTL_REG);
        }
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "smbus_PowerDown : Shutdown failed\n", (int)(jiffies-jiffies0)); } while (0);
}
void asus_PowerDown(char *CmdBuffer, char *ResultBuffer, SMBI_CMD_ROUTINE fSmbiExec)
{
        do { if (smbusDebug & (1 << (1))) printk(KERN_DEBUG "smbus(%d):" "asus_PowerDown(%p,%p,%p)\n", (int)(jiffies-jiffies0), CmdBuffer, ResultBuffer, fSmbiExec); } while (0);
        *CmdBuffer = 0x03;
        CmdBuffer++;
        *CmdBuffer = 0x01;
        ASMX86(PUSH_RDX);
        ASMX86(PUSH_RAX);
    (*fSmbiExec)();
        ASMX86(POP_RAX);
        ASMX86(POP_RDX);
        do { if (smbusDebug) printk(KERN_DEBUG "smbus(%d):" "asus_PowerDown : Shutdown failed (result: 0x%x)\n", (int)(jiffies-jiffies0), (int)*ResultBuffer); } while (0);
}
  
