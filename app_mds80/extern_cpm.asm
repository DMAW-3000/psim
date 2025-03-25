
__CPMENT	EQU 00005H

MON1:
	MOV A,E			; function code in E
	MOV E,C			; address in B,C
	MOV D,B
	MOV C,A
	JMP __CPMENT

MON2:
	MOV A,E			; function code in E
	MOV E,C			; address in B,C
	MOV D,B
	MOV C,A
	CALL __CPMENT
	MOV E,A			; return value in A
	RET

MON3:
	MOV A,E			; function code in E
	MOV E,C			; address in B,C
	MOV D,B
	MOV C,A
	CALL __CPMENT
	MOV E,A			; return value in B,A
	MOV D,B
	RET
