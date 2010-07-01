<?php
/**
 * $Horde: horde/services/problem.php,v 2.114.8.13 2009-01-06 15:26:20 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

/* Send the browser back to the correct page. */
function _returnToPage()
{
    $url = Util::getFormData('return_url', Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/login.php', true));
    header('Location: ' . str_replace('&amp;', '&', $url));
    exit;
}

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Identity.php';

if (!Horde::showService('problem')) {
    _returnToPage();
}

$identity = &Identity::singleton();
$email = $identity->getValue('from_addr');
if (!$email) {
    $email = Util::getFormData('email', Auth::getAuth());
}
$message = Util::getFormData('message', '');
$name = Util::getFormData('name', $identity->getValue('fullname'));
$subject = Util::getFormData('subject', '');

$actionID = Util::getFormData('actionID');
switch ($actionID) {
case 'send_problem_report':
    if ($subject && $message) {
        /* This is not a gettext string on purpose. */
        $remote = (!empty($_SERVER['REMOTE_HOST'])) ? $_SERVER['REMOTE_HOST'] : $_SERVER['REMOTE_ADDR'];
        $user_agent = $_SERVER['HTTP_USER_AGENT'];
        $body = "This problem report was received from $remote. " .
            "The user clicked the problem report link from the following location:\n" .
            Util::getFormData('return_url', 'No requesting page') .
            "\nand is using the following browser:\n$user_agent\n\n" .
            str_replace("\r\n", "\n", $message);

        /* Default to a relatively reasonable email address. */
        if (!$email) {
            $email = 'horde-problem@' . $conf['problems']['maildomain'];
        }

        /* Check for attachments. */
        $attachment = null;
        if (!empty($conf['problems']['attachments'])) {
            $result = Browser::wasFileUploaded('attachment', _("attachment"));
            if (is_a($result, 'PEAR_Error')) {
                if ($result->getCode() != UPLOAD_ERR_NO_FILE) {
                    $notification->push($result, 'horde.error');
                    break;
                }
            } else {
                $attachment = $_FILES['attachment'];
            }
        }

        if (!empty($conf['problems']['tickets']) &&
            $registry->hasMethod('tickets/addTicket')) {
            $info = array_merge($conf['problems']['ticket_params'],
                                array('summary' => $subject,
                                      'comment' => $body,
                                      'user_email' => $email));
            $result = $registry->call('tickets/addTicket', array($info));
            if (is_a($result, 'PEAR_Error')) {
                $notification->push($result);
            } else {
                if ($attachment &&
                    $registry->hasMethod('tickets/addAttachment')) {
                    $result = $registry->call(
                        'tickets/addAttachment',
                        array('ticket_id' => $result,
                              'name' => $attachment['name'],
                              'data' => file_get_contents($attachment['tmp_name'])));
                    if (is_a($result, 'PEAR_Error')) {
                        $notification->push($result);
                    }
                }
                _returnToPage();
            }
        } else {
            require_once 'Horde/MIME/Mail.php';

            /* Add user's name to the email address if provided. */
            if ($name) {
                @list($mailbox, $host) = @explode('@', $email, 2);
                if (empty($host)) {
                    $host = $conf['problems']['maildomain'];
                }
                $email = MIME::rfc822WriteAddress($mailbox, $host, $name);
            }

            $mail = new MIME_Mail(_("[Problem Report]") . ' ' . $subject,
                                  $body, $conf['problems']['email'], $email,
                                  NLS::getCharset());
            $mail->addHeader('Sender', 'horde-problem@' . $conf['problems']['maildomain']);

            /* Add attachment. */
            if ($attachment) {
                $mail->addAttachment($attachment['tmp_name'],
                                     $attachment['name'],
                                     $attachment['type']);
            }

            $mail_driver = $conf['mailer']['type'];
            $mail_params = $conf['mailer']['params'];
            if ($mail_driver == 'smtp' && $mail_params['auth'] &&
                empty($mail_params['username'])) {
                if (Auth::getAuth()) {
                    $mail_params['username'] = Auth::getAuth();
                    $mail_params['password'] = Auth::getCredential('password');
                } elseif (!empty($conf['problems']['username']) &&
                          !empty($conf['problems']['password'])) {
                    $mail_params['username'] = $conf['problems']['username'];
                    $mail_params['password'] = $conf['problems']['password'];
                }
            }

            if (is_a($sent = $mail->send($mail_driver, $mail_params),
                     'PEAR_Error')) {
                $notification->push($sent);
            } else {
                /* We succeeded. */
                Horde::logMessage(
                    sprintf("%s Message sent to %s from %s",
                            $_SERVER['REMOTE_ADDR'],
                            preg_replace('/^.*<([^>]+)>.*$/', '$1', $conf['problems']['email']),
                            preg_replace('/^.*<([^>]+)>.*$/', '$1', $email)),
                    __FILE__, __LINE__, PEAR_LOG_INFO);

                /* Return to previous page and exit this script. */
                _returnToPage();
            }
        }
    }
    break;

case 'cancel_problem_report':
    _returnToPage();
}

$title = _("Problem Description");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/menu/menu.inc';
$notification->notify(array('listeners' => 'status'));
require HORDE_TEMPLATES . '/problem/problem.inc';
require HORDE_TEMPLATES . '/common-footer.inc';
