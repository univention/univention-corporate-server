_LNG=$(LANGUAGE)
STAMP=stampinf -f $@ -a $(_BUILDARCH) -d * -v $(VERSION)

$(OBJ_PATH)\$(O)\$(TARGETNAME).inf: $(TARGETNAME).inx sources ..\common.inc
    copy $(@B).inx $@
    $(STAMP)
