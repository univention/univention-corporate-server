<table class="nopadding" cellspacing="6" width="100%">
<?php
$rows = $layout->rows();
list($current_row, $current_col) = $layout->getCurrentBlock();
$allow_add = !empty($conf['hooks']['permsdenied']) ||
    (Horde::hasPermission('max_blocks') === true) ||
    (Horde::hasPermission('max_blocks') > $layout->count());
$columns = 0;
for ($row = 0; $row < $rows; ++$row):
?>
  <tr>
<?php
$columns = $layout->columns($row);
if (is_a($columns, 'PEAR_Error')) {
    $columns = 0;
}
for ($col = 0; $col < $columns; ++$col):
    $isEditing = ($current_row === $row && $current_col === $col);
    $colspan = $layout->getWidth($row, $col);
    if ($layout->isCovered($row, $col)):
?>
    <!-- covered cell here -->
<?php else: ?>
    <td class="<?php echo $isEditing ? 'currentBlock' : 'headerbox' ?>" valign="top" width="<?php echo floor(100 / ($columns + 1)) * $colspan ?>%" rowspan="<?php echo $layout->getHeight($row, $col) ?>" colspan="<?php echo $colspan ?>">
<?php
$blockInfo = $layout->getBlockInfo($row, $col);
if (!$layout->isEmpty($row, $col) && !is_a($blockInfo, 'PEAR_Error')) {
    require dirname(__FILE__) . '/layout.inc';
} else {
    if ($allow_add) {
        require dirname(__FILE__) . '/add.inc';
    }
}
?>
    </td>
<?php endif; endfor; if ($allow_add): ?>
    <td valign="top" class="headerbox">
      <?php require dirname(__FILE__) . '/add.inc'; ?>
    </td>
<?php endif; ?>
  </tr>
<?php endfor; if ($allow_add): ?>
  <tr>
<?php
for ($col = 0; $col <= $columns; ++$col):
?>
    <td valign="top" class="headerbox">
      <?php require dirname(__FILE__) . '/add.inc'; ?>
    </td>
<?php endfor; ?>
  </tr>
<?php endif; ?>
</table>
