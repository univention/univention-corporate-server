<?php
/**
 * The Turba_List:: class provides an interface for dealing with a
 * list of Turba_Objects.
 *
 * $Horde: turba/lib/List.php,v 1.41.10.8 2008-08-28 21:24:04 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @package Turba
 */
class Turba_List {

    /**
     * The array containing the Turba_Objects represented in this list.
     *
     * @var array
     */
    var $objects = array();

    /**
     * The field to compare objects by.
     *
     * @var string
     */
    var $_usortCriteria;

    /**
     * Constructor.
     */
    function Turba_List($ids = array())
    {
        if ($ids) {
            foreach ($ids as $value) {
                list($source, $key) = explode(':', $value);
                $driver = &Turba_Driver::singleton($source);
                if (is_a($driver, 'Turba_Driver')) {
                    $this->insert($driver->getObject($key));
                }
            }
        }
    }

    /**
     * Inserts a new object into the list.
     *
     * @param Turba_Object $object  The object to insert.
     */
    function insert($object)
    {
        if (is_a($object, 'Turba_Object')) {
            $key = $object->getSource() . ':' . $object->getValue('__key');
            if (!isset($this->objects[$key])) {
                $this->objects[$key] = $object;
            }
        }
    }

    /**
     * Resets our internal pointer to the beginning of the list. Use this to
     * hide the internal storage (array, list, etc.) from client objects.
     *
     * @return Turba_Object  The next object in the list.
     */
    function reset()
    {
        return reset($this->objects);
    }

    /**
     * Returns the next Turba_Object in the list. Use this to hide internal
     * implementation details from client objects.
     *
     * @return Turba_Object  The next object in the list.
     */
    function next()
    {
        list(,$tmp) = each($this->objects);
        return $tmp;
    }

    /**
     * Returns the number of Turba_Objects that are in the list. Use this to
     * hide internal implementation details from client objects.
     *
     * @return integer  The number of objects in the list.
     */
    function count()
    {
        return count($this->objects);
    }

    /**
     * Filters/Sorts the list based on the specified sort routine.
     * The default sort order is by last name, ascending.
     *
     * @param $order  Array of hashes describing sort fields.  Each hash has
     *                the following fields:
     *                'field'      =>  String sort field
     *                'ascending'  =>  Boolean indicating sort direction
     */
    function sort($order = null)
    {
        if (!$order) {
            $order = array(array('field' => 'lastname', 'ascending' => true));
        }

        $need_lastname = false;
        $last_first = $GLOBALS['prefs']->getValue('name_format') == 'last_first';
        foreach (array_keys($order) as $key) {
            if ($last_first && $order[$key]['field'] == 'name') {
                $order[$key]['field'] = 'lastname';
            }
            if ($order[$key]['field'] == 'lastname') {
                $order[$key]['field'] = '__lastname';
                $need_lastname = true;
                break;
            }
        }

        if (!$need_lastname) {
            $sorted_objects = $this->objects;
        } else {
            $sorted_objects = array();
            foreach ($this->objects as $key => $object) {
                $lastname = $object->getValue('lastname');
                if (!$lastname) {
                    $lastname = Turba::guessLastname($object->getValue('name'));
                }
                $object->setValue('__lastname', $lastname);
                $sorted_objects[$key] = $object;
            }
        }

        $this->_usortCriteria = $order;
        usort($sorted_objects, array($this, 'cmp'));
        $this->objects = $sorted_objects;
    }

    /**
     * Usort helper function.
     *
     * Compares two Turba_Objects based on the member variable
     * $_usortCriteria, taking care to sort numerically if it is an integer
     * field.
     *
     * @param Turba_Object $a  The first Turba_Object to compare.
     * @param Turba_Object $b  The second Turba_Object to compare.
     *
     * @return integer  Comparison of the two field values.
     */
    function cmp($a, $b)
    {
        foreach ($this->_usortCriteria as $field) {
            // Set the comparison type based on the type of attribute we're
            // sorting by.
            $usortType = 'text';
            if (isset($attributes[$field['field']])) {
                if (!empty($attributes[$field['field']]['cmptype'])) {
                    $usortType = $attributes[$field['field']]['cmptype'];
                } elseif ($attributes[$field['field']]['type'] == 'int' ||
                          $attributes[$field['field']]['type'] == 'intlist'||
                          $attributes[$field['field']]['type'] == 'number') {
                    $usortType = 'int';
                }
            }

            $method = 'cmp_' . $usortType;
            $result = $this->$method($a->getValue($field['field']),
                                     $b->getValue($field['field']));
            if (!$field['ascending']) {
                $result = -$result;
            }
            if ($result != 0) {
                return $result;
            }
        }
        return 0;
    }

    function cmp_text($a, $b)
    {
        $acmp = String::lower($a, true);
        $bcmp = String::lower($b, true);

        // Use strcoll for locale-safe comparisons.
        return strcoll($acmp, $bcmp);
    }

    function cmp_int($a, $b)
    {
        return ($a > $b) ? 1 : -1;
    }

}
