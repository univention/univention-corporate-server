<?php
/**
 * $Horde: framework/Share/Share/kolab.php,v 1.42.2.21 2009-01-06 15:23:36 jan Exp $
 *
 * @package Horde_Share
 */

/** Kolab */
require_once 'Horde/Kolab.php';

/**
 * Horde_Share_kolab:: provides the kolab backend for the horde share driver.
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @since   Horde 3.2
 * @package Horde_Share
 */
class Horde_Share_kolab extends Horde_Share {

    /**
     * Our Kolab folder list handler
     *
     * @var Kolab_List
     */
    var $_list;

    /**
     * The share type
     *
     * @var string
     */
    var $_type;

    /**
     * A marker for the validity of the list cache
     *
     * @var int
     */
    var $_listCacheValidity;

    /**
     * Initializes the object.
     */
    function __wakeup()
    {
        if (empty($GLOBALS['conf']['kolab']['enabled'])) {
            Horde::fatal('You must enable the kolab settings to use the Kolab Share driver.', __FILE__, __LINE__);
        }

        $app_consts = Kolab::getAppConsts($this->_app);
        if (is_a($app_consts, 'PEAR_Error')) {
            return $app_consts;
        }
        $this->_type = $app_consts['folder_type'];

        $this->_list = Kolab_List::singleton();

        parent::__wakeup();
    }

    /**
     * Returns the properties that need to be serialized.
     *
     * @return array  List of serializable properties.
     */
    function __sleep()
    {
        $properties = get_object_vars($this);
        unset($properties['_sortList'], $properties['_list']);
        $properties = array_keys($properties);
        return $properties;
    }

    /**
     * Returns a Horde_Share_Object_kolab object of the request folder.
     *
     * @param string $object  The share to fetch.
     *
     * @return Horde_Share_Object_kolab  The share object.
     */
    function &_getShare($object)
    {
        if (empty($object)) {
            $error = PEAR::raiseError('No object requested.');
            return $error;
        }

        /** Get the corresponding folder for this share ID */
        $folder = $this->_list->getByShare($object, $this->_type);
        if (is_a($folder, 'PEAR_Error')) {
            return $folder;
        }

        /** Does the folder exist? */
        if (!$folder->exists()) {
            return PEAR::raiseError(sprintf(_("Share \"%s\" does not exist."), $object));
        }

        /** Create the object from the folder */
        $share = new Horde_Share_Object_kolab($object, $this->_type);
        $result = $share->setFolder($folder);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        return $share;
    }

    /**
     * Returns a Horde_Share_Object_kolab object of the requested folder.
     *
     * @param string $id  The id of the share to fetch.
     *
     * @return Horde_Share_Object_kolab  The share object.
     */
    function &_getShareById($id)
    {
        return $this->_getShare($id);
    }

    /**
     * Returns an array of Horde_Share_Object_kolab objects corresponding to
     * the requested folders.
     *
     * @param string $ids  The ids of the shares to fetch.
     *
     * @return array  An array of Horde_Share_Object_kolab objects.
     */
    function &_getShares($ids)
    {
        $objects = array();
        foreach ($ids as $id) {
            $result = &$this->_getShare($id);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }
            $objects[$id] = &$result;
        }
        return $objects;
    }

    /**
     * Lists *all* shares for the current app/share, regardless of
     * permissions.
     *
     * Currently not implemented in this class.
     *
     * @return array  All shares for the current app/share.
     */
    function &_listAllShares()
    {
        $shares = array();
        return $shares;
    }

    /**
     * Returns an array of all shares that $userid has access to.
     *
     * @param string $userid     The userid of the user to check access for.
     * @param integer $perm      The level of permissions required.
     * @param mixed $attributes  Restrict the shares counted to those
     *                           matching $attributes. An array of
     *                           attribute/values pairs or a share owner
     *                           username.
     *
     * @return array  The shares the user has access to.
     */
    function &_listShares($userid, $perm = PERMS_SHOW, $attributes = null,
                          $from = 0, $count = 0, $sort_by = null,
                          $direction = 0)
    {
        $key = serialize(array($this->_type, $userid, $perm, $attributes));
        if (empty($this->_listCache[$key]) 
            || $this->_list->validity != $this->_listCacheValidity) {
            $sharelist = $this->_list->getByType($this->_type);
            if (is_a($sharelist, 'PEAR_Error')) {
                return $sharelist;
            }

            $shares = array();
            foreach ($sharelist as $folder) {
                $id = $folder->getShareId();
                $share = &$this->getShare($id);
                if (is_a($share, 'PEAR_Error')) {
                    return $share;
                }

                $keep = true;
                if (!$share->hasPermission($userid, $perm)) {
                    $keep = false;
                }
                if (isset($attributes) && $keep) {
                    if (is_array($attributes)) {
                        foreach ($attributes as $key => $value) {
                            if (!$share->get($key) == $value) {
                                $keep = false;
                                break;
                            }
                        }
                    } elseif (!$share->get('owner') == $attributes) {
                        $keep = false;
                    }
                }
                if ($keep) {
                    $shares[] = $id;
                }
            }
            $this->_listCache[$key] = $shares;
            $this->_listCacheValidity = $this->_list->validity;
        }

        return $this->_listCache[$key];
    }

    /**
     * Returns the number of shares that $userid has access to.
     *
     * @since Horde 3.2
     *
     * @param string $userid     The userid of the user to check access for.
     * @param integer $perm      The level of permissions required.
     * @param mixed $attributes  Restrict the shares counted to those
     *                           matching $attributes. An array of
     *                           attribute/values pairs or a share owner
     *                           username.
     *
     * @return integer  The number of shares
     */
    function _countShares($userid, $perm = PERMS_SHOW, $attributes = null)
    {
        $shares = $this->_listShares($userid, $perm, $attributes);
        if (is_a($share, 'PEAR_Error')) {
            return $share;
        }

        return count($shares);
    }

    /**
     * Returns a new share object.
     *
     * @param string $name  The share's name.
     *
     * @return Horde_Share_Object_kolab  A new share object.
     */
    function &_newShare($name)
    {
        $storageObject = &new Horde_Share_Object_kolab($name, $this->_type);
        return $storageObject;
    }

    /**
     * Adds a share to the shares system.
     *
     * The share must first be created with Horde_Share_kolab::_newShare(),
     * and have any initial details added to it, before this function is
     * called.
     *
     * @param Horde_Share_Object_kolab $share  The new share object.
     */
    function _addShare(&$share)
    {
        return $share->save();
    }

    /**
     * Removes a share from the shares system permanently.
     *
     * @param Horde_Share_Object_kolab $share  The share to remove.
     */
    function _removeShare(&$share)
    {
        $share_id = $share->getName();

        $result = $share->delete();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
    }

    /**
     * Checks if a share exists in the system.
     *
     * @param string $share  The share to check.
     *
     * @return boolean  True if the share exists.
     */
    function _exists($object)
    {
        if (empty($object)) {
            return false;
        }

        /** Get the corresponding folder for this share ID */
        $folder = $this->_list->getByShare($object, $this->_type);
        if (is_a($folder, 'PEAR_Error')) {
            return $folder;
        }

        return $folder->exists();
    }

    /**
     * Create a default share for the current app
     *
     * @return string The share ID of the new default share.
     */
    function getDefaultShare()
    {
        $default = $this->_list->getDefault($this->_type);
        if (is_a($default, 'PEAR_Error')) {
            return $default;
        }
        if ($default !== false) {
            return $this->getShare($default->getShareId());
        }

        /** Okay, no default folder yet */
        $share = $this->newShare(Auth::getAuth());
        if (is_a($share, 'PEAR_Error')) {
            return $share;
        }
        /** The value does not matter here as the share will rewrite it */
        $share->set('name', '');
        $result = $this->addShare($share);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }
        return $share;
    }
}

/**
 * Extension of the Horde_Share_Object class for handling Kolab share
 * information.
 *
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @author  Gunnar Wrobel <wrobel@pardus.de>
 * @since   Horde 3.2
 * @package Horde_Share
 */
class Horde_Share_Object_kolab extends Horde_Share_Object {

    /**
     * The Kolab folder this share is based on.
     *
     * @var Kolab_Folder
     */
    var $_folder;

    /**
     * The Kolab folder name.
     *
     * @var string
     */
    var $_folder_name;

    /**
     * A cache for the share attributes.
     *
     * @var array
     */
    var $_data;

    /**
     * Our Kolab folder list handler
     *
     * @var Kolab_List
     */
    var $_list;

    /**
     * Constructor.
     *
     * Sets the folder name.
     *
     * @param string $id  The share id.
     */
    function Horde_Share_Object_kolab($id, $type)
    {
        // We actually ignore the random id string that all horde apps provide
        // as initial name and wait for a set('name', 'xyz') call. But we want
        // to know if we should create a default share.
        if ($id == Auth::getAuth()) {
            $this->_data['default'] = true;
        } else {
            $this->_data['default'] = false;
        }
        $this->_type = $type;
        $this->__wakeup();
    }

    /**
     * Associates a Share object with this share.
     *
     * @param Horde_Share $shareOb  The Share object.
     */
    function setShareOb(&$shareOb)
    {
        /** Ignore the parent as we don't need it */
    }

    /**
     * Initializes the object.
     */
    function __wakeup()
    {
        $this->_list = Kolab_List::singleton();
        if (isset($this->_folder_name)) {
            $this->_folder = $this->_list->getFolder($this->_folder_name);
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
        unset($properties['_shareOb'], $properties['_list'],
              $properties['_folder']);
        $properties = array_keys($properties);
        return $properties;
    }

    /**
     * Returns the default share name for the current application.
     *
     * @return string  The default share name.
     */
    function getDefaultShareName()
    {
        switch ($this->_type) {
        case 'contact':
            return _("Contacts");
        case 'note':
            return _("Notes");
        case 'event':
            return _("Calendar");
        case 'task':
            return _("Tasks");
        case 'filter':
            return _("Filters");
        case 'h-prefs':
            return _("Preferences");
        }
    }

    /**
     * Sets the folder for this storage object.
     *
     * @param string $folder  Name of the Kolab folder.
     * @param array  $perms  The permissions of the folder if they are known.
     */
    function setFolder(&$folder)
    {
        if (!isset($this->_folder)) {
            $this->_folder = &$folder;
            $this->_folder_name = $folder->name;
        } else {
            return PEAR::raiseError(_("The share has already been initialized!"));
        }
    }

    /**
     * Returns the ID of this share.
     *
     * @return string  The share's ID.
     */
    function _getId()
    {
        return $this->_folder->getShareId();
    }

    /**
     * Returns the name of this share.
     *
     * @return string  The share's name.
     */
    function _getName()
    {
        return $this->_folder->getShareId();
    }

    /**
     * Returns an attribute value from this object.
     *
     * @param string $attribute  The attribute to return.
     *
     * @return mixed  The value for $attribute.
     */
    function _get($attribute)
    {
        if (isset($this->_data[$attribute])) {
            return $this->_data[$attribute];
        }
        
        if (!isset($this->_folder)) {
            return $this->_folderError();
        }

        switch ($attribute) {
        case 'owner':
            $this->_data['owner'] = $this->_folder->getOwner();
            break;

        case 'name':
            $this->_data['name'] = $this->_folder->getTitle();
            break;

        case 'type':
            $this->_data['type'] = $this->_folder->getType();
            break;

        case 'params':
            $params = @unserialize($this->_folder->getAttribute('params'));
            $default = array('source' => 'kolab',
                             'default' => $this->get('default'),
                             'name' => $this->get('name'));
            $type = $this->get('type');
            if (!is_a($type, 'PEAR_Error') && $type == 'event') {
                $default = array_merge($default, array(
                                           'fbrelevance' => $this->_folder->getFbrelevance(),
                                           'xfbaccess'   => $this->_folder->getXfbaccess()
                                       ));
            }
            if (is_a($params, 'PEAR_Error') || $params == '') {
                $params = $default;
            }
            $this->_data['params'] = serialize(array_merge($default, $params));
            break;

        case 'default':
            $this->_data['default'] = $this->_folder->isDefault();
            break;

        default:
            $annotation = $this->_folder->getAttribute($attribute);
            if (is_a($annotation, 'PEAR_Error') || empty($annotation)) {
                $annotation = '';
            }
            $this->_data[$attribute] = $annotation;
            break;
        }

        return $this->_data[$attribute];
    }

    /**
     * Sets an attribute value in this object.
     *
     * @param string $attribute  The attribute to set.
     * @param mixed $value       The value for $attribute.
     *
     * @return mixed  True if setting the attribute did succeed, a PEAR_Error
     *                otherwise.
     */
    function _set($attribute, $value)
    {
        switch ($attribute) {
        case 'name':
            /* On folder creation of default shares we wish to ignore
             * the names provided by the Horde applications. We use
             * the Kolab default names. */
            if (!isset($this->_folder)) {
                if ($this->get('default')) {
                    $value = $this->getDefaultShareName();
                }
                $this->setFolder($this->_list->getNewFolder());
            }
            $this->_folder->setName($value);
            $this->_data['name'] = $this->_folder->getTitle();
            break;

        case 'params':
            $value = unserialize($value);
            if (isset($value['default'])) {
                $this->_data['default'] = $value['default'];
                unset($value['default']);
            }
            $value = serialize($value);

        default:
            $this->_data[$attribute] = $value;
        }
    }

    /**
     * Saves the current attribute values.
     */
    function _save()
    {
        if (!isset($this->_folder)) {
            return $this->_folderError();
        }

        $data = $this->_data;
        /** The name is handled immediately when set */
        unset($data['name']);
        $data['type'] = $this->_type;
        
        $result = $this->_folder->save($data);
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        /** The name may have changed */
        $this->_data['name'] = $this->_folder->getTitle();
        $this->_folder_name = $this->_folder->name;
        return true;
    }

    /**
     * Delete this share.
     *
     * @return boolean|PEAR_Error  True on success.
     */
    function delete()
    {
        if (!isset($this->_folder)) {
            return $this->_folderError();
        }
        return $this->_folder->delete();
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
        if (!isset($this->_folder)) {
            return $this->_folderError();
        }
        return $this->_folder->hasPermission($userid, $permission, $creator);
    }

    /**
     * Returns the permissions from this storage object.
     *
     * @return Horde_Permission_Kolab|PEAR_Error  The permissions on the share.
     */
    function &getPermission()
    {
        if (!isset($this->_folder)) {
            return $this->_folderError();
        }
        return $this->_folder->getPermission();
    }

    /**
     * Sets the permissions on the share.
     *
     * @param Horde_Permission_Kolab $perms Permission object to folder on the
     *                                     object.
     * @param boolean $update              Save the updated information?
     *
     * @return boolean|PEAR_Error  True on success.
     */
    function setPermission(&$perms, $update = true)
    {
        if (!isset($this->_folder)) {
            return $this->_folderError();
        }
        return $this->_folder->setPermission($perms, $update);
    }

    /**
     * Return a standard error in case the share has not been
     * correctly initialized.
     *
     * @return PEAR_Error  The PEAR_Error to return.
     */
    function _folderError() 
    {
        return PEAR::raiseError(_("The Kolab share object has not been initialized yet!"));
    }
}
