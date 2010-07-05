<?php

@%@BCWARNING=// @%@

// Make sure that constants are defined.
@define('IMP_BASE', '/usr/share/horde3/imp');
require_once IMP_BASE . '/lib/IMP.php';

// Personal Information preferences

// sent mail folder
$_prefs['sent_mail_folder'] = array(
// For Exchange server uncomment the line below and delete the line above
//    'value' => 'Sent Items',
@!@
value=baseConfig.get('horde/folder/sent')
if value:
	value="'%s'" % value
else:
	value='_("Sent")'
print "    'value' => %s," % value
@!@    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// drafts folder
$_prefs['drafts_folder'] = array(
@!@
value=baseConfig.get('horde/folder/drafts')
if value:
	value="'%s'" % value
else:
	value='_("Drafts")'
print "    'value' => %s," % value
@!@    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// trash folder
$_prefs['trash_folder'] = array(
// for Exchange, uncomment the entry below and remove the default value entry
//    'value' => 'Deleted Items',
@!@
value=baseConfig.get('horde/folder/trash')
if value:
	value="'%s'" % value
else:
	value='_("Trash")'
print "    'value' => %s," % value
@!@    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// spam folder
$_prefs['spam_folder'] = array(
@!@
value=baseConfig.get('horde/folder/spam')
if value:
	value="'%s'" % value
else:
	value='_("Spam")'
print "    'value' => %s," % value
@!@    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// End Personal Information preferences
?>
