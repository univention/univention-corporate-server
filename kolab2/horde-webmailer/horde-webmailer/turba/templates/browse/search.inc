<?php
/* Build the directory sources select widget. */
$source_options = '';
$criteria_options = '';
$js_criteria = "var criteriaOptions = [];\n"
    . "var shareSources = [];\n";

$source_count = 0;
foreach (Turba::getAddressBooks() as $key => $entry) {
    $js_criteria .= "criteriaOptions[$source_count] = []\n"
        . "criteriaOptions[$source_count][0] = '$key';\n";

    /* Build the criteria select widget. */
    $field_count = 1;
    foreach ($entry['search'] as $field) {
        $js_criteria .= "criteriaOptions[$source_count][$field_count] = ['$field', '" . $GLOBALS['attributes'][$field]['label'] . "'];\n";
        if ($key == $source) {
            $selected = ($criteria == $field) ? ' selected="selected"' : '';
            $criteria_options .= "<option value=\"$field\"$selected>" .
                htmlspecialchars($GLOBALS['attributes'][$field]['label']) . "</option>\n";
        }
        $field_count++;
    }

    $selected = ($key == $source) ? ' selected="selected"' : '';
    $source_options .= "<option value=\"$key\"$selected>"
        . htmlspecialchars($entry['title']) . "</option>\n";

    $unique_source = $key;
    $source_count++;

    /* Remember vbooks and sources that are using shares. */
    if ($entry['type'] != 'vbook') {
        $js_criteria .= "shareSources['$key'] = true;\n";
    } else {
        $js_criteria .= "shareSources['$key'] = false;\n";
    }
}

/* Build search mode tabs. */
require_once 'Horde/UI/Tabs.php';
require_once 'Horde/Variables.php';
$sUrl = Horde::applicationUrl('search.php');
$vars = Variables::getDefaultVariables();
$tabs = new Horde_UI_Tabs('search_mode', $vars);
$tabs->addTab(_("Basic Search"), $sUrl, 'basic');
$tabs->addTab(_("Advanced Search"), $sUrl, 'advanced');
echo $tabs->render($_SESSION['turba']['search_mode']);

?>
<div class="text" style="padding:1em">
<form name="directory_search" action="search.php" method="get" onsubmit="RedBox.loading(); return true;">
<?php echo Util::formInput() ?>
<?php if ($source_count == 1): ?>
 <input type="hidden" name="source" value="<?php echo $unique_source ?>" />
<?php endif; ?>

<?php if ($_SESSION['turba']['search_mode'] == 'basic'): ?>
<script type="text/javascript">
<?php echo $js_criteria ?>
function updateCriteria()
{
    var f = document.directory_search;
    if (!f.source.options) {
        return;
    }

    while (f.criteria.length > 0) {
        f.criteria.options[f.criteria.length - 1] = null;
    }

    var index = f.source.selectedIndex;
    if (!index) {
        index = 0;
    }

    for (var i = 0; i < criteriaOptions.length; i++) {
        if (criteriaOptions[i][0] == f.source.options[index].value) {
            for (var j = 1; j < criteriaOptions[i].length; j++) {
                f.criteria.options[f.criteria.length] = new Option(criteriaOptions[i][j][1], criteriaOptions[i][j][0]);
            }
            f.criteria.selectedIndex = 0;
            if ($('vbook-form')) {
                if (shareSources[criteriaOptions[i][0]] == true) {
                    Element.show('vbook-form');
                } else {
                    Element.hide('vbook-form');
                }
            }
            return;
        }
    }
}
Event.observe(window, 'load', updateCriteria);
</script>

<?php if ($source_count > 1): ?>
 <strong><?php echo Horde::label('source', _("From")) ?></strong>
 <select id="source" name="source" onchange="updateCriteria();">
  <?php echo $source_options ?>
 </select>
<?php endif; ?>

 <strong><?php echo Horde::label('criteria', _("Find")) ?></strong>
 <select id="criteria" name="criteria">
  <?php echo $criteria_options ?>
 </select>

 <strong><?php echo Horde::label('val', _("Matching")) ?></strong>
 <input type="text" size="30" id="val" name="val" value="<?php echo htmlspecialchars($val) ?>" />
 <input class="button" type="submit" name="search" value="<?php echo _("Search") ?>" />

<?php else: ?>

<table cellspacing="5" width="100%">
 <tr>
  <td>&nbsp;</td>
  <td>
   <input type="submit" class="button" name="search" value="<?php echo _("Search") ?>" />
   <input type="reset" class="button" name="reset" value="<?php echo _("Reset to Defaults") ?>" />
  </td>
 </tr>
 <?php if ($source_count > 1): ?>
 <tr>
  <td class="rightAlign"><strong><?php echo Horde::label('source', _("Address Book")) ?></strong></td>
  <td class="leftAlign">
   <select id="source" name="source" onchange="directory_search.submit()">
    <?php echo $source_options ?>
   </select>
  </td>
 </tr>
 <?php endif; ?>
<?php endif; ?>
