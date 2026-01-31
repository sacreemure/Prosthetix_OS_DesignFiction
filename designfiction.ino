

#include <M5Unified.h>

bool systemFixed = false;

void setup() {
  auto cfg = M5.config();
  M5.begin(cfg);
  
  // Serial for Python connection
  Serial.begin(115200); 
  
  M5.Display.setTextSize(3);
  showFailureScreen();
}

void loop() {
  M5.update();
  
  // Check if screen is touched
  if (M5.Touch.getCount() > 0) {
    auto t = M5.Touch.getDetail(0);
    if (t.wasPressed()) { // If touched
       if (!systemFixed) {
         fixSystem();
       }
    }
  }
}

void showFailureScreen() {
  M5.Display.fillScreen(TFT_RED);
  M5.Display.setTextColor(TFT_WHITE);
  M5.Display.setCursor(10, 80);
  M5.Display.print("CRITICAL ERROR");
  
  // Draw Button
  M5.Display.fillRect(60, 160, 200, 60, TFT_BLACK);
  M5.Display.drawRect(60, 160, 200, 60, TFT_WHITE);
  M5.Display.setCursor(85, 175);
  M5.Display.print("OVERRIDE");
}

void fixSystem() {
  M5.Speaker.tone(1000, 200); // Beep
  M5.Display.fillScreen(TFT_GREEN);
  M5.Display.setTextColor(TFT_BLACK);
  M5.Display.setCursor(20, 100);
  M5.Display.print("RESTORED");
  
  // Send signal to Python
  Serial.println("ACTION_RESET_CONFIRMED"); 
  
  systemFixed = true;
  delay(5000); // Wait 5 seconds
  systemFixed = false;
  showFailureScreen(); // Reset for next demo
}