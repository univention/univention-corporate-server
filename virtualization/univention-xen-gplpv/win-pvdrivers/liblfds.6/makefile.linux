##### paths #####
BINDIR  = bin
INCDIR  = inc
OBJDIR  = obj
SRCDIR  = src

##### misc #####
QUIETLY = 1>/dev/null 2>/dev/null

##### sources, objects and libraries #####
BINNAME = liblfds
AR_BINARY = $(BINDIR)/$(BINNAME).a
SO_BINARY = $(BINDIR)/$(BINNAME).so
SRCDIRS = abstraction freelist queue ringbuffer slist stack
# TRD : be aware - in the linux makefile, with the one-pass linking behaviour of the GNU linker, the order
#       of source files matters!  this is because it leads to the ordering of objects in the library and
#       that in turn, since the data structures all use the freelist API and the abstraction API, has to be
#       correct 
SOURCES = queue_delete.c queue_new.c queue_query.c queue_queue.c \
          ringbuffer_delete.c ringbuffer_get_and_put.c ringbuffer_new.c ringbuffer_query.c \
          slist_delete.c slist_get_and_set.c slist_link.c slist_new.c \
          stack_delete.c stack_new.c stack_push_pop.c stack_query.c \
          freelist_delete.c freelist_get_and_set.c freelist_new.c freelist_query.c freelist_pop_push.c \
          abstraction_aligned_free.c abstraction_aligned_malloc.c abstraction_cas.c abstraction_dcas.c abstraction_increment.c
OBJECTS = $(patsubst %.c,$(OBJDIR)/%.o,$(notdir $(SOURCES)))

##### CPU variants #####
GCCARCH = $(shell uname -m)

ifeq ($(GCCARCH),x86_64)
  GCCARCH = core2
endif

ifeq ($(findstring arm,$(GCCARCH)),arm)
  GCCARCH = armv6k
endif

##### tools #####
MAKE    = make
MFLAGS  = 

DG      = gcc
DGFLAGS = -MM -std=c99 -I"$(SRCDIR)" -I"$(INCDIR)"

CC      = gcc
CBASE   = -Wall -Wno-unknown-pragmas -std=c99 -march=$(GCCARCH) -c -I"$(SRCDIR)" -I"$(INCDIR)"
CFREL   = -O2 -finline-functions -Wno-strict-aliasing
CFDBG   = -O0 -g

AR      = ar
AFLAGS  = -rcs

LD      = gcc
LFBASE  = -Wall -std=c99 -shared
LFREL   = -O2 -s
LFDBG   = -O0 -g

##### rel/dbg .a/.so variants #####
ifeq ($(findstring so,$(MAKECMDGOALS)),so)
  CBASE := $(CBASE) -fpic
endif

CFLAGS  = $(CBASE) $(CFDBG)
LFLAGS  = $(LFBASE) $(LFDBG)

ifeq ($(findstring rel,$(MAKECMDGOALS)),rel)
  CFLAGS  = $(CBASE) $(CFREL)
  LFLAGS  = $(LFBASE) $(LFREL)
endif

##### search paths #####
vpath %.c $(patsubst %,$(SRCDIR)/%:,$(SRCDIRS))

##### implicit rules #####
$(OBJDIR)/%.o : %.c
	$(DG) $(DGFLAGS) $< >$(OBJDIR)/$*.d
	$(CC) $(CFLAGS) -o $@ $<

##### explicit rules #####
$(AR_BINARY) : $(OBJECTS)
	$(AR) $(AFLAGS) $(AR_BINARY) $(OBJECTS)

$(SO_BINARY) : $(OBJECTS)
	$(LD) $(LFLAGS) $(SYSLIBS) $(OBJECTS) -o $(SO_BINARY)

##### phony #####
.PHONY : clean arrel ardbg sorel sodbg

clean : 
	@rm -f $(BINDIR)/$(BINNAME).* $(OBJDIR)/*.o $(OBJDIR)/*.d

arrel : $(AR_BINARY)
ardbg : $(AR_BINARY)

sorel : $(SO_BINARY)
sodbg : $(SO_BINARY)

##### dependencies #####
-include $(DEPENDS)

##### notes #####
# TRD : we use -std=c99 purely to permit C++ style comments

