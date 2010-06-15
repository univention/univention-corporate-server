<?php
/**
 * The Turba_List:: class provides an interface for dealing with a
 * list of Turba_AbstractObjects.
 *
 * $Horde: turba/lib/List.php,v 1.39 2004/02/24 23:05:21 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Turba 0.0.1
 * @package Turba
 */
class Turba_List {

    /**
     * The array containing the Turba_Objects represented in this
     * list.
     * @var array $objects
     */
    var $objects = array();

    /**
     * An array of objects which have just been added during this page
     * load.
     * @var array $fresh
     */
    var $fresh = array();

    /**
     * The field to compare objects by.
     * @var string $_usortCriteria
     */
    var $_usortCriteria;

    /**
     * Inserts a new list.
     *
     * @param          object Turba_Object $object  The object to insert.
     * @param optional boolean             $new     This object is from a new search (defaults to true).
     */
    function insert($object, $new = true)
    {
        if (is_a($object, 'Turba_AbstractObject')) {
            $key = $object->source->name . ':' . $object->getValue('__key');
            if (!isset($this->objects[$key])) {
                if ($new) {
                    $this->fresh[$key] = 1;
                }
                $this->objects[$key] = $object;
            }
        }
    }

    /**
     * Remove an entry from the list.
     *
     * @param string $key  The key of the object to remove.
     *
     * @since Turba 1.2
     */
    function remove($key)
    {
        if (isset($this->objects[$key])) {
            unset($this->objects[$key]);
        }
    }

    /**
     * Merges an existing Turba_List into this one.
     *
     * @param          mixed   $list  The list to merge - either a Turba_List object or an array.
     * @param optional boolean $new   These objects are coming from a new search (defaults to true).
     */
    function merge($list, $new = true)
    {
        if (is_object($list)) {
            $list = $list->objects;
        }
        if (is_array($list)) {
            foreach ($list as $object) {
                $this->insert($object, $new);
            }
        }
    }

    /**
     * Reset our internal pointer to the beginning of the list. Use
     * this to hide the internal storage (array, list, etc.) from
     * client objects.
     */
    function reset()
    {
        reset($this->objects);
    }

    /**
     * Return the next Turba_Object in the list. Use this to hide
     * internal implementation details from client objects.
     *
     * @return Turba_Object $object   The next object in the list.
     */
    function next()
    {
        list(,$tmp) = each($this->objects);
        return $tmp;
    }

    /**
     * Return the number of Turba_Objects that are in the list. Use
     * this to hide internal implementation details from client
     * objects.
     *
     * @return integer $count The number of objects in the list.
     */
    function count()
    {
        return count($this->objects);
    }

    /**
     * Filters/Sorts the list based on the specified sort routine.
     *
     * @param $sort         The sort method.
     * @param $low          The low end of the sort range.
     * @param $high         The high end of the sort range.
     * @param $dir          Sort direction, 0 = ascending, 1 = descending
     */
    function sort($sort = 'lastname', $dir = 0)
    {
        global $prefs, $attributes;

        $sorted_objects = array();

        foreach ($this->objects as $key => $object) {
            $lastname = $object->getValue('lastname');
            if (!$lastname) {
                $lastname = Turba::guessLastname($object->getValue('name'));
            }
            $object->setValue('lastname', $lastname);
            $sorted_objects[$key] = $object;
        }

        $this->_usortCriteria = $sort;

        // Set the comparison type based on the type of attribute
        // we're sorting by.
        $this->_usortType = 'text';
        if (isset($attributes[$sort])) {
            if (!empty($attributes[$sort]['cmptype'])) {
                $this->_usortType = $attributes[$sort]['cmptype'];
            } elseif ($attributes[$sort]['type'] == 'int' ||
                      $attributes[$sort]['type'] == 'intlist' ||
                      $attributes[$sort]['type'] == 'number') {
                $this->_usortType = 'int';
            }
        }

        usort($sorted_objects, array($this, 'cmp'));

        if ($dir == 1) {
            $this->objects = array_reverse($sorted_objects);
        } else {
            $this->objects = $sorted_objects;
        }
    }

    /**
     * Usort helper function. Compares two Turba_AbstractObjects
     * based on the member variable $_usortCriteria, taking care
     * to sort numerically if it is an integer field.
     *
     * @param $a        The first Turba_AbstractObject to compare.
     * @param $b        The second Turba_AbstroctObject to compare.
     *
     * @return          Integer comparison of the two field values.
     */
    function cmp($a, $b)
    {
        switch ($this->_usortType) {
        case 'int':
            return ($a->getValue($this->_usortCriteria) > $b->getValue($this->_usortCriteria)) ? 1 : -1;
            break;

        case 'text':
        default:
            $acmp = String::lower($a->getValue($this->_usortCriteria), true);
            $bcmp = String::lower($b->getValue($this->_usortCriteria), true);

            // Use strcoll for locale-safe comparisons.
            return strcoll($acmp, $bcmp);
        }
    }

    function isFresh($object)
    {
        return isset($this->fresh[$object->source->name . ':' . $object->getValue('__key')]);
    }

    function serialize()
    {
        $data = array();
        $data['keys'] = array();
        $data['fresh'] = $this->fresh;
        foreach ($this->objects as $key => $object) {
            $data['keys'][] = $object->source->name . ':' . $object->getValue('__key');
        }
        return $data;
    }

    function unserialize($data)
    {
        if (!isset($data) || !is_array($data)) {
            return null;
        }

        $tmp = &new Turba_List();
        $objects = array();
        foreach ($data['keys'] as $value) {
            list($source, $key) = explode(':', $value);
            if (isset($GLOBALS['cfgSources'][$source])) {
                $sourceOb = &Turba_Source::singleton($source, $GLOBALS['cfgSources'][$source]);
                $tmp->insert($sourceOb->getObject($key));
            }
        }

        /* Not the best way of doing this, but it works for now. */
        $tmp->fresh = $data['fresh'];
        return $tmp;
    }

}
