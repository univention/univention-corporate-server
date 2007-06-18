<?php
require_once "Date/Calc.php";

/**
 * Test dates from 1970 to 2029
 * Data from: http://www.merlyn.demon.co.uk/wknotest.txt
 * Others usefull datas available from:
 * http://www.merlyn.demon.co.uk/#dat
 */
$failed_test_data   = false;
$wkno   = file('wknotest.txt');
$cnt    = sizeof($wkno);
for( $i=0;$i<$cnt;$i++ ){
    $parts      = explode(':',$wkno[$i]);
    $weeksno[$parts[0]] = str_replace("\n",'',$parts[1]);
}
unset($wkno);
foreach($weeksno as $date=>$iso){
    $year       = substr($date,0,4);
    $month      = substr($date,4,2);
    $day        = substr($date,6);
    $iso9601 = Date_Calc::gregorianToISO($day,$month,$year);
    if($iso9601!=$iso){
        $failed_test_data   = true;
        echo $date . '(' . $iso . ') =>' . $year.'-'.$month.'-'.$day .'=>' . $iso9601 . " : failed\n";
    }
}

/**
 * Bugs #19788
 */
$failed_test_19788  = false;
$pass1  = 2==Date_Calc::weekOfYear(5,1,1998)?true:false;
$pass2  = 2==Date_Calc::weekOfYear(6,1,1998)?true:false;
$pass3  = 2==Date_Calc::weekOfYear(5,1,2004)?true:false;
$pass4  = 2==Date_Calc::weekOfYear(6,1,2004)?true:false;
if( !($pass1 && $pass2 && $pass3 && $pass4) ){
    $failed_test_19788   = true;
    echo "Test Bug 19788 failed.\n";
}

if($failed_test_19788 || $failed_test_data){
    echo "Tests failed\n";
} else {
    echo "End test, succesfully passed\n";
}
?>