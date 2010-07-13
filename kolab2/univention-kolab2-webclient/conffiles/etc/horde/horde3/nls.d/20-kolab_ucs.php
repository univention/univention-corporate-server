<?php

@%@BCWARNING=// @%@

@!@
locale = baseConfig.get('locale/default', 'de_DE.UTF-8:UTF-8')
locale_charset_encoding = locale.rsplit(':',1)
if len(locale_charset_encoding) == 2:
	encoding = locale_charset_encoding[1]
	locale_charset_encoding = locale_charset_encoding[0].rsplit('.',1)
	if len(locale_charset_encoding) == 2:
		print "$nls['charsets']['%s'] = '%s'" % (locale_charset_encoding[0], encoding)
		#if encoding == 'UTF-8' and locale_charset_encoding[0] == 'de_DE':
		#	$nls['spelling']['de_DE'] = '-d deutsch';
@!@
?>
