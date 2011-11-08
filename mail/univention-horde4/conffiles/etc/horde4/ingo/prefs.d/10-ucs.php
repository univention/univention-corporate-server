<?php

@%@BCWARNING=// @%@

// default filter rules.
$_prefs['rules'] = array(
    'value' =>   'a:1:{i:3;a:3:{s:4:"name";s:11:"Spam Filter";s:6:"action";i:' . Ingo_Storage::ACTION_SPAM . ';s:7:"disable";b:0;}}',
    'locked' => false,
    'type' => 'implicit'
);


@!@
try:
	flo = float(cr.get("mail/antispam/requiredhits", "5.0"))
	spamHits = int(flo)
	if spamHits < flo:
		spamHits = spamHits + 1
except:
    spamHits = 5

print "$_prefs['spam']['value'] = 'a:2:{s:6:\"folder\";s:10:\"INBOX/%s\";s:5:\"level\";i:%s;}';" % (baseConfig.get('mail/cyrus/folder/spam', "Spam"), spamHits)
@!@

?>
