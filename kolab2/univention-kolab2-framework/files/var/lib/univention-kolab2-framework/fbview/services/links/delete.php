<?php
/**
 * $Horde: horde/services/links/delete.php,v 1.12 2004/04/07 14:43:45 chuck Exp $
 *
 * Generic delete API for Horde_Links 
 *
 * Copyright 2003-2004, Jeroen Huinink <j.huinink@wanadoo.nl>
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Links.php';

if (!Auth::isAuthenticated()) {
    Horde::authenticationFailureRedirect();
}

$links = &Horde_Links::singleton($registry->getApp());

$link_data = @unserialize(Util::getFormData('link_data'));
$return_url = Util::getFormData('return_url');

$result = $links->deleteLink($link_data);
if (is_a($result, 'PEAR_Error')) {
    $notification->push($result, 'horde.error');
} elseif ($registry->hasMethod($link_data['link_params']['to_application'] . '/getLinkSummary')) {
    $summary = $registry->call($link_data['link_params']['to_application']. '/getLinkSummary', array($link_data));
    if (is_a($summary, 'PEAR_Error')) {
        $summary = $summary->getMessage();
    }
    $notification->push(sprintf(_("The %s link to %s has been removed."), $link_data['link_params']['link_type'], $summary),
                        'horde.success');
} else {
    $notification->push(_("The link has been removed"), 'horde.success');
}

header('Location: ' . $return_url);
