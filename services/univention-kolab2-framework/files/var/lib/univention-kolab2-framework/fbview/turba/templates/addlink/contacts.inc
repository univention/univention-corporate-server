<script language="JavaScript" type="text/javascript">
<!--

var display = "<?php echo (!empty($display) ? $display : 'name') ?>";

function changeDisplay()
{
    var listDisplay = window.document.contacts.display;

    if (listDisplay.options[listDisplay.selectedIndex].value != display) {
        display = listDisplay.options[listDisplay.selectedIndex].value;

        s = window.document.contacts.search_results;
        for(var i = 0; i < s.length; i++) {
            var temp = s.options[i].value;
            if (temp == "") { continue; }

            s.options[i].value = escape(s.options[i].text);
            s.options[i].text = unescape(temp);
        }

        d = window.document.contacts.selected_addresses;
        for(var i = 0; i < d.length; i++) {
            var temp = d.options[i].value;
            if (temp == "") { continue; }

            d.options[i].value = escape(d.options[i].text);
            d.options[i].text = unescape(temp);
        }
    }
}

function selectContact()
{
    if (validate()) {
        document.addlink.submit();
    }
}

function validate()
{
    var list = window.document.contacts.search_results;
    if (list.selectedIndex < 0) {
        alert('<?php echo addslashes(_("You must select an address first.")) ?>');
        return false;
    }
    var to_parameters = window.document.addlink.to_parameters;
    to_parameters.value = list.options[list.selectedIndex].value;   

    return true;
}

//-->
</script>

<table border="0" align="center" cellpadding="0" cellspacing="1">
<tr height="25">
  <td class="header">
    <b><?php echo _("Contact List") ?></b>
  </td>
</tr>

<tr>
  <td>
<form name="contacts"><?php echo Help::javascript() ?>
<input type="hidden" name="from_application" value="<?php echo $from_application ?>" />
<input type="hidden" name="from_parameters" value='<?php echo serialize($from_parameters) ?>' />
<input type="hidden" name="link_type" value="<?php echo $link_type ?>" />
<input type="hidden" name="to_application" value="<?php echo $to_application ?>" />
<input type="hidden" name="to_parameters" value="" />
<input type="hidden" name="url" value="<?php echo $return_url ?>" />
<input type="hidden" name="actionID" value="" />
<?php echo Util::formInput() ?>

<table border="0" width="100%" cellpadding="0">
<tr>
  <td class="light" align="left" nowrap="nowrap"><b><?php echo _("Find") ?></b>
    <input value="<?php echo $search ?>" name="search" tabindex="<?php echo $tabindex++ ?>" style="width:150px"></td>
<?php if (count($source_list) > 1): ?>
    <td class="light" align="left" nowrap="nowrap"><b><?php echo _("from") ?></b>
    <select name="source" tabindex="<?php echo $tabindex++ ?>">
    <?php foreach ($source_list as $key => $select): ?>
    <option value="<?php echo $key ?>"<?php if ($key == $source) echo ' selected="selected"' ?>><?php echo htmlspecialchars($select) ?></option>
    <?php endforeach; ?>
    </select></td>
<?php else: ?>
    <td class="light"><input name="source" type="hidden" value="<?php echo key($source_list) ?>" /></td>
<?php endif; ?>
    <td class="light" align="left" nowrap="nowrap"><input type="submit" class="button" value="<?php echo _("Search") ?>" />
  </td>
</tr>
</table>

<tr>
  <td>
<?php echo _("Please select contact") ?>
<table border="0" width="100%" cellpadding="0">
<tr>
  <td width="45%"><select name="search_results" size="10" width="200" ondblclick="selectContact()">
    <?php foreach ($addresses as $addr):  
        $v = serialize(array('source' => $addr['source'], 
                             'to_key' => 'id', 
                             'to_value' => $addr['id'])); ?>
        <option value='<?php echo $v ?>'><?php echo $addr['name'] ?></option>
    <?php endforeach; ?>
    </select>
  </td>
</tr>
</table>
</form>
  </td>
</tr>

<!-- Buttons Row -->
<tr>
  <td align="right">
  <form name="addlink">
    <input type="hidden" name="from_application" value="<?php echo $from_application ?>" />
    <input type="hidden" name="from_parameters" value='<?php echo serialize($from_parameters) ?>' />
    <input type="hidden" name="link_type" value="<?php echo $link_type ?>" />
    <input type="hidden" name="to_application" value="<?php echo $to_application ?>" />
    <input type="hidden" name="to_parameters" value="" />
    <input type="hidden" name="url" value="<?php echo $return_url ?>" />
    <input type="hidden" name="actionID" value="addlink_add" />
    <?php echo Util::formInput() ?>
    <input type="submit" class="button" onclick="return validate();" value="<?php echo _("Select") ?>" />
    <input type="button" class="button" onclick="document.cancel.submit();" value="<?php echo _("Cancel") ?>" />
<?php if ($conf['user']['online_help'] && $browser->hasFeature('javascript')): ?>
    <input type="button" class="button" onclick="<?php echo Help::listLink('turba', 'select-contact'); ?>" value="<?php echo _("Help") ?>" />
    </form>
<?php endif; ?>
  </td>
</tr>
<!-- End Buttons Row -->

</table>

<form name="cancel">
  <input type="hidden" name="actionID" value="addlink_cancel" />
  <input type="hidden" name="url" value="<?php echo $return_url ?>" />
</form>
