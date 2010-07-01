<form method="post" name="contacts" id="contacts" action="browse.php">
<input type="hidden" name="source" value="<?php echo htmlspecialchars($GLOBALS['default_source']) ?>" />
<?php echo Util::formInput() ?>
<table cellspacing="0" width="100%" class="linedRow">
<thead>
 <tr>
<?php $col_count = count($this->columns) + 1; if ($this->showMark): $col_count++; ?>
  <th class="item leftAlign" width="1%" style="cursor:pointer" onclick="document.contacts.checkAll.checked = !document.contacts.checkAll.checked; SelectAll();" nowrap="nowrap"><label for="checkAll" class="hidden"><?php echo _("Check All/None") ?></label><input type="checkbox" id="checkAll" name="checkAll" onclick="document.contacts.checkAll.checked = !document.contacts.checkAll.checked; SelectAll();" <?php echo Horde::getAccessKeyAndTitle(_("Check _All/None")) ?> /></th>
<?php endif; ?>
<?php if ($this->showEdit): $col_count++; ?>
  <th class="item" width="1%"><?php echo Horde::img('edit.png', _("Edit"), '', $GLOBALS['registry']->getImageDir('horde')) ?></th>
<?php endif; ?>
<?php if ($this->showVcard): $col_count++; ?>
  <th class="item" width="1%"><?php echo Horde::img('mime/vcard.png', _("vCard"), '', $GLOBALS['registry']->getImageDir('horde')) ?></th>
<?php endif; ?>
<?php if ($this->showGroup): $col_count++; ?>
  <th class="item" width="1%"><?php echo Horde::img('group.png', _("List")) ?></th>
<?php endif; ?>
  <?php $s_url = Util::removeParameter(Horde::selfUrl(true), array('sortadd', 'sortby', 'sortdir')); for ($i = 0, $imax = count($this->columns); $i <= $imax; ++$i): ?>
    <?php $columnlabel = $GLOBALS['attributes'][$i == 0 ? 'name' : $this->getColumnName($i)]['label']; ?>
  <th class="<?php echo ($this->showSort && $this->isSortColumn($i)) ? 'selected' : 'item' ?> leftAlign" width="<?php echo $width ?>%" nowrap="nowrap">
<?php if ($this->showSort): ?>
   <?php if ($this->isSortColumn($i)): ?>
      <?php $sortdir = $this->getColumnSortDirection($i); ?>
      <?php $changetitle = sprintf(_("Change %s sort to %s"), $columnlabel, $sortdir == 0 ? _("descending") : _("ascending")) ?>
      <a class="widget" title="<?php echo $changetitle ?>" href="<?php echo Util::addParameter($s_url, array('sortadd' => 1, 'sortby' => $i, 'sortdir' => abs(1 - $sortdir))) ?>"><?php echo $this->getColumnSortImage($i) ?></a>
      <?php $changetitle = sprintf(_("Sort by %s only"), $columnlabel) ?>
      <a class="widget" title="<?php echo $changetitle ?>" href="<?php echo Util::addParameter($s_url, array('sortby' => $i, 'sortdir' => abs(1 - $sortdir))) ?>">
   <?php else: ?>
      <?php $sorttitle = sprintf(_("Sort by %s, then by %s"), $this->getSortOrderDescription(), $columnlabel) ?>
      <a class="widget" title="<?php echo $sorttitle ?>" href="<?php echo Util::addParameter($s_url, array('sortadd' => 1, 'sortby' => $i, 'sortdir' => 0)) ?>"><?php echo $this->getColumnSortImage($i, $sorttitle) ?></a>
      <a class="widget" title="<?php echo sprintf(_("Sort by %s"), $columnlabel) ?>" href="<?php echo Util::addParameter($s_url, array('sortby' => $i, 'sortdir' => 0)) ?>">
   <?php endif; ?>
<?php endif; ?>
   <?php echo $columnlabel ?>
<?php if ($this->showSort): ?></a><?php endif; ?>
  </th>
  <?php endfor; ?>
 </tr>
</thead>
<tbody id="QuickFinderEmpty" style="display:none">
 <tr>
  <td colspan="<?php echo $col_count ?>">
   <?php echo _("No contacts match the current filter.") ?>
  </td>
 </tr>
</tbody>
<tbody id="QuickFinderContacts">
