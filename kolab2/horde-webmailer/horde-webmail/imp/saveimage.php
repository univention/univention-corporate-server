<?php
/**
 * $Horde: imp/saveimage.php,v 1.1.2.9 2009-01-06 15:24:02 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Michael Slusarz <slusarz@horde.org>
 */

@define('IMP_BASE', dirname(__FILE__));
require_once IMP_BASE . '/lib/base.php';
require_once IMP_BASE . '/lib/Template.php';

$id = Util::getFormData('id');
$index = Util::getFormData('index');

/* Run through the action handlers. */
$actionID = Util::getFormData('actionID');
switch ($actionID) {
case 'save_image':
    require_once IMP_BASE . '/lib/MIME/Contents.php';
    $contents = &IMP_Contents::singleton($index);
    $mime_part = $contents->getDecodedMIMEPart($id);
    $image_data = array(
        'filename' => $mime_part->getName(true, true),
        'description' => $mime_part->getDescription(true),
        'data' => $mime_part->getContents(),
        'type' => $mime_part->getType()
    );
    $res = $registry->call('images/saveImage', array(null, Util::getFormData('gallery'), $image_data));
    if (is_a($res, 'PEAR_Error')) {
        $notification->push($res, 'horde.error');
        break;
    }
    Util::closeWindowJS();
    exit;
}

/* Build the template. */
$t = new IMP_Template();
$t->setOption('gettext', true);
$t->set('action', Horde::applicationUrl('saveimage.php'));
$t->set('id', htmlspecialchars($id));
$t->set('index', htmlspecialchars($index));
$t->set('image_img', Horde::img('mime/image.png', _("Image"), null, $registry->getImageDir('horde')));

/* Build the list of galleries. */
$t->set('gallerylist', $registry->call('images/selectGalleries', array(null, PERMS_EDIT)));

$title = _("Save Image");
require IMP_TEMPLATES . '/common-header.inc';
IMP::status();
echo $t->fetch(IMP_TEMPLATES . '/saveimage/saveimage.html');
require $registry->get('templates', 'horde') . '/common-footer.inc';
