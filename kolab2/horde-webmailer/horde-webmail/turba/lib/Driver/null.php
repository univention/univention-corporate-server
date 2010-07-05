<?php
/**
 * Null Turba directory driver.
 *
 * $Horde: turba/lib/Driver/null.php,v 1.2.2.1 2005-11-10 00:02:40 mdjukic Exp $
 *
 * @author  Marko Djukic <mdjukic@horde.org>
 * @since   Turba 2.2
 * @package Turba
 */
class Turba_Driver_null extends Turba_Driver {

    /**
     * Whether this source has a readonly driver.
     *
     * @var boolean
     */
    var $readonly = true;

    /**
     *
     */
    function _init()
    {
        return true;
    }

    /**
     * Checks if the current user has the requested permissions on this
     * source.
     *
     * @param integer $perm  The permission to check for.
     *
     * @return boolean  True if the user has permission, otherwise false.
     */
     function hasPermission($perm)
     {
         switch ($perm) {
             case PERMS_EDIT: return false;
             case PERMS_DELETE: return false;
             default: return true;
         }
     }

    function _search()
    {
        return PEAR::raiseError(_("Searching is not available."));
    }

    function _read()
    {
        return PEAR::raiseError(_("Reading contacts is not available."));
    }

    function _add($attributes)
    {
        return PEAR::raiseError(_("Adding contacts is not available."));
    }

    function _delete($object_key, $object_id)
    {
        return PEAR::raiseError(_("Deleting contacts is not available."));
    }

    function _save($object_key, $object_id, $attributes)
    {
        return PEAR::raiseError(_("Saving contacts is not available."));
    }

}
