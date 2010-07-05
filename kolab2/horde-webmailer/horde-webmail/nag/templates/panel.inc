<?php

Horde::addScriptFile('redbox.js', 'nag', true);

$info_img = Horde::img('info_icon.png', _("Task List Information"), array('class' => 'tasklist-info'), $registry->getImageDir('horde'));

$current_user = Auth::getAuth();
$my_tasklists = array();
$shared_tasklists = array();
foreach (Nag::listTasklists() as $id => $tl) {
    if ($tl->get('owner') == $current_user) {
        $my_tasklists[$id] = $tl;
    } else {
        $shared_tasklists[$id] = $tl;
    }
}
?>

<div id="pageControls">
<script type="text/javascript">
//<![CDATA[
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

    new Ajax.Request('<?php echo Horde::applicationUrl('pref_api.php', true) ?>', { parameters: { app: 'nag', pref: 'show_panel', value: pref_value } });
}

document.observe('dom:loaded', function() {
    $$('#pageControlsInner .tasklist-info').invoke('observe', 'click', function() {
        RedBox.loading();
        var tasklist_id = this.previous().down('.checkbox').value;
        new Ajax.Request('<?php echo Horde::applicationUrl('tasklists/info.php') ?>', {
            parameters: { t: tasklist_id },
            method: 'get',
            onSuccess: function(transport) {
                RedBox.showHtml('<div id="RB_info">' + transport.responseText + '<input type="button" class="button" onclick="RedBox.close();" value="<?php echo _("Close") ?>" /><' + '/div>');
            },
            onFailure: function(transport) {
                RedBox.close();
            }
        });
    });
});
//]]>
</script>
<a id="sbarShow" href="#" onclick="sbarToggle(); return false;"><?php echo _("Task Lists") ?></a>
<a id="sbarHide" href="#" onclick="sbarToggle(); return false;"><?php echo _("Task Lists") ?></a>

<div id="pageControlsInner">
<form action="<?php echo Horde::selfUrl() ?>" method="post">
<?php echo Util::formInput() ?>
 <h4><?php echo _("Search for Task Lists:") ?></h4>
 <p>
  <input id="tasklistSearch" type="text" for="mytasklists,sharedtasklists" />
 </p>

<?php if (Auth::getAuth()): ?>
 <p>
  <a href="<?php echo Horde::applicationUrl('tasklists/') ?>"><?php echo _("[Manage Task Lists]") ?></a>
 </p>
<?php endif; ?>

<?php if ($current_user): ?>
 <h4><?php echo _("My Task Lists:") ?></h4>
 <ul id="mytasklists">
<?php foreach ($my_tasklists as $id => $tl): ?>
  <li><label><input type="checkbox" class="checkbox" name="display_tasklist[]" value="<?php echo htmlspecialchars($id) ?>"<?php echo (in_array($id, $display_tasklists) ? ' checked="checked"' : '') . ' /> ' . htmlspecialchars($tl->get('name')) ?></label> <?php echo $info_img ?></li>
<?php endforeach; ?>
 </ul>
<?php endif; ?>

<?php if (count($shared_tasklists)): ?>
 <h4><?php echo _("Shared Task Lists:") ?></h4>
 <ul id="sharedtasklists">
<?php foreach ($shared_tasklists as $id => $tl): ?>
  <li><label><input type="checkbox" class="checkbox" name="display_tasklist[]" value="<?php echo htmlspecialchars($id) ?>"<?php echo (in_array($id, $display_tasklists) ? ' checked="checked"' : '') . ' /> [' . htmlspecialchars(Auth::removeHook($tl->get('owner'))) . '] ' . htmlspecialchars($tl->get('name')) ?></label> <?php echo $info_img ?></li>
<?php endforeach; ?>
 </ul>
<?php endif; ?>

 <p>
  <input type="submit" value="<?php echo _("Save") ?>" class="button" />
 </p>
</form>

</div>
</div>
