<?php

require_once 'Horde/Template.php';

/**
 * This class represent a view of multiple free busy information sets.
 *
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information.
 *
 * $Horde: kronolith/lib/FBView.php,v 1.5 2004/05/03 02:29:50 chuck Exp $
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @package Kronolith
 */
class Kronolith_FreeBusy_View {

    var $_requiredMembers = array();
    var $_optionalMembers = array();

    function addRequiredMember(&$vFreebusy)
    {
        $this->_requiredMembers[] = $vFreebusy;
    }

    function addOptionalMember(&$vFreebusy)
    {
        $this->_optionalMembers[] = $vFreebusy;
    }

    /**
     * Attempts to return a concrete Kronolith_FreeBusy_View instance based on $view.
     *
     * @param string    $view       The type of concrete Kronolith_FreeBusy_View subclass
     *                              to return.
     *
     * @return mixed    The newly created concrete Kronolith_FreeBusy_View instance, or
     *                  false on an error.
     */
    function &factory($view)
    {
        $driver = basename($view);
        require_once dirname(__FILE__) . '/FBView/' . $view . '.php';
        $class = 'Kronolith_FreeBusy_View_' . $view;
        if (class_exists($class)) {
            return $ret = &new $class($user, $params);
        } else {
            return false;
        }
    }

    /**
     * Attempts to return a reference to a concrete
     * Kronolith_FreeBusy_View instance based on $view.  It will only
     * create a new instance if no Kronolith_FreeBusy_View instance
     * with the same parameters currently exists.
     *
     * This method must be invoked as: $var = &Kronolith_FreeBusy_View::singleton()
     *
     * @param string    $view       The type of concrete Kronolith_FreeBusy_View subclass
     *                              to return.
     *
     * @return mixed    The created concrete Kronolith_FreeBusy_View instance, or
     *                  false on an error.
     */
    function &singleton($view)
    {
        static $instances;

        if (!isset($instances)) {
            $instances = array();
        }

        if (!isset($instances[$view])) {
            $instances[$view] = &Kronolith_FreeBusy_View::factory($view);
        }

        return $instances[$view];
    }

}
