<?php
/**
 * $Horde: horde/admin/sqlshell.php,v 1.17 2004/05/12 15:14:37 chuck Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 */

@define('HORDE_BASE', dirname(__FILE__) . '/..');
require_once HORDE_BASE . '/lib/base.php';
require_once 'Horde/Menu.php';
require_once 'Horde/Help.php';
require_once 'DB.php';

if (!Auth::isAdmin()) {
    Horde::fatal('Forbidden.', __FILE__, __LINE__);
}

$title = _("SQL Shell");
require HORDE_TEMPLATES . '/common-header.inc';
require HORDE_TEMPLATES . '/admin/common-header.inc';

?>
<form name="sqlshell" action="<?php echo $_SERVER['PHP_SELF'] ?>" method="post">
<?php Util::pformInput() ?>

<?php
if (Util::getFormData('list-tables')) {
    $description = 'LIST TABLES';
    $dbh = &DB::connect($conf['sql']);
    if (is_a($dbh, 'PEAR_Error')) {
        $result = $dbh;
    } else {
        $result = $dbh->getListOf('tables');
    }
} elseif (Util::getFormData('list-dbs')) {
    $description = 'LIST DATABASES';
    $dbh = &DB::connect($conf['sql']);
    if (is_a($dbh, 'PEAR_Error')) {
        $result = $dbh;
    } else {
        $result = $dbh->getListOf('databases');
    }
} elseif ($command = trim(Util::getFormData('sql'))) {
    // Keep a cache of prior queries for convenience.
    if (!isset($_SESSION['_sql_query_cache'])) {
        $_SESSION['_sql_query_cache'] = array();
    }
    if (($key = array_search($command, $_SESSION['_sql_query_cache'])) !== false) {
        unset($_SESSION['_sql_query_cache'][$key]);
    }
    array_unshift($_SESSION['_sql_query_cache'], $command);
    while (count($_SESSION['_sql_query_cache']) > 20) {
        array_pop($_SESSION['_sql_query_cache']);
    }

    // Parse out the query results.
    $dbh = &DB::connect($conf['sql']);
    if (is_a($dbh, 'PEAR_Error')) {
        $result = $dbh;
    } else {
        $result = $dbh->query(String::convertCharset($command, NLS::getCharset(), $conf['sql']['charset']));
    }
}

if (isset($result)) {
    if (isset($command)) {
        echo '<table cellpadding="2" cellspacing="0" border="0" width="100%"><tr><td class="header">' . _("Query") . '</td></tr><tr><td class="text"><pre>' . htmlspecialchars($command) . '</pre></td></tr></table>';
    }

    echo '<table width="100%" cellpadding="2" cellspacing="0" border="0"><tr><td class="header">' . _("Results") . '</td></tr><tr><td>';

    if (is_a($result, 'PEAR_Error')) {
        echo '<pre>'; var_dump($result); echo '</pre>';
    } else {
        if (is_object($result)) {
            echo '<table border="0" cellpadding="1" cellspacing="1" class="item">';
            $first = true;
            $i = 0;
            while ($row = $result->fetchRow(DB_FETCHMODE_ASSOC)) {
                if ($first) {
                    echo '<tr>';
                    foreach ($row as $key => $val) {
                        echo '<th align="left">' . (empty($key) ? '&nbsp;' : htmlspecialchars(String::convertCharset($key, $conf['sql']['charset']))) . '</th>';
                    }
                    echo '</tr>';
                    $first = false;
                }
                echo '<tr class="item' . ($i % 2) . '">';
                foreach ($row as $val) {
                    echo '<td class="fixed">' . (empty($val) ? '&nbsp;' : htmlspecialchars(String::convertCharset($val, $conf['sql']['charset']))) . '</td>';
                }
                echo '</tr>';
                $i++;
            }
            echo '</table>';
        } elseif (is_array($result)) {
            echo '<table border="0" cellpadding="1" cellspacing="1" class="item">';
            $first = true;
            foreach ($result as $i => $val) {
                if ($first) {
                    echo '<tr><th align="left">' . (isset($description) ? htmlspecialchars($description) : '&nbsp;') . '</th></tr>';
                    $first = false;
                }
                echo '<tr class="item' . ($i % 2) . '">';
                echo '<td class="fixed">' . (empty($val) ? '&nbsp;' : htmlspecialchars(String::convertCharset($val, $conf['sql']['charset']))) . '</td>';
                echo '</tr>';
            }
            echo '</table>';
        } else {
            echo '<b>' . _("Success") . '</b>';
        }
    }

    echo '</td></tr></table><br />';
}
?>

<?php if (isset($_SESSION['_sql_query_cache']) &&
          count($_SESSION['_sql_query_cache'])): ?>
  <select name="query_cache" onchange="document.sqlshell.sql.value = document.sqlshell.query_cache[document.sqlshell.query_cache.selectedIndex].value;">
  <?php foreach ($_SESSION['_sql_query_cache'] as $query): ?>
    <option value="<?php echo htmlspecialchars($query) ?>"><?php echo htmlspecialchars($query) ?></option>
  <?php endforeach; ?>
  </select>
  <input type="button" value="<?php echo _("Paste") ?>" class="button" onclick="document.sqlshell.sql.value = document.sqlshell.query_cache[document.sqlshell.query_cache.selectedIndex].value;" />
  <input type="button" value="<?php echo _("Run") ?>" class="button" onclick="document.sqlshell.sql.value = document.sqlshell.query_cache[document.sqlshell.query_cache.selectedIndex].value; document.sqlshell.submit();" />
  <br />
<?php endif; ?>

<textarea class="fixed" name="sql" rows="10" cols="60" wrap="hard">
<?php if (!empty($command)) echo htmlspecialchars($command) ?></textarea>
<br />
<input type="submit" class="button" value="<?php echo _("Execute") ?>">
<input type="submit" class="button" name="list-tables" value="<?php echo _("List Tables") ?>">
<input type="submit" class="button" name="list-dbs" value="<?php echo _("List Databases") ?>">
<?php if ($conf['user']['online_help'] && $browser->hasFeature('javascript')): ?>
    <?php Help::javascript(); ?>
    <td class="header" align="right"><?php echo Help::link('admin', 'admin-sqlshell') ?></td>
<?php endif; ?>

</form>
<?php

require HORDE_TEMPLATES . '/common-footer.inc';
