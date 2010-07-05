<?php

$block_name = _("Menu List");
$block_type = 'tree';

/**
 * $Horde: nag/lib/Block/tree_menu.php,v 1.2.2.2 2008-01-02 16:50:50 chuck Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_nag_tree_menu extends Horde_Block {

    var $_app = 'nag';

    function _buildTree(&$tree, $indent = 0, $parent = null)
    {
        global $registry;

        require_once dirname(__FILE__) . '/../base.php';

        $add = Horde::applicationUrl('task.php?actionID=add_task');
        $icondir = $registry->getImageDir();

        $tree->addNode($parent . '__new',
                       $parent,
                       _("New Task"),
                       $indent + 1,
                       false,
                       array('icon' => 'add.png',
                             'icondir' => $icondir,
                             'url' => $add));

        foreach (Nag::listTasklists() as $name => $tasklist) {
            $tree->addNode($parent . $name . '__new',
                           $parent . '__new',
                           sprintf(_("in %s"), $tasklist->get('name')),
                           $indent + 2,
                           false,
                           array('icon' => 'add.png',
                                 'icondir' => $icondir,
                                 'url' => Util::addParameter($add, array('tasklist_id' => $name))));
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
