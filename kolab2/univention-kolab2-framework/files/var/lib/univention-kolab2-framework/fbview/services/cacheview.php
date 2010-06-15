<?php
/**
 * $Horde: horde/services/cacheview.php,v 1.8 2004/04/07 14:43:45 chuck Exp $
 *
 * Copyright 2002-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Cache.php';

$cid = Util::getFormData('cid');
if (empty($cid)) {
    _cacheError();
}

$cache = &Horde_Cache::singleton($conf['cache']['driver'], Horde::getDriverConfig('cache', $conf['cache']['driver']));
$cdata = unserialize($cache->getData($cid, "_cacheError('$cid')", $conf['cache']['default_lifetime']));

$browser->downloadHeaders('cacheObject', $cdata['ctype'], true, strlen($cdata['data']));
echo $cdata['data'];

/**
 * Output an error if no CID was specified or the data wasn't in the
 * cache.
 */
function _cacheError($cid = null)
{
    if (!is_null($cid)) {
        Horde::logMessage('CID ' . $cid . ' not found in the cache, unable to display.', __FILE__, __LINE__, PEAR_LOG_ERR);
    }
    exit;
}
