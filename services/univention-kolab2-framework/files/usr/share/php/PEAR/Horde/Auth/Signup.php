<?php

require_once 'Horde/DataTree.php';
require_once 'Horde/Form.php';
require_once 'Horde/Form/Renderer.php';

/**
 * Auth_Signup:: This class provides an interface to sign up or have
 * new users sign themselves up into the horde installation, depending
 * on how the admin has configured Horde.
 *
 * $Horde: framework/Auth/Auth/Signup.php,v 1.32 2004/04/07 14:43:05 chuck Exp $
 *
 * Copyright 2002-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class Auth_Signup {

    /**
     * Pointer to a DataTree instance to manage/store signups
     *
     * @var object DataTree $_datatree
     */
    var $_datatree;

    function Auth_Signup()
    {
        global $conf;

        if (!isset($conf['datatree']['driver'])) {
            Horde::fatal(_("You must configure a DataTree backend to use Signups."));
        }
        $driver = $conf['datatree']['driver'];
        $this->_datatree = &DataTree::singleton($driver,
                                                array_merge(Horde::getDriverConfig('datatree', $driver),
                                                            array('group' => 'horde.signup')));
    }

    /**
     * Attempts to return a reference to a concrete Auth_Signup
     * instance. It will only create a new instance if no Auth_Signup
     * instance currently exists.
     *
     * This method must be invoked as: $var = &Auth_Signup::singleton()
     *
     * @return object Signup  The concrete Signup reference, or false on an
     *                        error.
     */
    function &singleton()
    {
        static $signup;

        if (!isset($signup)) {
            $signup = new Auth_Signup();
        }

        return $signup;
    }

    /**
     * Adds a new user to the system and handles any extra fields
     * that may have been compiled, relying on the hooks.php file.
     *
     * @access public
     *
     * @return mixed  PEAR_Error if any errors, otherwise true.
     */
    function addSignup(&$info)
    {
        global $auth, $conf;

        // Perform any preprocessing if requested
        if ($conf['signup']['preprocess']) {
            $info = Horde::callHook('_horde_hook_signup_preprocess', array($info));
            if (is_a($info, 'PEAR_Error')) {
                return $info;
            }
        }

        // Attempt to add the user to the system
        $success = $auth->addUser($info['user_name'], array('password' => $info['password']));
        if (is_a($success, 'PEAR_Error')) {
            return $success;
        }

        // Attempt to add/update any extra data handed in
        if (!empty($info['extra'])) {
            $added = false;
            $added = Horde::callHook('_horde_hook_signup_addextra',
                                     array($info['user_name'], $info['extra']));
            if (!$added || is_a($added, 'PEAR_Error')) {
                Horde::logMessage($added, __FILE__, __LINE__, PEAR_LOG_EMERG);
                Horde::fatal(new PEAR_Error(_("Unable to add extra user information when signing up.")), __FILE__, __LINE__);
            }
        }

        return true;
    }

    /**
     * Queues the user's submitted registration info for later admin
     * approval.
     *
     * @access public
     *
     * @return mixed  PEAR_Error if any errors, otherwise true.
     */
    function &queueSignup(&$info)
    {
        global $auth,$conf;

        // Perform any preprocessing if requested
        if ($conf['signup']['preprocess']) {
            $info = Horde::callHook('_horde_hook_signup_preprocess',
                                    array($info));
            if (is_a($info, 'PEAR_Error')) {
                return $info;
            }
        }

        // Check to see if the username already exists
        if ($auth->exists($info['user_name']) ||
            $this->_datatree->exists($info['user_name'])) {
            return PEAR::raiseError(sprintf(_("Username '%s' already exists."), $info['user_name']));
        }

        // If it's a unique username, go ahead and queue the request
        $signup = $this->newSignup($info['user_name']);
        if (!empty($info['extra'])) {
            $signup->data = array_merge($info['extra'],
                                        array('password' => $info['password'],
                                              'dateReceived' => time()));
        } else {
            $signup->data = array('password' => $info['password'],
                                  'dateReceived' => time());
        }

        if ($conf['signup']['queue']) {
            $result = Horde::callHook('_horde_hook_signup_queued',
                                      array($info['user_name'], $info));
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        return $this->_datatree->add($signup);
    }

    /**
     * Get a user's queued signup information.
     *
     * @access public
     *
     * @param string $username  The username to retrieve the queued info for.
     * @return object DataTreeObject_Signup  The DataTreeObject for the
     *                                       requested signup.
     */
    function getQueuedSignup($username)
    {
        return $this->_datatree->getObject($username, 'DataTreeObject_Signup');
    }

    /**
     * Get the queued information for all pending signups.
     *
     * @access public
     *
     * @return array  An array of DataTreeObject_Signup objects, one for
     *                each signup in the queue.
     */
    function getQueuedSignups()
    {
        $signups = array();
        foreach ($this->_datatree->get(DATATREE_FORMAT_FLAT, -1, true) as $username) {
            if ($username != -1) {
                $signups[] = $this->_datatree->getObject($username);
            }
        }
        return $signups;
    }

    /**
     * Remove a queued signup.
     *
     * @access public
     *
     * @param string $username  The user to remove from the signup queue.
     */
    function removeQueuedSignup($username)
    {
        $this->_datatree->remove($username);
    }

    /**
     * Return a new signup object.
     *
     * @param string $name The signups's name.
     *
     * @return object DataTreeObject_Signup A new signup object.
     */
    function &newSignup($name)
    {
        if (empty($name)) {
            return PEAR::raiseError('Signup names must be non-empty');
        }
        return $ret = &new DataTreeObject_Signup($name);
    }

}

/**
 * Extension of the DataTreeObject class for storing Signup
 * information in the DataTree driver. If you want to store
 * specialized Signup information, you should extend this class
 * instead of extending DataTreeObject directly.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class DataTreeObject_Signup extends DataTreeObject {

    /**
     * We want to see queued signups in descending order of receipt.
     * Insert new signups at position 0 and push the rest down.
     * @var integer $order
     */
    var $order = 0;

    /**
     * The DataTreeObject_Signup constructor. Just makes sure to call
     * the parent constructor so that the signup's is is set
     * properly.
     *
     * @param string $id The id of the signup.
     */
    function DataTreeObject_Signup($id)
    {
        parent::DataTreeObject($id);
        if (is_null($this->data)) {
            $this->data = array();
        }
    }

}

/**
 * Horde Signup Form, extending of Horde_Form::
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (GPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class HordeSignupForm extends Horde_Form {

    var $_useFormToken = true;

    function HordeSignupForm(&$vars)
    {
        global $registry;

        parent::Horde_Form($vars, sprintf(_("%s Sign Up"), $registry->getParam('name')));

        $this->setButtons(_("Sign up"), true);

        $this->addHidden('', 'url', 'text', false);
        $this->addVariable(_("Choose a username"), 'user_name', 'text', true);
        $this->addVariable(_("Choose a password"), 'password', 'passwordconfirm', true, false, _("type the password twice to confirm"));

        /* Use hooks get any extra fields required in signing up. */
        $extra = Horde::callHook('_horde_hook_signup_getextra');
        if (!is_a($extra, 'PEAR_Error') && !empty($extra)) {
            foreach ($extra as $field_name => $field) {
                $readonly = isset($field['readonly']) ? $field['readonly'] : null;
                $desc = isset($field['desc']) ? $field['desc'] : null;
                $required = isset($field['required']) ? $field['required'] : false;
                $field_params = isset($field['params']) ? $field['params'] : array();

                $this->addVariable($field['label'], 'extra[' . $field_name . ']',
                                   $field['type'], $required, $readonly,
                                   $desc, $field_params);
            }
        }
    }

}
