#include <stdint.h>

// Pins
const int TRIG_PIN = 9;
const int ECHO_PIN = 10;

// Anything over 400 cm (23200 us pulse) is "out of range"
uint16_t MAX_PULSE_WIDTH = 23200;


uint16_t read_max_pulse_width_from_serial() {
  while(Serial.available() == 0); // Wait for data
  uint16_t max_dist;
  uint16_t read_byte = Serial.read();
  max_dist = (read_byte << 8);
  max_dist |= (uint16_t)Serial.read();
  while(Serial.available() > 0) Serial.read(); // consume line break
  return max_dist;
}

bool wait_for_serial_request() {
  // Waits until host sends a byte to start a new request
  while(Serial.available() == 0);  // wait
  while(Serial.available() > 0) Serial.read();
  return true;
}

void setup() {
  // The Trigger pin will tell the sensor to range find
  pinMode(TRIG_PIN, OUTPUT);
  digitalWrite(TRIG_PIN, LOW);

  // We'll use the serial monitor to view the sensor output
  Serial.begin(115200);
  while(!Serial); // Wait for PC to connect
  //Serial.println("Reading max pulse width");
  MAX_PULSE_WIDTH = read_max_pulse_width_from_serial();
  // Serial.println(MAX_PULSE_WIDTH);
  
  // todo:
  // set watchdog?
  // interrupts - async read - sleep etc
}


float read_sensor() {
  unsigned long t1;
  unsigned long t2;
  unsigned long pulse_width;
  float cm;
  float inches;

  // Hold the trigger pin high for at least 10 us
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // Wait for pulse on echo pin
  while (digitalRead(ECHO_PIN) == 0);

  // Measure how long the echo pin was held high (pulse width)
  // Note: the micros() counter will overflow after ~70 min
  t1 = micros();
  while (digitalRead(ECHO_PIN) == 1);
  t2 = micros();
  pulse_width = t2 - t1;

  if (pulse_width > MAX_PULSE_WIDTH) {
    return -1.;
  }
    
  // Calculate distance in centimeters and inches. The constants
  // are found in the datasheet, and calculated from the assumed speed 
  //of sound in air at sea level (~340 m/s).
  cm = pulse_width / 58.0;
  return cm;
}

void loop() {
  wait_for_serial_request();
  float distance_cm = read_sensor();
  // Print out results
  Serial.println(distance_cm);
  // Serial.println(" cm \t");
}
