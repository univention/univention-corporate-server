<?php
/**
 * $Horde: horde/services/resetpassword.php,v 1.4 2004/05/25 08:50:29 mdjukic Exp $
 *
 * Copyright 2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Form.php';
require_once 'Horde/Variables.php';

// Make sure auth backend allows passwords to be reset.
$auth = &Auth::singleton($conf['auth']['driver']);
if (!$auth->hasCapability('resetpassword')) {
    $notification->push(_("Can not reset password automatically, contact your administrator."), 'horde.error');
    header('Location: ' . Auth::getLoginScreen('', Util::getFormData('url')));
    exit;
}

$vars = &Variables::getDefaultVariables();

$title = _("Reset Your Password");
$form = &Horde_Form::singleton('HordeSignupForm', $vars, $title);
$form->setButtons(_("Continue"));

/* Set up the fields for the username and alternate email. */
$form->addHidden('', 'url', 'text', false);
$v = &$form->addVariable(_("Username"), 'username', 'text', true);
$v->setOption('trackchange', true);
$form->addVariable(_("Alternate email address"), 'email', 'email', true);
$can_validate = false;

/* If a username has been supplied try fetching the prefs stored info. */
if ($username = $vars->get('username')) {
    $prefs = &Prefs::singleton($conf['prefs']['driver'], 'horde', $username, '', null, false);
    $prefs->retrieve();
    $email = $prefs->getValue('alternate_email');
    /* Does the alternate email stored in prefs match the one submitted? */
    if ($vars->get('email') == $email) {
        $can_validate = true;
        $form->setButtons(_("Reset Password"));
        $question = $prefs->getValue('security_question');
        $form->addVariable($question, 'question', 'description', false);
        $form->addVariable(_("Answer"), 'answer', 'text', true);
    } else {
        $notification->push(_("Incorrect username or alternate address. Try again or contact your administrator if you need further help."), 'horde.error');
    }
}

/* Validate the form. */
if ($can_validate && $form->validate($vars)) {
    $form->getInfo($vars, $info);

    /* Fetch values from prefs for selected user. */
    $answer = $prefs->getValue('security_answer');

    /* Check the given values witht the prefs stored ones. */
    require_once 'Horde/String.php';
    if ($email == $info['email'] && String::lower($answer) == String::lower($info['answer'])) {
        /* Info matches, so reset the password. */
        $password = $auth->resetPassword($info['username']);

        require_once 'Mail.php';
        $mailer = &Mail::factory($conf['mailer']['type'], $conf['mailer']['params']);

        /* Set up the email headers and body. */
        $headers['From'] = $email;
        $headers['To'] = $email;
        $recipients[] = $headers['To'];
        $headers['Subject'] = _("Your password has been reset");
        $body = sprintf(_("Your new password for %s is: %s"), $registry->getParam('name', 'horde'), $password);
        $mailer->send($recipients, $headers, $body);

        $notification->push(_("Your password has been reset, check your email and log in with your new password."), 'horde.success');
        header('Location: ' . Auth::getLoginScreen('', $info['url']));
        exit;
    } else {
        /* Info submitted does not match what is in prefs, redirect user back
         * to login. */
        $notification->push(_("Could not reset the password for the requested user. Some or all of the details are not correct. Try again or contact your administrator if you need further help."), 'horde.error');
    }
}

require HORDE_TEMPLATES . '/common-header.inc';
$notification->notify(array('listeners' => 'status'));
require_once 'Horde/Form/Renderer.php';
$renderer = &new Horde_Form_Renderer();
$form->renderActive($renderer, $vars, 'resetpassword.php', 'post');
require HORDE_TEMPLATES . '/common-footer.inc';
