<form action="filters.php" method="post" name="rulesetsmenu">
<?php echo Util::formInput() ?>
<div id="menu">
<?php if (!empty($ingo_shares) && count($all_rulesets) > 1): ?>
 <div style="float:right">
<label for="ruleset" class="hidden"><?php echo _("Select ruleset to display:") ?></label>
<select id="ruleset" name="ruleset" onchange="document.rulesetsmenu.submit(); return false;">
  <option value=""><?php echo _("Select ruleset to display:") ?></option>
<?php foreach (array_keys($all_rulesets) as $id): ?>
  <option value="<?php echo htmlspecialchars($id) ?>"<?php echo ($_SESSION['ingo']['current_share'] == $id ? ' selected="selected"' : '') . '>' . htmlspecialchars($all_rulesets[$id]->get('name')) ?></option>
<?php endforeach; ?>
</select>
 </div>
<?php endif; ?>

 <?php echo Ingo::getMenu('string') ?>
</div>
</form>

<?php $GLOBALS['notification']->notify(array('listeners' => 'status')) ?>
