<?php if ($prefs->isLocked('default_identity')): ?>
<input type="hidden" name="identity" value="<?php echo (int)$GLOBALS['identity']->getDefault() ?>" />
<?php else: ?>
<script type="text/javascript">
var identities = [];
<?php
global $identity;
$identities = $identity->getAll('id');
$default_identity = $identity->getDefault();
$members = $prefGroups['identities']['members'];
for ($i = 0; $i < count($identities); ++$i):
?>
identities[<?php echo $i ?>] = [];
<?php
$k = 0;
foreach ($members as $member):
    if ($member == 'default_identity' ||
        !empty($_prefs[$member]['locked']) ||
        $_prefs[$member]['type'] == 'special' ||
        $_prefs[$member]['type'] == 'link') {
        continue;
    }
?>
identities[<?php echo $i ?>][<?php echo $k++ ?>] = ["<?php echo $member ?>", "<?php echo $_prefs[$member]['type'] ?>", <?php
$val = $identity->getValue($member, $i);
switch ($_prefs[$member]['type']) {
case 'checkbox':
    echo $val ? 'true' : 'false';
    break;

case 'number':
    echo (int)$val;
    break;

case 'textarea':
    if (is_array($val)) {
        $val = implode("\n", $val);
    }
    $val = String::convertCharset($val, NLS::getCharset(), 'UTF-8');
    echo 'decodeURIComponent("' . rawurlencode($val) . '")';
    break;

default:
    $val = String::convertCharset($val, NLS::getCharset(), 'UTF-8');
    echo 'decodeURIComponent("' . rawurlencode($val) . '")';
}
?>];
<?php endforeach; endfor; ?>

function newChoice()
{
    var field, val;
    var index = document.prefs.identity.selectedIndex;
    var id = document.prefs.identity.options[index].value;
    if (id < 0) {
        document.prefs.reset();
        document.prefs.identity.selectedIndex = index;
        return;
    }
    for (var i = 0; i < identities[id].length; i++) {
        field = document.prefs[identities[id][i][0]];
        if (!field) {
            continue;
        }
        val = identities[id][i][2];
        switch (identities[id][i][1]) {
        case "enum":
            for (var j = 0; j < field.options.length; j++) {
                if (field.options[j].value == val) {
                    field.selectedIndex = j;
                    break;
                }
            }
            break;

        case "checkbox":
            field.checked = val;
            break;

        case "implicit":
            eval("newChoice_" + identities[id][i][0] + "(val)");
            break;

        default:
            field.value = val;
        }
    }
}
</script>
<br />
<?php echo Horde::label('identity', _("Select the identity you want to change:")) ?><br />
<select name="identity" id="identity" onchange="javascript:newChoice()">
  <option value="-2" selected="selected"><?php echo _("None") ?></option>
  <option value="-1"><?php echo _("Create a new one") ?></option>
<?php for ($i = 0; $i < count($identities); $i++): ?>
  <option value="<?php echo $i ?>"<?php if ($i == $default_identity) echo ' selected="selected"' ?>><?php echo htmlspecialchars($identities[$i]) ?></option>
<?php endfor; ?>
</select><br />
<?php endif; ?>
