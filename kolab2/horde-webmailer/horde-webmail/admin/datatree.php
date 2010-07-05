<?php
/**
 * $Horde: horde/admin/datatree.php,v 1.7.2.9 2009-01-06 15:22:10 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

function addTree($parent, $parent_id, $indent = 1)
{
    global $datatree, $tree;

    $nodes = $datatree->getById(DATATREE_FORMAT_FLAT, $parent_id, true, $parent, 1);
    $expanded = $tree->isExpanded($parent);
    $url = Horde::url('datatree.php');
    foreach ($nodes as $id => $node) {
        if ($id == $parent_id) {
            continue;
        }
        $tree->addNode($parent . ':' . $id, $parent, $datatree->getShortName($node), $indent, false, array('url' => Util::addParameter($url, 'show', $datatree->getParam('group') . ':' . $id) . '#show'));
        if ($expanded) {
            addTree($parent . ':' . $id, $id, $indent + 1);
        }
    }
}

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Tree.php';
require_once 'Horde/DataTree.php';

if (!Auth::isAdmin()) {
    Horde::authenticationFailureRedirect();
}

$tree = &Horde_Tree::factory('datatree', 'html');
$tree->setOption('alternate', true);

$driver = $conf['datatree']['driver'];
$config = Horde::getDriverConfig('datatree', $conf['datatree']['driver']);
$datatree = &DataTree::singleton($conf['datatree']['driver']);
$roots = $datatree->getGroups();

if (is_a($roots, 'PEAR_Error')) {
    $notification->push($roots);
} else {
    foreach ($roots as $root) {
        $tree->addNode($root, null, $root, 0, false);
        $datatree = &DataTree::singleton($driver, array_merge($config, array('group' => $root)));
        addTree($root, DATATREE_ROOT);
    }
}

if ($show = Util::getFormData('show')) {
    list($root, $id) = explode(':', $show);
    $datatree = &DataTree::singleton($driver, array_merge($config, array('group' => $root)));
    $data = $datatree->getData($id);
    $attributes = $datatree->getAttributes($id);
}

$title = _("DataTree Browser");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/menu.inc';
echo '<h1 class="header">' . Horde::img('datatree.png') . ' ' . _("DataTree") . '</h1>';
$tree->renderTree();
if ($show) {
    echo '<br /><div class="text" style="white-space:pre"><a id="show"></a>';
    ob_start('htmlspecialchars');
    print_r($data);
    print_r($attributes);
    ob_end_flush();
    echo '</div>';
}
require HORDE_TEMPLATES . '/common-footer.inc';
