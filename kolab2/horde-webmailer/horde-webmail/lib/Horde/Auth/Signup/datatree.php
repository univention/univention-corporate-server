<?php

require_once 'Horde/DataTree.php';

/**
 * Auth_Signup:: This class provides an interface to sign up or have
 * new users sign themselves up into the horde installation, depending
 * on how the admin has configured Horde.
 *
 * $Horde: framework/Auth/Auth/Signup/datatree.php,v 1.1.2.4 2009-11-17 14:17:41 mrubinsk Exp $
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
class Auth_Signup_datatree extends Auth_Signup {

    /**
     * Pointer to a DataTree instance to manage/store signups
     *
     * @var DataTree
     */
    var $_datatree;

    function Auth_Signup_datatree()
    {
        global $conf;

        if (empty($conf['datatree']['driver'])) {
            Horde::fatal(_("You must configure a DataTree backend to use Signups."), __FILE__, __LINE__);
        }
        $driver = $conf['datatree']['driver'];
        $this->_datatree = &DataTree::singleton($driver,
                                                array_merge(Horde::getDriverConfig('datatree', $driver),
                                                            array('group' => 'horde.signup')));
    }

    /**
     * Stores the signup data in the backend.
     *
     * @params DataTreeObject_Signup $signup  Signup data.
     */
    function _queueSignup($signup)
    {
        return $this->_datatree->add($signup);
    }

    /**
     * Get a user's queued signup information.
     *
     * @param string $username  The username to retrieve the queued info for.
     *
     * @return DataTreeObject_Signup  The DataTreeObject for the requested
     *                                signup.
     */
    function getQueuedSignup($username)
    {
        return $this->_datatree->getObject($username, 'DataTreeObject_Signup');
    }

    /**
     * Get the queued information for all pending signups.
     *
     * @return array  An array of DataTreeObject_Signup objects, one for
     *                each signup in the queue.
     */
    function getQueuedSignups()
    {
        $signups = array();
        foreach ($this->_datatree->get(DATATREE_FORMAT_FLAT, DATATREE_ROOT, true) as $username) {
            if ($username != DATATREE_ROOT) {
                $signups[] = $this->_datatree->getObject($username);
            }
        }
        return $signups;
    }

    /**
     * Remove a queued signup.
     *
     * @param string $username  The user to remove from the signup queue.
     */
    function removeQueuedSignup($username)
    {
        $this->_datatree->remove($username);
    }

    /**
     * See if an existing request exists.
     *
     * @param string $name  The signup name.
     *
     * @return boolean
     */
    function exists($name)
    {
        return $this->_datatree->exists($name);
    }
    
    /**
     * Return a new signup object.
     *
     * @param string $name  The signups's name.
     *
     * @return DataTreeObject_Signup  A new signup object.
     */
    function newSignup($name)
    {
        if (empty($name)) {
            return PEAR::raiseError('Signup names must be non-empty');
        }
        return new DataTreeObject_Signup($name);
    }

}

/**
 * Extension of the DataTreeObject class for storing Signup
 * information in the DataTree driver. If you want to store
 * specialized Signup information, you should extend this class
 * instead of extending DataTreeObject directly.
 *
 * @author  Marko Djukic <marko@oblo.com>
 * @since   Horde 3.0
 * @package Horde_Auth
 */
class DataTreeObject_Signup extends DataTreeObject {

    /**
     * We want to see queued signups in descending order of receipt.
     * Insert new signups at position 0 and push the rest down.
     *
     * @var integer
     */
    var $order = 0;

    /**
     * The DataTreeObject_Signup constructor. Just makes sure to call
     * the parent constructor so that the signup's is is set
     * properly.
     *
     * @param string $id  The id of the signup.
     */
    function DataTreeObject_Signup($id)
    {
        parent::DataTreeObject($id);
        if (is_null($this->data)) {
            $this->data = array();
        }
    }

}
