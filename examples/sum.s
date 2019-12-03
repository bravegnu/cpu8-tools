list:
	.byte 0x01
	.byte 0x02
	.byte 0x03
	.byte 0x00

	LI  R1, 0x00    # Set running sum to zero
	LI  R0, list    # Start at beginning of list
loop:	LW  R2, (R0)    # Get the next number
	JEQ R2, end     # Exit loop if number == 0
	ADD R1, R2      # Add number to running sum
	LI  R3, 0x01    # Put 1 into R3, so we can do
	ADD R0, R3      # R0++
	JMP loop        # Loop back
end:  	SWI R1, 0x40    # Store result at address 0x40
inf:  	JMP inf         # Infinite loop
