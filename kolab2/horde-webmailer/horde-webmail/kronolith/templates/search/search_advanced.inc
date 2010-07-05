<?php require KRONOLITH_TEMPLATES . '/edit/javascript.inc'; ?>
<form method="post" name="eventform" action="search.php">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="search_calendar" />
<input type="hidden" name="search_mode" value="advanced" />

<?php
/* build search mode tabs. */
require_once 'Horde/UI/Tabs.php';
require_once 'Horde/Variables.php';
$sUrl = Horde::applicationUrl('search.php');
$vars = Variables::getDefaultVariables();
$tabs = new Horde_UI_Tabs('search_mode', $vars);
$tabs->addTab(_("Basic Search"), $sUrl, 'basic');
$tabs->addTab(_("Advanced Search"), $sUrl, 'advanced');
echo $tabs->render('advanced');
?>

<table cellspacing="0" class="striped">

<!-- general header -->
<tr><td align="left" colspan="5" class="control">
 <strong><?php echo _("General") ?></strong>
</td></tr>

<?php
$calendars = Kronolith::listCalendars(false, PERMS_READ);
$issearch = true;
?>
<!-- title -->
<tr>
 <td class="rightAlign"><strong><?php echo Horde::label('title', _("Tit_le")) ?></strong></td>
 <td colspan="4">
  <input type="text" name="title" id="title" value="<?php echo htmlspecialchars($event->title) ?>" size="40" maxlength="255" />
 </td>
</tr>

<!-- calendar -->
<tr>
 <td class="rightAlign">
  <strong><?php echo Horde::label('calendar', _("C_alendar")) ?></strong>
 </td>
 <td colspan="4">
  <select id="calendar" name="calendar">
  <?php
  $eCalendar = $event->getCalendar();
  echo '<option value="__any"' .
       (!$eCalendar ? ' selected="selected"' : '') . '>' . _("Any") .
       '</option>';
  foreach ($calendars as $id => $cal) {
      $sel = ($id == $eCalendar) ? ' selected="selected"' : '';
      printf('<option value="%s"%s>%s</option>',
             htmlspecialchars($id), $sel, htmlspecialchars($cal->get('name'))) . "\n";
  } ?>
  </select>
 </td>
</tr>

<!-- category -->
<tr>
 <td class="rightAlign">
  <strong><?php echo Horde::label('category', _("Categor_y")) ?></strong>
 </td>
 <td align="left" colspan="4">
  <select id="category" name="category">
  <?php
  echo '<option value="__any"';
  echo (!isset($event->category)) ? ' selected="selected"' : '';
  echo '>' . _("Any") . '</option>';
  $categories = $cManager->get();

  foreach ($categories as $name) {
      echo '<option value="' . htmlspecialchars($name) . '"' .
          (($event->category == $name) ? ' selected="selected">' : '>') .
          htmlspecialchars($name) . '</option>';
   }
  ?>
  </select>
 </td>
</tr>

<!-- location -->
<tr>
 <td class="rightAlign">
  <strong><?php echo Horde::label('location', _("Lo_cation")) ?></strong>
 </td>
 <td colspan="4">
  <input type="text" name="location" id="location" value="<?php echo htmlspecialchars($event->location) ?>" size="40" maxlength="255" />
 </td>
</tr>

<!-- status -->
<tr>
 <td class="rightAlign">
  <strong><?php echo Horde::label('status', _("Stat_us")) ?></strong>
 </td>
 <td colspan="4">
  <?php echo Kronolith::buildStatusWidget('status', $event->status, true) ?>
 </td>
</tr>

<!-- description -->
<tr>
 <td class="rightAlign">
  <strong><?php echo Horde::label('description', _("Descri_ption")) ?></strong>
 </td>
 <td colspan="4">
  <input type="text" name="description" id="description" value="<?php echo htmlspecialchars($event->description) ?>" size="40" maxlength="255" />
 </td>
</tr>

<?php require KRONOLITH_TEMPLATES . '/edit/edit_timespan.inc'; ?>

</table>

<br />
<input type="submit" class="button" value="<?php echo _("Search") ?>" />
</form>
