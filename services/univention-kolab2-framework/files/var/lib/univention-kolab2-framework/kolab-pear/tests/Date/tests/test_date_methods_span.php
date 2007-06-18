<?php    
// vim: set expandtab tabstop=4 softtabstop=4 shiftwidth=4:
// +----------------------------------------------------------------------+
// | PHP Version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2003 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.02 of the PHP license,      |
// | that is bundled with this package in the file LICENSE, and is        |
// | available at through the world-wide-web at                           |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Author: Leandro Lucarella <llucax@php.net>                           |
// +----------------------------------------------------------------------+
//
// $Id: test_date_methods_span.php,v 1.1.2.1 2005/10/05 14:39:49 steuwer Exp $
//

require_once 'Date.php';
require_once 'Date/Span.php';

$date = new Date();
$tmp = new Date($date);

printf("Actual date: %s\n", $date->getDate(DATE_FORMAT_ISO));

$tmp->copy($date);
$tmp->subtractSpan(new Date_Span('0:00:00:05'));
printf("Subtracting 5 seconds: %s\n", $tmp->getDate(DATE_FORMAT_ISO));

$tmp->copy($date);
$tmp->subtractSpan(new Date_Span('0:00:20:00'));
printf("Subtracting 20 minutes: %s\n", $tmp->getDate(DATE_FORMAT_ISO));

$tmp->copy($date);
$tmp->subtractSpan(new Date_Span('0:10:00:00'));
printf("Subtracting 10 hours: %s\n", $tmp->getDate(DATE_FORMAT_ISO));

$tmp->copy($date);
$tmp->subtractSpan(new Date_Span('3:00:00:00'));
printf("Subtracting 3 days: %s\n", $tmp->getDate(DATE_FORMAT_ISO));

$tmp->copy($date);
$tmp->subtractSpan(new Date_Span('3:10:20:05'));
printf("Subtracting 3 days, 10 hours, 20 minutes and 5 seconds: %s\n", $tmp->getDate(DATE_FORMAT_ISO));

$tmp->copy($date);
$tmp->addSpan(new Date_Span('0:00:00:05'));
printf("Adding 5 seconds: %s\n", $tmp->getDate(DATE_FORMAT_ISO));

$tmp->copy($date);
$tmp->addSpan(new Date_Span('0:00:20:00'));
printf("Adding 20 minutes: %s\n", $tmp->getDate(DATE_FORMAT_ISO));

$tmp->copy($date);
$tmp->addSpan(new Date_Span('0:10:00:00'));
printf("Adding 10 hours: %s\n", $tmp->getDate(DATE_FORMAT_ISO));

$tmp->copy($date);
$tmp->addSpan(new Date_Span('3:00:00:00'));
printf("Adding 3 days: %s\n", $tmp->getDate(DATE_FORMAT_ISO));

$tmp->copy($date);
$tmp->addSpan(new Date_Span('3:10:20:05'));
printf("Adding 3 days, 10 hours, 20 minutes and 5 seconds: %s\n", $tmp->getDate(DATE_FORMAT_ISO));

?>
