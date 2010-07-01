<h1 class="header" style="text-align:center">
<?php
$prev = $this->getMonth(-1);
$next = $this->getMonth(1);
echo Horde::link($this->link(-1), _("Last Month"), 'iconNav', '', 'return ShowView(\'Month\', { month: ' . $prev['month'] . ', year: ' . $prev['year'] . '});') . Horde::img('nav/left.png', '<', '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
echo '<span id="view_title">' . htmlspecialchars(strftime('%B %Y', $this->getStamp())) . '</span>';
echo Horde::link($this->link(1), _("Next Month"), 'iconNav', '', 'return ShowView(\'Month\', { month: ' . $next['month'] . ', year: ' . $next['year'] . '});') . Horde::img('nav/right.png', '>', '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
?>
</h1>

<table class="monthgrid nopadding" cellspacing="0">
<thead>
 <tr>
<?php if (!$prefs->getValue('week_start_monday')): ?>
  <th class="item"><?php echo _("Sunday") ?></th>
<?php endif; ?>
  <th class="item"><?php echo _("Monday") ?></th>
  <th class="item"><?php echo _("Tuesday") ?></th>
  <th class="item"><?php echo _("Wednesday") ?></th>
  <th class="item"><?php echo _("Thursday") ?></th>
  <th class="item"><?php echo _("Friday") ?></th>
  <th class="item"><?php echo _("Saturday") ?></th>
<?php if ($prefs->getValue('week_start_monday')): ?>
  <th class="item"><?php echo _("Sunday") ?></th>
<?php endif; ?>
 </tr>
</thead>
<tbody>
