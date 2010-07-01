<?php
/**
 * $Horde: horde/services/confirm.php,v 1.7.2.3 2009-01-06 15:26:20 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Identity.php';

$identity = &Identity::singleton();
list($message, $type) = $identity->confirmIdentity(Util::getFormData('h'));
$notification->push($message, $type);

$url = Horde::url('services/prefs.php', true);
$url = Util::addParameter($url, array('app' => 'horde', 'group' => 'identities'),
                          null, false);
header('Location: ' . $url);
exit;
