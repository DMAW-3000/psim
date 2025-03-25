
; external variables
BDISK		EQU	00004H
MAXB		EQU 00006H
FCB			EQU 0005CH
BUFF		EQU	00080H

; ROM MON calls
__READIN 	EQU 0F806H
__CONOUT 	EQU 0F809H

; external procedures
MON1:
	MOV A,E			; function code in E
	CPI 2
	JZ  __CONOUT	; conout - character in C
	CPI 9
	JZ  __STROUT	; emulate CP/M string output
	RET

MON2:
	MOV A,E			; function code in E
	CPI 3
	JZ  __READTAPE
	MVI E,0FFH
	RET

__READTAPE:
	CALL __READIN	; readerf - character returned in A
	MOV E,A			
	RET

__STROUT:
	MOV L,C			; string address in B,C
	MOV H,B
__STROUT1:
	MOV A,M			; load next character
	CPI '$'
	RZ				; string end
	MOV C,A
	CALL __CONOUT	; character in C
	INX H
	JMP __STROUT1
