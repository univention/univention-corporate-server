<script language="JavaScript" type="text/javascript">
<!--
// Check all of the main form fields to make sure they are filled in
function validate()
{
    if (document.problem_report.subject.value == '') {
        alert('<?php echo _("Please provide a summary of the problem."); ?>');
        document.problem_report.subject.focus();
        return false;
    } else if (document.problem_report.message.value == '') {
        alert('<?php echo _("You must describe the problem before you can send the problem report."); ?>');
        document.problem_report.message.focus();
        return false;
    }

    document.problem_report.actionID.value = 'send_problem_report';
    return true;
}
//-->
</script>

<form method="post" name="problem_report" action="problem.php">
<?php Util::pformInput() ?>
<input type="hidden" name="actionID" value="cancel_problem_report" />
<?php if (isset($return_url)): ?><input type="hidden" name="return_url" value="<?php echo htmlspecialchars($return_url) ?>" /><?php endif; ?>

<table border="0" cellpadding="3" cellspacing="2" width="100%">
<tr class="header">
    <td colspan="2" class="header"><b><?php echo $label ?></b></td>
</tr>

<tr>
    <td class="light" align="right"><?php echo _("Your Name") ?></td>
    <td><input type="text" tabindex="1" name="name" value="<?php echo $name ?>" size="70" /></td>
</tr>

<tr>
    <td class="light" align="right"><?php echo _("Your Email Address") ?></td>
    <td><input type="text" tabindex="2" name="email" value="<?php echo $email ?>" size="70" /></td>
</tr>

<tr>
    <td class="light" align="right"><?php echo _("Short Summary") ?></td>
    <td><input type="text" tabindex="3" name="subject" value="<?php echo $subject ?>" size="70" /></td>
</tr>

<tr>
    <td colspan="2" class="smallheader"><b><?php echo _("Full Description") ?></b></td>
</tr>
<tr>
    <td></td>
    <td><textarea tabindex="4" name="message" rows="20" cols="80" wrap="hard"><?php echo $message ?></textarea></td>
</tr>

<tr>
  <td></td>
  <td class="light">
    <input class="button" type="submit" name="formsubmit" onclick="return validate();" value="<?php echo _("Send Problem Report") ?>" />
    <input class="button" type="submit" name="formsubmit" value="<?php echo _("Cancel Problem Report") ?>" />
  </td>
</tr>

</table>
</form>
