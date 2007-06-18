/**
 * Horde Html Helper Javascript Class
 *
 * Provides the javascript class insert html tags by clicking on icons.
 *
 * The helpers available:
 *      emoticons - for inserting emoticons strings
 *
 * $Horde: horde/templates/javascript/open_html_helper.js,v 1.7 2004/04/07 14:43:48 chuck Exp $
 *
 * Copyright 2003-2004 Marko Djukic <marko@oblo.com>
 *
 * See the enclosed file COPYING for license information (GPL). If you did not
 * receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Marko Djukic <marko@oblo.com>
 * @version $Revision: 1.1.2.1 $
 * @package horde
 * @todo add handling for font tags, tables, etc.
 */

var targetElement;

function openHtmlHelper(type, target)
{
    var lay = document.getElementById('htmlhelper_' + target);
    targetElement = document.getElementById(target);

    if (lay.style.visibility == 'visible') {
        lay.style.visibility = 'hidden';
        return false;
    }

    if (lay.firstChild) {
        lay.removeChild(lay.firstChild);
    }

    var table = document.createElement('TABLE');
    var tbody = document.createElement('TBODY');
    table.appendChild(tbody);
    table.cellSpacing = 0;
    table.border = 0;

    if (type == 'emoticons') {
        row = document.createElement('TR');
        cell = document.createElement('TD');
        <?php require_once 'Horde/Text/Filter/emoticons.php'; $patterns = Text_Filter_emoticons::getPatterns(); $icons = array_flip($patterns['replace']); foreach ($icons as $icon => $string): ?>
        link = document.createElement('A');
        link.href = '#';
        link.onclick = function() {
            targetElement.value = targetElement.value + '<?php echo $string; ?>' + ' ';
        }
        cell.appendChild(link);
        img = document.createElement('IMG')
        img.src = '<?php echo $GLOBALS['registry']->getParam('graphics', 'horde') . '/emoticons/' . $icon . '.gif'; ?>';
        img.align = 'middle';
        img.border = 0;
        link.appendChild(img);
        <?php endforeach; ?>
        row.appendChild(cell);
        tbody.appendChild(row);
        table.appendChild(tbody);
    }

    lay.appendChild(table);
    lay.style.visibility = 'visible';
}
