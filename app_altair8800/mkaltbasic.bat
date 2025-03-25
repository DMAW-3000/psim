
..\..\asw\bin\asw -g -cpu 8080 altbasic.asm
..\..\asw\bin\p2hex -R 57344 -F Moto altbasic.p
..\..\asw\bin\p2hex -F Moto altbasic.p altbasic0.hex
python ..\casmake.py altbasic0.hex altbasic4k.cas 0000 0fae
 


