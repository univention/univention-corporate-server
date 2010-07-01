<?php
Horde::addScriptFile('QuickFinder.js', 'kronolith', true);
Horde::addScriptFile('redbox.js', 'kronolith', true);
Horde::addScriptFile('calendar-panel.js', 'kronolith', true);

$info_img = Horde::img('info_icon.png', _("Calendar Information"), array('class' => 'calendar-info'), $registry->getImageDir('horde'));

$remote_calendars = @unserialize($prefs->getValue('remote_cals'));
$current_user = Auth::getAuth();
$my_calendars = array();
$shared_calendars = array();
foreach (Kronolith::listCalendars() as $id => $cal) {
    if ($cal->get('owner') == $current_user) {
        $my_calendars[$id] = $cal;
    } else {
        $shared_calendars[$id] = $cal;
    }
}
?>

<div id="pageControls">

<a id="sbarShow" href="#" onclick="sbarToggle(); return false;"><?php echo _("Calendars") ?></a>
<a id="sbarHide" href="#" onclick="sbarToggle(); return false;"><?php echo _("Calendars") ?></a>

<div id="pageControlsInner">
<form action="<?php echo Horde::selfUrl() ?>" method="post">
<?php echo Util::formInput() ?>
 <h4><?php echo _("Search for Calendars:") ?></h4>
 <p>
  <input id="calendarSearch" type="text" for="mycalendars,sharedcalendars,remotecalendars,externalcalendars" />
 </p>

<?php if (Auth::getAuth()): ?>
 <p>
  <a href="<?php echo Horde::applicationUrl('calendars/') ?>"><?php echo _("[Manage Calendars]") ?></a>
 </p>
<?php endif; ?>

<?php if (count($my_calendars)): ?>
 <h4><?php echo _("My Calendars:") ?></h4>
 <ul id="mycalendars">
<?php foreach ($my_calendars as $id => $cal): ?>
  <li><label><input type="checkbox" class="checkbox" name="display_cal[]" value="<?php echo htmlspecialchars($id) ?>"<?php echo (in_array($id, $display_calendars) ? ' checked="checked"' : '') . ' /> ' . htmlspecialchars($cal->get('name')) ?></label> <?php echo $info_img ?></li>
<?php endforeach; ?>
 </ul>
<?php endif; ?>

<?php if (count($shared_calendars)): ?>
 <h4><?php echo _("Shared Calendars:") ?></h4>
 <ul id="sharedcalendars">
<?php foreach ($shared_calendars as $id => $cal): ?>
  <li><label><input type="checkbox" class="checkbox" name="display_cal[]" value="<?php echo htmlspecialchars($id) ?>"<?php echo (in_array($id, $display_calendars) ? ' checked="checked"' : '') . ' /> [' . htmlspecialchars(Auth::removeHook($cal->get('owner'))) . '] ' . htmlspecialchars($cal->get('name')) ?></label> <?php echo $info_img ?></li>
<?php endforeach; ?>
 </ul>
<?php endif; ?>

<?php if (count($GLOBALS['all_external_calendars'])): ?>
 <h4><?php echo _("External Events:") ?></h4>
 <ul id="externalcalendars">
<?php foreach ($GLOBALS['all_external_calendars'] as $api => $categories): ?>
 <?php if (count($categories)): ?>
  <li class="category"><?php echo htmlspecialchars($GLOBALS['registry']->get('name', $GLOBALS['registry']->hasInterface($api))) ?></li>
  <?php foreach ($categories as $id => $name): ?>
   <li><label><input type="checkbox" class="checkbox" name="display_cal[]" value="external_<?php echo htmlspecialchars($api . '/' . $id) ?>"<?php echo (in_array($api . '/' . $id, $GLOBALS['display_external_calendars']) ? ' checked="checked"' : '') . ' /> ' . htmlspecialchars($name) ?></label></li>
  <?php endforeach; ?>
 <?php endif; ?>
<?php endforeach; ?>
 </ul>
<?php endif; ?>

<?php if (count($remote_calendars)): ?>
 <h4><?php echo _("Remote Calendars:") ?></h4>
 <ul id="remotecalendars">
<?php foreach ($remote_calendars as $id => $cal): ?>
  <li><label><input type="checkbox" class="checkbox" name="display_cal[]" value="remote_<?php echo htmlspecialchars($cal['url']) ?>"<?php echo (in_array($cal['url'], $display_remote_calendars) ? ' checked="checked"' : '') . ' /> ' . htmlspecialchars($cal['name']) ?></label> <?php echo $info_img ?></li>
<?php endforeach; ?>
 </ul>
<?php endif; ?>

<noscript>
 <p>
  <input type="submit" value="<?php echo _("Save") ?>" class="button" />
 </p>
</noscript>
</form>

</div>
</div>
