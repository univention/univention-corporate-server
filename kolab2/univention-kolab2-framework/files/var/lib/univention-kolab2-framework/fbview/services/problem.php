<?php
/**
 * $Horde: horde/services/problem.php,v 2.107 2004/04/07 14:43:45 chuck Exp $
 *
 * Copyright 1999-2004 Charles J. Hagenbuch <chuck@horde.org>
 * Copyright 1999-2004 Jon Parise <jon@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

/* Send the browser back to the correct page. */
function _returnToPage()
{
    $returnURL = Util::getFormData('return_url', Horde::url($GLOBALS['registry']->getParam('webroot', 'horde') . '/login.php', true));
    header('Location: ' . str_replace('&amp;', '&', $returnURL));
}

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once HORDE_BASE . '/lib/version.php';
require_once 'Horde/Identity.php';

if (!($perms->exists('problem') ?
      $perms->hasPermission('problem', Auth::getAuth(), PERMS_READ) :
      Auth::getAuth())) {
    _returnToPage();
}

$identity = &Identity::singleton();
$email = $identity->getValue('from_addr');
if (empty($email)) {
    $email = Util::getFormData('email', '');
}
if (empty($email)) {
    $email = Auth::getAuth();
}
$message = Util::getFormData('message', '');
$name = Util::getFormData('name', $identity->getValue('fullname'));
$subject = Util::getFormData('subject', '');

$actionID = Util::getFormData('actionID');
switch ($actionID) {
case 'send_problem_report':
    require_once 'Horde/Text.php';

    if (!empty($subject) && !empty($message)) {
        require_once 'Horde/MIME.php';
        require_once 'Horde/MIME/Headers.php';
        require_once 'Horde/MIME/Message.php';

        $msg_headers = &new MIME_Headers();
        $msg_headers->addReceivedHeader();
        $msg_headers->addMessageIdHeader();
        $msg_headers->addAgentHeader();
        $msg_headers->addHeader('Date', date('r'));
        $msg_headers->addHeader('To', $conf['problems']['email']);
        $msg_headers->addHeader('Subject', _("[Problem Report]") . ' ' . $subject);

        if (!empty($email)) {
            if (!empty($name)) {
                list($mailbox, $host) = @explode('@', $email);
                if (empty($host)) {
                    $host = $conf['server']['name'];
                }
                $msg_headers->addHeader('From', MIME::rfc822WriteAddress($mailbox, $host, $name));
            } else {
                $msg_headers->addHeader('From', $email);
            }
            $msg_headers->addHeader('Sender', 'horde-problem@' . $conf['server']['name']);
        } else {
            $msg_headers->addHeader('From', 'horde-problem@' . $conf['server']['name']);
        }
        $recipients = $conf['problems']['email'];

        $message = str_replace("\r\n", "\n", $message);

        // This is not a gettext string on purpose.
        $remote = (!empty($_SERVER['REMOTE_HOST'])) ? $_SERVER['REMOTE_HOST'] : $_SERVER['REMOTE_ADDR'];
        $user_agent = $_SERVER['HTTP_USER_AGENT'];
        $message = "This problem report was received from $remote. " .
            "The user clicked the problem report link from the following location:\n" .
            Util::getFormData('return_url', 'No requesting page') .
            "\nand is using the following browser:\n$user_agent\n\n$message";

        $mime = &new MIME_Message();
        $body = &new MIME_Part('text/plain', Text::wrap($message, 80, "\n"));

        $mime->addPart($body);
        $msg_headers->addMIMEHeaders($mime);

        if (!is_a($mime->send($recipients, $msg_headers), 'PEAR_Error')) {
            /* We succeeded. Return to previous page and exit this script. */
            _returnToPage();
            exit;
        } else {
            $label = _("Describe the Problem");
        }
    } else {
        /* Something wasn't quite right. Strange. */
        $label = _("Describe the Problem");
    }
    break;

case 'cancel_problem_report':
    _returnToPage();
    exit;
    break;
}

if (empty($label)) {
    $label = _("Describe the Problem");
}

$title = _("Problem Description");
$menu = $menu->getMenu();
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/menu/menu.inc';
require HORDE_TEMPLATES . '/problem/problem.inc';
require HORDE_TEMPLATES . '/common-footer.inc';
