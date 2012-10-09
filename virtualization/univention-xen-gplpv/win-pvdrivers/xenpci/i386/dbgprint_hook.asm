
.586P
.model	flat

public _Int2dHandlerNew@0
public _Int2dHandlerOld

extern _Int2dHandlerProc@20 : near

.code

_Int2dHandlerNew@0 proc
	pushfd
	push	eax
	push	ecx
	push	edx
	push	edi
	push	ebx
	push	edx
	push	ecx
	push	eax
	call	_Int2dHandlerProc@20
	pop edx
	pop ecx
	pop eax
	popfd
	jmp dword ptr cs:[_Int2dHandlerOld]
_Int2dHandlerNew@0 endp

.data
_Int2dHandlerOld DWORD 1

END
