<?php
$calendar_names = array();
foreach ($GLOBALS['display_calendars'] as $calendarId) {
    $calendar_names[] = htmlspecialchars($GLOBALS['all_calendars'][$calendarId]->get('name'));
}
?>
<br />
<h3><?php echo _("Calendars Printed: ") ?></h3>
<p><?php echo implode(', ', $calendar_names) ?></p>
