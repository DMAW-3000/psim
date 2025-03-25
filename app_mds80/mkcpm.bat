del ccp.hex
del bdos.hex
del cdump.hex
del loadtap.hex

..\..\asw\bin\asw -g -cpu 8080 bdos.asm
..\..\asw\bin\p2hex -F Moto bdos.p
..\..\asw\bin\asw -g -cpu 8080 ccp.asm
..\..\asw\bin\p2hex -F Moto ccp.p

..\..\asw\bin\asw -g -cpu 8080 cdump.asm
..\..\asw\bin\p2hex -F Moto cdump.p

python ..\..\pyplm\pyplm.py -o -e extern_cpm.asm -s LOADCOM loadtap.plm loadtap.asm
..\..\asw\bin\asw -g -cpu 8080 loadtap.asm
..\..\asw\bin\p2hex -F Moto loadtap.p



