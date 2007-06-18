<tr>
    <td>&nbsp;</td>
</tr>
<tr>
    <td>
        <input type="submit" class="button" value="<?php echo _("Perform Maintenance Operations") ?>" onclick="document.maint_confirm.submit();" />
<?php if ($browser->hasFeature('javascript')) : ?>
        &nbsp;&nbsp;
        <input type="button" class="button" value="<?php echo _("Skip Maintenance") ?>" onclick="uncheckAll(); document.maint_confirm.submit();" />
<?php endif; ?>
    </td>
</tr>

</table>
