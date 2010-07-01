/* This compressed file is part of Xinha. For uncompressed sources, forum, and bug reports, go to xinha.org */
/* This file is part of version 0.95 released Mon, 12 May 2008 17:33:15 +0200 */
/* The URL of the most recent version of this file is http://svn.xinha.webfactional.com/trunk/plugins/CharacterMap/character-map.js */
Xinha.loadStyle("CharacterMap.css","CharacterMap");
function CharacterMap(_1){
this.editor=_1;
var _2=_1.config;
var _3=this;
_2.registerButton({id:"insertcharacter",tooltip:Xinha._lc("Insert special character","CharacterMap"),image:_1.imgURL("ed_charmap.gif","CharacterMap"),textMode:false,action:function(_4){
_3.buttonPress(_4);
}});
_2.addToolbarElement("insertcharacter","createlink",-1);
if(_2.CharacterMap.mode=="panel"){
_1._CharacterMap=_1.addPanel("right");
Xinha._addClass(_1._CharacterMap,"CharacterMap");
_1.notifyOn("modechange",function(e,_6){
if(_6.mode=="text"){
_1.hidePanel(_1._CharacterMap);
}
});
var _7=["&Yuml;","&scaron;","&#064;","&quot;","&iexcl;","&cent;","&pound;","&curren;","&yen;","&brvbar;","&sect;","&uml;","&copy;","&ordf;","&laquo;","&not;","&macr;","&deg;","&plusmn;","&sup2;","&sup3;","&acute;","&micro;","&para;","&middot;","&cedil;","&sup1;","&ordm;","&raquo;","&frac14;","&frac12;","&frac34;","&iquest;","&times;","&Oslash;","&divide;","&oslash;","&fnof;","&circ;","&tilde;","&ndash;","&mdash;","&lsquo;","&rsquo;","&sbquo;","&ldquo;","&rdquo;","&bdquo;","&dagger;","&Dagger;","&bull;","&hellip;","&permil;","&lsaquo;","&rsaquo;","&euro;","&trade;","&Agrave;","&Aacute;","&Acirc;","&Atilde;","&Auml;","&Aring;","&AElig;","&Ccedil;","&Egrave;","&Eacute;","&Ecirc;","&Euml;","&Igrave;","&Iacute;","&Icirc;","&Iuml;","&ETH;","&Ntilde;","&Ograve;","&Oacute;","&Ocirc;","&Otilde;","&Ouml;","&reg;","&times;","&Ugrave;","&Uacute;","&Ucirc;","&Uuml;","&Yacute;","&THORN;","&szlig;","&agrave;","&aacute;","&acirc;","&atilde;","&auml;","&aring;","&aelig;","&ccedil;","&egrave;","&eacute;","&ecirc;","&euml;","&igrave;","&iacute;","&icirc;","&iuml;","&eth;","&ntilde;","&ograve;","&oacute;","&ocirc;","&otilde;","&ouml;","&divide;","&oslash;","&ugrave;","&uacute;","&ucirc;","&uuml;","&yacute;","&thorn;","&yuml;","&OElig;","&oelig;","&Scaron;"];
for(var i=0;i<_7.length;i++){
this.addEntity(_7[i],i);
}
_1.hidePanel(_1._CharacterMap);
}
}
Xinha.Config.prototype.CharacterMap={"mode":"popup"};
CharacterMap._pluginInfo={name:"CharacterMap",version:"2.0",developer:"Laurent Vilday",developer_url:"http://www.mokhet.com/",c_owner:"Xinha community",sponsor:"",sponsor_url:"",license:"Creative Commons Attribution-ShareAlike License"};
CharacterMap._isActive=false;
CharacterMap.prototype.buttonPress=function(_9){
var _a=_9.config;
if(_a.CharacterMap.mode=="panel"){
if(this._isActive){
this._isActive=false;
_9.hidePanel(_9._CharacterMap);
}else{
this._isActive=true;
_9.showPanel(_9._CharacterMap);
}
}else{
_9._popupDialog("plugin://CharacterMap/select_character",function(_b){
if(!_b){
return false;
}
if(Xinha.is_ie){
_9.focusEditor();
}
_9.insertHTML(_b);
},null);
}
};
CharacterMap.prototype.addEntity=function(_c,_d){
var _e=this.editor;
var _f=this;
var a=document.createElement("a");
Xinha._addClass(a,"entity");
a.innerHTML=_c;
a.href="javascript:void(0)";
Xinha._addClass(a,(_d%2)?"light":"dark");
a.onclick=function(){
if(Xinha.is_ie){
_e.focusEditor();
}
_e.insertHTML(_c);
return false;
};
_e._CharacterMap.appendChild(a);
a=null;
};

