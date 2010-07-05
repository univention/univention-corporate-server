<?php

if ($this->list->isFresh($ob)) {
    $class = 'text';
} else {
    $class = 'old';
}

if ($ob->hasValue('name')) {
    $link_text = htmlspecialchars(Turba::formatName($ob));
} else {
    $link_text = _("[no value]");
}

$edit_url = '&nbsp;';

global $prefs;
if ($ob->hasValue('__key')) {
    $url = Util::addParameter($ob->isGroup() ? 'browse.php' : 'display.php',
                              array('source' => $ob->getSource(),
                                    'key' => $ob->getValue('__key')));

    $vcard_url = Util::addParameter('vcard.php', array('source' => $ob->getSource(),
                                                       'key' => $ob->getValue('__key')));
    $vcard_url = Horde::link(Horde::applicationUrl($vcard_url), _("Download vCard")) . Horde::img('mime/vcard.png', _("Download vCard"), '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';

    $cell = Horde::link(Horde::applicationUrl($url), sprintf(_("View \"%s\""), $ob->getValue('name')));
    $cell .= $link_text . '</a>';
    if (Turba::hasPermission($ob, 'object', PERMS_EDIT)) {
        $edit_url = Util::addParameter('edit.php', array('source' => $ob->getSource(),
                                                         'key' => $ob->getValue('__key'),
                                                         'url' => Horde::selfUrl()));
        $edit_url = Horde::link(Horde::applicationUrl($edit_url), sprintf(_("Edit \"%s\""), $ob->getValue('name'))) . Horde::img('edit.png', _("Edit"), '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
    }
} else {
    $cell = $link_text;
    $edit_url = $vcard_url = null;
}
?>
<tr class="<?php echo $class ?>">
  <td><input type="checkbox" class="checkbox" name="objectkeys[]" value="<?php echo htmlspecialchars($ob->getSource() . ':' . $ob->getValue('__key')) ?>" /></td>
  <td><?php echo $edit_url ?></td>
  <td><?php echo $vcard_url ?></td>
  <td><?php echo $ob->isGroup() ? Horde::img('group.png', _("Group")) : '&nbsp;' ?></td>
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
            $show[$column] = Turba::formatEmailAddresses($show[$column], $ob->getValue('name'));
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
