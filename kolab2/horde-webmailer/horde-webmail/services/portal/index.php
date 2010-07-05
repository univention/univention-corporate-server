<?php
/**
 * $Horde: horde/services/portal/index.php,v 1.39.10.18 2009-01-06 15:27:33 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Mike Cochrane <mike@graftonhall.co.nz>
 */

require_once dirname(__FILE__) . '/../../lib/base.php';
require_once 'Horde/Block/Collection.php';
require_once 'Horde/Block/Layout/View.php';
require_once 'Horde/Identity.php';

if (!Auth::isAuthenticated()) {
    Horde::authenticationFailureRedirect();
}

// Get full name.
$identity = &Identity::singleton();
$fullname = $identity->getValue('fullname');
if (empty($fullname)) {
    $fullname = Auth::removeHook(Auth::getAuth());
}

// Get refresh interval.
if (($r_time = $prefs->getValue('summary_refresh_time'))
    && !$browser->hasFeature('xmlhttpreq')) {
    $refresh_time = $r_time;
    $refresh_url = Horde::applicationUrl('services/portal/');
}

// Load layout from preferences.
$layout_pref = @unserialize($prefs->getValue('portal_layout'));
if (!is_array($layout_pref)) {
    $layout_pref = array();
}
if (!count($layout_pref)) {
    $layout_pref = Horde_Block_Collection::getFixedBlocks();
}

// If we're serving a request to the JS update client, just return the blocks
// updated HTML content.
if (Util::getFormData('httpclient')) {
    header('Content-Type: text/html; charset=' . NLS::getCharset());
    $row = Util::getFormData('row');
    $col = Util::getFormData('col');
    if (!is_null($row) && !is_null($col) && !empty($layout_pref[$row][$col])) {
        $item = $layout_pref[$row][$col];
        $block = &Horde_Block_Collection::getBlock($item['app'], $item['params']['type'], $item['params']['params'], $row, $col);
        $content = $block->getContent();
        if (is_a($content, 'PEAR_Error')) {
            $content = $content->getMessage();
        }
        echo $content;
    }
    exit;
}

// Render layout.
$view = new Horde_Block_Layout_View(
    $layout_pref,
    Horde::applicationUrl('services/portal/edit.php'),
    Horde::applicationUrl('services/portal/index.php', true));
$layout_html = $view->toHtml();
$cssApps = $view->getApplications();
$linkTags = $view->getLinkTags();

Horde::addScriptFile('prototype.js', 'horde', true);
$title = _("My Portal");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/menu/menu.inc';
echo '<div id="menuBottom">';
echo htmlspecialchars($fullname);
if (!$prefs->isLocked('portal_layout')) {
    echo ' | <a href="' . Horde::applicationUrl('services/portal/edit.php') . '">' . _("Add Content") . '</a>';
}
echo '</div><br class="clear" />';
$notification->notify(array('listeners' => 'status'));
echo $layout_html;
require HORDE_TEMPLATES . '/common-footer.inc';
