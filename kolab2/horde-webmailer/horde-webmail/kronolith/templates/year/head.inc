<h1 class="header" style="text-align:center">
<?php
echo Horde::link($this->link(-1), _("Last Year"), 'iconNav', '', 'return ShowView(\'Year\', {year:' . ($this->year - 1) . '});') . Horde::img('nav/left.png', '<', '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
echo '<span id="view_title">' . htmlspecialchars($this->year) . '</span>';
echo Horde::link($this->link(1), _("Next Year"), 'iconNav', '', 'return ShowView(\'Year\', {year:' . ($this->year + 1) . '});') . Horde::img('nav/right.png', '>', '', $GLOBALS['registry']->getImageDir('horde')) . '</a>';
?>
</h1>
