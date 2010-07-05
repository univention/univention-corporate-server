<?php

/** We require the base Horde library. */
require_once 'Horde.php';

/** We need access to the Kolab IMAP storage */
require_once 'Horde/Kolab/Deprecated.php';

/** We need the Kolab date functions */
require_once 'Horde/Kolab/Format/Date.php';

/**
 * The Horde_Kolab library is both an object used by application drivers to
 * communicate with a Kolab server, as well as a utility library providing
 * several functions to help in the IMAP folder <-> Horde Share synchronisation
 * process.
 *
 * $Horde: framework/Kolab/Kolab.php,v 1.26.10.32 2009-01-06 15:23:13 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @package Horde_Kolab
 */
class Kolab {

    /**
     * The current application that this Kolab object instance is catering to.
     *
     * @deprecated
     *
     * @var string
     */
    var $_app;

    /**
     * The storage driver for the Kolab server.
     *
     * @deprecated
     *
     * @var Kolab_Storage
     */
    var $_storage;

    /**
     * Indicates the version of this driver
     *
     * @deprecated
     *
     * @var int
     */
    var $version = 2;

    /**
     * The DomDocument object that contains the XML DOM tree of the currently
     * loaded groupware object. We cache this here to ensure preservation of
     * unknown fields when re-saving the object.
     *
     * @deprecated
     *
     * @var DomDocument
     */
    var $_xml;

    /**
     * The (Kolab) UID of the current message.
     *
     * @deprecated
     *
     * @var string
     */
    var $_uid;

    /**
     *
     * @deprecated
     *
     */
    function Kolab($app = null)
    {
        if (!isset($app)) {
            global $registry;
            $app = $registry->getApp();
        }
        $this->_app = $app;
        
        $this->_storage = &new Kolab_Storage_Deprecated();
    }

    /**
     * Return the uid of the message we are currently dealing with.
     *
     * @deprecated
     *
     * @return string  The Kolab UID of the message we are currently
     *                 dealing with.
     */
    function getUID()
    {
      return $this->_uid;
    }

    /**
     * Open the specified share.
     *
     * @deprecated
     *
     * @param string $share_uid      The uid of the share that
     *                               should be opened.
     * @param int    $loader         The version of the XML
     *                               loader
     *
     * @return mixed  True on success, a PEAR error otherwise
     */
    function open($share_uid, $loader = 0)
    {
        $app_consts = Kolab::getAppConsts($this->_app);
        if (is_a($app_consts, 'PEAR_Error')) {
            return $app_consts;
        }

        return $this->_storage->open($share_uid, $app_consts, $loader);
    }

    /**
     * Close the current share.
     *
     * @deprecated
     */
    function close()
    {
        $this->_storage->close();
    }

    /**
     * Retrieve all objects in the current folder
     *
     * @deprecated
     *
     * @return array  All object data arrays
     */
    function getObjects()
    {
        return $this->_storage->getObjects();
    }

    /**
     * Returns a list of all IMAP folders (including their groupware type)
     * that the current user has acccess to.
     *
     * @deprecated
     *
     * @return array  An array of array($foldername, $foldertype) items (empty
     *                on error).
     */
    function listFolders()
    {
        return Kolab_Storage_Deprecated::listFolders();
    }

    /**
     * List the objects in the current share.
     *
     * @deprecated
     *
     * @return mixed  false if there are no objects, a list of message
     *                ids or a PEAR error.
     */
    function listObjects()
    {
        return $this->_storage->listObjects();
    }

    /**
     * List the objects in the specified folder.
     *
     * @deprecated
     *
     * @param string $folder  The folder to search.
     *
     * @return mixed  false if there are no objects, a list of message
     *                ids otherwise.
     */
    function listObjectsInFolder($folder)
    {
        return $this->_storage->listObjectsInFolder($folder);
    }

    /**
     * Find the object with the given UID in the current share.
     *
     * @deprecated
     *
     * @param string $uid  The UID of the object.
     *
     * @return mixed  false if there is no such object
     */
    function findObject($uid)
    {
        return $this->_storage->findObject($uid);
    }

    /**
     * Load the object with the given UID into $this->_xml
     *
     * @deprecated
     *
     * @param string  $uid      The UID of the object.  
     * @param boolean $is_msgno Indicate if $uid holds an 
     *                          IMAP message number
     *
     * @return mixed  false if there is no such object, a PEAR error if
     *                the object could not be loaded. Otherwise the xml
     *                document will be returned
     */
    function &loadObject($uid, $is_msgno = false)
    {
        $result = $this->_storage->loadObject($uid, $is_msgno);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_xml = $result;
        $this->_uid = $this->getVal('uid');
        $element = $this->_xml->document_element();
        return $element;

    }

    /**
     * Create the object with UID in the current share
     *
     * @deprecated
     *
     * @param string  $uid      The UID of the object.  
     *
     * @return mixed  false if there is no open share, a PEAR error if
     *                the object could not be created. Otherwise the xml
     *                document will be returned
     */
    function &newObject($uid)
    {
        $result = $this->_storage->newObject($uid);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_xml = $result;
        $this->_uid = $uid;

        $element = $this->_xml->document_element();
        return $element;
    }

    /**
     * Save the current object.
     *
     * @deprecated
     *
     * @return mixed  false if there is no open share, a PEAR error if
     *                the object could not be saved. True otherwise
     */
    function saveObject()
    {
        $this->setVal('last-modification-date', Kolab::encodeDateTime());
        $this->setVal('product-id', KOLAB_PRODUCT_ID);

        return $this->_storage->saveObject($this->_xml, $this->_uid);
    }

    /**
     * Move the object with the given UID from the current share into
     * the specified new share.
     *
     * @deprecated
     *
     * @param string  $uid       The UID of the object.  
     * @param boolean $new_share The share the object should be moved to.
     *
     * @return mixed  false if there is no current share, a PEAR error if
     *                the object could not be moved. True otherwise.
     */
    function moveObject($uid, $new_share)
    {
        return $this->_storage->moveObject($uid, $new_share);
    }

    /**
     * Remove the specified objects from the current share.
     *
     * @deprecated
     *
     * @param string  $objects  The UIDs (or maessage numbers) 
     *                          of the objects to be deleted.  
     * @param boolean $is_msgno Indicate if $objects holds  
     *                          IMAP message numbers
     *
     * @return mixed  false if there is no IMAP connection, a PEAR
     *                error if the objects could not be removed. True
     *                if the call succeeded.
     */
    function removeObjects($objects, $is_msgno = false)
    {
        return $this->_storage->removeObjects($objects, $is_msgno);
    }

    /**
     * Remove all objects from the current share.
     *
     * @deprecated
     *
     * @return mixed  false if there is no IMAP connection, a PEAR
     *                error if the objects could not be removed. True
     *                if the call succeeded.
     */
    function removeAllObjects()
    {
        return $this->_storage->removeAllObjects();
    }

    /**
     * Returns the groupware type of the given IMAP folder.
     *
     * @deprecated
     *
     * @param object $mailbox  The mailbox of interest.
     *
     * @return mixed  A string indicating the groupware type of $mailbox or
     *                boolean "false" on error.
     */
    function getMailboxType($mailbox)
    {
        $list = &Kolab_List::singleton();
        $folder = $list->getFolder($mailbox);
        if (is_a($folder, 'PEAR_Error')) {
            return $folder;
        }
        return $folder->getType();
    }

    /**
     * Find the object using the given criteria in the current share.
     *
     * @deprecated
     *
     * @param string $criteria  The search criteria.
     *
     * @return mixed  false if no object can be found
     */
    function findObjects($criteria)
    {
        return $this->_storage->findObjects($criteria);
    }

    /**
     * Return the MIME type of the message we are currently dealing with.
     *
     * @deprecated
     *
     * @return string  The MIME type of the message we are currently
     *                 dealing with.
     */
    function getMimeType()
    {
        return $this->_mime_type;
    }

    function &getCurrentObject()
    {
        $element = $this->_xml->document_element();
        return $element;
    }

    function &getElem($name, &$parent)
    {
        $elements = $this->getAllElems($name, $parent);

        if (empty($elements)) {
            $elements = false;
            return $elements;
        }

        return $elements[0];
    }

    function &getAllElems($name, &$parent)
    {
        $elements = $parent->get_elements_by_tagname($name);
        return $elements;
    }

    function &getRootElem($name)
    {
        $element = $this->getElem($name, $this->getCurrentObject());
        return $element;
    }

    function &getAllRootElems($name)
    {
        $elements = $this->getAllElems($name, $this->getCurrentObject());
        return $elements;
    }

    function delElem($name, &$parent)
    {
        $element = $this->getElem($name, $parent);
        if ($element === false) {
            return;
        }

        return $parent->remove_child($element);
    }

    function delAllElems($name, &$parent)
    {
        $elements = $this->getAllElems($name, $parent);
        for ($i = 0, $j = count($elements); $i < $j; $i++) {
            $parent->remove_child($elements[$i]);
        }
        return true;
    }

    function delAllRootElems($name)
    {
        return $this->delAllElems($name, $this->getCurrentObject());
    }

    function delRootElem(&$element)
    {
        if ($element === false) {
            return;
        }

        $root = $this->getCurrentObject();
        return $root->remove_child($element);
    }

    function getElemVal(&$parent, $name, $default = 0)
    {
        if ($parent === false) {
            return $default;
        }

        $element = $this->getElem($name, $parent);
        if ($element === false) {
            return $default;
        }

        return $element->get_content();
    }

    function getElemStr(&$parent, $name, $default = '')
    {
        if ($parent === false) {
            return $default;
        }

        $element = $this->getElem($name, $parent);
        if ($element === false) {
            return $default;
        }

        return String::convertCharset($element->get_content(), 'utf-8');
    }

    function getVal($name, $default = 0)
    {
        $val = $this->getElemVal($this->getCurrentObject(), $name, $default);
        return $val;
    }

    function getStr($name, $default = '')
    {
        $str = $this->getElemStr($this->getCurrentObject(), $name, $default);
        return $str;
    }

    function &initElem($name, &$parent)
    {
        if ($parent === false) {
            $parent = $this->getCurrentObject();
        }

        $element = $this->getElem($name, $parent);

        if ($element === false) {
            $element = $parent->append_child($this->_xml->create_element($name));
        }

        $children = $element->child_nodes();
        foreach ($children as $child) {
            if ($child->node_type() == XML_TEXT_NODE) {
                $element->remove_child($child);
            }
        }

        return $element;
    }

    function &initRootElem($name)
    {
        $rootElement = $this->initElem($name, $this->getCurrentObject());
        return $rootElement;
    }

    function &appendElem($name, &$parent)
    {
        $child = $parent->append_child($this->_xml->create_element($name));
        return $child;
    }

    function &appendRootElem($name)
    {
        $append = $this->appendElem($name, $this->getCurrentObject());
        return $append;
    }

    function &setElemVal(&$parent, $name, $value = '')
    {
        $element = $this->initElem($name, $parent);
        $element->set_content($value);

        return $element;
    }

    function &setElemStr(&$parent, $name, $value = '')
    {
        return $this->setElemVal($parent, $name, String::convertCharset($value, NLS::getCharset(), 'utf-8'));
    }

    function &setVal($name, $value = '')
    {
        $result = $this->setElemVal($this->getCurrentObject(), $name, $value);
        return $result;
    }

    function &setStr($name, $value = '')
    {
        $result = $this->setElemStr($this->getCurrentObject(), $name, $value);
        return $result;
    }

    /**
     * Converts a string in the current character set to an IMAP UTF-7 string,
     * suitable for use as the name of an IMAP folder.
     *
     * @deprecated
     *
     * @param string $name  The text in the current character set to convert.
     *
     * @return string  $name encoded in the IMAP variation of UTF-7.
     */
    function encodeImapFolderName($name)
    {
        return String::convertCharset($name, NLS::getCharset(), 'UTF7-IMAP');
    }

    /**
     * Converts a string in the IMAP variation of UTF-7 into a string in the
     * current character set.
     *
     * @deprecated
     *
     * @param string $name  The text in IMAP UTF-7 to convert.
     *
     * @return string  $name encoded in the current character set.
     */
    function decodeImapFolderName($name)
    {
        return String::convertCharset($name, 'UTF7-IMAP');
    }

    /**
     * Converts all newlines (in DOS, MAC & UNIX format) in the specified text
     * to unix-style (LF) format.
     *
     * @deprecated
     *
     * @param string $text  The text to convert.
     *
     * @return string  $text with all newlines replaced by LF.
     */
    function unixNewlines($text)
    {
        return preg_replace("/\r\n|\n|\r/s", "\n", $text);
    }

    /**
     * Returns the unfolded representation of the given text.
     *
     * @deprecated
     *
     * @param string $text  The text to unfold.
     *
     * @return string  The unfolded representation of $text.
     */
    function unfoldText($text)
    {
        return preg_replace("/\r\n[ \t]+/", "", $text);
    }

    /**
     * Returns a string containing the current UTC date in the format
     * prescribed by the Kolab Format Specification.
     *
     * @deprecated
     *
     * @return string  The current UTC date in the format 'YYYY-MM-DD'.
     */
    function encodeDate($date = false)
    {
        return Horde_Kolab_Format_Date::encodeDate($date);
    }

    /**
     * Returns a UNIX timestamp corresponding the given date string which is
     * in the format prescribed by the Kolab Format Specification.
     *
     * @deprecated
     *
     * @param string $date  The string representation of the date.
     *
     * @return integer  The unix timestamp corresponding to $date.
     */
    function decodeDate($date)
    {
        return Horde_Kolab_Format_Date::decodeDate($date);
    }

    /**
     * Returns a string containing the current UTC date and time in the format
     * prescribed by the Kolab Format Specification.
     *
     * @deprecated
     *
     * @return string  The current UTC date and time in the format
     *                 'YYYY-MM-DDThh:mm:ssZ', where the T and Z are literal
     *                 characters.
     */
    function encodeDateTime($datetime = false)
    {
        return Horde_Kolab_Format_Date::encodeDateTime($datetime);
    }

    /**
     * Returns a UNIX timestamp corresponding the given date-time string which
     * is in the format prescribed by the Kolab Format Specification.
     *
     * @deprecated
     *
     * @param string $datetime  The string representation of the date & time.
     *
     * @return integer  The unix timestamp corresponding to $datetime.
     */
    function decodeDateTime($datetime)
    {
        return Horde_Kolab_Format_Date::decodeDateTime($datetime);
    }

    /**
     * Returns a UNIX timestamp corresponding the given date or date-time
     * string which is in either format prescribed by the Kolab Format
     * Specification.
     *
     * @deprecated
     *
     * @param string $date  The string representation of the date (& time).
     *
     * @return integer  The unix timestamp corresponding to $date.
     */
    function decodeDateOrDateTime($date)
    {
        return Horde_Kolab_Format_Date::decodeDateOrDateTime($date);
    }

    /**
     * Returns a UNIX timestamp corresponding the given date-time string which
     * is in the format prescribed by the Kolab Format Specification.
     *
     * @deprecated
     *
     * @param string $date The string representation of the date (& time).
     *
     * @return integer  The unix timestamp corresponding to $datetime.
     */
    function decodeFullDayDate($date)
    {
        if (empty($date)) {
            return 0;
        }

        return (strlen($date) == 10
                ? Kolab::decodeDate($date) + 24 * 60 * 60
                : Kolab::decodeDateTime($date));
    }

    function percentageToBoolean($percentage)
    {
        return $percentage == 100 ? '1' : '0';
    }

    function booleanToPercentage($boolean)
    {
        return $boolean ? '100' : '0';
    }

    /**
     * Returns an array of application-specific constants, that are used in
     * a generic manner throughout the library.
     *
     * @deprecated
     *
     * @param string $app  The application whose constants to query.
     *
     * @return mixed  An array of application-specific constants if $app is a
     *                supported application, or a PEAR_Error object if $app is
     *                not supported.
     */
    function getAppConsts($app)
    {
        switch ($app) {
        case 'mnemo':
            return array(
                'folder_type'           => 'note',
                'mime_type_suffix'      => 'note',
                'allowed_types'         => array(
                    'note',
                ),
                'default_folder_name'   => _("Notes"),
                'application'           => $app,
            );

        case 'kronolith':
            return array(
                'folder_type'           => 'event',
                'mime_type_suffix'      => 'event',
                'allowed_types'         => array(
                    'event',
                ),
                'default_folder_name'   => _("Calendar"),
                'application'           => $app,
            );

        case 'turba':
            return array(
                'folder_type'           => 'contact',
                'mime_type_suffix'      => 'contact',
                'allowed_types'         => array(
                    'contact',
                    'distribution-list',
                ),
                'default_folder_name'   => _("Contacts"),
                'application'           => $app,
            );

        case 'nag':
            return array(
                'folder_type'           => 'task',
                'mime_type_suffix'      => 'task',
                'allowed_types'         => array(
                    'task',
                ),
                'default_folder_name'   => _("Tasks"),
                'application'           => $app,
            );

        case 'h-prefs':
            return array(
                'folder_type'           => 'h-prefs',
                'mime_type_suffix'      => 'h-prefs',
                'allowed_types'         => array(
                    'h-prefs',
                ),
                'default_folder_name'   => _("Preferences"),
                'application'           => $app,
            );

        default:
            return PEAR::raiseError(sprintf(_("The Horde/Kolab integration engine does not support \"%s\""), $app));
        }
    }

    /**
     * Returns the server url of the given type.
     *
     * This method is used to encapsulate multidomain support.
     *
     * @return string The server url or empty on error.
     */
    function getServer($server_type)
    {
        global $conf;

        switch ($server_type) {
        case 'imap':
            return $conf['kolab']['imap']['server'];
        case 'ldap':
            return $conf['kolab']['ldap']['server'];
        case 'smtp':
            return $conf['kolab']['smtp']['server'];
        default:
            return '';
        }
    }

    /**
     * @deprecated
     */
    function triggerFreeBusyUpdate()
    {
    }
}
