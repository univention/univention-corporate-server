/* This compressed file is part of Xinha. For uncompressed sources, forum, and bug reports, go to xinha.org */
/* This file is part of version 0.95 released Mon, 12 May 2008 17:33:15 +0200 */
/* The URL of the most recent version of this file is http://svn.xinha.webfactional.com/trunk/plugins/ListType/list-type.js */
Xinha.loadStyle("ListType.css","ListType");
function ListType(_1){
this.editor=_1;
var _2=_1.config;
var _3=this;
if(_2.ListType.mode=="toolbar"){
var _4={};
_4[Xinha._lc("Decimal numbers","ListType")]="decimal";
_4[Xinha._lc("Lower roman numbers","ListType")]="lower-roman";
_4[Xinha._lc("Upper roman numbers","ListType")]="upper-roman";
_4[Xinha._lc("Lower latin letters","ListType")]="lower-alpha";
_4[Xinha._lc("Upper latin letters","ListType")]="upper-alpha";
if(!Xinha.is_ie){
_4[Xinha._lc("Lower greek letters","ListType")]="lower-greek";
}
var _5={id:"listtype",tooltip:Xinha._lc("Choose list style type (for ordered lists)","ListType"),options:_4,action:function(_6){
_3.onSelect(_6,this);
},refresh:function(_7){
_3.updateValue(_7,this);
},context:"ol"};
_2.registerDropdown(_5);
_2.addToolbarElement("listtype",["insertorderedlist","orderedlist"],1);
}else{
_1._ListType=_1.addPanel("right");
Xinha.freeLater(_1,"_ListType");
Xinha.addClass(_1._ListType,"ListType");
Xinha.addClass(_1._ListType.parentNode,"dialog");
_1.notifyOn("modechange",function(e,_9){
if(_9.mode=="text"){
_1.hidePanel(_1._ListType);
}
});
var _a=["disc","circle","square","none"];
var _b=["decimal","lower-alpha","upper-alpha","lower-roman","upper-roman","none"];
var _c=document.createElement("div");
_c.style.height="90px";
var _d=document.createElement("div");
this.divUL=_d;
_d.style.display="none";
for(var i=0;i<_a.length;i++){
_d.appendChild(this.createImage(_a[i]));
}
_c.appendChild(_d);
var _d=document.createElement("div");
this.divOL=_d;
_d.style.display="none";
for(var i=0;i<_b.length;i++){
_d.appendChild(this.createImage(_b[i]));
}
_c.appendChild(_d);
_1._ListType.appendChild(_c);
_1.hidePanel(_1._ListType);
}
}
Xinha.Config.prototype.ListType={"mode":"toolbar"};
ListType._pluginInfo={name:"ListType",version:"2.1",developer:"Laurent Vilday",developer_url:"http://www.mokhet.com/",c_owner:"Xinha community",sponsor:"",sponsor_url:"",license:"Creative Commons Attribution-ShareAlike License"};
ListType.prototype.onSelect=function(_f,_10){
var _11=_f._toolbarObjects[_10.id].element;
var _12=_f.getParentElement();
while(!/^ol$/i.test(_12.tagName)){
_12=_12.parentNode;
}
_12.style.listStyleType=_11.value;
};
ListType.prototype.updateValue=function(_13,_14){
var _15=_13._toolbarObjects[_14.id].element;
var _16=_13.getParentElement();
while(_16&&!/^ol$/i.test(_16.tagName)){
_16=_16.parentNode;
}
if(!_16){
_15.selectedIndex=0;
return;
}
var _17=_16.style.listStyleType;
if(!_17){
_15.selectedIndex=0;
}else{
for(var i=_15.firstChild;i;i=i.nextSibling){
i.selected=(_17.indexOf(i.value)!=-1);
}
}
};
ListType.prototype.onUpdateToolbar=function(){
if(this.editor.config.ListType.mode=="toolbar"){
return;
}
var _19=this.editor.getParentElement();
while(_19&&!/^[o|u]l$/i.test(_19.tagName)){
_19=_19.parentNode;
}
if(_19&&/^[o|u]l$/i.test(_19.tagName)){
this.showPanel(_19);
}else{
if(this.editor._ListType.style.display!="none"){
this.editor.hidePanel(this.editor._ListType);
}
}
};
ListType.prototype.createImage=function(_1a){
var _1b=this;
var _1c=this.editor;
var a=document.createElement("a");
a.href="javascript:void(0)";
Xinha._addClass(a,_1a);
Xinha._addEvent(a,"click",function(){
var _1e=_1c._ListType.currentListTypeParent;
_1e.style.listStyleType=_1a;
_1b.showActive(_1e);
return false;
});
return a;
};
ListType.prototype.showActive=function(_1f){
var _20=(_1f.tagName.toLowerCase()=="ul")?this.divUL:this.divOL;
this.divUL.style.display="none";
this.divOL.style.display="none";
_20.style.display="block";
var _21=_1f.style.listStyleType;
if(""==_21){
_21=(_1f.tagName.toLowerCase()=="ul")?"disc":"decimal";
}
for(var i=0;i<_20.childNodes.length;i++){
var elt=_20.childNodes[i];
if(Xinha._hasClass(elt,_21)){
Xinha._addClass(elt,"active");
}else{
Xinha._removeClass(elt,"active");
}
}
};
ListType.prototype.showPanel=function(_24){
this.editor._ListType.currentListTypeParent=_24;
this.showActive(_24);
this.editor.showPanel(this.editor._ListType);
};

