<?php
/**
 * $Horde: horde/services/portal/edit.php,v 1.39 2004/04/07 14:43:45 chuck Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 * Copyright 2003-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Block.php';
require_once 'Horde/Block/Collection.php';
require_once 'Horde/Block/Layout.php';
require_once 'Horde/Identity.php';
require_once 'Horde/Menu.php';
require_once 'Horde/Help.php';

if (!Auth::isAuthenticated()) {
    Horde::authenticationFailureRedirect();
}

// Get form values
$col = (int)Util::getFormData('col');
$row = (int)Util::getFormData('row');
$action = Util::getFormData('action');
$edit_row = null;
$edit_col = null;

// Get full name for title
$identity = &Identity::singleton();
$fullname = $identity->getValue('fullname');
if (empty($fullname)) {
    $fullname = Auth::getAuth();
}

// Instantiate the blocks objects.
$blocks = &Horde_Block_Collection::singleton();
$layout = &Horde_Block_Layout::singleton();

// Handle requested actions
switch ($action) {
case 'moveUp':
case 'moveDown':
case 'moveLeft':
case 'moveRight':
case 'expandUp':
case 'expandDown':
case 'expandLeft':
case 'expandRight':
case 'shrinkLeft':
case 'shrinkRight':
case 'shrinkUp':
case 'shrinkDown':
case 'removeBlock':
    $result = call_user_func(array(&$layout, $action), $row, $col);
    if (is_a($result, 'PEAR_Error')) {
        $notification->push($result);
    } else {
        $layout->save();
    }
    break;

// Save the changes made to a block.
case 'save':
// Save the changes made to a block and continue editing.
case 'save-resume':
    // Get requested block type.
    list($newapp, $newtype) = explode(':', Util::getFormData('app'));

    // Make sure there is somewhere to put it.
    if ($layout->isEmpty($row, $col) || 
        !$layout->rowExists($row) || 
        !$layout->colExists($col)) {
        $layout->addBlock($row, $col);
        $layout->setBlockInfo($row, $col, array('app' => $newapp, 'block' => $newtype));
    } elseif ($layout->isBlock($row, $col)) {
        // Get target block info.
        $info = $layout->getBlockInfo($row, $col);

        if ($info['app'] != $newapp || $info['block'] != $newtype) {
            // Change app or type.
            $info = array();
            $info['app'] = $newapp;
            $info['block'] = $newtype;
            $info['params'] = Util::getFormData('params');
            $params = $blocks->getParams($newapp, $newtype);
            foreach ($params as $newparam) {
                if (is_null($info['params'][$newparam])) {
                    $info['params'][$newparam] = $blocks->getDefaultValue($newapp, $newtype, $newparam);
                }
            }
            $layout->setBlockInfo($row, $col, $info);
        } else {
            // Change values.
            $layout->setBlockInfo($row, $col, array('params' => Util::getFormData('params', array())));
        }
    }
    $layout->save();
    if ($action == 'save') {
        break;
    }

// Make a block the current block for editing.
case 'edit':
    $edit_row = $row;
    $edit_col = $col;
    break;
}

$title = _("My Portal Layout");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/portal/menu.inc';
$notification->notify(array('listeners' => 'status'));
require HORDE_TEMPLATES . '/portal/edit.inc';
require HORDE_TEMPLATES . '/common-footer.inc';
