# Just to jump into the src directory...

include ID

KDIR		:= /lib/modules/$(shell uname -r)/extra/

FILES		:= $(CARD).ko
ifeq ($(CARD),fcpcmcia)
FILES		+= fcpcmcia_cs.ko
endif
FILES2		:= $(foreach file,$(FILES),src/$(file))

all:		$(FILES2)
	
.PHONY:		install $(FILES2)
	
$(FILES2):	; make -C src

clean:		; make -C src clean

install:	$(FILES2) $(KDIR)
		for f in $(FILES2); do cp -vf $$f $(KDIR); done

$(KDIR):	; mkdir -p $(KDIR)

