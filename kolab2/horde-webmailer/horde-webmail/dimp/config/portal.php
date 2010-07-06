<?php
/**
 * DIMP portal configuration page.
 *
 * Format: An array named $dimp_block_list
 *         KEY: Block label text
 *         VALUE: An array with the following entries:
 *                'ob' => The Horde_Block object to display
 *
 *                These entries are optional and will only be used if you need
 *                to customize the portal output:
 *                'class' => A CSS class to assign to the containing block.
 *                           Defaults to "headerbox".
 *                'domid' => A DOM ID to assign to the containing block
 *                'tag' => A tag name to add to the template array. Allows
 *                         the use of <if:block.tag> in custom template files.
 *
 * $Horde: dimp/config/portal.php.dist,v 1.6 2007-09-04 21:31:14 jan Exp $
 */

require_once 'Horde/Block.php';
require_once 'Horde/Block/Collection.php';
$collection = new Horde_Block_Collection();
$dimp_block_list = array();

// Show a folder summary of the mailbox.  All polled folders are displayed.
require_once DIMP_BASE . '/lib/Block/foldersummary.php';
$dimp_block_list[_("Folder Summary")] = array(
    'ob' => new Horde_Block_dimp_foldersummary(array())
);

// Alternate DIMP block - shows details of 'msgs_shown' number of the most
// recent unseen messages.
//require_once DIMP_BASE . '/lib/Block/newmail.php';
//$dimp_block_list[_("Newest Unseen Messages")] = array(
//    'ob' => new Horde_Block_dimp_newmail(array('msgs_shown' => 2))
//);

// Show a contact search box.
// Must include 'turba' in $conf['menu']['apps']
$dimp_block_list[$collection->getName('turba', 'minisearch')] = array(
    'ob' => $collection->getBlock('turba', 'minisearch', array())
);

// Display calendar events
// Must include 'kronolith' in $conf['menu']['apps']
$dimp_block_list[$collection->getName('kronolith', 'summary')] = array(
    'ob' => $collection->getBlock('kronolith', 'summary', array())
);
