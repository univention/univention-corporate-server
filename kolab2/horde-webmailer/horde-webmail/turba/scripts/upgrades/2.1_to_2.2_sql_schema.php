#!/usr/bin/php
<?php
/**
 * Very basic migration script for moving to the Turba 2.2 default sql schema.
 *
 * Note: This is NOT complete yet, but will get your Turba 2.1 data into
 * enough shape to run with the new default sql schema in Turba 2.2.
 *
 * It is HIGHLY RECOMMENDED to back up your current Turba tables BEFORE
 * attempting this upgrade!
 *
 * $Horde: turba/scripts/upgrades/2.1_to_2.2_sql_schema.php,v 1.18.2.9 2009-10-15 10:13:59 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file LICENSE for license information (ASL).  If you
 * did not receive this file, see http://www.horde.org/licenses/asl.php.
 */

/* Set this variable to 'true' to activate the script. */
$for_real = false;

/* You must set these to an appropriate user/pass/table for your server. */
$db_user = 'root';
$db_pass = '';
$db_table = 'turba_objects';

/* Allow skipping of parsing certain fields.
 * You can force fields to not be parsed by setting the field to false
 * below. */
$do_name = true;
$do_home = true;
$do_work = true;
$do_email = true;

/* YOU SHOULD NOT HAVE TO TOUCH ANYTHING BELOW THIS LINE */
@define('AUTH_HANDLER', true);
@define('HORDE_BASE', dirname(__FILE__) . '/../../..');

/* Set up the CLI environment */
require_once HORDE_BASE . '/lib/core.php';
require_once 'Horde/CLI.php';
if (!Horde_CLI::runningFromCli()) {
    exit("Must be run from the command line\n");
}
$cli = &Horde_CLI::singleton();
$cli->init();

/* Grab what we need to steal the DB config */
require_once HORDE_BASE . '/config/conf.php';
require_once 'Horde/Form.php';
require 'Horde/NLS/carsigns.php';
require_once 'DB.php';

$config = $GLOBALS['conf']['sql'];
$config['username'] = $db_user;
$config['password'] = $db_pass;
unset($config['charset']);
$db = DB::connect($config);
if (is_a($db, 'PEAR_Error')) {
    Horde::fatal($db, __FILE__, __LINE__);
}
if (!$for_real) {
    $cli->message('No changes will done to the existing data. Please read the comments in the code, then set the $for_real flag to true before running.', 'cli.message');
}

/* Define how to transform the address book table */
$queries = array(
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_firstname VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_lastname VARCHAR(255)',
    'UPDATE ' . $db_table . ' SET object_lastname = object_name',
    'ALTER TABLE ' . $db_table . ' DROP COLUMN object_name',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_middlenames VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_nameprefix VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_namesuffix VARCHAR(32)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_phototype VARCHAR(10)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_bday VARCHAR(10)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_homestreet VARCHAR(255)',
    'UPDATE ' . $db_table . ' SET object_homestreet = object_homeaddress',
    'ALTER TABLE ' . $db_table . ' DROP COLUMN object_homeaddress',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_homepob VARCHAR(10)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_homecity VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_homeprovince VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_homepostalcode VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_homecountry VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_workstreet VARCHAR(255)',
    'UPDATE ' . $db_table . ' SET object_workstreet = object_workaddress',
    'ALTER TABLE ' . $db_table . ' DROP COLUMN object_workaddress',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_workpob VARCHAR(10)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_workcity VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_workprovince VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_workpostalcode VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_workcountry VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_tz VARCHAR(32)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_geo VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_pager VARCHAR(25)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_role VARCHAR(255)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_logotype VARCHAR(10)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_category VARCHAR(80)',
    'ALTER TABLE ' . $db_table . ' ADD COLUMN object_url VARCHAR(255)',
    'CREATE INDEX turba_email_idx ON ' . $db_table . ' (object_email)',
    'CREATE INDEX turba_firstname_idx ON ' . $db_table . ' (object_firstname)',
    'CREATE INDEX turba_lastname_idx ON ' . $db_table . ' (object_lastname)',
);
switch ($config['phptype']) {
case 'mssql':
    $queries[] = 'ALTER TABLE ' . $db_table . ' ADD COLUMN object_photo VARBINARY(MAX)';
    $queries[] = 'ALTER TABLE ' . $db_table . ' ADD COLUMN object_logo VARBINARY(MAX)';
    break;
case 'pgsql':
    $queries[] = 'ALTER TABLE ' . $db_table . ' ADD COLUMN object_photo TEXT';
    $queries[] = 'ALTER TABLE ' . $db_table . ' ADD COLUMN object_logo TEXT';
    break;
default:
    $queries[] = 'ALTER TABLE ' . $db_table . ' ADD COLUMN object_photo BLOB';
    $queries[] = 'ALTER TABLE ' . $db_table . ' ADD COLUMN object_logo BLOB';
    break;
}

/* Perform the queries */
/* @TODO - Better error handling */
$error = false;
foreach ($queries as $query) {
    if ($config['phptype'] == 'oci8') {
        $query = str_replace('ADD COLUMN', 'ADD', $query);
    }
    if ($for_real) {
        $results = $db->query($query);
        if (is_a($results, 'PEAR_Error')) {
            $cli->message($results->toString(), 'cli.error');
            $error = true;
            continue;
        }
    }
    $cli->message($query, 'cli.success');
}
if ($error &&
    $cli->prompt('Continue?', array('y' => 'Yes', 'n' => 'No'), 'n') != 'y') {
    exit(1);
}

/* Attempt to transform the fullname into lastname and firstname */
if ($do_name) {
    require_once HORDE_BASE . '/turba/lib/Turba.php';
    $sql = 'SELECT object_id, ' . ($for_real ? 'object_lastname' : 'object_name') . ' FROM ' . $db_table;
    $names = $db->getAssoc($sql);
    if (is_a($names, 'PEAR_Error')) {
        $cli->message($names->toString(), 'cli.error');
        exit(1);
    }
    $insert_query = 'UPDATE ' . $db_table . ' SET object_firstname = ?, object_lastname = ? WHERE object_id = ?';
    if (!$for_real) {
        $cli->writeln($insert_query);
    }
    $insert = $db->prepare($insert_query);
    foreach ($names as $id => $name ) {
        $lastname = Turba::guessLastName($name);
        $firstname = '';
        if (strpos($name, ',') !== false) {
            $firstname = preg_replace('/' . preg_quote($lastname, '/') . ',\s*/', '', $name);
        } elseif ($name != $lastname) {
            $firstname = preg_replace('/\s+' . preg_quote($lastname, '/') . '/', '', $name);
        }
        if ($for_real) {
            $db->execute($insert, array($firstname, $lastname, $id));
        } else {
            $cli->writeln("ID=$id\nFirst name: $firstname; Last name: $lastname; Name: $name\n");
        }
    }
    $cli->message('Contact name fields parsed.', 'cli.success');
} else {
    $cli->message('Contact name fields SKIPPED.', 'cli.success');
}

if ($do_home) {
    $sql = 'SELECT object_id, ' . ($for_real ? 'object_homestreet' : 'object_homeaddress') . ' FROM ' . $db_table;
    $addresses = $db->getAssoc($sql);
    if (is_a($addresses, 'PEAR_Error')) {
        $cli->message($addresses->toString(), 'cli.error');
        exit(1);
    }
    $insert_query = 'UPDATE ' . $db_table . ' SET object_homestreet = ?, object_homecity = ?, object_homeprovince = ?, object_homepostalcode = ?, object_homecountry = ? WHERE object_id = ?';
    if (!$for_real) {
        $cli->writeln($insert_query);
    }
    $insert = $db->prepare($insert_query);
    parseAddress($addresses, $insert, $for_real);
    $cli->message('Home address fields parsed.', 'cli.success');
} else {
    $cli->message('Home address fields SKIPPED.', 'cli.success');
}

if ($do_work) {
    $sql = 'SELECT object_id, ' . ($for_real ? 'object_workstreet' : 'object_workaddress') . ' FROM ' . $db_table;
    $addresses = $db->getAssoc($sql);
    if (is_a($addresses, 'PEAR_Error')) {
        $cli->message($addresses->toString(), 'cli.error');
        exit(1);
    }
    $insert_query = 'UPDATE ' . $db_table . ' SET object_workstreet = ?, object_workcity = ?, object_workprovince = ?, object_workpostalcode = ?, object_workcountry = ? WHERE object_id = ?';
    if (!$for_real) {
        $cli->writeln($insert_query);
    }
    $insert = $db->prepare($insert_query);
    parseAddress($addresses, $insert, $for_real);
    $cli->message('Work address fields parsed.', 'cli.success');
} else {
    $cli->message('Work address fields SKIPPED.', 'cli.success');
}

if ($do_email) {
    $sql = 'SELECT object_id, object_email FROM ' . $db_table;
    $emails = $db->getAssoc($sql);
    if (is_a($emails, 'PEAR_Error')) {
        $cli->message($emails->toString(), 'cli.error');
        exit(1);
    }
   $insert_query = 'UPDATE ' . $db_table . ' SET object_email = ? WHERE object_id = ?';
    if (!$for_real) {
        $cli->writeln($insert_query);
    }
    if ($for_real) {
        $insert = $db->prepare($insert_query);
        foreach ($emails as $id => $email) {
            $db->execute($insert, array(getBareEmail($email), $id));
        }
    } else {
        $cli->writeln($insert_query);
    }
}

/**
 * Helper function to parse out freeform addresses
 *
 * Try to parse out the free form addresses.
 * Assumptions we make to fit into our schema:
 * - Postal code is on the same line as state/province information
 * - If there is a line following the state/province/postal code line,
 *   it is taken as a country.
 * - Any lines before the postal code are treated as street address.
 *
 * @param array $addresses   An array of addresses to parse.
 * @param object $insert     A prepared update query to write the results.
 * @param boolean $for_real  Whether to really change any data.
 */
function parseAddress($addresses, $insert, $for_real)
{
    global $countries;

    foreach ($addresses as $id => $address) {
        if (empty($address)) {
            continue;
        }
        $city = $state = $postalCode = $street = $country = '';
        $p_address = Horde_Form_Type_address::parse($address);
        if (!count($p_address)) {
            $street = $address;
        } else {
            if (!empty($p_address['street'])) {
                $street = $p_address['street'];
            }
            if (!empty($p_address['city'])) {
                $city = $p_address['city'];
            }
            if (!empty($p_address['state'])) {
                $state = $p_address['state'];
            }
            if (!empty($p_address['zip'])) {
                $postalCode = $p_address['zip'];
            }
            if (!empty($p_address['country'])) {
                $country = isset($countries[String::upper($p_address['country'])])
                    ? $countries[String::upper($p_address['country'])]
                    : String::upper($p_address['country']);
            }
        }
        if ($for_real) {
            $GLOBALS['db']->execute($insert, array($street, $city, $state, $postalCode, $country, $id));
        } else {
            $GLOBALS['cli']->writeln("ID: $id\nStreet: $street\nCity: $city\nState: $state\nPostal Code: $postalCode\nCountry: $country\nAddress:\n$address\n");
        }
    }
}

/**
 * Static function to make a given email address rfc822 compliant.
 *
 * @param string $address  An email address.
 *
 * @return string  The RFC822-formatted email address.
 */
function getBareEmail($address)
{
    // Empty values are still empty.
    if (!$address) {
        return $address;
    }

    require_once 'Mail/RFC822.php';
    require_once 'Horde/MIME.php';

    static $rfc822;
    if (is_null($rfc822)) {
        $rfc822 = new Mail_RFC822();
    }

    $rfc822->validateMailbox($address);
    return MIME::rfc822WriteAddress($address->mailbox, $address->host);
}
