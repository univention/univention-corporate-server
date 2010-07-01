<form name="directory_list" action="<?php echo Horde::applicationUrl('browse.php') ?>" method="get">
<?php echo Util::formInput() ?>
<div id="menu">
<?php if ($browse_source_count > 1): ?>
 <div class="rightFloat">
  <label for="menu_source" class="hidden"><?php echo _("Source:") ?></label>
  <select id="menu_source" name="source" onchange="document.directory_list.submit();"><?php echo $browse_source_options ?></select>
  <noscript><input class="button" type="submit" value="<?php echo _("Browse") ?>" /></noscript>
 </div>
<?php endif; ?>
 <div class="leftFloat">
  <?php echo Turba::getMenu('string') ?>
 </div>
</div>
</form>
<?php $GLOBALS['notification']->notify(array('listeners' => 'status')) ?>
