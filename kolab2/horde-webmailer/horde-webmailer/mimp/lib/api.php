<?php
/**
 * MIMP external API interface.
 *
 * This file defines MIMP's external API interface. Other applications can
 * interact with MIMP through this API.
 *
 * $Horde: mimp/lib/api.php,v 1.6.2.3 2009-01-06 15:24:53 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package MIMP
 */

$_services['compose'] = array(
    'args' => array('args' => '{urn:horde}hash', 'extra' => '{urn:horde}hash'),
    'type' => 'string'
);

$_services['batchCompose'] = array(
    'args' => array('args' => '{urn:horde}hash', 'extra' => '{urn:horde}hash'),
    'type' => 'string'
);

/**
 * Returns a compose window link.
 *
 * @param string|array $args   List of arguments to pass to compose.php.
 *                             If this is passed in as a string, it will be
 *                             parsed as a toaddress?subject=foo&cc=ccaddress
 *                             (mailto-style) string.
 * @param array $extra         Hash of extra, non-standard arguments to pass to
 *                             compose.php.
 *
 * @return string  The link to the message composition screen.
 */
function _mimp_compose($args = array(), $extra = array())
{
    $link = _mimp_batchCompose(array($args), array($extra));
    return reset($link);
}

/**
 * Return a list of compose window links.
 *
 * @param mixed $args   List of lists of arguments to pass to compose.php. If
 *                      the lists are passed in as strings, they will be parsed
 *                      as toaddress?subject=foo&cc=ccaddress (mailto-style)
 *                      strings.
 * @param array $extra  List of hashes of extra, non-standard arguments to pass
 *                      to compose.php.
 *
 * @return string  The list of links to the message composition screen.
 */
function _mimp_batchCompose($args = array(), $extra = array())
{
    $GLOBALS['authentication'] = 'none';
    $GLOBALS['noset_mimpview'] = true;
    require_once dirname(__FILE__) . '/base.php';

    $links = array();
    foreach ($args as $i => $arg) {
        if (!isset($extra[$i])) {
            $extra[$i] = array();
        }
        $extra[$i]['type'] = 'new';
        $links[$i] = MIMP::composeLink($arg, $extra[$i]);
    }

    return $links;
}
