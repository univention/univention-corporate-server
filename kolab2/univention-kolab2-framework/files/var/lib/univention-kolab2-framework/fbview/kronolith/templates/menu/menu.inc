<?php if ($browser->hasFeature('dom')):
    $gotourl = Util::addParameter($registry->getParam('webroot', 'horde') . '/services/javascript.php', 'file', 'goto.inc');
    $gotourl = Util::addParameter($gotourl, 'app', 'kronolith');
    $gotourl = Horde::url($gotourl);
?>
<script language="JavaScript" type="text/javascript" src="<?php echo $gotourl ?>"></script>
<div id="kgoto" class="headerbox" style="position:absolute;visibility:hidden;left:50px;top:50px;padding:0px;"></div>
<?php endif; ?>
<table border="0" cellpadding="0" cellspacing="0" width="100%">
<tr><td class="menu"><table border="0" width="100%"><tr>

<?php
/* Kronolith menu items. */
/*echo Menu::createItem(Horde::applicationUrl($prefs->getValue('defaultview') . '.php'), _("_Today"), 'today.gif', null, null, null, '__noselection');
if ($browser->hasFeature('dom')) {
    echo Menu::createItem('#', _("_Goto"), 'goto.gif', null, '', 'openGoto(\'' . $timestamp . '\'); return false;');
}
echo Menu::createItem(Horde::applicationUrl('day.php' . $append), _("_Day"), 'dayview.gif');
echo Menu::createItem(Horde::applicationUrl('workweek.php' . $append), _("Wor_k Week"), 'workweekview.gif');
echo Menu::createItem(Horde::applicationUrl('week.php' . $append), _("_Week"), 'weekview.gif');
echo Menu::createItem(Horde::applicationUrl('month.php' . $append), _("_Month"), 'monthview.gif');*/
echo Menu::createItem(Horde::applicationUrl('attendeesview.php' . $append), _("_Free/Busy"), 'attendees.gif');

/*if (Kronolith::getDefaultCalendar(PERMS_EDIT)) {
    echo Menu::createItem(Horde::applicationUrl('addevent.php'), _("_New Event"), 'new.gif');
}*/

/* Import/Export. */
/*if ($conf['menu']['import_export']) {
    echo Menu::createItem(Horde::applicationUrl('data.php' . $append), _("_Import/Export"), 'data.gif', $registry->getParam('graphics', 'horde'));
}*/

/* Print. */
/*if ($conf['menu']['print'] && isset($print_link) && $browser->hasFeature('javascript')) {
    echo Menu::createItem('#', _("_Print"), 'print.gif', $registry->getParam('graphics', 'horde'), '', "open_print_win('$print_link'); return false;");
}*/

/* Additional site-specific menu items. */
//Menu::siteLinks();

/* Options menu. */
/*if (($conf['prefs']['driver'] != '') && ($conf['prefs']['driver'] != 'none')) {
    echo Menu::createItem(Horde::url($registry->getParam('webroot', 'horde') . '/services/prefs.php?app=kronolith'), _("_Options"), 'prefs.gif', $registry->getParam('graphics', 'horde'));
}*/

/* Online Help. */
/*if ($help_link = Help::listLink('kronolith')) {
    echo Menu::createItem($help_link, _("_Help"), 'manual.gif', $registry->getParam('graphics', 'horde'));
}*/

/* Links to other Horde applications. */
Menu::appLinks();
?>
<td width="100%">&nbsp;</td><!-- spacer -->

<?php if (!$prefs->isLocked('default_share') && ((count($remote_calendars) > 1 || count($GLOBALS['all_calendars']) > 1) || !count($GLOBALS['display_calendars']))): ?>
<?php echo Menu::createItem(Horde::applicationUrl($prefs->getValue('defaultview') . '.php'), _("_Show"), 'kronolith.gif', null, null, 'return listCalendarsSubmit();', '__noselection'); ?>
<td class="light" align="left">
<?php if (strstr($_SERVER['PHP_SELF'], 'month.php') !== false ||
                strstr($_SERVER['PHP_SELF'], 'week.php') !== false ||
                strstr($_SERVER['PHP_SELF'], 'workweek.php') !== false ||
                strstr($_SERVER['PHP_SELF'], 'day.php') !== false) :?>
<form action="<?php echo Horde::selfUrl() ?>" method="post" name="calmenu">
<?php else: ?>
<form action="<?php echo Horde::applicationUrl($prefs->getValue('defaultview') . '.php') ?>" method="post" name="calmenu">
<?php endif; ?>
<?php Util::pformInput() ?>
<input type="hidden" name="timestamp" value="<?php echo $timestamp ?>" />
<select name="display_cal" onchange="listCalendarsSubmit();">
<?php if (count($my_calendars)): ?>
  <option value=""><?php echo _("My Calendars:") ?></option>
<?php foreach ($my_calendars as $id => $cal): ?>
  <option value="<?php echo $id ?>"><?php echo (in_array($id, $display_calendars) ? '+ ' : '&#8211; ') . $cal->get('name') ?></option>
<?php endforeach; ?>
<?php endif; ?>
<?php if (count($shared_calendars)): ?>
  <option value=""><?php echo _("Shared Calendars:") ?></option>
<?php foreach ($shared_calendars as $id => $cal): ?>
  <option value="<?php echo $id ?>"><?php echo (in_array($id, $display_calendars) ? '+ ' : '&#8211; ') . '[' . $cal->get('owner') . '] ' . $cal->get('name') ?></option>
<?php endforeach; ?>
<?php endif; ?>
<?php if (count($remote_calendars)): ?>
  <option value=""><?php echo _("Remote Calendars:") ?></option>
  <?php foreach ($remote_calendars as $id => $cal): ?>
    <option value="remote_<?php echo $cal['url'] ?>"><?php echo (in_array($cal['url'], $display_remote_calendars) ? '+ ' : '&#8211; ') . $cal['name'] ?></option>
  <?php endforeach; ?>
<?php endif; ?>
</select>
</form>
<script language="JavaScript" type="text/javascript">
<!--
var loading;
function listCalendarsSubmit()
{
    document.calmenu.submit();
    return false;
}
// -->
</script>
</td>
<?php endif; ?>
</tr></table></td></tr></table><br />
