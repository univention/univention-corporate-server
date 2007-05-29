
ALL = README.html README.1 README.txt 

all: $(ALL)


%.txt:%.pod
	pod2text $< > $@

%.1:%.pod
	pod2man $< > $@

%.html:%.pod
	pod2html $< > $@


clean:
	rm -f $(ALL)

realclean: clean
	rm -f *~
