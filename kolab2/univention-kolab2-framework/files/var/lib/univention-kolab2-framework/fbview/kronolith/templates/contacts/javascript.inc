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

function passAddresses()
{
    var list = window.document.contacts.selected_addresses;
    var action = "";

    for (var i = 0; i < list.length; i++) {
        var item = list.options[i];
        if (item.value == "") { continue; }
        action += '<?php echo ini_get('arg_separator.output') ?>sa' + i + '=' + escape(item.value + "|" + item.text);
    }
    if (window.document.contacts.action.indexOf("?") < 0) {
        action = window.document.contacts.action + "?" + action.substring(1, action.length);
    } else {
        action = window.document.contacts.action + "<?php echo ini_get('arg_separator.output') ?>" + action;
    }
    window.document.contacts.action = action;
}

function addAddress()
{
    var s = window.document.contacts.search_results;
    var d = window.document.contacts.selected_addresses;

    if (s.selectedIndex < 0) {
        alert('<?php echo addslashes(_("You must select an address first.")) ?>');
        return false;
    } else {
        for (var i = 0; i < s.length; i++) {
            var item = s.options[i];
            if (item.value == "") { continue; }
            if (item.selected) {
                d.options[d.length] = new Option(item.text, item.value);
            }
        }
    }
}

function updateMessage()
{
    if (parent.opener.closed) {
        alert('<?php echo addslashes(_("The Edit Attendees screen is no longer present. Exiting.")) ?>');
        this.close();
        return;
    }

    if (!parent.opener.document.attendeesForm) {
        alert('<?php echo addslashes(_("You can only use this form from the Edit Attendees screen.")) ?>');
        this.close();
        return;
    }

    var list = window.document.contacts.selected_addresses;
    var field = parent.opener.document.attendeesForm.newAttendees;
    for (var i = 0; i < list.length; i++) {
        if (list.options[i].value == '') {
            continue;
        }
        if (display == 'name') {
            var address = unescape(list.options[i].value);
        } else {
            var address = list.options[i].text;
        }

        if (field.value) {
            field.value = field.value + ', ' + address;
        } else {
            field.value = address;
        }
    }
    this.close();
}

function saClear()
{
    window.document.contacts.selected_addresses.length = 1;
}

function removeAddress()
{
    var list = window.document.contacts.selected_addresses;
    for (var i = list.length - 1; i > 0; i--) {
        if (list.options[i].selected) {
            list.options[i] = null;
        }
    }
}
//-->
</script>
