<?php
/**
 * $Horde: horde/services/images/pixel.php,v 1.14.10.7 2009-01-06 15:27:29 jan Exp $
 *
 * Copyright 2002-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/core.php';

header('Content-type: image/gif');
header('Expires: Wed, 21 Aug 1969 11:11:11 GMT');
header('Cache-Control: no-cache');
header('Cache-Control: must-revalidate');

$rgb = str_replace('#', '', Util::getFormData('c'));

$r = hexdec(substr($rgb, 0, 2));
$g = hexdec(substr($rgb, 2, 2));
$b = hexdec(substr($rgb, 4, 2));

if ($rgb) {
    printf('%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c',
           71,73,70,56,57,97,1,0,1,0,128,0,0,$r,$g,$b,0,0,0,44,0,0,0,0,1,0,1,0,0,2,2,68,1,0,59);
} else {
    printf('%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%c%',
           71,73,70,56,57,97,1,0,1,0,128,255,0,192,192,192,0,0,0,33,249,4,1,0,0,0,0,44,0,0,0,0,1,0,1,0,0,2,2,68,1,0,59);
}
