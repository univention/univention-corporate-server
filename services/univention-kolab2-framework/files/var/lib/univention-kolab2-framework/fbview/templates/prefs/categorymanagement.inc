<script language="JavaScript" type="text/javascript">
<!--
function remove(category)
{
    document.prefs.cAction.value = 'remove';
    document.prefs.category.value = category;
    document.prefs.submit();
}

function add()
{
    var category = window.prompt('<?php echo addslashes(_("Please enter a name for the new category:")) ?>', '');
    if (category != null && category != '') {
        document.prefs.cAction.value = 'add';
        document.prefs.category.value = category;
        document.prefs.submit();
    }
}
//-->
</script>
<input name="cAction" value="" type="hidden" />
<input name="category" value="" type="hidden" />
<table border="0">

<tr>
  <td colspan="2">
    <input type="button" class="button" value="<?php echo _("New Category") ?>" onclick="add();" />
  </td>
</tr>

<?php

require_once 'Horde/Prefs/CategoryManager.php';
$cManager = &new Prefs_CategoryManager();
$categories = $cManager->get();
$colors = $cManager->colors();
$url = Horde::url($registry->getParam('webroot', 'horde') . '/services/images/colorpicker.php');
$url = Util::addParameter($url, 'form', 'prefs');

// Default Color
$color = isset($colors['_default_']) ? $colors['_default_'] : '#FFFFFF';
$c_url = Util::addParameter($url, 'target', 'color_' . base64_encode('_default_'));
?>
<tr>
  <td style="background-color:<?php echo $color ?>"><b><?php echo _("Default Color") ?></b></td>
  <td>
    <?php if (!$prefs->isLocked('category_colors')): ?>
      <input class="fixed" size="7" style="background-color:<?php echo $color ?>" name="color_<?php echo base64_encode('_default_') ?>" value="<?php echo $color ?>" />
      <a href="<?php echo $c_url ?>" onclick="window.open('<?php echo $c_url ?>', 'colorpicker', 'toolbar=no,location=no,status=no,scrollbars=no,resizable=no,width=120,height=250,left=100,top=100'); return false;" onmouseout="window.status='';" onmouseover="window.status='<?php echo _('Color Picker') ?>'; return true;" class="widget" target="colorpicker">
      <?php echo Horde::img('colorpicker.gif', _('Color Picker'), 'height="16"', $registry->getParam('graphics', 'horde')) ?></a>
    <?php endif; ?>
  </td>
</tr>

<?php
// Unfiled Color
$color = isset($colors['_unfiled_']) ? $colors['_unfiled_'] : '#FFFFFF';
$c_url = Util::addParameter($url, 'target', 'color_' . base64_encode('_unfiled_'));
?>
<tr>
  <td style="background-color:<?php echo $color ?>"><b><?php echo _("Unfiled") ?></b></td>
  <td>
    <?php if (!$prefs->isLocked('category_colors')): ?>
      <input class="fixed" size="7" style="background-color:<?php echo $color ?>" name="color_<?php echo base64_encode('_unfiled_') ?>" value="<?php echo $color ?>" />
      <a href="<?php echo $c_url ?>" onclick="window.open('<?php echo $c_url ?>', 'colorpicker', 'toolbar=no,location=no,status=no,scrollbars=no,resizable=no,width=120,height=250,left=100,top=100'); return false;" onmouseout="window.status='';" onmouseover="window.status='<?php echo _('Color Picker') ?>'; return true;" class="widget" target="colorpicker">
      <?php echo Horde::img('colorpicker.gif', _('Color Picker'), 'height="16"', $registry->getParam('graphics', 'horde')) ?></a>
    <?php endif; ?>
  </td>
</tr>

<?php
foreach ($categories as $name):
    $color = isset($colors[$name]) ? $colors[$name] : '#FFFFFF';
    $c_url = Util::addParameter($url, 'target', 'color_' . base64_encode($name));
?>
<tr>
  <td style="background-color:<?php echo $color ?>"><b><?php echo ($name == '_default_' ? _("Default Color") : $name) ?></b></td>
  <td>
    <?php if (!$prefs->isLocked('category_colors')): ?>
      <input class="fixed" size="7" style="background-color:<?php echo $color ?>" name="color_<?php echo base64_encode($name) ?>" value="<?php echo $color ?>" />
      <a href="<?php echo $c_url ?>" onclick="window.open('<?php echo $c_url ?>', 'colorpicker', 'toolbar=no,location=no,status=no,scrollbars=no,resizable=no,width=120,height=250,left=100,top=100'); return false;" onmouseout="window.status='';" onmouseover="window.status='<?php echo _('Color Picker') ?>'; return true;" class="widget" target="colorpicker">
      <?php echo Horde::img('colorpicker.gif', _('Color Picker'), 'height="16"', $registry->getParam('graphics', 'horde')) ?></a>
    <?php endif; ?>
    <a href="" onclick="remove('<?php echo htmlspecialchars($name) ?>'); return false;"><?php echo Horde::img('delete.gif') ?></a>
  </td>
</tr>
<?php endforeach; ?>

</table>
