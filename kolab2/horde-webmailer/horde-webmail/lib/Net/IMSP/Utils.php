<?php
require_once 'Net/IMSP.php';
/**
 * Net_IMSP_Utils::
 *
 * $Horde: framework/Net_IMSP/IMSP/Utils.php,v 1.3.10.11 2009-01-06 15:23:27 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Michael Rubinsky <mrubinsk@horde.org>
 * @package Net_IMSP
 */
class Net_IMSP_Utils {

    /**
     * Utility function to retrieve the names of all the address books
     * that the user has access to, along with the acl for those
     * books.  For information about the $serverInfo array see
     * turba/config/sources.php as this is the cfgSources[] entry for
     * the address books.
     *
     * @param array $serverInfo  Information about the server
     *                           and the current user.
     *
     * @return array  Information about all the address books or PEAR_Error.
     */
    function getAllBooks($serverInfo)
    {
        $foundDefault = false;
        $results = array();
        $imsp = &Net_IMSP::singleton('Book', $serverInfo['params']);
        $result = $imsp->init();

        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $books = $imsp->getAddressBookList();
        if (is_a($books, 'PEAR_Error')) {
            return $books;
        }
        $bCount = count($books);
        for ($i = 0; $i < $bCount; $i++) {
            $newBook = $serverInfo;
            if ($books[$i] != $serverInfo['params']['username']) {
                $newBook['title'] = $books[$i];
                // We need the 'name' param to store the IMSP
                // address book name when not using shares (for BC).
                $newBook['params']['name'] = $books[$i];
                $newBook['params']['is_root'] = false;
                $newBook['params']['my_rights'] = $imsp->myRights($books[$i]);
            } else {
                $foundDefault = true;
                $newBook['params']['my_rights'] = $imsp->myRights($books[$i]);
            }
            $results[] = $newBook;
        }

        /* If there is no default address book (named username) then we should create one. */
        if (!$foundDefault) {
            $result = $imsp->createAddressBook($serverInfo['params']['username']);
            if (is_a($result, 'PEAR_Error')) {
                return PEAR::raiseError('Login to IMSP host failed.' .
                                        ': Default address book is missing and could not be created.');
            }
        }
        return $results;
    }

    /**
     * Utility function to make it easier for client applications to delete
     * address books without having to create imsp drivers.  The $source array
     * is a horde/turba style $cfgSources entry for the address book being
     * deleted.
     *
     * @param array $source  Information about the address book being deleted.
     *
     * @return mixed  True on success or PEAR_Error on failure.
     */
    function deleteBook($source)
    {
        if (is_array($source)) {
            // Not using shares
            $params = $source['params'];
            $bookName = $source['title'];
        } else {
            // Using shares.
            $params = $GLOBALS['cfgSources']['imsp:' . $source]['params'];
            $bookName = $source;
        }
        $imsp = &Net_IMSP::singleton('Book', $params);
        $result = $imsp->init();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $imsp->deleteAddressBook($bookName);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return true;
    }

    /**
     * Utility function to help clients create new address books without having
     * to create an imsp driver instance first.
     *
     * @param array $source    Information about the user's default IMSP
     *                         address book.
     * @param string $newName  The name of the new address book.
     *
     * @return mixed  true on success or PEAR_Error on failure.
     */
    function createBook($source, $newName)
    {
        $imsp = &Net_IMSP::singleton('Book', $source['params']);
        $result = $imsp->init();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        // We now check if the username is already prepended to
        // the address book name or not.
        if (strpos($newName, $source['params']['username'] . '.') === 0) {
            $name = $newName;
        } else {
            $name = $source['params']['username'] . '.' . $newName;
        }
        $result = $imsp->createAddressBook($name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return true;
    }

    /**
     * Synchronize Horde_Shares to existing IMSP address books.
     *
     * @param Horde_Share $share_obj  The Horde_Share object to use.
     * @param array $serverInfo       Information about the IMSP server and
     *                                the current user.
     *
     * @return mixed  Array describing any shares added or removed  | PEAR_Error.
     * @since Horde 3.2
     */
    function synchShares(&$share_obj, $serverInfo)
    {
        $found_shares = array();
        $return = array('added' => array(), 'removed' => array());
        $params = array();

        $imsp = &Net_IMSP::singleton('Book', $serverInfo['params']);
        $result = $imsp->init();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        $abooks = $imsp->getAddressBookList();
        if (is_a($abooks, 'PEAR_Error')) {
            return $abooks;
        }

        // Do we have a default address book? If not, create one.
        if (array_search($serverInfo['params']['username'], $abooks) === false) {
            $result = $imsp->createAddressbook($serverInfo['params']['username']);
            if (!is_a($result, 'PEAR_Error')) {
                // Make sure we add it to our list of books.
                $abooks[] = $serverInfo['params']['username'];
            }
        }

        $shares = &$share_obj->listShares(Auth::getAuth());
        // A share for each IMSP adress book we can see.
        foreach ($abooks as $abook_uid) {
            $found = false;
            foreach ($shares as $id => $share) {
                $params = @unserialize($share->get('params'));
                if (!empty($params['name']) && $params['name'] == $abook_uid &&
                    $params['source'] == 'imsp') {
                    $found = true;
                    break;
                }
            }
            if (!$found) {
                $shareparams = array('name' => $abook_uid,
                                     'source' => 'imsp');

                $params['uid'] = md5(mt_rand());
                $params['name'] = $abook_uid . ' (IMSP)';
                $params['acl'] = $imsp->myRights($abook_uid);
                if ($abook_uid == $serverInfo['params']['username']) {
                    // This is the default address book
                    $shareparams['default'] = true;
                } else {
                    $shareparams['default'] = false;
                }
                if (Net_IMSP_Utils::_isOwner($abook_uid,
                                             $serverInfo['params']['username'],
                                             $params['acl'])) {
                    $params['owner'] = Auth::getAuth();
                } else {
                    // TODO: What to do for the owner when it's not current user?
                    //       We'd have to try to match the owner per IMSP
                    //       address book name to a Horde user...how to do that
                    //       without assuming usernames are equal?
                }
                $result = Net_IMSP_Utils::_createShare($share_obj, $params, $shareparams);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
                $return['added'][] = $params['uid'];
            } else {
                // Share already exists, just update the acl.
                $params['acl'] = $imsp->myRights($abook_uid);
            }
            $found_shares[] = $abook_uid;
        }

        // Now prune any shares that no longer exist on the IMSP server.
        $existing = $share_obj->listShares(Auth::getAuth(), PERMS_READ);
        foreach ($existing as $key => $share) {
            $temp = unserialize($share->get('params'));
            if (is_array($temp)) {
                $sourceType = $temp['source'];
                if ($sourceType == 'imsp' &&
                    array_search($temp['name'], $found_shares) === false) {
                        $result = $share_obj->removeShare($share);
                        if (is_a($result, 'PEAR_Error')) {
                            return $result;
                        }
                        $return['removed'][] = $share->getName();
                }
            }
        }
        return $return;
    }

    /**
     * Creates a Horde_Share for an *existing* IMSP address book.
     * Needed for creating shares for address books created outside
     * of Horde.
     *
     * @param Horde_Share  The share object to create the new share with.
     * @param array        Parameters for the share
     *
     * @return mixed  True | PEAR_Error
     * @since Horde 3.2
     */
    function _createShare(&$share_obj, $params, $shareparams)
    {
        $share = &$share_obj->newShare($params['uid']);
        if (is_a($share, 'PEAR_Error')) {
            return $share;
        }
        $share->set('params', serialize($shareparams));
        $share->set('name', $params['name']);
        Net_IMSP_Utils::_setPerms($share, $params['acl']);
        $share->save();
        return true;
    }

    /**
     * Determine if we are the owner of the address book.
     * Assumes ownership if username is beginning address book name or
     * if user has admin rights ('a') in acl.
     *
     * @param array $params  Parameters to check for ownership.
     *
     * @return boolean  True if $user is owner, otherwise false.
     * @since Horde 3.2
     */
    function _isOwner($bookName, $username, $acl)
    {
        if (strpos($bookName, $username) === 0) {
            return true;
        } elseif (strpos($acl, 'a')) {
            return true;
        }
        return false;
    }

    /**
     * Translates IMSP acl into share permissions and sets them in share.
     *
     * @param Datatree_Object_Share $share  The share to assign perms to
     * @param string $acl                   The IMSP acl string.
     * @since Horde 3.2
     */
    function _setPerms(&$share, $acl)
    {
         $hPerms = 0;
         if (strpos($acl, 'w') !== false) {
             $hPerms |= PERMS_EDIT;
         }
         if (strpos($acl, 'r') !== false) {
             $hPerms |= PERMS_READ;
         }
         if (strpos($acl, 'd') !== false) {
             $hPerms |= PERMS_DELETE;
         }
         if (strpos($acl, 'l') !== false) {
             $hPerms |= PERMS_SHOW;
         }
        $share->addUserPermission(Auth::getAuth(), $hPerms);
    }

    /**
     * Translates Horde_Share permissions into IMSP acl.
     *
     * @param integer $perms   Horde_Perms style permission bitmask.
     *
     * @return string   An IMSP acl string
     * @since Horde 3.2
     */
    function permsToACL($perms)
    {
        $acl = '';

        if ($perms & PERMS_SHOW) {
            $acl = 'l';
        }
        if ($perms & PERMS_READ) {
            $acl .= 'r';
        }
        if ($perms & PERMS_EDIT) {
            $acl .= 'w';
        }
        if ($perms & PERMS_DELETE) {
            $acl .= 'd';
        }
        return $acl;
    }

    /**
     * Set's an address book's acl on the IMSP server.
     *
     * @param string $book  The address book name to set
     * @param string $name  The user name to set for.
     * @param string $acl   The acl string to set.
     *
     * @return mixed  True | Pear_Error
     * @since Horde 3.2
     */
    function setACL($params, $book, $name, $acl)
    {
        $imsp = &Net_IMSP::singleton('Book', $params);
        $imsp->init();
        return $imsp->setACL($book, $name, $acl);
    }
}
