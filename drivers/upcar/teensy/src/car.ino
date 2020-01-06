#include <Arduino.h>
#include <Servo.h>

int speed=0;
int pwmA=4;
int pwmB=5;
int dirA=7;
int dirB=8;

const int speed_min=0;
const int speed_max=255;

const int steer_left=50;
const int steer_right=120;

Servo steering;
int steer=85;

char cmdBuf[8];
char message[10];

int dir=0;
int last_serial=0;

void setup(){
	pinMode(pwmA, OUTPUT);
	pinMode(pwmB, OUTPUT);
	pinMode(dirA, OUTPUT);
	pinMode(dirB, OUTPUT);
	digitalWrite(dirA, dir);
	digitalWrite(dirB, dir);
	steering.attach(6);

	analogWrite(pwmA, speed);
	analogWrite(pwmB, speed);
	steering.write(steer);

	last_serial=millis();
	Serial.begin(9600);
}

void loop(){

	if(Serial.available()){

		Serial.readBytes(cmdBuf, 8);
		last_serial=millis();
		cmdBuf[7]='\0';
		steer=atoi(cmdBuf+4);
		steer=(steer<steer_left)?steer_left:steer;
		steer=(steer>steer_right)?steer_right:steer;

		cmdBuf[3]='\0';
		speed=atoi(cmdBuf);
		speed=speed-255;
		if(speed<0){
			dir=1;
			speed=-speed;
		}else{
			dir=0;
		}
			
		speed=(speed<speed_min)?0:speed;
		speed=(speed>speed_max)?speed_max:speed;

		sprintf(message, "%d, %d\n", speed, steer);
		Serial.print(message);
		steering.write(steer);
		digitalWrite(dirA, dir);
		digitalWrite(dirB, dir);
		analogWrite(pwmA, speed);
		analogWrite(pwmB, speed);

	}else if((millis()-last_serial)>500){

		steering.write(85);
		analogWrite(pwmA, 0);
		analogWrite(pwmB, 0);

	}

	delay(10);
}

