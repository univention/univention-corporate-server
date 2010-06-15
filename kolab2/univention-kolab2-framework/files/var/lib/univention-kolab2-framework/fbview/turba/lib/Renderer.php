<?php

require_once 'Horde/Form/Renderer.php';

/**
 * Turba Form Renderer
 *
 * $Horde: turba/lib/Renderer.php,v 1.14 2004/05/20 16:39:08 jan Exp $
 *
 * @package Turba
 */
class Turba_Renderer extends Horde_Form_Renderer {

    var $_active = false;
    var $_object;

    function setObject(&$object)
    {
        $this->_object = &$object;
    }

    function beginActive($name)
    {
        $this->_active = true;
        parent::beginActive($name);
    }

    function beginInactive($name)
    {
        $this->_active = false;
        parent::beginInactive($name);
    }

    function _sectionHeader($title)
    {
?><table border="0" cellpadding="2" cellspacing="0" width="100%">
<tr><td align="left" class="header"><b><?php echo $title ?></b></td>
<?php
if (!$this->_active &&
    Turba::checkPermissions($this->_object, 'object', PERMS_EDIT)) {
    $url = Util::addParameter('', 'source', $this->_object->source->name);
    $url = Util::addParameter($url, 'key', $this->_object->getValue('__key'));
?>
  <td align="right" class="header">
    <span class="smallheader">
    <?php echo Horde::link(Horde::applicationUrl('edit.php' . $url), _("Edit"), 'smallheader') . _("Edit") ?></a> |
    <?php echo Horde::link(Horde::applicationUrl('delete.php' . $url), _("Delete"), 'smallheader') . _("Delete") ?></a>
    </span>
  </td>
<?php } ?>
</tr></table><?php
    }

}
