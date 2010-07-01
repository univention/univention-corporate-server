<?php
/**
 * $Horde: turba/view.php,v 1.6.2.6 2009-01-06 15:27:39 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author Jan Schneider <jan@horde.org>
 */

@define('TURBA_BASE', dirname(__FILE__));
require_once TURBA_BASE . '/lib/base.php';

if ($conf['documents']['type'] == 'none') {
    Horde::fatal(_("The VFS backend needs to be configured to enable attachment uploads."), __FILE__, __LINE__);
}

$source = Util::getFormData('source');
$key = Util::getFormData('key');
$actionID = Util::getFormData('actionID');
$filename = Util::getFormData('file');
$type = Util::getFormData('type');

/* Get the object. */
if (!isset($cfgSources[$source])) {
    Horde::fatal(_("The contact you requested does not exist."), __FILE__, __LINE__);
}
$driver = &Turba_Driver::singleton($source);
$object = $driver->getObject($key);
if (is_a($object, 'PEAR_Error')) {
    Horde::fatal($object, __FILE__, __LINE__);
}

/* Check permissions. */
if (!$object->hasPermission(PERMS_READ)) {
    Horde::fatal(_("You do not have permission to view this contact."), __FILE__, __LINE__);
}

$v_params = Horde::getVFSConfig('documents');
if (is_a($v_params, 'PEAR_Error')) {
    Horde::fatal($v_params, __FILE__, __LINE__);
}
require_once 'VFS.php';
$vfs = &VFS::singleton($v_params['type'], $v_params['params']);
if (is_a($vfs, 'PEAR_Error')) {
    Horde::fatal($vfs, __FILE__, __LINE__);
} else {
    $data = $vfs->read(TURBA_VFS_PATH . '/' . $object->getValue('__uid'), $filename);
}
if (is_a($data, 'PEAR_Error')) {
    Horde::logMessage($data, __FILE__, __LINE__, PEAR_LOG_ERR);
    Horde::fatal(sprintf(_("Access denied to %s"), $filename), __FILE__, __LINE__);
}

/* Run through action handlers */
switch ($actionID) {
case 'download_file':
     $browser->downloadHeaders($filename);
     echo $data;
     exit;

case 'view_file':
    require_once 'Horde/MIME/Magic.php';
    require_once 'Horde/MIME/Viewer.php';
    require_once 'Horde/MIME/Part.php';
    if (is_callable(array('Horde', 'loadConfiguration'))) {
        require_once 'Horde/Array.php';
        $result = Horde::loadConfiguration('mime_drivers.php', array('mime_drivers', 'mime_drivers_map'), 'horde');
        extract($result);
        $result = Horde::loadConfiguration('mime_drivers.php', array('mime_drivers', 'mime_drivers_map'), 'turba');
        if (isset($result['mime_drivers'])) {
            $mime_drivers = Horde_Array::array_merge_recursive_overwrite($mime_drivers, $result['mime_drivers']);
        }
        if (isset($result['mime_drivers_map'])) {
            $mime_drivers_map = Horde_Array::array_merge_recursive_overwrite($mime_drivers_map, $result['mime_drivers_map']);
        }
    } else {
        require HORDE_BASE . '/config/mime_drivers.php';
        require TURBA_BASE . '/config/mime_drivers.php';
    }
    $mime_part = new MIME_Part(MIME_Magic::extToMIME($type), $data);
    $mime_part->setName($filename);
    $viewer = MIME_Viewer::factory($mime_part);

    $body = $viewer->render();
    $browser->downloadHeaders($filename, $viewer->getType(), true, strlen($body));
    echo $body;
    exit;
}
