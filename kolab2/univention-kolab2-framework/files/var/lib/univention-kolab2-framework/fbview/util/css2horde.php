<!-- $Horde: horde/util/css2horde.php,v 1.6 2003/09/24 21:22:06 chuck Exp $ -->

<form method="post">
<textarea name="css" rows="8" cols="80"><?php if (!empty($_POST['css'])) echo $_POST['css'] ?></textarea>
<br />
<input type="submit" />
</form>

<?php
if (isset($_POST['css'])) {
    $css = get_magic_quotes_gpc() ? stripslashes($_POST['css']) : $_POST['css'];
    $items = explode('}', $css);
    $styles = array();
    foreach ($items as $item) {
        $item = trim(str_replace('}', '', $item));
        if (!empty($item)) {
            $styleitem = explode('{', $item);
            $styleitems = explode(';', $styleitem[1]);
            foreach ($styleitems as $stylebit) {
                $stylebit = trim($stylebit);
                if (!empty($stylebit)) {
                    $attribute = explode(':', $stylebit);
                    $styles[trim($styleitem[0])][trim($attribute[0])] = trim($attribute[1]);
                }
            }
        }
    }

    foreach ($styles as $class => $props) {
        foreach ($props as $prop => $value) {
            echo '$css[\'' . escape($class) . '\'][\'' . escape($prop) . '\'] = \'' . escape($value) . '\';' . "\n<br />";
        }
        echo '<br />';
    }
}

/**
 * Make sure single quotes get escaped.
 *
 * @param string $text  The string to escape.
 *
 * @return  Escaped $text.
 */
function escape($text)
{
    return str_replace("'", "\'", $text);
}
