<?php
@%@BCWARNING=// @%@

// UI theme
$_prefs['theme'] = array(
    'value' => 'silver',
    'locked' => false,
    'shared' => true,
    'type' => 'select',
    'desc' => _("Select your color scheme.")
);

// the layout of the portal page.
$_prefs['portal_layout'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

@!@
## // Perform maintenance operations on login
ucr_key="horde/prefs/do_maintenance"
if ucr_key in baseConfig:
	bool_value={True: "true", False: "false"}[ baseConfig.is_true(ucr_key, True) ]
	print "$_prefs['do_maintenance']['value'] = %s;\n" % bool_value
@!@
?>
