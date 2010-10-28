<?php
@%@BCWARNING=// @%@

@!@
## // HTML driver settings
ucr_key="horde/mime_settings/imp/html/inline"
if ucr_key in baseConfig:
	bool_value={True: "true", False: "false"}[ baseConfig.is_true(ucr_key, False) ]
	print "$mime_drivers['imp']['html']['inline'] = %s;\n" % bool_value
@!@
?>
