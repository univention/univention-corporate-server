<?php
if (empty($url)) {
    $url = Util::addParameter('month.php', array('month' => $month,
                                                 'year' => $year));
    $url = Horde::applicationUrl($url, true);
}
?>
<form action="delete.php" method="post" id="deleteform" name="delete">
<?php echo Util::formInput() ?>
<input type="hidden" name="year" value="<?php if (isset($year)) echo htmlspecialchars($year) ?>" />
<input type="hidden" name="month" value="<?php if (isset($month)) echo htmlspecialchars($month) ?>" />
<input type="hidden" name="mday" value="<?php if (isset($day)) echo htmlspecialchars($day) ?>" />
<input type="hidden" name="url" value="<?php echo htmlspecialchars($url) ?>" />
<input type="hidden" name="eventID" value="<?php echo htmlspecialchars($this->event->getId()) ?>" />
<input type="hidden" name="calendar" value="<?php echo htmlspecialchars($this->event->getCalendar()) ?>" />

<table class="striped" cellspacing="0">
<tr><td class="warning"><?php echo _("This is a recurring event. Delete the current event only, this<br />occurrence and all future occurences, or all occurences?") ?></td></tr>

<?php if (!empty($this->event->attendees)): ?>
<tr><td><input id="sendupdates_del" type="checkbox" class="checkbox" name="sendupdates" checked="checked" /><label for="sendupdates_del"> <?php echo _("Send a cancel notification to all attendees when deleting this event?") ?></label></td></tr>
<?php endif ?>

<tr><td>
 <input type="submit" class="button" name="current" value="<?php echo _("Current") ?>" />
 <input type="submit" class="button" name="future" value="<?php echo _("Future") ?>" />
 <input type="submit" class="button" name="all" value="<?php echo _("All") ?>" />
 <a class="button" href="<?php echo htmlspecialchars($url) ?>"><?php echo _("Cancel") ?></a>
</td></tr>
</table>

</form>
