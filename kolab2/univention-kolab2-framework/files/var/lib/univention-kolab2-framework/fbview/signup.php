<?php
/**
 * $Horde: horde/signup.php,v 1.17 2004/04/07 14:43:00 chuck Exp $
 *
 * Copyright 2002-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__));
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Auth/Signup.php';
require_once 'Horde/Variables.php';

// Make sure signups are enabled before proceeding
if ($conf['signup']['allow'] !== true) {
    $notification->push(_("User Registration has been disabled for this site."), 'horde.error');
    header('Location: ' . Auth::getLoginScreen());
    exit;
}

$auth = &Auth::singleton($conf['auth']['driver']);
$signup = &Auth_Signup::singleton();

$renderer = &new Horde_Form_Renderer();

$vars = &Variables::getDefaultVariables();

$formsignup = &Horde_Form::singleton('HordeSignupForm', $vars);
$formsignup->validate($vars);

if ($vars->get('formname') != 'hordesignupform') {
    /* Not yet submitted. */
    $formsignup->clearValidation();
}

if ($formsignup->isValid() && $vars->get('formname') == 'hordesignupform') {
    $formsignup->getInfo($vars, $info);

    if ($auth->hasCapability('add')) {
        if (!$conf['signup']['approve']) {
            /* User can sign up directly, no intervention necessary. */
            $success = $signup->addSignup($info);
            $success_message = sprintf(_("Added '%s' to the system. You can log in now."), $info['user_name']);
        } elseif ($conf['signup']['approve']) {
            /* Insert this user into a queue for admin approval. */
            $success = $signup->queueSignup($info);
            $success_message = sprintf(_("Submitted request to add '%s' to the system. You can not log in until your request has been approved."), $info['user_name']);
        }
    }

    if (is_a($success, 'PEAR_Error')) {
        $notification->push(sprintf(_("There was a problem adding '%s' to the system. %s."), $info['user_name'], $success->getMessage()), 'horde.error');
    } else {
        $notification->push($success_message, 'horde.success');
        $url = Auth::getLoginScreen('', $info['url']);
        header('Location: ' . $url);
        exit;
    }
}

$title = _("User Registration");
require HORDE_TEMPLATES . '/common-header.inc';
$notification->notify(array('listeners' => 'status'));
$formsignup->renderActive($renderer, $vars, 'signup.php', 'post');
require HORDE_TEMPLATES . '/common-footer.inc';
