#include <Wire.h>
#include <VL53L1X.h>
#include <Adafruit_NeoPixel.h>

#define LED_PIN 6
#define NUM_LEDS 150
#define MAX_DISTANCE 1100
#define MIN_DISTANCE 100
#define NUM_SECTIONS 8
#define THRESHOLD_MM 50     
#define COOLDOWN_MS 300
#define GAME_DURATION 30000 // ★30秒の時間制限を復活

VL53L1X sensor;
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_GRB + NEO_KHZ800);

int currentTarget = -1;  
unsigned long lastHitTime = 0;
unsigned long gameStartTime = 0; // 開始時間を記録する変数
int score = 0;
bool isGameRunning = false;

// 終了前のカウントダウン用フラグ
bool count3played = false;
bool count2played = false;
bool count1played = false;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);

  sensor.setTimeout(500);
  if (!sensor.init()) {
    Serial.println("VL53L1X init failed!");
    while (1);
  }

  sensor.setDistanceMode(VL53L1X::Short);
  sensor.setMeasurementTimingBudget(50000);
  sensor.startContinuous(50);

  strip.begin();
  strip.show();

  randomSeed(analogRead(A0));
  
  // 待機状態で起動
  stopGame();
}

void loop() {
  // PCからの指令チェック
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    
    if (cmd == 's') {
      startGame();
    }
    else if (cmd == 'r') {
      stopGame();
    }
  }

  if (!isGameRunning) return;

  // --- 時間管理 ---
  unsigned long currentTime = millis();
  long remainingTime = GAME_DURATION - (currentTime - gameStartTime);

  // 終了前のカウントダウン (3, 2, 1)
  if (remainingTime <= 3000 && remainingTime > 2000 && !count3played) {
    Serial.println("COUNT_3");
    count3played = true;
  }
  else if (remainingTime <= 2000 && remainingTime > 1000 && !count2played) {
    Serial.println("COUNT_2");
    count2played = true;
  }
  else if (remainingTime <= 1000 && remainingTime > 0 && !count1played) {
    Serial.println("COUNT_1");
    count1played = true;
  }

  // 時間切れ判定
  if (remainingTime <= 0) {
    finishGame(); // タイムアップ処理
    return;
  }
  // ----------------

  int distance = sensor.read();
  if (sensor.timeoutOccurred()) return;

  int sectionRange = (MAX_DISTANCE - MIN_DISTANCE) / NUM_SECTIONS;
  int targetMin = MIN_DISTANCE + currentTarget * sectionRange;
  int targetMax = targetMin + sectionRange;

  if (distance >= targetMin - THRESHOLD_MM && distance <= targetMax + THRESHOLD_MM) {
    if (millis() - lastHitTime > COOLDOWN_MS) { 
      score++;
      Serial.println("PLAY_HIT"); 
      Serial.print("HIT! スコア: ");
      Serial.println(score);
      flashTargetColor(currentTarget, strip.Color(255, 255, 255)); 
      
      pickNewTarget(currentTarget);
      lastHitTime = millis();
    }
  }
  delay(10);
}

// ゲーム開始
void startGame() {
  score = 0;
  
  // カウントダウンフラグのリセット
  count3played = false;
  count2played = false;
  count1played = false;

  startCountdown(); // 3,2,1演出
  
  isGameRunning = true;
  gameStartTime = millis(); // 時間計測スタート
  pickNewTarget(-1);
  
  Serial.println("=== ゲームスタート(30秒) ===");
}

// タイムアップによる自然終了
void finishGame() {
  isGameRunning = false;
  strip.clear();
  strip.show();
  
  Serial.println("PLAY_END"); // PCに終了合図（これでランキングが出ます）
  Serial.println("RESET_DONE"); // ボタンを復活させる
  Serial.println("=== タイムアップ！ ===");
}

// リセットボタンによる強制終了
void stopGame() {
  isGameRunning = false;
  score = 0;
  strip.clear();
  strip.show();
  Serial.println("=== リセット中断 ===");
  Serial.println("RESET_DONE");
}

void startCountdown() {
  strip.clear();
  strip.show();
  
  // 3
  Serial.println("COUNT_3");
  colorWipe(strip.Color(255, 0, 0), 0); 
  delay(1000);

  // 2
  Serial.println("COUNT_2");
  colorWipe(strip.Color(255, 255, 0), 0); 
  delay(1000);

  // 1
  Serial.println("COUNT_1");
  colorWipe(strip.Color(0, 255, 0), 0); 
  delay(1000);

  // START!
  Serial.println("PLAY_START");
  strip.clear();
  strip.show();
}

void colorWipe(uint32_t color, int wait) {
  for(int i=0; i<strip.numPixels(); i++) {
    strip.setPixelColor(i, color);
  }
  strip.show();
}

void pickNewTarget(int prevTarget) {
  int newTarget;
  do {
    newTarget = random(NUM_SECTIONS);
  } while (abs(newTarget - prevTarget) <= 1); 

  currentTarget = newTarget;

  uint8_t r, g, b;
  switch (newTarget) {
    case 0: r = 255; g = 0; b = 0; break;        
    case 1: r = 255; g = 64; b = 0; break;       
    case 2: r = 255; g = 255; b = 0; break;      
    case 3: r = 128; g = 255; b = 0; break;      
    case 4: r = 0; g = 255; b = 0; break;        
    case 5: r = 0; g = 255; b = 255; break;      
    case 6: r = 0; g = 0; b = 255; break;        
    case 7: r = 128; g = 0; b = 255; break;      
  }

  strip.clear();
  int ledsPerSection = NUM_LEDS / NUM_SECTIONS;
  int startLED = newTarget * ledsPerSection;
  int endLED = startLED + ledsPerSection - 1;

  for (int i = startLED; i <= endLED; i++) {
    strip.setPixelColor(i, strip.Color(r, g, b));
  }
  strip.show();
}

void flashTargetColor(int section, uint32_t color) {
  int ledsPerSection = NUM_LEDS / NUM_SECTIONS;
  int startLED = section * ledsPerSection;
  int endLED = startLED + ledsPerSection - 1;

  for (int i = startLED; i <= endLED; i++) {
    strip.setPixelColor(i, color);
  }
  strip.show();
}