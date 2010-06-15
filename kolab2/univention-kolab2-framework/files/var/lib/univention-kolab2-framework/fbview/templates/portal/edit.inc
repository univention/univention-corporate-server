<table cellpadding="0" cellspacing="6" border="0" width="100%">
<?php
$rows = $layout->rows();
$columns = 0;
for ($row = 0; $row < $rows; $row++):
?>
  <tr>
<?php
$columns = $layout->columns($row);
for ($col = 0; $col < $columns; $col++):
    if ($layout->isCovered($row, $col)):
?>
    <!-- covered cell here -->
<?php else: ?>
    <td class="summary" valign="top" width="<?php echo floor(100 / ($columns + 1)) ?>%" rowspan="<?php echo $layout->getHeight($row, $col) ?>" colspan="<?php echo $layout->getWidth($row, $col) ?>"<?php if ($edit_row === $row && $edit_col === $col) echo ' style="border:2px solid red"' ?>>
<?php
$blockInfo = $layout->getBlockInfo($row, $col);
if (!$layout->isEmpty($row, $col) && !is_a($blockInfo, 'PEAR_Error')) {
    if ($edit_row === $row && $edit_col === $col) {
        $edit_link = '&nbsp;';
    } else {
        $edit_link = Horde::link($layout->getActionUrl('edit', $row, $col), _("Edit Block"), 'smallheader', '', '', _("Edit Block")) . _("Edit") . '</a>';
    }

    $defaults = array();
    foreach ($blocks->getParams($blockInfo['app'], $blockInfo['block']) as $param) {
        $defaults[$param] = $blocks->getDefaultValue($blockInfo['app'], $blockInfo['block'], $param);
    }
    include HORDE_TEMPLATES . '/portal/layout.inc';
} else {
    include HORDE_TEMPLATES . '/portal/add.inc';
}
?>
    </td>
<?php endif; endfor; ?>
    <td valign="top" class="summary">
      <?php include HORDE_TEMPLATES . '/portal/add.inc'; ?>
    </td>
  </tr>
<?php endfor; ?>
  <tr>
<?php
for ($col = 0; $col <= $columns; $col++):
?>
    <td valign="top" class="summary">
      <?php include HORDE_TEMPLATES . '/portal/add.inc'; ?>
    </td>
<?php endfor; ?>
  </tr>
</table>
