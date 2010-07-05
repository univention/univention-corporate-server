<form method="post" id="prefs" name="prefs" action="<?php echo Horde::selfUrl() ?>">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="update_prefs" />
<input type="hidden" name="group" value="<?php echo htmlspecialchars($group) ?>" />
<input type="hidden" id="prefs_app" name="app" value="<?php echo htmlspecialchars($app) ?>" />

<div class="header">
 <?php Prefs_UI::generateNavigationCell($group) ?>
 <?php echo htmlspecialchars($prefGroups[$group]['label']) ?>
 <br class="clear" />
</div>

<div class="prefsContainer item">
