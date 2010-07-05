<?php
if ($registry->hasMethod('contacts/sources')) {
    $selected = explode("\t", $prefs->getValue('search_sources'));
    $readable = $registry->call('contacts/sources');
    $writeable = $registry->call('contacts/sources', array(true));

    $nbReadSources = count(array_keys($readable));
    $nbWriteSources = count(array_keys($writeable));

    if (count($selected) == 1 && empty($selected[0])) {
        $selected = array();
    }

    if ($nbReadSources == 1) {
        // Only one source, no need to display the selection widget
        $selected = array_keys($readable);
        $readSelect = '';
    }

    $prefSelect = '';
    foreach ($selected as $source) {
        if (!empty($readable[$source])) {
            $prefSelect .= '<option value="' . $source . '">' . $readable[$source] . "</option>\n";
        }
    }

    $readSelect = '';
    if (!is_a($readable, 'PEAR_Error') && is_array($readable)) {
        foreach (array_diff(array_keys($readable), $selected) as $source) {
            $readSelect .= '<option value="' . $source . '">' . $readable[$source] . "</option>\n";
        }
    }

    if (!is_a($writeable, 'PEAR_Error') && is_array($writeable)) {
        $writeSelect = '<option value="">' . _("None") . '</option>' . "\n";
        $writeSource = '';
        foreach ($writeable as $source => $name) {
            $sel = $prefs->getValue('add_source') == $source ? ' selected="selected"' : '';
            $writeSelect .= '<option value="' . $source . '"' . "$sel>" . $name . "</option>\n";
            $writeSource = $source;
        }
    }

    $selected_fields = array();
    $search_field_pref = $prefs->getValue('search_fields');
    if (!empty($search_field_pref)) {
        $selected_fields = explode("\n", $prefs->getValue('search_fields'));
        foreach ($selected_fields as $field) {
            $field = trim($field);
            if (!empty($field)) {
                $tmp = explode("\t", $field);
                if (count($tmp) > 1) {
                    $source = array_splice($tmp, 0, 1);
                    $selected_fields[$source[0]] = $tmp;
                }
            }
        }
    }

    $search_fields = array();
    if (!is_a($readable, 'PEAR_Error') && is_array($readable)) {
        foreach (array_keys($readable) as $source) {
            $search_fields[$source] = $registry->call('contacts/fields', array($source));
        }
    }

    $js = "var searchFields = [];\n";
    $source_count = 0;
    foreach ($search_fields as $source => $fields) {
        $js .= "searchFields[$source_count] = [];\n";
        $js .= "searchFields[$source_count][0] = '$source';\n";

        $field_count = 1;
        foreach ($fields as $field) {
            if ($field['search']) {
                $marked = isset($selected_fields[$source]) && in_array($field['name'], $selected_fields[$source]) ? 'true' : 'false';
                $js .= "searchFields[$source_count][$field_count] = ['" . $field['name'] . "', '" . $field['label'] . "', $marked];\n";
                $field_count++;
            }
        }

        $source_count++;
    }
}
?>

<?php if (!$prefs->isLocked('search_sources') && (!empty($readSelect) || !empty($prefSelect))): ?>
<script type="text/javascript">

function deselectHeaders()
{
    document.prefs.unselected_search_sources[0].selected = false;
    document.prefs.selected_search_sources[0].selected = false;
}

function resetHidden()
{
    var tmp = '';
    for (i = 1; i < document.prefs.selected_search_sources.length; i++) {
        tmp += document.prefs.selected_search_sources[i].value;
        if (i < document.prefs.selected_search_sources.length - 1)
            tmp += "\t";
    }

    document.prefs.search_sources.value = tmp;
}

function addSource()
{
    for (i = 1; i < document.prefs.unselected_search_sources.length; i++) {
        if (document.prefs.unselected_search_sources[i].selected) {
            document.prefs.selected_search_sources[document.prefs.selected_search_sources.length] = new Option(document.prefs.unselected_search_sources[i].text, document.prefs.unselected_search_sources[i].value);
            document.prefs.unselected_search_sources[i] = null;
            i--;
        }
    }

    resetHidden();
}

function removeSource()
{
    for (i = 1; i < document.prefs.selected_search_sources.length; i++) {
        if (document.prefs.selected_search_sources[i].selected) {
            document.prefs.unselected_search_sources[document.prefs.unselected_search_sources.length] = new Option(document.prefs.selected_search_sources[i].text, document.prefs.selected_search_sources[i].value)
            document.prefs.selected_search_sources[i] = null;
            i--;
        }
    }

    resetHidden();
}

function moveSourceUp()
{
    var sel = document.prefs.selected_search_sources.selectedIndex;

    if (sel == -1 || document.prefs.selected_search_sources.length <= 2) return;

    // deselect everything but the first selected item
    document.prefs.selected_search_sources.selectedIndex = sel;

    if (sel == 1) {
        tmp = document.prefs.selected_search_sources[sel];
        document.prefs.selected_search_sources[sel] = null;
        document.prefs.selected_search_sources[document.prefs.selected_search_sources.length] = tmp;
        document.prefs.selected_search_sources.selectedIndex = document.prefs.selected_search_sources.length - 1;
    } else {
        tmp = [];
        for (i = 1; i < document.prefs.selected_search_sources.length; i++) {
            tmp[i - 1] = new Option(document.prefs.selected_search_sources[i].text, document.prefs.selected_search_sources[i].value)
        }

        for (i = 0; i < tmp.length; i++) {
            if (i + 1 == sel - 1) {
                document.prefs.selected_search_sources[i + 1] = tmp[i + 1];
            } else if (i + 1 == sel) {
                document.prefs.selected_search_sources[i + 1] = tmp[i - 1];
            } else {
                document.prefs.selected_search_sources[i + 1] = tmp[i];
            }
        }

        document.prefs.selected_search_sources.selectedIndex = sel - 1;
    }

    resetHidden();
}

function moveSourceDown()
{
    var sel = document.prefs.selected_search_sources.selectedIndex;

    if (sel == -1 || document.prefs.selected_search_sources.length <= 2) return;

    // deselect everything but the first selected item
    document.prefs.selected_search_sources.selectedIndex = sel;

    if (sel == document.prefs.selected_search_sources.length - 1) {
        tmp = [];
        for (i = 1; i < document.prefs.selected_search_sources.length; i++) {
            tmp[i - 1] = new Option(document.prefs.selected_search_sources[i].text, document.prefs.selected_search_sources[i].value)
        }

        document.prefs.selected_search_sources[1] = tmp[tmp.length - 1];
        for (i = 0; i < tmp.length - 1; i++) {
            document.prefs.selected_search_sources[i + 2] = tmp[i];
        }

        document.prefs.selected_search_sources.selectedIndex = 1;
    } else {
        tmp = [];
        for (i = 1; i < document.prefs.selected_search_sources.length; i++) {
            tmp[i - 1] = new Option(document.prefs.selected_search_sources[i].text, document.prefs.selected_search_sources[i].value)
        }

        for (i = 0; i < tmp.length; i++) {
            if (i + 1 == sel) {
                document.prefs.selected_search_sources[i + 1] = tmp[i + 1];
            } else if (i + 1 == sel + 1) {
                document.prefs.selected_search_sources[i + 1] = tmp[i - 1];
            } else {
                document.prefs.selected_search_sources[i + 1] = tmp[i];
            }
        }

        document.prefs.selected_search_sources.selectedIndex = sel + 1;
    }

    resetHidden();
}

<?php echo $js ?>

var selectedIndex = false;
var selectedValue = false;
var nbSources = <?php echo $nbReadSources ?>;
<?php if ($nbReadSources == 1): ?>
selectedIndex = 1;
selectedValue = "<?php echo $selected[0] ?>";
<?php endif; ?>

function updateSearchFields()
{
    var f = document.prefs;
    <?php if ($nbReadSources > 1): ?>
    selectedIndex = f.selected_search_sources.selectedIndex;
    <?php endif; ?>
    var fieldString = '';

    while (f.search_fields.length > 0) {
        f.search_fields.options[f.search_fields.length-1] = null;
    }

    if (selectedIndex < 1) {
        return;
    }

    <?php if ($nbReadSources > 1): ?>
    selectedValue = f.selected_search_sources.options[selectedIndex].value;
    <?php endif; ?>

    for (var i = 0; i < searchFields.length; i++) {
        if (i > 0) {
            fieldString += "\n";
        }
        fieldString += searchFields[i][0];
        for (var j = 1; j < searchFields[i].length; j++) {
            if (searchFields[i][j][2]) {
                fieldString += "\t" + searchFields[i][j][0];
            }

            if (searchFields[i][0] == selectedValue) {
                f.search_fields.options[f.search_fields.length] = new Option(searchFields[i][j][1], searchFields[i][j][0]);
                if (searchFields[i][j][2]) {
                    f.search_fields.options[f.search_fields.length - 1].selected = true;
                }
            }
        }
    }

    f.search_fields_string.value = fieldString;
}

function changeSearchFields()
{
    var f = document.prefs;
    <?php if ($nbReadSources > 1): ?>
    selectedIndex = f.selected_search_sources.selectedIndex;
    selectedValue = f.selected_search_sources.options[selectedIndex].value;
    <?php endif; ?>

    for (var i = 0; i < searchFields.length; i++) {
        if (searchFields[i][0] == selectedValue) {
            for (var j = 1; j < searchFields[i].length; j++) {
                searchFields[i][j][2] = f.search_fields.options[j - 1].selected;
            }
            updateSearchFields();
            return;
        }
    }
}

</script>

<br />
<input type="hidden" name="search_sources" value="<?php echo implode("\t", $selected) ?>" />
<?php if ($nbReadSources > 1): ?>
<?php echo _("Choose the order of address books to search when expanding addresses.") ?><br />
<table>
 <tr>
  <td>
   <label for="unselected_search_sources" class="hidden"><?php echo _("Available Address books:") ?></label>
   <select id="unselected_search_sources" name="unselected_search_sources" multiple="multiple" size="5" style="width:20em" onchange="deselectHeaders()">
    <option value=""><?php echo _("Available Address books:") ?></option>
    <?php echo $readSelect ?>
   </select>
  </td>
  <td>
   <a href="#" onclick="addSource(); return false;"><?php echo Horde::img(isset($GLOBALS['nls']['rtl'][$GLOBALS['language']]) ? 'lhand.png' : 'rhand.png', _("Add source"), null, $registry->getImageDir('horde')) ?></a>
   <br />
   <a href="#" onclick="removeSource(); return false;"><?php echo Horde::img(isset($GLOBALS['nls']['rtl'][$GLOBALS['language']]) ? 'rhand.png' : 'lhand.png', _("Remove source"), null, $registry->getImageDir('horde')) ?></a>
  </td>
  <td>
   <label for="selected_search_sources" class="hidden"><?php echo _("Selected Address books:") ?></label>
   <select name="selected_search_sources" multiple="multiple" size="5" style="width:20em" onchange="deselectHeaders();updateSearchFields();">
    <option value=""><?php echo _("Selected Address books:") ?></option>
    <?php echo $prefSelect ?>
   </select>
  </td>
  <td>
   <a href="#" onclick="moveSourceUp(); return false;"><?php echo Horde::img('nav/up.png', _("Move up"), null, $registry->getImageDir('horde')) ?></a>
   <br />
   <a href="#" onclick="moveSourceDown(); return false;"><?php echo Horde::img('nav/down.png', _("Move down"), null, $registry->getImageDir('horde')) ?></a>
  </td>
 </tr>
</table>

<?php echo _("Click on one of your selected address books and then select all fields to search.") ?><br />
<?php else: ?>
<?php echo _("Select all fields to search when expanding addresses.") ?><br />
<?php endif; ?>

<?php echo _("To select multiple fields, hold down the Control (PC) or Command (Mac) while clicking.") ?><br />
<input type="hidden" name="search_fields_string" />
<table>
 <tr>
  <td>
   <label for="search_fields" class="hidden"><?php echo _("Fields to search") ?></label>
   <select id="search_fields" name="search_fields" multiple="multiple" size="5" style="width:20em" onchange="changeSearchFields()">
    <option><?php echo str_repeat('&nbsp;', 50) ?></option>
   </select>
  </td>
 </tr>
</table>

<script type="text/javascript">
updateSearchFields();
</script>
<?php endif; ?>

<?php if (!$prefs->isLocked('add_source') && !empty($writeSelect)): ?>
 <?php echo _("Choose the address book to use when adding addresses.") ?><br />
 <br />
 <label for="add_source" class="hidden"><?php echo _("Address book to add addresses to") ?></label>
 <select id="add_source" name="add_source"><?php echo $writeSelect ?></select>
<?php endif; ?>
