#include <Servo.h>

Servo s;
String input = "";

void setup() {
  Serial.begin(9600);
  s.attach(9);
  s.write(0);
  delay(500);
  Serial.println("READY");
}

void loop() {

  if (Serial.available()) {

    input = Serial.readStringUntil('\n');   // 🔥 FIXED
    input.trim();

    Serial.print("Received: ");
    
    Serial.println(input);

    // ---------- ACCESS GRANTED ----------
    if (input == "GRANT") {
      Serial.println("Rotating Servo...");
      
      for (int pos = 0; pos <= 180; pos++) {
        s.write(pos);
        delay(10);
      }
      delay(700);
      for (int pos = 180; pos >= 0; pos--) {
        s.write(pos);
        delay(10);
      }

      Serial.println("Done.");
    }

    // ---------- ACCESS DENIED ----------
    if (input == "DENY") {
      Serial.println("Denied. Servo at 0 degree.");
      s.write(0);
    }
  }
}
