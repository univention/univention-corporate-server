<?php
//
//  $Log: treeClass.php,v $
//  Revision 1.1.2.1  2005/10/05 14:39:48  steuwer
//  provide more php-includes, anonymous bind for filter-scripts
//
//  Revision 1.1  2003/01/30 17:18:24  cain
//  - moved all examples to docs
//  - and make them work properly
//
//  Revision 1.1  2002/08/23 17:18:28  cain
//  - a good example to show how the tree works
//
//

require_once('Tree/Memory.php');


class treeClass extends Tree_Memory
{

    function getPathAsString( $id )
    {
        return preg_replace('/Root\s-\s/','',parent::getPathAsString( $id , ' - ' ));
    }

    /**
    *   just a wrapper to be compatible to vp_DB_Common
    *
    */
    function &getAll()
    {
        return $this->getNode();
    }

    /**
    *   this is only for the getAllVisible it is called by the walk-method
    *   to retreive only the nodes that shall be visible
    *
    *   @param      array   this is the node to check
    *   @return     mixed   an array if the node shall be visible
    *                       nothing if the node shall not be shown
    */
    function _walkForGettingVisibleFolders( $node )
    {
        global $session;

        if( $node['id']==$this->getRootId() )
            return $node;

        $parentsIds = $this->getParentsIds($node['id']);
        if( !@$this->_unfoldAll )
        {
            foreach( $parentsIds as $aParentId )
            {
                if( !@$session->temp->openProjectFolders[$aParentId] &&
                    $aParentId!=$node['id'])    // dont check the node itself, since we only look if the parents are openend, then this $node is shown!
                    return false;
            }
        }
        else
        {
            // if all folders shall be unfolded save the unfold-ids in the session
            $session->temp->openProjectFolders[$node['id']] = $node['id'];
        }
        return $node;
    }

    /**
    *   this returns all the visible projects, the folders returned
    *   are those which are unfolded, the explorer-like way
    *   it also handles the 'unfold' parameter, which we simply might be given
    *   so the unfold/fold works on every page that shows only visible folders
    *   i think that is really cool :-)
    *
    *   @return     array   only those folders which are visible
    */
    function getAllVisible()
    {
        $this->unfoldHandler();
        return $this->walk( array(&$this,'_walkForGettingVisibleFolders') , 0 , 'ifArray' );
    }

    function unfoldHandler()
    {
        global $session;

        if( @$_REQUEST['unfoldAll'] )
        {
            $this->_unfoldAll = true;
        }

        if( @$_REQUEST['unfold'] )
        {
            if( @$session->temp->openProjectFolders[$_REQUEST['unfold']] )
            {
                unset($session->temp->openProjectFolders[$_REQUEST['unfold']]);
            }
            else
            {
                $session->temp->openProjectFolders[$_REQUEST['unfold']] = $_REQUEST['unfold'];
            }
        }
    }


}

?>
