<?php
/**
 * $Horde: mnemo/note/pdf.php,v 1.4.2.3 2009-01-06 15:25:00 jan Exp $
 *
 * Copyright 2001-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL). If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 */

@define('MNEMO_BASE', dirname(dirname(__FILE__)));
require_once MNEMO_BASE . '/lib/base.php';
require_once 'File/PDF.php';

/* Check if a passphrase has been sent. */
$passphrase = Util::getFormData('memo_passphrase');

/* We can either have a UID or a memo id and a notepad. Check for UID
 * first. */
$storage = &Mnemo_Driver::singleton();
if ($uid = Util::getFormData('uid')) {
    $note = $storage->getByUID($uid, $passphrase);
    if (is_a($note, 'PEAR_Error')) {
        header('Location: ' . Horde::applicationUrl('list.php', true));
        exit;
    }

    $note_id = $note['memo_id'];
    $notelist_id = $note['memolist_id'];
} else {
    /* If we aren't provided with a memo and memolist, redirect to
     * list.php. */
    $note_id = Util::getFormData('note');
    $notelist_id = Util::getFormData('notepad');
    if (!isset($note_id) || !$notelist_id) {
        header('Location: ' . Horde::applicationUrl('list.php', true));
        exit;
    }

    /* Get the current memo. */
    $note = Mnemo::getMemo($notelist_id, $note_id, $passphrase);
}

$share = &$GLOBALS['mnemo_shares']->getShare($notelist_id);
if (is_a($share, 'PEAR_Error')) {
    $notification->push(sprintf(_("There was an error viewing this notepad: %s"), $share->getMessage()), 'horde.error');
    header('Location: ' . Horde::applicationUrl('list.php', true));
    exit;
} elseif (!$share->hasPermission(Auth::getAuth(), PERMS_READ)) {
    $notification->push(sprintf(_("You do not have permission to view the notepad %s."), $share->get('name')), 'horde.error');
    header('Location: ' . Horde::applicationUrl('list.php', true));
    exit;
}

/* If the requested note doesn't exist, display an error message. */
if (!$note || !isset($note['memo_id'])) {
    $notification->push(_("Note not found."), 'horde.error');
    header('Location: ' . Horde::applicationUrl('list.php', true));
    exit;
}

/* Set up the PDF object. */
$pdf = File_PDF::factory(array('format' => 'Letter', 'unit' => 'pt'));
$pdf->setMargins(50, 50);

/* Enable automatic page breaks. */
$pdf->setAutoPageBreak(true, 50);

/* Start the document. */
$pdf->open();

/* Start a page. */
$pdf->addPage();

/* Write the header in Times 24 Bold. */
$pdf->setFont('Times', 'B', 24);
$pdf->multiCell(0, 24, $note['desc'], 'B', 1);
$pdf->newLine(20);

/* Write the note body in Times 14. */
$pdf->setFont('Times', '', 14);
$pdf->write(14, $note['body']);

/* Output the generated PDF. */
$browser->downloadHeaders($note['desc'] . '.pdf', 'application/pdf');
echo $pdf->getOutput();
