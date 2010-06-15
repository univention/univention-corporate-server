<?php

require_once TURBA_BASE . '/lib/AbstractObject.php';

/**
 * The Turba_Object:: class provides a set of methods for dealing with
 * individual Turba objects - whether those are people, restaurants, etc.
 *
 * $Horde: turba/lib/Object.php,v 1.15 2004/02/20 19:44:54 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @author  Jon Parise <jon@csh.rit.edu>
 * @version $Revision: 1.1.2.1 $
 * @since   Turba 0.0.1
 * @package Turba
 */
class Turba_Object extends Turba_AbstractObject {

    /**
     * Constructs a new Turba_Object() object.
     *
     * @param $source       Hash describing the object Source.
     * @param $attributes   (optional) Hash of attributes for this object.
     */
    function Turba_Object(&$source, $attributes = array())
    {
        parent::Turba_AbstractObject($source, $attributes);
        $this->attributes['__type'] = 'Object';
    }

}
