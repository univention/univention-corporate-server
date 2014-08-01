_LNG=$(LANGUAGE)
STAMP=stampinf -f $@ -a $(_BUILDARCH) -d * -k $(KMDF_VERSION_MAJOR).$(KMDF_VERSION_MINOR) -v $(GPLPV_VERSION)

$(OBJ_PATH)\$(O)\$(TARGETNAME).inf: $(TARGETNAME).inx sources ..\common.inc
    copy $(@B).inx $@
    $(STAMP)
