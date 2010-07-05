<?php
/**
 * $Horde: horde/signup.php,v 1.17.10.16 2009-01-06 15:13:50 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Marko Djukic <marko@oblo.com>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__));
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Auth/Signup.php';
require_once 'Horde/Variables.php';

$auth = &Auth::singleton($conf['auth']['driver']);

// Make sure signups are enabled before proceeding
if ($conf['signup']['allow'] !== true ||
    !$auth->hasCapability('add')) {
    $notification->push(_("User Registration has been disabled for this site."), 'horde.error');
    header('Location: ' . Auth::getLoginScreen());
    exit;
}

$signup = Auth_Signup::factory();
if (is_a($signup, 'PEAR_Error')) {
    Horde::logMessage($signup->getMessage(), __FILE__, __LINE__, PEAR_LOG_ERR);
    $notification->push(_("User Registration is not properly configured for this site."), 'horde.error');
    header('Location: ' . Auth::getLoginScreen());
    exit;
}

$vars = Variables::getDefaultVariables();
$formsignup = new HordeSignupForm($vars);
if ($formsignup->validate()) {
    $formsignup->getInfo($vars, $info);
    $success_message = null;

    if (!$conf['signup']['approve']) {
        /* User can sign up directly, no intervention necessary. */
        $success = $signup->addSignup($info);
        if (!is_a($success, 'PEAR_Error')) {
            $success_message = sprintf(_("Added \"%s\" to the system. You can log in now."), $info['user_name']);
        }
    } elseif ($conf['signup']['approve']) {
        /* Insert this user into a queue for admin approval. */
        $success = $signup->queueSignup($info);
        if (!is_a($success, 'PEAR_Error')) {
            $success_message = sprintf(_("Submitted request to add \"%s\" to the system. You cannot log in until your request has been approved."), $info['user_name']);
        }
    }

    if (is_a($info, 'PEAR_Error')) {
        $notification->push(sprintf(_("There was a problem adding \"%s\" to the system: %s"), $vars->get('user_name'), $info->getMessage()), 'horde.error');
    } elseif (is_a($success, 'PEAR_Error')) {
        $notification->push(sprintf(_("There was a problem adding \"%s\" to the system: %s"), $info['user_name'], $success->getMessage()), 'horde.error');
    } else {
        $notification->push($success_message, 'horde.success');
        $url = Auth::getLoginScreen('', $info['url']);
        header('Location: ' . $url);
        exit;
    }
}

$title = _("User Registration");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/login/header.inc';
$notification->notify(array('listeners' => 'status'));
$formsignup->renderActive($formsignup->getRenderer(), $vars, 'signup.php', 'post');
require HORDE_TEMPLATES . '/common-footer.inc';
