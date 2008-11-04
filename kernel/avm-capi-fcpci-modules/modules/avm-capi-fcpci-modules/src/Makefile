# COMMON

CARD		:= fcpci
LIBDIR		:= /var/lib/fritz
OBJECTS		:= main.o driver.o tools.o tables.o queue.o lib.o

ifneq ($(KERNELRELEASE),)

# KERNEL

EXTRA_CFLAGS	+= -D__$(CARD)__ -DTARGET=\"$(CARD)\"
ifndef DEBUG
EXTRA_CFLAGS	+= -DNDEBUG
endif
EXTRA_LDFLAGS	+= $(LIBDIR)/$(CARD)-lib.o

ifeq ($(CARD),fcpcmcia)
obj-m           := $(CARD).o $(CARD)_cs.o
else
obj-m           := $(CARD).o
endif
$(CARD)-objs	:= $(OBJECTS)

else

# ARCHIVE

SOURCES		:= $(patsubst %.o,%.c,$(OBJECTS))
HEADERS		:= defs.h driver.h lib.h libdefs.h libstub.h lock.h \
		   main.h queue.h tables.h tools.h

ifeq ($(KDIR),)
KDIR		:= /lib/modules/$(shell uname -r)/build
endif

ifeq ($(CARD),fcpcmcia)
all:		$(CARD).ko $(CARD)_cs.ko
else
all:		$(CARD).ko
endif
	
$(CARD).ko:	$(LIBDIR) $(SOURCES) $(HEADERS)
		@cp -f ../lib/$(CARD)-lib.o $(LIBDIR)
		$(MAKE) -C $(KDIR) SUBDIRS=$(shell pwd) modules

$(CARD)_cs.ko:	$(CARD)_cs.c $(CARD).ko
		
clean:	;	$(RM) $(OBJECTS)
		$(RM) $(CARD).o $(CARD).ko 
		@$(RM) .*.cmd $(CARD).mod.* 
ifeq ($(CARD),fcpcmcia)
		@$(RM) $(CARD)_cs.o $(CARD)_cs.ko $(CARD)_cs.mod.*
endif

$(LIBDIR):	
		mkdir -p $(LIBDIR)

endif

