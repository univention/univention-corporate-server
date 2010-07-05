<?php
/**
 * $Horde: horde/admin/signup_confirm.php,v 1.1.2.1 2009-06-15 16:01:22 jan Exp $
 *
 * Copyright 2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Auth/Signup.php';

// Make sure signups are enabled before proceeding
$auth = &Auth::singleton($conf['auth']['driver']);
if ($conf['signup']['allow'] !== true ||
    !$auth->hasCapability('add')) {
    Horde::fatal(_("User Registration has been disabled for this site."), __FILE__, __LINE__);
}
$signup = Auth_Signup::factory();
if (is_a($signup, 'PEAR_Error')) {
    Horde::logMessage($signup, __FILE__, __LINE__, PEAR_LOG_ERR);
    Horde::fatal(_("User Registration is not properly configured for this site."), __FILE__, __LINE__);
}

// Verify hash.
$user = Util::getFormData('u');
$hash = Util::getFormData('h');
$action = Util::getFormData('a');
if (Util::hmac($user, $conf['secret_key']) != $hash) {
    Horde::fatal(_("Invalid hash."), __FILE__, __LINE__);
}

// Deny signup.
if ($action == 'deny') {
    $result = $signup->removeQueuedSignup($user);
    if (is_a($result, 'PEAR_Error')) {
        Horde::fatal($result, __FILE__, __LINE__);
    }
    printf(_("The signup request for user \"%s\" has been removed."), $user);
    exit;
}
if ($action != 'approve') {
    Horde::fatal(sprintf(_("Invalid action %s"), $action), __FILE__, __LINE__);
}

// Read and verify user data.
$thisSignup = $signup->getQueuedSignup($user);
$info = $thisSignup->getData();

if (empty($info['user_name']) && isset($info['extra']['user_name'])) {
    $info['user_name'] = $info['extra']['user_name'];
}
if (empty($info['password']) && isset($info['extra']['password'])) {
    $info['password'] = $info['extra']['password'];
}
if (empty($info['user_name'])) {
    Horde::fatal(_("No username specified."), __FILE__, __LINE__);
}
if ($auth->exists($info['user_name'])) {
    Horde::fatal(sprintf(_("The user \"%s\" already exists."), $info['user_name']), __FILE__, __LINE__);
}

$credentials = array('password' => $info['password']);
if (isset($info['extra'])) {
    foreach ($info['extra'] as $field => $value) {
        $credentials[$field] = $value;
    }
}

// Add user.
if (is_a($ret = $auth->addUser($info['user_name'], $credentials), 'PEAR_Error')) {
    Horde::fatal(sprintf(_("There was a problem adding \"%s\" to the system: %s"), $info['user_name'], $ret->getMessage()), __FILE__, __LINE__);
}
if (isset($info['extra'])) {
    $result = Horde::callHook('_horde_hook_signup_addextra',
                              array($info['user_name'], $info['extra']));
    if (is_a($result, 'PEAR_Error')) {
        Horde::fatal(sprintf(_("Added \"%s\" to the system, but could not add additional signup information: %s."), $info['user_name'], $result->getMessage()), __FILE__, __LINE__);
    }
}
$signup->removeQueuedSignup($info['user_name']);

echo sprintf(_("Successfully added \"%s\" to the system."), $info['user_name']);
