<?php
/**
 * $Horde: imp/attachment.php,v 2.5.10.22 2008-10-23 16:10:11 slusarz Exp $
 *
 * Copyright 2004-2007 Andrew Coleman <mercury@appisolutions.net>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * This file should be the basis for serving hosted attachments.  It
 * should fetch the file from the VFS and funnel it to the client
 * wishing to download the attachment. This will allow for the
 * exchange of massive attachments without causing mail server havoc.
 */

// Set up initial includes.
// This does *not* include IMP's base.php because we do not need to be
// authenticated to get the file. Most users won't send linked
// attachments just to other IMP users.
if (!defined('HORDE_BASE')) {
    @define('HORDE_BASE', dirname(__FILE__) . '/..');
}
@define('IMP_BASE', dirname(__FILE__));
require_once HORDE_BASE . '/lib/core.php';
require_once IMP_BASE . '/lib/Compose.php';
require_once 'Horde/MIME/Magic.php';
require_once 'VFS.php';
$registry = &Registry::singleton();
$registry->importConfig('imp');

$_self_url = Horde::selfUrl(false, true, true);

// Lets see if we are even able to send the user an attachment.
if (!$conf['compose']['link_attachments']) {
    Horde::fatal(_("Linked attachments are forbidden."), $_self_url, __LINE__);
}

// Gather required form variables.
$mail_user = Util::getFormData('u');
$time_stamp = Util::getFormData('t');
$file_name = Util::getFormData('f');
if (!isset($mail_user) || !isset($time_stamp) || !isset($file_name) ||
    $mail_user == '' || $time_stamp == '' || $file_name == '') {
    Horde::fatal(_("The attachment was not found."),
        $_self_url, __LINE__);
}

// Initialize the VFS.
$vfsroot = &VFS::singleton($conf['vfs']['type'], Horde::getDriverConfig('vfs', $conf['vfs']['type']));
if (is_a($vfsroot, 'PEAR_Error')) {
    Horde::fatal(sprintf(_("Could not create the VFS backend: %s"), $vfsroot->getMessage()), $_self_url, __LINE__);
}

// Check if the file exists.
$mail_user = basename($mail_user);
$time_stamp = basename($time_stamp);
$file_name = escapeshellcmd(basename($file_name));
$full_path = sprintf(IMP_VFS_LINK_ATTACH_PATH . '/%s/%d', $mail_user, $time_stamp);
if (!$vfsroot->exists($full_path, $file_name)) {
    Horde::fatal(_("The specified attachment does not exist. It may have been deleted by the original sender."), $_self_url, __LINE__);
}

// Check to see if we need to send a verification message.
if ($conf['compose']['link_attachments_notify']) {
    if ($vfsroot->exists($full_path, $file_name . '.notify')) {
        $delete_id = Util::getFormData('d');
        $read_id = $vfsroot->read($full_path, $file_name . '.notify');
        if (is_a($read_id, 'PEAR_Error')) {
            Horde::logMessage($read_id, __FILE__, __LINE__, PEAR_LOG_ERR);
        } elseif ($delete_id == $read_id) {
            $vfsroot->deleteFile($full_path, $file_name);
            $vfsroot->deleteFile($full_path, $file_name . '.notify');
            printf(_("Attachment %s deleted."), $file_name);
            exit;
        }
    } else {
        /* Create a random identifier for this file. */
        $id = base_convert($file_name . microtime(), 10, 36);
        $res = $vfsroot->writeData($full_path, $file_name . '.notify' , $id, true);
        if (is_a($res, 'PEAR_Error')) {
            Horde::logMessage($res, __FILE__, __LINE__, PEAR_LOG_ERR);
        } else {
            /* Load $mail_user's preferences so that we can use their
             * locale information for the notification message. */
            include_once 'Horde/Prefs.php';
            $prefs = &Prefs::singleton($conf['prefs']['driver'],
                                       'horde', $mail_user);
            $prefs->retrieve();
            include_once 'Horde/Identity.php';
            $mail_identity = &Identity::singleton('none', $mail_user);
            $mail_address = $mail_identity->getDefaultFromAddress();
            /* Ignore missing addresses, which are returned as <>. */
            if (strlen($mail_address) > 2) {
                $mail_address_full = $mail_identity->getDefaultFromAddress(true);
                NLS::setTimeZone();
                NLS::setLang($prefs->getValue('language'));
                NLS::setTextdomain('imp', IMP_BASE . '/locale', NLS::getCharset());
                String::setDefaultCharset(NLS::getCharset());

                /* Set up the mail headers and read the log file. */
                include_once 'Horde/MIME/Headers.php';
                $msg_headers = new MIME_Headers();
                $msg_headers->addReceivedHeader();
                $msg_headers->addMessageIdHeader();
                $msg_headers->addAgentHeader();
                $msg_headers->addHeader('Date', date('r'));
                $msg_headers->addHeader('From', $mail_address_full);
                $msg_headers->addHeader('To', $mail_address_full);
                $msg_headers->addHeader('Subject', _("Notification: Linked attachment downloaded"));

                include_once 'Horde/MIME/Message.php';
                $msg = new MIME_Message();
                $msg->setType('text/plain');
                $msg->setCharset(NLS::getCharset());
                $msg->setContents(String::wrap(sprintf(_("Your linked attachment has been downloaded by at least one user.\n\nAttachment name: %s\nAttachment date: %s\n\nClick on the following link to permanently delete the attachment:\n%s"), $file_name, date('r', $time_stamp), Util::addParameter(Horde::selfUrl(true, false, true), 'd', $id))));

                $msg_headers->addMIMEHeaders($msg);

                $msg->send($mail_address, $msg_headers);
            }
        }
    }
}

// Find the file's mime-type.
$file_data = $vfsroot->read($full_path, $file_name);
if (is_a($file_data, 'PEAR_Error')) {
    Horde::logMessage($file_data, __FILE__, __LINE__, PEAR_LOG_ERR);
    Horde::fatal(_("The specified file cannot be read."), $_self_url, __LINE__);
}
$mime_type = MIME_Magic::analyzeData($file_data, isset($conf['mime']['magic_db']) ? $conf['mime']['magic_db'] : null);
if ($mime_type === false) {
    $mime_type = MIME_Magic::filenameToMIME($file_name, false);
}

// Prevent 'jar:' attacks on Firefox.  See Ticket #5892.
if ($browser->isBrowser('mozilla')) {
    if (in_array(String::lower($mime_type), array('application/java-archive', 'application/x-jar'))) {
        $mime_type = 'application/octet-stream';
    }
}

// Send the client the file.
$browser->downloadHeaders($file_name, $mime_type, false, strlen($file_data));
echo $file_data;
