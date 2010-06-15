<html>
<body>
<!--
    $Id: index.tpl,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $
-->

<style>
    td\{padding:5px;\}
</style>

{if(@$methodCall)}
    <font color="red">
        {if( @$methodFailed )}
            ERROR
        {else}
            OK
        <br>
        call: ${$methodCall}<br>
        method returned: {print_r($result)}
    </font>

<form action="{$_SERVER['PHP_SELF']}" method="post" name="myForm">
<input type="hidden" name="fid" value="{$_REQUEST['fid']}">

<table border="1" align="left">
    <tr>
        <td colspan="3">
            path<br>
            {foreach( $path as $index=>$aFolder )}
                <a href="{$_SERVER['PHP_SELF']}?fid={$aFolder['id']}">{$aFolder['name']}</a> /
        </td>
    </tr>

    <tr>
        <td rowspan="20" valign="top">
            children<br>
            {foreach( $children as $aChild )}
                <a href="{$_SERVER['PHP_SELF']}?fid={$aChild['id']}">{$aChild['name']}</a><br>
        </td>

    <!--
    |      add folder
    +-->
        <th colspan="2">
            <input type="hidden" name="parentId" value="{$aFolder['id']}">
            add folder under '{$aFolder['name']}'
        </th>
    </tr>

    <tr>
        <td>&nbsp;</td>
        <td>
            <select name="prevId">
                {%copy block childrenAsOptions here %}
            </select>
        </td>
    </tr>
    <tr>
        <td>name</td>
        <td><input name="newData[name]"></td>
    </tr>
    <tr>
        <td>comment</td>
        <td><textarea name="newData[comment]" cols="50" rows="3"></textarea></td>
    </tr>
    <tr>
        <td colspan="2" align="center"><input type="submit" name="action_add" value="add"></td>
    </tr>

    <!--
    |      remove folder
    +-->
    <tr>
        <th colspan="2">
            remove folder
        </th>
    </tr>
    <tr>
        <td>name</td>
        <td>
            <select name="removeId" onChange="updateComment(this.value)">
                {%copy block childrenAsRemoveOptions here %}
            </select>
        </td>
    </tr>
    <tr>
        <td>comment</td>
        <td><textarea name="removeData[comment]" cols="50" rows="3" readonly></textarea></td>
    </tr>
    <tr>
        <td colspan="2" align="center"><input type="submit" name="action_remove" value="remove"></td>
    </tr>
    <!--
    |      update folder
    +-->
    <tr>
        <th colspan="2">
            update folder
        </th>
    </tr>
    <tr>
        <td>name</td>
        <td>
            <select name="updateId" onChange="updateComment(this.value)">
                {%copy block childrenAsRemoveOptions here %}
            </select>
        </td>
    </tr>
    <tr>
        <td>name</td>
        <td><input name="updateData[name]"></td>
    </tr>
    <tr>
        <td>comment</td>
        <td><textarea name="updateData[comment]" cols="50" rows="3"></textarea></td>
    </tr>
    <tr>
        <td colspan="2" align="center"><input type="submit" name="action_update" value="update"></td>
    </tr>
    <!--
    |      move folder
    +-->
    <tr>
        <th colspan="2">
            move folder
        </th>
    </tr>
    <tr>
        <td>name</td>
        <td>
            <select name="move_id">
                {%copy block treeAsOptions here %}
            </select>
            under parent
            <select name="move_newParentId">
                <option value="0"></option>
                {%copy block treeAsOptions here %}
            </select>
            or behind
            <select name="move_newPrevId">
                <option value="0"></option>
                {%copy block treeAsOptions here %}
            </select>
        </td>
    </tr>
    <tr>
        <td colspan="2" align="center"><input type="submit" name="action_move" value="move"></td>
    </tr>
</table>

the entire tree (depth={$treeDepth}):<br><br>
{foreach($entireTree as $aNode)}
    &nbsp;
    {%repeat $aNode['level']%}
        -
    <a href="{$_SERVER['PHP_SELF']}?fid={$aNode['id']}">{$aNode['name']}</a>
    (id={$aNode['id']})<br>


</form>

<script>
    function updateComment(id)
    \{
        var comments = new Array();
        {foreach( $children as $aChild )}
            comments[{$aChild['id']}] = "{echo addslashes($aChild['comment'])}";
        document.myForm["updateData[comment]"].value = comments[id];
        document.myForm["removeData[comment]"].value = comments[id];
    \}
</script>

</body>
</html>








{%block childrenAsOptions%}
    <option value="0">as first</option>
    {foreach( $children as $aChild )}
        <option value="{$aChild['id']}">after '{$aChild['name']}'</option>
{%/block%}


{%block childrenAsRemoveOptions%}
    {foreach( $children as $aChild )}
        <option value="{$aChild['id']}">{$aChild['name']}</option>
{%/block%}

{%block treeAsOptions%}
    {foreach( $entireTree as $aNode )}
        <option value="{$aNode['id']}">
        {%repeat $aNode['level']%}
            -
        {$aNode['name']}
        </option>
{%/block%}

