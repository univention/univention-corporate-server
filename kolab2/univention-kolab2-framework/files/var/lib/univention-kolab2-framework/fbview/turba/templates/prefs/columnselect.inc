<?php if (!$prefs->isLocked('columns')):

require TURBA_BASE . '/config/sources.php';
require TURBA_BASE . '/config/attributes.php';

$sources = Turba::string2Columns($prefs->getValue('columns'));

$js = "var columns = new Array();\n";
$source_count = 0;
foreach ($cfgSources as $source => $info) {
    $selected = isset($sources[$source]) ? array_flip($sources[$source]) : array();
    $js .= "columns[$source_count] = new Array();\n";
    $js .= "columns[$source_count][0] = '$source';\n";

    $column_count = 1;
    foreach ($info['map'] as $column => $null) {
        if (substr($column, 0, 2) == '__' || $column == 'name') {
            continue;
        }
        $marked = isset($selected[$column]) ? 'true' : 'false';
        $js .= "columns[$source_count][$column_count] = ['$column', '" . addslashes($attributes[$column]['label']) . "', $marked, " . (($marked === 'true') ? $selected[$column] : 'null') . "];\n";
        $column_count++;
    }

    $source_count++;
}
?>

<script language="JavaScript1.1" type="text/javascript">
<!--
<?php echo $js ?>

function selectSource()
{
    var f = document.prefs;
    var fieldString = '';

    while (f.unselected_columns.length > 1) {
        f.unselected_columns.options[f.unselected_columns.length - 1] = null;
    }
    while (f.selected_columns.length > 1) {
        f.selected_columns.options[f.selected_columns.length - 1] = null;
    }

    if (f.source.selectedIndex < 1) {
        return;
    }
    var source = f.source.selectedIndex - 1;

    var selected = new Array();
    var unselected = new Array();
    for (var i = 1; i < columns[source].length; i++) {
        if (columns[source][i][2]) {
            selected[columns[source][i][3]] = new Array(columns[source][i][1], columns[source][i][0]);
        } else {
            unselected[unselected.length] = new Array(columns[source][i][1], columns[source][i][0]);
        }
    }
    for (i = 0; i < selected.length; i++) {
        f.selected_columns.options[i + 1] = new Option(selected[i][0], selected[i][1]);
    }
    for (i = 0; i < unselected.length; i++) {
        f.unselected_columns.options[i + 1] = new Option(unselected[i][0], unselected[i][1]);
    }
}

function deselectHeaders()
{
    document.prefs.unselected_columns[0].selected = false;
    document.prefs.selected_columns[0].selected = false;
}

function resetHidden()
{
    var tmp = '';
    for (var i = 0; i < columns.length; i++) {
        if (i > 0) {
            tmp += '\n';
        }
        tmp += columns[i][0];
        for (var j = 1; j < columns[i].length; j++) {
            if (columns[i][j][2]) {
                tmp += '\t' + columns[i][j][0];
            }
        }
    }
    document.prefs.columns.value = tmp;
}

function addColumn()
{
    var f = document.prefs;
    var source = f.source.selectedIndex - 1;

    for (i = 1; i < f.unselected_columns.length; i++) {
        if (f.unselected_columns[i].selected) {
            for (var j = 1; j < columns[source].length; j++) {
                if (columns[source][j][0] == f.unselected_columns[i].value) {
                    columns[source][j][2] = true;
                }
            }
            f.selected_columns[f.selected_columns.length] = new Option(f.unselected_columns[i].text, f.unselected_columns[i].value);
            f.unselected_columns[i] = null;
            i--;
        }
    }

    resetHidden();
}

function removeColumn()
{
    var f = document.prefs;
    var source = f.source.selectedIndex - 1;

    for (i = 1; i < f.selected_columns.length; i++) {
        if (f.selected_columns[i].selected) {
            for (var j = 1; j < columns[source].length; j++) {
                if (columns[source][j][0] == f.selected_columns[i].value) {
                    columns[source][j][2] = false;
                }
            }
            f.unselected_columns[f.unselected_columns.length] = new Option(f.selected_columns[i].text, f.selected_columns[i].value)
            f.selected_columns[i] = null;
            i--;
        }
    }

    resetHidden();
}

function moveColumnUp()
{
    var f = document.prefs;
    var sel = f.selected_columns.selectedIndex;
    var source = f.source.selectedIndex - 1;

    if (sel <= 1 || f.selected_columns.length <= 2) return;

    // deselect everything but the first selected item
    f.selected_columns.selectedIndex = sel;
    var up = f.selected_columns[sel].value;

    tmp = new Array();

    for (i = 1; i < f.selected_columns.length; i++) {
        tmp[i - 1] = new Option(f.selected_columns[i].text, f.selected_columns[i].value)
    }

    for (i = 0; i < tmp.length; i++) {
        if (i + 1 == sel - 1) {
            f.selected_columns[i + 1] = tmp[i + 1];
        } else if (i + 1 == sel) {
            f.selected_columns[i + 1] = tmp[i - 1];
        } else {
            f.selected_columns[i + 1] = tmp[i];
        }
    }

    f.selected_columns.selectedIndex = sel - 1;

    for (i = 2; i < columns[source].length - 1; i++) {
        if (columns[source][i][0] == up) {
            column = columns[source][i];
            columns[source][i] = columns[source][i - 1];
            columns[source][i - 1] = column;
        }
    }

    resetHidden();
}

function moveColumnDown()
{
    var f = document.prefs;
    var sel = f.selected_columns.selectedIndex;
    var source = f.source.selectedIndex - 1;

    if (sel == -1 || f.selected_columns.length <= 2 || sel == f.selected_columns.length - 1) return;

    // deselect everything but the first selected item
    f.selected_columns.selectedIndex = sel;
    var down = f.selected_columns[sel].value;

    tmp = new Array();

    for (i = 1; i < f.selected_columns.length; i++) {
        tmp[i - 1] = new Option(f.selected_columns[i].text, f.selected_columns[i].value)
    }

    for (i = 0; i < tmp.length; i++) {
        if (i + 1 == sel) {
            f.selected_columns[i + 1] = tmp[i + 1];
        } else if (i + 1 == sel + 1) {
            f.selected_columns[i + 1] = tmp[i - 1];
        } else {
            f.selected_columns[i + 1] = tmp[i];
        }
    }

    f.selected_columns.selectedIndex = sel + 1;

    for (i = columns[source].length - 2; i > 0; i--) {
        if (columns[source][i][0] == down || columns[source][i + 1][0] == down) {
            column = columns[source][i];
            columns[source][i] = columns[source][i + 1];
            columns[source][i + 1] = column;
        }
    }

    resetHidden();
}
// -->
</script>

<table>
    <tr>
        <td>
            <select name="source" onchange="if (document.prefs.source.selectedIndex != 0) selectSource();">
                <option value=""><?php echo _("Please select a directory:") ?></option>
<?php foreach ($cfgSources as $key => $info): ?>
                <option value="<?php echo $key ?>"><?php echo $info['title'] ?></option>
<?php endforeach; ?>
            </select>
        </td>
    </tr>
</table>

<?php echo _("Choose the order of the columns to display in the address list.") ?><br />
<input type="hidden" name="columns" value="<?php echo $prefs->getValue('columns') ?>" />
<table>
    <tr>
        <td>
            <select name="unselected_columns" multiple="multiple" size="5" width="20" onchange="deselectHeaders();">
                <option value=""><?php echo _("Available Columns:") ?></option>
            </select>
        </td>
        <td>
            <a href="" onclick="addColumn(); return false;"><?php echo Horde::img('rhand.gif', _("Add column"), null, $registry->getParam('graphics', 'horde')) ?></a>
            <br />
            <a href="" onclick="removeColumn(); return false;"><?php echo Horde::img('lhand.gif', _("Remove column"), null, $registry->getParam('graphics', 'horde')) ?></a>
        </td>
        <td>
            <select name="selected_columns" multiple="multiple" size="5" width="20" onchange="deselectHeaders();">
                <option value=""><?php echo _("Selected Columns:") ?></option>
            </select>
        </td>
        <td>
            <a href="" onclick="moveColumnUp(); return false;"><?php echo Horde::img('nav/up.gif', _("Move left"), null, $registry->getParam('graphics', 'horde')) ?></a>
            <br />
            <a href="" onclick="moveColumnDown(); return false;"><?php echo Horde::img('nav/down.gif', _("Move right"), null, $registry->getParam('graphics', 'horde')) ?></a>
        </td>
    </tr>
</table>
<?php endif; ?>
