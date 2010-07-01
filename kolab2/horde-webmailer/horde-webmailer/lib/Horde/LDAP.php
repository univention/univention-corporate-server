<?php
/**
 * This is a utility class, every method is static.
 *
 * $Horde: framework/LDAP/LDAP.php,v 1.5.12.15 2009-01-06 15:23:19 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 2.2
 * @package Horde_LDAP
 */
class Horde_LDAP {

    /**
     * Return a boolean expression using the specified operator.
     *
     * @static
     *
     * @param string $lhs    The attribute to test.
     * @param string $op     The operator.
     * @param string $rhs    The comparison value.
     * @param array $params  Any additional parameters for the operator. @since
     *                       Horde 3.2
     *
     * @return string  The LDAP search fragment.
     */
    function buildClause($lhs, $op, $rhs, $params = array())
    {
        switch ($op) {
        case 'LIKE':
            if (empty($rhs)) {
                return '(' . $lhs . '=*)';
            } elseif (!empty($params['begin'])) {
                return sprintf('(|(%s=%s*)(%s=* %s*))', $lhs, Horde_LDAP::quote($rhs), $lhs, Horde_LDAP::quote($rhs));
            } elseif (!empty($params['approximate'])) {
                return sprintf('(%s=~%s)', $lhs, Horde_LDAP::quote($rhs));
            }
            return sprintf('(%s=*%s*)', $lhs, Horde_LDAP::quote($rhs));

        default:
            return sprintf('(%s%s%s)', $lhs, $op, Horde_LDAP::quote($rhs));
        }
    }

    /**
     * Escape characters with special meaning in LDAP searches.
     *
     * @static
     *
     * @param string $clause  The string to escape.
     *
     * @return string  The escaped string.
     */
    function quote($clause)
    {
        return str_replace(array('\\',   '(',  ')',  '*',  "\0"),
                           array('\\5c', '\(', '\)', '\*', "\\00"),
                           $clause);
    }

    /**
     * Take an array of DN elements and properly quote it according to RFC
     * 1485.
     *
     * @static
     *
     * @param array $parts  An array of tuples containing the attribute
     *                      name and that attribute's value which make
     *                      up the DN. Example:
     *
     *    $parts = array(0 => array('cn', 'John Smith'),
     *                   1 => array('dc', 'example'),
     *                   2 => array('dc', 'com'));
     *
     * @return string  The properly quoted string DN.
     */
    function quoteDN($parts)
    {
        $dn = '';
        $count = count($parts);
        for ($i = 0; $i < $count; $i++) {
            if ($i > 0) {
                $dn .= ',';
            }
            $dn .= $parts[$i][0] . '=';

            // See if we need to quote the value.
            if (preg_match('/^\s|\s$|\s\s|[,+="\r\n<>#;]/', $parts[$i][1])) {
                $dn .= '"' . str_replace('"', '\\"', $parts[$i][1]) . '"';
            } else {
                $dn .= $parts[$i][1];
            }
        }

        return $dn;
    }

}
