<?php
/**
 * @package Kolab_Storage
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage/Folder.php,v 1.7.2.20 2009-04-25 18:42:27 wrobel Exp $
 */

/** We need the current user session. */
require_once 'Horde/Kolab/Session.php';

/** Data handling for Kolab **/
require_once 'Horde/Kolab/Storage/Data.php';

/** Permission library for Kolab **/
require_once 'Horde/Kolab/Storage/Perms.php';

/** We need the Kolab XML library for xml handling. */
require_once 'Horde/Kolab/Format.php';

/** We need the Horde History System for logging */
require_once 'Horde/History.php';

/** We need the Horde MIME library to deal with MIME messages. */
require_once 'Horde/MIME.php';
require_once 'Horde/MIME/Part.php';
require_once 'Horde/MIME/Message.php';
require_once 'Horde/MIME/Headers.php';
require_once 'Horde/MIME/Structure.php';

/** We need the String & NLS libraries for character set conversions, etc. */
require_once 'Horde/String.php';
require_once 'Horde/NLS.php';

/**
 * The root of the Kolab annotation hierarchy, used on the various IMAP folder
 * that are used by Kolab clients.
 */
define('KOLAB_ANNOT_ROOT', '/vendor/kolab/');

/**
 * The annotation, as defined by the Kolab format spec, that is used to store
 * information about what groupware format the folder contains.
 */
define('KOLAB_ANNOT_FOLDER_TYPE', KOLAB_ANNOT_ROOT . 'folder-type');

/**
 * Kolab specific free/busy relevance
 */
define('KOLAB_FBRELEVANCE_ADMINS',  0);
define('KOLAB_FBRELEVANCE_READERS', 1);
define('KOLAB_FBRELEVANCE_NOBODY',  2);
 
/**
 * Horde-specific annotations on the imap folder have this prefix.
 */
define('HORDE_ANNOT_SHARE_ATTR', '/vendor/horde/share-');

/**
 * The Kolab_Folder class represents an IMAP folder on the Kolab
 * server.
 *
 * $Horde: framework/Kolab_Storage/lib/Horde/Kolab/Storage/Folder.php,v 1.7.2.20 2009-04-25 18:42:27 wrobel Exp $
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
class Kolab_Folder {

    /**
     * The folder name.
     *
     * @var string
     */
    var $name;

    /**
     * A new folder name if the folder should be renamed on the next
     * save.
     *
     * @var string
     */
    var $new_name;

    /**
     * The handler for the list of Kolab folders.
     *
     * @var Kolab_List
     */
    var $_list;

    /**
     * The type of this folder.
     *
     * @var string
     */
    var $_type;

    /**
     * The complete folder type annotation (type + default).
     *
     * @var string
     */
    var $_type_annotation;

    /**
     * The owner of this folder.
     *
     * @var string
     */
    var $_owner;

    /**
     * The pure folder.
     *
     * @var string
     */
    var $_subpath;

    /**
     * Additional Horde folder attributes.
     *
     * @var array
     */
    var $_attributes;

    /**
     * Additional Kolab folder attributes.
     *
     * @var array
     */
    var $_kolab_attributes;

    /**
     * Is this a default folder?
     *
     * @var boolean
     */
    var $_default;

    /**
     * The title of this folder.
     *
     * @var string
     */
    var $_title;

    /**
     * The permission handler for the folder.
     *
     * @var Horde_Permission_Kolab
     */
    var $_perms;

    /**
     * Links to the data handlers for this folder.
     *
     * @var array
     */
    var $_data;

    /**
     * Links to the annotation data handlers for this folder.
     *
     * @var array
     */
    var $_annotation_data;

    /**
     * Indicate that the folder data has been modified from the
     * outside and all Data handlers need to synchronize.
     *
     * @var boolean
     */
    var $tainted = false;

    /**
     * Creates a Kolab Folder representation.
     *
     * @param string     $name  Name of the folder
     */
    function Kolab_Folder($name = null)
    {
        $this->name  = $name;
        $this->__wakeup();
    }

    /**
     * Initializes the object.
     */
    function __wakeup()
    {
        if (!isset($this->_data)) {
            $this->_data = array();
        }

        foreach($this->_data as $data) {
            $data->setFolder($this);
        }

        if (isset($this->_perms)) {
            $this->_perms->setFolder($this);
        }
    }

    /**
     * Returns the properties that need to be serialized.
     *
     * @return array  List of serializable properties.
     */
    function __sleep()
    {
        $properties = get_object_vars($this);
        unset($properties['_list']);
        $properties = array_keys($properties);
        return $properties;
    }

    /**
     * Set the list handler.
     *
     * @param Kolab_List $list  The handler for the list of folders.
     */
    function setList(&$list)
    {
        $this->_list = &$list;
    }

    /**
     * Set a new name for the folder. The new name will be realized
     * when saving the folder.
     *
     * @param string $name  The new folder name
     */
    function setName($name)
    {
        $name = str_replace(':', '/', $name);
        if (substr($name, 0, 5) != 'user/' && substr($name, 0, 7) != 'shared.') {
            $name = 'INBOX/' . $name;
        }
        $this->new_name = String::convertCharset($name, NLS::getCharset(), 'UTF7-IMAP');
    }

    /**
     * Set a new IMAP folder name for the folder. The new name will be
     * realized when saving the folder.
     *
     * @param string $name  The new folder name.
     */
    function setFolder($name)
    {
        $this->new_name = $name;
    }

    /**
     * Return the share ID of this folder.
     *
     * @return string The share ID of this folder.
     */
    function getShareId()
    {
        $current_user = Auth::getAuth();
        if ($this->isDefault() && $this->getOwner() == $current_user) {
            return $current_user;
        }
        return rawurlencode($this->name);
    }

    /**
     * Saves the folder.
     *
     * @param array $attributes An array of folder attributes. You can
     *                          set any attribute but there are a few
     *                          special ones like 'type', 'default',
     *                          'owner' and 'desc'.
     *
     * @return boolean|PEAR_Error True on success.
     */
    function save($attributes = null)
    {
        if (!isset($this->name)) {
            /* A new folder needs to be created */
            if (!isset($this->new_name)) {
                return PEAR::raiseError(_("Cannot create this folder! The name has not yet been set."));
            }

            if (isset($attributes['type'])) {
                $this->_type = $attributes['type'];
                unset($attributes['type']);
            } else {
                $this->_type = 'mail';
            }

            if (isset($attributes['default'])) {
                $this->_default = $attributes['default'];
                unset($attributes['default']);
            } else {
                $this->_default = false;
            }

            $result = $this->_list->create($this);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            $this->name = $this->new_name;
            $this->new_name = null;

            /* Initialize the new folder to default permissions */
            if (empty($this->_perms)) {
                $this->getPermission();
            }

        } else {

            $type = $this->getType();

            if (isset($attributes['type'])) {
                if ($attributes['type'] != $type) {
                    Horde::logMessage(sprintf('Cannot modify the type of a folder from %s to %s!',
                                              $type, $attributes['type']),
                                      __FILE__, __LINE__, PEAR_LOG_ERR);
                }
                unset($attributes['type']);
            }

            if (isset($attributes['default'])) {
                $this->_default = $attributes['default'];
                unset($attributes['default']);
            } else {
                $this->_default = $this->isDefault();
            }

            if (isset($this->new_name)
                && $this->new_name != $this->name) {
                /** The folder needs to be renamed */
                $result = $this->_list->rename($this);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }

                /**
                 * Trigger the old folder on an empty IMAP folder.
                 */
                $session = &Horde_Kolab_Session::singleton();
                $imap = &$session->getImap();
                if (!is_a($imap, 'PEAR_Error')) {
                    $result = $imap->create($this->name);
                    if (is_a($result, 'PEAR_Error')) {
                        Horde::logMessage(sprintf('Failed creating dummy folder: %s!',
                                                  $result->getMessage()),
                                          __FILE__, __LINE__, PEAR_LOG_ERR);
                    }
                    $imap->setAnnotation(KOLAB_ANNOT_FOLDER_TYPE, 
                                         array('value.shared' => $this->_type),
                                         $this->name);

                    $result = $this->trigger($this->name);
                    if (is_a($result, 'PEAR_Error')) {
                        Horde::logMessage(sprintf('Failed triggering dummy folder: %s!',
                                                  $result->getMessage()),
                                          __FILE__, __LINE__, PEAR_LOG_ERR);
                    }
                    $result = $imap->delete($this->name);
                    if (is_a($result, 'PEAR_Error')) {
                        Horde::logMessage(sprintf('Failed deleting dummy folder: %s!',
                                                  $result->getMessage()),
                                          __FILE__, __LINE__, PEAR_LOG_ERR);
                    }
                }

                $this->name     = $this->new_name;
                $this->new_name = null;
                $this->_title   = null;
                $this->_owner   = null;
            }
        }

        if (isset($attributes['owner'])) {
            if ($attributes['owner'] != $this->getOwner()) {
                Horde::logMessage(sprintf('Cannot modify the owner of a folder from %s to %s!',
                                          $this->getOwner(), $attributes['owner']),
                                  __FILE__, __LINE__, PEAR_LOG_ERR);
            }
            unset($attributes['owner']);
        }

        /** Handle the folder type */
        $folder_type = $this->_type . ($this->_default ? '.default' : '');
        if ($this->_type_annotation != $folder_type) {
            $result = $this->_setAnnotation(KOLAB_ANNOT_FOLDER_TYPE, $folder_type);
            if (is_a($result, 'PEAR_Error')) {
                $this->_type = null;
                $this->_default = false;
                $this->_type_annotation = null;
                return $result;
            }
        }

        if (!empty($attributes)) {
            if (!is_array($attributes)) {
                $attributes = array($attributes);
            }
            foreach ($attributes as $key => $value) {
                if ($key == 'params') {
                    $params = unserialize($value);
                    if (isset($params['xfbaccess'])) {
                        $result = $this->setXfbAccess($params['xfbaccess']);
                        if (is_a($result, 'PEAR_Error')) {
                            return $result;
                        }
                    }
                    if (isset($params['fbrelevance'])) {
                        $result = $this->setFbrelevance($params['fbrelevance']);
                        if (is_a($result, 'PEAR_Error')) {
                            return $result;
                        }
                    }
                }

                // setAnnotation apparently does not suppoort UTF-8 nor any special characters
                $store = base64_encode($value);
                if ($key == 'desc') {
                    $entry = '/comment';
                } else {
                    $entry = HORDE_ANNOT_SHARE_ATTR . $key;
                }
                $result = $this->_setAnnotation($entry, $store);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            }
            $this->_attributes = $attributes;
        }

        /** Now save the folder permissions */
        if (isset($this->_perms)) {
            $result = $this->_perms->save();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = $this->trigger();
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage(sprintf('Failed triggering folder %s! Error was: %s',
                                      $this->name, $result->getMessage()),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        return true;
    }

    /**
     * Delete this folder.
     *
     * @return boolean|PEAR_Error True if the operation succeeded.
     */
    function delete()
    {
        $result = $this->_list->remove($this);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return true;
    }

    /**
     * Returns the owner of the folder.
     *
     * @return string|PEAR_Error  The owner of this folder.
     */
    function getOwner()
    {
        if (!isset($this->_owner)) {
            if (!isset($this->name) && isset($this->new_name)) {
                $name = $this->new_name;
            } else {
                $name = $this->name;
            }

            if (!preg_match(";(shared\.|INBOX[/]?|user/([^/]+)[/]?)([^@]*)(@.*)?;", $name, $matches)) {
                return PEAR::raiseError(sprintf(_("Owner of folder %s cannot be determined."), $name));
            }

            $this->_subpath = $matches[3];

            if (substr($matches[1], 0, 6) == 'INBOX/') {
                $this->_owner = Auth::getAuth();
            } elseif (substr($matches[1], 0, 5) == 'user/') {
                $domain = strstr(Auth::getAuth(), '@');
                $user_domain = isset($matches[4]) ? $matches[4] : $domain;
                $this->_owner = $matches[2] . $user_domain;
            } elseif ($matches[1] == 'shared.') {
                $this->_owner =  'anonymous';
            }
        }
        return $this->_owner;
    }

    /**
     * Returns the subpath of the folder.
     *
     * @param string $name Name of the folder that should be triggered.
     *
     * @return string|PEAR_Error  The subpath of this folder.
     */
    function getSubpath($name = null)
    {
        if (!isset($this->_subpath) || isset($name)) {
            if (!isset($name)) {
                if (!isset($this->name) && isset($this->new_name)) {
                    $name = $this->new_name;
                } else {
                    $name = $this->name;
                }
            }

            if (!preg_match(";(shared\.|INBOX[/]?|user/([^/]+)[/]?)([^@]*)(@.*)?;", $name, $matches)) {
                return PEAR::raiseError(sprintf(_("Subpath of folder %s cannot be determined."), $name));
            }

            $this->_subpath = $matches[3];

        }
        return $this->_subpath;
    }

    /**
     * Returns a readable title for this folder.
     *
     * @return string  The folder title.
     */
    function getTitle()
    {
        if (!isset($this->_title) && isset($this->name)) {
            $title = $this->name;
            if (substr($title, 0, 6) == 'INBOX/') {
                $title = substr($title, 6);
            }
            $title = str_replace('/', ':', $title);
            $this->_title = String::convertCharset($title, 'UTF7-IMAP');
        }
        return $this->_title;
    }

    /**
     * The type of this folder.
     *
     * @return string|PEAR_Error  The folder type.
     */
    function getType()
    {
        if (!isset($this->_type)) {
            $type_annotation = $this->_getAnnotation(KOLAB_ANNOT_FOLDER_TYPE,
                                                     $this->name);
            if (is_a($type_annotation, 'PEAR_Error')) {
                $this->_default = false;
                return $type_annotation;
            } else if (empty($type_annotation)) {
                $this->_default = false;
                $this->_type = '';
            } else {
                $type = explode('.', $type_annotation);
                $this->_default = (!empty($type[1]) && $type[1] == 'default');
                $this->_type = $type[0];
            }
            $this->_type_annotation = $type_annotation;
        }
        return $this->_type;
    }

    /**
     * Is this a default folder?
     *
     * @return boolean Boolean that indicates the default status.
     */
    function isDefault()
    {
        if (!isset($this->_default)) {
            /* This call also determines default status */
            $this->getType();
        }
        return $this->_default;
    }

    /**
     * Returns one of the attributes of the folder, or an empty string
     * if it isn't defined.
     *
     * @param string $attribute  The attribute to retrieve.
     *
     * @return mixed The value of the attribute, an empty string or an
     *               error.
     */
    function getAttribute($attribute)
    {
        if (!isset($this->_attributes[$attribute])) {
            if ($attribute == 'desc') {
                $entry = '/comment';
            } else {
                $entry = HORDE_ANNOT_SHARE_ATTR . $attribute;
            }
            $annotation = $this->_getAnnotation($entry, $this->name);
            if (is_a($annotation, 'PEAR_Error')) {
                return $annotation;
            }
            if (empty($annotation)) {
                $this->_attributes[$attribute] = '';
            } else {
                $this->_attributes[$attribute] = base64_decode($annotation);
            }
        }
        return $this->_attributes[$attribute];
    }

    /**
     * Returns one of the Kolab attributes of the folder, or an empty
     * string if it isn't defined.
     *
     * @param string $attribute  The attribute to retrieve.
     *
     * @return mixed The value of the attribute, an empty string or an
     *               error.
     */
    function getKolabAttribute($attribute)
    {
        if (!isset($this->_kolab_attributes[$attribute])) {
            $entry = KOLAB_ANNOT_ROOT . $attribute;
            $annotation = $this->_getAnnotation($entry, $this->name);
            if (is_a($annotation, 'PEAR_Error')) {
                return $annotation;
            }
            if (empty($annotation)) {
                $this->_kolab_attributes[$attribute] = '';
            } else {
                $this->_kolab_attributes[$attribute] = $annotation;
            }
        }
        return $this->_kolab_attributes[$attribute];
    }


    /**
     * Returns whether the folder exists.
     *
     * @return boolean|PEAR_Error  True if the folder exists.
     */
    function exists()
    {
        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        $result = $imap->exists($this->name);
        if (is_a($result, 'PEAR_Error')) {
            return false;
        }
        return $result;
    }

    /**
     * Returns whether the folder is accessible.
     *
     * @return boolean|PEAR_Error   True if the folder can be accessed.
     */
    function accessible()
    {
        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        $result = $imap->select($this->name);
        if (is_a($result, 'PEAR_Error')) {
            return false;
        }
        return $result;
    }

    /**
     * Retrieve a handler for the data in this folder.
     *
     * @param Kolab_List $list  The handler for the list of folders.
     *
     * @return Kolab_Data|PEAR_Error  The data handler.
     */
    function &getData($object_type = null, $data_version = 1)
    {
        if (empty($object_type)) {
            $object_type = $this->getType();
            if (is_a($object_type, 'PEAR_Error')) {
                return $object_type;
            }
        }

        if ($this->tainted) {
            foreach ($this->_data as $data) {
                $data->synchronize();
            }
            $this->tainted = false;
        }

        $key = $object_type . '|' . $data_version;
        if (!isset($this->_data[$key])) {
            if ($object_type != 'annotation') {
                $type = $this->getType();
            } else {
                $type = 'annotation';
            }
            $data = new Kolab_Data($type, $object_type, $data_version);
            $data->setFolder($this);
            $data->synchronize();
            $this->_data[$key] = &$data;
        }
        return $this->_data[$key];
    }

    /**
     * Delete the specified message from this folder.
     *
     * @param  string  $id      IMAP id of the message to be deleted.
     * @param  boolean $trigger Should the folder be triggered?
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function deleteMessage($id, $trigger = true)
    {
        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        // Select folder
        $result = $imap->select($this->name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $imap->deleteMessages($id);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $imap->expunge();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        if ($trigger) {
            $result = $this->trigger();
            if (is_a($result, 'PEAR_Error')) {
                Horde::logMessage(sprintf('Failed triggering folder %s! Error was: %s',
                                          $this->name, $result->getMessage()),
                                  __FILE__, __LINE__, PEAR_LOG_ERR);
            }
        }

        return true;
    }

    /**
     * Move the specified message to the specified folder.
     *
     * @param string $id     IMAP id of the message to be moved.
     * @param string $folder Name of the receiving folder.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function moveMessage($id, $folder)
    {
        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        // Select folder
        $result = $imap->select($this->name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $imap->moveMessage($id, $folder);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $imap->expunge();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $result = $this->trigger();
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage(sprintf('Failed triggering folder %s! Error was: %s',
                                      $this->name, $result->getMessage()),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        return true;
    }

    /**
     * Move the specified message to the specified share.
     *
     * @param string $id    IMAP id of the message to be moved.
     * @param string $share Name of the receiving share.
     *
     * @return boolean|PEAR_Error True if successful.
     */
    function moveMessageToShare($id, $share)
    {
        $folder = $this->_list->getByShare($share, $this->getType());
        if (is_a($folder, 'PEAR_Error')) {
            return $folder;
        }
        $folder->tainted = true;

        $success = $this->moveMessage($id, $folder->name);

        $result = $this->trigger();
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage(sprintf('Failed triggering folder %s! Error was: %s',
                                      $this->name, $result->getMessage()),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
        }
        return $success;
    }

    /**
     * Retrieve the supported formats.
     *
     * @return array The names of the supported formats.
     */
    function getFormats()
    {
        global $conf;

        if (empty($conf['kolab']['misc']['formats'])) {
            $formats = array('XML');
        } else {
            $formats = $conf['kolab']['misc']['formats'];
        }
        if (!is_array($formats)) {
            $formats = array($formats);
        }
        if (!in_array('XML', $formats)) {
            $formats[] = 'XML';
        }
        return $formats;
    }

    /**
     * Save an object in this folder.
     *
     * @param array  $object        The array that holds the data of the object.
     * @param int    $data_version  The format handler version.
     * @param string $object_type   The type of the kolab object.
     * @param string $id            The IMAP id of the old object if it
     *                              existed before
     * @param array  $old_object    The array that holds the current data of the
     *                              object.
     *
     * @return boolean|PEAR_Error  True on success.
     */
    function saveObject(&$object, $data_version, $object_type, $id = null,
                        &$old_object = null)
    {
        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        // Select folder
        $result = $imap->select($this->name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $new_headers = new MIME_Headers();

        $formats = $this->getFormats();

        $handlers = array();
        foreach ($formats as $type) {
            $handlers[$type] = &Horde_Kolab_Format::factory($type, $object_type,
                                                            $data_version);
            if (is_a($handlers[$type], 'PEAR_Error')) {
                if ($type == 'XML') {
                    return $handlers[$type];
                }
                Horde::logMessage(sprintf('Loading format handler "%s" failed: %s',
                                          $type, $handlers[$type]->getMessage()),
                                  __FILE__, __LINE__, PEAR_LOG_ERR);
                continue;
            }
        }

        if ($id != null) {
            /** Update an existing kolab object */
            $session = &Horde_Kolab_Session::singleton();
            $imap = &$session->getImap();
            if (is_a($imap, 'PEAR_Error')) {
                return $imap;
            }

            if (!in_array($id, $imap->getUids())) {
                return PEAR::raiseError(sprintf(_("The message with ID %s does not exist. This probably means that the Kolab object has been modified by somebody else while you were editing it. Your edits have been lost."),
                                                $id));
            }

            /** Parse email and load Kolab format structure */
            $result = $this->parseMessage($id, $handlers['XML']->getMimeType(),
                                          true, $formats);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            list($old_message, $part_ids, $mime_message, $mime_headers) = $result;
            if (is_a($old_message, 'PEAR_Error')) {
                return $old_message;
            }

            if (isset($object['_attachments']) && isset($old_object['_attachments'])) {
                $attachments = array_keys($object['_attachments']);
                foreach (array_keys($old_object['_attachments']) as $attachment) {
                    if (!in_array($attachment, $attachments)) {
                        foreach ($mime_message->getParts() as $part) {
                            if ($part->getName() === $attachment) {
                                foreach (array_keys($mime_message->_parts) as $key) {
                                    if ($mime_message->_parts[$key]->getMIMEId() == $part->getMIMEId()) {
                                        unset($mime_message->_parts[$key]);
                                        break;
                                    }
                                }
                                $mime_message->_generateIdMap($mime_message->_parts);
                            }
                        }
                    }
                }
            }
            $object = array_merge($old_object, $object);

            if (isset($attachments)) {
                foreach ($mime_message->getParts() as $part) {
                    $name = $part->getName();
                    foreach ($attachments as $attachment) {
                        if ($name === $attachment) {
                            $object['_attachments'][$attachment]['id'] = $part->getMIMEId();
                        }
                    }
                }
            }

            /** Copy email header */
            if (!empty($mime_headers) && !$mime_headers === false) {
                foreach ($mime_headers as $header => $value) {
                    $new_headers->addheader($header, $value);
                }
            }
        } else {
            $mime_message = $this->_prepareNewMessage($new_headers);
            $mime_part_id = false;
        }

        if (isset($object['_attachments'])) {
            $attachments = array_keys($object['_attachments']);
            foreach ($attachments as $attachment) {
                $data = $object['_attachments'][$attachment];

                if (!isset($data['content']) && !isset($data['path'])) {
                    /**
                     * There no new content and no new path. Do not rewrite the
                     * attachment.
                     */
                    continue;
                }

                $part = new MIME_Part(isset($data['type']) ? $data['type'] : null,
                                      isset($data['content']) ? $data['content'] : file_get_contents($data['path']),
                                      NLS::getCharset());
                $part->setTransferEncoding('quoted-printable');
                $part->setDisposition('attachment');
                $part->setName($attachment);

                if (!isset($data['id'])) {
                    $mime_message->addPart($part);
                } else {
                    $mime_message->alterPart($data['id'], $part);
                }
            }
        }

        foreach ($formats as $type) {
            $new_content = $handlers[$type]->save($object);
            if (is_a($new_content, 'PEAR_Error')) {
                return $new_content;
            }

            /** Update mime part */
            $part = new MIME_Part($handlers[$type]->getMimeType(),
                                  $new_content, NLS::getCharset());
            $part->setTransferEncoding('quoted-printable');
            $part->setDisposition($handlers[$type]->getDisposition());
            $part->setDispositionParameter('x-kolab-type', $type);
            $part->setName($handlers[$type]->getName());

            if (!isset($part_ids) || $part_ids[$type] === false) {
                $mime_message->addPart($part);
            } else {
                $mime_message->alterPart($part_ids[$type], $part);
            }
        }

        $session = &Horde_Kolab_Session::singleton();

        // Update email headers
        $new_headers->addHeader('From', $session->user_mail);
        $new_headers->addHeader('To', $session->user_mail);
        $new_headers->addHeader('Date', date('r'));
        $new_headers->addHeader('X-Kolab-Type', $handlers['XML']->getMimeType());
        $new_headers->addHeader('Subject', $object['uid']);
        $new_headers->addHeader('User-Agent', 'Horde::Kolab::Storage v0.2');
        $new_headers->addMIMEHeaders($mime_message);

        $msg = preg_replace("/\r\n|\n|\r/s", "\r\n",
                            $new_headers->toString() . $mime_message->toString(false));

        // delete old email?
        if ($id != null) {
            $result = $imap->deleteMessages($id);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        // store new email
        $result = $imap->appendMessage($msg);
        if (is_a($result, 'PEAR_Error')) {
            if ($id != null) {
                $result = $imap->undeleteMessages($id);
                if (is_a($result, 'PEAR_Error')) {
                    return $result;
                }
            }
            return $result;
        }

        // remove deleted object
        if ($id != null) {
            $result = $imap->expunge();
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
        }

        $result = $this->trigger();
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage(sprintf('Failed triggering folder %s! Error was: %s',
                                      $this->name, $result->getMessage()),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        return true;
    }

    /**
     * Get an IMAP message and retrieve the Kolab Format object.
     *
     * @param int     $id             The message to retrieve.
     * @param string  $mime_type      The mime type of the part to retrieve.
     * @param boolean $parse_headers  Should the heades be MIME parsed?
     * @param array   $formats        The list of possible format parts.
     *
     * @return array|PEAR_Error An array that list the Kolab XML
     *                          object text, the mime ID of the part
     *                          with the XML object, the MIME parsed
     *                          message and the MIME parsed headers if
     *                          requested.
     */
    function parseMessage($id, $mime_type, $parse_headers = true,
                          $formats = array('XML'))
    {
        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        $raw_headers = $imap->getMessageHeader($id);
        if (is_a($raw_headers, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Failed retrieving the message with ID %s. Original error: %s."),
                                            $id, $raw_headers->getMessage()));
        }

        $body = $imap->getMessageBody($id);
        if (is_a($body, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Failed retrieving the message with ID %s. Original error: %s."),
                                            $id, $body->getMessage()));
        }

        $mime_message = MIME_Structure::parseTextMIMEMessage($raw_headers . $body);
        $parts = $mime_message->contentTypeMap();

        $mime_headers = false;
        $xml = false;

        // Read in a Kolab event object, if one exists
        $part_ids['XML'] = array_search($mime_type, $parts);
        if ($part_ids['XML'] !== false) {
            if ($parse_headers) {
                $mime_headers = MIME_Structure::parseMIMEHeaders($raw_headers);
            }

            $part = $mime_message->getPart($part_ids['XML']);
            $part->transferDecodeContents();
            $xml = $part->getContents();
        }

        $alternate_formats = array_diff(array('XML'), $formats);
        if (!empty($alternate_formats)) {
            foreach ($alternate_formats as $type) {
                $part_ids[$type] = false;
            }
            foreach ($mime_message->getParts() as $part) {
                $params = $part->getDispositionParameters();
                foreach ($alternate_formats as $type) {
                    if (isset($params['x-kolab-format'])
                        && $params['x-kolab-format'] == $type) {
                        $part_ids[$type] = $part->getMIMEId();
                    }
                }
            }
        }

        $result = array($xml, $part_ids, $mime_message, $mime_headers);
        return $result;
    }

    /**
     * Prepares a new kolab Groupeware message.
     *
     * @return string The MIME message
     */
    function _prepareNewMessage()
    {
        $mime_message = new MIME_Message();
        $kolab_text = sprintf(_("This is a Kolab Groupware object. To view this object you will need an email client that understands the Kolab Groupware format. For a list of such email clients please visit %s"),
                                'http://www.kolab.org/kolab2-clients.html');
        $part = new MIME_Part('text/plain', String::wrap($kolab_text, 76, "\r\n", NLS::getCharset()),
                                NLS::getCharset());
        $part->setTransferEncoding('quoted-printable');
        $mime_message->addPart($part);
        return $mime_message;
    }

    /**
     * Report the status of this folder.
     *
     * @return array|PEAR_Error An array listing the validity ID, the
     *                          next IMAP ID and an array of IMAP IDs.
     */
    function getStatus()
    {
        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        // Select the folder to update uidnext
        $result = $imap->select($this->name);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $status = $imap->status();
        if (is_a($status, 'PEAR_Error')) {
            return $status;
        }

        $uids = $imap->getUids();
        if (is_a($uids, 'PEAR_Error')) {
            return $uids;
        }
        return array($status['uidvalidity'], $status['uidnext'], $uids);
    }

    /**
     * Triggers any required updates after changes within the
     * folder. This is currently only required for handling free/busy
     * information with Kolab.
     *
     * @param string $name Name of the folder that should be triggered.
     *
     * @return boolean|PEAR_Error True if successfull.
     */
    function trigger($name = null)
    {
        $type =  $this->getType();
        if (is_a($type, 'PEAR_Error')) {
            return $type;
        }

        $owner = $this->getOwner();
        if (is_a($owner, 'PEAR_Error')) {
            return $owner;
        }

        $subpath = $this->getSubpath($name);
        if (is_a($subpath, 'PEAR_Error')) {
            return $subpath;
        }

        switch($type) {
        case 'event':
            $session = &Horde_Kolab_Session::singleton();
            $url = sprintf('%s/trigger/%s/%s.pfb',
                           $session->freebusy_server, $owner, $subpath);
            break;
        default:
            return true;
        }

        $result = $this->triggerUrl($url);
        if (is_a($result, 'PEAR_Error')) {
            return PEAR::raiseError(sprintf(_("Failed triggering folder %s. Error was: %s"),
                                            $this->name, $result->getMessage()));
        }
        return $result;
    }

    /**
     * Triggers a URL.
     *
     * @param string $url The URL to be triggered.
     *
     * @return boolean|PEAR_Error True if successfull.
     */
    function triggerUrl($url)
    {
        global $conf;

        if (!empty($conf['kolab']['no_triggering'])) {
            return true;
        }

        $options['method'] = 'GET';
        $options['timeout'] = 5;
        $options['allowRedirects'] = true;

        if (isset($conf['http']['proxy']) && !empty($conf['http']['proxy']['proxy_host'])) {
            $options = array_merge($options, $conf['http']['proxy']);
        }

        require_once 'HTTP/Request.php';
        $http = new HTTP_Request($url, $options);
        $http->setBasicAuth(Auth::getAuth(), Auth::getCredential('password'));
        @$http->sendRequest();
        if ($http->getResponseCode() != 200) {
            return PEAR::raiseError(sprintf(_("Unable to trigger URL %s. Response: %s"),
                                            $url, $http->getResponseCode()));
        }
        return true;
    }

    /**
     * Checks to see if a user has a given permission.
     *
     * @param string $userid       The userid of the user.
     * @param integer $permission  A PERMS_* constant to test for.
     * @param string $creator      The creator of the shared object.
     *
     * @return boolean|PEAR_Error  Whether or not $userid has $permission.
     */
    function hasPermission($userid, $permission, $creator = null)
    {
        if ($userid == $this->getOwner()) {
            return true;
        }

        $perm = &$this->getPermission();
        if (is_a($perm, 'PEAR_Error')) {
            return $perm;
        }
        return $perm->hasPermission($userid, $permission, $creator);
    }

    /**
     * Returns the permissions from this storage object.
     *
     * @return Horde_Permission_Kolab  The permissions on the share.
     */
    function &getPermission()
    {
        if (!isset($this->_perms)) {
            if ($this->exists()) {
                // The permissions are unknown but the folder exists
                // -> discover permissions
                $perms = null;
            } else {
                $perms = array(
                    'users' => array(
                        Auth::getAuth() => PERMS_SHOW | PERMS_READ |
                        PERMS_EDIT | PERMS_DELETE));
            }
            $this->_perms = &new Horde_Permission_Kolab($this, $perms);
        }
        return $this->_perms;
    }

    /**
     * Sets the permissions on the share.
     *
     * @param Horde_Permission_Kolab $perms Permission object to store on the
     *                                     object.
     * @param boolean $update              Save the updated information?
     *
     * @return boolean|PEAR_Error  True on success.
     */
    function setPermission(&$perms, $update = true)
    {
        if (!is_a($perms, 'Horde_Permission')) {
            return PEAR::raiseError('The permissions for this share must be specified as an instance of the Horde_Permission class!');
        }

        if (!is_a($perms, 'Horde_Permission_Kolab')) {
            $this->_perms = &new Horde_Permission_Kolab($this, $perms->data);
        } else {
            $this->_perms = &$perms;
            $this->_perms->setFolder($this);
        }

        if ($update) {
            return $this->save();
        }

        return true;
    }

    /**
     * Return the IMAP ACL of this folder.
     *
     * @return array|PEAR_Error  An array with IMAP ACL.
     */
    function getACL()
    {
        global $conf;

        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        if (!empty($conf['kolab']['imap']['no_acl'])) {
            $acl = array();
            $acl[Auth::getAuth()] = 'lrid';
            return $acl;
        }

        $acl = $imap->getACL($this->name);

        /*
         * Check if the getPerm comes from the owner in this case we
         * can use getACL to have all the right of the share Otherwise
         * we just ask for the right of the current user for a folder
         */
        if ($this->getOwner() == Auth::getAuth()) {
            return $acl;
        } else {
            if (!is_a($acl, 'PEAR_Error')) {
                return $acl;
            }

            $my_rights = $imap->getMyrights($this->name);
            if (is_a($my_rights, 'PEAR_Error')) {
                return $my_rights;
            }

            $acl = array();
            $acl[Auth::getAuth()] = $my_rights;
            return $acl;
        }
    }

    /**
     * Set the IMAP ACL of this folder.
     *
     * @param $user The user for whom the ACL should be set.
     * @param $acl  The new ACL value.
     *
     * @return boolean|PEAR_Error  True on success.
     */
    function setACL($user, $acl)
    {
        global $conf;

        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        if (!empty($conf['kolab']['imap']['no_acl'])) {
            return true;
        }

        $iresult = $imap->setACL($this->name, $user, $acl);
        if (is_a($iresult, 'PEAR_Error')) {
            return $iresult;
        }

        if (!empty($this->_perms)) {
            /** Refresh the cache after changing the permissions */
            $this->_perms->getPerm();
        }

        $result = $this->trigger();
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage(sprintf('Failed triggering folder %s! Error was: %s',
                                      $this->name, $result->getMessage()),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        return $iresult;
    }

    /**
     * Delete the IMAP ACL for a user on this folder.
     *
     * @param $user The user for whom the ACL should be deleted.
     *
     * @return boolean|PEAR_Error  True on success.
     */
    function deleteACL($user)
    {
        global $conf;

        $session = &Horde_Kolab_Session::singleton();
        $imap = &$session->getImap();
        if (is_a($imap, 'PEAR_Error')) {
            return $imap;
        }

        if (!empty($conf['kolab']['imap']['no_acl'])) {
            return true;
        }

        $iresult = $imap->deleteACL($this->name, $user);
        if (is_a($iresult, 'PEAR_Error')) {
            return $iresult;
        }

        $result = $this->trigger();
        if (is_a($result, 'PEAR_Error')) {
            Horde::logMessage(sprintf('Failed triggering folder %s! Error was: %s',
                                      $this->name, $result->getMessage()),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
        }

        return $iresult;
    }


    /**
     * Get annotation values on IMAP server that do not support
     * METADATA.
     *
     * @return array|PEAR_Error  The anotations of this folder.
     */
    function _getAnnotationData()
    {
        $this->_annotation_data = $this->getData('annotation');
    }


    /**
     * Get an annotation value of this folder.
     *
     * @param $key The key of the annotation to retrieve.
     *
     * @return string|PEAR_Error  The anotation value.
     */
    function _getAnnotation($key)
    {
        global $conf;

        if (empty($conf['kolab']['imap']['no_annotations'])) {
            $session = &Horde_Kolab_Session::singleton();
            $imap = &$session->getImap();
            if (is_a($imap, 'PEAR_Error')) {
                return $imap;
            }
            return $imap->getAnnotation($key, 'value.shared',
                                               $this->name);
        }

        if (!isset($this->_annotation_data)) {
            $this->_getAnnotationData();
        }
        $data = $this->_annotation_data->getObject('KOLAB_FOLDER_CONFIGURATION');
        if (is_a($data, 'PEAR_Error')) {
            Horde::logMessage(sprintf('Error retrieving annotation data on folder %s: %s',
                                      $this->name, $data->getMessage()),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return '';
        }
        if (isset($data[$key])) {
            return $data[$key];
        } else {
            return '';
        }
    }

    /**
     * Set an annotation value of this folder.
     *
     * @param $key   The key of the annotation to change.
     * @param $value The new value.
     *
     * @return boolean|PEAR_Error  True on success.
     */
    function _setAnnotation($key, $value)
    {
        if (empty($conf['kolab']['imap']['no_annotations'])) {
            $session = &Horde_Kolab_Session::singleton();
            $imap = &$session->getImap();
            if (is_a($imap, 'PEAR_Error')) {
                return $imap;
            }
            return $imap->setAnnotation($key,
                                        array('value.shared' => $value),
                                        $this->name);
        }

        if (!isset($this->_annotation_data)) {
            $this->_getAnnotationData();
        }
        $data = $this->_annotation_data->getObject('KOLAB_FOLDER_CONFIGURATION');
        if (is_a($data, 'PEAR_Error')) {
            Horde::logMessage(sprintf('Error retrieving annotation data on folder %s: %s',
                                      $this->name, $data->getMessage()),
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            $data = array();
            $uid = null;
        } else {
            $uid = 'KOLAB_FOLDER_CONFIGURATION';
        }
        $data[$key] = $value;
        $data['uid'] = 'KOLAB_FOLDER_CONFIGURATION';
        return $this->_annotation_data->save($data, $uid);
    }



    /**
     * Get the free/busy relevance for this folder
     *
     * @return int  Value containing the FB_RELEVANCE.
     */
    function getFbrelevance()
    {
        $result = $this->getKolabAttribute('incidences-for');
        if (is_a($result, 'PEAR_Error') || empty($result)) {
            return KOLAB_FBRELEVANCE_ADMINS;
        }
        switch ($result) {
        case 'admins':
            return KOLAB_FBRELEVANCE_ADMINS;
        case 'readers':
            return KOLAB_FBRELEVANCE_READERS;
        case 'nobody':
            return KOLAB_FBRELEVANCE_NOBODY;
        default:
            return KOLAB_FBRELEVANCE_ADMINS;
        }
    }

    /**
     * Set the free/busy relevance for this folder
     *
     * @param int $relevance Value containing the FB_RELEVANCE
     *
     * @return mixed  True on success or a PEAR_Error.
     */
    function setFbrelevance($relevance)
    {
        switch ($relevance) {
        case KOLAB_FBRELEVANCE_ADMINS:
            $value = 'admins';
            break;
        case KOLAB_FBRELEVANCE_READERS:
            $value = 'readers';
            break;
        case KOLAB_FBRELEVANCE_NOBODY:
            $value = 'nobody';
            break;
        default:
            $value = 'admins';
        }

        return $this->_setAnnotation(KOLAB_ANNOT_ROOT . 'incidences-for',
                                     $value);
    }

    /**
     * Get the extended free/busy access settings for this folder
     *
     * @return array  Array containing the users with access to the
     *                extended information.
     */
    function getXfbaccess()
    {
        $result = $this->getKolabAttribute('pxfb-readable-for');
        if (is_a($result, 'PEAR_Error') || empty($result)) {
            return array();
        }
        return explode(' ', $result);
    }

    /**
     * Set the extended free/busy access settings for this folder
     *
     * @param array $access  Array containing the users with access to the
     *                      extended information.
     *
     * @return mixed  True on success or a PEAR_Error.
     */
    function setXfbaccess($access)
    {
        $value = join(' ', $access);
        return $this->_setAnnotation(KOLAB_ANNOT_ROOT . 'pxfb-readable-for',
                                     $value);
    }
}
