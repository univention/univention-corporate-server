#ident "$Header$"
#******************************************************************************
#* Copyright (C) Fujitsu Siemens Computers 2001, 2002
#* All rights reserved
#*
#* Makefile for the ServerView Agent modules
#*
#* The modules needed by the ServerView Agents are build for the current
#* running kernel. This requires that the kernel include files are present
#* and match to the current kernel.
#* It tries to use /proc/config.gz (SuSE) or <linux/vmlinuz.autoconf.h> (SuSE)
#* or <linux/autoconf.h> (which implicitly includes /boot/kernel.h on RedHat)
#* as the current kernel's configuration. Therefore an own linux/autoconf.h
#* file is created.
#* In all cases CONFIG_SMP redetermined bye 'cpu0'-line in /proc/stat.
#* An own linux/version.h file is created which contains the version defines
#* of the currently running kernel.
#* It searches for the kernel include path with the following priority:
#*     1. /lib/modules/<kernel>/build/include
#*     2. /usr/src/linux-<kernel>/include
#*     3. /usr/include
#* If the kernel source tree is on another location, you can add the following
#* argument to the make call (please specify without include subdirectory):
#*     LINUX_DIR=<path>
#* It checks if the kernel version mentioned in <include path>linux/version.h
#* is the same as reported by uname -r.
#*
#******************************************************************************
AWK		= awk
CP              = cp -f

ARCH           := $(shell uname -m)
SYSTEM         := univention
ifeq ($(SYSTEM),)
$(error SYSTEM variable not set)
endif

ifeq ($(ARCH),x86_64)
KERNEL_X86_64  := -mcmodel=kernel
endif

ifeq ($(ARCH),ia64)
KERNEL_IA64_DEFINES     := -D_IA64_ -DDO_NOT_USE_OS_PM_POWER_OFF
endif

ifeq ($(shell uname -r | grep -s xen),)
KERNEL_DEFINES = 
else
KERNEL_DEFINES = -DXEN_KERNEL
endif


LINUX_VERSION  := $(shell uname -r)
LINUX_KERNEL   := $(word 1,$(subst -, ,$(LINUX_VERSION)))
LINUX_VER_1    := $(word 1,$(subst ., ,$(LINUX_KERNEL)))
LINUX_VER_2    := $(word 2,$(subst ., ,$(LINUX_KERNEL)))
LINUX_VER_3    := $(word 3,$(subst ., ,$(LINUX_KERNEL)))
KERNEL_VERS    := $(LINUX_VER_1).$(LINUX_VER_2)

ifeq ($(shell grep -s 'smp_num_cpus' /proc/ksyms),)
LINUX_SMP      := no
else
LINUX_SMP      := yes
endif

LINUX_LIBMOD    := no
LINUX_CPVERS    := no
LINUX_DIR	:= /usr/src/linux
ifeq ($(shell ls -d $(LINUX_DIR)/include/linux 2>/dev/null),)
else
LINUX_LIBMOD   :=yes
endif

LINUX_VFILE    := version.h
LINUX_VPATH    := $(LINUX_DIR)/include/linux/$(LINUX_VFILE)
ifeq ($(shell ls $(LINUX_VPATH) 2>/dev/null),)
LINUX_VFILE    := .kversion
LINUX_VPATH    := $(LINUX_DIR)/$(LINUX_VFILE)
ifeq ($(shell ls $(LINUX_VPATH) 2>/dev/null),)
ifeq ($(LINUX_LIBMOD),no)
LINUX_DIR      := /usr
LINUX_VFILE    := version.h
LINUX_VPATH    := $(LINUX_DIR)/include/linux/$(LINUX_VFILE)
else
LINUX_CPVERS   := yes
LINUX_VFILE    := version.h
LINUX_VPATH    := /usr/include/linux/$(LINUX_VFILE)
endif
endif
endif

ifeq ($(LINUX_VFILE),.kversion)
SOURCE_KERNEL  := $(shell cat $(LINUX_VPATH))
SOURCE_VER_1   := $(word 1,$(subst ., ,$(SOURCE_KERNEL)))
SOURCE_VER_2   := $(word 2,$(subst ., ,$(SOURCE_KERNEL)))
SOURCE_VER_3   := $(word 3,$(subst ., ,$(SOURCE_KERNEL)))
else
SOURCE_KERNEL  := $(shell awk '/\#define[ ]+LINUX_VERSION_CODE[ ]+/ {print $$3; exit(0)}' $(LINUX_VPATH))
SOURCE_VER_1   := $(shell echo $$(($(SOURCE_KERNEL) >> 16)))
SOURCE_VER_2   := $(shell echo $$((($(SOURCE_KERNEL) >> 8) & 0xff)))
SOURCE_VER_3   := $(shell echo $$(($(SOURCE_KERNEL) & 0xff)))
endif

SOURCE_VERSION := $(SOURCE_VER_1).$(SOURCE_VER_2).$(SOURCE_VER_3)

MODULE_DIR     := /lib/modules/$(LINUX_VERSION)/srvmagt
AUTOCONF_INC   := ./linux/autoconf.h
VERSION_INC    := ./linux/version.h
RHCONFIG_INC   := ./linux/rhconfig.h
MODVERS_INC    := $(LINUX_DIR)/include/linux/modversions.h

ifeq ($(shell ls $(LINUX_DIR)/include/linux/vmlinuz.autoconf.h 2>/dev/null),)
LINUX_BCONF    := no
else
LINUX_BCONF    := yes
endif

ifeq ($(shell ls /proc/config.gz 2>/dev/null),)
LINUX_PCONF    := no
else
LINUX_PCONF    := yes
endif

define INCLUDE_PCONF
				gunzip -dc /proc/config.gz | awk '$$1~/^CONFIG_.*=/ { \
					split($$0, def, /=/); \
					if (def[2] == "n") next; \
					if (def[2] == "m") def[1] = def[1] "_MODULE"; \
					if ((def[2] == "y") || (def[2] == "m")) def[2] = "1"; \
					printf "#define %s (%s)\n", def[1], def[2]; \
				}'
endef

ifeq ($(MODVERSIONS),no)
NOMODVERSIONS  := -DPRECOMPILE
else
NOMODVERSIONS  :=
endif

define COMPILE_MOD
				$(CC) -c -O -g $(KERNEL_X86_64) $(KERNEL_DEFINES) $(KERNEL_IA64_DEFINES) -I. -I$(LINUX_DIR)/include -D$(shell echo $(SYSTEM) | tr [:lower:] [:upper:]) $(NEW_REMAP_INTF) $(NOMODVERSIONS) -o $@ $(notdir $(@:%.o=%.c))
endef

ifeq ($(ARCH),ia64)
SRCS           := ipmi.c smbus.c
else
ifeq ($(SOURCE_VERSION),2.6.24)
SRCS           := ipmi.c smbus.c
else
SRCS           := copa.c ipmi.c smbus.c
endif
endif
OBJS           := $(SRCS:%.c=%.o)
MODS           := $(addprefix $(MODULE_DIR)/,$(OBJS))

ifeq ($(KERNEL_VERS), 2.6)
OPTIMIZE       := -O
NODEPREC =-Wno-deprecated-declarations
# Suppress -O optimize option for ia64 platforms because the Message 
#    *** Warning: "__put_user_unknown" [/etc/srvmagt/sources/ipmi.ko] undefined!
# disappeared without -O
ifeq ($(ARCH),ia64)
OPTIMIZE       :=
endif
obj-m          := $(OBJS)
EXTRA_CFLAGS   += -c $(OPTIMIZE) -g -I. -I$(LINUX_DIR)/include $(KERNEL_X86_64) $(KERNEL_DEFINES) $(KERNEL_IA64_DEFINES) -D$(shell echo $(SYSTEM) | tr [:lower:] [:upper:]) $(NEW_REMAP_INTF) $(NOMODVERSIONS) -DKERNEL26 $(NODEPREC)
KSRCDIR         = /usr/src/linux
endif

#******************************************************************************

ifdef ONLY_SHOW_MODS
.SILENT:
endif

ifeq ($(KERNEL_VERS), 2.6)
.PHONY:         $(AUTOCONF_INC) $(VERSION_INC)
all:            default clean

default:
		$(MAKE) -C $(LINUX_DIR) V=0 SUBDIRS=$$PWD modules
		mkdir -m 755 -p $(MODULE_DIR)
		$(CP) *.ko $(MODULE_DIR)
else
.PHONY:         $(AUTOCONF_INC) $(VERSION_INC) $(MODS)

ifeq ($(SOURCE_VER_1).$(SOURCE_VER_2),$(LINUX_VER_1).$(LINUX_VER_2))
all:            $(MODS) clean
else
all:
				$(error Kernel include sources doesn't match the running kernel)
endif

$(MODS):        $(MODULE_DIR) $(AUTOCONF_INC) $(VERSION_INC) $(MODVERS_INC) $(RHCONFIG_INC)
ifdef ONLY_SHOW_MODS
				@if $(COMPILE_MOD) 2>/dev/null; then \
					echo -n "$(notdir $(@:%.o=%))(Ok) "; \
				else \
					echo -n "$(notdir $(@:%.o=%))(Err) "; \
					exit 1; \
				fi
else
				$(COMPILE_MOD)
endif

$(OBJS:%.o=%):  % : %.o ;

$(OBJS):        $(MODULE_DIR) $(AUTOCONF_INC) $(VERSION_INC) $(MODVERS_INC) $(RHCONFIG_INC)
				-$(COMPILE_MOD)
				rm -rf $(dir $(VERSION_INC))
endif

$(AUTOCONF_INC):
				mkdir -m 755 -p $(dir $@)
ifeq ($(LINUX_CPVERS),yes)
				@echo 'copy version.h, autoconf.h, rhconfig.h'
				cp /usr/include/linux/version.h $(LINUX_DIR)/include/linux
				cp /usr/include/linux/autoconf.h $(LINUX_DIR)/include/linux
				cp /usr/include/linux/rhconfig.h $(LINUX_DIR)/include/linux
endif

ifeq ($(LINUX_PCONF),yes)
				echo '#define AUTOCONF_INCLUDED' >$@
				$(INCLUDE_PCONF) >>$@
else
ifeq ($(LINUX_BCONF),yes)
				cp $(LINUX_DIR)/include/linux/vmlinuz.autoconf.h $@
else
				cp $(LINUX_DIR)/include/linux/autoconf.h $@
endif
endif
				echo '#undef  CONFIG_SMP' >>$@
ifeq ($(LINUX_SMP),yes)
				echo '#define CONFIG_SMP 1' >>$@
endif
				chmod 644 $@

$(VERSION_INC):
				mkdir -m 755 -p $(dir $@)
				echo '#define UTS_RELEASE "$(LINUX_VERSION)"' >$@
				echo '#define LINUX_VERSION_CODE $(shell printf 0x%02x%02x%02x $(LINUX_VER_1) $(LINUX_VER_2) $(LINUX_VER_3))' >>$@
				echo '#define KERNEL_VERSION(a,b,c) (((a) << 16) + ((b) << 8) + (c))' >>$@
				chmod 644 $@

$(MODVERS_INC):
				touch ./linux/modversions.h

$(RHCONFIG_INC):
ifeq ($(SUMMIT_KERNEL),yes)
				mkdir -m 755 -p $(dir $@)
				echo '#ifndef __rh_config_h' >$@
				echo '#define __rh_config_h' >>$@
				echo '#define __module__summit' >>$@
				echo '#define _ver_str(x) smp_ ## x' >>$@
				echo '#define RED_HAT_LINUX_KERNEL 1' >>$@
				echo '#endif' >>$@
				chmod 644 $@
endif

$(MODULE_DIR):
				mkdir -m 755 -p $@

clean:
ifeq ($(KERNEL_VERS), 2.6)
				rm -f $(obj-m)
				rm -f *.mod.c
else
				rm -rf $(dir $(VERSION_INC))
endif

show:
				@echo 'SYSTEM:        "$(SYSTEM)"'
				@echo 'NEW_REMAP_INTF: "$(NEW_REMAP_INTF)"'
				@echo 'LINUX_VERSION: "$(LINUX_VERSION)"'
				@echo 'LINUX_KERNEL:  "$(LINUX_KERNEL)"'
				@echo 'LINUX_VER_1:   "$(LINUX_VER_1)"'
				@echo 'LINUX_VER_2:   "$(LINUX_VER_2)"'
				@echo 'LINUX_VER_3:   "$(LINUX_VER_3)"'
				@echo 'LINUX_SMP:     "$(LINUX_SMP)"'
				@echo 'LINUX_BCONF:   "$(LINUX_BCONF)"'
				@echo 'LINUX_PCONF:   "$(LINUX_PCONF)"'
				@echo 'LINUX_DIR:     "$(LINUX_DIR)"'
				@echo 'LINUX_VPATH:   "$(LINUX_VPATH)"'
				@echo 'SOURCE_KERNEL: "$(SOURCE_KERNEL)"'
				@echo 'SOURCE_VER_1:  "$(SOURCE_VER_1)"'
				@echo 'SOURCE_VER_2:  "$(SOURCE_VER_2)"'
				@echo 'SOURCE_VER_3:  "$(SOURCE_VER_3)"'
				@echo 'SOURCE_VERSION:"$(SOURCE_VERSION)"'
				@echo 'MODULE_DIR:    "$(MODULE_DIR)"'
				@echo 'NOMODVERSIONS: "$(NOMODVERSIONS)"'
				@echo 'SRCS:          "$(SRCS)"'
				@echo 'OBJS:          "$(OBJS)"'
				@echo 'MODS:          "$(MODS)"'
