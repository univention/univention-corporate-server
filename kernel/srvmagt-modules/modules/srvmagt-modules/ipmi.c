/* $Copyright$
 *  Copyright (C) Fujitsu Siemens Computers GmbH 2001, 2002, 2004, 2005, 2006
 *  All rights reserved
 */
#ident "$Header$"
#ifndef WITHOUT_INCLUDES
#ifndef KERNEL26
#ifndef __KERNEL__
#  define __KERNEL__
#endif
#ifndef MODULE_SUB
#  define MODULE
#endif
#endif  // KERNEL26
#ifndef PRECOMPILE
#ifndef KERNEL26
#include <linux/modversions.h>
#endif
#endif  // PRECOMPILE
#include <linux/module.h>
#include <linux/types.h>
#include <linux/kernel.h>
#include <linux/sched.h>    // includes <linux/spinlock.h>
#include <linux/mm.h>
#include <linux/string.h>
#include <linux/delay.h>
#include <linux/errno.h>
#include <linux/ioctl.h>
#include <linux/timer.h>
#include <linux/pci.h>
#include <linux/pm.h>
#include <asm/io.h>            	/* inb */
#include <asm/uaccess.h>		/* put_user */
#ifndef LINUX_VERSION_CODE
#include <linux/version.h>
#endif  // LINUX_VERSION_CODE
#if defined(__x86_64__)
#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,16)
#include <asm/ioctl32.h>
#endif // LINUX_VERSION_CODE < KERNEL_VERSION(2,6,16)
#endif // __x86_64__
#if LINUX_VERSION_CODE < KERNEL_VERSION(2,4,00)
#ifndef KERNEL26
#include <linux/kcomp.h>
#endif
#endif // LINUX_VERSION_CODE < KERNEL_VERSION(2,4,00)
// On e.g. SLES10 the kernel version from 2.6.16 is used
// So, we have to adjust some defines
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,16)
#ifndef KERNEL2616
#define	KERNEL2616								 1
#endif  // KERNEL2616
#ifndef USE_SYMBOL_IF_FOR_MODULE_INTERACTION
#define	USE_SYMBOL_IF_FOR_MODULE_INTERACTION	 1
#endif  // USE_SYMBOL_IF_FOR_MODULE_INTERACTION
#ifndef USE_REMAP_PFN_RANGE
#define	USE_REMAP_PFN_RANGE						 1
#endif  // USE_REMAP_PFN_RANGE
#endif  // LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,16)
#if defined(__x86_64__)
#if LINUX_VERSION_CODE < KERNEL_VERSION(2,6,16)
#ifndef USE_REGISTER_IOCTL32_CONVERSION
#define USE_REGISTER_IOCTL32_CONVERSION			 1
#endif  // USE_REGISTER_IOCTL32_CONVERSION
#else
#ifndef USE_COMPAT_IOCTL
#define USE_COMPAT_IOCTL						 1
#endif  // USE_COMPAT_IOCTL
#endif  // LINUX_VERSION_CODE < KERNEL_VERSION(2,6,16)
#endif  // __x86_64__
//
// SASSI #12324290; Oktawian Krawczuk; 24.10.2005
// We use MODULE_LICENSE("GPL") on Kernels 2.4.x too.
// This avoids the "... will taint the kernel: no license" message
// on insmod command.
// We do this change only for Linux Agents 3.10.x, 4.10.x, and 4.11.x
//
// #ifdef KERNEL26
MODULE_LICENSE("GPL");
// #endif
#endif // WITHOUT_INCLUDES
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
typedef enum
{
        Unknown = 0x00,
        KCS,
        SMIC,
        BT
} InterfaceType, *PInterfaceType;
typedef struct
{
        BYTE data_reg;
        BYTE control_reg;
} SmicRegs;
typedef enum
{
    BYTE_BOUNDARY = 0x00,
    BIT32_BOUNDARY,
    BYTE16_BOUNDARY
}REGISTER_SPACING;
#pragma pack (1)
typedef struct tagSMBIOSEntryPoint
{
        char schAnchorString[4];
        BYTE byCheckSum;
        BYTE byLength;
        BYTE bySmBiosMajorVersion;
        BYTE bySmBiosMinorVersion;
        WORD wMaxSize;
        BYTE byepRevision;
        BYTE byFmtArea[5];
        BYTE byImAnchor[5];
        BYTE byImCheckSum;
        WORD wTableLength;
    DWORD dwTableAddress;
        WORD nSmBiosStructures;
        BYTE bybcdRevision;
} SMBIOSEntryPoint, *PSMBIOSEntryPoint;
typedef struct tadSMBIOSHeader
{
        BYTE Type;
        BYTE Length;
        WORD Handle;
} SMBIOSHeader, *PSMBIOSHeader;
typedef struct tagIPMIDeviceInformation
{
        SMBIOSHeader smbhdr;
    BYTE InterfaceType;
    BYTE SpecRevision;
    BYTE I2CSlaveAddress;
    BYTE NVDevAddress;
    struct {
                DWORD LowPart;
                DWORD HighPart;
        }BaseAddress;
    BYTE bBamIntrTrigger : 1;
    BYTE bBamIntrPolarity : 1;
    BYTE bBamIntrReserved : 1;
    BYTE bBamInterruptInfo : 1;
    BYTE bBamLSBitAddress : 1;
    BYTE bBamReserved : 1;
    BYTE bBamRegisterSpacing : 2;
    BYTE InterruptNumber;
} IPMIDeviceInformation, *PIPMIDeviceInformation;
typedef struct {
        BYTE nfLn;
        BYTE cmd;
        BYTE data[1];
} BmcRequest;
typedef struct {
        BYTE nfLn;
        BYTE cmd;
        BYTE cCode;
        BYTE data[1];
} BmcResponse;
#pragma pack ()
#pragma pack (1)
typedef struct
{
        BYTE cmdType;
        BYTE rsSa;
        BYTE busType;
        BYTE netFn;
        BYTE rsLun;
        BYTE reserved1[3];
        DWORD64 pdata;
        DWORD dataLength;
        DWORD timeout;
        DWORD64 preply;
        DWORD replyLength;
} IOCTL_IPMB_REQUEST_LINUX;
#pragma pack ()
typedef enum {
    ACCESS_OK,
    ACCESS_ERROR,
    ACCESS_OUT_OF_RANGE,
    ACCESS_END_OF_DATA,
    ACCESS_UNSUPPORTED,
    ACCESS_INVALID_TRANSACTION
}ACCESS_STATUS;
#ifdef KERNEL2616
#define DRIVER_PARAMETER(param,str,type,perm) module_param(param, type, perm)
#else
#define DRIVER_PARAMETER(param,str,type,perm) MODULE_PARM(param, str)
#endif
static int ipmiArchMode = 0x00000000;
DRIVER_PARAMETER(ipmiArchMode, "i", int, 0);
#ifdef DO_NOT_USE_OS_PM_POWER_OFF
#define DRIVER_POWEROFF_ROUTINE 0x00000002
#define DEFINE_SYMBOL_PM_POWER_OFF pm_power_off_t ipmi_pm_power_off = NULL
#define PM_POWER_OFF ipmi_pm_power_off
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
#else
#ifdef KERNEL2616
#ifdef XEN_KERNEL
#define DRIVER_KERNEL_MODE (0x02000000 | 0x04000000 | 0x08000000)
#else
#define DRIVER_KERNEL_MODE (0x02000000 | 0x04000000)
#endif
#else
#define DRIVER_KERNEL_MODE 0x02000000
#endif
#define DRIVER_PCI_PRESENT(result) {result = 1;}
#define DRIVER_EXPORT_SYMBOLS
#define DRIVER_MOD_INC_USE_COUNT
#define DRIVER_MOD_DEC_USE_COUNT
#define DRIVER_SET_OWNER do {ipmi_fops.owner = THIS_MODULE;} while (0)
#define DRIVER_SAVE_FLAGS(flags) local_save_flags(flags)
#define DRIVER_DISABLE_IRQ() local_irq_disable()
#define DRIVER_FLAGS_RESTORE(flags) local_irq_restore(flags)
#endif
#define DRIVER_FOPS_WITHOUT_COMPAT .ioctl = ipmi_ioctl, .open = ipmi_open, .release = ipmi_release
#define DRIVER_FOPS_WITH_COMPAT .ioctl = ipmi_ioctl, .compat_ioctl = ipmi_ioctl_compat, .open = ipmi_open, .release = ipmi_release
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
DRIVER_EXPORT_SYMBOLS;
static unsigned long jiffies0 = 0;
static short ipmiDebug = 0;
DRIVER_PARAMETER(ipmiDebug, "h", short, 0);
static short ipmiPowerOff = 1;
DRIVER_PARAMETER(ipmiPowerOff, "h", short, 0);
typedef void (*pm_power_off_t) (void);
DEFINE_SYMBOL_PM_POWER_OFF;
static pm_power_off_t ipmi_PowerOff_saved = NULL;
static BOOL ipmi_OS_Poff_routine_changed = 0;
static void ipmi_register_PowerOff_routine (void);
static void ipmi_unregister_PowerOff_routine (void);
                void ipmi_PowerOff (void);
static int ipmi_register_ioctl32 (void);
static void ipmi_unregister_ioctl32 (void);
static void DumpMsg (BYTE *msg, int cnt);
static void ipmi_init_BMC_timer (struct timer_list *pTimer);
static void ipmi_disable_BMC_timer (struct timer_list *pTimer);
static int ipmi_start_BMC_timer (struct timer_list *pTimer, int timeout, BOOL forcetimer);
static void ipmi_stop_BMC_timer (struct timer_list *pTimer);
static void ipmi_set_BMC_timeout (unsigned long data);
static BOOL ScanForIPMIDeviceInfo ( ULONG paSmBiosTableAddress, ULONG ulSmBiosTableLength);
static BOOL GetIPMIDeviceInformation (void);
static BOOL IsKCS (void);
static int wait_for_KCS_flag (BYTE flag, int delay_loops);
                int do_KCS_Abort_Transaction (void);
                int do_KCSSendMessage (BYTE *msgBuf, int length);
                int do_KCSReadBMCData (BYTE *msgBuf);
                int KCSReadBMCData (BYTE *msgBuf, int timeout, BOOL forcetimer);
                int KCSSendMessage (BYTE *msgBuf, int length, int timeout, BOOL forcetimer);
static BOOL IsSMIC (void);
static int wait_for_condition (int cond, int delay_loops, int busy_loops);
static void test_TX_READY_flag (void);
                SmicRegs SmicOut (BYTE smic_data, BYTE smic_control);
                int do_SMICSendMessage (BYTE *msgBuf, int length);
                int do_SMICReadBMCData (BYTE *msgBuf);
                int SMICReadBMCData (BYTE *msgBuf, int timeout, BOOL forcetimer);
                int SMICSendMessage (BYTE *msgBuf, int length, int timeout, BOOL forcetimer);
                void DetermineInterface (void);
                int ReadBMCData (BYTE *msgBuf, int timeout, BOOL forcetimer);
                int SendMessage (BYTE *msgBuf, int length, int timeout, BOOL forcetimer);
                BOOL enableMessageChannel (BYTE Channel, BOOL Enable);
                int IsIPMIControllerAvailable (void);
static int calcChecksum (BYTE *pData,int length);
static BOOL smsBufferAvail (void);
static int doIpmbCmd (IOCTL_IPMB_REQUEST_LINUX *pdata);
static BYTE getMessageFlags (void);
static int ipmi_ioctl (struct inode *inode,
                                                                                         struct file *file,
                                                                                         unsigned int cmd,
                                                                                         unsigned long arg);
                long ipmi_ioctl_compat (struct file *file,
                                                                                         unsigned int cmd,
                                                                                         unsigned long arg);
static int ipmi_open (struct inode *inode, struct file *file);
static int ipmi_release (struct inode *inode, struct file *file);
static int ipmi_DetermineEnvironment (void);
                int init_module (void);
                void cleanup_module (void);
static int ipmi_DisableIRQsFromBMC (void);
static int ipmi_ResetBMCCommunication (int method);
static int ipmi_GetPowerOffInhibit (void);
static int ipmi_SetPowerOffInhibit (BYTE value);
static int ipmi_SendOEMCmdToBMC (BYTE OpcodeGroup,
                                                                                         BYTE OpcodeSpecifier,
                                                                                         BYTE *SendData,
                                                                                         BYTE sendlen,
                                                                                         BYTE *ReceiveData,
                                                                                         BYTE *reclen);
static void ipmi_delay (int clocks);
static void ipmi_delay_busy (int clocks);
typedef void (*PDELAY) (int);
static PDELAY p_ipmi_delay = ipmi_delay;
                int ipmi_lock (int control_code);
                int ipmi_unlock (int control_code);
static BYTE ipmi_PowerOffInhibitState = (BYTE) 0;
static BYTE ipmi_IRQ_disabled = (BYTE) 0;
static BYTE ipmi_Comm_reinitialized = (BYTE) 0;
static BYTE ipmi_lockFunc_successful = (BYTE) 0;
static BYTE ipmi_unlockFunc_successful = (BYTE) 0;
static const int SUCCESS = 0;
static const char *IPMI_DEV = "ipmi";
static BYTE ipmi_KCS_status;
static BOOL ipmi_2times_wait_for_KCS_flag = 0;
static int ipmi_deviceOpen = -1;
static int ipmi_major = 0;
static int sequence = 0;
static BOOL OldIpmi=0;
static InterfaceType ipmi_BMCinterface = Unknown;
static ULONG bmcBaseAddress;
static BYTE bmcRegSpacing = 1;
static BYTE bmc_I2C_Address = 0x20;
static BYTE bmcVer = 0x90;
static DECLARE_MUTEX(ipmi_ioctl_mutex);
static spinlock_t bmcTimerlock;
static unsigned int bmcTimeoutOccured = 0;
static struct timer_list bmcTimer;
static unsigned int bmcTimerState = 0x00;
DRIVER_SYMBOL_IMPORT(pm_power_off_t ,copa_PowerOff);
DRIVER_SYMBOL_IMPORT(pm_power_off_t*,copa_PowerOff_saved);
DRIVER_SYMBOL_IMPORT(pm_power_off_t ,smbus_PowerOff);
DRIVER_SYMBOL_IMPORT(pm_power_off_t*,smbus_PowerOff_saved);
DRIVER_SYMBOL_EXPORT(ipmi_lock);
DRIVER_SYMBOL_EXPORT(ipmi_unlock);
DRIVER_SYMBOL_EXPORT(ipmi_PowerOff);
DRIVER_SYMBOL_EXPORT(ipmi_PowerOff_saved);
static BYTE dumpbuf[(3*256 +1)];
static void DumpMsg(BYTE *msg, int cnt)
{
        int i;
        BYTE *p;
        for (i=0, p=&(dumpbuf[0]); i < cnt; i++, msg++, p++) {
                if ((*p = ((*msg >> 0x04) + 0x30)) > 0x39) *p += 0x07;
                p++;
                if ((*p = ((*msg & 0x0F) + 0x30)) > 0x39) *p += 0x07;
                p++;
                *p = ' ';
        }
        *p = '\0';
        printk(KERN_DEBUG "ipmi(%d): data: 0x  %s\n", (int)(jiffies-jiffies0), dumpbuf);
        return;
}
static void ipmi_init_BMC_timer (struct timer_list *pTimer)
{
        unsigned long flags = 0;
        spin_lock_init(&bmcTimerlock);
        spin_lock_irqsave( &bmcTimerlock, flags );
        init_timer(pTimer);
        bmcTimeoutOccured = 0;
        bmcTimerState = 0x00;
        spin_unlock_irqrestore( &bmcTimerlock, flags );
        return;
}
static void ipmi_disable_BMC_timer (struct timer_list *pTimer)
{
        unsigned long flags = 0;
        spin_lock_irqsave( &bmcTimerlock, flags );
        if (timer_pending( pTimer ))
        {
                del_timer_sync( pTimer );
        }
        bmcTimerState = 0xFF;
        spin_unlock_irqrestore( &bmcTimerlock, flags );
        return;
}
static int ipmi_start_BMC_timer(struct timer_list *pTimer, int timeout, BOOL forcetimer)
{
        unsigned long flags = 0;
        spin_lock_irqsave( &bmcTimerlock, flags );
        if ((bmcTimerState == 0xFF) && !forcetimer)
        {
                spin_unlock_irqrestore( &bmcTimerlock, flags );
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_start_BMC_timer: start timer (%p) failed, unload in progress\n", (int)(jiffies-jiffies0), pTimer);
                return -EFAULT;
        }
        if (!timer_pending( pTimer ))
        {
                if (timeout > 0)
                {
                        init_timer( pTimer );
                        pTimer->function = &ipmi_set_BMC_timeout;
                        pTimer->data = (unsigned long) 0;
                        pTimer->expires = jiffies + ((unsigned long )timeout*HZ)/1000;
                        bmcTimeoutOccured = 0;
                        add_timer( pTimer );
                }
                else
                {
                        bmcTimeoutOccured = 0;
                }
                spin_unlock_irqrestore( &bmcTimerlock, flags );
                return 0;
        }
        else
        {
                spin_unlock_irqrestore( &bmcTimerlock, flags );
                printk(KERN_ERR "ipmi(%d): " "ipmi_start_BMC_timer: try to start the timer (%p) twice\n", (int)(jiffies-jiffies0), pTimer);
                return -EFAULT;
        }
}
static void ipmi_stop_BMC_timer(struct timer_list *pTimer)
{
        unsigned long flags = 0;
        spin_lock_irqsave( &bmcTimerlock, flags );
        if (timer_pending( pTimer ))
        {
                del_timer_sync( pTimer );
        }
        spin_unlock_irqrestore( &bmcTimerlock, flags );
        return;
}
static void ipmi_set_BMC_timeout(unsigned long data)
{
        bmcTimeoutOccured = 1;
        return;
}
static BOOL ScanForIPMIDeviceInfo ( ULONG paSmBiosTableAddress, ULONG ulSmBiosTableLength)
{
        int i;
        ULONG Length = ulSmBiosTableLength;
        PUCHAR pVirtualAddress = NULL, pucTemp = NULL, pvaSave = NULL;
        BOOL ErrataCompliant = 0;
        BOOL Success = 0;
        BOOL dounmap = 0;
        PIPMIDeviceInformation pInfo = NULL;
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ScanForIPMIDeviceInfo: Scan for record 38 ...\n", (int)(jiffies-jiffies0));
        if ((!paSmBiosTableAddress) || (ulSmBiosTableLength <= 0)) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Invalid Physical Address and Range of Bios Table\n", (int)(jiffies-jiffies0));
                return 0;
        }
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "INFO: SMBios Table 0x%0lX Length: 0x%0lX, (high_memory = 0x%0lX)\n", (int)(jiffies-jiffies0), paSmBiosTableAddress, ulSmBiosTableLength, virt_to_phys(high_memory));
        if (ipmiArchMode & 0x08000000) {
                pvaSave = pVirtualAddress = ioremap_nocache(paSmBiosTableAddress, ulSmBiosTableLength);
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "INFO: Physical address remapped by using ioremap_nocache\n", (int)(jiffies-jiffies0));
                dounmap = 1;
        } else {
                if ((ULONG)(paSmBiosTableAddress+ulSmBiosTableLength) < (ULONG)virt_to_phys(high_memory) ) {
                        pvaSave = pVirtualAddress = phys_to_virt(paSmBiosTableAddress);
                        dounmap = 0;
                } else {
                        pvaSave = pVirtualAddress = ioremap_nocache(paSmBiosTableAddress, ulSmBiosTableLength);
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "INFO: Physical address remapped by using ioremap_nocache\n", (int)(jiffies-jiffies0));
                        dounmap = 1;
                }
        }
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ScanForIPMIDeviceInfo: INFO: pVirtualAddress = 0x%016lX\n", (int)(jiffies-jiffies0), (long) pVirtualAddress);
        if (!pVirtualAddress) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "No Virtual Pointer to SMBios Table\n", (int)(jiffies-jiffies0));
                return 0;
        }
        while (Length > 0) {
                if (((PSMBIOSHeader)pVirtualAddress)->Type == 38) {
                        pInfo = (PIPMIDeviceInformation)pVirtualAddress;
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Located IPMI Device Info Record @0x%p Len: 0x%02X\n", (int)(jiffies-jiffies0), (void *)pVirtualAddress, ((PSMBIOSHeader)pVirtualAddress)->Length);
                        bmc_I2C_Address = pInfo->I2CSlaveAddress;
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "IPMI BMC I2C Address: 0x%02X\n", (int)(jiffies-jiffies0), bmc_I2C_Address);
                        if (!bmc_I2C_Address || bmc_I2C_Address == 0xFF)
                                bmc_I2C_Address = 0x20;
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "IPMI BMC I2C Address used !: 0x%02X\n", (int)(jiffies-jiffies0), bmc_I2C_Address);
                        switch(pInfo->InterfaceType) {
                                case KCS:
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCS Interface detected. Setting up...\n", (int)(jiffies-jiffies0));
                                        ipmi_BMCinterface = KCS;
                                        break;
                                case SMIC:
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "SMIC Interface detected. Setting up...\n", (int)(jiffies-jiffies0));
                                        ipmi_BMCinterface = SMIC;
                                        break;
                                case Unknown:
                                case BT:
                                default:
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "BT/Unknown Interface NOT supported.\n", (int)(jiffies-jiffies0));
                                        ipmi_BMCinterface = Unknown;
                                        break;
                        }
                        bmcRegSpacing = 1;
                        if ( ((PSMBIOSHeader)pVirtualAddress)->Length > 0x10) {
                                ErrataCompliant = 1;
                        }
                        if (ErrataCompliant) {
                                switch(pInfo->bBamRegisterSpacing)
                                {
                                        case BYTE_BOUNDARY:
                                                bmcRegSpacing = 1;
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Reg. Spacing is BYTE (1)\n", (int)(jiffies-jiffies0));
                                                break;
                                        case BIT32_BOUNDARY:
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Reg. Spacing is DWORD (4)\n", (int)(jiffies-jiffies0));
                                                bmcRegSpacing = 4;
                                                break;
                                        case BYTE16_BOUNDARY:
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Reg. Spacing is QWORD (16)\n", (int)(jiffies-jiffies0));
                                                bmcRegSpacing = 16;
                                                break;
                                        default:
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Inv. Register Spacing ... using default\n", (int)(jiffies-jiffies0));
                                                bmcRegSpacing = 1;
                                                break;
                                }
                        }
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "BMC BaseAddress    : 0x%08X:%08X\n", (int)(jiffies-jiffies0), pInfo->BaseAddress.HighPart, pInfo->BaseAddress.LowPart);
                        if (pInfo->BaseAddress.LowPart & 0x01) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Base Address is I/O Mapped.\n", (int)(jiffies-jiffies0));
                                bmcBaseAddress = pInfo->BaseAddress.LowPart;
                                if ((ipmiArchMode & 0x20000000) || (ipmiArchMode & 0x40000000)) {
                                        bmcBaseAddress |= (ULONG)(((DWORD64)pInfo->BaseAddress.HighPart) << 32);
                                }
                                if (ErrataCompliant) {
                                        bmcBaseAddress &= ~0x01;
                                        bmcBaseAddress |= pInfo->bBamLSBitAddress;
                                }
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Final BMC Base Address is @ 0x%lX\n", (int)(jiffies-jiffies0), bmcBaseAddress);
                                switch (ipmi_BMCinterface) {
                                        case KCS:
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "INFO: KCS DATA: 0x%lX KCS CMD_STATUS: 0x%lX \n", (int)(jiffies-jiffies0), (bmcBaseAddress), ((bmcBaseAddress) + 1));
                                                break;
                                        case SMIC:
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "INFO: SMIC DATA: 0x%lX  CNTL: 0x%lX FLAG: 0x%lX\n", (int)(jiffies-jiffies0), (bmcBaseAddress), ((bmcBaseAddress) + 1), ((bmcBaseAddress) + 2));
                                                break;
                                        default:
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "INFO: Unsupported Interface in Record 38\n", (int)(jiffies-jiffies0));
                                                break;
                                }
                        }
                        Success = 1;
                        break;
                }
                Length -= ((PSMBIOSHeader)pVirtualAddress)->Length;
                pVirtualAddress += ((PSMBIOSHeader)pVirtualAddress)->Length;
                for(i=0,pucTemp = pVirtualAddress;(ULONG)i < Length;i++) {
                        if (!(pucTemp[i] || pucTemp[i+1])) {
                                break;
                        }
                }
                Length -= (i+2);
                pVirtualAddress += (i+2);
        }
        if (dounmap) iounmap((void *)pvaSave);
        return Success;
}
static BOOL GetIPMIDeviceInformation (void)
{
        BOOL Success = 0;
        ULONG SmBiosAddress = 0xF0000;
        ULONG ulLength = 0xFFFE;
        ULONG SmTableAddress = 0;
        ULONG ulTableLength = 0;
        PSMBIOSEntryPoint pSmEp = NULL;
        UCHAR ucChecksum;
        PUCHAR pVirtualAddress = NULL;
        ULONG Offset;
        BOOL dounmap = 0;
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "GetIPMIDeviceInformation: Scan for IPMI info ...\n", (int)(jiffies-jiffies0));
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "INFO: SMBios Address 0x%0lX Length: 0x%0lX, (high_memory = 0x%0lX)\n", (int)(jiffies-jiffies0), SmBiosAddress, ulLength, virt_to_phys(high_memory));
        if (ipmiArchMode & 0x08000000) {
                pVirtualAddress = ioremap_nocache(SmBiosAddress, ulLength);
                dounmap = 1;
        } else {
                if ((ULONG)(SmBiosAddress+ulLength) < (ULONG)virt_to_phys(high_memory) ) {
                        pVirtualAddress = phys_to_virt(SmBiosAddress);
                        dounmap = 0;
                } else {
                        pVirtualAddress = ioremap_nocache(SmBiosAddress, ulLength);
                        dounmap = 1;
                }
        }
        if (!pVirtualAddress) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR: No Virtual pointer to SMBIOS Memory\n", (int)(jiffies-jiffies0));
                return 0;
        }
        for(Offset=0,pSmEp=NULL; Offset<ulLength - sizeof("_SM_") + 1; Offset++) {
                if (strncmp(pVirtualAddress + Offset, "_SM_", sizeof("_SM_")-1) == 0) {
                        pSmEp = (PSMBIOSEntryPoint)(pVirtualAddress + Offset);
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "SMBIOS Entry Point @ 0x%p, offset: 0x%0lX\n", (int)(jiffies-jiffies0), (void *)pSmEp, Offset);
                        break;
                }
        }
        if (!pSmEp) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "WARNING: Unable to Locate SMBIOS signature\n", (int)(jiffies-jiffies0));
                if (dounmap) iounmap((void *)pVirtualAddress);
                return 0;
        }
        for(Offset=0,ucChecksum=0x00;Offset<pSmEp->byLength;Offset++) {
                ucChecksum += (UCHAR) *((PUCHAR)pSmEp + Offset);
        }
        if (ucChecksum) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Invalid BIOS Entrypoint Checksum\n", (int)(jiffies-jiffies0));
                if (dounmap) iounmap((void *)pVirtualAddress);
                return 0;
        }
        if ((pSmEp->bySmBiosMajorVersion < 2) || (pSmEp->bySmBiosMinorVersion < 3)) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " " SMBIOS Incompatible Version (%x.%x) detected\n", (int)(jiffies-jiffies0), pSmEp->bySmBiosMajorVersion, pSmEp->bySmBiosMinorVersion);
        } else {
                SmTableAddress = (ULONG)pSmEp->dwTableAddress;
                ulTableLength = (ULONG)pSmEp->wTableLength;
                if (dounmap) {
                        iounmap((void *)pVirtualAddress);
                        dounmap = 0;
                }
                Success = ScanForIPMIDeviceInfo(SmTableAddress, ulTableLength);
                if (!Success) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR: Record Type 38 Could NOT be located\n", (int)(jiffies-jiffies0));
                }
        }
        if (dounmap) iounmap((void *)pVirtualAddress);
        return Success;
}
static BOOL IsKCS(void)
{
        if((inb(((bmcBaseAddress) + 1)) == 0xFF) &&
                (inb((bmcBaseAddress)) == 0xFF))
        {
                return(0);
        }
        else
        {
                return(1);
        }
}
static int wait_for_KCS_flag (BYTE flag, int delay_loops)
{
        int dl;
        int mod;
        if (ipmi_2times_wait_for_KCS_flag)
                delay_loops *= 2;
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_for_KCS_flag %d, delay_loops=%d\n", (int)(jiffies-jiffies0), flag,delay_loops);
        for (dl=1; dl <= delay_loops; dl ++) {
                switch (flag) {
                 case 0x01 :
                                if (((BYTE)(inb(((bmcBaseAddress) + 1)) & 0x01)) == 0x01) {
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_4_obf dloops=%d\n", (int)(jiffies-jiffies0), dl);
                                        udelay (5);
                                        return (0);
                                }
                                break;
                 case 0x02 :
                                if ( !(((BYTE)(inb(((bmcBaseAddress) + 1)) & 0x02)) == 0x02)) {
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_4_ibf dloops=%d\n", (int)(jiffies-jiffies0), dl);
                                        udelay (5);
                                        return (0);
                                }
                                break;
                 default:
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "--> ERROR wait_for_KCS_flag: EINVAL\n", (int)(jiffies-jiffies0));
                                return (-EINVAL);
                }
                mod = dl % 8;
                if (mod == 0) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_for_KCS_flag: calling p_ipmi_delay(0)\n", (int)(jiffies-jiffies0));
                        p_ipmi_delay(0);
                }
                else {
                        udelay(50);
                }
                if (bmcTimeoutOccured == 1) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_for_KCS_flag: BMC Timer expired\n", (int)(jiffies-jiffies0));
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_for_KCS_flag: %d dloops, KCS_STATUS: 0x%02X\n", (int)(jiffies-jiffies0), dl,((BYTE)(inb(((bmcBaseAddress) + 1)))));
                        return (-ETIME);
                }
        }
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_for_KCS_flag: %d dloops, KCS_STATUS: 0x%02X\n", (int)(jiffies-jiffies0), dl,((BYTE)(inb(((bmcBaseAddress) + 1)))));
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "--> wait_for_KCS_flag: MAX-TIMEOUT occured\n", (int)(jiffies-jiffies0));
        return (-ETIME);
}
int do_KCS_Abort_Transaction(void)
{
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "do_KCS_Abort_Transaction: active Method entered\n", (int)(jiffies-jiffies0));
        return(0);
}
int do_KCSSendMessage(BYTE *msgBuf, int length)
{
        int i;
        int ret;
        if ((ret=wait_for_KCS_flag(0x02,10000)) != 0) {
                return (ret);
        }
        (outb(0x61,((bmcBaseAddress) + 1)));
        if ((ret=wait_for_KCS_flag(0x02,10000)) != 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Timeout during WRITE_START ibf full\n", (int)(jiffies-jiffies0));
                return (ret);
        }
        for (i = 0; i < length - 1; i++){
                udelay(20);
                ipmi_KCS_status = ((BYTE)(inb(((bmcBaseAddress) + 1))));
                if (ipmi_KCS_status & 0x01){
                        ((BYTE)(inb((bmcBaseAddress))));
                }
                if ((ipmi_KCS_status & 0xC0) != 0x80){
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR invalid KCS state 0x%02X on ReqByte %d\n", (int)(jiffies-jiffies0), (ipmi_KCS_status & 0xC0), i);
                        return(-1);
                }
                (outb(msgBuf[i],(bmcBaseAddress)));
                if ((ret=wait_for_KCS_flag(0x02,10000)) != 0) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Timeout during DATA ibf full\n", (int)(jiffies-jiffies0));
                        return (ret);
                }
        }
        (outb(0X62,((bmcBaseAddress) + 1)));
        if ((ret=wait_for_KCS_flag(0x02,10000)) != 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Timeout during WRITE_END ibf full\n", (int)(jiffies-jiffies0));
                return (ret);
        }
        udelay(10);
        ipmi_KCS_status = ((BYTE)(inb(((bmcBaseAddress) + 1))));
        if ((ipmi_KCS_status & 0xC0) != 0x80){
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR invalid KCS state 0x%02X on WRITE_END\n", (int)(jiffies-jiffies0), (ipmi_KCS_status & 0xC0));
                return(-1);
        }
        if (ipmi_KCS_status & 0x01) {
                ((BYTE)(inb((bmcBaseAddress))));
        }
        (outb(msgBuf[i],(bmcBaseAddress)));
        if ((ret=wait_for_KCS_flag(0x02,10000)) != 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Timeout during last DATA ibf full\n", (int)(jiffies-jiffies0));
                return (ret);
        }
        udelay(20);
        ipmi_KCS_status = ((BYTE)(inb(((bmcBaseAddress) + 1))));
        if ((ipmi_KCS_status & 0xC0) != 0x40){
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR invalid KCS state 0x%02X expect READ_STATE\n", (int)(jiffies-jiffies0), (ipmi_KCS_status & 0xC0));
                return(-1);
        }
        return(0);
}
int do_KCSReadBMCData(BYTE *msgBuf)
{
        int i;
        int ret;
        int cnt;
        int mod;
        int delaytime;
        BYTE state;
        BYTE dummy;
        for (i = 0; i <= 256; ) {
                cnt = 1;
                delaytime = 0;
                do {
                        udelay(20);
                        ipmi_KCS_status = ((BYTE)(inb(((bmcBaseAddress) + 1))));
                        state = (BYTE)(ipmi_KCS_status & 0xC0);
                        switch (state) {
                                case 0xC0:
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSReadBMCData invalid KCS_ERROR_STATE\n", (int)(jiffies-jiffies0));
                                        return(-1);
                                        break;
                                case 0x80:
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSReadBMCData invalid KCS_WRITE_STATE\n", (int)(jiffies-jiffies0));
                                        return(-1);
                                        break;
                                case 0x40:
                                        if ((ipmi_KCS_status & 0x01) != 0x01) {
                                                mod = cnt % 8;
                                                if (mod == 0) {
                                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSReadBMCData: calling p_ipmi_delay(0)\n", (int)(jiffies-jiffies0));
                                                        p_ipmi_delay(0);
                                                        delaytime += 10000;
                                                }
                                                else {
                                                        delaytime += 50;
                                                        udelay(50);
                                                }
                                                ++cnt;
                                                if (bmcTimeoutOccured == 1) {
                                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "WARNING: Timeout while waiting for obf when READ_STATE signalled\n", (int)(jiffies-jiffies0));
                                                        if (i >= 3) return(i);
                                                        else return (-ETIME);
                                                }
                                        }
                                        break;
                                case 0x00:
                                        if (OldIpmi) {
                                                return(i);
                                        } else {
                                                if ((ret=wait_for_KCS_flag(0x01,50)) != 0) {
                                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "WARNING: Timeout waiting for FINAL obf (IPMI 1.0 or later)\n", (int)(jiffies-jiffies0));
                                                }
                                                dummy = ((BYTE)(inb((bmcBaseAddress))));
                                                return(i);
                                        }
                                        break;
                                default:
                                        return(-1);
                        }
                } while ((ipmi_KCS_status & 0x01) != 0x01);
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSReadBMCData waited for IBF %d usec\n", (int)(jiffies-jiffies0), delaytime);
                udelay(10);
                msgBuf[i] = ((BYTE)(inb((bmcBaseAddress))));
                i++;
                udelay(10);
                if ((ret=wait_for_KCS_flag(0x02,10000)) != 0) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSReadBMCData wait for IBF: BMC Timer expired\n", (int)(jiffies-jiffies0));
                        return (ret);
                }
                (outb(0X68,(bmcBaseAddress)));
        }
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSReadBMCData KCS_IDLE_STATE ERROR\n", (int)(jiffies-jiffies0));
        return(-1);
}
int KCSReadBMCData(BYTE *msgBuf, int timeout, BOOL forcetimer)
{
        int ret = 0;
        if ((ret = ipmi_start_BMC_timer(&bmcTimer, timeout, forcetimer)) == 0)
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSReadBMCData: BMC timer (%p) started for %d ms\n", (int)(jiffies-jiffies0), &bmcTimer, timeout);
                ret = do_KCSReadBMCData(msgBuf);
                ipmi_stop_BMC_timer(&bmcTimer);
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSReadBMCData: BMC timer (%p) stopped\n", (int)(jiffies-jiffies0), &bmcTimer);
        }
        else
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSReadBMCData: KCS-Call already in progress (%p, ret=%d) -> bail out\n", (int)(jiffies-jiffies0), &bmcTimer, ret);
        }
        return ret;
}
int KCSSendMessage(BYTE *msgBuf, int length, int timeout, BOOL forcetimer)
{
        int ret = 0;
        if ((ret = ipmi_start_BMC_timer(&bmcTimer, timeout, forcetimer)) == 0)
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSSendMessage: BMC timer (%p) started for %d ms\n", (int)(jiffies-jiffies0), &bmcTimer, timeout);
                ret = do_KCSSendMessage(msgBuf,length);
                ipmi_stop_BMC_timer(&bmcTimer);
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSSendMessage: BMC timer (%p) stopped\n", (int)(jiffies-jiffies0), &bmcTimer);
        }
        else
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "KCSSendMessage: KCS-Call already in progress (%p, ret=%d) -> bail out\n", (int)(jiffies-jiffies0), &bmcTimer, ret);
        }
        return ret;
}
static BOOL IsSMIC(void)
{
        if((inb(((bmcBaseAddress) + 1)) != 0xFF))
        {
                return(1);
        }
        else
        {
                return(0);
        }
}
static int wait_for_condition (int cond, int delay_loops, int busy_loops)
{
        int dl, bl;
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_for_condition %d, delay_loops=%d, busy_loops=%d\n", (int)(jiffies-jiffies0), cond,delay_loops,busy_loops);
        for (dl=0; dl < delay_loops; dl ++) {
                switch (cond) {
                        case 1 :
                                for (bl=0; bl<busy_loops; bl++) {
                                        if (((inb(((bmcBaseAddress) + 2)) & 0x01) == 0x00)) {
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_4_not_busy dloops=%d, bloops=%d\n", (int)(jiffies-jiffies0), dl,bl);
                                                return (0);
                                        }
                                }
                                break;
                        case 2 :
                                for (bl=0; bl<busy_loops; bl++) {
                                        if (((inb(((bmcBaseAddress) + 2)) & (0x01 | 0x80)) == 0x80)) {
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_4_data_ready dloops=%d, bloops=%d\n", (int)(jiffies-jiffies0), dl,bl);
                                                return (0);
                                        }
                                }
                                break;
                        case 3 :
                                for (bl=0; bl<busy_loops; bl++) {
                                        if (((inb(((bmcBaseAddress) + 2)) & (0x01 | 0x40)) == 0x40)) {
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_4_send_ready dloops=%d, bloops=%d\n", (int)(jiffies-jiffies0), dl,bl);
                                                return (0);
                                        }
                                }
                                break;
                        default:
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "--> ERROR wait_for_condition: EINVAL\n", (int)(jiffies-jiffies0));
                                return (-EINVAL);
                }
                p_ipmi_delay(0);
                if (bmcTimeoutOccured == 1) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_for_condition: BMC Timer expired\n", (int)(jiffies-jiffies0));
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_for_condition: %d dloops\n", (int)(jiffies-jiffies0), dl);
                        return (-ETIME);
                }
        }
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "wait_for_condition: %d dloops\n", (int)(jiffies-jiffies0), dl);
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "--> wait_for_condition: MAX-TIMEOUT occured\n", (int)(jiffies-jiffies0));
        return (-ETIME);
}
static unsigned int wait_cond_transmit_ready = 3;
static void test_TX_READY_flag (void)
{
        int ret = 0;
        unsigned int timeout = 300 * 5;;
        if ((ret = ipmi_start_BMC_timer(&bmcTimer, timeout, 0)) == 0)
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "test_TX_READY_flag: BMC timer (%p) started for %d ms\n", (int)(jiffies-jiffies0), &bmcTimer, timeout);
                if (wait_for_condition(3,10000,100) != 0) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "WAIT_COND_TRANSMIT_READY is NOT signaled\n", (int)(jiffies-jiffies0));
                        wait_cond_transmit_ready = 1;
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "WAIT_COND_TRANSMIT_READY has been signaled\n", (int)(jiffies-jiffies0));
                        wait_cond_transmit_ready = 3;
                }
                ipmi_stop_BMC_timer(&bmcTimer);
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "test_TX_READY_flag: BMC timer (%p) stopped\n", (int)(jiffies-jiffies0), &bmcTimer);
        }
        else
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "test_TX_READY_flag: TX_READY-Call already in progress (%p, ret=%d) -> bail out\n", (int)(jiffies-jiffies0), &bmcTimer, ret);
        }
        return;
}
SmicRegs SmicOut(BYTE smic_data, BYTE smic_control)
{
        SmicRegs getc_regs;
        UCHAR flagReg;
        outb(smic_data,(bmcBaseAddress));
        outb(smic_control,((bmcBaseAddress) + 1));
        flagReg = inb(((bmcBaseAddress) + 2));
        outb((UCHAR)(flagReg | 0x01),((bmcBaseAddress) + 2));
        if (wait_for_condition(1,10000,1000) != 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "WAIT_COND_NOT_BUSY is NOT Signaled\n", (int)(jiffies-jiffies0));
                getc_regs.data_reg = 0;
                getc_regs.control_reg = 0;
                return(getc_regs);
        }
        getc_regs.data_reg= (BYTE)(inb((bmcBaseAddress)));
        getc_regs.control_reg= (BYTE)(inb(((bmcBaseAddress) + 1)));
        return(getc_regs);
}
int do_SMICSendMessage(BYTE *msgBuf, int length)
{
        SmicRegs netcom;
        int i;
        int ret;
        if ((ret=wait_for_condition(wait_cond_transmit_ready,10000,100)) != 0) {
                return (ret);
        }
        netcom = SmicOut(*msgBuf++,0x41);
        if (netcom.control_reg != 0xC1)
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR - did not receive SC_SMS_WR_START from SMIC\n", (int)(jiffies-jiffies0));
                return (-1);
        }
        for (i = 0; i < length - 2; i++)
        {
                if ((ret=wait_for_condition(wait_cond_transmit_ready,10000,100)) != 0) {
                        return (ret);
                }
                netcom = SmicOut(*msgBuf++,0x42);
                if (netcom.control_reg != 0xC2)
                {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR - did not receive SC_SMS_WR_NEXT from SMIC\n", (int)(jiffies-jiffies0));
                        return(-1);
                }
        }
        if ((ret=wait_for_condition(wait_cond_transmit_ready,10000,100)) != 0) {
                return (ret);
        }
        netcom = SmicOut(*msgBuf,0x43);
        if (netcom.control_reg != 0xC3)
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR - did not receive SC_SMS_WR_END from SMIC\n", (int)(jiffies-jiffies0));
                return(-1);
        }
        return(0);
}
int do_SMICReadBMCData(BYTE *msgBuf)
{
        SmicRegs netcom;
        int count = 0;
        int ret;
        if ((ret=wait_for_condition(2,10000,10)) != 0) {
                return (ret);
        }
        netcom = SmicOut(0,0x44);
        if (netcom.control_reg != 0xC4)
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Failed to get Read Start from SMIC.\n", (int)(jiffies-jiffies0));
                return(-1);
        }
        else
        {
                *msgBuf++ = netcom.data_reg;
        }
        for (count = 1; count < 67; count++)
        {
                if ((ret=wait_for_condition(2,10000,10)) != 0) {
                        return (ret);
                }
                netcom = SmicOut(0,0x45);
                if (netcom.control_reg != 0xC5)
                {
                        break;
                }
                else
                {
                        *msgBuf++ = netcom.data_reg;
                }
        }
        if (netcom.control_reg != 0xC6)
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "SMIC_SC_SMS_RD_END not received\n", (int)(jiffies-jiffies0));
                return(-1);
        }
        else
        {
                *msgBuf++ = netcom.data_reg;
        }
        if ((ret=wait_for_condition(2,10000,10)) != 0) {
                return (ret);
        }
        netcom = SmicOut(0,0x46);
        if ((netcom.control_reg != 0xC0) ||
                (netcom.data_reg != 0) || (count == 0))
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR !!!!\n", (int)(jiffies-jiffies0));
                return(-1);
        }
        return (count+1);
}
int SMICReadBMCData(BYTE *msgBuf, int timeout, BOOL forcetimer)
{
        int ret = 0;
        if ((ret = ipmi_start_BMC_timer(&bmcTimer, timeout, forcetimer)) == 0)
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "SMICReadBMCData: BMC timer (%p) started for %d ms\n", (int)(jiffies-jiffies0), &bmcTimer, timeout);
                ret = do_SMICReadBMCData(msgBuf);
                ipmi_stop_BMC_timer(&bmcTimer);
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "SMICReadBMCData: BMC timer (%p) stopped\n", (int)(jiffies-jiffies0), &bmcTimer);
        }
        else
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "SMICReadBMCData: SMIC-Call already in progress (%p, ret=%d) -> bail out\n", (int)(jiffies-jiffies0), &bmcTimer, ret);
        }
        return ret;
}
int SMICSendMessage(BYTE *msgBuf, int length, int timeout, BOOL forcetimer)
{
        int ret = 0;
        if ((ret = ipmi_start_BMC_timer(&bmcTimer, timeout, forcetimer)) == 0)
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "SMICSendMessage: BMC timer (%p) started for %d ms\n", (int)(jiffies-jiffies0), &bmcTimer, timeout);
                ret = do_SMICSendMessage(msgBuf,length);
                ipmi_stop_BMC_timer(&bmcTimer);
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "SMICSendMessage: BMC timer (%p) stopped\n", (int)(jiffies-jiffies0), &bmcTimer);
        }
        else
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "SMICSendMessage: SMIC-Call already in progress (%p, ret=%d) -> bail out\n", (int)(jiffies-jiffies0), &bmcTimer, ret);
        }
        return ret;
}
void DetermineInterface(void)
{
        if (ipmi_BMCinterface == Unknown) {
                if (!GetIPMIDeviceInformation()) {
                        bmcBaseAddress = ((ULONG)0xCA2);
                        if(IsKCS()) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "BMC Interface = Legacy KCS\n", (int)(jiffies-jiffies0));
                                ipmi_BMCinterface = KCS;
                        } else {
                                bmcBaseAddress = ((ULONG)0x0CA9);
                                if (IsSMIC()) {
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "BMC Interface = Legacy SMIC\n", (int)(jiffies-jiffies0));
                                        ipmi_BMCinterface = SMIC;
                                        test_TX_READY_flag();
                                } else {
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Could not detect BMC Interface - NON IPMI system\n", (int)(jiffies-jiffies0));
                                        ipmi_BMCinterface = Unknown;
                                }
                        }
                }
        }
}
int ReadBMCData(BYTE *msgBuf, int timeout, BOOL forcetimer)
{
        int bytesread;
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Receive-Timeout has been set to: %d (forcetimer=%d)\n", (int)(jiffies-jiffies0), timeout, forcetimer);
        bytesread = 0;
        switch(ipmi_BMCinterface)
        {
                case KCS:
                        bytesread=KCSReadBMCData(msgBuf, timeout, forcetimer);
                        break;
                case SMIC:
                        bytesread=SMICReadBMCData(msgBuf, timeout, forcetimer);
                        break;
                case BT:
                case Unknown:
                default:
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData: ERROR - unable to determine Interface type\n", (int)(jiffies-jiffies0));
                        return -1;
        }
        if (ipmiDebug >= 2) DumpMsg(msgBuf, bytesread);
        return(bytesread);
}
int SendMessage(BYTE *msgBuf, int length, int timeout, BOOL forcetimer)
{
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Send-Timeout has been set to: %d (forcetimer = %d)\n", (int)(jiffies-jiffies0), timeout, forcetimer);
        if (ipmiDebug >= 3) DumpMsg(msgBuf, length);
        switch(ipmi_BMCinterface)
        {
                case KCS:
                        return(KCSSendMessage(msgBuf,length, timeout, forcetimer));
                case SMIC:
                        return(SMICSendMessage(msgBuf,length, timeout, forcetimer));
                case BT:
                case Unknown:
                default:
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "SendMessage: ERROR - unable to determine Interface type\n", (int)(jiffies-jiffies0));
                        return -1;
        }
}
BOOL enableMessageChannel(BYTE Channel, BOOL Enable)
{
        BYTE reqBuffer [(3 + (7 + 96))];
        BYTE respBuffer[(3 + (7 + 96))];
        BmcRequest *bmcReq = (BmcRequest *)reqBuffer;
        BmcResponse *bmcResp= (BmcResponse *)respBuffer;
        int bytesread;
        bmcReq->nfLn = (((((0x06) << 2 ) & 0xFC) | ((0) & 0x3)));
        bmcReq->cmd = 0x32;
        bmcReq->data[0] = (BYTE)Channel & 0x0F;
        bmcReq->data[1] = Enable ? 0x01 : 0x00;
        if(SendMessage(reqBuffer, 2+2, 300, 0) != 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Error sending ENABLE_MESSAGE_CHANNEL_CMD command to BMC.\n", (int)(jiffies-jiffies0));
                return 0;
        }
        bytesread = ReadBMCData(respBuffer, 300, 0);
        if (bytesread < 0 || bmcResp->cCode != 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData ENABLE_MESSAGE_CHANNEL_CMD returned an error: bytesread = %d, cCode = %d\n", (int)(jiffies-jiffies0), bytesread, bmcResp->cCode);
                return 0;
        }
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData ENABLE_MESSAGE_CHANNEL_CMD returned %d bytes\n", (int)(jiffies-jiffies0), bytesread);
        return 1;
}
int IsIPMIControllerAvailable(void)
{
        BYTE CmdBuffer[256];
        BYTE ResponseBuffer[256];
        int BytesRead;
        int i;
        CmdBuffer[0] = 0x18;
        CmdBuffer[1] = 0x01;
        DetermineInterface();
        if (ipmi_BMCinterface == Unknown) return 0;
        if(SendMessage(CmdBuffer, 0x02, 300, 0) != 0)
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Error sending GetDeviceID command to BMC.\n", (int)(jiffies-jiffies0));
                return 0;
        }
        else
        {
                BytesRead = ReadBMCData(ResponseBuffer, 300, 0);
                if (BytesRead < 0) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData returned an error %d\n", (int)(jiffies-jiffies0), BytesRead);
                        return 0;
                }
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "OK sending GetDeviceID command to BMC. received %d bytes\n", (int)(jiffies-jiffies0), BytesRead);
                for (i=0;i<BytesRead;i++)
                {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Byte %d 0x%02X\n", (int)(jiffies-jiffies0), i,ResponseBuffer[i]);
                }
                if ((BytesRead >= 8) && (ResponseBuffer[2] == 0))
                {
                        OldIpmi = (BytesRead < 14) ? 1 : 0;
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Detected %s IPMI Interface\n", (int)(jiffies-jiffies0), OldIpmi ? "OLD (0.9)" : "NEW (1.0 or later)");
                        if (OldIpmi) {
                                bmcVer = 0x90;
                        } else {
                                switch (ResponseBuffer[7]) {
                                        case 0x01:
                                                bmcVer = (BYTE)0x01;
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "IPMI Version 1.0 Detected!\n", (int)(jiffies-jiffies0));
                                                break;
                                        case 0x51:
                                                bmcVer = (BYTE)0x51;
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "IPMI Version 1.5 Detected!\n", (int)(jiffies-jiffies0));
                                                break;
                                        case 0x02:
                                                bmcVer = (BYTE)0x51;
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "IPMI Version 2.0 Detected!\n", (int)(jiffies-jiffies0));
                                                break;
                                        default:
                                                bmcVer = (BYTE)0x01;
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Future IPMI Version?, assume Version 1.0\n", (int)(jiffies-jiffies0));
                                                break;
                                }
                        }
                        if (bmcVer == (BYTE)0x51) {
                                enableMessageChannel(0, 1);
                        }
                        return 1;
                } else {
                        return 0;
                }
        }
}
static int calcChecksum(BYTE *pData,int length)
{
        int i;
        int checksum;
        checksum=0;
        for(i=0;i<length;i++,pData++)
        {
                checksum += *pData;
        }
        checksum=(~checksum) + 1;
        return (checksum);
}
static BYTE getMessageFlags(void)
{
        BYTE reqBuffer[(3 + (7 + 96))];
        BYTE respBuffer[(3 + (7 + 96))];
        BmcRequest *bmcReq = (BmcRequest *)reqBuffer;
        BmcResponse *bmcResp= (BmcResponse *)respBuffer;
        int bytesread;
        bmcReq->nfLn = (((((0x06) << 2 ) & 0xFC) | ((0) & 0x3)));
        bmcReq->cmd = 0x31;
        if(SendMessage(reqBuffer, 2, 300, 0) != 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Error sending GET_MESSAGE_FLAGS_CMD command to BMC.\n", (int)(jiffies-jiffies0));
                return 0x00;
        }
        bytesread = ReadBMCData(respBuffer, 300, 0);
        if (bytesread < 0 || bmcResp->cCode != 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData GET_MESSAGE_FLAGS_CMD returned an error: bytesread = %d, cCode = %d\n", (int)(jiffies-jiffies0), bytesread, bmcResp->cCode);
                return 0x00;
        }
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData GET_MESSAGE_FLAGS_CMD returned %d bytes\n", (int)(jiffies-jiffies0), bytesread);
        return (bmcResp->data[0]);
}
static BOOL smsBufferAvail(void)
{
        return 1;
}
static int doIpmbCmd(IOCTL_IPMB_REQUEST_LINUX *prequest)
{
        int i;
        int err = 0;
        int retries;
        int bytesread;
        BYTE *prequestdata;
        BYTE *preplydata;
        BYTE msgbuffer[256];
        BYTE replybuffer[256];
        prequestdata = (BYTE *)(unsigned long)(prequest->pdata);
        preplydata = (BYTE *)(unsigned long)(prequest->preply);
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "doIpmbCmd: prequestdata = 0x%p, preplydata = 0x%p\n", (int)(jiffies-jiffies0), prequestdata, preplydata);
        if (prequest->rsSa != bmc_I2C_Address) {
                BYTE MessageFlags = 0x00;
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "IPMB Request I2C: 0x%02X Cmd 0x%02X NetFn: 0x%02X LUN %d Len %d\n", (int)(jiffies-jiffies0), prequest->rsSa, prequest->cmdType, prequest->netFn, prequest->rsLun, prequest->dataLength);
                msgbuffer[0]=0x18;
                if (OldIpmi) {
                        msgbuffer[1]=0x50;
                } else {
                        msgbuffer[1]=0x34;
                }
                msgbuffer[2]=prequest->busType;
                msgbuffer[3]=prequest->rsSa;
                msgbuffer[4]=(((prequest->netFn << 2) & 0xFC) | (prequest->rsLun & 3));
                msgbuffer[5]=calcChecksum(&msgbuffer[3],2);
                msgbuffer[6]=bmc_I2C_Address;
                sequence++;
                msgbuffer[7]=(((sequence << 2) & 0xFC) | 0x02);
                msgbuffer[8]=prequest->cmdType;
                if (prequest->dataLength > 0) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Cmd 0x%02X Request datalength %d\n", (int)(jiffies-jiffies0), prequest->cmdType, prequest->dataLength);
                        if ((prequest->dataLength < (256 -2)) && (prequestdata != NULL)) {
                                err = copy_from_user(&msgbuffer[9], (BYTE *)prequestdata, prequest->dataLength);
                                if (err != 0) {
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "doIpmbCmd: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, prequestdata);
                                        return -EFAULT;
                                }
                        }
                }
                msgbuffer[9+prequest->dataLength] = calcChecksum(&msgbuffer[6],3+prequest->dataLength);
                for (i=0;i<10;i++)
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "data %d: 0x%02X\n", (int)(jiffies-jiffies0), i,msgbuffer[i]);
                if(SendMessage(msgbuffer, prequest->dataLength + 10, prequest->timeout, 0) != 0)
                {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Error sending command Write Master SendMessage to BMC.\n", (int)(jiffies-jiffies0));
                        return -EINVAL;
                }
                bytesread = ReadBMCData(replybuffer, prequest->timeout, 0);
                if (bytesread < 0) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData returned an error %d\n", (int)(jiffies-jiffies0), bytesread);
                        return (bytesread);
                }
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData read %d bytes\n", (int)(jiffies-jiffies0), bytesread);
                if (replybuffer[2] == 0)
                {
                        for(retries=0;retries<20;retries++)
                        {
                                MessageFlags = getMessageFlags();
                                if (((bmcVer != 0x90) && (MessageFlags & 0x01)) ||
                                        ((bmcVer == 0x90) && smsBufferAvail())) {
                                        msgbuffer[0]=0x18;
                                        if (OldIpmi) {
                                                msgbuffer[1]=0x37;
                                        } else {
                                                msgbuffer[1]=0x33;
                                        }
                                        if(SendMessage(msgbuffer,2, prequest->timeout, 0) != 0)
                                        {
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Error sending GetMessage command to BMC.\n", (int)(jiffies-jiffies0));
                                                continue;
                                        }
                                        bytesread = ReadBMCData(replybuffer, prequest->timeout, 0);
                                        if (bytesread < 0) {
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData returned an error %d\n", (int)(jiffies-jiffies0), bytesread);
                                                continue;
                                        }
                                        for (i=0;i<bytesread;i++)
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "reply data %d: 0x%02X\n", (int)(jiffies-jiffies0), i,replybuffer[i]);
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData read %d bytes CompletionCode 0x%02X\n", (int)(jiffies-jiffies0), bytesread,replybuffer[2]);
                                        if (replybuffer[2] == 0)
                                        {
                                                if (OldIpmi) {
                                                        if ((replybuffer[7] == prequest->cmdType) && ((sequence & 0x3F) == ((replybuffer[6] >> 2) & 0x3F)))
                                                        {
                                                                break;
                                                        } else {
                                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR Got SMS Message which is not our response\n", (int)(jiffies-jiffies0));
                                                        }
                                                } else {
                                                        if ((replybuffer[8] == prequest->cmdType) && ((sequence & 0x3F) == ((replybuffer[7] >> 2) & 0x3F)))
                                                        {
                                                                break;
                                                        } else {
                                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR Got SMS Message which is not our response\n", (int)(jiffies-jiffies0));
                                                        }
                                                }
                                        }
                                }
                                p_ipmi_delay(10);
                        }
                        if (retries >= 20)
                        {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Could not get SMS Message after %d retries\n", (int)(jiffies-jiffies0), 20);
                                return -EINVAL;
                        }
                        if ((bytesread > 7) && (preplydata != NULL) && (bytesread < prequest->replyLength))
                        {
                                if (OldIpmi) {
                                        prequest->replyLength = bytesread-7;
                                        err = copy_to_user(preplydata, &replybuffer[6], prequest->replyLength);
                                        if (err != 0) {
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "doIpmbCmd: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, preplydata);
                                                return -EFAULT;
                                        }
                                        return 0;
                                } else {
                                        prequest->replyLength = bytesread-8;
                                        err = copy_to_user(preplydata, &replybuffer[7], prequest->replyLength);
                                        if (err != 0) {
                                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "doIpmbCmd: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, preplydata);
                                                return -EFAULT;
                                        }
                                        return 0;
                                }
                        }
                        else
                        {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData SMS Message too small %d bytes read\n", (int)(jiffies-jiffies0), bytesread);
                                return -EINVAL;
                        }
                }
                else
                {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData CompletionCode SendMessage 0x%02X 0x%02X 0x%02X \n", (int)(jiffies-jiffies0), replybuffer[0],replybuffer[1],replybuffer[2]);
                        return -EINVAL;
                }
        }
        else
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "BMC Req Cmd 0x%02X NetFn 0x%02X LUN %d Len %d\n", (int)(jiffies-jiffies0), prequest->cmdType, prequest->netFn, prequest->rsLun, prequest->dataLength);
                msgbuffer[0] = (((prequest->netFn << 2) & 0xFC) | (prequest->rsLun & 3));
                msgbuffer[1] = prequest->cmdType;
                if (prequest->dataLength > 0) {
                        if ((prequest->dataLength < (256 -2)) && (prequestdata != NULL)) {
                                err = copy_from_user(&msgbuffer[2], (BYTE *) prequestdata, prequest->dataLength);
                                if (err != 0) {
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "doIpmbCmd: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, prequestdata);
                                        return -EFAULT;
                                }
                        } else {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ERROR Invalid data pointer\n", (int)(jiffies-jiffies0));
                                return -EINVAL;
                        }
                }
                if ((prequest->netFn == 0x08 && prequest->cmdType == 0x01) ||
                (msgbuffer[0] == 0xB8 && msgbuffer[1] == 0xF5 && msgbuffer[5] == 0x13))
                        ipmi_2times_wait_for_KCS_flag = 1;
                if(SendMessage(msgbuffer, prequest->dataLength + 2, prequest->timeout, 0) != 0) {
                        ipmi_2times_wait_for_KCS_flag = 0;
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Error sending command to BMC.\n", (int)(jiffies-jiffies0));
                        return -EINVAL;
                }
                bytesread = ReadBMCData(replybuffer, prequest->timeout, 0);
                ipmi_2times_wait_for_KCS_flag = 0;
                if (bytesread < 0) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData returned an error %d\n", (int)(jiffies-jiffies0), bytesread);
                        return (bytesread);
                }
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ReadBMCData returned %d bytes\n", (int)(jiffies-jiffies0), bytesread);
                if ((bytesread > 0) && (preplydata != NULL) && (bytesread < prequest->replyLength)) {
                        prequest->replyLength = bytesread;
                        err = copy_to_user(preplydata, replybuffer, prequest->replyLength);
                        if (err != 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "doIpmbCmd: ERROR: copy_to_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, preplydata);
                                return -EFAULT;
                        }
                        return 0;
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Error invalid reply pointer\n", (int)(jiffies-jiffies0));
                        return -EINVAL;
                }
        }
}
long ipmi_ioctl_compat( struct file *file,
                                                                 unsigned int cmd,
                                                                 unsigned long arg)
{
        return (long) ipmi_ioctl(NULL, file, cmd, arg);
}
static int ipmi_ioctl( struct inode *inode,
                                                struct file *file,
                                                unsigned int cmd,
                                                unsigned long arg )
{
        unsigned int ioc_number = 0;
        unsigned int ioc_magic = 0;
        unsigned int ioc_size = 0;
        int err = 0;
        int ret = -EINVAL;
        IOCTL_IPMB_REQUEST_LINUX request;
        IOCTL_IPMB_REQUEST_LINUX *parg = NULL;
        ioc_magic = _IOC_TYPE(cmd);
        ioc_size = _IOC_SIZE(cmd);
        ioc_number = _IOC_NR(cmd);
        parg = (IOCTL_IPMB_REQUEST_LINUX *) (unsigned long) arg;
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: (%p,%p) IOCTL = 0x%08X, arg = 0x%016lX\n", (int)(jiffies-jiffies0), (void *)inode, (void *)file, cmd, arg);
        if (ioc_magic != 'i') {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: CmdType != magic (0x%08X 0x%08X) !!!\n", (int)(jiffies-jiffies0), ioc_magic, 'i');
                return -EINVAL;
        }
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ioc_size = 0x%08X (0x%08X)\n", (int)(jiffies-jiffies0), ioc_size, (int)sizeof(IOCTL_IPMB_REQUEST_LINUX));
        if ((ioc_number < 0x40) || (ioc_number > 0x43)) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: CmdNumber out of range (0x%08X [0x%08X 0x%08X]) !!! \n", (int)(jiffies-jiffies0), ioc_number, 0x40, 0x43);
                return -EINVAL;
        }
        switch (ioc_number) {
        case 0x41:
                {
                        if (parg == NULL) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: arg pointer is NULL !!! \n", (int)(jiffies-jiffies0));
                                return -EINVAL;
                        }
                        down(&ipmi_ioctl_mutex);
                        err = copy_from_user(&request, (BYTE *)parg, sizeof(IOCTL_IPMB_REQUEST_LINUX));
                        if (err != 0) {
                                up(&ipmi_ioctl_mutex);
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg);
                                return -EFAULT;
                        }
                        ret = doIpmbCmd(&request);
                        if (ret != 0) {
                                up(&ipmi_ioctl_mutex);
                                return ret;
                        }
                        err = put_user(request.replyLength, &(parg->replyLength));
                        if (err != 0) {
                                up(&ipmi_ioctl_mutex);
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: put_user failed err = 0x%08X, &(parg->replyLength) = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)&(parg->replyLength));
                                return -EFAULT;
                        }
                        up(&ipmi_ioctl_mutex);
                        break;
                }
        case 0x40:
                {
                        BYTE *preplydata;
                        if (parg == NULL) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: arg pointer is NULL !!! \n", (int)(jiffies-jiffies0));
                                return -EINVAL;
                        }
                        err = copy_from_user(&request, (BYTE *)parg, sizeof(IOCTL_IPMB_REQUEST_LINUX));
                        if (err != 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: copy_from_user failed err = 0x%08X, parg = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)parg);
                                return -EFAULT;
                        }
                        preplydata = (BYTE *)(unsigned long)(request.preply);
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: preplydata = 0x%p\n", (int)(jiffies-jiffies0), preplydata);
                        if ((preplydata == NULL) || (request.replyLength < sizeof(bmc_I2C_Address))) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: invalid reply pointer (0x%p) or length (0x%08X)\n", (int)(jiffies-jiffies0), preplydata, request.replyLength);
                                return -EINVAL;
                        }
                        err = copy_to_user(preplydata, &bmc_I2C_Address, sizeof(bmc_I2C_Address));
                        if (err != 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: copy_to_user failed err = 0x%08X, preplydata = 0x%p\n", (int)(jiffies-jiffies0), err, preplydata);
                                return -EFAULT;
                        }
                        err = put_user(sizeof(bmc_I2C_Address), &(parg->replyLength));
                        if (err != 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: put_user failed err = 0x%08X, &(parg->replyLength) = 0x%p\n", (int)(jiffies-jiffies0), err, (BYTE *)&(parg->replyLength));
                                return -EFAULT;
                        }
                        break;
                }
        case 0x42:
                {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: IPMI_LOCK command entered\n", (int)(jiffies-jiffies0));
                        if (ipmiDebug >= 255) {
                                if (ipmi_lock (1) < 0 ) {
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: IPMI_LOCK command failed !!!\n", (int)(jiffies-jiffies0));
                                        return -EINVAL;
                                }
                        } else {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ioctl-cmd IOCTL_IMB_BMC_LOCK (0x%08X) not allowd\n", (int)(jiffies-jiffies0), cmd);
                                return -EINVAL;
                        }
                        break;
                }
        case 0x43:
                {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: IPMI_UNLOCK command entered\n", (int)(jiffies-jiffies0));
                        if (ipmiDebug >= 255) {
                                if (ipmi_unlock (1) < 0 ) {
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: IPMI_UNLOCK command failed !!!\n", (int)(jiffies-jiffies0));
                                        return -EINVAL;
                                }
                        } else {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ioctl-cmd IOCTL_IMB_BMC_UNLOCK (0x%08X) not allowd\n", (int)(jiffies-jiffies0), cmd);
                                return -EINVAL;
                        }
                        break;
                }
        default:
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ioctl: ERROR: ioc_number =0x%04X not valid\n", (int)(jiffies-jiffies0), cmd);
                        return -EINVAL;
        }
        return SUCCESS;
}
static int ipmi_open(struct inode *inode, struct file *file)
{
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "-->ipmi_open: (%p,%p)\n", (int)(jiffies-jiffies0), (void *)inode, (void *)file);
        if(ipmi_deviceOpen < 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_open: device not initialized\n", (int)(jiffies-jiffies0));
                return -ENODEV;
        }
        ipmi_deviceOpen++;
        DRIVER_MOD_INC_USE_COUNT;
        return SUCCESS;
}
static int ipmi_release(struct inode *inode, struct file *file)
{
        ipmi_stop_BMC_timer(&bmcTimer);
        ipmi_deviceOpen--;
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "-->ipmi_release: (%p,%p)\n", (int)(jiffies-jiffies0), (void *)inode, (void *)file);
        DRIVER_MOD_DEC_USE_COUNT;
        return SUCCESS;
}
static struct file_operations ipmi_fops =
{
        DRIVER_FOPS
};
static int ipmi_DetermineEnvironment(void)
{
        char *pointer = NULL;
        if (ipmiArchMode == 0x00000000) {
                ipmiArchMode |= DRIVER_REMAP_RANGE_INTF;
                ipmiArchMode |= DRIVER_KERNEL_MODE;
                ipmiArchMode |= DRIVER_POWEROFF_ROUTINE;
                ipmiArchMode |= DRIVER_MODULE_INTERACTION;
                ipmiArchMode |= DRIVER_IOCTL32_CONV;
                if (sizeof(pointer) == 4) {
                        ipmiArchMode |= 0x10000000;
                } else if (sizeof(pointer) == 8) {
                        ipmiArchMode |= DRIVER_64BIT_MODE;
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: unknown XX-Bit mode\n", (int)(jiffies-jiffies0));
                        return -1;
                }
        } else {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: has been determined by insmod\n", (int)(jiffies-jiffies0));
        }
        if ( ipmiArchMode & 0x10000000 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: IA32 (x86) mode is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x40000000 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: IA64 mode is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x20000000 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: __x86_64__ mode is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x01000000 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: KERNEL 2.4    mode is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x02000000 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: KERNEL 2.6    mode is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x04000000 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: KERNEL 2.6.16 mode is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x08000000 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: KERNEL XEN    mode is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x00000100 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: OLD_REMAP_INTF     is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x00000200 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: NEW_REMAP_INTF     is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x00000400 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: PFN_REMAP_INTF     is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x00000010 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: IOCTL32_CONVERSION is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x00000020 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: IOCTL32_COMPAT     is active\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x00000001 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: OS pm_power_off    is used\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x00000002 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: My ipmi_pm_power_off is used\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x00000004 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: inter_module_xxx() functions are used\n", (int)(jiffies-jiffies0));
        if ( ipmiArchMode & 0x00000008 ) if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "Environment: symbol_get/put()   functions are used\n", (int)(jiffies-jiffies0));
        return 0;
}
static int ipmi_register_ioctl32 (void)
{
        int ret;
        if (ipmiArchMode & 0x00000010) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_ioctl32: register ioctl32 commands\n", (int)(jiffies-jiffies0));
                REGISTER_IOCTL32_CONVERSION(ret,_IOR ('i', 0x40, IOCTL_IPMB_REQUEST_LINUX));
                if (ret < 0) {
                        printk(KERN_ERR "ipmi(%d): " "ipmi_register_ioctl32: unable to register IOCTL_IMB_GET_BMC_I2C, ret=%d\n", (int)(jiffies-jiffies0), ret);
                        return ret;
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_ioctl32: successfully registered IOCTL_IMB_GET_BMC_I2C\n", (int)(jiffies-jiffies0));
                }
                REGISTER_IOCTL32_CONVERSION(ret,_IOR ('i', 0x41, IOCTL_IPMB_REQUEST_LINUX));
                if (ret < 0) {
                        printk(KERN_ERR "ipmi(%d): " "ipmi_register_ioctl32: unable to register IOCTL_IPMI_REQUEST, ret=%d\n", (int)(jiffies-jiffies0), ret);
                        return ret;
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_ioctl32: successfully registered IOCTL_IPMI_REQUEST\n", (int)(jiffies-jiffies0));
                }
                REGISTER_IOCTL32_CONVERSION(ret,0x42);
                if (ret < 0) {
                        printk(KERN_ERR "ipmi(%d): " "ipmi_register_ioctl32: unable to register IPMI_IOC_BMC_LOCK, ret=%d\n", (int)(jiffies-jiffies0), ret);
                        return ret;
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_ioctl32: successfully registered IPMI_IOC_BMC_LOCK\n", (int)(jiffies-jiffies0));
                }
                REGISTER_IOCTL32_CONVERSION(ret,0x43);
                if (ret < 0) {
                        printk(KERN_ERR "ipmi(%d): " "ipmi_register_ioctl32: unable to register IPMI_IOC_BMC_UNLOCK, ret=%d\n", (int)(jiffies-jiffies0), ret);
                        return ret;
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_ioctl32: successfully registered IPMI_IOC_BMC_UNLOCK\n", (int)(jiffies-jiffies0));
                }
        }
        return 0;
}
static void ipmi_unregister_ioctl32 (void)
{
        int ret;
        if (ipmiArchMode & 0x00000010) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unregister_ioctl32: unregister ioctl32 commands\n", (int)(jiffies-jiffies0));
                UNREGISTER_IOCTL32_CONVERSION(ret,_IOR ('i', 0x40, IOCTL_IPMB_REQUEST_LINUX));
                if (ret < 0) {
                        printk(KERN_ERR "ipmi(%d): " "ipmi_unregister_ioctl32: unable to unregister IOCTL_IMB_GET_BMC_I2C, ret=%d\n", (int)(jiffies-jiffies0), ret);
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unregister_ioctl32: successfully unregistered IOCTL_IMB_GET_BMC_I2C\n", (int)(jiffies-jiffies0));
                }
                UNREGISTER_IOCTL32_CONVERSION(ret,_IOR ('i', 0x41, IOCTL_IPMB_REQUEST_LINUX));
                if (ret < 0) {
                        printk(KERN_ERR "ipmi(%d): " "ipmi_unregister_ioctl32: unable to unregister IOCTL_IPMI_REQUEST, ret=%d\n", (int)(jiffies-jiffies0), ret);
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unregister_ioctl32: successfully unregistered IOCTL_IPMI_REQUEST\n", (int)(jiffies-jiffies0));
                }
                UNREGISTER_IOCTL32_CONVERSION(ret,0x42);
                if (ret < 0) {
                        printk(KERN_ERR "ipmi(%d): " "ipmi_unregister_ioctl32: unable to unregister IPMI_IOC_BMC_LOCK, ret=%d\n", (int)(jiffies-jiffies0), ret);
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unregister_ioctl32: successfully unregistered IPMI_IOC_BMC_LOCK\n", (int)(jiffies-jiffies0));
                }
                UNREGISTER_IOCTL32_CONVERSION(ret,0x43);
                if (ret < 0) {
                        printk(KERN_ERR "ipmi(%d): " "ipmi_unregister_ioctl32: unable to unregister IPMI_IOC_BMC_UNLOCK, ret=%d\n", (int)(jiffies-jiffies0), ret);
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unregister_ioctl32: successfully unregistered IPMI_IOC_BMC_UNLOCK\n", (int)(jiffies-jiffies0));
                }
        } else {
                return;
        }
}
int init_module(void)
{
        int ret;
        jiffies0 = jiffies;
        ipmi_init_BMC_timer(&bmcTimer);
        if ((ret = ipmi_DetermineEnvironment()) < 0) {
                printk(KERN_ERR "ipmi(%d): " "init_module: unable to determine OS/HW environment (return = %d)\n", (int)(jiffies-jiffies0), ret);
                return -ENODEV;
        }
        if (! IsIPMIControllerAvailable()) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "init_module: IPMI not present\n", (int)(jiffies-jiffies0));
                return -ENODEV;
        }
        DRIVER_SET_OWNER;
        if((ret = register_chrdev(ipmi_major, IPMI_DEV, &ipmi_fops)) < 0) {
                printk(KERN_ERR "ipmi(%d): " "init_module: unable to get major %d return = %d\n", (int)(jiffies-jiffies0), ipmi_major, ret);
                return -EIO;
        }
        if (ret > 0) ipmi_major = ret;
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "init_module: major device number = %d (0x%08x)\n", (int)(jiffies-jiffies0), ipmi_major, ipmi_major);
        ipmi_register_PowerOff_routine();
        DRIVER_INTER_MODULE_REGISTER(ipmi_lock);
        DRIVER_INTER_MODULE_REGISTER(ipmi_unlock);
        DRIVER_INTER_MODULE_REGISTER(ipmi_PowerOff);
        DRIVER_INTER_MODULE_REGISTER_P(ipmi_PowerOff_saved);
        if ( ipmiArchMode & 0x00000004 ) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "init_module: ipmi_lock           function (inter_module) registered\n", (int)(jiffies-jiffies0));
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "init_module: ipmi_unlock         function (inter_module) registered\n", (int)(jiffies-jiffies0));
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "init_module: ipmi_PowerOff       function (inter_module) registered\n", (int)(jiffies-jiffies0));
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "init_module: ipmi_PowerOff_saved function (inter_module) registered\n", (int)(jiffies-jiffies0));
        }
        if ((ret = ipmi_register_ioctl32()) < 0) {
                printk(KERN_ERR "ipmi(%d): " "init_module: ipmi_register_ioctl32 failed, ret = %d\n", (int)(jiffies-jiffies0), ret);
                cleanup_module();
                return -EIO;
        }
        ipmi_deviceOpen = 0;
        return SUCCESS;
}
void cleanup_module(void)
{
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "cleanup_module: entered\n", (int)(jiffies-jiffies0));
        ipmi_disable_BMC_timer(&bmcTimer);
        DRIVER_INTER_MODULE_UNREGISTER(ipmi_lock);
        DRIVER_INTER_MODULE_UNREGISTER(ipmi_unlock);
        DRIVER_INTER_MODULE_UNREGISTER(ipmi_PowerOff);
        DRIVER_INTER_MODULE_UNREGISTER(ipmi_PowerOff_saved);
        if ( ipmiArchMode & 0x00000004 ) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "cleanup_module: ipmi_lock           function (inter_module) unregistered\n", (int)(jiffies-jiffies0));
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "cleanup_module: ipmi_unlock         function (inter_module) unregistered\n", (int)(jiffies-jiffies0));
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "cleanup_module: ipmi_PowerOff       function (inter_module) unregistered\n", (int)(jiffies-jiffies0));
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "cleanup_module: ipmi_PowerOff_saved function (inter_module) unregistered\n", (int)(jiffies-jiffies0));
        }
        ipmi_unregister_PowerOff_routine();
        ipmi_unregister_ioctl32();
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,23)
	/* unregister_chrdev returns void now */
        unregister_chrdev(ipmi_major, IPMI_DEV);
#else
        int err;
        err = unregister_chrdev(ipmi_major, IPMI_DEV);
        if (err < 0) {
                printk(KERN_ERR "ipmi(%d): " "unregister_chrdev(%i) failed! return = %d\n", (int)(jiffies-jiffies0), ipmi_major, err);
        }
#endif
        ipmi_deviceOpen = -1;
}
static void ipmi_register_PowerOff_routine(void)
{
        pm_power_off_t tmp_POff_copa = NULL;
        pm_power_off_t tmp_POff_smbus = NULL;
        pm_power_off_t *tmp_POff_copa_sav = NULL;
        pm_power_off_t *tmp_POff_smbus_sav = NULL;
        DWORD tmp_ipmi_poff_prio = 2;
        if (ipmiPowerOff <= 0) {
                return;
        }
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: OS   PowerOff routine = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF);
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: IPMI PowerOff routine = 0x%016lX\n", (int)(jiffies-jiffies0), (long) ipmi_PowerOff);
        tmp_POff_copa = (pm_power_off_t) DRIVER_INTER_MODULE_GET(copa_PowerOff);
        tmp_POff_copa_sav = (pm_power_off_t *) DRIVER_INTER_MODULE_GET(copa_PowerOff_saved);
        tmp_POff_smbus = (pm_power_off_t) DRIVER_INTER_MODULE_GET(smbus_PowerOff);
        tmp_POff_smbus_sav = (pm_power_off_t *) DRIVER_INTER_MODULE_GET(smbus_PowerOff_saved);
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: tmp_POff_copa         = 0x%016lX\n", (int)(jiffies-jiffies0), (long) tmp_POff_copa);
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: tmp_POff_copa_sav     = 0x%016lX\n", (int)(jiffies-jiffies0), (long) tmp_POff_copa_sav);
        if (tmp_POff_copa_sav != NULL)
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: *tmp_POff_copa_sav    = 0x%016lX\n", (int)(jiffies-jiffies0), (long) *tmp_POff_copa_sav);
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: tmp_POff_smbus        = 0x%016lX\n", (int)(jiffies-jiffies0), (long) tmp_POff_smbus);
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: tmp_POff_smbus_sav    = 0x%016lX\n", (int)(jiffies-jiffies0), (long) tmp_POff_smbus_sav);
        if (tmp_POff_smbus_sav != NULL)
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: *tmp_POff_smbus_sav   = 0x%016lX\n", (int)(jiffies-jiffies0), (long) *tmp_POff_smbus_sav);
        if (PM_POWER_OFF == NULL) {
                 ipmi_PowerOff_saved = NULL;
                 PM_POWER_OFF = ipmi_PowerOff;
                 ipmi_OS_Poff_routine_changed = 1;
                 if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: IPMI PowerOff routine inserted \n", (int)(jiffies-jiffies0));
                 if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: PM_POWER_OFF        = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF);
                 if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: ipmi_PowerOff_saved = 0x%016lX\n", (int)(jiffies-jiffies0), (long) ipmi_PowerOff_saved);
        } else if (PM_POWER_OFF == tmp_POff_copa) {
                if (tmp_ipmi_poff_prio > 1) {
                        ipmi_OS_Poff_routine_changed = 0;
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: COPA PowerOff routine has already been inserted -> Do nothing!\n", (int)(jiffies-jiffies0));
                } else {
                         ipmi_PowerOff_saved = *tmp_POff_copa_sav;
                         PM_POWER_OFF = ipmi_PowerOff;
                         ipmi_OS_Poff_routine_changed = 1;
                         if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: COPA PowerOff routine replaced by IPMI routine\n", (int)(jiffies-jiffies0));
                         if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: PM_POWER_OFF        = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF);
                         if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: ipmi_PowerOff_saved = 0x%016lX\n", (int)(jiffies-jiffies0), (long) ipmi_PowerOff_saved);
                }
        } else if (PM_POWER_OFF == tmp_POff_smbus) {
                if (tmp_ipmi_poff_prio > 3) {
                        ipmi_OS_Poff_routine_changed = 0;
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: SMBUS PowerOff routine has already been inserted -> Do nothing!\n", (int)(jiffies-jiffies0));
                } else {
                         ipmi_PowerOff_saved = *tmp_POff_smbus_sav;
                         PM_POWER_OFF = ipmi_PowerOff;
                         ipmi_OS_Poff_routine_changed = 1;
                         if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: SMBUS PowerOff routine replaced by IPMI routine\n", (int)(jiffies-jiffies0));
                         if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: PM_POWER_OFF        = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF);
                         if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: ipmi_PowerOff_saved = 0x%016lX\n", (int)(jiffies-jiffies0), (long) ipmi_PowerOff_saved);
                }
        } else {
                 ipmi_PowerOff_saved = PM_POWER_OFF;
                 PM_POWER_OFF = ipmi_PowerOff;
                 ipmi_OS_Poff_routine_changed = 1;
                 if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: OS PowerOff routine replaced by IPMI Power Off routine!\n", (int)(jiffies-jiffies0));
                 if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: PM_POWER_OFF        = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF);
                 if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_register_PowerOff_routine: ipmi_PowerOff_saved = 0x%016lX\n", (int)(jiffies-jiffies0), (long) ipmi_PowerOff_saved);
        }
        if (tmp_POff_copa) DRIVER_INTER_MODULE_PUT(copa_PowerOff);
        if (tmp_POff_copa_sav) DRIVER_INTER_MODULE_PUT(copa_PowerOff_saved);
        if (tmp_POff_smbus) DRIVER_INTER_MODULE_PUT(smbus_PowerOff);
        if (tmp_POff_smbus_sav) DRIVER_INTER_MODULE_PUT(smbus_PowerOff_saved);
}
static void ipmi_unregister_PowerOff_routine(void)
{
        if (ipmiPowerOff <= 0) {
                return;
        }
        if (ipmi_OS_Poff_routine_changed && (PM_POWER_OFF == ipmi_PowerOff)) {
                 PM_POWER_OFF = ipmi_PowerOff_saved;
                 ipmi_PowerOff_saved = NULL;
                 ipmi_OS_Poff_routine_changed = 0;
                 if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unregister_PowerOff_routine: IPMI Power Off routine replaced by original routine !\n", (int)(jiffies-jiffies0));
                 if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unregister_PowerOff_routine: PM_POWER_OFF        = 0x%016lX\n", (int)(jiffies-jiffies0), (long) PM_POWER_OFF);
                 if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unregister_PowerOff_routine: ipmi_PowerOff_saved = 0x%016lX\n", (int)(jiffies-jiffies0), (long) ipmi_PowerOff_saved);
        }
}
void ipmi_PowerOff (void)
{
        int BytesToSend;
        int BytesRead;
        int RetryCnt;
        int TimeOut;
        BYTE SendBuf [16];
        BYTE RespBuf [16];
        printk(KERN_INFO "ipmi(%d): " "POWER OFF BY BMC !\n", (int)(jiffies-jiffies0));
        if (ipmi_PowerOff_saved != NULL) {
                (ipmi_PowerOff_saved)();
        }
        if (ipmi_DisableIRQsFromBMC() < 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_PowerOff: WARNING: Disabling IRQs from BMC failed !\n", (int)(jiffies-jiffies0));
        }
        ipmi_disable_BMC_timer(&bmcTimer);
        if (ipmi_ResetBMCCommunication(1) < 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_PowerOff: WARNING: BMC communication reinitializing failed !!!\n", (int)(jiffies-jiffies0));
        }
        SendBuf[0] = ((BYTE)(0x00 << 2) & 0xFC) | (((BYTE)0x00 & 0x03));
        SendBuf[1] = 0x02;
        SendBuf[2] = 0x00;
        BytesToSend = 3;
        for (RetryCnt = 0; RetryCnt < 6; RetryCnt++)
        {
                TimeOut = 300 + (RetryCnt * 500);
                if (SendMessage (SendBuf, BytesToSend, TimeOut, 1) != 0) {
                        continue;
                } else {
                        break;
                }
        }
        for (RetryCnt = 0; RetryCnt < 6; RetryCnt++)
        {
                TimeOut = 300 + (RetryCnt * 500);
                BytesRead = ReadBMCData (RespBuf, TimeOut, 1);
                if (BytesRead < 0) {
                        continue;
                } else {
                        break;
                }
        }
}
static void ipmi_delay (int clocks)
{
        set_current_state(TASK_UNINTERRUPTIBLE);
        schedule_timeout(clocks);
}
static void ipmi_delay_busy (int clocks)
{
        int i, j;
        if (clocks == 0) clocks = 1;
        for (j=0; j<clocks; j++) {
                for (i=0; i<200; i++) udelay (50);
        }
}
static int ipmi_DisableIRQsFromBMC (void)
{
        ipmi_IRQ_disabled = (BYTE) 1;
        return 0;
}
static int ipmi_ResetBMCCommunication(int method)
{
        int Success = 0;
        switch(ipmi_BMCinterface)
        {
                case KCS:
                        switch(method)
                        {
                                case 1:
                                        Success = 0;
                                        break;
                                case 2:
                                        Success = do_KCS_Abort_Transaction();
                                        break;
                                case 0:
                                default:
                                        Success = 0;
                                        break;
                        }
                        break;
                case SMIC:
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ResetBMCCommunication: WARNING: Rest of SMIC Interface NOT supported !\n", (int)(jiffies-jiffies0));
                        Success = -1;
                        break;
                case BT:
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ResetBMCCommunication: WARNING: Reset of BT Interface NOT supported !\n", (int)(jiffies-jiffies0));
                        Success = -1;
                        break;
                case Unknown:
                default:
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ResetBMCCommunication: WARNING: Reset of UNKNOWN Interface NOT supported !\n", (int)(jiffies-jiffies0));
                        Success = -1;
                        break;
        }
        ipmi_Comm_reinitialized = (BYTE) 1;
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_ResetBMCCommunication: Reset BMC Communication successfully done!\n", (int)(jiffies-jiffies0));
        return Success;
}
static int ipmi_GetPowerOffInhibit (void)
{
        BYTE value = 0;
        BYTE vallen = sizeof(BYTE);
        int ret = 0;
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_GetPowerOffInhibit: has been called \n", (int)(jiffies-jiffies0));
        ret = ipmi_SendOEMCmdToBMC ( 0x01,
                                                                        0x1D,
                                                                        NULL,
                                                                        0,
                                                                        &value,
                                                                        &vallen
                                                                );
        if (ret >= 0) {
                ipmi_PowerOffInhibitState = value;
        }
        return ret;
}
static int ipmi_SetPowerOffInhibit (BYTE value)
{
        BYTE val;
        int ret;
        val = value;
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_SetPowerOffInhibit: called with value = 0x%02X\n", (int)(jiffies-jiffies0), value);
        ret = ipmi_SendOEMCmdToBMC ( 0x01,
                                                                        0x1C,
                                                                        &val,
                                                                        sizeof(BYTE),
                                                                        NULL,
                                                                        NULL
                                                                );
        return ret;
}
static int ipmi_SendOEMCmdToBMC (BYTE OpcodeGroup, BYTE OpcodeSpecifier, BYTE *SendData, BYTE sendlen, BYTE *ReceiveData, BYTE *reclen)
{
        int i;
        int BytesToSend;
        int BytesRead;
        int RetryCnt;
        int TimeOut;
        int Success;
        BYTE SendBuf [256];
        BYTE RespBuf [256];
        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_SendOEMCmd: called with OpGr=0x%02X OpSp=0x%02X SL=%d\n", (int)(jiffies-jiffies0), OpcodeGroup, OpcodeSpecifier, sendlen);
        SendBuf[0] = ((BYTE)(0x2E << 2) & 0xFC) | (((BYTE)0x00 & 0x03));
        SendBuf[1] = OpcodeGroup;
        SendBuf[2] = (BYTE)(((unsigned int)0x802800 >> 16) & (unsigned int)0x000000FF);
        SendBuf[3] = (BYTE)(((unsigned int)0x802800 >> 8) & (unsigned int)0x000000FF);
        SendBuf[4] = (BYTE)(((unsigned int)0x802800 >> 0) & (unsigned int)0x000000FF);
        SendBuf[5] = OpcodeSpecifier;
        BytesToSend = 6;
        if ((SendData != NULL) || (sendlen > 0)) {
                SendBuf[6] = 0x00;
                SendBuf[7] = 0x00;
                SendBuf[8] = 0x00;
                SendBuf[9] = (BYTE)sendlen;
                BytesToSend = 10;
                for (i = 1; i <= sendlen; i++) {
                        SendBuf[9+i] = *SendData;
                        SendData++;
                }
                BytesToSend = BytesToSend + (i-1);
        }
        for (RetryCnt = 0; RetryCnt < 6; RetryCnt++)
        {
                TimeOut = 300 + (RetryCnt * 500);
                if (SendMessage (SendBuf, BytesToSend, TimeOut, 1) != 0) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_SendOEMCmd: WARNING: sending OEM command to BMC failed. (try=%d, Timeout=%d)\n", (int)(jiffies-jiffies0), RetryCnt, TimeOut);
                        Success = -1;
                        continue;
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_SendOEMCmd: OEM command to BMC successfully sent\n", (int)(jiffies-jiffies0));
                        Success = 0;
                        break;
                }
        }
        if (Success < 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_SendOEMCmd: ERROR: sending OEM command to BMC failed !!!\n", (int)(jiffies-jiffies0));
                return Success;
        }
        for (RetryCnt = 0; RetryCnt < 6; RetryCnt++)
        {
                TimeOut = 300 + (RetryCnt * 500);
                BytesRead = ReadBMCData (RespBuf, TimeOut, 1);
                if (BytesRead < 0) {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_SendOEMCmd: WARNING: reading OEM command from BMC failed. (try=%d, Timeout=%d)\n", (int)(jiffies-jiffies0), RetryCnt, TimeOut);
                        continue;
                } else {
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_SendOEMCmd: OEM command from BMC successfully read\n", (int)(jiffies-jiffies0));
                        break;
                }
        }
        if (BytesRead < 0) {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_SendOEMCmd: ERROR: reading OEM command from failed !!!\n", (int)(jiffies-jiffies0));
                return -1;
        }
        if ((BytesRead < 6) ||
                (RespBuf[0] != 0xBC) ||
                (RespBuf[1] != SendBuf[1]) ||
                (RespBuf[2] != 0x00) ||
                (RespBuf[3] != SendBuf[2]) ||
                (RespBuf[4] != SendBuf[3]) ||
                (RespBuf[5] != SendBuf[4]) )
        {
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_SendOEMCmd: ERROR: Command response ist NOT OK (bytes=%d, CompletionCode=0x%02X)\n", (int)(jiffies-jiffies0), BytesRead, RespBuf[2]);
                return -1;
        }
        if ((ReceiveData != NULL) &&
                (reclen != NULL) &&
                (*reclen > 0) &&
                (RespBuf[6] > 0) )
        {
                if (*reclen > RespBuf[6]) *reclen = RespBuf[6];
                for (i = 1; i <= *reclen; i++) {
                        *ReceiveData = RespBuf[6+i];
                        ReceiveData++;
                }
        }
        return 0;
}
int ipmi_lock (int control_code)
{
        int success = 0;
        ipmi_IRQ_disabled = (BYTE) 0;
        ipmi_Comm_reinitialized = (BYTE) 0;
        ipmi_lockFunc_successful = (BYTE) 0;
        switch (control_code) {
                case 1:
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_lock: called with control_code = 0x%08X\n", (int)(jiffies-jiffies0), control_code);
                        p_ipmi_delay = ipmi_delay_busy;
                        if (ipmi_DisableIRQsFromBMC() < 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_lock: WARNING: Disabling IRQs from BMC failed !\n", (int)(jiffies-jiffies0));
                        }
                        ipmi_disable_BMC_timer(&bmcTimer);
                        if (ipmi_ResetBMCCommunication(1) < 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_lock: WARNING: BMC communication reinitializing failed !!!\n", (int)(jiffies-jiffies0));
                        }
                        if (ipmi_GetPowerOffInhibit() < 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_lock: WARNING: Can't get PowerOffInhibit state from BMC !\n", (int)(jiffies-jiffies0));
                        }
                        if (ipmi_SetPowerOffInhibit ((BYTE) 1) < 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_lock: ERROR: Can't set PowerOffInhibit State to BMC !!!\n", (int)(jiffies-jiffies0));
                                success = -EINVAL;
                                break;
                        }
                        if (ipmi_GetPowerOffInhibit() < 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_lock: WARNING: Can't get BMC PowerOffInhibit state after setting!\n", (int)(jiffies-jiffies0));
                        } else {
                                if (ipmi_PowerOffInhibitState != (BYTE) 1) {
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_lock: ERROR: BMC PowerOffInhibit was NOT set correctly by previous commands (it returns = %d)!!!\n", (int)(jiffies-jiffies0), ipmi_PowerOffInhibitState);
                                        success = -EINVAL;
                                        break;
                                }
                        }
                        success = 0;
                        break;
                default:
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_lock: called with invalid control_code = 0x%08X\n", (int)(jiffies-jiffies0), control_code);
                        success = -EINVAL;
                        break;
        }
        p_ipmi_delay = ipmi_delay;
        if (success == 0 ) {
                ipmi_lockFunc_successful = (BYTE) 1;
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_lock: returns successfully\n", (int)(jiffies-jiffies0));
        }
        return success;
}
int ipmi_unlock (int control_code)
{
        int success = 0;
        ipmi_unlockFunc_successful = (BYTE) 0;
        switch (control_code) {
                case 1:
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unlock: called with control_code = 0x%08X\n", (int)(jiffies-jiffies0), control_code);
                        p_ipmi_delay = ipmi_delay_busy;
                        ipmi_disable_BMC_timer(&bmcTimer);
                        if ((ipmi_IRQ_disabled != (BYTE) 1) ||
                                (ipmi_Comm_reinitialized != (BYTE) 1) ||
                                (ipmi_lockFunc_successful != (BYTE) 1) ||
                                (ipmi_PowerOffInhibitState != (BYTE) 1)) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unlock: WARNING: unexpected BMC state detected (%d %d %d %d)!\n", (int)(jiffies-jiffies0), ipmi_IRQ_disabled, ipmi_Comm_reinitialized, ipmi_lockFunc_successful, ipmi_PowerOffInhibitState);
                        }
                        if (ipmi_GetPowerOffInhibit() < 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unlock: WARNING: Can't get the PowerOffInhibit state from BMC !\n", (int)(jiffies-jiffies0));
                        } else {
                                if (ipmi_PowerOffInhibitState != (BYTE) 1) {
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unlock: WARNING: BMC PowerOffInhibit state is NOT TRUE (as expected) (it is = %d)!!!\n", (int)(jiffies-jiffies0), ipmi_PowerOffInhibitState);
                                }
                        }
                        if (ipmi_SetPowerOffInhibit ((BYTE) 0) < 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unlock: ERROR: Can't unset the PowerOffInhibit of BMC !!!\n", (int)(jiffies-jiffies0));
                                success = -EINVAL;
                                break;
                        }
                        if (ipmi_GetPowerOffInhibit() < 0) {
                                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unlock: WARNING: Can't get the PowerOffInhibit state after setting!\n", (int)(jiffies-jiffies0));
                        } else {
                                if (ipmi_PowerOffInhibitState != (BYTE) 0) {
                                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unlock: ERROR: BMC PowerOffInhibit state was NOT set correctly by previous command (it is = %d)!!!\n", (int)(jiffies-jiffies0), ipmi_PowerOffInhibitState);
                                        success = -EINVAL;
                                        break;
                                }
                        }
                        success = 0;
                        break;
                default:
                        if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unlock: called with invalid control_code = 0x%08X\n", (int)(jiffies-jiffies0), control_code);
                        success = -EINVAL;
                        break;
        }
        p_ipmi_delay = ipmi_delay;
        if (success == 0 ) {
                ipmi_unlockFunc_successful = (BYTE) 1;
                if (ipmiDebug) printk(KERN_DEBUG "ipmi(%d): " "ipmi_unlock: returns successfully\n", (int)(jiffies-jiffies0));
        }
        return success;
}
  
