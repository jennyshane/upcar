import time
import serial

def enum(**enums):
	return type('Enum', (), enums)

commandEnum=enum(
	NOT_ACTUAL_COMMAND=0,
	RC_SIGNAL_WAS_LOST=1,
	RC_SIGNALED_STOP_AUTONOMOUS=2, 
	STEERING_VALUE_OUT_OF_RANGE=3,
	THROTTLE_VALUE_OUT_OF_RANGE=4,
	RUN_AUTONOMOUSLY=5,
	STOP_AUTONOMOUS=6,
	STOPPED_AUTO_COMMAND_RECIEVED=7,
	NO_COMMAND_AVAILABLE=8,
	GOOD_PI_COMMAND_RECIEVED=9,
	TOO_MANY_VALUES_IN_COMMAND=10,
	GOOD_RC_SIGNALS_RECIEVED=11)


def serial_read(serial_conn):
	serial_conn.flushInput()
	n_read_items=0
	data=[]
	while n_read_items!=10:
		try:
			data_input=serial_conn.readline()
			data=list(map(float, str(data_input, 'ascii').split(',')))
			n_read_items=len(data)
		except ValueError:
			continue
	print(data)
	return data

def serial_write(serial_conn, data):
	assert(len(data)==4)
	dataline='{0}, {1}, {2}, {3}\n'.format(data[0], data[1], data[2], data[3])
	print(dataline)
	serial_conn.write(dataline.encode('ascii'))
	serial_conn.flush()


try:
	ser=serial.Serial('/dev/ttyACM1')
except serial.SerialException:
	try:
		ser=serial.Serial('/dev/ttyACM0')
	except serial.SerialException:
		print("can't connect to serial")
		sys.exit()
	
for i in range(0, 100):
	data=serial_read(ser)
	print(data)
	time.sleep(.01)
	
for i in range(0, 100):
	serial_write(ser, [commandEnum.RUN_AUTONOMOUSLY, 1100+8*i, 1555, 0])
	data=serial_read(ser)
	data=serial_read(ser)
	print(data)
	time.sleep(.01)



