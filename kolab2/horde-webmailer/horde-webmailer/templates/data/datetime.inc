<?php
$i = 0;
while ($i < count($date['values']) && empty($date['values'][$i])) {
    $i++;
}
$day_del = $time_del = '';
if (isset($date['values'][$i]) && strpos($date['values'][$i], ' ') !== false) {
    for ($order = 0; (empty($time_del) || empty($day_del)) && $order <= 1; $order++) {
        if ($order) {
            list($time, $day) = explode(' ', $date['values'][$i], 2);
        } else {
            list($day, $time) = explode(' ', $date['values'][$i], 2);
        }
        if (strpos($day, '/') !== false) {
            $day_del = '/';
        } elseif (strpos($day, '.') !== false) {
            $day_del = '.';
        } elseif (strpos($day, '-') !== false) {
            $day_del = '-';
        } else {
            $day_del = '';
        }
        if (strpos($time, ':') !== false) {
            $time_del = ':';
        } elseif (strpos($time, '.') !== false) {
            $time_del = '.';
        } else {
            $time_del = '';
        }
    }
    $order--;
}

// Try to guess the date format as much as possible
$form = null;
if (!empty($day_del) && isset($date['values'][$i])) {
    $parts = explode($day_del, $date['values'][$i]);
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
$ampm = isset($date['values'][$i]) &&
    (strpos(String::lower($date['values'][$i]), 'am') !== false ||
     strpos(String::lower($date['values'][$i]), 'pm') !== false);

if (!isset($date['values'][$i]) || strpos($date['values'][$i], ' ') === false):
?>
<tr>
  <td><?php echo Horde::label('order_' . htmlspecialchars($key), _("Select the date and time format:")) ?></td>
  <td>
    <select id="order_<?php echo htmlspecialchars($key) ?>" name="order[<?php echo htmlspecialchars($key) ?>]">
      <option value="-1" selected="selected"><?php echo _("Timestamp or unknown") ?></option>
    </select>
  </td>
</tr>
<?php else: ?>
<tr>
  <td><?php echo Horde::label('order_' . htmlspecialchars($key), _("Select the day and time order:")) ?></td>
  <td>
    <select id="order_<?php echo htmlspecialchars($key) ?>" name="order[<?php echo htmlspecialchars($key) ?>]">
      <option value="-1"<?php echo ($order && (empty($day_del) || empty($time_del))) ? ' selected="selected"' : '' ?>><?php echo _("Timestamp or unknown") ?></option>
      <option value="0"<?php echo (!$order) ? ' selected="selected"' : '' ?>><?php printf(_("Date: %s; time: %s"), $day, $time) ?></option>
      <option value="1"<?php echo $order ? ' selected="selected"' : '' ?>><?php printf(_("Date: %s; time: %s"), $day, $time) ?></option>
    </select>
  </td>
</tr>
<tr>
  <td><?php echo Horde::label('day_delimiter_' . htmlspecialchars($key), _("Select the date delimiter:")) ?></td>
  <td>
    <select id="day_delimiter_<?php echo htmlspecialchars($key) ?>" name="day_delimiter[<?php echo htmlspecialchars($key) ?>]">
      <option value="/"<?php echo $day_del == '/' ? ' selected="selected"' : '' ?>>/</option>
      <option value="."<?php echo $day_del == '.' ? ' selected="selected"' : '' ?>>.</option>
      <option value="-"<?php echo $day_del == '-' ? ' selected="selected"' : '' ?>>-</option>
    </select>
  </td>
</tr>
<tr>
  <td><?php echo Horde::label('day_format_' . htmlspecialchars($key), _("Select the date format:")) ?></td>
  <td>
    <select id="day_format_<?php echo htmlspecialchars($key) ?>" name="day_format[<?php echo htmlspecialchars($key) ?>]">
      <option value="mday/month/year"<?php echo $form == 'dmy' ? ' selected="selected"' : '' ?>><?php echo _("DD") . $day_del . _("MM") . $day_del . _("YY") ?></option>
      <option value="month/mday/year"<?php echo $form == 'mdy' ? ' selected="selected"' : '' ?>><?php echo _("MM") . $day_del . _("DD") . $day_del . _("YY") ?></option>
      <option value="year/month/mday"<?php echo $form == 'ymd' ? ' selected="selected"' : '' ?>><?php echo _("YY") . $day_del . _("MM") . $day_del . _("DD") ?></option>
      <option value="year/mday/month"<?php echo $form == 'ydm' ? ' selected="selected"' : '' ?>><?php echo _("YY") . $day_del . _("DD") . $day_del . _("MM") ?></option>
    </select>
  </td>
</tr>
<tr>
  <td><?php echo Horde::label('time_delimiter_' . htmlspecialchars($key), _("Select the time delimiter:")) ?></td>
  <td>
    <select id="time_delimiter_<?php echo htmlspecialchars($key) ?>" name="time_delimiter[<?php echo htmlspecialchars($key) ?>]">
      <option value=":"<?php echo $time_del == ':' ? ' selected="selected"' : '' ?>>:</option>
      <option value="."<?php echo $time_del == '.' ? ' selected="selected"' : '' ?>>.</option>
    </select>
  </td>
</tr>
<tr>
  <td><?php echo Horde::label('time_format_' . htmlspecialchars($key), _("Select the time format:")) ?></td>
  <td>
    <select id="time_format_<?php echo htmlspecialchars($key) ?>" name="time_format[<?php echo htmlspecialchars($key) ?>]">
      <option value="24hr"<?php echo $ampm ? '' : ' selected="selected"' ?>><?php echo _("24 hours") ?></option>
      <option value="ampm"<?php echo $ampm ? ' selected="selected"' : '' ?>><?php echo _("AM/PM") ?></option>
    </select>
  </td>
</tr>
<?php endif; ?>
