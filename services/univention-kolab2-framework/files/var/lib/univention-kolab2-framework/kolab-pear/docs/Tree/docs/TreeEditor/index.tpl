<!--
    $Id: index.tpl,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $
-->

<html>
<body>
<style>
    body, table.simple
    \{
        font-family : verdana, geneva, arial;
        font-size : 11px;
        background-color: #DCDCDC;
    \}
    table,td, input
    \{
        background-color: white;
    \}
    input.button,img.button
    \{
        border: 1px outset black;
    \}
    td.selected
    \{
        background-color: lightblue;
    \}
    a
    \{
        color: red;
        text-decoration: none;
    \}

</style>

<form method="post" action="{$_SERVER['PHP_SELF']}">

    {if(@$session->action == 'cut')}
        <img src="cut"> &nbsp;
        <img src="copy"> &nbsp;
    {else}
        <input id="cut" src="cut" name="action_cut" type="image" class="button" onmousedown="document.getElementById('cut').style.border='1px inset black'" alt="cut" name="cut" title="cut"> &nbsp;
        <input id="copy" src="copy" name="action_copy" type="image" class="button" onmousedown="document.getElementById('copy').style.border='1px inset black'" title="copy"> &nbsp;
    <input id="paste" src="paste" name="action_paste" type="image" class="button" onmousedown="document.getElementById('paste').style.border='1px inset black'" title="paste"> &nbsp;

    <img src="" width="1" height="22" class="button"> &nbsp;

    {if(@$session->action == 'cut')}
        <img src="delete"> &nbsp;
    {else}
        <input id="delete" src="delete" name="action_delete" type="image" class="button" onmousedown="document.getElementById('delete').style.border='1px inset black'" title="delete">

    &nbsp;
    <img src="" width="1" height="22" class="button"> &nbsp;

    &nbsp;
    work on: &nbsp;
    <input type="submit" value="DB" name="use_DB">
    &nbsp;
    <input type="submit" value="Filesystem" name="use_Filesystem">
    &nbsp;
    <input type="submit" value="XML" name="use_XML">
    &nbsp;
    <input type="submit" value="Array" name="use_Array">

    <br><br>

    current tree instanciation used:
    <code>
    {if( @$session->use == 'DB' )}
        $tree = new treeClass( 'DBnested' , 'mysql://root@localhost/test' , array('table'=&gt;TABLE_TREE , 'order' =&gt;  'name') );
    {else}
        $tree = new treeClass( 'Filesystem' , '/home/cain/tmp' ,array('order' =&gt;  'name') );
    </code>

    <hr>

    <table align="left">
        {foreach( $allVisibleFolders as $aFolder )}
            { $class=''}
            {if( in_array($aFolder['id'],$session->data) )}
                { $class=' class="selected"'}
            <tr>
                <td {$class}>
                    {if( @$session->action == 'cut')}
                        <input type="radio" name="moveDest" value="{$aFolder['id']}">
                    {else}
                        <input type="checkbox" name="selectedNodes[]" value="{$aFolder['id']}">
                </td>
                <td {$class}>
                    {%tree_showNode($aFolder)%}
                </td>
            </tr>
    </table>

    {if( @$session->action!='cut' )}
        <table class="simple" border="1">
            <tr>
                <th colspan="2">Add Folder</th>
            </tr>
            <tr>
                <td colspan="2">
                    Choose the parent folder on the left side,
                    <br>
                    under which the new folder shall be created!
                </td>
            </tr>
            <tr>
                <td>Name</td>
                <td>
                    <input name="newFolder[name]">
                </td>
            </tr>
            <tr>
                <td>&nbsp;</td>
                <td>
                    <input type="submit" name="action_add" value="add">
                </td>
            </tr>
        </table>



    {if(@$session->action=='cut')}
        You have chosen 'CUT', those folders are in the clipboard now.<br>
        Please select the destination and push the 'PASTE' button! <img class="button" src="paste">
        <br>
    {if(@$session->action=='copy')}
        You have chosen 'COPY', those folders are in the clipboard now.<br>
        Please select the destination and push the 'PASTE' button! <img class="button" src="paste"><br>
        Or choose other folder(s) that you want to put in the clipboard.
        <br>


    {if(@$results)}
        <font color="red">
            {if( @$methodFailed )}
                ERROR
            {else}
                OK
            <br>
        </font>
        {if(sizeof($methodCalls))}
            <table class="simple" border="1">
                <tr>
                    <th>methods called</th>
                    <th>returned</th>
                </tr>
                {foreach( $methodCalls as $key=>$aCall)}
                    <tr>
                        <td nowrap>{$aCall}</td>
                        <td align="center">
                            {if(PEAR::isError($results[$key]))}
                                <font color="red">{$results[$key]->getMessage()}</font>
                                <br>
                            {print_r($results[$key])}
                        </td>
                    </tr>
            </table>
        {else}
            <font color="red">
                {print_r($results)}
            </font>




</form>

<script type="text/javascript" language="JavaScript" src="{$config->vApplRoot}/external/calendar/popcalendar.js.php"></script>

</body>
</html>







<!--
    this macro shows a node for the explorer view

    @param  array   the current project
-->
{%macro tree_showNode($aNode)%}
    {global $tree,$session}

    {%repeat $aNode['level'] times%}
        &nbsp; &nbsp;

    {if( $tree->hasChildren($aNode['id']) )}
        <a href="{$_SERVER['PHP_SELF']}?unfold={$aNode['id']}">
            {if(@$session->temp->openProjectFolders[$aNode['id']])}
                <img src="openFolder" border="0"></a>
            {else}
                <img src="closedFolder" border="0"></a>
    {else}
        <img src="folder">

    &nbsp;
    <b>
        {if( $tree->getRootId() == $aNode['id'] )}
            ...{echo substr($aNode['name'],-28)}
        {else}
            {$aNode['name']}
    </b>

    {if( $tree->getRootId() == $aNode['id'] )}
        &nbsp; <a href="{$_SERVER['PHP_SELF']}?unfoldAll=true" title="unfold all">++</a>
