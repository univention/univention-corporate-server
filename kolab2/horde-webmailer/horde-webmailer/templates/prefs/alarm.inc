<?php
Horde::addScriptFile('prototype.js', 'horde', true);
$alarm_pref = unserialize($prefs->getValue($pref));
$selected = array_keys($alarm_pref);
$methods = Horde_Alarm::notificationMethods();
echo Horde::label($pref, $_prefs[$pref]['desc']) ?>&nbsp;<?php echo $helplink ?><br />
<select id="<?php echo $pref ?>" multiple="multiple" name="<?php echo $pref ?>[]" onchange="updateParams()">
<?php foreach ($methods as $method => $params): ?>
<option<?php if (in_array($method, $selected)) echo ' selected="selected"' ?> value="<?php echo $method ?>"><?php echo $params['__desc'] ?></option>
<?php endforeach; ?>
</select>
<?php foreach ($methods as $method => $params): if (count($params) > 1): ?>
<div id="<?php echo $method ?>Params">
<?php foreach ($params as $name => $param): if (substr($name, 0, 2) == '__') continue; ?>

<?php if ($param['type'] == 'text'): ?>
<?php echo Horde::label($pref . '_' . $name, $param['desc']) ?><br />
<input type="text" id="<?php echo $pref . '_' . $name ?>" name="<?php echo $pref . '_' . $name ?>" value="<?php echo empty($alarm_pref[$method][$name]) ? '' : htmlspecialchars($alarm_pref[$method][$name]) ?>" /><br />

<?php elseif ($param['type'] == 'boolean'): ?>
<input type="checkbox" id="<?php echo $pref . '_' . $name ?>" name="<?php echo $pref . '_' . $name ?>"<?php if (!empty($alarm_pref[$method][$name])) echo ' checked="checked"' ?> />
<?php echo Horde::label($pref . '_' . $name, $param['desc']) ?><br />

<?php elseif ($param['type'] == 'sound'): $current_sound = !empty($alarm_pref[$method][$name]) ? $alarm_pref[$method][$name] : ''; ?>
<ul class="sound-list">
 <li><label><input type="radio" name="<?php echo $pref . '_' . $name ?>" value=""<?php if (!$current_sound) echo ' checked="checked"' ?> /> <?php echo _("No Sound") ?></label></li>
<?php foreach (glob($registry->get('themesfs', 'horde') . '/sounds/*.wav') as $sound): $sound = basename($sound); ?>
 <li>
  <label>
   <input type="radio" name="<?php echo $pref . '_' . $name ?>" value="<?php echo htmlspecialchars($sound) ?>"<?php if ($current_sound == $sound) echo ' checked="checked"' ?> />
   <?php echo htmlspecialchars($sound) ?>
  </label>
  <embed autostart="false" src="<?php echo $registry->get('themesuri', 'horde') . '/sounds/' . htmlspecialchars($sound) ?>" />
 </li>
<?php endforeach; ?>
</ul>

<?php endif; endforeach; ?>
</div>
<?php endif; endforeach; ?>
<script type="text/javascript">
function updateParams()
{
    ['notify','popup','mail','sms'].each(function(method) {
        if ($(method + 'Params')) {
            if (Form.Element.getValue('<?php echo $pref ?>').include(method)) {
                Element.show(method + 'Params');
            } else {
                Element.hide(method + 'Params');
            }
        }
    });
}
updateParams();
</script>
