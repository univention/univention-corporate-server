<?php
if (empty($url)) {
    $url = Util::addParameter('month.php', array('month' => $month,
                                                 'year' => $year));
    $url = Horde::applicationUrl($url, true);
}
?>
<form action="delete.php" method="post" name="delete">
<?php echo Util::formInput() ?>
<input type="hidden" name="year" value="<?php if (isset($year)) echo htmlspecialchars($year) ?>" />
<input type="hidden" name="month" value="<?php if (isset($month)) echo htmlspecialchars($month) ?>" />
<input type="hidden" name="mday" value="<?php if (isset($day)) echo htmlspecialchars($day) ?>" />
<input type="hidden" name="url" value="<?php echo htmlspecialchars($url) ?>" />
<input type="hidden" name="eventID" value="<?php echo htmlspecialchars($this->event->getId()) ?>" />
<input type="hidden" name="calendar" value="<?php echo htmlspecialchars(Util::getFormData('calendar')) ?>" />

<div class="headerbox">
<?php if (!empty($this->event->attendees)): ?>
 <p><input id="sendupdates_del" type="checkbox" class="checkbox" name="sendupdates" checked="checked" /><label for="sendupdates_del"> <?php echo _("Send a cancel notification to all attendees when deleting this event?") ?></label></p>
<?php endif ?>

 <p><?php echo _("Permanently delete this event?") ?></p>

 <input type="submit" class="button" name="delete" value="<?php echo _("Delete") ?>" />
 <a class="button" href="<?php echo htmlspecialchars($url) ?>"><?php echo _("Cancel") ?></a>
</div>

</form>
