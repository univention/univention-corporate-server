<h1 class="header">
 <?php echo _("My Free/Busy URL") ?>
</h1>
<div class="headerbox">
 <div class="control">
  <?php echo _("Copy this URL for use wherever you need your Free/Busy URL:") ?>
 </div>
 <p class="text">
  <?php echo Util::addParameter(Horde::applicationUrl('fb.php', true, -1), 'u', Auth::getAuth()) ?>
 </p>
</div>

<br class="spacer" />
<?php
if (!$prefs->isLocked('fb_cals')) {
    $fb_cals = Kronolith::ListCalendars();
    $fb_calsSaved = unserialize($prefs->getValue('fb_cals'));
    $fb_calSelect = '';
    foreach ($fb_cals as $fb_cal => $cal) {
        if (!is_bool(array_search($fb_cal, $fb_calsSaved))) {
            $fb_calSelect .= '<option value="' . htmlspecialchars($fb_cal) . '" selected="selected">' . htmlspecialchars($cal->get('name')) . '</option>';
        } else {
            $fb_calSelect .= '<option value="' . htmlspecialchars($fb_cal) . '">' . htmlspecialchars($cal->get('name')) . '</option>';
        }
    }

    if ($fb_calSelect) {
        echo Horde::label('fb_cals', _("Choose the calendars to include in the above Free/Busy URL:")) . '<br />' .
            '<select multiple="multiple" id="fb_cals" name="fb_cals[]">' . $fb_calSelect . '</select><br /><br class="spacer" />';
    }
}
