import sys
import serial
import time

def main():
    if len(sys.argv) < 7:
        print("Mandatory parameters [Port, Speed, Data Bits, Stop Bits, Parity, Flow Control]")
        sys.exit(1)

    port_name = sys.argv[1]
    speed = int(sys.argv[2])
    data_bits_arg = int(sys.argv[3])
    stop_bits_arg = int(sys.argv[4])
    parity_arg = int(sys.argv[5])
    flow_control_arg = int(sys.argv[6])

    # Mapping Java gnu.io.SerialPort constants to pyserial constants
    
    # Data bits
    if data_bits_arg == 5:
        data_bits = serial.FIVEBITS
    elif data_bits_arg == 6:
        data_bits = serial.SIXBITS
    elif data_bits_arg == 7:
        data_bits = serial.SEVENBITS
    elif data_bits_arg == 8:
        data_bits = serial.EIGHTBITS
    else:
        data_bits = serial.EIGHTBITS
        
    # Stop bits (Java: 1=1, 2=2, 3=1.5)
    if stop_bits_arg == 1:
        stop_bits = serial.STOPBITS_ONE
    elif stop_bits_arg == 2:
        stop_bits = serial.STOPBITS_TWO
    elif stop_bits_arg == 3:
        stop_bits = serial.STOPBITS_ONE_POINT_FIVE
    else:
        stop_bits = serial.STOPBITS_ONE

    # Parity (Java: 0=None, 1=Odd, 2=Even, 3=Mark, 4=Space)
    parity_map = {
        0: serial.PARITY_NONE,
        1: serial.PARITY_ODD,
        2: serial.PARITY_EVEN,
        3: serial.PARITY_MARK,
        4: serial.PARITY_SPACE
    }
    parity = parity_map.get(parity_arg, serial.PARITY_NONE)

    # Flow Control (Java: 0=None, 1=RTSCTS_IN, 2=RTSCTS_OUT, 4=XONXOFF_IN, 8=XONXOFF_OUT)
    xonxoff = False
    rtscts = False
    # If any bit of flow control matches XON/XOFF
    if (flow_control_arg & 4) or (flow_control_arg & 8):
        xonxoff = True
    # If any bit of flow control matches RTS/CTS
    if (flow_control_arg & 1) or (flow_control_arg & 2):
        rtscts = True

    print(f"Opening {port_name} ...")
    try:
        ser = serial.Serial(
            port=port_name,
            baudrate=speed,
            bytesize=data_bits,
            parity=parity,
            stopbits=stop_bits,
            xonxoff=xonxoff,
            rtscts=rtscts,
            timeout=1  # 1 second timeout for blocking read
        )
        print("Parameterizing Port...")
        print("Port Ready ...")

        while True:
            # Replicating the logic to read bits and print them
            if ser.in_waiting > 0:
                # To match Java thread sleep of 200ms before reading
                time.sleep(0.2)
                while ser.in_waiting > 0:
                    data = ser.read(1)
                    if data:
                        bit = data[0]
                        try:
                            # Replicating `=>>[char|bit]` format
                            # Java casts to char, which prints ASCII chars
                            char_val = chr(bit) if 32 <= bit <= 126 else chr(bit)
                            print(f"=>>[{char_val}|{bit}]")
                        except Exception as e:
                            print(f"Error in processStr(): {e}")
            else:
                time.sleep(0.1)

    except serial.SerialException as e:
        print(f"Error opening or reading from serial port: {e}")
    except KeyboardInterrupt:
        print("Closed")
        if 'ser' in locals() and ser.is_open:
            ser.close()

if __name__ == '__main__':
    main()
