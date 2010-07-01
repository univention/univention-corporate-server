 <tr>
  <th class="control" width="1%" colspan="3">&nbsp;</th>
<?php $colwidth = round((100 - (count($this->days) * 2) - 1) / count($this->days)); foreach ($this->days as $day): ?>
  <th class="control" width="1%">&nbsp;</th>
<?php if (!count($this->_currentCalendars)): ?>
  <th width="<?php echo $colwidth ?>%" class="<?php echo ($day->isToday() ? 'selected-control' : 'control') ?>">&nbsp;</th>
<?php endif; ?>
<?php foreach ($this->_currentCalendars as $cid => $cal): ?>
  <th class="<?php echo ($day->isToday() ? 'selected-control' : 'control') ?>" width="<?php echo floor((90 / count($this->days)) / count($this->_currentCalendars)) ?>%" colspan="<?php echo $day->_span[$cid] ?>">
   <strong><?php echo htmlspecialchars($cal->get('name')) ?></strong>
  </th>
<?php endforeach; endforeach; ?>
 </tr>
