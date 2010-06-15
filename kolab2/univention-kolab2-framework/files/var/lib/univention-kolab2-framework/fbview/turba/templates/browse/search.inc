<?php
/* Build the directory sources select widget. */
$source_options = '';
$criteria_options = '';
$js_criteria = "var criteriaOptions = new Array();\n";
$source_count = 0;
foreach ($cfgSources as $key => $entry) {
    $js_criteria .= "criteriaOptions[$source_count] = new Array()\n";
    $js_criteria .= "criteriaOptions[$source_count][0] = '$key';\n";

    /* Build the criteria select widget. */
    $field_count = 1;
    foreach ($entry['search'] as $field) {
        $js_criteria .= "criteriaOptions[$source_count][$field_count] = new Array('$field', '" . $attributes[$field]['label'] . "');\n";
        if ($key == $source) {
            $criteria_options .= "<option value=\"$field\">";
            $criteria_options .= $attributes[$field]['label'] . "</option>\n";
        }
        $field_count++;
    }

    $selected = ($key == $source) ? ' selected="selected"' : '';
    $source_options .= "<option value=\"$key\"$selected>";
    $source_options .= $entry['title'] . "</option>\n";

    $source_count++;
}

if ($_SESSION['turba_search_mode'] == 'basic'): ?>
<script language="JavaScript" type="text/javascript">
<!--
<?php echo $js_criteria ?>
function updateCriterias()
{
    var f = document.directory_search;

    while (f.criteria.length > 0) {
        f.criteria.options[f.criteria.length-1] = null;
    }

    for (var i = 0; i < criteriaOptions.length; i++) {
        if (criteriaOptions[i][0] == f.source.options[f.source.selectedIndex].value) {
            for (var j = 1; j < criteriaOptions[i].length; j++) {
                f.criteria.options[f.criteria.length] = new Option(criteriaOptions[i][j][1], criteriaOptions[i][j][0]);
            }
            f.criteria.selectedIndex = 0;
            return;
        }
    }
}
//-->
</script>

<form name="directory_search" action="<?php echo Horde::applicationUrl('search.php') ?>" method="get">
<input type="hidden" name="actionID" value="1" />
<?php echo Util::formInput() ?>

<table border="0" cellpadding="1" cellspacing="0" width="100%">
<tr class="header">
  <td class="header">
      <b><?php echo _("Basic Search") ?></b>
  </td>
  <td align="right" class="header">
    <?php echo Horde::widget(Util::addParameter(Horde::applicationUrl('search.php'), 'search_mode', 'advanced'), _("Advanced Search"), 'menuitem', '', '', _("Ad_vanced Search")) ?></a>
  </td>
</tr>
</table>

<table border="0" cellpadding="0" cellspacing="5">
<tr>
    <td class="light" align="right"><b><?php echo _("Find") ?></b></td>
    <td class="item">
        <select name="criteria">
<?php echo $criteria_options ?>
        </select>
    </td>

    <td class="light" align="right"><b><?php echo _("Matching") ?></b></td>
    <td class="item">
        <input type="text" size="30" name="val" value="" />
    </td>

<?php if (count($cfgSources) > 1): ?>
    <td class="light" align="right"><b><?php echo _("From") ?></b></td>
    <td class="item">
        <select name="source" onchange="updateCriterias()">
<?php echo $source_options ?>
        </select>
    </td>
<?php else: ?>
    <td>
        <input type="hidden" name="source" value="<?php reset($cfgSources); echo key($cfgSources) ?>" />
    </td>
<?php endif; ?>

    <td>
        <input class="button" type="submit" value="<?php echo _("Search") ?>" />
    </td>
</tr>
</table>
</form>
<br/>

<?php else: ?>

<form name="directory_search" action="<?php echo Horde::applicationUrl('search.php') ?>" method="get">
<?php echo Util::formInput() ?>

<table border="0" cellpadding="1" cellspacing="0" width="100%">
<tr class="header">
  <td class="header">
    <b><?php echo _("Advanced Search") ?></b>
  </td>
  <td align="right" class="header">
    <?php echo Horde::widget(Util::addParameter(Horde::applicationUrl('search.php'), 'search_mode', 'basic'), _("Basic Search"), 'menuitem', '', '', _("Basi_c Search")) ?></a>
  </td>
</tr>
</table>

<table border="0" cellpadding="0" cellspacing="5" width="100%">
<tr>
    <td>&nbsp;</td>
    <td>
        <input type="submit" class="button" name="search" value="<?php echo _("Search") ?>" />
        <input type="reset" class="button" name="reset" value="<?php echo _("Reset") ?>" />
    </td>
</tr>

<tr><td class="light" align="right"><b><?php echo _("Directory") ?></b></td>
    <td align="left"><select name="source" onchange="directory_search.submit()">
<?php echo $source_options ?>
</select></td></tr>

<?php endif;
