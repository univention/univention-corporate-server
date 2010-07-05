<?php
/**
 * $Horde: horde/services/cacheview.php,v 1.9.10.7 2009-01-06 15:26:20 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Cache.php';

$cid = Util::getFormData('cid');
if (empty($cid)) {
    exit;
}

$cache = &Horde_Cache::singleton($conf['cache']['driver'], Horde::getDriverConfig('cache', $conf['cache']['driver']));
$cdata = @unserialize($cache->get($cid, $conf['cache']['default_lifetime']));
if (!$cdata) {
    exit;
}

$browser->downloadHeaders('cacheObject', $cdata['ctype'], true, strlen($cdata['data']));
echo $cdata['data'];
