<?php
/**
 * @package Kolab_Storage
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Deprecated.php,v 1.1.2.4 2009-01-06 15:23:17 jan Exp $
 */

/** Load the main class. */
require_once 'Horde/Kolab/Storage.php';

/**
 * The Kolab_Storage class provides the means to access the Kolab server
 * storage for groupware objects.
 *
 * This contains the functionality that has been deprecated but not
 * yet removed. This will happen once we move to Horde4 and can break
 * backward compatibility. The intended way of using the Kolab storage
 * handling is to use the main Kolab_Storage class only.
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Deprecated.php,v 1.1.2.4 2009-01-06 15:23:17 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @package Kolab_Storage
 */
class Kolab_Storage_Deprecated extends Kolab_Storage {

    /**
     * The the folder we currently access.
     *
     * @deprecated
     *
     * @var Kolab_Folder
     */
    var $_folder;

    /**
     * The the folder data we currently access.
     *
     * @deprecated
     *
     * @var Kolab_Data
     */
    var $_data;

    /**
     * A copy of the app_consts for the current app
     *
     * @deprecated
     *
     * @var string
     */
    var $_app_consts;

    /**
     * Version of the data format to load
     *
     * @deprecated
     *
     * @var int
     */
    var $_loader_version;

    /**
     * The (encoded) name of the IMAP folder that corresponds to the current
     * share.
     *
     * @deprecated
     *
     * @var string
     */
    var $_share;

    /**
     * The IMAP connection
     *
     * @deprecated
     *
     * @var resource
     */
    var $_imap;

    /**
     * Folder object type
     *
     * @deprecated
     *
     * @var string
     */
    var $_object_type;

    /**
     * The full mime type string of the current Kolab object format we're
     * dealing with.
     *
     * @deprecated
     *
     * @var string
     */
    var $_mime_type;

    /**
     * The id of the part with the Kolab attachment.
     *
     * @deprecated
     *
     * @var int
     */
    var $_mime_id;

    /**
     * Message headers
     *
     * @deprecated
     *
     * @var MIME_Header
     */
    var $_headers;

    /**
     * The MIME_Message object that contains the currently loaded message. This
     * is used when updating an object, in order to preserve everything else
     * within the message that we don't know how to handle.
     *
     * @deprecated
     *
     * @var MIME_Message
     */
    var $_message;

    /**
     * The IMAP message number of $this->_message.
     *
     * @deprecated
     *
     * @var integer
     */
    var $_msg_no;

    /**
     * Open the specified share.
     *
     * @deprecated
     *
     * @param string $share          The id of the share
     *                               that should be opened.
     * @param int    $loader_version The version of the format
     *                               loader
     *
     * @return mixed  True on success, a PEAR error otherwise
     */
    function open($share, $app_consts, $loader_version = 0)
    {
        $folder = $this->getShare($share,
                                  $app_consts['mime_type_suffix']);
        if (is_a($folder, 'PEAR_Error')) {
            return $folder;
        }
        $this->_folder = &$folder;

        $data = $this->getData($this->_folder,
                               $app_consts['mime_type_suffix'],
                               $loader_version);
        if (is_a($data, 'PEAR_Error')) {
            return $data;
        }
        $this->_data = $data;

        $this->_app_consts = &$app_consts;
        $this->_loader_version = $loader_version;

        // This is only necessary for the old framework.
        if ($loader_version == 0) {
            /** We need the DOM library for xml handling (PHP4/5). */
            require_once 'Horde/DOM.php';

            $session = &Horde_Kolab_Session::singleton();
            $this->_imap = &$session->getImap();

            $this->_object_type = $app_consts['mime_type_suffix'];
            $this->_mime_type = 'application/x-vnd.kolab.' . $this->_object_type;

            // Check that the folder exists. For the new framework
            // this happens in _synchronize()
            $result = $this->exists();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        return true;
    }

    /**
     * Handles the horde syntax for default shares
     *
     * @deprecated
     *
     * @param string $share The share name that should be parsed
     *
     * @return string The corrected IMAP folder name.
     */
    function parseFolder($share)
    {
        global $registry;
        $const = Kolab::getAppConsts($registry->getApp());
        $list = &Kolab_List::singleton();
        return $list->parseShare($share, $const['folder_type']);
    }

    /**
     * Selects the type of data we are currently dealing with.
     *
     * @deprecated
     */
    function setObjectType($type)
    {
        if (in_array($type, $this->_app_consts['allowed_types'])) {
            $data = $this->getData($this->_folder,
                                   $type,
                                   $this->_loader_version);
            if (is_a($data, 'PEAR_Error')) {
                return $data;
            }
            $this->_data = $data;
        } else {
            return PEAR::raiseError(sprintf(_("Object type %s not allowed for folder type %s!"), $type, $this->_store_type));
        }
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
        $list = &Kolab_List::singleton();
        $folders = $list->getFolders();
        if (is_a($folders, 'PEAR_Error')) {
            return $folders;
        }
        $result = array();
        foreach ($folders as $folder) {
            $result[] = array($folder->name, $folder->getType());
        }
        return $result;
    }

    /**
     * Close the current folder.
     *
     * @deprecated
     */
    function close()
    {
    }

    /**
     *
     *
     * @deprecated
     */
    function exists()
    {
        return $this->_folder->exists();
    }

    /**
     *
     * @deprecated
     *
     */
    function deleteAll()
    {
        return $this->_data->deleteAll();
    }

    /**
     * Delete the specified message from the current folder
     *
     * @deprecated
     *
     * @param  string $object_uid Id of the message to be deleted.
     *
     * @return mixed True is successful, false if the message does not
     * exist, a PEAR error otherwise.
     */
    function delete($object_uid)
    {
        return $this->_data->delete($object_uid);
    }

    /**
     * Move the specified message from the current folder into a new
     * folder
     *
     * @deprecated
     *
     * @param  string $object_uid  ID of the message to be deleted.
     * @param  string $new_share   ID of the target share.
     *
     * @return mixed True is successful, false if the object does not
     *               exist, a PEAR error otherwise.
     */
    function move($object_uid, $new_share)
    {
        return $this->_data->move($object_uid, $new_share);
    }

    /**
     * Save an object.
     *
     * @deprecated
     *
     * @param array  $object         The array that holds the data object
     * @param string $old_object_id  The id of the object if it existed before
     *
     * @return mixed  True on success, a PEAR error otherwise
     */
    function save($object, $old_object_id = null)
    {
        return $this->_data->save($object, $old_object_id);
    }

    /**
     * Generate a unique object id
     *
     * @deprecated
     *
     * @return string  The unique id
     */
    function generateUID()
    {
        return $this->_data->generateUID();
    }

    /**
     * Check if the given id exists
     *
     * @deprecated
     *
     * @param string $uid  The object id
     *
     * @return boolean  True if the id was found, false otherwise
     */
    function objectUidExists($uid)
    {
        return $this->_data->objectUidExists($uid);
    }

    /**
     * Return the specified object
     *
     * @deprecated
     *
     * @param string     $object_id       The object id
     *
     * @return mixed The object data as array or a PEAR error if the
     * object is missing from the cache.
     */
    function getObject($object_id)
    {
        return $this->_data->getObject($object_id);
    }

    /**
     * Retrieve all object ids in the current folder
     *
     * @deprecated
     *
     * @return array  The object ids
     */
    function getObjectIds()
    {
        return $this->_data->getObjectIds();
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
        return $this->_data->getObjects();
    }

    /**
     * Retrieve all objects in the current folder as an array
     *
     * @deprecated
     *
     * @return array  The object data array
     */
    function getObjectArray()
    {
        return $this->_data->getObjectArray();
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
        if (empty($this->_imap)) {
            return false;
        }

        // Select folder
        $result = $this->_imap->select($this->_folder);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->_imap->searchHeaders('X-Kolab-Type', $this->_mime_type);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return $result;
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
        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();

        // Select mailbox to search in
        $result = $imap->select($folder);
        if (is_a($result, 'PEAR_Error')) {
            return false;
        }

        $result = $imap->searchHeaders('X-Kolab-Type', $this->_mime_type);
        if (!isset($result)) {
            $result = array();
        }
        return $result;
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
        if (empty($this->_imap)) {
            return false;
        }

        if (empty($uid) || $uid == "") {
            return PEAR::raiseError("Cannot search for an empty uid.");
        }

        // Select folder
        $result = $this->_imap->select($this->_folder->name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->_imap->search("SUBJECT \"$uid\"");
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if (empty($result)) {
            return PEAR::raiseError(sprintf(_("No message corresponds to object %s"), $uid));
        }

        return $result[0];
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
    function loadObject($uid, $is_msgno = false)
    {
        if (empty($this->_imap)) {
            $object = false;
            return $object;
        }

        // Select folder
        $result = $this->_imap->select($this->_folder->name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($is_msgno === false) {
            $uid = $this->findObject($uid);
            if (is_a($uid, 'PEAR_Error')) {
                return $uid;
            }
        }

        $header = $this->_imap->getMessageHeader($uid);
        if (is_a($header, 'PEAR_Error')) {
            return $header;
        }
        $this->_headers = MIME_Structure::parseMIMEHeaders($header);

        $message_text = $this->_imap->getMessage($uid);
        if (is_a($message_text, 'PEAR_Error')) {
            return $message_text;
        }

        if (is_array($message_text)) {
            $message_text = array_shift($message_text);
        }

        $this->_msg_no = $uid;
        $this->_message = &MIME_Structure::parseTextMIMEMessage($message_text);

        $parts = $this->_message->contentTypeMap();
        $this->_mime_id = array_search($this->_mime_type, $parts);
        if ($this->_mime_id !== false) {
            $part = $this->_message->getPart($this->_mime_id);
            $text = $part->transferDecode();
        } else {
            return PEAR::raiseError(sprintf(_("Horde/Kolab: No object of type %s found in message %s"), $this->_mime_type, $uid));
        }

        return Horde_DOM_Document::factory(array('xml' => $text));
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
    function newObject($uid)
    {
        if (empty($this->_imap)) {
            $object = false;
            return $object;
        }

        $this->_msg_no = -1;
        $this->_message = new MIME_Message();

        $kolab_text = sprintf(_("This is a Kolab Groupware object. To view this object you will need an email client that understands the Kolab Groupware format. For a list of such email clients please visit %s"),
                              'http://www.kolab.org/kolab2-clients.html');
        $part = new MIME_Part('text/plain',
                              String::wrap($kolab_text, 76, "\r\n", NLS::getCharset()),
                              NLS::getCharset());
        $part->setTransferEncoding('quoted-printable');
        $this->_message->addPart($part);

        $part = new MIME_Part($this->_mime_type, '', NLS::getCharset());
        $part->setTransferEncoding('quoted-printable');
        $this->_message->addPart($part);

        $parts = $this->_message->contentTypeMap();
        $this->_mime_id = array_search($this->_mime_type, $parts);
        if ($this->_mime_id === false) {
            return PEAR::raiseError(sprintf(_("Horde/Kolab: Unable to retrieve MIME ID for the part of type %s"), $this->_mime_type));
        }

        $headers = new MIME_Headers();
        $headers->addHeader('From', Auth::getAuth());
        $headers->addHeader('To', Auth::getAuth());
        $headers->addHeader('Subject', $uid);
        $headers->addHeader('User-Agent', 'Horde::Kolab v1.1');
        $headers->addHeader('Reply-To', '');
        $headers->addHeader('Date', date('r'));
        $headers->addHeader('X-Kolab-Type', $this->_mime_type);
        $headers->addMIMEHeaders($this->_message);

        $this->_headers = $headers->toArray();

        $xml = '<?xml version="1.0" encoding="UTF-8"?>' .
            '<' . $this->_object_type . ' version="1.0">' .
            '<uid>' . $uid . '</uid>' .
            '<body></body>' .
            '<categories></categories>' .
            '<creation-date>' . Kolab::encodeDateTime() . '</creation-date>' .
            '<sensitivity>public</sensitivity>' .
            '</' . $this->_object_type . '>';

        return Horde_DOM_Document::factory(array('xml' => $xml));
    }

    /**
     * Save the current object.
     *
     * @deprecated
     *
     * @return mixed  false if there is no open share, a PEAR error if
     *                the object could not be saved. True otherwise
     */
    function saveObject($xml, $uid)
    {
        if (empty($this->_imap)) {
            return false;
        }

        // Select folder
        $result = $this->_imap->select($this->_folder->name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $part = new MIME_Part($this->_mime_type, $xml->dump_mem(true),
                              NLS::getCharset());
        $part->setTransferEncoding('quoted-printable');
        $this->_message->alterPart($this->_mime_id, $part);

        if ($this->_msg_no != -1) {
            $this->removeObjects($this->_msg_no, true);
        }

        $headers = new MIME_Headers();
        foreach ($this->_headers as $key => $val) {
            $headers->addHeader($key, $val);
        }

        $message = Horde_Kolab_IMAP::kolabNewlines($headers->toString() .
                                                   $this->_message->toString(false));

        $result = $this->_imap->appendMessage($message);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $this->_msg_no = $this->findObject($uid);
        if (is_a($this->_msg_no, 'PEAR_Error')) {
            return $this->_msg_no;
        }

        return true;
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
        if (empty($this->_imap)) {
            return false;
        }

        // No IMAP folder select needed as findObject
        // does it for us

        $new_share = rawurldecode($new_share);
        $new_share = $this->parseFolder($new_share);
        if (is_a($new_share, 'PEAR_Error')) {
            return $new_share;
        }

        $msg_no = $this->findObject($uid);
        if (is_a($msg_no, 'PEAR_Error')) {
            return $msg_no;
        }

        $result = $this->_imap->copyMessage($msg_no, $new_share);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->_imap->deleteMessages($msg_no);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $this->_imap->expunge();
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
        if (empty($this->_imap)) {
            return false;
        }

        if (!is_array($objects)) {
            $objects = array($objects);
        }

        if ($is_msgno === false) {
            $new_objects = array();

            foreach ($objects as $object) {
                $result = $this->findObject($object);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }

                $new_objects[] = $result;
            }

            $objects = $new_objects;
        }

        // Select folder
        $result = $this->_imap->select($this->_folder->name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->_imap->deleteMessages($objects);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->_imap->expunge();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return true;
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
        if (empty($this->_imap)) {
            return false;
        }

        // Select folder
        $result = $this->_imap->select($this->_folder->name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $messages = $this->listObjects();

        if ($messages) {
            $result = $this->_imap->deleteMessages($messages);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        return true;
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
        return $this->_folder->getType();
    }

    /**
     * Converts all newlines (in DOS, MAC & UNIX format) in the specified text
     * to Kolab (Cyrus) format.
     *
     * @deprecated
     *
     * @param string $text  The text to convert.
     *
     * @return string  $text with all newlines replaced by KOLAB_NEWLINE.
     */
    function kolabNewlines($text)
    {
        return preg_replace("/\r\n|\n|\r/s", "\r\n", $text);
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
        if (empty($this->_imap)) {
            return false;
        }

        return $this->_imap->search($criteria);
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
}

