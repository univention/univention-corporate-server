<html>
<head>
<title>PHP Extensions</title>
<style type="text/css">
body { font-family: Geneva,Arial,Helvetica,sans-serif; font-size: 90% }
td { font-family: Geneva,Arial,Helvetica,sans-serif }h1 { font-size: 110%; color: black; font-family: Verdana,Geneva,Arial,Helvetica,sans-serif; }
</style>
</head>
<body>
<a href="<?php echo isset($_GET['url']) ? htmlspecialchars($_GET['url']) : 'test.php' ?>?mode=test">&lt;&lt; Back to test.php</a>
<br />
<table width="100%" cellspacing="0"><tr><td colspan="2"><table>
<tr><td>php version:</td><td><strong><?php echo PHP_VERSION ?></strong></td></tr>
<tr><td>server api:</td><td><strong><?php echo PHP_SAPI ?></strong></td></tr>
<tr><td>loaded extensions:</td><td><strong><?php $extensions = @get_loaded_extensions(); echo count($extensions); ?></strong></td></tr>
<tr><td>system:</td><td><strong><?php echo @php_uname() ?></strong></td></tr>
</table><br /></td></tr>
<tr class="black">
<td><strong>activated extensions:</strong></td>
<td><strong><?php echo isset($_GET['ext']) ? htmlspecialchars($_GET['ext']) : '' ?> function list:</strong></td>
</tr>
<tr><td valign="top" width="50%"><table width="100%">
<?php
    @sort($extensions);
    foreach ($extensions as $extension) {
        echo '<tr><td width="30%">' . $extension . '</td><td><a href="?mode=extensions&amp;ext=' . $extension . '&amp;url=' . urlencode(isset($_GET['url']) ? $_GET['url'] : '') . '">function list</a></td></tr>';
    }
?>
</table></td><td valign="top" width="50%"><table>
<?php
    if (isset($_GET['ext'])) {
        $functions = @get_extension_funcs($_GET['ext']);
        if (is_array($functions)) {
            sort($functions);
            foreach ($functions as $function) {
                echo "<tr><td><a href=\"http://www.php.net/manual/function." . str_replace('_', '-', $function) . ".php\" target=\"_blank\">$function</a></td></tr>\n";
            }
        }
    }
?>
</table></td></tr></table></body></html>
