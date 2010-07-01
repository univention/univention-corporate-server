<form method="post" name="eventform" action="search.php">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="search_calendar" />
<input type="hidden" name="search_mode" value="basic" />

<?php
/* build search mode tabs. */
require_once 'Horde/UI/Tabs.php';
require_once 'Horde/Variables.php';
$sUrl = Horde::applicationUrl('search.php');
$vars = Variables::getDefaultVariables();
$tabs = new Horde_UI_Tabs('search_mode', $vars);
$tabs->addTab(_("Basic Search"), $sUrl, 'basic');
$tabs->addTab(_("Advanced Search"), $sUrl, 'advanced');
echo $tabs->render('basic');
?>

<table cellspacing="0" class="striped">
<!-- search pattern -->
<tr>
  <td class="rightAlign">
    <strong><?php echo Horde::label('pattern_title', _("Title")) ?></strong>
  </td>
  <td>
    <input name="pattern_title" id="pattern_title" type="text" value="<?php echo htmlspecialchars(Util::getFormData('pattern_title')) ?>" size="50" maxlength="100" />
  </td>
</tr>
<tr>
  <td class="rightAlign">
    <strong><?php echo Horde::label('pattern_desc', _("Descri_ption")) ?></strong>
  </td>
  <td>
    <input name="pattern_desc" id="pattern_desc" type="text" value="<?php echo htmlspecialchars(Util::getFormData('pattern_desc')) ?>" size="50" maxlength="100" />
  </td>
</tr>
<!-- range -->
<tr>
  <td class="rightAlign">
    <strong><?php echo Horde::label('range', _("Time Sp_an")) ?></strong>
  </td>
  <td>
    <select id="range" name="range">
<?php
function range_option_string($thisrange, $descr)
{
    echo '<option ';
    if (Util::getFormData('range') == $thisrange) {
        echo "value=\"$thisrange\" selected=\"selected\"";
    } else {
        echo "value=\"$thisrange\"";
    }
    echo '>' . $descr . '</option>';
}

range_option_string('-', _("All Past"));
range_option_string('-604800', _("Last week"));
range_option_string('-86400', _("Last 24 hours"));
range_option_string('0', _("Now"));
range_option_string('86400', _("Next 24 hours"));
range_option_string('604800', _("Next week"));
range_option_string('+', _("All Future"));
?>
    </select>
  </td>
</tr>
</table>

<br />
<input type="submit" class="button" value="<?php echo _("Search") ?>" />
</form>
