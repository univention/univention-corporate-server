<?php
/**
 * DIMP external API interface.
 *
 * This file defines DIMP's external API interface. Other applications can
 * interact with DIMP through this API.
 *
 * $Horde: dimp/lib/api.php,v 1.17.2.2 2009-01-06 15:22:38 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @package DIMP
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
function _dimp_compose($args = array(), $extra = array())
{
    $link = _dimp_batchCompose(array($args), array($extra));
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
function _dimp_batchCompose($args = array(), $extra = array())
{
    $GLOBALS['authentication'] = 'none';
    $GLOBALS['noset_impview'] = true;
    require_once dirname(__FILE__) . '/base.php';

    $links = array();
    foreach ($args as $i => $arg) {
        if (!isset($extra[$i])) {
            $extra[$i] = array();
        }
        $extra[$i]['type'] = 'new';
        $extra[$i]['popup'] = true;
        $links[$i] = DIMP::composeLink($arg, $extra[$i]);
    }

    return $links;
}
