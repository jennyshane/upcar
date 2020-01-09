import io
import struct


joystick_file='/dev/input/js0'
js_data=open(joystick_file, 'rb')




while True:
	input_buffer=js_data.read(8)
	t, value, in_type, in_id=struct.unpack('IhBB', input_buffer);
	print("Type: "+str(in_type))
	print("ID: "+str(in_id))
	print("Value: "+str(value))
	print("\n")


			
js_data.close()
