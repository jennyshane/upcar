import threading
from flask import Flask, render_template, Response
from observer import *
from cam import *

class imageStream(object):
	def __init__(self):
		self.frame=None
		Observer.observe("frame", self.new_frame)
		self.frame_event=threading.Event()

	def new_frame(self, flag):
		self.frame=cv2.imencode('.jpg', flag.image)[1].tostring()
		self.frame_event.set()
	
	def generate_stream(self):
		while True:
			self.frame_event.wait()
			yield (b'--frame\r\n'
				b'Content-Type: image/jpeg\r\n\r\n' + self.frame + b'\r\n')
			self.frame_event.clear()

stream=imageStream()

app=Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/video_feed')
def video_feed():
	return Response(stream.generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

try:
	cam=camera()
	cam.start_recording()
	if __name__=="__main__":
		app.run(host='0.0.0.0')
finally:
	cam.stop_recording()
