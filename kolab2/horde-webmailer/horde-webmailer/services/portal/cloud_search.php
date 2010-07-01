<?php
/**
 * Perform search request for the horde-wide tag cloud block.
 *
 * $Horde: horde/services/portal/cloud_search.php,v 1.1.2.4 2009-01-06 15:27:33 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.

 * @TODO: If/when more apps support the searchTags api calls, probably
 *        should not hardcode the supported apps.  Also should allow excluding
 *        of applications in the tag search
 *
 * @author Michael J. Rubinksy <mrubinsk@horde.org>
 */

require_once dirname(__FILE__) . '/../../lib/base.php';

// If/when more apps support the searchTags api calls, we should probably
// find a better solution to putting the apps hardcoded like this.
// Should also probably
$apis = array('images', 'news');

$tag = Util::getFormData('tag');
$results = $registry->call('images/searchTags', array(array($tag)));
$results = array_merge($results, $registry->call('news/searchTags',
                                                 array(array($tag))));
echo '<div class="control"><strong>'
    . sprintf(_("Results for %s"), '<span style="font-style:italic">' . htmlspecialchars($tag) . '</span>')
    . '</strong>'
    . Horde::link('#', '', '', '', '$(\'cloudsearch\').hide();', '', '', array('style' => 'font-size:75%;'))
    . '(' . _("Hide Results") . ')</a></span></div><ul class="linedRow">';

foreach ($results as $result) {
    echo '<li class="linedRow">' .
         Horde::img($result['app'] . '.png', '', '', $registry->getImageDir($result['app'])) .
         Horde::link($result['view_url'], '', '', '', '', '', '', array('style' => 'margin:4px')) .
         $result['title'] .
         '</a><span style="font-style:italic;"><div style="margin-left:10px;font-style:italic">' . $result['desc'] . '</div></li>';
}
echo '</ul>';
