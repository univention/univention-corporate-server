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
#include <linux/sched.h>
#include <linux/mm.h>
#include <linux/string.h>
#include <linux/errno.h>
#include <linux/ioctl.h>
#include <linux/sched.h>
#include <linux/delay.h>
#ifndef KERNEL26
#include <linux/tqueue.h>
#endif  // KERNEL26
#include <linux/pci.h>
#include <linux/pm.h>
#include <linux/interrupt.h>
#include <asm/io.h>
#include <asm/system.h>
#include <asm/uaccess.h>
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
#ifndef LINUX_VERSION_CODE
#include <linux/version.h>
#endif  // LINUX_VERSION_CODE
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,4,00)
static DECLARE_WAIT_QUEUE_HEAD(WaitQ);
#else
#define vm_pgoff                        vm_offset
#define pci_resource_start(dev, i)      (dev->base_address[i])
static struct wait_queue *WaitQ = NULL;
#endif  // LINUX_VERSION_CODE >= KERNEL_VERSION(2,4,00)
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
#endif  // WITHOUT_INCLUDES
#ident "$Header$"
#ident "$Header: $"
typedef struct _IoctlStructPciInfo
{
        unsigned int BusNumber;
        unsigned int DeviceNumber;
        unsigned int FunctionNumber;
        unsigned short VendorId;
        unsigned short DeviceId;
        unsigned short SubVendorId;
        unsigned short SubDeviceId;
} IoctlPciInfo, IOCTL_STRUCT_PCI_INFO, *PIOCTL_STRUCT_PCI_INFO;
#pragma pack(1) 
typedef struct _CopernicusAShmemAnyObjectHeader
{
    unsigned int Type;
    unsigned int Length;
} COPA_SHMEM_ANY_HEADER, *PCOPA_SHMEM_ANY_HEADER;
typedef struct _CopernicusAShmemTopHeaderObject
{
    unsigned int Type;
    unsigned int Length;
    union
        {
                char c[4];
        unsigned int AsDWord;
    } Signature;
    unsigned int SharedMemLength;
    unsigned int Version;
        unsigned int Reserved1;
        unsigned int Reserved2;
        unsigned int Reserved3;
        unsigned int Reserved4;
        unsigned int DisconnectRequest;
        unsigned int Disconnected;
        unsigned int TopHeaderError;
        unsigned int AgentCmdQueueError;
        unsigned int AgentEventQueueError;
        unsigned int BiosCmdQueueError;
        unsigned int BiosEventQueueError;
        unsigned int Reserved12;
        unsigned int Reserved13;
        unsigned int Reserved14;
        unsigned int Reserved15;
        unsigned int Reserved16;
        unsigned int IntForAgent;
        unsigned int Properties;
        unsigned int Reserved19;
        unsigned int Reserved20;
} COPA_SHMEM_TOP_HEADER, *PCOPA_SHMEM_TOP_HEADER;
typedef struct _CopernicusAShmemQueueObject
{
        unsigned int Type;
        unsigned int Length;
        unsigned int Size;
        unsigned int ReadPos;
        unsigned int WritePos;
        unsigned int Count;
        unsigned int SpAccess;
        unsigned int DrvAccess;
        unsigned char Data[1];
} COPA_SHMEM_QUEUE, *PCOPA_SHMEM_QUEUE;
#pragma pack() 
#pragma pack (1)
typedef unsigned short V1_CMD_OPCODE;
typedef int time_t32;
typedef unsigned short V1_CMD_OPCODE_EXT;
typedef unsigned short V1_CMD_OBJECTID;
typedef unsigned short V1_CMD_DATA_LENGTH;
typedef unsigned short V1_CMD_CABINETNR;
typedef unsigned short V1_CMD_SETCOUNT;
typedef unsigned char V1_CMD_STATUS;
typedef struct {
        unsigned char Index:6;
        unsigned char Layer:2;
} V1_ModuleId_Index_Layer;
typedef union _V1_ModuleId {
        unsigned char Id;
        V1_ModuleId_Index_Layer u;
        V1_ModuleId_Index_Layer Index_Layer;
} V1_CMD_MODULEID, *P_V1_CMD_MODULEID;
typedef union _V1_StdData {
        unsigned char AsByte;
        unsigned short AsWord;
        unsigned int AsDWord;
        time_t32 AsTime;
        unsigned char AsByteStream[1];
        unsigned short AsWordStream[1];
        unsigned int AsDWordStream[1];
} V1_CMD_DATA, *P_V1_CMD_DATA;
typedef struct _V1_SC_Command {
        V1_CMD_OPCODE OpCode;
        V1_CMD_OPCODE_EXT OpCodeExt;
        V1_CMD_OBJECTID ObjectId;
        V1_CMD_CABINETNR CabinetNr;
        unsigned short Reserved;
        V1_CMD_SETCOUNT SetCount;
        V1_CMD_MODULEID ModuleId;
        V1_CMD_STATUS CmdStatus;
        V1_CMD_DATA_LENGTH DataLength;
        V1_CMD_DATA CmdData;
} V1_SC_COMMAND, *P_V1_SC_COMMAND;
#pragma pack ()
#ifdef KERNEL2616
#define DRIVER_PARAMETER(param,str,type,perm) module_param(param, type, perm)
#else
#define DRIVER_PARAMETER(param,str,type,perm) MODULE_PARM(param, str)
#endif
static int copaArchMode = 0x00000000;
DRIVER_PARAMETER(copaArchMode, "i", int, 0);
#ifdef DO_NOT_USE_OS_PM_POWER_OFF
#define DRIVER_POWEROFF_ROUTINE 0x00000002
#define DEFINE_SYMBOL_PM_POWER_OFF pm_power_off_t copa_pm_power_off = NULL
#define PM_POWER_OFF copa_pm_power_off
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
typedef void irqreturn_t;
#define IRQ_NONE
#define IRQ_HANDLED
#define IRQ_RETVAL(x)
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
#define DRIVER_SET_OWNER do {copa_fops.owner = THIS_MODULE;} while (0)
#define DRIVER_SAVE_FLAGS(flags) local_save_flags(flags)
#define DRIVER_DISABLE_IRQ() local_irq_disable()
#define DRIVER_FLAGS_RESTORE(flags) local_irq_restore(flags)
#endif
#define DRIVER_FOPS_WITHOUT_COMPAT .ioctl = copa_ioctl, .mmap = copa_mmap, .open = copa_open, .release = copa_release
#define DRIVER_FOPS_WITH_COMPAT .ioctl = copa_ioctl, .compat_ioctl = copa_ioctl_compat, .mmap = copa_mmap, .open = copa_open, .release = copa_release
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
static short copaDebug = 0;
DRIVER_PARAMETER(copaDebug, "h", short, 0);
static short copaPowerOff = 1;
DRIVER_PARAMETER(copaPowerOff, "h", short, 0);
typedef void (*pm_power_off_t) (void);
DEFINE_SYMBOL_PM_POWER_OFF;
static pm_power_off_t copa_PowerOff_saved = NULL;
static int copa_OS_Poff_routine_changed = 0;
static void copa_register_PowerOff_routine (void);
static void copa_unregister_PowerOff_routine (void);
                void copa_PowerOff (void);
static const int SUCCESS = 0;
static const char *COPA_DEV = "copa";
static const unsigned int SNI_VENDOR_ID = 0x110A;
static const unsigned int COPA_F1_DEVICE_ID = 0x007C;
static const unsigned int COPA_F0_DEVICE_ID = 0x007B;
static const unsigned int PCI_SUBDEVID_RSB = 0x007E;
static const unsigned long COPA_PCI_REG0_LEN = 4*1024;
static unsigned long phys_PCI_REG0_Address = 0;
static unsigned char *pvirt_PCI_REG0_Address = NULL;
static unsigned int *pDoorbellRegister = NULL;
static unsigned long phys_PCI_REG1_Address = 0;
static const unsigned long COPA_PCI_REG2_LEN = 0x4000;
static unsigned long phys_PCI_REG2_Address = 0;
static unsigned char *pvirt_PCI_REG2_Address = NULL;
static COPA_SHMEM_TOP_HEADER *pcopaTopHdr = NULL;
static unsigned int *pProperties = NULL;
static unsigned int Properties = 0;
static COPA_SHMEM_QUEUE *pcopaCommandQueue = NULL;
static COPA_SHMEM_QUEUE *pcopaEventQueue = NULL;
static const u8 COPA_DEVICE_CONTROL_REGISTER = 0x04;
static const u8 COPA_BASE_ADDRES_REGISTER0 = 0x10;
static const u8 COPA_BASE_ADDRES_REGISTER1 = 0x14;
static const u8 COPA_BASE_ADDRES_REGISTER2 = 0x18;
static const u8 COPA_INTERRUPT_LINE_REGISTER = 0x3C;
static const u8 COPA_INTERRUPT_PIN_REGISTER = 0x3D;
static const u8 COPA_MAILBOX_DATA = 0x40;
static const u8 COPA_MAILBOX_STATUS = 0x44;
static const u8 COPA_INTERRUPT_SET_REGISTER = 0x30;
static const u8 COPA_INTERRUPT_CLEAR_REGISTER = 0x34;
static int IsRSB = 0;
static unsigned short cabId = 0;
static int deviceOpen = 0;
static int copa_major = 0;
static struct pci_dev *copaf1Dev = NULL;
static struct pci_dev *copaf0Dev = NULL;
static int copa_interrupt_received = 0;
static unsigned int copaCommand[((sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA)) / sizeof(unsigned int)) + 8];
static V1_SC_COMMAND *pcopaCommandHeader = (V1_SC_COMMAND *)&copaCommand;
static int copa_open (struct inode *inode, struct file *file);
static int copa_release (struct inode *inode, struct file *file);
static void copa_vma_open (struct vm_area_struct *area);
static int copa_mmap (struct file *file, struct vm_area_struct *vma);
static irqreturn_t copa_irq_handler (int irq, void *dev_id, struct pt_regs *regs);
                long copa_ioctl_compat (struct file *file,
                                                                                 unsigned int cmd,
                                                                                 unsigned long arg );
static int copa_ioctl (struct inode *inode,
                                                                                 struct file *file,
                                                                                 unsigned int cmd,
                                                                                 unsigned long arg );
                int init_module (void);
                void cleanup_module (void);
static COPA_SHMEM_QUEUE * copa_FindShmemQueue (COPA_SHMEM_TOP_HEADER * pcopaTopHdr, int RequestType);
static int copa_DisableIRQsFromCopa (void);
static int copa_GetPowerOffInhibit (void);
static int copa_ResetAllShmemQueues (COPA_SHMEM_TOP_HEADER * pcopaTopHdr);
static int copa_WaitForShmemRestoring (COPA_SHMEM_TOP_HEADER * pcopaTopHdr);
static int copa_WriteToQueue (COPA_SHMEM_QUEUE * pcopaCommandQueue,
                                                                                         unsigned int * copBuffer,
                                                                                         unsigned int bytesToWrite);
static int copa_ReadFromQueue (COPA_SHMEM_QUEUE * pcopaEventQueue,
                                                                                         unsigned int * copBuffer,
                                                                                         unsigned int copBufferSize);
static int copa_SendScciCmd (unsigned int *copBuffer, unsigned int bytesToWrite);
static int copa_GetCabinetId (void);
static int copa_WaitForCond (unsigned int *pVar,
                                                                                         unsigned int Cond,
                                                                                         int MaxLoops,
                                                                                         int uSecBusyWait,
                                                                                         int ModPeriod,
                                                                                         int DelayClock);
static void copa_delay (int clocks);
static void copa_delay_busy (int clocks);
typedef void (*PDELAY) (int);
static PDELAY p_copa_delay = copa_delay;
                int copa_lock (int control_code);
                int copa_unlock (int control_code);
static unsigned char copa_PowerOffInhibitState = (unsigned char) 0;
static unsigned char copa_IRQ_disabled = (unsigned char) 0;
static unsigned char copa_CommArrea_reinitialized = (unsigned char) 0;
static unsigned char copa_lockFunc_successful = (unsigned char) 0;
static unsigned char copa_unlockFunc_successful = (unsigned char) 0;
DRIVER_SYMBOL_IMPORT(pm_power_off_t ,ipmi_PowerOff);
DRIVER_SYMBOL_IMPORT(pm_power_off_t*,ipmi_PowerOff_saved);
DRIVER_SYMBOL_IMPORT(pm_power_off_t ,smbus_PowerOff);
DRIVER_SYMBOL_IMPORT(pm_power_off_t*,smbus_PowerOff_saved);
DRIVER_SYMBOL_EXPORT(copa_lock);
DRIVER_SYMBOL_EXPORT(copa_unlock);
DRIVER_SYMBOL_EXPORT(copa_PowerOff);
DRIVER_SYMBOL_EXPORT(copa_PowerOff_saved);
static int copa_open(struct inode *inode, struct file *file)
{
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_open: (%p,%p)\n", inode, file);
        if(deviceOpen) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_open: device is busy\n");
                return -EBUSY;
        }
        deviceOpen++;
        DRIVER_MOD_INC_USE_COUNT;
        return SUCCESS;
}
static int copa_release(struct inode *inode, struct file *file)
{
        deviceOpen--;
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_release: (%p,%p)\n", inode, file);
        DRIVER_MOD_DEC_USE_COUNT;
        return SUCCESS;
}
static void copa_vma_open(struct vm_area_struct *area)
{
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_vma_open\n");
        DRIVER_MOD_INC_USE_COUNT;
}
static void copa_vma_close(struct vm_area_struct *area)
{
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_vma_close\n");
        DRIVER_MOD_DEC_USE_COUNT;
}
static struct vm_operations_struct copa_vm_ops = {
        copa_vma_open,
        copa_vma_close,
};
static int copa_mmap(struct file *file, struct vm_area_struct *vma)
{
        int err;
        unsigned long virt_add = vma->vm_start;
        unsigned long vsize = vma->vm_end-vma->vm_start;
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_mmap virt=0x%lx phys=0x%lx(0x%lx) size=0x%lx(0x%lx)\n", virt_add, phys_PCI_REG2_Address, (long unsigned int)vma->vm_pgoff, COPA_PCI_REG2_LEN, vsize);
        if (vsize > COPA_PCI_REG2_LEN) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_mmap: vsize > COPA_PCI_REG2_LEN\n");
                return -EINVAL;
        }
        err = DRIVER_REMAP_RANGE(vma, virt_add, phys_PCI_REG2_Address, vsize, vma->vm_page_prot);
        if (err) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_mmap: remap_page_range failed: %d\n", err);
                return -EAGAIN;
        }
        if (vma->vm_ops) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_mmap: vma->vm_ops != NULL\n");
                return -EINVAL;
        }
        vma->vm_ops = &copa_vm_ops;
        DRIVER_MOD_INC_USE_COUNT;
        return SUCCESS;
}
static irqreturn_t copa_irq_handler(int irq,void *dev_id,struct pt_regs *regs)
{
        if ((pDoorbellRegister) && (*pDoorbellRegister & (1<<24)))
        {
                *pDoorbellRegister |= (1<<24);
                wake_up(&WaitQ);
                copa_interrupt_received=1;
                return IRQ_HANDLED;
        }
        return IRQ_NONE;
}
long copa_ioctl_compat( struct file *file,
                                                           unsigned int cmd,
                                                           unsigned long arg )
{
        return (long)copa_ioctl(NULL, file, cmd, arg);
}
static int copa_ioctl( struct inode *inode,
                                                struct file *file,
                                                unsigned int cmd,
                                                unsigned long arg )
{
        unsigned long flags = 0;
        unsigned long copyrc = 0;
        if (inode != NULL && file != NULL) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ==> external call to copa_ioctl() via ioctl() (cmd = 0x%08X)\n", cmd);
        } else {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: --> internal call to copa_ioctl() (might be from inside the kernel (cmd = 0x%08X)\n", cmd);
        }
        if (_IOC_TYPE(cmd) != 'r') {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ERROR: CmdType != magic (0x%02X 0x%02X) !!!\n", _IOC_TYPE(cmd), 'r');
                return -EINVAL;
        }
        if (_IOC_NR(cmd) > 8) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ERROR: CmdNumber> MaxNumber (0x%02X 0x%02X) !!! \n", _IOC_NR(cmd), 8);
                return -EINVAL;
        }
        switch(cmd)
        {
                case _IO('r', 0):
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: COPA_IOC_WAIT_FOR_IRQ received\n");
                        DRIVER_SAVE_FLAGS(flags);
                        DRIVER_DISABLE_IRQ();
                        if (copa_interrupt_received )
                        {
                        }
                        else
                        {
                                DRIVER_FLAGS_RESTORE(flags);
                                interruptible_sleep_on(&WaitQ);
                                DRIVER_SAVE_FLAGS(flags);
                                DRIVER_DISABLE_IRQ();
                        }
                        copa_interrupt_received=0;
                        DRIVER_FLAGS_RESTORE(flags);
                        break;
                case _IO('r', 1):
                        if (pDoorbellRegister) {
                                if (*pDoorbellRegister & (1<<0))
                                {
                                        *pDoorbellRegister |= (1<<8);
                                }
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: COPA_IOC_GENERATE_IRQ pDoorbellRegister 0x%016lX data 0x%08X\n", (long)pDoorbellRegister,*pDoorbellRegister);
                        } else {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ERROR: COPA_IOC_GENERATE_IRQ pDoorbellRegister NOT valid !!!\n");
                                return -EINVAL;
                        }
                        break;
                case _IO('r', 2):
                        if ((pDoorbellRegister) && (*pProperties & (1<<1)))
                        {
                                Properties = *pProperties;
                                Properties |= (1<<2);
                                *pProperties=Properties;
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: COPA_IOC_ENABLE_RECEIVE_IRQ Properties 0x%x\n",*pProperties);
                                *pDoorbellRegister |= (1<<16);
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: COPA_IOC_ENABLE_RECEIVE_IRQ pDoorbellRegister 0x%016lX data 0x%08x\n",(long)pDoorbellRegister,*pDoorbellRegister);
                        } else {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ERROR: COPA_IOC_ENABLE_RECEIVE_IRQ pDoorbellRegister (0x%016lX) or its value (0x%08X) NOT valid !!!\n", (long)pDoorbellRegister,*pDoorbellRegister);
                                return -EINVAL;
                        }
                        break;
                case _IO('r', 3):
                        if ((pDoorbellRegister) && (*pProperties & (1<<1)))
                        {
                                Properties = *pProperties;
                                Properties &= ~(1<<2);
                                *pProperties=Properties;
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: COPA_IOC_DISABLE_RECEIVE_IRQ Properties 0x%x\n",*pProperties);
                                *pDoorbellRegister &= ~(1<<16);
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: COPA_IOC_DISABLE_RECEIVE_IRQ pDoorbellRegister 0x%016lX data 0x%08x\n",(long)pDoorbellRegister,*pDoorbellRegister);
                                copa_interrupt_received=0;
                        } else {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ERROR: COPA_IOC_DISABLE_RECEIVE_IRQ pDoorbellRegister (0x%016lX) or its value (0x%08X) NOT valid !!!\n", (long)pDoorbellRegister,*pDoorbellRegister);
                                return -EINVAL;
                        }
                        break;
                case _IO('r', 4):
                        if (pDoorbellRegister)
                        {
                                copa_interrupt_received=0;
                                *pDoorbellRegister |= (1<<24);
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: COPA_IOC_RESET_RECEIVE_IRQ pDoorbellRegister 0x%016lX data 0x%08x\n",(long)pDoorbellRegister,*pDoorbellRegister);
                        } else {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ERROR: COPA_IOC_RESET_RECEIVE_IRQ pDoorbellRegister (0x%016lX) or its value (0x%08X) NOT valid !!!\n", (long)pDoorbellRegister,*pDoorbellRegister);
                                return -EINVAL;
                        }
                        break;
                case _IO('r', 5):
                        {
                                IOCTL_STRUCT_PCI_INFO data;
                                if (copaf1Dev == NULL)
                                {
                                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ERROR: COPA_IOC_GET_PCI_INFO copaf1Dev is NULL\n");
                                        return -ENODEV;
                                }
                                copyrc = copy_from_user(&data, (IOCTL_STRUCT_PCI_INFO *)arg, sizeof(IOCTL_STRUCT_PCI_INFO));
                                data.BusNumber = copaf1Dev->bus->number;
                                data.DeviceNumber = PCI_SLOT(copaf1Dev->devfn);
                                data.FunctionNumber = PCI_FUNC(copaf1Dev->devfn);
                                data.VendorId = copaf1Dev->vendor;
                                data.DeviceId = copaf1Dev->device;
                                data.SubVendorId = copaf1Dev->subsystem_vendor;
                                data.SubDeviceId = copaf1Dev->subsystem_device;
                                copyrc = copy_to_user((IOCTL_STRUCT_PCI_INFO *)arg, &data, sizeof(IOCTL_STRUCT_PCI_INFO));
                        }
                        break;
                case _IO('r', 6):
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: COPA_LOCK command entered\n");
                        if (copaDebug >= 255) {
                                if (copa_lock (1) < 0 ) {
                                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ERROR: COPA_LOCK command failed !!!\n");
                                        return -EINVAL;
                                }
                        } else {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ioctl-cmd COPA_IOC_COPA_LOCK (0x%08X) not allowd\n", cmd);
                                return -EINVAL;
                        }
                        break;
                case _IO('r', 7):
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: COPA_UNLOCK command entered\n");
                        if (copaDebug >= 255) {
                                if (copa_unlock (1) < 0 ) {
                                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ERROR: COPA_UNLOCK command failed !!!\n");
                                        return -EINVAL;
                                }
                        } else {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ioctl-cmd COPA_IOC_COPA_UNLOCK (0x%08X) not allowd\n", cmd);
                                return -EINVAL;
                        }
                        break;
                default:
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ioctl: ioctl-cmd=%x is NOT valid !!!\n", cmd);
                        return -EINVAL;
        }
        return SUCCESS;
}
static struct file_operations copa_fops =
{
        DRIVER_FOPS
};
static int copa_DetermineEnvironment(void)
{
        char *pointer = NULL;
        if (copaArchMode == 0x00000000) {
                copaArchMode |= DRIVER_REMAP_RANGE_INTF;
                copaArchMode |= DRIVER_KERNEL_MODE;
                copaArchMode |= DRIVER_POWEROFF_ROUTINE;
                copaArchMode |= DRIVER_MODULE_INTERACTION;
                copaArchMode |= DRIVER_IOCTL32_CONV;
                if (sizeof(pointer) == 4) {
                        copaArchMode |= 0x10000000;
                } else if (sizeof(pointer) == 8) {
                        copaArchMode |= DRIVER_64BIT_MODE;
                } else {
                        if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: unknown XX-Bit mode\n");
                        return -1;
                }
        } else {
                if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: has been determined by insmod\n");
        }
        if ( copaArchMode & 0x10000000 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: IA32 (x86) mode is active\n");
        if ( copaArchMode & 0x40000000 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: IA64 mode is active\n");
        if ( copaArchMode & 0x20000000 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: __x86_64__ mode    is active\n");
        if ( copaArchMode & 0x01000000 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: KERNEL 2.4    mode is active\n");
        if ( copaArchMode & 0x02000000 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: KERNEL 2.6    mode is active\n");
        if ( copaArchMode & 0x04000000 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: KERNEL 2.6.16 mode is active\n");
        if ( copaArchMode & 0x00000100 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: OLD_REMAP_INTF     is active\n");
        if ( copaArchMode & 0x00000200 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: NEW_REMAP_INTF     is active\n");
        if ( copaArchMode & 0x00000400 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: PFN_REMAP_INTF     is active\n");
        if ( copaArchMode & 0x00000010 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: IOCTL32_CONVERSION is active\n");
        if ( copaArchMode & 0x00000020 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: IOCTL32_COMPAT     is active\n");
        if ( copaArchMode & 0x00000001 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: OS pm_power_off    is used\n");
        if ( copaArchMode & 0x00000002 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: My copa_pm_power_off is used\n");
        if ( copaArchMode & 0x00000004 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: inter_module_xxx() functions are used\n");
        if ( copaArchMode & 0x00000008 ) if (copaDebug) printk(KERN_DEBUG "copa :" "Environment: symbol_get/put()   functions are used\n");
        return 0;
}
int init_module(void)
{
        int ret = 0;
        int result = 0;
        if ((ret = copa_DetermineEnvironment()) < 0) {
                printk(KERN_ERR "copa : " "init_module: unable to determine OS/HW environment (return = %d)\n", ret);
                return -ENODEV;
        }
        DRIVER_PCI_PRESENT(result);
        if (result == 0) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: ERROR: pcibios  is NOT present\n");
                return -ENODEV;
        }
        copaf1Dev = pci_find_device(SNI_VENDOR_ID, COPA_F1_DEVICE_ID, copaf1Dev);
        if (copaf1Dev == NULL)
        {
                if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: Copernicus (Agilent) NOT detected !!!\n");
                return -ENODEV;
        }
        if (copaf1Dev->subsystem_device == PCI_SUBDEVID_RSB) {
                IsRSB = 1;
                if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: Copernicus (Agilent)  as RSB detected !!!\n");
        } else {
                IsRSB = 0;
                if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: Copernicus (Agilent) onboard detected !!!\n");
        }
        if (copaDebug) printk(KERN_DEBUG "copa :" "PCI-Info:\n" "      BusNumber          = %d\n" "      DeviceNumber       = %d\n" "      FunctionNumber     = %d\n" "      IRQNumber          = %d\n" "      VendorId           = 0x%04X\n" "      DeviceId           = 0x%04X\n" "      SubVendorId        = 0x%04X\n" "      SubDeviceId        = 0x%04X\n", copaf1Dev->bus->number, PCI_SLOT(copaf1Dev->devfn), PCI_FUNC(copaf1Dev->devfn), copaf1Dev->irq, copaf1Dev->vendor, copaf1Dev->device, copaf1Dev->subsystem_vendor, copaf1Dev->subsystem_device);
        phys_PCI_REG0_Address = pci_resource_start(copaf1Dev, 0) & ~((unsigned long)0x0F);
        phys_PCI_REG1_Address = pci_resource_start(copaf1Dev, 1) & ~((unsigned long)0x0F);
        phys_PCI_REG2_Address = pci_resource_start(copaf1Dev, 2) & ~((unsigned long)0x0F);
        if (copaDebug) printk(KERN_DEBUG "copa :" "phys Address PCI REG0: 0x%016lX\n", phys_PCI_REG0_Address);
        if (copaDebug) printk(KERN_DEBUG "copa :" "phys Address PCI REG1: 0x%016lX\n", phys_PCI_REG1_Address);
        if (copaDebug) printk(KERN_DEBUG "copa :" "phys Address PCI REG2: 0x%016lX\n", phys_PCI_REG2_Address);
        pvirt_PCI_REG0_Address = ioremap(phys_PCI_REG0_Address, COPA_PCI_REG0_LEN);
        if (pvirt_PCI_REG0_Address)
        {
                pDoorbellRegister = (unsigned int *)(pvirt_PCI_REG0_Address + 0x1C);
                if (copaDebug) printk(KERN_DEBUG "copa :" "pDoorbellRegister:  0x%016lX data 0x%08X\n",(long)pDoorbellRegister,*pDoorbellRegister);
        }
        pvirt_PCI_REG2_Address = ioremap_nocache(phys_PCI_REG2_Address,COPA_PCI_REG2_LEN);
        if (pvirt_PCI_REG2_Address)
        {
                pcopaTopHdr = (COPA_SHMEM_TOP_HEADER *) pvirt_PCI_REG2_Address;
                pProperties = &(pcopaTopHdr->Properties);
                if (copaDebug) printk(KERN_DEBUG "copa :" "pProperties:        0x%016lX data 0x%08X\n",(long)pProperties,*pProperties);
                Properties=*pProperties;
                Properties |= 0x4;
                *pProperties = Properties;
                if (copaDebug) printk(KERN_DEBUG "copa :" "pProperties:        0x%016lX data 0x%08X\n",(long)pProperties,*pProperties);
        }
        pcopaCommandQueue = copa_FindShmemQueue(pcopaTopHdr, 0x0021);
        pcopaEventQueue = copa_FindShmemQueue(pcopaTopHdr, 0x0022);
        if (pcopaCommandQueue == NULL) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: ERROR: Command Queue NOT found !!!\n");
        } else {
                if (copaDebug) printk(KERN_DEBUG "copa :" "pcopaCommandQueue:  0x%016lX type = 0x%08X, size = 0x%08X \n", (long)pcopaCommandQueue, pcopaCommandQueue->Type, pcopaCommandQueue->Size);
        }
        if (pcopaEventQueue == NULL) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: ERROR: Event Queue NOT found !!!\n");
        } else {
                if (copaDebug) printk(KERN_DEBUG "copa :" "pcopaEventQueue:    0x%016lX type = 0x%08X, size = 0x%08X \n", (long)pcopaEventQueue, pcopaEventQueue->Type, pcopaEventQueue->Size);
        }
        if (copaDebug) printk(KERN_DEBUG "copa :" "V1_SC_COMMAND_HDR_SIZE 0x%04X (%d)\n", (int)(sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA)), (int)(sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA)));
        if (copaf1Dev->irq != 0)
        {
                result=request_irq(copaf1Dev->irq,(void *) copa_irq_handler,SA_SHIRQ | SA_INTERRUPT,COPA_DEV,copaf1Dev);
                if (result < 0)
                {
                        if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: Bad IRQ number or handler\n");
                        return result;
                }
                if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: copa IRQ-Handler registered\n");
        }
        DRIVER_SET_OWNER;
        if((ret = register_chrdev(copa_major, COPA_DEV, &copa_fops)) < 0) {
                printk(KERN_ERR "init_module: copa unable to get major %d return = %d\n", copa_major, ret);
                return -EIO;
        }
        if (ret > 0) copa_major = ret;
        if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: major device number = %d (0x%08x)\n",copa_major, copa_major);
        copa_register_PowerOff_routine();
        DRIVER_INTER_MODULE_REGISTER(copa_lock);
        DRIVER_INTER_MODULE_REGISTER(copa_unlock);
        DRIVER_INTER_MODULE_REGISTER(copa_PowerOff);
        DRIVER_INTER_MODULE_REGISTER_P(copa_PowerOff_saved);
        if ( copaArchMode & 0x00000004 ) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: copa_lock           function (inter_module) registered\n");
                if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: copa_unlock         function (inter_module) registered\n");
                if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: copa_PowerOff       function (inter_module) registered\n");
                if (copaDebug) printk(KERN_DEBUG "copa :" "init_module: copa_PowerOff_saved function (inter_module) registered\n");
        }
        return SUCCESS;
}
void cleanup_module(void)
{
        int err;
        if (copaDebug) printk(KERN_DEBUG "copa :" "cleanup_module: ENTER\n");
        wake_up(&WaitQ);
        if (copaf1Dev->irq != 0)
                free_irq(copaf1Dev->irq,copaf1Dev);
        DRIVER_INTER_MODULE_UNREGISTER(copa_lock);
        DRIVER_INTER_MODULE_UNREGISTER(copa_unlock);
        DRIVER_INTER_MODULE_UNREGISTER(copa_PowerOff);
        DRIVER_INTER_MODULE_UNREGISTER(copa_PowerOff_saved);
        if ( copaArchMode & 0x00000004 ) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "cleanup_module: copa_lock           function (inter_module) unregistered\n");
                if (copaDebug) printk(KERN_DEBUG "copa :" "cleanup_module: copa_unlock         function (inter_module) unregistered\n");
                if (copaDebug) printk(KERN_DEBUG "copa :" "cleanup_module: copa_PowerOff       function (inter_module) unregistered\n");
                if (copaDebug) printk(KERN_DEBUG "copa :" "cleanup_module: copa_PowerOff_saved function (inter_module) unregistered\n");
        }
        copa_unregister_PowerOff_routine();
        err = unregister_chrdev(copa_major, COPA_DEV);
        if (err < 0) {
                printk(KERN_ERR "copa: cleanup_module: ERROR: unregister_chrdev(%i) failed! return = %d\n", copa_major, err);
        }
        copaf1Dev = NULL;
        copaf0Dev = NULL;
        if (copaDebug) printk(KERN_DEBUG "copa :" "cleanup_module: LEAVE\n");
}
static void copa_register_PowerOff_routine(void)
{
        pm_power_off_t tmp_POff_ipmi = NULL;
        pm_power_off_t tmp_POff_smbus = NULL;
        pm_power_off_t *tmp_POff_ipmi_sav = NULL;
        pm_power_off_t *tmp_POff_smbus_sav = NULL;
        unsigned int tmp_copa_poff_prio = 1;
        if (copaPowerOff <= 0) {
                return;
        }
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: OS   PowerOff routine = 0x%016lX\n", (long) PM_POWER_OFF);
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: COPA PowerOff routine = 0x%016lX\n", (long) copa_PowerOff);
        tmp_POff_ipmi = (pm_power_off_t) DRIVER_INTER_MODULE_GET(ipmi_PowerOff);
        tmp_POff_ipmi_sav = (pm_power_off_t *) DRIVER_INTER_MODULE_GET(ipmi_PowerOff_saved);
        tmp_POff_smbus = (pm_power_off_t) DRIVER_INTER_MODULE_GET(smbus_PowerOff);
        tmp_POff_smbus_sav = (pm_power_off_t *) DRIVER_INTER_MODULE_GET(smbus_PowerOff_saved);
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: tmp_POff_ipmi         = 0x%016lX\n", (long) tmp_POff_ipmi);
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: tmp_POff_ipmi_sav     = 0x%016lX\n", (long) tmp_POff_ipmi_sav);
        if (tmp_POff_ipmi_sav != NULL)
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: *tmp_POff_ipmi_sav    = 0x%016lX\n", (long) *tmp_POff_ipmi_sav);
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: tmp_POff_smbus        = 0x%016lX\n", (long) tmp_POff_smbus);
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: tmp_POff_smbus_sav    = 0x%016lX\n", (long) tmp_POff_smbus_sav);
        if (tmp_POff_smbus_sav != NULL)
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: *tmp_POff_smbus_sav   = 0x%016lX\n", (long) *tmp_POff_smbus_sav);
        if (PM_POWER_OFF == NULL) {
                 copa_PowerOff_saved = NULL;
                 PM_POWER_OFF = copa_PowerOff;
                 copa_OS_Poff_routine_changed = 1;
                 if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: COPA PowerOff routine inserted \n");
                 if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: PM_POWER_OFF        = 0x%016lX\n", (long) PM_POWER_OFF);
                 if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: copa_PowerOff_saved = 0x%016lX\n", (long) copa_PowerOff_saved);
        } else if (PM_POWER_OFF == tmp_POff_ipmi) {
                if (tmp_copa_poff_prio > 2) {
                        copa_OS_Poff_routine_changed = 0;
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: IPMI PowerOff routine has already been inserted -> Do nothing!\n");
                } else {
                         copa_PowerOff_saved = *tmp_POff_ipmi_sav;
                         PM_POWER_OFF = copa_PowerOff;
                         copa_OS_Poff_routine_changed = 1;
                         if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: IPMI PowerOff routine replaced by COPA routine\n");
                         if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: PM_POWER_OFF        = 0x%016lX\n", (long) PM_POWER_OFF);
                         if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: copa_PowerOff_saved = 0x%016lX\n", (long) copa_PowerOff_saved);
                }
        } else if (PM_POWER_OFF == tmp_POff_smbus) {
                if (tmp_copa_poff_prio > 3) {
                        copa_OS_Poff_routine_changed = 0;
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: SMBUS PowerOff routine has already been inserted -> Do nothing!\n");
                } else {
                         copa_PowerOff_saved = *tmp_POff_smbus_sav;
                         PM_POWER_OFF = copa_PowerOff;
                         copa_OS_Poff_routine_changed = 1;
                         if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: SMBUS PowerOff routine replaced by COPA routine\n");
                         if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: PM_POWER_OFF        = 0x%016lX\n", (long) PM_POWER_OFF);
                         if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: copa_PowerOff_saved = 0x%016lX\n", (long) copa_PowerOff_saved);
                }
        } else {
                 copa_PowerOff_saved = PM_POWER_OFF;
                 PM_POWER_OFF = copa_PowerOff;
                 copa_OS_Poff_routine_changed = 1;
                 if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: OS PowerOff routine replaced by COPA Power Off routine!\n");
                 if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: PM_POWER_OFF        = 0x%016lX\n", (long) PM_POWER_OFF);
                 if (copaDebug) printk(KERN_DEBUG "copa :" "copa_register_PowerOff_routine: copa_PowerOff_saved = 0x%016lX\n", (long) copa_PowerOff_saved);
        }
        if (tmp_POff_ipmi) DRIVER_INTER_MODULE_PUT(ipmi_PowerOff);
        if (tmp_POff_ipmi_sav) DRIVER_INTER_MODULE_PUT(ipmi_PowerOff_saved);
        if (tmp_POff_smbus) DRIVER_INTER_MODULE_PUT(smbus_PowerOff);
        if (tmp_POff_smbus_sav) DRIVER_INTER_MODULE_PUT(smbus_PowerOff_saved);
}
static void copa_unregister_PowerOff_routine(void)
{
        if (copaPowerOff <= 0) {
                return;
        }
        if (copa_OS_Poff_routine_changed && (PM_POWER_OFF == copa_PowerOff)) {
                 PM_POWER_OFF = copa_PowerOff_saved;
                 copa_PowerOff_saved = NULL;
                 copa_OS_Poff_routine_changed = 0;
                 if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unregister_PowerOff_routine: COPA Power Off routine replaced by original routine !\n");
                 if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unregister_PowerOff_routine: PM_POWER_OFF        = 0x%016lX\n", (long) PM_POWER_OFF);
                 if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unregister_PowerOff_routine: copa_PowerOff_saved = 0x%016lX\n", (long) copa_PowerOff_saved);
        }
}
void copa_PowerOff (void)
{
        printk(KERN_INFO "copa: POWER OFF BY COPA !\n");
        if (copa_PowerOff_saved != NULL) {
                (copa_PowerOff_saved)();
        }
        if (copa_DisableIRQsFromCopa() < 0) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_PowerOff: WARNING: Disabling IRQs from CopA failed !\n");
        }
        if (copa_ResetAllShmemQueues(pcopaTopHdr) < 0) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_PowerOff: ERROR: CopA communication area reinitializing failed !!!\n");
        }
        memset(pcopaCommandHeader, 0, sizeof(copaCommand));
        pcopaCommandHeader->CmdStatus = (V1_CMD_STATUS) 0x16;
        pcopaCommandHeader->OpCode = 0x0112;
        pcopaCommandHeader->CabinetNr = cabId;
        pcopaCommandHeader->DataLength = sizeof(unsigned char);
        pcopaCommandHeader->CmdData.AsByte = 0x00;
        if(copa_SendScciCmd(copaCommand, ((sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA)) + pcopaCommandHeader->DataLength)) < 0 ) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_PowerOff: ERROR: Power Off failed (status = 0x%08X)!!!\n", pcopaCommandHeader->CmdStatus);
        }
}
static COPA_SHMEM_QUEUE * copa_FindShmemQueue(COPA_SHMEM_TOP_HEADER * pcopaTopHdr, int RequestType)
{
        int len;
        COPA_SHMEM_ANY_HEADER *pAnyHeader;
        pAnyHeader = (COPA_SHMEM_ANY_HEADER *)pcopaTopHdr;
        while (pAnyHeader->Type != 0x0001)
        {
                if ((pAnyHeader->Type < 0x0020) || (pAnyHeader->Type > 0x002F)) {
                        return NULL;
                }
                if (pAnyHeader->Type == RequestType)
                {
                        return (COPA_SHMEM_QUEUE *)pAnyHeader;
                }
                len = pAnyHeader->Length;
                pAnyHeader = (COPA_SHMEM_ANY_HEADER *)((char *)pAnyHeader + len);
        }
        return NULL;
}
static int copa_ResetAllShmemQueues(COPA_SHMEM_TOP_HEADER * pcopaTopHdr)
{
        pcopaTopHdr->Signature.AsDWord = 0;
        if (copa_WaitForShmemRestoring (pcopaTopHdr) < 0) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "ResetQueues: ERROR: TIMEOUT COPA communication area NOT restored !!!\n");
                return -1;
        }
        if (0x0020 != pcopaTopHdr->Type) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "ResetQueues: ERROR: Top Header Type NOT valid !!!\n");
                return -1;
        }
        if (0x00494E53 != pcopaTopHdr->Signature.AsDWord) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "ResetQueues: ERROR: Top Header Signature NOT valid !!!\n");
                return -1;
        }
        if ((pcopaTopHdr->Version < 0x0104) || (pcopaTopHdr->Version > 0x01FF)) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "ResetQueues: ERROR: Top Header Version NOT valid !!!\n");
                return -1;
        }
        if (pcopaTopHdr->Length >= pcopaTopHdr->SharedMemLength) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "ResetQueues: ERROR: Top Header shared memory size NOT valid !!!\n");
                return -1;
        }
        pcopaCommandQueue = copa_FindShmemQueue(pcopaTopHdr, 0x0021);
        pcopaEventQueue = copa_FindShmemQueue(pcopaTopHdr, 0x0022);
        if ((pcopaCommandQueue == NULL) || (pcopaEventQueue == NULL)) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "ResetQueues: ERROR: Can't find the COPA communication queues !!!\n");
                if (copaDebug) printk(KERN_DEBUG "copa :" "ResetQueues: pcopaCommandQueue = 0x%016lX\n", (long)pcopaCommandQueue);
                if (copaDebug) printk(KERN_DEBUG "copa :" "ResetQueues: pcopaEventQueue   = 0x%016lX\n", (long)pcopaEventQueue);
                return -1;
        }
        if ((pcopaCommandQueue->Count != 0) || (pcopaEventQueue->Count != 0)) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "ResetQueues: ERROR: Queues NOT empty !!! (CmdCnt=%d EvtCnt=%d\n", pcopaCommandQueue->Count, pcopaEventQueue->Count);
                return -1;
        }
        copa_CommArrea_reinitialized = (unsigned char) 1;
        if (copaDebug) printk(KERN_DEBUG "copa :" "ResetQueues: COPA communication area has been restored !!!\n");
        return 0;
}
static void copa_delay (int clocks)
{
        set_current_state(TASK_UNINTERRUPTIBLE);
        schedule_timeout(clocks);
}
static void copa_delay_busy (int clocks)
{
        int i, j;
        if (clocks == 0) clocks = 1;
        for (j=0; j<clocks; j++) {
                for (i=0; i<200; i++) udelay (50);
        }
}
static int copa_WaitForCond (unsigned int *pVar,
                                                         unsigned int Cond,
                                                         int MaxLoops,
                                                         int uSecBusyWait,
                                                         int ModPeriod,
                                                         int DelayClock)
{
        int dl;
        int mod;
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_WaitForCond: entered for max. %d loops (%d %d %d)\n", MaxLoops, uSecBusyWait, ModPeriod, DelayClock);
        for (dl=1; dl <= MaxLoops; dl ++) {
                if ( *pVar == Cond) {
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_WaitForCond: OK, after %d delay loops left\n",dl);
                        udelay (50);
                        return 0;
                }
                mod = dl % ModPeriod;
                if (mod == 0) {
                        p_copa_delay(DelayClock);
                } else {
                        udelay(uSecBusyWait);
                }
        }
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_WaitForCond: NOK, TIMEOUT after %d delay loops left\n",dl);
        return -1;
}
static int copa_WaitForShmemRestoring (COPA_SHMEM_TOP_HEADER * pcopaTopHdr)
{
        int result;
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_WaitForShmemRestoring: entered\n");
        result = copa_WaitForCond (&(pcopaTopHdr->Signature.AsDWord),
                                                                 0x00494E53,
                                                                 10000,
                                                                 100,
                                                                 16,
                                                                 1);
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_WaitForShmemRestoring: returns = %d\n", result);
        return result;
}
static int copa_WriteToQueue(COPA_SHMEM_QUEUE * pcopaCommandQueue, unsigned int *copBuffer, unsigned int bytesToWrite)
{
        unsigned int count;
        unsigned int queueSize;
        unsigned int writePos;
        unsigned int bytesWritten;
        unsigned int dwordsWritten;
        int maxWait = 0;
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_WriteToQueue: entered with %d Bytes to Write\n", bytesToWrite);
        if (!copBuffer || (bytesToWrite < (sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA)))) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_WriteToQueue: ERROR: Invalid parameter\n");
                return -1;
        }
        pcopaCommandQueue->DrvAccess = 1;
        while (pcopaCommandQueue->SpAccess)
        {
                if (++maxWait > 100) {
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_WriteToQueue: WARNING: TIMEOUT on Wait for SpAccess\n");
                        break;
                }
                p_copa_delay(1);
        }
        count = pcopaCommandQueue->Count;
        queueSize = pcopaCommandQueue->Size;
        if ((count + bytesToWrite) > queueSize)
        {
                pcopaCommandQueue->DrvAccess = 0;
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_WriteToQueue: ERROR: NOT enough Space on Queue (%d %d) !!!\n", count + bytesToWrite, queueSize);
                return -1;
        }
        if (((V1_SC_COMMAND *)copBuffer)->DataLength > (bytesToWrite - (sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA))))
        {
                ((V1_SC_COMMAND *)copBuffer)->DataLength = bytesToWrite - (sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA));
        }
        bytesWritten = 0;
        dwordsWritten = 0;
        writePos = pcopaCommandQueue->WritePos;
        while (bytesWritten < bytesToWrite)
        {
                if ((bytesWritten >= (sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA))) &&
                        (bytesWritten > ((sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA)) + ((V1_SC_COMMAND *)copBuffer)->DataLength))) break;
                *((unsigned int *)&pcopaCommandQueue->Data[writePos]) = copBuffer[dwordsWritten++];
                bytesWritten += sizeof(unsigned int);
                writePos += sizeof(unsigned int);
                if (writePos >= queueSize) writePos = 0;
        }
        pcopaCommandQueue->WritePos = writePos;
        pcopaCommandQueue->Count += bytesWritten;
        pcopaCommandQueue->DrvAccess = 0;
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_WriteToQueue: %d Bytes written\n", bytesWritten);
        return bytesWritten;
}
static int copa_ReadFromQueue(COPA_SHMEM_QUEUE * pcopaEventQueue, unsigned int *copBuffer, unsigned int copBufferSize)
{
        unsigned int count;
        unsigned int queueSize;
        unsigned int readPos;
        unsigned int bytesRead;
        unsigned int dwordsRead;
        int maxWait = 0;
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ReadFromQueue: entered with max. %d Bytes to Read\n", copBufferSize);
        if (!copBuffer || (copBufferSize < (sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA)))) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ReadFromQueue: ERROR: Invalid parameter\n");
                return -1;
        }
        pcopaEventQueue->DrvAccess = 1;
        while (pcopaEventQueue->SpAccess)
        {
                if (++maxWait > 100) {
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ReadFromQueue: WARNING: TIMEOUT on Wait for SpAccess\n");
                        break;
                }
                p_copa_delay(1);
        }
        count = pcopaEventQueue->Count;
        queueSize = pcopaEventQueue->Size;
        if (count >= queueSize)
        {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ReadFromQueue: ERROR: Count NOT OK (%d %d) !!!\n", count, queueSize);
                pcopaEventQueue->DrvAccess = 0;
                return -1;
        }
        if (count < (sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA)))
        {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ReadFromQueue: Nothing to Read (%d %d) !!!\n", count, queueSize);
                pcopaEventQueue->DrvAccess = 0;
                return 0;
        }
        bytesRead = 0;
        dwordsRead = 0;
        readPos = pcopaEventQueue->ReadPos;
        while (bytesRead < count)
        {
                if ((bytesRead >= (sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA))) &&
                        (bytesRead > ((sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA)) + ((V1_SC_COMMAND *)copBuffer)->DataLength))) break;
                if (bytesRead <= (copBufferSize - sizeof(unsigned int)))
                {
                        copBuffer[dwordsRead++] = *((unsigned int *)&pcopaEventQueue->Data[readPos]);
                }
                bytesRead += sizeof(unsigned int);
                readPos += sizeof(unsigned int);
                if (readPos >= queueSize) readPos = 0;
        }
        pcopaEventQueue->ReadPos = readPos;
        pcopaEventQueue->Count -= bytesRead;
        pcopaEventQueue->DrvAccess = 0;
        dwordsRead *= sizeof(unsigned int);
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_ReadFromQueue: %d Bytes (dwords = %d) read\n", bytesRead, dwordsRead);
        return dwordsRead;
}
static int copa_SendScciCmd(unsigned int *copBuffer, unsigned int bytesToWrite)
{
        int success = 0;
        int maxWait = 0;
        int result = 0;
        if (copa_WriteToQueue(pcopaCommandQueue, copBuffer, bytesToWrite) <= 0) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_SendScciCmd: WriteToQueue failed !!!\n");
                success = -EINVAL;
        } else {
                if (copa_ioctl(NULL, NULL, _IO('r', 1), 0) < 0) {
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_SendScciCmd: generate interrupt failed !!!\n");
                        success = -EINVAL;
                }
                maxWait = 0;
                while ((result = copa_ReadFromQueue(pcopaEventQueue, copBuffer, sizeof copaCommand)) == 0)
                {
                        if (++maxWait > 50) break;
                        p_copa_delay(1);
                }
                if (result <= 0) {
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_SendScciCmd: ReadFromQueue failed (maxWait = %d)!!!\n", maxWait);
                        success = -EINVAL;
                }
                if (pcopaCommandHeader->CmdStatus != (V1_CMD_STATUS) 0x00) {
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_SendScciCmd: Command NOT successful status = 0x%08X!!!\n", pcopaCommandHeader->CmdStatus);
                        success = -EINVAL;
                }
        }
        return success;
}
static int copa_DisableIRQsFromCopa (void)
{
        if (copa_ioctl(NULL, NULL, _IO('r', 3), 0) < 0) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "DisableIRQ: Disabling receive interrupt from CopA failed !\n");
                return -1;
        }
        if (copa_ioctl(NULL, NULL, _IO('r', 4), 0) < 0) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "DisableIRQ: Reseting  receive interrupt from CopA failed !\n");
                return -1;
        }
        copa_IRQ_disabled = (unsigned char) 1;
        return 0;
}
static int copa_GetCabinetId (void)
{
        memset(pcopaCommandHeader, 0, sizeof(copaCommand));
        pcopaCommandHeader->CmdStatus = (V1_CMD_STATUS) 0x16;
        pcopaCommandHeader->OpCode = 0xE204;
        if (copa_SendScciCmd(copaCommand, ((sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA)) + pcopaCommandHeader->DataLength)) < 0 ) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_GetCabinetId: failed, status = 0x%08X!!!\n", pcopaCommandHeader->CmdStatus);
                return -1;
        } else {
                if (pcopaCommandHeader->DataLength >= sizeof(unsigned short)) {
                        cabId = pcopaCommandHeader->CmdData.AsWord;
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_GetCabinetId: CabinetNumber = %d\n", cabId);
                        return 0;
                } else {
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_GetCabinetId: NO Data (stat=0x%08X, dlen=%d)!!!\n", pcopaCommandHeader->CmdStatus, pcopaCommandHeader->DataLength);
                        return -1;
                }
        }
        return 0;
}
static int copa_GetPowerOffInhibit (void)
{
        memset(pcopaCommandHeader, 0, sizeof(copaCommand));
        pcopaCommandHeader->CmdStatus = (V1_CMD_STATUS) 0x16;
        pcopaCommandHeader->OpCode = 0x011D;
        pcopaCommandHeader->CabinetNr = cabId;
        pcopaCommandHeader->DataLength = 0;
        if(copa_SendScciCmd(copaCommand, (sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA))) < 0 ) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_GetPowerOffInhibit: failed (status = 0x%08X)!!!\n", pcopaCommandHeader->CmdStatus);
                return -1;
        } else {
                if (pcopaCommandHeader->DataLength >= sizeof(unsigned char)) {
                        copa_PowerOffInhibitState = pcopaCommandHeader->CmdData.AsByte;
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_GetPowerOffInhibit: copa_PowerOffInhibitState = %d\n", copa_PowerOffInhibitState);
                        return 0;
                } else {
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_GetPowerOffInhibit: NO Data (stat=0x%08X, dlen=%d)!!!\n", pcopaCommandHeader->CmdStatus, pcopaCommandHeader->DataLength);
                        return -1;
                }
        }
        return 0;
}
static int copa_SetPowerOffInhibit (unsigned char value)
{
        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_SetPowerOffInhibit: called with value %d\n", value);
        memset(pcopaCommandHeader, 0, sizeof(copaCommand));
        pcopaCommandHeader->CmdStatus = (V1_CMD_STATUS) 0x16;
        pcopaCommandHeader->OpCode = 0x011C;
        pcopaCommandHeader->CabinetNr = cabId;
        pcopaCommandHeader->DataLength = sizeof(unsigned char);
        pcopaCommandHeader->CmdData.AsByte = value;
        if(copa_SendScciCmd(copaCommand, ((sizeof (V1_SC_COMMAND) - sizeof (V1_CMD_DATA)) + pcopaCommandHeader->DataLength)) < 0 ) {
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_SetPowerOffInhibit: failed (status = 0x%08X)!!!\n", pcopaCommandHeader->CmdStatus);
                return -1;
        } else {
                copa_PowerOffInhibitState = value;
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_SetPowerOffInhibit: New State = %d (retDataLen=%d)\n", copa_PowerOffInhibitState, pcopaCommandHeader->DataLength);
        }
        return 0;
}
int copa_lock (int control_code)
{
        int success = 0;
        copa_IRQ_disabled = (unsigned char) 0;
        copa_CommArrea_reinitialized = (unsigned char) 0;
        copa_lockFunc_successful = (unsigned char) 0;
        p_copa_delay = copa_delay_busy;
        switch (control_code) {
                case 1:
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_lock: called with control_code = 0x%08X\n", control_code);
                        p_copa_delay = copa_delay_busy;
                        if (copa_DisableIRQsFromCopa() < 0) {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_lock: WARNING: Disabling IRQs from CopA failed !\n");
                        }
                        if (copa_ResetAllShmemQueues(pcopaTopHdr) < 0) {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_lock: ERROR: CopA communication area reinitializing failed !!!\n");
                                success = -EINVAL;
                                break;
                        }
                        if (copa_GetCabinetId() < 0) {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_lock: WARNING: Can't get the CabinetNumber from CopA !\n");
                        }
                        if (copa_GetPowerOffInhibit() < 0) {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_lock: WARNING: Can't get the PowerOffInhibit state from CopA !\n");
                        }
                        if (copa_SetPowerOffInhibit ((unsigned char) 1) < 0) {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_lock: ERROR: Can't set the PowerOffInhibit State to CopA!!!\n");
                                success = -EINVAL;
                                break;
                        }
                        if (copa_GetPowerOffInhibit() < 0) {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_lock: WARNING: Can't get the PowerOffInhibit state after setting!\n");
                        } else {
                                if (copa_PowerOffInhibitState != (unsigned char) 1) {
                                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_lock: ERROR: PowerOffInhibit was NOT set correctly by previous commands (it returns = %d)!!!\n", copa_PowerOffInhibitState);
                                        success = -EINVAL;
                                        break;
                                }
                        }
                        success = 0;
                        break;
                default:
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_lock: called with invalid control_code = 0x%08X\n", control_code);
                        success = -EINVAL;
                        break;
        }
        p_copa_delay = copa_delay;
        if (success == 0 ) {
                copa_lockFunc_successful = (unsigned char) 1;
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_lock: returns successfully\n");
        }
        return success;
}
int copa_unlock (int control_code)
{
        int success = 0;
        copa_unlockFunc_successful = (unsigned char) 0;
        switch (control_code) {
                case 1:
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unlock: called with control_code = 0x%08X\n", control_code);
                        p_copa_delay = copa_delay_busy;
                        if ((copa_IRQ_disabled != (unsigned char) 1) ||
                                (copa_CommArrea_reinitialized != (unsigned char) 1) ||
                                (copa_lockFunc_successful != (unsigned char) 1) ||
                                (copa_PowerOffInhibitState != (unsigned char) 1)) {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unlock: WARNING: unexpected CopA state detected (%d %d %d %d)!\n", copa_IRQ_disabled, copa_CommArrea_reinitialized, copa_lockFunc_successful, copa_PowerOffInhibitState);
                        }
                        if (copa_GetPowerOffInhibit() < 0) {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unlock: WARNING: Can't get the PowerOffInhibit state from CopA !\n");
                        } else {
                                if (copa_PowerOffInhibitState != (unsigned char) 1) {
                                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unlock: WARNING: CopA PowerOffInhibit state is NOT TRUE (as expected) (it is = %d)!!!\n", copa_PowerOffInhibitState);
                                }
                        }
                        if (copa_SetPowerOffInhibit ((unsigned char) 0) < 0) {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unlock: ERROR: Can't unset the PowerOffInhibit of CopA!!!\n");
                                success = -EINVAL;
                                break;
                        }
                        if (copa_GetPowerOffInhibit() < 0) {
                                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unlock: WARNING: Can't get the PowerOffInhibit state after setting!\n");
                        } else {
                                if (copa_PowerOffInhibitState != (unsigned char) 0) {
                                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unlock: ERROR: PowerOffInhibit was NOT set correctly by previous command (it is = %d)!!!\n", copa_PowerOffInhibitState);
                                        success = -EINVAL;
                                        break;
                                }
                        }
                        success = 0;
                        break;
                default:
                        if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unlock: called with invalid control_code = 0x%08X\n", control_code);
                        success = -EINVAL;
                        break;
        }
        p_copa_delay = copa_delay;
        if (success == 0 ) {
                copa_unlockFunc_successful = (unsigned char) 1;
                if (copaDebug) printk(KERN_DEBUG "copa :" "copa_unlock: returns successfully\n");
        }
        return success;
}
  
