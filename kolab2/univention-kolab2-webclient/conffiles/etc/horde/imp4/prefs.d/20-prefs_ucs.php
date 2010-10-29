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

@!@
## // default charset for sending messages
ucr_key="horde/prefs/imp/sending_charset"
if ucr_key in baseConfig:
	print "$_prefs['sending_charset']['value'] = '%s';\n" % baseConfig.get(ucr_key)
if baseConfig.is_true("horde/prefs/imp/sending_charset/locked"):
	print "$_prefs['sending_charset']['locked'] = true;\n"

## // save attachments when saving in sent-mail folder?
ucr_key="horde/prefs/imp/save_attachments"
if ucr_key in baseConfig:
	print "$_prefs['save_attachments']['value'] = '%s';\n" % baseConfig.get(ucr_key)

## // precede the signature with dashes ('-- ')?
ucr_key="horde/prefs/imp/sig_dashes"
if ucr_key in baseConfig:
	bin_value={True: 1, False: 0}[ baseConfig.is_true(ucr_key, False) ]
	print "$_prefs['sig_dashes']['value'] = %s;\n" % bin_value

## // default sorting column
ucr_key="horde/prefs/imp/sortby"
if ucr_key in baseConfig:
	print "$_prefs['sortby']['value'] = %s;\n" % baseConfig.get(ucr_key)
 
## // default sorting direction
ucr_key="horde/prefs/imp/sortdir"
if ucr_key in baseConfig:
	bin_value={True: 1, False: 0}[ baseConfig.get(ucr_key).lower() in ('descending', '1') ]
	print "$_prefs['sortdir']['value'] = %s;\n" % bin_value

## // When replying/forwarding to a message, should we use the format of the
## // original message?
ucr_key="horde/prefs/imp/reply_format"
if ucr_key in baseConfig:
	bin_value={True: 1, False: 0}[ baseConfig.get(ucr_key).lower() in ('original', '1') ]
	print "$_prefs['reply_format']['value'] = %s;\n" % bin_value
@!@
// End Personal Information preferences
?>
