<?php
/**
 * DIMP Hooks configuration file.
 *
 * THE HOOKS PROVIDED IN THIS FILE ARE EXAMPLES ONLY.  DO NOT ENABLE THEM
 * BLINDLY IF YOU DO NOT KNOW WHAT YOU ARE DOING.  YOU HAVE TO CUSTOMIZE THEM
 * TO MATCH YOUR SPECIFIC NEEDS AND SYSTEM ENVIRONMENT.
 *
 * For more information please see the horde/config/hooks.php.dist file.
 *
 * $Horde: dimp/config/hooks.php.dist,v 1.8.2.6 2008-05-19 08:24:46 jan Exp $
 */

// This is an example hook function for the DIMP mailbox view. This function
// is called for every message and allows additional information to be added
// to the array that is passed to the mailbox display template -
// dimp/templates/javascript/mailbox.js.  The current entry array is passed
// in, the value returned should be the altered array to use in the
// template. If you are going to add new columns, you also have to update
// dimp/templates/index/index.inc to contain the new field in the header and
// dimp/themes/screen.css to specify the column width.

// if (!function_exists('_dimp_hook_mailboxarray')) {
//     function _dimp_hook_mailboxarray($msg, $ob) {
//         $msg['foo'] = true;
//         return $msg;
//     }
// }

// This is an example hook function for the DIMP message view.  This function
// allows additional information to be added to the array that is passed to
// the message text display template - dimp/templates/chunks/message.html.
// The current entry array is passed in (see the showMessage() function in
// dimp/lib/Views/ShowMessage.php for the format). The value returned should
// be the altered array to use in the template. See the showMessage() function
// in dimp/lib/Views/ShowMessage for the base values contained in the original
// passed-in array.

// if (!function_exists('_dimp_hook_messageview')) {
//     function _dimp_hook_messageview($msg) {
//         // Ex.: Add a new foo variable
//         $msg['foo'] = '<div class="foo">BAR</div>';
//         return $msg;
//     }
// }

// This is an example hook function for the DIMP preview view.  This function
// allows additional information to be added to the preview view and its
// corresponding template - dimp/templates/index/index.inc. The current entry
// array is passed in (see the showMessage() function in
// dimp/lib/Views/ShowMessage.php for the format). Since the preview pane is
// dynamically updated via javascript, all updates other than the base
// entries must be provided in javascript code to be run at update time. The
// expected return is a 2 element array - the first element is the original
// array with any changes made to the initial data. The second element is an
// array of javascript commands, one command per array value.

// if (!function_exists('_dimp_hook_previewview')) {
//     function _dimp_hook_previewview($msg) {
//         // Ex.: Alter the subject
//         $msg['subject'] .= 'test';
//
//         // Ex.: Update the DOM ID 'foo' with the value 'bar'. 'foo' needs
//         //      to be manually added to the HTML template.
//         $js_code = array(
//             "$('foo').update('bar')"
//         );
//
//         return array($msg, $js_code);
//     }
// }

// This is an example hook function for the address formatting in email
// message headers. The argument passed to the function is an object with the
// following possible properties:
// 'address'   -  Full address
// 'host'      -  Host name
// 'inner'     -  Trimmed, bare address
// 'personal'  -  Personal string

// if (!function_exists('_dimp_hook_addressformatting')) {
//     function _dimp_hook_addressformatting($ob) {
//         return empty($ob->personal) ? $ob->address : $ob->personal;
//     }
// }

// This is an example hook function for displaying additional message
// information in the message listing screen for a mailbox.  This example hook
// will add a icon if the message contains attachments and will change the
// display of the message entry based on the X-Priority header.

// if (!function_exists('_dimp_hook_msglist_format')) {
//     function _dimp_hook_msglist_format($mailbox, $uid)
//     {
//         // Required return (array):
//         //   'atc'   - Attachment type (either 'signed', 'encrypted', or
//         //             'attachment').
//         //   'class' - An array of CSS classnames that will be added to
//         //             the row.
//         $ret = array('atc' => '', 'class' => array());
//
//         require_once IMP_BASE . '/lib/IMAP/MessageCache.php';
//         $cache = &IMP_MessageCache::singleton();
//         $cache_entry = $cache->retrieve($mailbox, array($uid), 8 | 32);
//         $ob = reset($cache_entry);
//
//         // Add attachment information
//         require_once IMP_BASE . '/lib/UI/Mailbox.php';
//         $imp_ui = new IMP_UI_Mailbox();
//         $ret['atc'] = $imp_ui->getAttachmentType($ob->structure);
//
//         // Add xpriority information
//         switch ($ob->header->getXpriority()) {
//         case 'high':
//             $ret['class'][] = 'important';
//             break;
//
//         case 'low':
//             $ret['class'][] = 'unimportant';
//             break;
//         }
//
//         return $ret;
//     }
// }
