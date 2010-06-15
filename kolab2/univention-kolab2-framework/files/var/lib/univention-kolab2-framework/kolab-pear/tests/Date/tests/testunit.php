<?php
/* vim: set expandtab tabstop=4 shiftwidth=4: */
// +----------------------------------------------------------------------+
// | PHP version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2003 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.0 of the PHP license,       |
// | that is bundled with this package in the file LICENSE, and is        |
// | available through the world-wide-web at                              |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Marshall Roch <mroch@php.net>                               |
// +----------------------------------------------------------------------+
//
// $Id: testunit.php,v 1.1.2.1 2005/10/05 14:39:49 steuwer Exp $

/**
 * Displays all test cases on the same page
 *
 * @package Date
 * @author Marshall Roch <mroch@php.net>
 */


echo "<pre>";
require_once 'PHPUnit.php';
require_once 'testunit_date.php';
require_once 'testunit_date_span.php';
echo "</pre>";
?>
