<?php

require_once IMP_BASE . '/lib/Imple.php';

/**
 * $Horde: dimp/lib/Dimple.php,v 1.10.2.2 2009-01-06 15:22:38 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package Dimple
 */
class Dimple extends Imple {

    /**
     * @see Imple::factory().
     */
    function factory($dimple, $params = array())
    {
        $dimple = basename($dimple);
        if (!$dimple) {
            return false;
        }

        $class = 'Dimple_' . $dimple;
        if (!class_exists($class)) {
            include_once dirname(__FILE__) . '/Dimple/' . $dimple . '.php';
            if (!class_exists($class)) {
                return false;
            }
        }

        return new $class($params);
    }

    /**
     * @see Imple::attach().
     */
    function attach()
    {
    }

}
