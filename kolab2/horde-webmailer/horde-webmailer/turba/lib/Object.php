<?php
/**
 * The Turba_Object:: class provides a base implementation for Turba
 * objects - people, groups, restaurants, etc.
 *
 * $Horde: turba/lib/Object.php,v 1.17.10.13 2009-10-24 18:48:23 mrubinsk Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @package Turba
 */
class Turba_Object {

    /**
     * Underlying driver.
     *
     * @var Turba_Driver
     */
    var $driver;

    /**
     * Hash of attributes for this contact.
     *
     * @var array
     */
    var $attributes;

    /**
     * Reference to this object's VFS instance.
     *
     * @var VFS
     */
    var $_vfs;

    /**
     * Constructs a new Turba_Object object.
     *
     * @param Turba_Driver $driver  The source that this object came from.
     * @param array $attributes     Hash of attributes for this object.
     */
    function Turba_Object(&$driver, $attributes = array())
    {
        $this->driver = &$driver;
        $this->attributes = $attributes;
        $this->attributes['__type'] = 'Object';
    }

    /**
     * Returns a key-value hash containing all properties of this object.
     *
     * @return array  All properties of this object.
     */
    function getAttributes()
    {
        return $this->attributes;
    }

    /**
     * Returns the name of the address book that this object is from.
     */
    function getSource()
    {
        return $this->driver->getName();
    }

    /**
     * Get a fully qualified key for this contact.
     *
     * @param string $delimiter Delimiter for the parts of the key, defaults to ':'.
     *
     * @return string Fully qualified contact id.
     */
    function getGuid($delimiter = ':')
    {
        return 'turba' . $delimiter . $this->driver->getName() . $delimiter . $this->getValue('__uid');
    }

    /**
     * Returns the value of the specified attribute.
     *
     * @param string $attribute  The attribute to retrieve.
     *
     * @return mixed  The value of $attribute, an array (for photo type)
     *                or the empty string.
     */
    function getValue($attribute)
    {
        /* Cache hooks to avoid multiple file_exists() calls. */
        static $hooks;
        if (!isset($hooks)) {
            $hooks = array();
            if (is_callable(array('Horde', 'loadConfiguration'))) {
                Horde::loadConfiguration('hooks.php', null, 'turba');
            } else {
                if (file_exists(TURBA_BASE . '/config/hooks.php')) {
                    include_once TURBA_BASE . '/config/hooks.php';
                }
            }
        }
        if (!isset($hooks[$attribute])) {
            $function = '_turba_hook_decode_' . $attribute;
            if (function_exists($function)) {
                $hooks[$attribute] = $function;
            } else {
                $hooks[$attribute] = false;
            }
        }

        if (isset($this->attributes[$attribute]) &&
            !empty($hooks[$attribute])) {
            return call_user_func_array($hooks[$attribute],
                                        array($this->attributes[$attribute], &$this));
        }

        if (isset($this->driver->map[$attribute]) &&
            is_array($this->driver->map[$attribute])) {
            $args = array();
            foreach ($this->driver->map[$attribute]['fields'] as $field) {
                $value = $this->getValue($field);
                if (empty($value) && isset($this->driver->map[$attribute]['defaults'][$field])) {
                    $value = $this->driver->map[$attribute]['defaults'][$field];
                }
                $args[] = $value;
            }
            return trim(vsprintf($this->driver->map[$attribute]['format'], $args), " \t\n\r\0\x0B,");
        } elseif (!isset($this->attributes[$attribute])) {
            return null;
        } elseif (isset($GLOBALS['attributes'][$attribute]) &&
                  $GLOBALS['attributes'][$attribute]['type'] == 'image') {
            return empty($this->attributes[$attribute])
                ? null
                : array('load' => array('file' => basename(tempnam(Horde::getTempDir(), 'horde_form_')),
                                        'data' => $this->attributes[$attribute]));
        } else {
            return $this->attributes[$attribute];
        }
    }

    /**
     * Sets the value of the specified attribute.
     *
     * @param string $attribute  The attribute to set.
     * @param string $value      The value of $attribute.
     */
    function setValue($attribute, $value)
    {
        /* Cache hooks to avoid multiple file_exists() calls. */
        static $hooks;
        if (!isset($hooks)) {
            $hooks = array();
            if (is_callable(array('Horde', 'loadConfiguration'))) {
                Horde::loadConfiguration('hooks.php', null, 'turba');
            } else {
                if (file_exists(TURBA_BASE . '/config/hooks.php')) {
                    include_once TURBA_BASE . '/config/hooks.php';
                }
            }
        }
        if (!isset($hooks[$attribute])) {
            $function = '_turba_hook_encode_' . $attribute;
            if (function_exists($function)) {
                $hooks[$attribute] = $function;
            } else {
                $hooks[$attribute] = false;
            }
        }
        if ($hooks[$attribute]) {
            $value = call_user_func_array($hooks[$attribute], array($value, $this->attributes[$attribute], &$this));
        }

        if (isset($this->driver->map[$attribute]) &&
            is_array($this->driver->map[$attribute]) &&
            !isset($this->driver->map[$attribute]['attribute'])) {
            return false;
        }

        $this->attributes[$attribute] = $value;
        return true;
    }

    /**
     * Determines whether or not the object has a value for the specified
     * attribute.
     *
     * @param string $attribute  The attribute to check.
     *
     * @return boolean  Whether or not there is a value for $attribute.
     */
    function hasValue($attribute)
    {
        if (isset($this->driver->map[$attribute]) &&
            is_array($this->driver->map[$attribute])) {
            foreach ($this->driver->map[$attribute]['fields'] as $field) {
                if ($this->hasValue($field)) {
                    return true;
                }
            }
            return false;
        } else {
            return !is_null($this->getValue($attribute));
        }
    }

    /**
     * Returns true if this object is a group of multiple contacts.
     *
     * @return boolean  True if this object is a group of multiple contacts.
     */
    function isGroup()
    {
        return false;
    }

    /**
     * Returns true if this object is editable by the current user.
     *
     * @return boolean  Whether or not the current user can edit this object
     */
    function isEditable()
    {
        return $this->driver->hasPermission(PERMS_EDIT);
    }

    /**
     * Returns whether or not the current user has the requested permission.
     *
     * @param integer $perm  The permission to check.
     *
     * @return boolean True if user has the permission.
     */
    function hasPermission($perm)
    {
        return $this->driver->hasPermission($perm);
    }

    /**
     * Contact url.
     */
    function url($view = null, $full = false)
    {
        $url = Util::addParameter('contact.php',
                                  array('source' => $this->driver->name,
                                        'key' => $this->getValue('__key')));
        if (!is_null($view)) {
            $url = Util::addParameter($url, 'view', $view);
        }

        return Horde::applicationUrl($url, $full);
    }

    /**
     * Saves a file into the VFS backend associated with this object.
     *
     * @param array $info  A hash with the file information as returned from a
     *                     Horde_Form_Type_file.
     */
    function addFile($info)
    {
        $result = $this->_vfsInit();
        if (is_a($result, 'PEAR_Error')) {
            return $result;
        }

        $dir = TURBA_VFS_PATH . '/' . $this->getValue('__uid');
        $file = $info['name'];
        while ($this->_vfs->exists($dir, $file)) {
            if (preg_match('/(.*)\[(\d+)\](\.[^.]*)?$/', $file, $match)) {
                $file = $match[1] . '[' . ++$match[2] . ']' . $match[3];
            } else {
                $dot = strrpos($file, '.');
                if ($dot === false) {
                    $file .= '[1]';
                } else {
                    $file = substr($file, 0, $dot) . '[1]' . substr($file, $dot);
                }
            }
        }

        return $this->_vfs->write($dir, $file, $info['tmp_name'], true);
    }

    /**
     * Deletes a file from the VFS backend associated with this object.
     *
     * @param string $file  The file name.
     */
    function deleteFile($file)
    {
        if (!is_a($result = $this->_vfsInit(), 'PEAR_Error')) {
            return $this->_vfs->deleteFile(TURBA_VFS_PATH . '/' . $this->getValue('__uid'), $file);
        } else {
            return $result;
        }
    }

    /**
     * Deletes all files from the VFS backend associated with this object.
     */
    function deleteFiles()
    {
        if (!is_a($result = $this->_vfsInit(), 'PEAR_Error')) {
            if ($this->_vfs->exists(TURBA_VFS_PATH, $this->getValue('__uid'))) {
                return $this->_vfs->deleteFolder(TURBA_VFS_PATH, $this->getValue('__uid'), true);
            }

            return true;
        }

        return $result;
    }

    /**
     * Returns all files from the VFS backend associated with this object.
     *
     * @return array  A list of hashes with file informations.
     */
    function listFiles()
    {
        $result = $this->_vfsInit();

        if (!is_a($result, 'PEAR_Error') && $this->_vfs->exists(TURBA_VFS_PATH, $this->getValue('__uid'))) {
            return $this->_vfs->listFolder(TURBA_VFS_PATH . '/' . $this->getValue('__uid'));
        } else {
            return array();
        }
    }

    /**
     * Returns a link to display and download a file from the VFS backend
     * associated with this object.
     *
     * @param string $file  The file name.
     *
     * @return string  The HTML code of the generated link.
     */
    function vfsDisplayUrl($file)
    {
        global $registry, $mime_drivers_map, $mime_drivers;

        require_once 'Horde/MIME/Magic.php';
        require_once 'Horde/MIME/Part.php';
        require_once 'Horde/MIME/Viewer.php';
        if (is_callable(array('Horde', 'loadConfiguration'))) {
            $result = Horde::loadConfiguration('mime_drivers.php', array('mime_drivers', 'mime_drivers_map'), 'horde');
            extract($result);
            $result = Horde::loadConfiguration('mime_drivers.php', array('mime_drivers', 'mime_drivers_map'), 'turba');
            require_once 'Horde/Array.php';
            if (isset($result['mime_drivers'])) {
                $mime_drivers = Horde_Array::array_merge_recursive_overwrite($mime_drivers, $result['mime_drivers']);
            }
            if (isset($result['mime_drivers_map'])) {
                $mime_drivers_map = Horde_Array::array_merge_recursive_overwrite($mime_drivers_map, $result['mime_drivers_map']);
            }
        } else {
            require HORDE_BASE . '/config/mime_drivers.php';
            require TURBA_BASE . '/config/mime_drivers.php';
        }

        $mime_part = new MIME_Part(MIME_Magic::extToMIME($file['type']), '');
        $viewer = MIME_Viewer::factory($mime_part);

        // We can always download files.
        $url_params = array('actionID' => 'download_file',
                            'file' => $file['name'],
                            'type' => $file['type'],
                            'source' => $this->driver->name,
                            'key' => $this->getValue('__key'));
        $dl = Horde::link(Horde::downloadUrl($file['name'], $url_params), $file['name']) . Horde::img('download.png', _("Download"), '', $registry->getImageDir('horde')) . '</a>';

        // Let's see if we can view this one, too.
        if ($viewer && !is_a($viewer, 'MIME_Viewer_default')) {
            $url = Horde::applicationUrl('view.php');
            $url_params['actionID'] = 'view_file';
            $url = Util::addParameter($url, $url_params);
            $link = Horde::link($url, $file['name'], null, '_blank') . $file['name'] . '</a>';
        } else {
            $link = $file['name'];
        }

        return $link . ' ' . $dl;
    }

    /**
     * Returns a link to display, download, and delete a file from the VFS
     * backend associated with this object.
     *
     * @param string $file  The file name.
     *
     * @return string  The HTML code of the generated link.
     */
    function vfsEditUrl($file)
    {
        $delform = '<form action="deletefile.php" style="display:inline" method="post">' . Util::formInput() .
            '<input type="hidden" name="file" value="' . htmlspecialchars($file['name']) . '" />' .
            '<input type="hidden" name="source" value="' . htmlspecialchars($this->driver->name) . '" />' .
            '<input type="hidden" name="key" value="' . htmlspecialchars($this->getValue('__key')) . '" />' .
            '<input type="image" class="img" src="' . $GLOBALS['registry']->getImageDir('horde') . '/delete.png" />' .
            '</form>';

        return $this->vfsDisplayUrl($file) . ' ' . $delform;
    }

    /**
     * Saves the current state of the object to the storage backend.
     */
    function store()
    {
        $object_id = $this->driver->save($this);
        if (is_a($object_id, 'PEAR_Error')) {
            return $object_id;
        }

        return $this->setValue('__key', $object_id);
    }

    /**
     * Loads the VFS configuration and initializes the VFS backend.
     */
    function _vfsInit()
    {
        if (!isset($this->_vfs)) {
            $v_params = Horde::getVFSConfig('documents');
            if (is_a($v_params, 'PEAR_Error')) {
                Horde::fatal($v_params, __FILE__, __LINE__);
            }
            require_once 'VFS.php';
            $result = &VFS::singleton($v_params['type'], $v_params['params']);
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            } else {
                $this->_vfs = &$result;
                return true;
            }
        }
    }

}
