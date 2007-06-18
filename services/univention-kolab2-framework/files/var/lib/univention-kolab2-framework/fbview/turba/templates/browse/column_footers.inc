    </table>
    <input type="hidden" name="actionID" value="" />
    <input type="hidden" name="show" value="<?php echo Util::getFormData('show','all') ?>" />
    <input type="hidden" name="source" value="<?php echo $source ?>" />
    <input type="hidden" name="sortby" value="<?php echo $prefs->getValue('sortby') ?>" />
    <input type="hidden" name="sortdir" value="<?php echo $prefs->getValue('sortdir') ?>" />
    <input type="hidden" name="key" value="<?php echo Util::getFormData('key', '') ?>" />
    <input type="hidden" name="targetAddressbook" value="" />
    <input type="hidden" name="targetList" value="" />
    <input type="hidden" name="targetNew" value="" />
    </form>
  </td>
</tr>
