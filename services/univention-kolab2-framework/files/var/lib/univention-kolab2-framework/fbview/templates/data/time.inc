<?php
$i = 0;
while ($i <= count($date['values']) && empty($date['values'][$i])) {
    $i++;
}
if (strpos($date['values'][$i], ':') !== false) {
    $del = ':';
} elseif (strpos($date['values'][$i], '.') !== false) {
    $del = ".";
} else {
    $del = "";
}
$ampm = (strpos(String::lower($date['values'][0]), 'am') !== false || strpos(String::lower($date['values'][0]), 'pm') !== false);
?>
<tr>
    <td><?php echo _("Select the time delimiter:") ?></td>
    <td>
        <select name="delimiter[<?php echo $key ?>]">
            <option value=":"<?php echo $del == ':' ? ' selected="selected"' : '' ?>>:</option>
            <option value="."<?php echo $del == '.' ? ' selected="selected"' : '' ?>>.</option>
        </select>
    </td>
</tr>
<tr>
    <td><?php echo _("Select the time format:") ?></td>
    <td>
        <select name="format[<?php echo $key ?>]">
            <option value="24hr"<?php echo $ampm ? '' : ' selected="selected"' ?>><?php echo _("24 hours") ?></option>
            <option value="ampm"<?php echo $ampm ? ' selected="selected"' : '' ?>><?php echo _("AM/PM") ?></option>
        </select>
    </td>
</tr>
