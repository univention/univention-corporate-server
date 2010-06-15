<?php

if ($this->list->isFresh($ob)) {
    $class = 'listitem';
} else {
    $class = 'oldlistitem';
}

if ($ob->hasValue('name')) {
    $link_text = htmlspecialchars(Turba::formatName($ob));
} else {
    $link_text = '';
}

$edit_url = '&nbsp;';

global $prefs;
if ($ob->hasValue('__key')) {
    if ($ob->isGroup()) {
        $url = 'browse.php';
    } else {
        $url = 'display.php';
    }
    $url = Util::addParameter($url, 'source', $ob->getSource());
    $url = Util::addParameter($url, 'key', $ob->getValue('__key'));

    $vcard_url = Util::addParameter('vcard.php', 'source', $ob->getSource());
    $vcard_url = Util::addParameter($vcard_url, 'key', $ob->getValue('__key'));
    $vcard_url = Horde::link(Horde::applicationUrl($vcard_url), _("Download VCard")) . Horde::img('mime/vcard.gif', _("Download vCard"), '', $GLOBALS['registry']->getParam('graphics', 'horde')) . '</a>';

    $cell = Horde::link(Horde::applicationUrl($url), sprintf(_("View '%s'"), $ob->getValue('name')));
    $cell .= $link_text . '</a>';
    if (Turba::checkPermissions($ob, 'object', PERMS_EDIT)) {
        $edit_url = Util::addParameter('edit.php', 'source', $ob->getSource());
        $edit_url = Util::addParameter($edit_url, 'key', $ob->getValue('__key'));
        $edit_url = Util::addParameter($edit_url, 'url', Horde::selfURL());
        $edit_url = Horde::link(Horde::applicationUrl($edit_url), sprintf(_("Edit '%s'"), $ob->getValue('name'))) . Horde::img('edit.gif', _("Edit")) . '</a>';
    }
} else {
    $cell = $link_text;
}
?>
<tr class="<?php echo $class ?>" onmouseover="className='<?php echo $class ?>-hi';" onmouseout="className='<?php echo $class ?>';">
  <td><input type="checkbox" name="objectkeys[]" value="<?php echo htmlspecialchars($ob->getSource() . ':' . $ob->getValue('__key')) ?>" /></td>
  <td><?php echo $edit_url ?></td>
  <td><?php echo $vcard_url ?></td>
  <td><?php echo $ob->isGroup() ? Horde::img('group.gif', _("Group")) : '&nbsp;' ?></td>
  <td><?php
echo $cell;

// We purposefully do this before the </td> so that if we end up
// including a script file (say, for the IMP compose window), it's in
// a legal spot.
//
// Build the columns to display.
$show = array();
foreach ($GLOBALS['columns'] as $column) {
    if ($ob->hasValue($column)) {
        $show[$column] = htmlspecialchars($ob->getValue($column));
        if ($GLOBALS['attributes'][$column]['type'] == 'email') {
            $show[$column] = Turba::formatEmailAddresses($show[$column], $ob);
        }
    } else {
        $show[$column] = '&nbsp;';
    }
}

?></td>
<?php foreach ($show as $field): ?>
  <td><?php echo $field ?></td>
<?php endforeach; ?>
</tr>
