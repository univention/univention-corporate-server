<?php
$current_user = Auth::getAuth();
$my_notepads = array();
$shared_notepads = array();
$all_notepads = Mnemo::listNotepads();
foreach (array_keys($all_notepads) as $id) {
    if ($all_notepads[$id]->get('owner') == $current_user) {
        $my_notepads[$id] = &$all_notepads[$id];
    } else {
        $shared_notepads[$id] = &$all_notepads[$id];
    }
}

?>

<div id="pageControls">
<script type="text/javascript">
function sbarToggle()
{
    var pref_value;
    if (Element.hasClassName(document.body, 'rightPanel')) {
        pref_value = 0;
        Element.removeClassName(document.body, 'rightPanel');
    } else {
        pref_value = 1;
        Element.addClassName(document.body, 'rightPanel');
    }

    new Ajax.Request('<?php echo Horde::applicationUrl('pref_api.php', true) ?>', { parameters: { app: 'mnemo', pref: 'show_panel', value: pref_value } });
}
</script>
<a id="sbarShow" href="#" onclick="sbarToggle(); return false;"><?php echo _("Notepads") ?></a>
<a id="sbarHide" href="#" onclick="sbarToggle(); return false;"><?php echo _("Notepads") ?></a>

<div id="pageControlsInner">
<form action="<?php echo Horde::selfUrl() ?>" method="post">
<?php echo Util::formInput() ?>
 <h4><?php echo _("Search for Notepads:") ?></h4>
 <p>
  <input id="notepadSearch" type="text" for="mynotepads,sharednotepads" />
 </p>

<?php if (Auth::getAuth()): ?>
 <p>
  <a href="<?php echo Horde::applicationUrl('notepads/') ?>"><?php echo _("[Manage Notepads]") ?></a>
 </p>
<?php endif; ?>

<?php if ($current_user): ?>
 <h4><?php echo _("My Notepads:") ?></h4>
 <ul id="mynotepads">
<?php foreach (array_keys($my_notepads) as $id): ?>
  <li><label><input type="checkbox" class="checkbox" name="display_notepad[]" value="<?php echo htmlspecialchars($id) ?>"<?php echo (in_array($id, $display_notepads) ? ' checked="checked"' : '') . ' /> ' . htmlspecialchars($my_notepads[$id]->get('name')) ?></label></li>
<?php endforeach; ?>
 </ul>
<?php endif; ?>

<?php if (count($shared_notepads)): ?>
 <h4><?php echo _("Shared Notepads:") ?></h4>
 <ul id="sharednotepads">
<?php foreach (array_keys($shared_notepads) as $id): ?>
  <li><label><input type="checkbox" class="checkbox" name="display_notepad[]" value="<?php echo htmlspecialchars($id) ?>"<?php echo (in_array($id, $display_notepads) ? ' checked="checked"' : '') . ' /> [' . htmlspecialchars(Auth::removeHook($shared_notepads[$id]->get('owner'))) . '] ' . htmlspecialchars($shared_notepads[$id]->get('name')) ?></label></li>
<?php endforeach; ?>
 </ul>
<?php endif; ?>

 <p>
  <input type="submit" value="<?php echo _("Save") ?>" class="button" />
 </p>
</form>

</div>
</div>
