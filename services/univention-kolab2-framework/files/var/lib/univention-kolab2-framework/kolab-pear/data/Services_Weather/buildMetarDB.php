#!/usr/local/bin/php
<?php
/* vim: set expandtab tabstop=4 shiftwidth=4: */
// +----------------------------------------------------------------------+
// | PHP version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2004 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.0 of the PHP license,       |
// | that is bundled with this package in the file LICENSE, and is        |
// | available through the world-wide-web at                              |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Alexander Wirtz <alex@pc4p.net>                             |
// +----------------------------------------------------------------------+
//
// $Id: buildMetarDB.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once "DB.php";

// {{{ constants
// {{{ natural constants and measures
define("SERVICES_WEATHER_RADIUS_EARTH", 6378.15);
// }}}
// }}}

/**
* This script downloads, saves and processes the textfiles needed for
* the building the databases to enable searching for METAR stations.
*
* You can download the locations, which is a database of about 12000 world-
* wide locations, which can be used to determine the coordinates of your
* city or you can download a file with 6500 airports providing the metar
* data. This database is used for the next-METAR-station search. Please see
* the apropriate documentation in the Services_Weather_Metar class.
*
* For usage of this script, invoke with '-h'.
*
* @author       Alexander Wirtz <alex@pc4p.net>
* @link         http://weather.noaa.gov/tg/site.shtml
* @package      Services_Weather
* @version      1.2
*/

// {{{ Services_Weather_checkData()
/**
* Services_Weather_checkData
*
* Checks the data for a certain string-length and if it either consists of
* a certain char-type or a string of "-" as replacement.
*
* @param    array                           $data           The data to be checked
* @param    array                           $dataOrder      Because the data is in different locations, we provide this
* @return   bool
*/
function Services_Weather_checkData($data, $dataOrder)
{
    $return = true;
    foreach ($dataOrder as $type => $idx) {
        switch (strtolower($type)) {
            case "b":
                $len  = 2;
                $func = "ctype_digit";
                break;
            case "s":
                $len  = 3;
                $func = "ctype_digit";
                break;
            case "i":
                $len  = 4;
                $func = "ctype_alnum";
                break;
            default:
                break;
        }
        if ((strlen($data[$idx]) != $len) || (!$func($data[$idx]) && ($data[$idx] != str_repeat("-", $len)))) {
            $return = false;
            break;
        }
    }
    return $return;
}
// }}}

// {{{ Services_Weather_getNextArg()
/**
* Services_Weather_getNextArg
*
* Checks, if the next argument is a parameter to a predecessing option.
* Returns either that parameter or false, if the next argument is an option
*
* @param    int                             $c              Internal argument counter
* @return   string|bool
*/
function Services_Weather_getNextArg(&$c)
{
    if ((($c + 1) < $_SERVER["argc"]) && ($_SERVER["argv"][$c + 1]{0} != "-")) {
        $c++;
        return $_SERVER["argv"][$c];
    } else {
        return false;
    }    
}
// }}}

// First set a few variables for processing the options
$modeSet   = false;
$saveFile  = false;
$printHelp = false;
$invOpt    = false;
$verbose   = 0;
$dbType    = "mysql";
$dbProt    = "unix";
$dbName    = "servicesWeatherDB";
$dbUser    = "root";
$dbPass    = "";
$dbHost    = "localhost";
$dbOptions = array();
$userFile  = "";

// Iterate through the arguments and check their validity
for ($c = 1; $c < $_SERVER["argc"]; $c++) {
    switch ($_SERVER["argv"][$c]{1}) {
        case "l":
            // location-mode, if another mode is set, bail out
            if ($modeSet) {
                $printHelp = true;
            } else {
                $modeSet   = true;
                $filePart  = "bbsss";
                $tableName = "metarLocations";
                $dataOrder = array("b" => 0, "s" => 1, "i" => 2);
            }
            break;
        case "a":
            // dito for airport-mode
            if ($modeSet) {
                $printHelp = true;
            } else {
                $modeSet   = true;
                $filePart  = "cccc";
                $tableName = "metarAirports";
                $dataOrder = array("b" => 1, "s" => 2, "i" => 0);
            }
            break;
        case "f":
            // file-flag was provided, check if next argument is a string
            if (($userFile = Services_Weather_getNextArg($c)) === false) {
                $printHelp = true;
            }
            break;
        case "s":
            // If you download the file, it will be saved to disk
            $saveFile      = true;
            break;
        case "t":
            // The type of the DB to be used
            if (($dbType = Services_Weather_getNextArg($c)) === false) {
                $printHelp = true;
            }
            break;
        case "r":
            // The protocol of the DB to be used
            if (($dbProt = Services_Weather_getNextArg($c)) === false) {
                $printHelp = true;
            }
            break;
        case "d":
            // The name of the DB to be used
            if (($dbName = Services_Weather_getNextArg($c)) === false) {
                $printHelp = true;
            }
            break;
        case "u":
            // The user of the DB to be used
            if (($dbUser = Services_Weather_getNextArg($c)) === false) {
                $printHelp = true;
            }
            break;
        case "p":
            // The password of the DB to be used
            if (($dbPass = Services_Weather_getNextArg($c)) === false) {
                $printHelp = true;
            }
            break;
        case "h":
            // The host of the DB to be used
            if (($dbHost = Services_Weather_getNextArg($c)) === false) {
                $printHelp = true;
            }
            break;
        case "o":
            // Options for the DB
            if (($options = Services_Weather_getNextArg($c)) === false) {
                $printHelp = true;
            } else {
                $options   = explode(",", $options);
                foreach ($options as $option) {
                    $optPair = explode("=", $option);
                    $dbOptions[$optPair[0]] = $optPair[1];
                }
            }
            break;
        case "v":
            // increase verbosity
            for ($i = 1; $i < strlen($_SERVER["argv"][$c]); $i++) {
                if ($_SERVER["argv"][$c]{$i} == "v") {
                    $verbose++;
                } else {
                    $invOpt    = true;
                    break;
                }
            }
            break;
        default:
            // argument not valid, bail out
            $invOpt    = true;
            break;
    }
    if ($invOpt) {
        // see above
        $printHelp = true;
        echo "Invalid option: '".$_SERVER["argv"][$c]."'\n";
        break;
    }
}

// help-message
if (!$modeSet || $printHelp) {
    echo "Usage: ".basename($_SERVER["argv"][0], ".php")." -l|-a [options]\n";
    echo "Options:\n";
    echo "  -l              build locationsDB\n";
    echo "  -a              build airportsDB\n";
    echo "  -f <file>       use <file> as input\n";
    echo "  -s              save downloaded file to disk\n";
    echo "  -t <dbtype>     type of the DB to be used\n";
    echo "  -r <dbprotocol> protocol -----\"----------\n";
    echo "  -d <dbname>     name ---------\"----------\n";
    echo "  -u <dbuser>     user ---------\"----------\n";
    echo "  -p <dbpass>     pass ---------\"----------\n";
    echo "  -h <dbhost>     host ---------\"----------\n";
    echo "  -o <dboptions>  options ------\"----------\n";
    echo "                  in the notation option=value,...\n";
    echo "  -v              display verbose debugging messages\n";
    echo "                  multiple -v increases verbosity\n";
    exit(255);
}

// check, if zlib is available
if (extension_loaded("zlib")) {
    $open  = "gzopen";
    $close = "gzclose";
    $files = array(
        $userFile, "nsd_".$filePart, "nsd_".$filePart.".txt",
        "nsd_".$filePart.".gz", "http://weather.noaa.gov/data/nsd_".$filePart.".gz"
    );
} else {
    $open  = "fopen";
    $close = "fclose";
    $files = array(
        $userFile, "nsd_".$filePart, "nsd_".$filePart.".txt",
        "http://weather.noaa.gov/data/nsd_".$filePart.".txt"
    );
}
// then try to open a source in the given order
foreach ($files as $file) {
    $fp = @$open($file, "rb");
    if ($fp) {
        // found a valid source
        if ($verbose > 0) {
            echo "Services_Weather: Using '".$file."' as source.\n";
        }
        if ($saveFile && !file_exists($file)) {
            // apparently we want to save the file, and it's a remote file
            $file = basename($file);
            $fps = @$open($file, "wb");
            if (!$fps) {
                echo "Services_Weather: Couldn't save to '".$file."'!\n";
            } else {
                if ($verbose > 0) {
                    echo "Services_Weather: Saving source to '".$file."'.\n";
                }
                // read from filepointer and save to disk
                while ($line = fread($fp, 1024)) {
                    fwrite($fps, $line, strlen($line));
                }
                // unfortunately zlib does not support r/w on a resource,
                // so no rewind -> move $fp to new file on disk
                $close($fp);
                $close($fps);
                $fp = @$open($file, "rb");
            }
        }
        break;
    }
}
if (!$fp) {
    // no files found, or connection not available... bail out
    die("Services_Weather: Sourcefile nsd_".$filePart." not found!\n");
}

$dsn     = $dbType."://".$dbUser.":".$dbPass."@".$dbProt."+".$dbHost."/".$dbName;
$dsninfo = array(
    "phptype"  => $dbType,
    "protocol" => $dbProt,
    "username" => $dbUser,
    "password" => $dbPass,
    "hostspec" => $dbHost,
    "database" => $dbName,
    "mode"     => 0644
);

$db  = DB::connect($dsninfo, $dbOptions);
if (DB::isError($db)) {
    echo "Services_Weather: Connection to DB with '".$dbType."://".$dbUser.":PASS@".$dbHost."/".$dbName."' failed!\n";
    die($db->getMessage()."\n");
} else {
    // Test, if we have to swipe or create the table first
    $select = "SELECT * FROM ".$tableName;
    $result = $db->query($select);

    if (DB::isError($result)) {
        // Create new table
        $create = "CREATE TABLE ".$tableName."(id int,block int,station int,icao varchar(4),name varchar(80),state varchar(2),country varchar(50),wmo int,latitude float,longitude float,elevation float,x float,y float,z float)";
        if ($verbose > 0) {
            echo "Services_Weather: Creating table '".$tableName."'.\n";
        }
        $result  = $db->query($create);
        if (DB::isError($result)) {
            die($result->getMessage()."\n");
        }
    } else {
        // Delete the old stuff
        $delete = "DELETE FROM ".$tableName;
        if ($verbose > 0) {
            echo "Services_Weather: Deleting from table '".$tableName."'.\n";
        }
        $result = $db->query($delete);
        if (DB::isError($result)) {
            die($result->getMessage()."\n");
        }
    }

    // Ok, DB should be up and running now, let's shove in the data
    $line   = 0;
    $error  = 0;
    // read data from file
    while ($data = fgetcsv($fp, 1000, ";")) {
        // Check for valid data
        if ((sizeof($data) < 9) || !Services_Weather_checkData($data, $dataOrder)) {
                echo "Services_Weather: Invalid data in file!\n";
                echo "\tLine ".($line + 1).": ".implode(";", $data)."\n";
                $error++;
        } else {
            // calculate latitude and longitude
            // it comes in a ddd-mm[-ss]N|S|E|W format
            $coord = array( "latitude" => 7, "longitude" => 8);
            foreach ($coord as $latlon => $aId) {
                preg_match("/^(\d{1,3})-(\d{1,2})(-(\d{1,2}))?([NSEW])$/", $data[$aId], $result);
                ${$latlon} = 0; $factor = 1;
                foreach ($result as $var) {
                    if ((strlen($var) > 0) && ctype_digit($var)) {
                        ${$latlon} += $var / $factor;
                        $factor *= 60;
                    } elseif (ctype_alpha($var) && in_array($var, array("S", "W"))) {
                        ${$latlon} *= (-1);
                    }
                }
            }

            // Calculate the cartesian coordinates for latitude and longitude
            $theta = deg2rad($latitude);
            $phi   = deg2rad($longitude);

            $x = SERVICES_WEATHER_RADIUS_EARTH * cos($phi) * cos($theta);
            $y = SERVICES_WEATHER_RADIUS_EARTH * sin($phi) * cos($theta);
            $z = SERVICES_WEATHER_RADIUS_EARTH             * sin($theta);

            // Check for elevation in data
            $elevation = is_numeric($data[11]) ? $data[11] : 0;

            // integers: convert "--" fields to null, empty fields to 0
            foreach (array($dataOrder["b"], $dataOrder["s"], 6) as $i) {
                if (strpos($data[$i], "--") !== false) { 
                    $data[$i] = "null"; 
                } elseif ($data[$i] == "") { 
                    $data[$i] = 0; 
                }
            }

            // strings: quote
            foreach (array($dataOrder["i"], 3, 4, 5) as $i) {
                $data[$i] = $db->quote($data[$i]);
            }

            // insert data
            $insert  = "INSERT INTO ".$tableName." VALUES(".($line - $error).",";
            $insert .= $data[$dataOrder["b"]].",".$data[$dataOrder["s"]].",";
            $insert .= $data[$dataOrder["i"]].",".$data[3].",".$data[4].",";
            $insert .= $data[5].",".$data[6].",".round($latitude, 4).",";
            $insert .= round($longitude, 4).",".$elevation.",".round($x, 4).",";
            $insert .= round($y, 4).",".round($z, 4).")";

            $result = $db->query($insert);
            if (DB::isError($result)) {
                echo "\tLine ".($line + 1).": ".$insert."\n";
                echo $result->getMessage()."\n";
                $error++;
            } elseif($verbose > 2) {
                echo $insert."\n";
            }
        }
        $line++;
    }
    // commit and close
    $db->disconnect();
    if ($verbose > 0 || $error > 0) {
        echo "Services_Weather: ".($line - $error)." ".$tableName." added ";
        echo "to database '".$dbName."' (".$error." error(s)).\n";
    }
}
$close($fp);
?>
