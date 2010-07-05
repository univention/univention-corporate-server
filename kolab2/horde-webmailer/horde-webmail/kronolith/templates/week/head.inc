<h1 class="header" style="text-align:center">
<?php
$currentView = is_a($this, 'Kronolith_View_WorkWeek') ? 'WorkWeek' : 'Week';
$prev = $this->getWeek(-1);
$next = $this->getWeek(1);
echo Horde::link($this->link(-1), _("Last week"), 'iconNav', '', 'return ShowView(\'' . $currentView . '\', { week: ' . $prev['week'] . ', year: ' . $prev['year'] . '});') . Horde::img('nav/left.png', '<', '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
echo '<span id="view_title">' . htmlspecialchars($this->days[$this->startDay]->getTime($prefs->getValue('date_format')) . ' - ' . $this->days[$this->endDay]->getTime($prefs->getValue('date_format'))) . '</span>';
echo Horde::link($this->link(1), _("Next week"), 'iconNav', '', 'return ShowView(\'' . $currentView . '\', { week: ' . $next['week'] . ', year: ' . $next['year'] . '});') . Horde::img('nav/right.png', '>', '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
?>
</h1>

<table cellspacing="0" width="100%" class="striped">
<thead>
 <tr>
  <th class="control" width="1%" colspan="3">&nbsp;</th>

<?php $colwidth = round((100 - count($this->days) - 1) / count($this->days)); foreach ($this->days as $day): ?>
  <th class="control" width="1%">&nbsp;</th>
  <th class="nowrap <?php echo ($day->isToday() ? 'selected-control' : 'control') ?>" width="<?php echo $colwidth ?>%" colspan="<?php echo $day->_totalspan ?>">
<?php
if (Kronolith::getDefaultCalendar(PERMS_EDIT) &&
    (!empty($conf['hooks']['permsdenied']) ||
     Kronolith::hasPermission('max_events') === true ||
     Kronolith::hasPermission('max_events') > Kronolith::countEvents())) {
    $addurl = Util::addParameter('new.php', array('month' => $day->month,
                                                  'year' => $day->year,
                                                  'mday' => $day->mday,
                                                  'url' => $this->link(0, true)));
    echo Horde::link(Horde::applicationUrl($addurl), _("Create a New Event"), 'iconAdd')
    . Horde::img('new_small.png', '+')
    . '</a>';
}
?>
   <strong><?php echo Horde::link($day->link(), '', 'widget') . $day->getTime('%A, %d.') ?></a></strong>
  </th>
<?php endforeach; ?>
 </tr>
