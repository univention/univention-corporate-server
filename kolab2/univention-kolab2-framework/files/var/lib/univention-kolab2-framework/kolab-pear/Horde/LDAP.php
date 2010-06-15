<?php
/**
 * This is a utility class, every method is static.
 *
 * $Horde: framework/LDAP/LDAP.php,v 1.5 2004/01/01 15:15:52 jan Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL).  If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 2.2
 * @package Horde_LDAP
 */
class Horde_LDAP {

    /**
     * Return a boolean expression using the specified operator.
     *
     * @access public
     *
     * @param string $lhs  The attribute to test.
     * @param string $op   The operator.
     * @param string $rhs  The comparison value.
     *
     * @returns string  The LDAP search fragment.
     */
    function buildClause($lhs, $op, $rhs)
    {
        switch ($op) {
        case 'LIKE':
            return empty($rhs) ?
                sprintf('(%s=*)', $lhs) :
                sprintf('(%s=*%s*)', $lhs, $rhs);

        default:
            return sprintf('(%s%s%s)', $lhs, $op, $rhs);
        }
    }

}
