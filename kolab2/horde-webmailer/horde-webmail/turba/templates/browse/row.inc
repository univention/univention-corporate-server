<?php

if ($ob->hasValue('name')) {
    $link_text = htmlspecialchars(Turba::formatName($ob));
} elseif (isset($ob->driver->alternativeName) &&
          !in_array($ob->driver->alternativeName, $this->columns) &&
          $ob->hasValue($ob->driver->alternativeName)) {
    $link_text = htmlspecialchars($ob->getValue($ob->driver->alternativeName));
} else {
    $link_text = '<em>' . _("Blank name") . '</em>';
}

if ($own_source == $ob->getSource() && $own_id == $ob->getValue('__key')) {
    $own_icon = Horde::img('user.png', _("Your own contact"),
                           array('title' => _("Your own contact")),
                           $GLOBALS['registry']->getImageDir('horde'));
} else {
    $own_icon = '&nbsp;';
}

$edit_url = $vcard_url = '&nbsp;';
if ($ob->hasValue('__key')) {
    $vcard_url = Util::addParameter('vcard.php',
                                    array('source' => $ob->getSource(),
                                          'key' => $ob->getValue('__key')));
    $vcard_url = Horde::link(Horde::applicationUrl($vcard_url),
                             _("Download vCard"))
        . Horde::img('mime/vcard.png', _("Download vCard"), '',
            $GLOBALS['registry']->getImageDir('horde'))
        . '</a>';

    $cell = Horde::link($ob->url()) . $link_text . '</a>';
    if ($ob->hasPermission(PERMS_EDIT)) {
        $edit_url = Util::addParameter(
            'contact.php',
            array('view' => 'EditContact',
                  'source' => $ob->getSource(),
                  'key' => $ob->getValue('__key'),
                  'url' => Horde::selfUrl(true, false, true)));
        $edit_url = Horde::link(Horde::applicationUrl($edit_url), _("Edit"))
            . Horde::img('edit.png', _("Edit"), '',
                         $GLOBALS['registry']->getImageDir('horde'))
            . '</a>';
    }
} else {
    $cell = $link_text;
}

?>
<tr>
<?php if ($this->showMark): ?>
  <td><label for="<?php echo htmlspecialchars($ob->getSource() . ':' . $ob->getValue('__key')) ?>" class="hidden"><?php echo _("Select contact") ?></label><input type="checkbox" class="checkbox" name="objectkeys[]" id="<?php echo htmlspecialchars($ob->getSource() . ':' . $ob->getValue('__key')) ?>" value="<?php echo htmlspecialchars($ob->getSource() . ':' . $ob->getValue('__key')) ?>" /></td>
<?php endif; ?>
<?php if ($this->showEdit): ?>
  <td><?php echo $edit_url ?></td>
<?php endif; ?>
<?php if ($this->showVcard): ?>
  <td><?php echo $vcard_url ?></td>
<?php endif; ?>
<?php if ($this->showGroup): ?>
  <td><?php echo $ob->isGroup() ? Horde::img('group.png', _("Group")) : $own_icon ?></td>
<?php endif; ?>
  <td<?php if ($this->showSort && $this->isSortColumn(0)) echo ' class="linedRowSelectedCol"' ?>><?php
echo $cell;

// We purposefully do this before the </td> so that if we end up including a
// script file (say, for the IMP compose window), it's in a legal spot.
//
// Build the columns to display.
$shown_columns = array();
for ($c = 1; $c <= count($this->columns); $c++) {
    $type = $GLOBALS['attributes'][$this->columns[$c - 1]]['type'];
    $params = isset($GLOBALS['attributes'][$this->columns[$c - 1]]['params'])
        ? $GLOBALS['attributes'][$this->columns[$c - 1]]['params']
        : array();
    if (!isset($this->variables[$this->columns[$c - 1]])) {
        if ($type == 'email') {
            $this->variables[$this->columns[$c - 1]] =
                new Horde_Form_Variable('', $this->columns[$c - 1],
                                        Horde_Form::getType('html'), false);
        } else {
            $this->variables[$this->columns[$c - 1]] =
                new Horde_Form_Variable('', $this->columns[$c - 1],
                                        Horde_Form::getType($type, $params),
                                        false);
        }
    }
    if ($ob->hasValue($this->columns[$c - 1])) {
        $value = $ob->getValue($this->columns[$c - 1]);
        $shown_columns[$c] = htmlspecialchars($value);
        if ($type == 'email') {
            $value = Turba::formatEmailAddresses($value,
                                                 $ob->getValue('name'));
        }
        $this->vars->set($this->columns[$c - 1], $value);
        $shown_columns[$c] = $this->renderer->render(
            $this->form,
            $this->variables[$this->columns[$c - 1]],
            $this->vars);
    } else {
        $shown_columns[$c] = '&nbsp;';
    }
}

echo '</td>';
foreach ($shown_columns as $column => $value) {
    echo '<td';
    if ($this->showSort && $this->isSortColumn($column)) {
        echo ' class="linedRowSelectedCol"';
    }
    echo '>' . $value . '</td>';
}
?>
</tr>
