
RAM_ADDR	EQU		$000900
ROM_ADDR	EQU		$020000

	ORG	$7f00
	
TLOAD	LEA		RAM_ADDR,A0		; RAM addr
		LEA		ROM_ADDR,A1		; ROM addr
		MOVE.L	(A1)+,D1		; length is first long in ROM
		LSR.L	#2,D1			; length in longs
		ADDQ.L	#1,D1			; round up
		
TLOOP	MOVE.L	(A1)+,D0		; copy image to RAM
		MOVE.L	D0,(A0)+
		DBRA	D1,TLOOP
		
		JMP		RAM_ADDR		; go to start
		