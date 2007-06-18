<?php
foreach ($map as $name => $v) {
  if ($name != '__owner' &&
      $name != '__type' &&
      $name != '__members') {
?>
<tr>
    <td width="1%" nowrap="nowrap" class="light" align="right"><b><?php echo $attributes[$name]['label'] ?></b></td>
    <td align="left"><input type="text" size="30" name="<?php echo $name ?>" /></td>
</tr>
<?php
  }
}
?>

</table>
</form>