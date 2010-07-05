<?php
/**
 * $Horde: turba/browse.php,v 1.76.2.29 2009-01-06 15:27:38 jan Exp $
 *
 * Copyright 2000-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you did
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Turba
 */

require_once dirname(__FILE__) . '/lib/base.php';
require_once 'Horde/Variables.php';
require_once TURBA_BASE . '/lib/Views/Browse.php';

$params = array('vars' => Variables::getDefaultVariables(),
                'prefs' => &$prefs,
                'notification' => &$notification,
                'registry' => &$registry,
                'browse_source_count' => $browse_source_count,
                'browse_source_options' => $browse_source_options,
                'copymove_source_options' => $copymove_source_options,
                'copymoveSources' => $copymoveSources,
                'addSources' => $addSources,
                'cfgSources' => $cfgSources,
                'attributes' => $attributes,
                'turba_shares' => &$turba_shares,
                'conf' => $conf,
                'source' => $default_source,
                'browser' => $browser);
$browse = new Turba_View_Browse($params);
$browse->run();
