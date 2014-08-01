
.586P
.model	flat

public _MoveTprToEax@0
public _MoveTprToEcx@0
public _MoveTprToEdx@0
public _MoveTprToEsi@0
public _PushTpr@0
public _MoveEaxToTpr@0
public _MoveEbxToTpr@0
public _MoveEcxToTpr@0
public _MoveEdxToTpr@0
public _MoveEsiToTpr@0
public _MoveConstToTpr@4
public _MoveZeroToTpr@0

extern _ReadTpr@0 : near
extern _WriteTpr@4 : near
.code

_MoveTprToEax@0 proc
	pushfd
	cli
	push	ecx
	push	edx
	call	_ReadTpr@0
	pop	edx
	pop	ecx
	popfd
	ret
_MoveTprToEax@0 endp

_MoveTprToEcx@0 proc
	pushfd
	cli
	push	eax
	push	edx
	call	_ReadTpr@0
	mov	ecx, eax
	pop	edx
	pop	eax
	popfd
	ret
_MoveTprToEcx@0 endp

_MoveTprToEdx@0 proc
	pushfd
	cli
	push	eax
	push	ecx
	call	_ReadTpr@0
	mov	edx, eax
	pop	ecx
	pop	eax
	popfd
	ret
_MoveTprToEdx@0 endp

_MoveTprToEsi@0 proc
	pushfd
	cli
	push	eax
	push	ecx
	push	edx
	call	_ReadTpr@0
	mov	esi, eax
	pop	edx
	pop	ecx
	pop	eax
	popfd
	ret
_MoveTprToEsi@0 endp

_PushTpr@0 proc
	sub	esp, 4
	pushfd
	cli
	push	eax
	push	ecx
	push	edx
	mov	eax, dword ptr [esp + 20]
	mov	dword ptr [esp + 16], eax
	call	_ReadTpr@0
	mov	dword ptr [esp + 20], eax
	pop	edx
	pop	ecx
	pop	eax
	popfd
	ret
_PushTpr@0 endp

_MoveEaxToTpr@0 proc
	pushfd
	cli
	push	eax
	push	ecx
	push	edx
	push	eax
	call	_WriteTpr@4
	pop edx
	pop ecx
	pop eax
	popfd
	ret
_MoveEaxToTpr@0 endp

_MoveEbxToTpr@0 proc
	pushfd
	cli
	push	eax
	push	ecx
	push	edx
	push	ebx
	call	_WriteTpr@4
	pop edx
	pop ecx
	pop eax
	popfd
	ret
_MoveEbxToTpr@0 endp

_MoveEcxToTpr@0 proc
	pushfd
	cli
	push	eax
	push	ecx
	push	edx
	push	ecx
	call	_WriteTpr@4
	pop edx
	pop ecx
	pop eax
	popfd
	ret
_MoveEcxToTpr@0 endp

_MoveEdxToTpr@0 proc
	pushfd
	cli
	push	eax
	push	ecx
	push	edx
	push	edx
	call	_WriteTpr@4
	pop edx
	pop ecx
	pop eax
	popfd
	ret
_MoveEdxToTpr@0 endp

_MoveEsiToTpr@0 proc
	pushfd
	cli
	push	eax
	push	ecx
	push	edx
	push	esi
	call	_WriteTpr@4
	pop edx
	pop ecx
	pop eax
	popfd
	ret
_MoveEsiToTpr@0 endp

_MoveConstToTpr@4 proc
	pushfd
	cli
	push	eax
	push	ecx
	push	edx
	mov	eax, [esp + 20]
	push	eax
	call	_WriteTpr@4
	pop edx
	pop ecx
	pop eax
	popfd
	ret 4
_MoveConstToTpr@4 endp

_MoveZeroToTpr@0 proc
	pushfd
	cli
	push	eax
	push	ecx
	push	edx
	push	0
	call	_WriteTpr@4
	pop edx
	pop ecx
	pop eax
	popfd
	ret
_MoveZeroToTpr@0 endp

END
