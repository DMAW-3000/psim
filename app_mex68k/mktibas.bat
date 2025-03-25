..\..\asw\bin\asw -g -cpu 68000 tibasic.asm
..\..\asw\bin\p2hex -F Moto tibasic.p

..\..\asw\bin\asw -g -cpu 68000 tload.asm
..\..\asw\bin\p2hex -F Moto +5 tload.p