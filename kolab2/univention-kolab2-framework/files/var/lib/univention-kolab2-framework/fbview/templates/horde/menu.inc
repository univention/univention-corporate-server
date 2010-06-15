<table border="0" cellpadding="0" cellspacing="0" width="100%">
<?php if (!empty($conf['logo']['image']) || !Util::getFormData('mozbar')): ?>
  <tr>
    <td class="menu" colspan="2">
      <table border="0" width="100%">
        <tr>
         <td width="100%" class="themelogo">
           <?php
           if (!empty($conf['logo']['image'])) {
               if (!empty($conf['logo']['link'])) {
                   echo Horde::link($conf['logo']['link'], null, null, '_top');
               }
               echo Horde::img($conf['logo']['image'], '', 'border="0"', '');
               if (!empty($conf['logo']['link'])) {
                   echo '</a>';
               }
           } else {
               echo '&nbsp;';
           }
           ?>
         </td>
        </tr>
      </table>
    </td>
  </tr>
<?php endif; ?>
  <tr>
    <td valign="top" class="sidebar-panel" width="100%">
      <?php echo $menutext ?>
    </td>
    <td>&nbsp;</td>
  </tr>
</table>
