<?php
$i = 0;
while ($i < count($date['values']) && empty($date['values'][$i])) {
    $i++;
}
if (strpos($date['values'][$i], '/') !== false) {
    $del = '/';
} elseif (strpos($date['values'][$i], '.') !== false) {
    $del = ".";
} elseif (strpos($date['values'][$i], '-') !== false) {
    $del = "-";
} else {
    $del = "";
}
?>
<tr>
    <td><?php echo _("Select the date delimiter:") ?></td>
    <td>
        <select name="delimiter[<?php echo $key ?>]">
            <option value="/"<?php echo $del == '/' ? ' selected="selected"' : '' ?>>/</option>
            <option value="."<?php echo $del == '.' ? ' selected="selected"' : '' ?>>.</option>
            <option value="-"<?php echo $del == '-' ? ' selected="selected"' : '' ?>>-</option>
        </select>
    </td>
</tr>
<tr>
    <td><?php echo _("Select the date format:") ?></td>
    <td>
        <select name="format[<?php echo $key ?>]">
            <option value="mday/month/year"><?php echo _("DD") . $del . _("MM") . $del . _("YY") ?></option>
            <option value="month/mday/year"><?php echo _("MM") . $del . _("DD") . $del . _("YY") ?></option>
            <option value="year/month/mday"><?php echo _("YY") . $del . _("MM") . $del . _("DD") ?></option>
            <option value="year/mday/month"><?php echo _("YY") . $del . _("DD") . $del . _("MM") ?></option>
        </select>
    </td>
</tr>
