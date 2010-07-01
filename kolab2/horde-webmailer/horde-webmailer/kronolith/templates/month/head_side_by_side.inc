<h1 class="header" style="text-align:center">
<?php
$prev = $this->getMonth(-1);
$next = $this->getMonth(1);
echo Horde::link($this->link(-1), _("Last Month"), 'iconNav', '', 'return ShowView(\'Month\', { month: ' . $prev['month'] . ', year: ' . $prev['year'] . '});') . Horde::img('nav/left.png', '<', '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
echo htmlspecialchars(strftime('%B %Y', $this->getStamp()));
echo Horde::link($this->link(1), _("Next Month"), 'iconNav', '', 'return ShowView(\'Month\', { month: ' . $next['month'] . ', year: ' . $next['year'] . '});') . Horde::img('nav/right.png', '>', '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
?>
</h1>

<table class="monthgrid" cellspacing="0">
<thead>
 <tr class="item">
<?php
$dayofweek = 0;
$offset = $prefs->getValue('week_start_monday') ? 1 : 0;
for ($day = (1 - $this->_startday); $day < (1 - $this->_startday) + $this->_daysInView; $day++):
?>
  <th><?php echo strftime('%A', mktime(0, 0, 0, $this->month, $day + $offset, $this->year)) ?></th>
<?php $dayofweek++; if (($dayofweek % 7 == 0) && ($dayofweek != 0)): ?>
  <th>&nbsp;</th>
<?php endif; endfor; ?>
 </tr>
</thead>
<tbody>
