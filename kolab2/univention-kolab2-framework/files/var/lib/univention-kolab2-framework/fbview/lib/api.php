<?php
/**
 * Horde external API interface.
 *
 * This file defines Horde's external API interface. Other
 * applications can interact with Horde through this API.
 *
 * $Horde: horde/lib/api.php,v 1.32 2004/05/30 13:09:10 jan Exp $
 *
 * @package Horde
 */

$_types = array(
    'stringArray' => array(array('item' => 'string')),
    'hashItem' => array('key' => 'string', 'value' => 'string'),
    'hash' => array(array('item' => '{urn:horde}hashItem')));

$_services['admin_list'] = array(true);

/**
 * General API for deleting Horde_Links
 */
$_services['deleteLink'] = array(
    'link' => '%application%/services/links/delete.php?' .
    'link_data=|link_data|' . 
    ini_get('arg_separator.output') . 'return_url=|url|'
);

$_services['listApps'] = array(
    'args' => array('filter' => 'stringArray'),
    'type' => 'stringArray'
);

$_services['listAPIs'] = array(
    'args' => array(),
    'type' => 'stringArray'
);

$_services['block'] = array(
    'args' => array('type' => 'string', 'params' => 'stringArray'),
    'type' => 'stringArray'
);

$_services['defineBlock'] = array(
    'args' => array('type' => 'string'),
    'type' => 'string'
);

$_services['blocks'] = array(
    'args' => array(),
    'type' => 'hash'
);


function &_horde_block($block, $params = array())
{
    @define('HORDE_BASE', dirname(__FILE__) . '/..');
    require_once HORDE_BASE . '/lib/base.php';

    if (is_a(($blockClass = _horde_defineBlock($block)), 'PEAR_Error')) {
        return $blockClass;
    }

    return $ret = &new $blockClass($params);
}

function _horde_defineBlock($block)
{
    $blockClass = 'Horde_Block_' . $block;
    include_once HORDE_BASE . '/lib/Block/' . $block . '.php';
    if (class_exists($blockClass)) {
        return $blockClass;
    } else {
        return PEAR::raiseError(sprintf(_("%s not found."), $blockClass));
    }
}

function _horde_blocks()
{
    require_once 'Horde/Block/Collection.php';
    $collection = &Horde_Block_Collection::singleton();
    if (is_a($collection, 'PEAR_Error')) {
        return $collection;
    } else {
        return $collection->getBlocksList();
    }
}

function _horde_admin_list()
{
    return array('configuration' => array(
                     'link' => '%application%/admin/setup/',
                     'name' => _("Configuration"),
                     'icon' => 'config.gif'),
                 'users' => array(
                     'link' => '%application%/admin/user.php',
                     'name' => _("Users"),
                     'icon' => 'user.gif'),
                 'groups' => array(
                     'link' => '%application%/admin/groups.php',
                     'name' => _("Groups"),
                     'icon' => 'group.gif'),
                 'perms' => array(
                     'link' => '%application%/admin/perms/index.php',
                     'name' => _("Permissions"),
                     'icon' => 'perms.gif'),
                 'phpshell' => array(
                     'link' => '%application%/admin/phpshell.php',
                     'name' => _("PHP Shell"),
                     'icon' => 'shell.gif'),
                 'sqlshell' => array(
                     'link' => '%application%/admin/sqlshell.php',
                     'name' => _("SQL Shell"),
                     'icon' => 'sql.gif'),
                 'cmdshell' => array(
                     'link' => '%application%/admin/cmdshell.php',
                     'name' => _("Command Shell"),
                     'icon' => 'shell.gif'),
                 );
}

function _horde_listApps($filter = null)
{
    return $GLOBALS['registry']->listApps($filter);
}

function _horde_listAPIs()
{
    return $GLOBALS['registry']->listAPIs();
}
