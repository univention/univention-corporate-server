<thead>
 <tr>
  <th class="control" width="10%" colspan="3">&nbsp;</th>
<?php if (!count($this->_currentCalendars)): ?>
  <th class="control" width="90%">&nbsp;</th>
<?php endif; ?>
<?php $i = 0; foreach ($this->_currentCalendars as $cid => $cal): ?>
  <th class="control" width="<?php echo round(90 / count($this->_currentCalendars)) ?>%" colspan="<?php echo $this->_span[$cid] ?>">
   <strong><?php echo htmlspecialchars($cal->get('name')) ?></strong>
  </th>
<?php endforeach; ?>
 </tr>
</thead>
