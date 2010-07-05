<?php
/**
 * $Horde: horde/services/changepassword.php,v 1.1.2.6 2009-01-06 15:26:20 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Jason Felice <jason.m.felice@gmail.com>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Form.php';
require_once 'Horde/Form/Renderer.php';
require_once 'Horde/Variables.php';

if (!Auth::isAuthenticated()) {
    Horde::authenticationFailureRedirect();
}

// Make sure auth backend allows passwords to be reset.
$auth = &Auth::singleton($conf['auth']['driver']);
if (!$auth->hasCapability('update')) {
    $notification->push(_("Changing your password is not supported with the current configuration.  Contact your administrator."), 'horde.error');
    header('Location: ' . Auth::getLoginScreen('', Util::getFormData('url')));
    exit;
}

$vars = Variables::getDefaultVariables();

$title = _("Change Your Password");
$form = new Horde_Form($vars, $title);
$form->setButtons(_("Continue"));

$form->addHidden('', 'return_to', 'text', false);
$form->addVariable(_("Old password"), 'old_password', 'password', true);
$form->addVariable(_("New password"), 'password_1', 'password', true);
$form->addVariable(_("Retype new password"), 'password_2', 'password', true);

if ($vars->exists('formname')) {
    $form->validate($vars);
    if ($form->isValid()) {
        $form->getInfo($vars, $info);
        do {
            if ($auth->getCredential('password') != $info['old_password']) {
                $notification->push(_("Old password is not correct."),
                                    'horde.error');
                break;
            }

            if ($info['password_1'] != $info['password_2']) {
                $notification->push(_("New passwords don't match."),
                                    'horde.error');
                break;
            }

            if ($info['old_password'] == $info['password_1']) {
                $notification->push(_("Old and new passwords must be different."), 'horde.error');
                break;
            }

            /* FIXME: Need to clean up password policy patch and commit before
             * enabling this... -JMF

            $res = Auth::testPasswordStrength($info['password_1'],
                                              $conf['auth']['password_policy']);
            if (is_a($res, 'PEAR_Error')) {
                $notification->push($res->getMessage(), 'horde.error');
                break;
            }
            */

            $res = $auth->updateUser(Auth::getAuth(), Auth::getAuth(),
                                     array('password' => $info['password_1']));
            if (is_a($res, 'PEAR_Error')) {
                $notification->push(sprintf(_("Error updating password: %s"),
                                            $res->getMessage()),
                                    'horde.error');
                break;
            }

            $notification->push(_("Password changed successfully."),
                                'horde.success');
            if (!empty($info['return_to'])) {
                header('Location: ' . $info['return_to']);
                exit;
            }
            break;
        } while (false);
    }
}

$vars->remove('old_password');
$vars->remove('password_1');
$vars->remove('password_2');

require HORDE_TEMPLATES . '/common-header.inc';
$notification->notify(array('listeners' => 'status'));
$renderer = new Horde_Form_Renderer();
$form->renderActive($renderer, $vars, 'changepassword.php', 'post');
require HORDE_TEMPLATES . '/common-footer.inc';
