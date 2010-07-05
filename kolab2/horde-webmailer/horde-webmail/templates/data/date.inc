<?php
$i = 0;
while ($i < count($date['values']) && empty($date['values'][$i])) {
    $i++;
}
if (strpos($date['values'][$i], '/') !== false) {
    $del = '/';
} elseif (strpos($date['values'][$i], '.') !== false) {
    $del = '.';
} elseif (strpos($date['values'][$i], '-') !== false) {
    $del = '-';
} else {
    $del = '';
}

// Try to guess the date format as much as possible
$form = null;
if (!empty($del) && isset($date['values']) && isset($date['values'][$i])) {
    $parts = explode($del, $date['values'][$i]);
    if (count($parts) >= 3) {
        $form = 'mdy';
        if ((strlen($parts[0]) == 4) || ($parts[0] > 31)) {
            $form = 'ymd';
            if ($parts[1] > 12) {
                $form = 'ydm';
            }
        } elseif ($parts[0] > 12) {
            $form = 'dmy';
        }
    }
}
?>
<tr>
  <td><?php echo Horde::label('delimiter_' . htmlspecialchars($key), _("Select the date delimiter:")) ?></td>
  <td>
    <select id="delimiter_<?php echo htmlspecialchars($key) ?>" name="delimiter[<?php echo htmlspecialchars($key) ?>]">
      <option value="/"<?php echo $del == '/' ? ' selected="selected"' : '' ?>>/</option>
      <option value="."<?php echo $del == '.' ? ' selected="selected"' : '' ?>>.</option>
      <option value="-"<?php echo $del == '-' ? ' selected="selected"' : '' ?>>-</option>
    </select>
  </td>
</tr>
<tr>
  <td><?php echo Horde::label('format_' . htmlspecialchars($key), _("Select the date format:")) ?></td>
  <td>
    <select id="format_<?php echo htmlspecialchars($key) ?>" name="format[<?php echo htmlspecialchars($key) ?>]">
      <option value="mday/month/year"<?php echo $form == 'dmy' ? ' selected="selected"' : '' ?>><?php echo _("DD") . $del . _("MM") . $del . _("YY") ?></option>
      <option value="month/mday/year"<?php echo $form == 'mdy' ? ' selected="selected"' : '' ?>><?php echo _("MM") . $del . _("DD") . $del . _("YY") ?></option>
      <option value="year/month/mday"<?php echo $form == 'ymd' ? ' selected="selected"' : '' ?>><?php echo _("YY") . $del . _("MM") . $del . _("DD") ?></option>
      <option value="year/mday/month"<?php echo $form == 'ydm' ? ' selected="selected"' : '' ?>><?php echo _("YY") . $del . _("DD") . $del . _("MM") ?></option>
    </select>
  </td>
</tr>
