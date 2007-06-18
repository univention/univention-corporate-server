<?php

require_once TURBA_BASE . '/lib/AbstractObject.php';

/**
 * The Turba_Group:: class provides a set of methods for dealing with
 * contact groups.
 *
 * $Horde: turba/lib/Group.php,v 1.20 2004/05/20 16:39:08 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  jon Parise <jon@csh.rit.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Turba 0.0.1
 * @package Turba
 */
class Turba_Group extends Turba_AbstractObject {

    /**
     * Constructs a new Turba_Group object.
     *
     * @param Turba_Source $source   The source object that this group comes from
     * @param array $attributes      (optional) Hash of attributes for this group.
     */
    function Turba_Group(&$source, $attributes = array())
    {
        $this->Turba_AbstractObject($source, $attributes);
        $this->attributes['__type'] = 'Group';
    }

    /**
     * Returns true if this object is a group of multiple contacts.
     *
     * @return          True if this a group of multiple contacts.
     */
    function isGroup()
    {
        return true;
    }

    /**
     * Adds a new contact entry to this group.
     *
     * @param Turba_AbstractObject $object   The object to add to the Group
     *
     * @since Turba 1.2
     */
    function addMember($object)
    {
        // Can't add itself.
        if ($object->getValue('__key') != $this->attributes['__key']) {
            $members = @unserialize($this->attributes['__members']);
            if (!is_array($members)) {
                $members = array();
            }

            $members[] = $object->getValue('__key');
            // Remove duplicates
            $members = array_unique($members);
            $this->attributes['__members'] = serialize($members);
        }
    }

    /**
     * Deletes a contact entry from this group.
     *
     * @param Turba_AbstractObject $object   The object to remove from the Group
     *
     * @since Turba 1.2
     */
    function removeMember($object)
    {
        $members = unserialize($this->attributes['__members']);
        $key = $object->getValue('__key');

        if (($i = array_search($key, $members)) !== false) {
            unset($members[$i]);
        }

        $this->attributes['__members'] = serialize($members);
        $this->store();
        return true;
    }

    /**
     * Retrieve the Objects in this group
     *
     * @param $sort_criteria     The requested sort order which is passed to
     *                           Turba_List::sort().
     *
     * @param $sort_direction    The requested sort direction which is passed to
     *                           Turba_List::sort().
     *
     * @return Turba_List        List containing the members of this group
     *
     * @since Turba 1.2
     */
    function listMembers($sort_criteria = 'lastname', $sort_direction = 0)
    {
        require_once TURBA_BASE . '/lib/List.php';
        $list = &new Turba_List();

        $children = unserialize($this->attributes['__members']);
        if (!is_array($children)) {
            $children = array();
        }

        reset($children);
        foreach ($children as $member) {
            $newMember = $this->source->getObject($member);
            if (is_object($newMember)) {
                $list->insert($newMember);
            }
        }
        $list->sort($sort_criteria, $sort_direction);

        return $list;
    }

    /**
     * Searches the group based on the provided criteria.
     *
     * TODO: Allow $criteria to contain the comparison operator (<, =, >,
     *       'like') and modify the drivers accordingly.
     *
     * @param $search_criteria   Hash containing the search criteria.
     * @param $sort_criteria     The requested sort order which is passed to
     *                           Turba_List::sort().
     *
     * @return Turba_List        The sorted, filtered list of search results.
     *
     * @since Turba 1.2
     */
    function search($search_criteria, $sort_criteria = 'lastname')
    {
        require_once TURBA_BASE . '/lib/List.php';
        $results = new Turba_List();

        /* Get all members. */
        $members = $this->listMembers($sort_criteria);

        $members->reset();
        while ($member = $members->next()) {
            $match = true;
            foreach ($search_criteria as $key => $value) {
                if ($member->hasValue($key)) {
                    if ($member->getValue($key) == $value) {
                        $match = false;
                    }
                }
            }
            if ($match) {
                $results->insert($member);
            }
        }

        /* Return the filtered (sorted) results. */
        return $results;
    }

}
