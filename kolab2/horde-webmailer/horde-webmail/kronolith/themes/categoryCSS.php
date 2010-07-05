<?php
/**
 * $Horde: kronolith/themes/categoryCSS.php,v 1.4.2.7 2009-01-06 15:24:50 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Chuck Hagenbuch <chuck@horde.org>
 */

@define('AUTH_HANDLER', true);
@define('KRONOLITH_BASE', dirname(__FILE__) . '/..');
require_once KRONOLITH_BASE . '/lib/base.php';
require_once 'Horde/Image.php';

header('Content-Type: text/css');

$colors = $cManager->colors();
$fgColors = $cManager->fgColors();
foreach ($colors as $category => $color) {
    if ($category == '_unfiled_') {
        continue;
    } elseif ($category == '_default_') {
        echo '.month-eventBox, .week-eventBox, .day-eventBox, .block-eventBox, .legend-eventBox, ',
            '.month-eventBox a, .week-eventBox a, .day-eventBox a, .block-eventBox a, .legend-eventBox a, ',
            '.month-eventBox a:hover, .week-eventBox a:hover, .day-eventBox a:hover, .block-eventBox a:hover, .legend-eventBox a:hover { ';
    } else {
        $class = '.category' . md5($category);
        echo "$class, .linedRow td$class, $class a, $class a:hover { ";
    }

    echo 'color: ' . (isset($fgColors[$category]) ? $fgColors[$category] : $fgColors['_default_']) . '; ',
        'background: ' . $color . "; }\n";
}
