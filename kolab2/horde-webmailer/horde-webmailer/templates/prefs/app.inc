<form method="get" name="appswitch" id="appswitch" action="<?php echo $registry->get('webroot', 'horde') . '/services/prefs.php' ?>">
<?php echo Util::formInput() ?>
<div class="header">
 <span class="smallheader rightFloat">
  <?php echo Horde::label('app', _("Edit options for:")) ?>
  <select id="app" name="app" onchange="document.appswitch.submit();">
    <option value=""><?php echo _("Choose Application:") ?></option>
<?php if (!empty($apps['horde'])): ?>
    <option value="" disabled="disabled">- - - - - - - - -</option>
    <option value="horde"><?php echo _("Global Options") ?></option>
    <option value="" disabled="disabled">- - - - - - - - -</option>
<?php endif; ?>
   <?php foreach ($apps as $key => $val): if ($key == 'horde') continue; ?>
    <option value="<?php echo htmlspecialchars($key) ?>"><?php echo htmlspecialchars($val) ?></option>
   <?php endforeach; ?>
  </select>
  <input class="button" type="submit" onclick="return document.appswitch.app.selectedIndex != 0;" value="<?php echo _("Go") ?>" />
 </span>
 <?php if ($registry->getApp() == 'horde') echo _("Global Options"); else printf(_("Options for %s"), $registry->get('name')) ?>
 <br class="clear" />
</div>
</form>
<br class="spacer" />
