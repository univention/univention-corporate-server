<div id="footer">
<?php
require_once 'Horde/Text.php';
if ($GLOBALS['prefs']->getValue('show_legend') && count($eventCategories)) {
    $html = '';

    ksort($eventCategories);
    foreach ($eventCategories as $category => $v) {
        if (empty($category)) {
            continue;
        }

        $html .= ' <span class="legend-eventbox event category' . md5($category) . '">' .
            Text::htmlAllSpaces($category) . '</span>';
    }

    if (Auth::getAuth() && (!$GLOBALS['prefs']->isLocked('categories') ||
                            !$GLOBALS['prefs']->isLocked('category_colors'))) {
        $categoryUrl = Util::addParameter(Horde::url($GLOBALS['registry']->get('webroot', 'horde') . '/services/prefs.php'), array('app' => 'horde', 'group' => 'categories'));
        $html .= ' ' . Horde::link($categoryUrl, _("Edit categories and colors"), 'iconEdit', '_blank', 'popup(this.href); return false;') . Horde::img('colorpicker.png', _("Edit categories and colors"), '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
    }

    echo $html;
}
?>
</div>
