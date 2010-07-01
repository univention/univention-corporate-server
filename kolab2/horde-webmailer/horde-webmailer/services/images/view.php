<?php
/**
 * Displays an image and allows modifications if required.
 *
 * $Horde: horde/services/images/view.php,v 1.20.10.10 2009-01-06 15:27:29 jan Exp $
 *
 * Copyright 2003-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author Marko Djukic <marko@oblo.com>
 */

@define('HORDE_BASE', dirname(__FILE__) . '/../..');
require_once HORDE_BASE . '/lib/base.php';

/* Get file info. The following parameters are available:
 *  'f' - the filename.
 *  's' - the source, either the 'tmp' directory or VFS.
 *  'c' - which app's config to use for VFS, defaults to Horde.
 *  'p' - the directory of the file.
 *  'n' - the name to set to the filename or default to same as filename.
 *  'a' - perform some action on the image, such as scaling. */
$file = basename(Util::getFormData('f'));
$source = strtolower(Util::getFormData('s', 'tmp'));
$app_conf = strtolower(Util::getFormData('c', 'horde'));
$name = Util::getFormData('n', $file);
$action = strtolower(Util::getFormData('a'));

switch ($source) {
case 'vfs':
    /* Change app if needed to get the right VFS config. */
    $changed_conf = $registry->pushApp($app_conf);

    /* Getting a file from Horde's VFS. */
    require_once 'VFS.php';
    $vfs = &VFS::singleton($conf['vfs']['type'], Horde::getDriverConfig('vfs', $conf['vfs']['type']));
    $path = Util::getFormData('p');
    $file_data = $vfs->read($path, $file);
    if (is_a($file_data, 'PEAR_Error')) {
        Horde::logMessage(sprintf('Error displaying image [%s]: %s', $path . '/' . $file, $file_data->getMessage()), __FILE__, __LINE__, PEAR_LOG_ERR);
        exit;
    }

    /* Return the original app if changed previously. */
    if ($changed_conf) {
        $registry->popApp($app_conf);
    }
    break;

case 'tmp':
    /* Getting a file from Horde's temp dir. */
    $tmpdir = Horde::getTempDir();
    if (empty($action) || $action == 'resize') {
        /* Use original if no action or if resizing. */
        $file_name = $tmpdir . '/' . $file;
    } else {
        $file_name = $tmpdir . '/mod_' . $file;
        if (!file_exists($file_name)) {
            copy($tmpdir . '/' . $file, $file_name);
        }
    }
    if (!file_exists($file_name)) {
        Horde::logMessage(sprintf('Image not found [%s]', $file_name), __FILE__, __LINE__, PEAR_LOG_ERR);
        exit;
    }
    $file_data = file_get_contents($file_name);
    break;
}

/* Load the image object. */
require_once 'Horde/Image.php';
$params = array('temp' => Horde::getTempDir());
if (!empty($conf['image']['convert'])) {
    $image = &Horde_Image::singleton('im', $params);
} else {
    $image = &Horde_Image::singleton('gd', $params);
}
$image->loadString($file, $file_data);

/* Check if no editing action required and send the image to browser. */
if (empty($action)) {
    $image->display();
    exit;
}

/* Image editing required. */
switch ($action) {
case 'rotate':
    $image->rotate(Util::getFormData('v'));
    break;

case 'flip':
    $image->flip();
    break;

case 'mirror':
    $image->mirror();
    break;

case 'grayscale':
    $image->grayscale();
    break;

case 'resize':
    list($width, $height, $ratio) = explode('.', Util::getFormData('v'));

    /* If no width or height has been passed, get the original
     * ones. */
    if (empty($width) || empty($height)) {
        $orig = $image->getDimensions();
    }
    if (empty($width)) {
        $width = $orig['width'];
    }
    if (empty($height)) {
        $height = $orig['height'];
    }

    $image->resize($width, $height, $ratio);

    /* Since the original is always used for resizing make sure the
     * write is to 'mod_'. */
    $file_name = $tmpdir . '/mod_' . $file;
    break;
}

/* Write out any changes to the temporary file. */
$fp = @fopen($file_name, 'wb');
fwrite($fp, $image->raw());
fclose($fp);

$image->display();
