<?php if (!$prefs->isLocked('columns')):

Horde::addScriptFile('prototype.js', 'turba', true);
Horde::addScriptFile('effects.js', 'turba', true);
Horde::addScriptFile('dragdrop.js', 'turba', true);

global $cfgSources, $attributes;
$sources = Turba::getColumns();

?>

<script type="text/javascript">
var cur_source;
function updateColumnsPref()
{
    $('columns').value = $$('.turba-prefs-cols-panel').collect(updateColumnsPref_1).join("\n");
}
function updateColumnsPref_1(panel)
{
    var p = panel.id.replace('turba-prefs-cols-panel-', '');
    cur_source = p;
    var c = panel.select('input[type=checkbox]:checked').collect(updateColumnsPref_2).join("\t");
    if (c) {
        p += "\t" + c;
    }
    return p;
}
function updateColumnsPref_2(checkbox)
{
    if (checkbox.checked) {
        return checkbox.id.replace('turba-prefs-cols-' + cur_source + '-', '');
    }
}
</script>

<input type="hidden" name="columns" id="columns" value="<?php echo htmlspecialchars($prefs->getValue('columns')) ?>" />

<?php if (count($cfgSources) > 0): ?>

<div id="turba-prefs-cols-container">
<?php echo _("Click an address book to sort its columns. Drag columns to re-arrange them. Check a column to enable it.") ?><br /><br />

<div id="turba-prefs-cols-list">
 <ul>
  <?php $first = true; foreach ($cfgSources as $key => $info): ?>
  <li<?php if ($first) echo ' class="active"'; $first = false; ?>><a href="#" onclick="$$('#turba-prefs-cols-list .active').invoke('removeClassName', 'active'); $(this).up().addClassName('active'); $$('.turba-prefs-cols-panel').invoke('hide'); $('turba-prefs-cols-panel-' + this.readAttribute('sourcename')).show();" sourcename="<?php echo htmlspecialchars($key) ?>"><?php echo htmlspecialchars($info['title']) ?></a></li>
  <?php endforeach; ?>
 </ul>
</div>

 <div id="turba-prefs-cols-columns">

 <?php $first = true; foreach ($cfgSources as $source => $info): ?>
  <div class="turba-prefs-cols-panel" id="turba-prefs-cols-panel-<?php echo htmlspecialchars($source) ?>" style="display:<?php echo ($first ? 'block' : 'none'); $first = false; ?>;">
   <ol id="turba-prefs-<?php echo htmlspecialchars($source) ?>">
<?php

// First the selected columns in their current order.
$i = 0;
if (isset($sources[$source])) {
    $selected = array_flip($sources[$source]);
    foreach ($sources[$source] as $column) {
        if (substr($column, 0, 2) == '__' || $column == 'name') {
            continue;
        }
        $checked = isset($selected[$column]) ? ' checked="checked"' : '';
        $name = htmlspecialchars('turba-prefs-cols-' . $source . '-' . $column);
        echo '<li id="turba-prefs-cols-' . htmlspecialchars($source) . '_'
            . $i . '"><input name="' . $name . '" id="' . $name
            . '" type="checkbox" class="checkbox"' . $checked . ' />'
            . htmlspecialchars($attributes[$column]['label']) . '</li>';
        $i++;
    }
} else {
    // Need to unset this for the loop below, otherwise selected columns from
    // another source could interfere
    unset($selected);
}

// Then the unselected columns in source order.
foreach (array_keys($info['map']) as $column) {
    if (substr($column, 0, 2) == '__' || $column == 'name' ||
        isset($selected[$column])) {
        continue;
    }
    $checked = isset($selected[$column]) ? ' checked="checked"' : '';
    $name = htmlspecialchars('turba-prefs-cols-' . $source . '-' . $column);
    echo '<li id="turba-prefs-cols-' . htmlspecialchars($source) . '_' . $i
        . '"><input name="' . $name . '" id="' . $name
        . '" type="checkbox" class="checkbox"' . $checked . ' />'
        . htmlspecialchars($attributes[$column]['label']) . '</li>';
    $i++;
}
?>
   </ol>
   <script type="text/javascript">
   Sortable.create('turba-prefs-<?php echo htmlspecialchars($source, ENT_QUOTES) ?>', { onUpdate: updateColumnsPref });
   </script>
  </div>
 <?php endforeach; ?>
</div>

<br class="clear" />

</div>

<?php if ($browser->isBrowser('msie') && $browser->getMajor() < 7): ?>
<div style="clear:both;">&nbsp;</div>
<?php endif; ?>

<script type="text/javascript">
$('turba-prefs-cols-columns').observe('click', function(event) {
    if (event.element().match('input[type=checkbox]')) {
        updateColumnsPref();
    }
});
</script>

<?php
endif; // End form elements when at least 1 source.
endif; // End prefs UI if not locked.
