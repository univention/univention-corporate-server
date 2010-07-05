<?php

require_once TURBA_BASE . '/lib/Object.php';

/**
 * The Turba_Object_Group:: class provides a set of methods for dealing with
 * contact groups.
 *
 * $Horde: turba/lib/Object/Group.php,v 1.9.2.4 2008-02-15 16:44:07 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @package Turba
 */
class Turba_Object_Group extends Turba_Object {

    /**
     * Constructs a new Turba_Object_Group.
     *
     * @param Turba_Driver $driver  The driver object that this group comes
     *                              from.
     * @param array $attributes     Hash of attributes for this group.
     */
    function Turba_Object_Group(&$driver, $attributes = array())
    {
        parent::Turba_Object($driver, $attributes);
        $this->attributes['__type'] = 'Group';
    }

    /**
     * Returns true if this object is a group of multiple contacts.
     *
     * @return boolean  True.
     */
    function isGroup()
    {
        return true;
    }

    /**
     * Contact url.
     */
    function url($view = null, $full = false)
    {
        $url = Util::addParameter('browse.php',
                                  array('source' => $this->getSource(),
                                        'key' => $this->getValue('__key')));
        return Horde::applicationUrl($url, $full);
    }

    /**
     * Adds a new contact entry to this group.
     *
     * @param string $contactId  The id of the contact to add.
     * @param string $sourceId   The source $contactId is from.
     *
     * @since Turba 1.2
     */
    function addMember($contactId, $sourceId = null)
    {
        // Default to the same source as the group.
        if (is_null($sourceId)) {
            $sourceId = $this->getSource();
        }

        // Can't add a group to itself.
        if ($contactId == $this->attributes['__key']) {
            return PEAR::raiseError(_("Can't add a group to itself."));
        }

        // Try to find the contact being added.
        if ($sourceId == $this->getSource()) {
            $contact = $this->driver->getObject($contactId);
        } else {
            $driver = &Turba_Driver::singleton($sourceId);
            if (is_a($driver, 'PEAR_Error')) {
                return $driver;
            }
            $contact = $driver->getObject($contactId);
        }

        // Bail out if the contact being added doesn't exist or can't
        // be retrieved.
        if (is_a($contact, 'PEAR_Error')) {
            return $contact;
        }

        // Explode members.
        $members = @unserialize($this->attributes['__members']);
        if (!is_array($members)) {
            $members = array();
        }

        // If the contact is from a different source, store its source
        // id as well.
        if ($sourceId == $this->getSource()) {
            $members[] = $contactId;
        } else {
            $members[] = $sourceId . ':' . $contactId;
        }

        // Remove duplicates.
        $members = array_unique($members);

        $this->attributes['__members'] = serialize($members);

        return true;
    }

    /**
     * Deletes a contact from this group.
     *
     * @param string $contactId  The id of the contact to remove.
     * @param string $sourceId   The source $contactId is from.
     *
     * @since Turba 1.2
     */
    function removeMember($contactId, $sourceId = null)
    {
        $members = @unserialize($this->attributes['__members']);

        if (is_null($sourceId) || $sourceId == $this->getSource()) {
            $i = array_search($contactId, $members);
        } else {
            $i = array_search($sourceId . ':' . $contactId, $members);
        }

        if ($i !== false) {
            unset($members[$i]);
        }

        $this->attributes['__members'] = serialize($members);

        return true;
    }

    /**
     * Count the number of contacts in this group.
     *
     * @return integer
     *
     * @since Turba 2.1.7
     */
    function count()
    {
        $children = @unserialize($this->attributes['__members']);
        if (!is_array($children)) {
            return 0;
        } else {
            return count($children);
        }
    }

    /**
     * Retrieve the Objects in this group
     *
     * @param array $sort   The requested sort order which is passed to
     *                      Turba_List::sort().
     *
     * @return Turba_List   List containing the members of this group
     *
     * @since Turba 1.2
     */
    function &listMembers($sort = null)
    {
        require_once TURBA_BASE . '/lib/List.php';
        $list = &new Turba_List();

        $children = unserialize($this->attributes['__members']);
        if (!is_array($children)) {
            $children = array();
        }

        reset($children);
        $modified = false;
        foreach ($children as $member) {
            if (strpos($member, ':') === false) {
                $contact = $this->driver->getObject($member);
                if (is_a($contact, 'PEAR_Error')) {
                    // Remove the contact if it no longer exists
                    $this->removeMember($member);
                    $modified = true;
                }
            } else {
                list($sourceId, $contactId) = explode(':', $member, 2);
                if (strpos($contactId, ':')) {
                    list($owner, $contactId) = explode(':', $contactId, 2);
                    $sourceId .= ':' . $owner;
                }
                $driver = &Turba_Driver::singleton($sourceId);
                if (!is_a($driver, 'PEAR_Error')) {
                    $contact = $driver->getObject($contactId);
                    if (is_a($contact, 'PEAR_Error')) {
                        continue;
                    }
                } else {
                    continue;
                }
            }

            $list->insert($contact);
        }

        // If we've pruned any dead entries, store the changes.
        if ($modified) {
            $this->store();
        }

        $list->sort($sort);
        return $list;
    }

}
