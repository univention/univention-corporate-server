<script type="text/javascript">
function doSearch(tagName)
{
    ajaxurl = '<?php echo Horde::applicationUrl('services/portal/cloud_search.php', true)?>';
    params = 'tag=' + tagName;

    $('cloudloadingimg').show();
    new Ajax.Request(ajaxurl,
                    {
                        method: 'post',
                        parameters: params,
                        onSuccess: function(transport)
                        {
                            $('cloudsearch').innerHTML = transport.responseText;
                            $('cloudsearch').show();
                            $('cloudloadingimg').hide();
                        },
                        onFailure: function(transport)
                        {
                            $('cloudloadingimg').hide();
                        }
                    });


}
</script>
