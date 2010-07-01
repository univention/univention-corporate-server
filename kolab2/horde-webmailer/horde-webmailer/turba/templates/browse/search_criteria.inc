<?php
foreach ($map as $name => $v) {
    if (substr($name, 0, 2) != '__') {
?>
 <tr>
  <td width="1%" class="nowrap rightAlign" ><strong><?php echo Horde::label($name, $GLOBALS['attributes'][$name]['label']) ?></strong></td>
  <td class="leftAlign"><input type="text" size="30" id="<?php echo $name ?>" name="<?php echo $name ?>" value="<?php echo isset($criteria[$name]) ? htmlspecialchars($criteria[$name]) : '' ?>" /></td>
 </tr>
<?php
    }
}
?>
</table>
