<?php

$order = Turba::getAddressBookOrder();
$js = "var addressbooks = [];\n";
$source_count = 0;
foreach ($GLOBALS['cfgSources'] as $source => $info) {
    $selected = isset($order[$source]) ? 'true' : 'false';
    $js .= "addressbooks[$source_count] = ['" . addslashes($source) . "', decodeURIComponent('" . rawurlencode($info['title']) . "'), $selected, " . (isset($order[$source]) ? (int)$order[$source] : 'null') . "];\n";
    $source_count++;
}

if (!$prefs->isLocked('addressbooks') && $source_count):
?>

<script type="text/javascript">
<!--
<?php echo $js ?>

function selectAddressBooks()
{
    var selected = [];
    var unselected = [];
    for (var i = 0; i < addressbooks.length; i++) {
        if (addressbooks[i][2]) {
            selected[addressbooks[i][3]] = [addressbooks[i][1], addressbooks[i][0]];
        } else {
            unselected[unselected.length] = [addressbooks[i][1], addressbooks[i][0]];
        }
    }
    for (i = 0; i < selected.length; i++) {
        f.selected_addressbooks.options[i + 1] = new Option(selected[i][0], selected[i][1]);
    }
    for (i = 0; i < unselected.length; i++) {
        f.unselected_addressbooks.options[i + 1] = new Option(unselected[i][0], unselected[i][1]);
    }
}

function deselectHeaders()
{
    document.prefs.unselected_addressbooks[0].selected = false;
    document.prefs.selected_addressbooks[0].selected = false;
}

function resetHidden()
{
    var tmp = '';
    for (var i = 1; i < f.selected_addressbooks.length; i++) {
        if (tmp != '') {
            tmp += '\n';
        }
        tmp += f.selected_addressbooks[i].value;
    }
    document.prefs.addressbooks.value = tmp;
}

function addAddressBook()
{
    for (i = 1; i < f.unselected_addressbooks.length; i++) {
        if (f.unselected_addressbooks[i].selected) {
            f.selected_addressbooks[f.selected_addressbooks.length] = new Option(f.unselected_addressbooks[i].text, f.unselected_addressbooks[i].value);
            f.unselected_addressbooks[i] = null;
            i--;
        }
    }

    resetHidden();
}

function removeAddressBook()
{
    for (i = 1; i < f.selected_addressbooks.length; i++) {
        if (f.selected_addressbooks[i].selected) {
            f.unselected_addressbooks[f.unselected_addressbooks.length] = new Option(f.selected_addressbooks[i].text, f.selected_addressbooks[i].value)
            f.selected_addressbooks[i] = null;
            i--;
        }
    }

    resetHidden();
}

function moveAddressBookUp()
{
    var sel = f.selected_addressbooks.selectedIndex;

    if (sel <= 1 || f.selected_addressbooks.length <= 2) return;

    // deselect everything but the first selected item
    f.selected_addressbooks.selectedIndex = sel;
    var up = f.selected_addressbooks[sel].value;

    tmp = [];
    for (i = 1; i < f.selected_addressbooks.length; i++) {
        tmp[i - 1] = new Option(f.selected_addressbooks[i].text, f.selected_addressbooks[i].value)
    }

    for (i = 0; i < tmp.length; i++) {
        if (i + 1 == sel - 1) {
            f.selected_addressbooks[i + 1] = tmp[i + 1];
        } else if (i + 1 == sel) {
            f.selected_addressbooks[i + 1] = tmp[i - 1];
        } else {
            f.selected_addressbooks[i + 1] = tmp[i];
        }
    }

    f.selected_addressbooks.selectedIndex = sel - 1;

    for (i = 2; i < addressbooks.length - 1; i++) {
        if (addressbooks[i][0] == up) {
            addressbook = addressbooks[i];
            addressbooks[i] = addressbooks[i - 1];
            addressbooks[i - 1] = addressbook;
        }
    }

    resetHidden();
}

function moveAddressBookDown()
{
    var sel = f.selected_addressbooks.selectedIndex;

    if (sel == -1 || f.selected_addressbooks.length <= 2 || sel == f.selected_addressbooks.length - 1) return;

    // deselect everything but the first selected item
    f.selected_addressbooks.selectedIndex = sel;
    var down = f.selected_addressbooks[sel].value;

    tmp = [];
    for (i = 1; i < f.selected_addressbooks.length; i++) {
        tmp[i - 1] = new Option(f.selected_addressbooks[i].text, f.selected_addressbooks[i].value)
    }

    for (i = 0; i < tmp.length; i++) {
        if (i + 1 == sel) {
            f.selected_addressbooks[i + 1] = tmp[i + 1];
        } else if (i + 1 == sel + 1) {
            f.selected_addressbooks[i + 1] = tmp[i - 1];
        } else {
            f.selected_addressbooks[i + 1] = tmp[i];
        }
    }

    f.selected_addressbooks.selectedIndex = sel + 1;

    for (i = addressbooks.length - 2; i > 0; i--) {
        if (addressbooks[i][0] == down || addressbooks[i + 1][0] == down) {
            addressbook = addressbooks[i];
            addressbooks[i] = addressbooks[i + 1];
            addressbooks[i + 1] = addressbook;
        }
    }

    resetHidden();
}

// -->
</script>

<input type="hidden" name="addressbooks" value="<?php echo htmlspecialchars($prefs->getValue('addressbooks')) ?>" />

<?php echo _("Choose which address books to display, and in what order:") ?><br />
<table>
 <tr>
  <td>
   <label for="unselected_addressbooks" class="hidden"><?php echo _("Address books that will not be displayed:") ?></label>
   <select id="unselected_addressbooks" name="unselected_addressbooks" multiple="multiple" size="5" style="width:300px" onchange="deselectHeaders();">
    <option class="control" value=""><?php echo _("Address books that will not be displayed:") ?></option>
   </select>
  </td>
  <td>
   <a href="#" onclick="addAddressBook(); return false;"><?php echo Horde::img(isset($GLOBALS['nls']['rtl'][$GLOBALS['language']]) ? 'lhand.png' : 'rhand.png', _("Add address book"), null, $registry->getImageDir('horde')) ?></a>
   <br />
   <a href="#" onclick="removeAddressBook(); return false;"><?php echo Horde::img(isset($GLOBALS['nls']['rtl'][$GLOBALS['language']]) ? 'rhand.png' : 'lhand.png', _("Remove address book"), null, $registry->getImageDir('horde')) ?></a>
  </td>
  <td>
   <label for="selected_addressbooks" class="hidden"><?php echo _("These address books will display in this order:") ?></label>
   <select id="selected_addressbooks" name="selected_addressbooks" multiple="multiple" size="5" style="width:300px" onchange="deselectHeaders();">
    <option class="control" value=""><?php echo _("These address books will display in this order:") ?></option>
   </select>
  </td>
  <td>
   <a href="#" onclick="moveAddressBookUp(); return false;"><?php echo Horde::img('nav/up.png', _("Move left"), null, $registry->getImageDir('horde')) ?></a>
   <br />
   <a href="#" onclick="moveAddressBookDown(); return false;"><?php echo Horde::img('nav/down.png', _("Move right"), null, $registry->getImageDir('horde')) ?></a>
  </td>
 </tr>
</table>
<script type="text/javascript">
<!--
var f = document.prefs;
selectAddressBooks();
// -->
</script>

<?php endif; // End if not locked && address books exist.
