/* This compressed file is part of Xinha. For uncompressed sources, forum, and bug reports, go to xinha.org */
/* This file is part of version 0.95 released Mon, 12 May 2008 17:33:15 +0200 */
/* The URL of the most recent version of this file is http://svn.xinha.webfactional.com/trunk/modules/Dialogs/panel-dialog.js */
Xinha.PanelDialog=function(_1,_2,_3,_4){
this.id={};
this.r_id={};
this.editor=_1;
this.document=document;
this.rootElem=_1.addPanel(_2);
var _5=this;
if(typeof _4=="function"){
this._lc=_4;
}else{
if(_4){
this._lc=function(_6){
return Xinha._lc(_6,_4);
};
}else{
this._lc=function(_7){
return _7;
};
}
}
_3=_3.replace(/\[([a-z0-9_]+)\]/ig,function(_8,id){
if(typeof _5.id[id]=="undefined"){
_5.id[id]=Xinha.uniq("Dialog");
_5.r_id[_5.id[id]]=id;
}
return _5.id[id];
}).replace(/<l10n>(.*?)<\/l10n>/ig,function(_a,_b){
return _5._lc(_b);
}).replace(/="_\((.*?)\)"/g,function(_c,_d){
return "=\""+_5._lc(_d)+"\"";
});
this.rootElem.innerHTML=_3;
};
Xinha.PanelDialog.prototype.show=function(_e){
this.setValues(_e);
this.editor.showPanel(this.rootElem);
};
Xinha.PanelDialog.prototype.hide=function(){
this.editor.hidePanel(this.rootElem);
return this.getValues();
};
Xinha.PanelDialog.prototype.onresize=Xinha.Dialog.prototype.onresize;
Xinha.PanelDialog.prototype.toggle=Xinha.Dialog.prototype.toggle;
Xinha.PanelDialog.prototype.setValues=Xinha.Dialog.prototype.setValues;
Xinha.PanelDialog.prototype.getValues=Xinha.Dialog.prototype.getValues;
Xinha.PanelDialog.prototype.getElementById=Xinha.Dialog.prototype.getElementById;
Xinha.PanelDialog.prototype.getElementsByName=Xinha.Dialog.prototype.getElementsByName;

