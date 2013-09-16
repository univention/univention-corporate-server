#!/usr/bin/make -f

.PHONY: all
all::

CA := GlobalSign VeriSign

ifneq ($(filter GlobalSign,${CA}),)
include Makefile.GlobalSign
endif

ifneq ($(filter VeriSign,${CA}),)
include Makefile.VeriSign
endif


%.zip:
	wget -O "$@" "http://download.microsoft.com/download/2/4/E/24E730E6-C012-448F-92B6-78744D3B77E1/$(subst _,%20,$@)"
%.der: %.pem
	openssl x509 -inform pem -in "$<" -outform der -out "$@"
%.pem: %.zip
	unzip -p "$<" > "$@"
%.pem: %.p12
	openssl pkcs12 -in "$<" -nokeys -nokeys -out "$@"

.PHONY: clean
clean:
	$(RM) *.der
	$(RM) *.cer
	$(RM) *.crt
	$(RM) $(patsubst %.zip,%.pem,$(wildcard *.zip))

distclean:
	$(RM) *.zip
	$(RM) *.pem

.PHONY: info
info:
	for pem in *.pem; do echo "$$pem"; openssl x509 -noout -nameopt multiline -subject -issuer -in "$$pem"; done

CERT_PUBLIC_FILENAME ?= $(patsubst %.p12,%.der,${CERT_FILENAME})
.PHONY: install
install:: ${CERT_FILENAME}
	install -m644 "$<" ../win-pvdrivers/univention.p12
install:: ${CERT_CROSS_CERT_FILENAME}
	install -m644 "$<" ../win-pvdrivers/crosscert.pem
install:: ${CERT_PUBLIC_FILENAME}
	install -m644 "$<" ../win-pvdrivers/univention.der

.SECONDARY:
