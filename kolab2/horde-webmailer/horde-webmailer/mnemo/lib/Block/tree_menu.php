<?php

$block_name = _("Menu List");
$block_type = 'tree';

/**
 * $Horde: mnemo/lib/Block/tree_menu.php,v 1.4.2.2 2008-01-02 16:50:49 chuck Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_mnemo_tree_menu extends Horde_Block {

    var $_app = 'mnemo';

    function _buildTree(&$tree, $indent = 0, $parent = null)
    {
        require_once dirname(__FILE__) . '/../base.php';

        global $registry;

        $tree->addNode($parent . '__new',
                       $parent,
                       _("New Note"),
                       $indent + 1,
                       false,
                       array('icon' => 'add.png',
                             'icondir' => $registry->getImageDir(),
                             'url' => Horde::applicationUrl('memo.php?actionID=add_memo')));

        foreach (Mnemo::listNotepads() as $name => $notepad) {
            $tree->addNode($parent . $name . '__new',
                           $parent . '__new',
                           sprintf(_("in %s"), $notepad->get('name')),
                           $indent + 2,
                           false,
                           array('icon' => 'add.png',
                                 'icondir' => $registry->getImageDir(),
                                 'url' => Util::addParameter(Horde::applicationUrl('memo.php?memolist=' . urlencode($name)),
                                                             'actionID', 'add_memo')));
        }

        $tree->addNode($parent . '__search',
                       $parent,
                       _("Search"),
                       $indent + 1,
                       false,
                       array('icon' => 'search.png',
                             'icondir' => $registry->getImageDir('horde'),
                             'url' => Horde::applicationUrl('search.php')));
    }

}
