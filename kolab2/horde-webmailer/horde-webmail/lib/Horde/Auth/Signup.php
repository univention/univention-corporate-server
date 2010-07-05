<?php

require_once 'Horde/Form.php';
require_once 'Horde/Form/Renderer.php';

/**
 * Auth_Signup:: This class provides an interface to sign up or have
 * new users sign themselves up into the horde installation, depending
 * on how the admin has configured Horde.
 *
 * $Horde: framework/Auth/Auth/Signup.php,v 1.38.2.23 2009-08-13 15:43:57 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_Signup {

    /**
     * Attempts to return a concrete Auth_Signup instance based on $driver.
     *
     * @param string $driver  The type of the concrete Auth_Signup subclass
     *                        to return.  The class name is based on the
     *                        storage driver ($driver).  The code is
     *                        dynamically included.
     * @param array $params   A hash containing any additional configuration or
     *                        connection parameters a subclass might need.
     *
     * @return Auth_Signup  The newly created concrete Auth_Signup
     *                          instance, or false on an error.
     */
    function factory($driver = null, $params = null)
    {
        if ($driver === null) {
            if (!empty($GLOBALS['conf']['signup']['driver'])) {
                $driver = $GLOBALS['conf']['signup']['driver'];
            } else {
                $driver = 'datatree';
            }
        } else {
            $driver = basename($driver);
        }

        if ($params === null) {
            $params = Horde::getDriverConfig('signup', $driver);
        }

        $class = 'Auth_Signup_' . $driver;
        if (!class_exists($class)) {
            include dirname(__FILE__) . '/Signup/' . $driver . '.php';
        }
        if (class_exists($class)) {
            return new $class($params);
        } else {
            return PEAR::raiseError(_("You must configure a backend to use Signups."));
        }
    }

    /**
     * Adds a new user to the system and handles any extra fields that may have
     * been compiled, relying on the hooks.php file.
     *
     * @params mixed $info  Reference to array of parameteres to be passed
     *                      to hook
     *
     * @return mixed  PEAR_Error if any errors, otherwise true.
     */
    function addSignup(&$info)
    {
        global $auth, $conf;

        // Perform any preprocessing if requested.
        if ($conf['signup']['preprocess']) {
            $info = Horde::callHook('_horde_hook_signup_preprocess', array($info));
            if (is_a($info, 'PEAR_Error')) {
                return $info;
            }
        }

        // Check to see if the username already exists.
        if ($auth->exists($info['user_name']) ||
            $this->exists($info['user_name'])) {
            return PEAR::raiseError(sprintf(_("Username \"%s\" already exists."), $info['user_name']));
        }

        // Attempt to add the user to the system.
        $result = $auth->addUser($info['user_name'], array('password' => $info['password']));
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = true;
        // Attempt to add/update any extra data handed in.
        if (!empty($info['extra'])) {
            $result = false;
            $result = Horde::callHook('_horde_hook_signup_addextra',
                                      array($info['user_name'], $info['extra'], $info['password']));
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_EMERG);
                return $result;
            }
        }

        return $result;
    }

    /**
     * Queues the user's submitted registration info for later admin approval.
     *
     * @params mixed $info  Reference to array of parameteres to be passed
     *                      to hook
     *
     * @return mixed  PEAR_Error if any errors, otherwise true.
     */
    function queueSignup(&$info)
    {
        global $auth, $conf;

        // Perform any preprocessing if requested.
        if ($conf['signup']['preprocess']) {
            $info = Horde::callHook('_horde_hook_signup_preprocess',
                                    array($info));
            if (is_a($info, 'PEAR_Error')) {
                return $info;
            }
        }

        // Check to see if the username already exists.
        if ($auth->exists($info['user_name']) ||
            $this->exists($info['user_name'])) {
            return PEAR::raiseError(sprintf(_("Username \"%s\" already exists."), $info['user_name']));
        }

        // If it's a unique username, go ahead and queue the request.
        $signup = $this->newSignup($info['user_name']);
        if (!empty($info['extra'])) {
            $signup->data = array_merge($info['extra'],
                                        array('password' => $info['password'],
                                              'dateReceived' => time()));
        } else {
            $signup->data = array('password' => $info['password'],
                                  'dateReceived' => time());
        }

        $result = $this->_queueSignup($signup);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($conf['signup']['queue']) {
            $result = Horde::callHook('_horde_hook_signup_queued',
                                      array($info['user_name'], $info));
        }

        if (!empty($conf['signup']['email'])) {
            require_once 'Horde/MIME/Mail.php';
            $link = Util::addParameter(Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/admin/signup_confirm.php', true, -1),
                                       array('u' => $signup->name,
                                             'h' => Util::hmac($signup->name, $conf['secret_key'])),
                                       null, false);
            $message = sprintf(_("A new account for the user \"%s\" has been requested through the signup form."), $signup->name)
                . "\n\n"
                . _("Approve the account:")
                . "\n" . Util::addParameter($link, 'a', 'approve') . "\n"
                . _("Deny the account:")
                . "\n" . Util::addParameter($link, 'a', 'deny');
            $mail = new MIME_Mail(
                sprintf(_("Account signup request for \"%s\""), $signup->name),
                $message,
                $conf['signup']['email'],
                $conf['signup']['email'],
                NLS::getCharset());
            list($mail_driver, $mail_params) = Horde::getMailerConfig();
            $result = $mail->send($mail_driver, $mail_params);
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage($result, __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        }
    }

    /**
     * Queues the user's submitted registration info for later admin approval.
     *
     * @params mixed $info  Reference to array of parameteres to be passed
     *                      to hook
     *
     * @return mixed  PEAR_Error if any errors, otherwise true.
     */
    function &_queueSignup(&$info)
    {
        return PEAR::raiseError('Not implemented');
    }

    /**
     * Get a user's queued signup information.
     *
     * @param string $username  The username to retrieve the queued info for.
     *
     * @return object  The bject for the requested signup.
     */
    function getQueuedSignup($username)
    {
        return PEAR::raiseError('Not implemented');
    }

    /**
     * Get the queued information for all pending signups.
     *
     * @return array  An array of objects, one for each signup in the queue.
     */
    function getQueuedSignups()
    {
        return PEAR::raiseError('Not implemented');
    }

    /**
     * Remove a queued signup.
     *
     * @param string $username  The user to remove from the signup queue.
     */
    function removeQueuedSignup($username)
    {
        return PEAR::raiseError('Not implemented');
    }

    /**
     * Return a new signup object.
     *
     * @param string $name  The signups's name.
     *
     * @return object  A new signup object.
     */
    function newSignup($name)
    {
        return PEAR::raiseError('Not implemented');
    }

}

/**
 * Horde Signup Form.
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://opensource.org/licenses/lgpl-license.php.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class HordeSignupForm extends Horde_Form {

    var $_useFormToken = true;

    function HordeSignupForm(&$vars)
    {
        global $registry;

        parent::Horde_Form($vars, sprintf(_("%s Sign Up"), $registry->get('name')));

        $this->setButtons(_("Sign up"), true);

        $this->addHidden('', 'url', 'text', false);

        /* Use hooks get any extra fields required in signing up. */
        $extra = Horde::callHook('_horde_hook_signup_getextra');
        if (!is_a($extra, 'PEAR_Error') && !empty($extra)) {
            if (!isset($extra['user_name'])) {
                $this->addVariable(_("Choose a username"), 'user_name', 'text', true);
            }
            if (!isset($extra['password'])) {
                $this->addVariable(_("Choose a password"), 'password', 'passwordconfirm', true, false, _("type the password twice to confirm"));
            }
            foreach ($extra as $field_name => $field) {
                $readonly = isset($field['readonly']) ? $field['readonly'] : null;
                $desc = isset($field['desc']) ? $field['desc'] : null;
                $required = isset($field['required']) ? $field['required'] : false;
                $field_params = isset($field['params']) ? $field['params'] : array();

                $this->addVariable($field['label'], 'extra[' . $field_name . ']',
                                   $field['type'], $required, $readonly,
                                   $desc, $field_params);
            }
        } else {
            $this->addVariable(_("Choose a username"), 'user_name', 'text', true);
            $this->addVariable(_("Choose a password"), 'password', 'passwordconfirm', true, false, _("type the password twice to confirm"));
        }
    }

    /**
     * Fetch the field values of the submitted form.
     *
     * @param Variables $vars  A Variables instance, optional since Horde 3.2.
     * @param array $info      Array to be filled with the submitted field
     *                         values.
     */
    function getInfo($vars, &$info)
    {
        parent::getInfo($vars, $info);

        if (!isset($info['user_name']) && isset($info['extra']['user_name'])) {
            $info['user_name'] = $info['extra']['user_name'];
        }

        if (!isset($info['password']) && isset($info['extra']['password'])) {
            $info['password'] = $info['extra']['password'];
        }
    }

}
