import sys
import serial
import time
from serial_reader import SerialReader

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

    # Data bits
    if data_bits_arg == 5: data_bits = serial.FIVEBITS
    elif data_bits_arg == 6: data_bits = serial.SIXBITS
    elif data_bits_arg == 7: data_bits = serial.SEVENBITS
    else: data_bits = serial.EIGHTBITS
        
    # Stop bits
    if stop_bits_arg == 1: stop_bits = serial.STOPBITS_ONE
    elif stop_bits_arg == 2: stop_bits = serial.STOPBITS_TWO
    elif stop_bits_arg == 3: stop_bits = serial.STOPBITS_ONE_POINT_FIVE
    else: stop_bits = serial.STOPBITS_ONE

    # Parity
    parity_map = {0: serial.PARITY_NONE, 1: serial.PARITY_ODD, 2: serial.PARITY_EVEN, 3: serial.PARITY_MARK, 4: serial.PARITY_SPACE}
    parity = parity_map.get(parity_arg, serial.PARITY_NONE)

    # Flow Control
    xonxoff = bool((flow_control_arg & 4) or (flow_control_arg & 8))
    rtscts = bool((flow_control_arg & 1) or (flow_control_arg & 2))

    print(f"Opening {port_name} ...")
    
    reader = SerialReader(
        port=port_name,
        baudrate=speed,
        bytesize=data_bits,
        parity=parity,
        stopbits=stop_bits,
        xonxoff=xonxoff,
        rtscts=rtscts
    )
    
    try:
        reader.connect()
        print("Parameterizing Port...")
        print("Port Ready ...")
        
        def on_data(char_val, bit):
            try:
                print(f"=>>[{char_val}|{bit}]")
            except Exception as e:
                print(f"Error in processStr(): {e}")
                
        def on_error(msg):
            print(f"Error reading: {msg}")
            
        reader.start_reading(on_data, on_error)
        
        # Keep the main thread alive since reading happens in a daemon thread
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Closed")
        reader.disconnect()

if __name__ == '__main__':
    main()
