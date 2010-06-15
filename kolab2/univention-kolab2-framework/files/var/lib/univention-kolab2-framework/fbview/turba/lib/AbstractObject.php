<?php
/**
 * The Turba_AbstractObject:: class provides an interface for Turba objects -
 * people, groups, restaurants, etc.
 *
 * $Horde: turba/lib/AbstractObject.php,v 1.28 2004/04/28 20:13:39 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Turba 0.0.1
 * @package Turba
 */
class Turba_AbstractObject {

    /**
     * Underlying instance of Turba_Source.
     * @var object Turba_Source $source
     */
    var $source;

    /**
     * Hash of attributes for this contact.
     * @var array $attributes
     */
    var $attributes;

    /**
     * Constructs a new Turba_AbstractObject object.
     *
     * @param object Turba_Source $source      The source that this object came from.
     * @param array               $attributes  (optional) Hash of attributes for this object.
     */
    function Turba_AbstractObject(&$source, $attributes = array())
    {
        $this->source = &$source;
        $this->attributes = $attributes;
    }

    /**
     * Returns a key-value hash containing all properties of this
     * object.
     *
     * @return array  All properties of this object.
     */
    function getAttributes()
    {
        return $this->attributes;
    }

    /**
     * Return the name of the Turba_Source that this object is from.
     */
    function getSource()
    {
        return $this->source->name;
    }

    /**
     * Returns the value of the specified attribute.
     *
     * @param string $attribute  The attribute to retrieve.
     *
     * @return string  The value of $attribute, or the empty string.
     */
    function getValue($attribute)
    {
        if (file_exists(HORDE_BASE . '/config/hooks.php')) {
            require_once HORDE_BASE . '/config/hooks.php';
            $function = '_turba_hook_decode_' . $attribute;
            if (function_exists($function)) {
                return call_user_func($function, $this->attributes[$attribute]);
            }
        }

        if (isset($this->source->map[$attribute]) && is_array($this->source->map[$attribute])) {
            $args = array($this->source->map[$attribute]['format']);
            foreach ($this->source->map[$attribute]['fields'] as $field) {
                $args[] = $this->getValue($field);
            }
            return call_user_func_array('sprintf', $args);
        } else {
            return (isset($this->attributes[$attribute]) ? $this->attributes[$attribute] : null);
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
        if (file_exists(HORDE_BASE . '/config/hooks.php')) {
            require_once HORDE_BASE . '/config/hooks.php';
            $function = '_turba_hook_encode_' . $attribute;
            if (function_exists($function)) {
                $value = call_user_func($function, $value,
                                        $this->attributes[$attribute]);
            }
        }

        if (isset($this->source->map[$attribute]) && is_array($this->source->map[$attribute])) {
            return false;
        }

        $this->attributes[$attribute] = $value;
        return true;
    }

    /**
     * Determines whether or not the object has a value for the
     * specified attribute.
     *
     * @param string $attribute  The attribute to check.
     *
     * @return boolean  Whether or not there is a value for $attribute.
     */
    function hasValue($attribute)
    {
        if (isset($this->source->map[$attribute]) && is_array($this->source->map[$attribute])) {
            foreach ($this->source->map[$attribute]['fields'] as $field) {
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
     * Returns true if this instance is a member of a group.
     *
     * @return boolean  True if this instances is the member of a group.
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
        if (!$this->source->readonly) {
            return true;
        } elseif (isset($source['admin']) &&
                  in_array(Auth::getAuth(), $source['admin'])) {
            return true;
        } elseif ($this->hasValue('__owner') &&
                  $this->getValue('__owner') == Auth::getAuth()) {
            return true;
        }
        return false;
    }

    /**
     * Save the current state of the object to the storage backend.
     */
    function store()
    {
        $object_id = $this->source->setObject($this);
        if (is_a($object_id, 'PEAR_Error')) {
            return $object_id;
        }

        return $this->setValue('__key', $object_id);
    }

}
