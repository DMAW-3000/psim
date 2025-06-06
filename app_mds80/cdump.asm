;	FILE DUMP PROGRAM, READS AN INPUT FILE AND PRINTS IN HEX
;
;	COPYRIGHT (C) 1975, 1976, 1977, 1978
;	DIGITAL RESEARCH
;	BOX 579, PACIFIC GROVE
;	CALIFORNIA, 93950
;
	ORG	100H
BDOS	EQU	0005H	;DOS ENTRY POINT
CONS	EQU	1	;READ CONSOLE
TYPEF	EQU	2	;TYPE FUNCTION
PRINTF	EQU	9	;BUFFER PRINT ENTRY
BRKF	EQU	11	;BREAK KEY FUNCTION (TRUE IF CHAR READY)
OPENF	EQU	15	;FILE OPEN
READF	EQU	20	;READ FUNCTION
;
FCB	EQU	5CH	;FILE CONTROL BLOCK ADDRESS
BUFF	EQU	80H	;INPUT DISK BUFFER ADDRESS
;
;	NON GRAPHIC CHARACTERS
CR	EQU	0DH	;CARRIAGE RETURN
LF	EQU	0AH	;LINE FEED
;
;	FILE CONTROL BLOCK DEFINITIONS
FCBDN	EQU	FCB+0	;DISK NAME
FCBFN	EQU	FCB+1	;FILE NAME
FCBFT	EQU	FCB+9	;DISK FILE TYPE (3 CHARACTERS)
FCBRL	EQU	FCB+12	;FILE'S CURRENT REEL NUMBER
FCBRC	EQU	FCB+15	;FILE'S RECORD COUNT (0 TO 128)
FCBCR	EQU	FCB+32	;CURRENT (NEXT) RECORD NUMBER (0 TO 127)
FCBLN	EQU	FCB+33	;FCB LENGTH
;
;	SET UP STACK
	LXI	H,0
	DAD	SP
;	ENTRY STACK POINTER IN HL FROM THE CCP
	SHLD	OLDSP
;	SET SP TO LOCAL STACK AREA (RESTORED AT FINIS)
	LXI	SP,STKTOP
;	READ AND PRINT SUCCESSIVE BUFFERS
	CALL	SETUP	;SET UP INPUT FILE
BRP:
	CPI	255	;255 IF FILE NOT PRESENT
	JNZ	OPENOK	;SKIP IF OPEN IS OK
;
;	FILE NOT THERE, GIVE ERROR MESSAGE AND RETURN
	LXI	D,OPNMSG
	CALL	ERR
	JMP	FINIS	;TO RETURN
;
OPENOK:	;OPEN OPERATION OK, SET BUFFER INDEX TO END
	MVI	A,80H
	STA	IBP	;SET BUFFER POINTER TO 80H
;	HL CONTAINS NEXT ADDRESS TO PRINT
	LXI	H,0	;START WITH 0000
;
GLOOP:
	PUSH	H	;SAVE LINE POSITION
	CALL	GNB
	POP	H	;RECALL LINE POSITION
	JC	FINIS	;CARRY SET BY GNB IF END FILE
	MOV	B,A
;	PRINT HEX VALUES
;	CHECK FOR LINE FOLD
	MOV	A,L
	ANI	0FH	;CHECK LOW 4 BITS
	JNZ	NONUM
;	PRINT LINE NUMBER
	CALL	CRLF
;
;	CHECK FOR BREAK KEY
	CALL	BREAK
;	ACCUM LSB = 1 IF CHARACTER READY
	RRC		;INTO CARRY
	JC	FINIS	;DON'T PRINT ANY MORE
;
	MOV	A,H
	CALL	PHEX
	MOV	A,L
	CALL	PHEX
NONUM:
	INX	H	;TO NEXT LINE NUMBER
	MVI	A,' '
	CALL	PCHAR
	MOV	A,B
	CALL	PHEX
	JMP	GLOOP
;
FINIS:
;	END OF DUMP, RETURN TO CCP
;	(NOTE THAT A JMP TO 0000H REBOOTS)
	CALL	CRLF
	LHLD	OLDSP
	SPHL
;	STACK POINTER CONTAINS CCP'S STACK LOCATION
	RET		;TO THE CCP
;
;
;	SUBROUTINES
;
BREAK:	;CHECK BREAK KEY (ACTUALLY ANY KEY WILL DO)
	PUSH H
	PUSH D
	PUSH B; ENVIRONMENT SAVED
	MVI	C,BRKF
	CALL	BDOS
	POP B
	POP D
	POP H; ENVIRONMENT RESTORED
	RET
;
PCHAR:	;PRINT A CHARACTER
	PUSH H
	PUSH D
	PUSH B; SAVED
	MVI	C,TYPEF
	MOV	E,A
	CALL	BDOS
	POP B
	POP D
	POP H; RESTORED
	RET
;
CRLF:
	MVI	A,CR
	CALL	PCHAR
	MVI	A,LF
	CALL	PCHAR
	RET
;
;
PNIB:	;PRINT NIBBLE IN REG A
	ANI	0FH	;LOW 4 BITS
	CPI	10
	JNC	P10
;	LESS THAN OR EQUAL TO 9
	ADI	'0'
	JMP	PRN
;
;	GREATER OR EQUAL TO 10
P10:	ADI	'A' - 10
PRN:	CALL	PCHAR
	RET
;
PHEX:	;PRINT HEX CHAR IN REG A
	PUSH	PSW
	RRC
	RRC
	RRC
	RRC
	CALL	PNIB	;PRINT NIBBLE
	POP	PSW
	CALL	PNIB
	RET
;
ERR:	;PRINT ERROR MESSAGE
;	D,E ADDRESSES MESSAGE ENDING WITH "$"
	MVI	C,PRINTF	;PRINT BUFFER FUNCTION
	CALL	BDOS
	RET
;
;
GNB:	;GET NEXT BYTE
	LDA	IBP
	CPI	80H
	JNZ	G0
;	READ ANOTHER BUFFER
;
;
	CALL	DISKR
	ORA	A	;ZERO VALUE IF READ OK
	JZ	G0	;FOR ANOTHER BYTE
;	END OF DATA, RETURN WITH CARRY SET FOR EOF
	STC
	RET
;
G0:	;READ THE BYTE AT BUFF+REG A
	MOV	E,A	;LS BYTE OF BUFFER INDEX
	MVI	D,0	;DOUBLE PRECISION INDEX TO DE
	INR	A	;INDEX=INDEX+1
	STA	IBP	;BACK TO MEMORY
;	POINTER IS INCREMENTED
;	SAVE THE CURRENT FILE ADDRESS
	LXI	H,BUFF
	DAD	D
;	ABSOLUTE CHARACTER ADDRESS IS IN HL
	MOV	A,M
;	BYTE IS IN THE ACCUMULATOR
	ORA	A	;RESET CARRY BIT
	RET
;
SETUP:	;SET UP FILE 
;	OPEN THE FILE FOR INPUT
	XRA	A	;ZERO TO ACCUM
	STA	FCBCR	;CLEAR CURRENT RECORD
;
	LXI	D,FCB
	MVI	C,OPENF
	CALL	BDOS
;	255 IN ACCUM IF OPEN ERROR
	RET
;
DISKR:	;READ DISK FILE RECORD
	PUSH H
	PUSH D
	PUSH B
	LXI	D,FCB
	MVI	C,READF
	CALL	BDOS
	POP B
	POP D
	POP H
	RET
;
;	FIXED MESSAGE AREA
SIGNON:	DB	'FILE DUMP VERSION 1.4$'
OPNMSG:	DB	CR,LF,'NO INPUT FILE PRESENT ON DISK$'

;	VARIABLE AREA
IBP:	DS	2	;INPUT BUFFER POINTER
OLDSP:	DS	2	;ENTRY SP VALUE FROM CCP
;
;	STACK AREA
	DS	64	;RESERVE 32 LEVEL STACK
STKTOP:
