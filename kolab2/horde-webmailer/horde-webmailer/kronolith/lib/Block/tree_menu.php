<?php

$block_name = _("Menu List");
$block_type = 'tree';

/**
 * $Horde: kronolith/lib/Block/tree_menu.php,v 1.10.8.2 2007-12-20 14:12:34 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_kronolith_tree_menu extends Horde_Block {

    var $_app = 'kronolith';

    function _buildTree(&$tree, $indent = 0, $parent = null)
    {
        global $registry;

        $menus = array(
            array('new', _("New Event"), 'new.png', Horde::applicationUrl('new.php')),
            array('day', _("Day"), 'dayview.png', Horde::applicationUrl('day.php')),
            array('work', _("Work Week"), 'workweekview.png', Horde::applicationUrl('workweek.php')),
            array('week', _("Week"), 'weekview.png', Horde::applicationUrl('week.php')),
            array('month', _("Month"), 'monthview.png', Horde::applicationUrl('month.php')),
            array('year', _("Year"), 'yearview.png', Horde::applicationUrl('year.php')),
            array('search', _("Search"), 'search.png', Horde::applicationUrl('search.php'), $registry->getImageDir('horde')),
        );

        foreach ($menus as $menu) {
            $tree->addNode($parent . $menu[0],
                           $parent,
                           $menu[1],
                           $indent + 1,
                           false,
                           array('icon' => $menu[2],
                                 'icondir' => isset($menu[4]) ? $menu[4] : $registry->getImageDir(),
                                 'url' => $menu[3]));
        }
    }

}
