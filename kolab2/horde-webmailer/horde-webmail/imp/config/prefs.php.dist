<?php
/**
 * $Horde: imp/config/prefs.php.dist,v 1.216.4.37 2009-11-29 05:27:14 chuck Exp $
 *
 * See horde/config/prefs.php for documentation on the structure of this file.
 */

// Make sure that constants are defined.
require_once dirname(__FILE__) . '/../lib/IMP.php';
$is_pop3 = isset($_SESSION['imp']) &&
           $_SESSION['imp']['base_protocol'] == 'pop3';

$prefGroups['identities'] = array(
    'column' => _("General Options"),
    'label' => _("Personal Information"),
    'desc' => _("Change the name, address, and signature that people see when they read and reply to your email."),
    'members' => array('replyto_addr', 'alias_addr', 'tieto_addr', 'bcc_addr',
                       'signature', 'sig_dashes', 'sig_first',
                       'save_sent_mail', 'sent_mail_folder', 'sentmailselect')
);

if (!$is_pop3) {
    $prefGroups['server'] = array(
        'column' => _("General Options"),
        'label' => _("Server and Folder Information"),
        'desc' => _("Change mail server and folder settings."),
        'members' => array('use_vinbox', 'subscribe', 'folderselect',
                           'trashselect', 'spamselect')
        );
}

if (!empty($_SESSION['imp']['acl'])) {
    $prefGroups['acl'] = array(
        'column' => _("General Options"),
        'label' => _("Share Folders"),
        'desc' => _("Share your mail folders with other users."),
        'url' => 'acl.php'
    );
}

$prefGroups['logintasks'] = array(
    'column' => _("General Options"),
    'label' => _("Login Tasks"),
    'desc' => sprintf(_("Customize tasks to run upon logon to %s."), $GLOBALS['registry']->get('name')),
    'members' => array()
);
if (!$is_pop3) {
    $prefGroups['logintasks']['members'] = array_merge(
        $prefGroups['logintasks']['members'],
        array('initialpageselect', 'rename_sentmail_monthly',
              'delete_sentmail_monthly', 'delete_sentmail_monthly_keep',
              'purge_sentmail', 'purge_sentmail_interval',
              'purge_sentmail_keep', 'purge_trash', 'purge_trash_interval',
              'purge_trash_keep', 'purge_spam', 'purge_spam_interval',
              'purge_spam_keep'));
}
$prefGroups['logintasks']['members'] = array_merge(
    $prefGroups['logintasks']['members'],
    array('delete_attachments_monthly', 'delete_attachments_monthly_keep'));

$prefGroups['compose'] = array(
    'column' => _("Message Options"),
    'label' => _("Message Composition"),
    'desc' => _("Customize how you send mail."),
    'members' => array('stationery_link', 'mailto_handler', 'compose_cc',
                       'compose_bcc', 'compose_spellcheck', 'compose_confirm',
                       'set_priority', 'compose_popup', 'compose_html',
                       'jseditor', 'fckeditor_buttons', 'xinha_hide_buttons',
                       'mail_domain', 'compose_cursor', 'sending_charset',
                       'encryptselect', 'save_attachments')
);

if (!empty($GLOBALS['conf']['compose']['allow_receipts'])) {
    $prefGroups['compose']['members'] = array_merge($prefGroups['compose']['members'], array('disposition_request_read'));
}

$prefGroups['reply_forward'] = array(
    'column' => _("Message Options"),
    'label' => _("Message Replies/Forwards"),
    'desc' => _("Customize how you reply to or forward mail."),
    'members' => array('reply_quote', 'reply_format', 'forward_default',
                       'forward_bodytext', 'reply_headers', 'attrib_text')
);

$prefGroups['drafts'] = array(
    'column' => _("Message Options"),
    'label' => _("Message Drafts"),
    'desc' => _("Customize how to deal with message drafts."),
    'members' => array('folderselect', 'close_draft', 'unseen_drafts')
);

$prefGroups['viewing'] = array(
    'column' => _("Message Options"),
    'label' => _("Message Viewing"),
    'desc' => _("Configure how messages are displayed."),
    'members' => array('filtering', 'strip_attachments',
                       'html_image_replacement', 'html_image_addrbook',
                       'highlight_text', 'highlight_simple_markup',
                       'show_quoteblocks', 'dim_signature', 'emoticons',
                       'attachment_display', 'mail_hdr', 'default_msg_charset',
                       'alternative_display')
);
if (!empty($GLOBALS['conf']['maillog']['use_maillog'])) {
    $prefGroups['viewing']['members'] = array_merge($prefGroups['viewing']['members'], array('disposition_send_mdn'));
}

$prefGroups['delmove'] = array(
    'column' => _("Message Options"),
    'label' => _("Deleting and Moving Messages"),
    'desc' => _("Set preferences for what happens when you move and delete messages."),
    'members' => array('mailbox_return', 'delete_spam_after_report',
                       'empty_spam_menu')
);
if (!$is_pop3) {
    $prefGroups['delmove']['members'] = array_merge(
        $prefGroups['delmove']['members'],
        array('use_trash', 'trashselect', 'use_vtrash', 'empty_trash_menu'));
}

$prefGroups['newmail'] = array(
    'column' => _("Message Options"),
    'label' => _("New Mail"),
    'desc' => _("Control when new mail will be checked for, and whether or not to notify you when it arrives."),
    'members' => array('refresh_time', 'nav_poll_all', 'nav_popup', 'soundselect')
);

if (!empty($GLOBALS['conf']['mailbox']['show_preview'])) {
    $prefGroups['mailpreview'] = array(
        'column' => _("Message Options"),
        'label' => _("Mail Previews"),
        'desc' => _("Configure mail preview options."),
        'members' => array('preview_enabled', 'preview_maxlen', 'preview_strip_nl', 'preview_show_unread', 'preview_show_tooltip')
    );
}

if (!$is_pop3) {
    $prefGroups['fetchmail'] = array(
        'column' => _("Message Options"),
        'label' => _("Fetch Mail"),
        'desc' => _("Customize accounts for fetching mail from other accounts."),
        'members' => array('fetchmail_link', 'fetchmail_popup',
                           'fetchmail_menu')
    );
}

$prefGroups['display'] = array(
    'column' => _("Other Options"),
    'label' => _("Mailbox and Folder Display Options"),
    'desc' => _("Change display options such as how many messages you see on each page and how messages are sorted."),
    'members' => array('mailbox_start', 'sortby', 'sortdir', 'max_msgs',
                       'from_link', 'time_format')
);
if (!$is_pop3) {
    $prefGroups['display']['members'] = array_merge(
        $prefGroups['display']['members'],
        array('nav_expanded', 'tree_view', 'nav_expanded_sidebar'));
}

$prefGroups['filters'] = array(
    'column' => _("Other Options"),
    'label' => _("Filters"),
    'desc' => _("Create filtering rules to organize your incoming mail, sort it into folders, and delete spam."),
    'url' => 'filterprefs.php'
);

$contacts_app = $GLOBALS['registry']->hasInterface('contacts');
if ($contacts_app && $GLOBALS['registry']->hasPermission($contacts_app)) {
    $prefGroups['addressbooks'] = array(
        'column' => _("Other Options"),
        'label' => _("Address Books"),
        'desc' => _("Select address book sources for adding and searching for addresses."),
        'members' => array('save_recipients', 'display_contact', 'sourceselect')
        );
}

if (isset($GLOBALS['conf']['utils']['gnupg'])) {
    $prefGroups['pgp'] = array(
        'column' => _("Other Options"),
        'label' => _("PGP Options"),
        'desc' => sprintf(_("Control PGP support for %s."), $GLOBALS['registry']->get('name')),
        'url' => 'pgp.php'
    );
}

if (Util::extensionExists('openssl') && isset($GLOBALS['conf']['utils']['openssl_binary'])) {
    $prefGroups['smime'] = array(
        'column' => _("Other Options"),
        'label' => _("S/MIME Options"),
        'desc' => sprintf(_("Control S/MIME support for %s."), $GLOBALS['registry']->get('name')),
        'url' => 'smime.php'
    );
}

// Personal Information preferences

// user preferred email address for Reply-To:, if different from From:
$_prefs['replyto_addr'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'text',
    'desc' => _("Your Reply-to: address: <em>(optional)</em>"));

// user preferred alias addresses
$_prefs['alias_addr'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'textarea',
    'desc' => _("Your alias addresses: <em>(optional, enter each address on a new line)</em>"));

// user preferred 'tie to' addresses
$_prefs['tieto_addr'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'textarea',
    'desc' => _("Addresses to explicitly tie to this identity: <em>(optional, enter each address on a new line)</em>"));

// Automatically Bcc addresses when composing
$_prefs['bcc_addr'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'textarea',
    'desc' => _("Addresses to BCC all messages: <em>(optional, enter each address on a new line)</em>"));

// user signature
$_prefs['signature'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'textarea',
    'desc' => _("Your signature:"));

// precede the signature with dashes ('-- ')?
$_prefs['sig_dashes'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Precede your signature with dashes ('-- ')?"));

// signature before replies and forwards?
$_prefs['sig_first'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Place your signature before replies and forwards?"));

// save a copy of sent messages?
$_prefs['save_sent_mail'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Save sent mail?"));

// sent mail folder
$_prefs['sent_mail_folder'] = array(
    // The mailbox value must be encoded in the UTF7-IMAP charset (see RFC
    // 3501 [5.1.3]). For Exchange, uncomment the entry below and remove the
    // default value entry.
    // 'value' => 'Sent Items',
    'value' => _("Sent"),
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// sent mail folder selection widget. includes some javascript, so it's
// specific to IMP.
$_prefs['sentmailselect'] = array('type' => 'special');

// End Personal Information preferences


// Server and Folder Information preferences

// display Virtual INBOX?
$_prefs['use_vinbox'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Display Virtual Inbox?"));

// use IMAP subscribe?
$_prefs['subscribe'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Use IMAP folder subscriptions?"));

// drafts folder selection widget. includes some javascript, so it's specific
// to IMP.
$_prefs['folderselect'] = array('type' => 'special');

// drafts folder
$_prefs['drafts_folder'] = array(
    // The mailbox value must be encoded in the UTF7-IMAP charset (see RFC
    // 3501 [5.1.3]).
    'value' => _("Drafts"),
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// trash folder selection widget. includes some javascript, so it's
// specific to IMP.
$_prefs['trashselect'] = array('type' => 'special');

// trash folder
$_prefs['trash_folder'] = array(
    // The mailbox value must be encoded in the UTF7-IMAP charset (see RFC
    // 3501 [5.1.3]). For Exchange, uncomment the entry below and remove the
    // default value entry.
    // 'value' => 'Deleted Items',
    'value' => _("Trash"),
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// spam folder selection widget. includes some javascript, so it's
// specific to IMP.
$_prefs['spamselect'] = array('type' => 'special');

// spam folder
$_prefs['spam_folder'] = array(
    // The mailbox value must be encoded in the UTF7-IMAP charset (see RFC
    // 3501 [5.1.3]).
    'value' => _("Spam"),
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

$_prefs['vfolder'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// End Server and Folder Information preferences


// Folder sharing preferences

// folder sharing options
// set 'locked' => true to disable folder sharing
$_prefs['acl'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// End folder sharing preferences


// Login/Maintenance Tasks preferences

// select widget for the initial_page preference
$_prefs['initialpageselect'] = array('type' => 'special');

// the page to display. Either a filename like 'folders.php'
// or a mailbox name.
$_prefs['initial_page'] = array(
    'value' => 'INBOX',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// rename sent-mail folder every month?
$_prefs['rename_sentmail_monthly'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Rename sent-mail folder at beginning of month?"),
    'help' => 'prefs-rename_sentmail_monthly');

// delete sent-mail folders every month?
$_prefs['delete_sentmail_monthly'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Delete old sent-mail folders at beginning of month?"),
    'help' => 'prefs-delete_sentmail_monthly');

// how many old sent-mail folders to keep every month?
$_prefs['delete_sentmail_monthly_keep'] = array(
    'value' => 12,
    'locked' => false,
    'shared' => false,
    'type' => 'number',
    'desc' => _("Number of old sent-mail folders to keep if deleting monthly."),
    'help' => 'prefs-delete_sentmail_monthly_keep');

// purge sent-mail folder?
$_prefs['purge_sentmail'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Purge old messages in the sent-mail folder(s)?"),
    'help' => 'prefs-purge_sentmail');

// how often to purge the Sent-Mail folder?
// 'value': yearly = 1, monthly = 2, weekly = 3, daily = 4, every login = 5
$_prefs['purge_sentmail_interval'] = array(
    'value' => '2',
    'locked' => false,
    'shared' => false,
    'type' => 'select',
    'desc' => _("Purge sent-mail how often:"),
    'help' => 'prefs-purge_sentmail_interval');

// when purging sent-mail folder, purge messages older than how many days?
$_prefs['purge_sentmail_keep'] = array(
    'value' => 30,
    'locked' => false,
    'shared' => false,
    'type' => 'number',
    'desc' => _("Purge messages in sent-mail folder(s) older than this amount of days."),
    'help' => 'prefs-purge_sentmail_keep');

// purge old attachments every month?
$_prefs['delete_attachments_monthly'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Delete old linked attachments at beginning of month?"),
    'help' => 'prefs-delete_attachments_monthly');

// how many old months of attachments to keep?
$_prefs['delete_attachments_monthly_keep'] = array(
    'value' => 6,
    'locked' => false,
    'shared' => false,
    'type' => 'number',
    'desc' => _("Number of months to keep old linked attachments if deleting monthly."),
    'help' => 'prefs-delete_attachments_monthly_keep');

// purge Spam folder?
$_prefs['purge_spam'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Purge old messages in the Spam folder?"),
    'help' => 'prefs-purge_spam');

// how often to purge the Spam folder?
// 'value': yearly = 1, monthly = 2, weekly = 3, daily = 4, every login = 5
$_prefs['purge_spam_interval'] = array(
    'value' => '2',
    'locked' => false,
    'shared' => false,
    'type' => 'select',
    'desc' => _("Purge Spam how often:"),
    'help' => 'prefs-purge_spam_interval');

// when purging Spam folder, purge messages older than how many days?
$_prefs['purge_spam_keep'] = array(
    'value' => 30,
    'locked' => false,
    'shared' => false,
    'type' => 'number',
    'desc' => _("Purge messages in Spam folder older than this amount of days."),
    'help' => 'prefs-purge_spam_keep');

// purge Trash folder?
$_prefs['purge_trash'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Purge old messages in the Trash folder?"),
    'help' => 'prefs-purge_trash');

// how often to purge the Trash folder?
// 'value': yearly = 1, monthly = 2, weekly = 3, daily = 4, every login = 5
$_prefs['purge_trash_interval'] = array(
    'value' => '2',
    'locked' => false,
    'shared' => false,
    'type' => 'select',
    'desc' => _("Purge Trash how often:"),
    'help' => 'prefs-purge_trash_interval');

// when purging Trash folder, purge messages older than how many days?
$_prefs['purge_trash_keep'] = array(
    'value' => 30,
    'locked' => false,
    'shared' => false,
    'type' => 'number',
    'desc' => _("Purge messages in Trash folder older than this amount of days."),
    'help' => 'prefs-purge_trash_keep');

// show tos agreement?
$_prefs['tos_agreement'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// End Login/Maintenance preferences


// Message Composition preferences

// Link to the stationery preferences.
$_prefs['stationery_link'] = array(
    'type' => 'link',
    'url' => 'stationery.php',
    'desc' => _("To the stationery and form responses."));

$_prefs['stationery'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// Link to add a Firefox 3 mailto: handler
$_prefs['mailto_handler'] = array(
    'type' => 'link',
    'xurl' => 'javascript:if(typeof navigator.registerProtocolHandler==\'undefined\')alert(\''
        . addslashes(_("Your browser does not support this feature."))
        . '\');else navigator.registerProtocolHandler(\'mailto\',\''
        . Util::addParameter(Horde::applicationUrl('compose.php', true),
                             array('actionID' => 'mailto_link', 'to' => ''), false)
        . '%s\',\'' . $GLOBALS['registry']->get('name') . '\');',
    'desc' => sprintf(_("Click here to open all mailto: links in %s."), $GLOBALS['registry']->get('name')));

// Show Cc: field?
$_prefs['compose_cc'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show the Cc: header field when composing mail?")
);

// Show Bcc: field?
$_prefs['compose_bcc'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show the Bcc: header field when composing mail?")
);

// Check spelling before sending the message?
$_prefs['compose_spellcheck'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Check spelling before sending a message?"));

// confirm successful sending of messages?
$_prefs['compose_confirm'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Display confirmation after sending a message?"));

// allow the user to add a "X-Priority" header when composing messages?
$_prefs['set_priority'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Set the X-Priority header when composing messages?"));

// compose in a separate window?
$_prefs['compose_popup'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Compose messages in a separate window?")
);

// If browser supports the HTML editor, should we compose in HTML mode by
// default?
$_prefs['compose_html'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Compose messages with an HTML GUI by default (if browser supports the feature)?")
);

// The default JS HTML editor.
$_prefs['jseditor'] = array(
    'value' => 'xinha',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    // To use 'fckeditor', you must have Horde 3.2 or greater installed.
    'enum' => array('fckeditor' => _("FCKeditor"),
                    'xinha' => _("Xinha")),
    'desc' => _("The javascript editor to use on the compose page.")
);

// The list of buttons to show in FCKeditor
$_prefs['fckeditor_buttons'] = array(
    'value' => "[['Source','FitWindow','-','Templates'],['Cut','Copy','Paste','PasteText','PasteWord'],['Undo','Redo','-','Find','Replace','-','SelectAll','RemoveFormat'],'/',['OrderedList','UnorderedList','-','Outdent','Indent','Blockquote'],['JustifyLeft','JustifyCenter','JustifyRight','JustifyFull'],['Link','Unlink'],['Image','Flash','Table','Rule','Smiley','SpecialChar'],'/',['Bold','Italic','Underline','StrikeThrough','-','Subscript','Superscript'],['TextColor','BGColor'],'/',['Style','FontFormat','FontName','FontSize']]",
    // Use the following line for a very basic set of buttons:
    // 'value' => "['Bold','Italic','-','OrderedList','UnorderedList','-','Link','Unlink']",
    'locked' => true,
    'shared' => false,
    'type' => 'textarea',
    'desc' => _("The buttons to show when using FCKeditor.")
);

// Hidden Xinha buttons.
$_prefs['xinha_hide_buttons'] = array(
    'value' => 'a:25:{i:0;s:11:"popupeditor";i:1;s:13:"strikethrough";i:2;s:13:"textindicator";i:3;s:9:"subscript";i:4;s:11:"superscript";i:5;s:20:"inserthorizontalrule";i:6;s:11:"insertimage";i:7;s:11:"inserttable";i:8;s:9:"selectall";i:9;s:5:"print";i:10;s:3:"cut";i:11;s:4:"copy";i:12;s:5:"paste";i:13;s:9:"overwrite";i:14;s:6:"saveas";i:15;s:8:"killword";i:16;s:10:"clearfonts";i:17;s:12:"removeformat";i:18;s:13:"toggleborders";i:19;s:10:"splitblock";i:20;s:11:"lefttoright";i:21;s:11:"righttoleft";i:22;s:8:"htmlmode";i:23;s:8:"showhelp";i:24;s:5:"about";}',
    'locked' => false,
    'shared' => false,
    'type' => 'multienum',
    'enum' => array(
        'popupeditor' => _("Maximize/Minimize Editor"),
        'formatblock' => _("Text Format"),
        'fontname' => _("Text Font"),
        'fontsize' => _("Text Size"),
        'bold' => _("Bold"),
        'italic' => _("Italic"),
        'underline' => _("Underline"),
        'strikethrough' => _("Strikethrough"),
        'forecolor' => _("Font Color"),
        'hilitecolor' => _("Background Color"),
        'textindicator' => _("Current style"),
        'subscript' => _("Subscript"),
        'superscript' => _("Superscript"),
        'justifyleft' => _("Justify Left"),
        'justifycenter' => _("Justify Center"),
        'justifyright' => _("Justify Right"),
        'justifyfull' => _("Justify Full"),
        'insertorderedlist' => _("Ordered List"),
        'insertunorderedlist' => _("Bulleted List"),
        'outdent' => _("Decrease Indent"),
        'indent' => _("Increase Indent"),
        'inserthorizontalrule' => _("Horizontal Rule"),
        'createlink' => _("Insert Web Link"),
        'insertimage' => _("Insert/Modify Image"),
        'inserttable' => _("Insert Table"),
        'undo' => _("Undoes your last action"),
        'redo' => _("Redoes your last action"),
        'selectall' => _("Select all"),
        'print' => _("Print document"),
        'cut' => _("Cut selection"),
        'copy' => _("Copy selection"),
        'paste' => _("Paste from clipboard"),
        'overwrite' => _("Insert/Overwrite"),
        'saveas' => _("Save as"),
        'killword' => _("Clear MSOffice tags"),
        'clearfonts' => _("Clear Inline Font Specifications"),
        'removeformat' => _("Remove formatting"),
        'toggleborders' => _("Toggle Borders"),
        'splitblock' => _("Split Block"),
        'lefttoright' => _("Direction left to right"),
        'righttoleft' => _("Direction right to left"),
        'htmlmode' => _("Toggle HTML Source"),
        'showhelp' => _("Help using editor"),
        'about' => _("About this editor")),
    'desc' => _("The buttons NOT to show when using Xinha.")
);

// default outgoing mail domain and address completion
$_prefs['mail_domain'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'text',
    'desc' => _("When sending mail or expanding addresses, what domain should we append to unqualified addresses (email addresses without \"@\")?"));

// Where should the cursor be located in the compose text area by default?
$_prefs['compose_cursor'] = array(
    'value' => 'top',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('top' => _("Top"),
                    'bottom' => _("Bottom"),
                    'sig' => _("Before Signature")),
    'desc' => _("Where should the cursor be located in the compose text area by default?")
);

// Select widget for the possible charsets
$_prefs['sending_charset'] = array(
    'value' => '',
    'locked' => false,
    'shared' => true,
    'type' => 'enum',
    'enum' => array_merge(array('' => _("Default")),
    			  $GLOBALS['nls']['encodings']),
    'desc' => _("Your default charset for sending messages:"));

// Select widget for the 'default_encrypt' preference
$_prefs['encryptselect'] = array('type' => 'special');

// The default encryption method to use when sending messages
$_prefs['default_encrypt'] = array(
    'value' => IMP_ENCRYPT_NONE,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// Save attachments when saving in sent-mail folder?
$_prefs['save_attachments'] = array(
    'value' => 'prompt_no',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('always' => _("Always save attachments"),
                    'prompt_yes' => _("Prompt every time an attachment is sent; default to YES"),
                    'prompt_no' => _("Prompt every time an attachment is sent; default to NO"),
                    'never' => _("Never save attachments")),
    'desc' => _("When saving sent-mail, should we save attachment data?"),
    'help' => 'prefs-save_attachments');

// Disposition Notification Preferences
$_prefs['disposition_request_read'] = array(
    'value' => 'ask',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('never' => _("Never"),
                    'ask' => _("Ask"),
                    'always' => _("Always")),
    'desc' => _("Request read receipts?"),
    'help' => 'prefs-disposition_request_read'
);

// End Message Composition preferences


// Message Replies/Forwards preferences

// Should the original message be included?
$_prefs['reply_quote'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Include original message in a reply?"));

// When replying/forwarding to a message, should we use the same format as the
// original message?
$_prefs['reply_format'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("When replying/forwarding to a message, should we use the same format as the original message?"));

// What should the default forward method be?
$_prefs['forward_default'] = array(
    'value' => 'forward_all',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('forward_all' => _("Entire Message"),
                    'forward_body' => _("Body Text Only"),
                    'forward_attachments' => _("Body Text with Attachments")),
    'desc' => _("Default forwarding method:"),
    'help' => 'message-forward');

// Should the original message be included?
$_prefs['forward_bodytext'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Include body text in forward message by default?"));

// Reply to header summary - leave a brief summary of the header inside
// the message.
$_prefs['reply_headers'] = array(
    'desc' => _("Include a brief summary of the header in a reply?"),
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox');

// How should we attribute quoted lines in a reply
$_prefs['attrib_text'] = array(
    'value' => _("Quoting %f:"),
    'locked' => false,
    'shared' => false,
    'type' => 'text',
    'desc' => _("How to attribute quoted lines in a reply"),
    'help' => 'prefs-attrib_text');

// End Message Replies/Forwards preferences


// Message Drafts preferences

// closing window after saving a draft?
$_prefs['close_draft'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Should the compose window be closed after saving a draft?"));

// save drafts as seen or unseen
$_prefs['unseen_drafts'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Save drafts as unseen?"));

// auto-save drafts? value is in minutes, 0 == don't save.
// Only works w/DIMP - does not show in prefs screen by default
$_prefs['auto_save_drafts'] = array(
    'value' => 5,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(0 => _("No"),
                    5 => _("Every 5 minutes")),
    'desc' => _("Save drafts automatically while composing?"),
);

// End Message Drafts preferences


// Message Viewing preferences

// filter message content?
$_prefs['filtering'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Filter message content for profanity?"));

// Should we display an icon to strip attachments?
$_prefs['strip_attachments'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show an icon to allow stripping of attachments from messages?"));

// What should we do with spam messages after reporting them?
$_prefs['delete_spam_after_report'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(0 => _("Nothing"),
                    1 => _("Delete spam messages")),
    'desc' => _("What should we do with spam messages after they have been reported as spam or innocent?"),
    'help' => 'prefs-delete_spam_after_report'
);
if (!$is_pop3) {
    $_prefs['delete_spam_after_report']['enum'][2] =
        _("Move spam messages to spam folder and innocent messages to INBOX");
}

// Replace image tags in HTML messages with blank images?
$_prefs['html_image_replacement'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Block images in HTML messages unless they are specifically requested?"),
    'help' => 'prefs-html_image_replacement'
);

// By default, automatically show images in HTML messages if the sender is in
// the user's addressbook?
$_prefs['html_image_addrbook'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Automatically show images in HTML messages when the sender is in my address book?"),
    'help' => 'prefs-html_image_addrbook'
);

// should we try to mark different conversations with different colors?
$_prefs['highlight_text'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Mark different levels of quoting with different colors?"));

// should we try to mark simple markup with html tags?
$_prefs['highlight_simple_markup'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Mark simple markup?"));

// should we show large blocks of quoted text or hide them?
$_prefs['show_quoteblocks'] = array(
    'value' => 'thread',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('shown' => _("Shown"),
                    'thread' => _("Hidden in Thread View"),
                    'list' => _("Hidden in List Messages"),
                    'listthread' => _("Hidden in Thread View and List Messages"),
                    'hidden' => _("Hidden")),
    'desc' => _("Should large blocks of quoted text be shown or hidden by default? It can be toggled easily whichever you choose."));

// should we dim signatures?
$_prefs['dim_signature'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Dim signatures?"));

// Convert textual emoticons into graphical ones?
$_prefs['emoticons'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Convert textual emoticons into graphical ones?"));

// how do we display attachments?
$_prefs['attachment_display'] = array(
    'value' => 'list',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('list'   => _("Listing in the Header"),
                    'inline' => _("Display in Body of Message"),
                    'both'   => _("Both Header Listing and Body of Message")),
    'desc' => _("How do you want to display attachments?"));

// Display custom headers (configured via the identity screen) when viewing
// messages?
$_prefs['mail_hdr'] = array(
    'value' => '',
//  'value' => "Message-ID\nX-Spam-Level",
    'locked' => false,
    'shared' => false,
    'type' => 'textarea',
    'desc' => _("Additional headers to display when viewing: <em>(optional, enter each header on a new line)</em>"));

// default message character set
$_prefs['default_msg_charset'] = array(
    'value' => isset($GLOBALS['nls']['emails'][$GLOBALS['language']])
        ? $GLOBALS['nls']['emails'][$GLOBALS['language']]
        : (isset($GLOBALS['nls']['charsets'][$GLOBALS['language']])
            ? $GLOBALS['nls']['charsets'][$GLOBALS['language']]
            : ''),
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array_merge(array('' => _("Default (US-ASCII)")),
                          $GLOBALS['nls']['encodings']),
    'desc' => _("The default charset for messages with no charset information:"),
    'help' => 'prefs-default_msg_charset');

// how do we display alternative mime parts?
$_prefs['alternative_display'] = array(
    'value' => 'none',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array('above'   => _("Above the message text"),
                    'below' => _("Below the message text"),
                    'none'   => _("Not at all")),
    'desc' => _("Where do you want to display links to alternative formats of a message?"));

$_prefs['disposition_send_mdn'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Prompt to send read receipt when requested by the sender?"),
    'help' => 'prefs-disposition_send_mdn'
);

// End Message Viewing preferences


// Deleting and Moving Messages preferences

// should we return to the mailbox listing after deleting a message?
$_prefs['mailbox_return'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Return to the mailbox listing after deleting, moving, or copying a message?"));

// should we move messages to a trash folder instead of just marking
// them as deleted?
$_prefs['use_trash'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("When deleting messages, move them to your Trash folder instead of marking them as deleted?"));

// use Virtual Trash folder
$_prefs['use_vtrash'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// virtual trash folder identifier
$_prefs['vtrash_id'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// display the 'Empty Trash' link in the menubar?
$_prefs['empty_trash_menu'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Display the \"Empty Trash\" link in the menubar?"));

// display the 'Empty Spam' link in the menubar?
$_prefs['empty_spam_menu'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Display the \"Empty Spam\" link in the menubar?"));

// hide deleted
$_prefs['delhide'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// End Deleting and Moving Messages preferences


// New Mail preferences

// time before reloading the navigator or mailbox page
$_prefs['refresh_time'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(0 => _("Never"),
                    30 => _("Every 30 seconds"),
                    60 => _("Every minute"),
                    300 => _("Every 5 minutes"),
                    900 => _("Every 15 minutes"),
                    1800 => _("Every half hour")),
    'desc' => _("Refresh Folder Views:"),
);

// javascript popup if there's new mail?
$_prefs['nav_popup'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Display pop-up notification of new mail?"),
);

// play a sound on new mail? if so, which one?
$_prefs['nav_audio'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit',
);

// sound selection widget
$_prefs['soundselect'] = array('type' => 'special');

// End New Mail preferences


// Message Preview Preferences

$_prefs['preview_enabled'] = array(
    'value' => '0',
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Enable message previews?")
);

$_prefs['preview_maxlen'] = array(
    'value' => 250,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(100 => _("100 characters"),
                    250 => _("250 characters"),
                    500 => _("500 characters"),
                    1000 => _("1000 characters")),
    'desc' => _("Characters to display:")
);

$_prefs['preview_strip_nl'] = array(
    'value' => '1',
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Strip linebreaks?")
);

$_prefs['preview_show_unread'] = array(
    'value' => '1',
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show previews for unread messages only?")
);

$_prefs['preview_show_tooltip'] = array(
    'value' => '0',
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show previews in tooltips?")
);

// End Message Preview


// Fetch Mail preferences

// Change this if you want to customize how fetchmailprefs.php works.
$_prefs['fetchmail_link'] = array(
    'type' => 'link',
    'url' => 'fetchmailprefs.php',
    'img' => 'fetchmail.png',
    'desc' => _("Edit your preferences for accessing other mail accounts."));

// Fetch mail on separate window?
$_prefs['fetchmail_popup'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Fetch Mail in a separate window?"));

// Show the Fetch mail icon on the menubar?
$_prefs['fetchmail_menu'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Show the Fetch Mail icon on the menubar?"));

// Don't change anything here.
$_prefs['fm_accounts'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

$_prefs['fetchmail_login'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// End Fetch Mail preferences


// Display Options preferences

// which page to start on when opening mailbox
$_prefs['mailbox_start'] = array(
    'value' => IMP_MAILBOXSTART_FIRSTUNSEEN,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(IMP_MAILBOXSTART_FIRSTUNSEEN => _("Page with the First Unseen Message"),
                    IMP_MAILBOXSTART_LASTUNSEEN => _("Page with the Last Unseen Message"),
                    IMP_MAILBOXSTART_FIRSTPAGE => _("First Mailbox Page"),
                    IMP_MAILBOXSTART_LASTPAGE => _("Last Mailbox Page")),
    'desc' => _("When opening a new mailbox for the first time, which page do you want to start on?"),
    'help' => 'prefs-mailbox_start');

// default sorting column
$_prefs['sortby'] = array(
    'value' => SORTARRIVAL,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(SORTARRIVAL => _("Arrival Time"),
                    SORTDATE => _("Message Date"),
                    SORTFROM => _("From Address"),
                    SORTTO => _("To Address"),
                    SORTSUBJECT => _("Subject Field"),
                    SORTSIZE => _("Message Size"),
                    SORTTHREAD => _("Thread View")),
    'desc' => _("Default sorting criteria:"));

// default sorting direction
$_prefs['sortdir'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(0 => _("Ascending"),
                    1 => _("Descending")),
    'desc' => _("Default sorting direction:"));

// sort prefs for individual folders
$_prefs['sortpref'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// mailbox constraints
$_prefs['max_msgs'] = array(
    'value' => 20,
    'locked' => false,
    'shared' => false,
    'type' => 'number',
    'desc' => _("Messages per page in the mailbox view."));

// How the from field should be displayed on the mailbox screen
$_prefs['from_link'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(
        0 => _("Clicking on the address will compose a new message to the sender"),
        1 => _("Clicking on the address will open the message to be read"),
        2 => _("Do not generate a link in the From: column")
    ),
    'desc' => _("The From: column of the message should be linked:"));

// Time format for messages dated today
$_prefs['time_format'] = array(
    'value' => '%X',
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(
        '%X' => strftime('%X'),
        '%H:%M:%S' => strftime('%H:%M:%S'),
        '%I:%M:%S %p' => strftime('%I:%M:%S %p'),
        '%H:%M' => strftime('%H:%M'),
        '%I:%M%p' => strftime('%I:%M%p'),
    ),
    'desc' => _("Format of message dates in the mailbox view for messages dated today"));

// expand folder tree by default
$_prefs['nav_expanded'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(0 => _("No"),
                    1 => _("Yes"),
                    2 => _("Remember the last view")),
    'desc' => _("Expand the entire folder tree by default in the folders view?"));

// folder tree view style
$_prefs['tree_view'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(0 => _("Combine all namespaces"),
                    1 => _("Show non-private mailboxes in separate folders")),
    'desc' => _("How should namespaces be displayed in the folder tree view?")
);

// expand folder tree by default in sidebar
$_prefs['nav_expanded_sidebar'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'enum',
    'enum' => array(0 => _("No"),
                    1 => _("Yes"),
                    2 => _("Current expanded status in the folders view")),
    'desc' => _("Expand the entire folder tree by default in the sidebar?"));

// poll all folders for new mail?
$_prefs['nav_poll_all'] = array(
    'value' => false,
    'locked' => isset($_SESSION['imp']) && $_SESSION['imp']['base_protocol'] == 'pop3',
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Poll all folders for new mail?"));

// list of folders to expand by default
$_prefs['expanded_folders'] = array(
    'value' => 'a:0:{}',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// list of folders to poll for new mail
$_prefs['nav_poll'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// End Display Options preferences


// Filter preferences

// run filters on login?
$_prefs['filter_on_login'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// run filters with INBOX display?
$_prefs['filter_on_display'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// run filters when sidebar updates?
$_prefs['filter_on_sidebar'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// show filter icon on the menubar?
$_prefs['filter_menuitem'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// Allow filters to be applied to any mailbox?
$_prefs['filter_any_mailbox'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// End Filter preferences


// Address book preferences

// Should recipients of outgoing messages be added automatically to
// the address book?
$_prefs['save_recipients'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'checkbox',
    'desc' => _("Save recipients automatically to the default address book?"));

// By default, display all contacts in the address book when loading
// the contacts screen.  If your default address book is large and
// slow to display, you may want to disable and lock this option.
$_prefs['display_contact'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => true,
    'type' => 'checkbox',
    'desc' => _("List all contacts when loading the contacts screen? (if disabled, you will only see contacts that you search for explicitly)"));

// address book selection widget
$_prefs['sourceselect'] = array('type' => 'special');

// address book(s) to use when expanding addresses
// You can provide default values this way (note the \t and the double quotes):
// 'value' => "source_one\tsource_two"
// refer to turba/config/sources.php for possible source values
$_prefs['search_sources'] = array(
    'value' => "",
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// field(s) to use when expanding addresses
// This depends on the search_sources preference if you want to provide
// default values:
// 'value' => "source_one\tfield_one\tfield_two\nsource_two\tfield_three"
// will search the fields 'field_one' and 'field_two' in source_one and
// 'field_three' in source_two.
// refer to turba/config/sources.php for possible source and field values
$_prefs['search_fields'] = array(
    'value' => "",
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// address book to use for adding addresses
// put $cfgSources array element name in the value field.
// Setting value to localsql would allow you to add contacts to MySQL database
// See turba/config/sources.php for more info
$_prefs['add_source'] = array(
    'value' => '',
//  'value' => 'localsql',
    'locked' => false,
    'shared' => true,
    'type' => 'implicit'
);

// End Address book preferences


// PGP options

// Activate PGP support?
$_prefs['use_pgp'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit'
);

// You should not manually change the rest of the PGP entries
$_prefs['pgp_attach_pubkey'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

$_prefs['pgp_scan_body'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

$_prefs['pgp_verify'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

$_prefs['pgp_private_key'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

$_prefs['pgp_public_key'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// End PGP Options

// S/MIME options

// Activate S/MIME support?
$_prefs['use_smime'] = array(
    'value' => 0,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// You should not manually change the rest of the S/MIME entries
$_prefs['smime_verify'] = array(
    'value' => 1,
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

$_prefs['smime_private_key'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

$_prefs['smime_public_key'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

$_prefs['smime_additional_cert'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');

// End S/MIME Options

// Other entries (used internally in IMP)

// virtual inbox identifier
$_prefs['vinbox_id'] = array(
    'value' => '',
    'locked' => false,
    'shared' => false,
    'type' => 'implicit');
