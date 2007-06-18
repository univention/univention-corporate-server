</tr>
</table>
<table border="0" cellspacing="0" cellpadding="1" width="100%">
<tr>
  <td align="left" class="control" nowrap="nowrap">
    <span class="legend">
    <b><?php echo _("Records displayed:") ?></b>
<?php
if (!empty($numDisplayed)) {
    echo '[' . sprintf(_("%s to %s of %s"), $start, $end, $numDisplayed) . ']';
} else {
    echo _("None");
}
?>
  </span>
  </td>
  <td class="control" width="100%">
    <?php if (isset($pager)) echo $pager->render() ?>
  </td>
</tr>
</table>
