function toggleAddressesBlock(field, count)
{
    var block = new Horde_Hideable('ab_' + field);

    block.toggle();
    text = document.createTextNode(block.shown() ?
                                   '<?php echo _("[Hide Addresses]") ?>' :
                                   '<?php echo _("[Show Addresses -") ?> ' + count + ' <?php echo _("recipients]") ?>');
    link = document.createElement('A');
    link.href = '';
    link.className = 'widget';
    link.onclick = function() {
        toggleAddressesBlock(field, count);
        return false;
    }
    link.appendChild(text);

    var toggle = document.getElementById('at_' + field);
    if (toggle.firstChild) {
        toggle.removeChild(toggle.firstChild);
    }
    toggle.appendChild(link);
}
