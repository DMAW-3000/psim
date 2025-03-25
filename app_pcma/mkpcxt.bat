..\..\asw\bin\asw -g -cpu 8086 pcxtbios.asm
..\..\asw\bin\p2hex -F Moto pcxtbios.p

..\..\asw\bin\asw -g -cpu 8086 pcxtboot.asm
..\..\asw\bin\p2hex -F Moto -l 16 pcxtboot.p
