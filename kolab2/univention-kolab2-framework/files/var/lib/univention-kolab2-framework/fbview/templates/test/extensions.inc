<html>
<head>
<title>PHP Extensions</title>
<style>
body { background-color: white; margin-top: 0; margin-left: 20; margin-right: 20; }
table { font-family: Arial, Helvetica, sans-serif; font-size: 12px; margin-top: 0; margin-left: 0; }
a { text-decoration: none; font-family: Arial, Helvetica, sans-serif; font-size: 12px; margin-top: 0; margin-left: 0; }
a:active { color: #2457ff; }
a:hover { color: #2457ff; text-decoration: underline; }
a:link { color: #2457ff; }
a:visited { color: #2457ff; }
.black { background-color: #000000; color: #ffffff; }
</style>
</head>
<body>
<a href="<?php echo $_GET['url'] ?>?mode=test">&lt;&lt; Back to test.php</a>
<br />
<table width="100%" cellspacing="0"><tr><td colspan="2"><table>
<tr><td>php version:</td><td><b><?php echo phpversion() ?></b></td></tr>
<tr><td>server api:</td><td><b><?php echo @php_sapi_name()?></b></td></tr>
<tr><td>loaded extensions:</td><td><b><?php $extensions = @get_loaded_extensions(); echo count($extensions); ?></b></td></tr>
<tr><td>system:</td><td><b><?php echo @php_uname()?></b></td></tr>
</table><br /></td></tr>
<tr class="black">
<td><b>activated extensions:</b></td>
<td><b><?php echo @strtolower($_GET['ext']) ?> function list:</b></td>
</tr>
<tr><td valign="top" width="50%"><table width="100%">
<?php
    @sort($extensions);
    foreach ($extensions as $extension) {
        echo '<tr><td width="30%">' . $extension . '</td><td><a href="?mode=extensions&amp;ext=' . $extension . '&amp;url=' . urlencode($_GET['url']) . '">function list</a></td></tr>';
    }
?>
</table></td><td valign="top" width="50%"><table>
<?php
    if (isset($_GET['ext'])) {
        $functions = @get_extension_funcs($_GET['ext']);
        @sort($functions);
        foreach ($functions as $function) {
            echo "<tr><td><a href=\"http://www.php.net/manual/function." . str_replace('_', '-', $function) . ".php\" target=\"_blank\">$function</a></td></tr>\n";
        }
    }
?>
</table></td></tr></table></body></html>
