#define MOTOR_PWM_PIN 10
#define MOTOR_DIR_PIN 12
#define ENCODER_A_PIN 2
#define ENCODER_B_PIN 3

volatile bool commandReady = false;
char serialBuffer[32];
uint8_t bufferIndex = 0;

volatile int encoderCount = 0;
volatile bool motorDirection = false;
volatile unsigned long lastPulseTime = 0;
volatile float motorSpeed = 0.0;

int samplingInterval = 100; // อ่านทุก 100ms
bool sendSensorData = false;

const int windowSize = 50;              // เก็บข้อมูล 5 วินาที
const int shiftStep = 10;               // อัพเดททุก 1 วินาที

float speedBuffer[windowSize] = {0};
float currentBuffer[windowSize] = {0};
int windowBufferIndex = 0;  // Renamed to avoid conflict
int loopCount = 0;
unsigned long previousMillis = 0;

void setup() {
    pinMode(MOTOR_PWM_PIN, OUTPUT);
    pinMode(MOTOR_DIR_PIN, OUTPUT);
    pinMode(ENCODER_A_PIN, INPUT_PULLUP);
    pinMode(ENCODER_B_PIN, INPUT_PULLUP);
    
    attachInterrupt(digitalPinToInterrupt(ENCODER_A_PIN), encoderISR, CHANGE);
    attachInterrupt(digitalPinToInterrupt(ENCODER_B_PIN), encoderISR, CHANGE);
    
    Serial.begin(115200);
}

void serialEvent() {
    while (Serial.available()) {
        char receivedChar = Serial.read();
        if (receivedChar == '\n') {
            serialBuffer[bufferIndex] = '\0';
            commandReady = true;
            bufferIndex = 0;
        } else if (bufferIndex < sizeof(serialBuffer) - 1) {
            serialBuffer[bufferIndex++] = receivedChar;
        }
    }
}

void encoderISR() {
    int a = digitalRead(ENCODER_A_PIN);
    int b = digitalRead(ENCODER_B_PIN);
    motorDirection = (a == b);
    encoderCount += (motorDirection ? 1 : -1);
    unsigned long now = micros();
    
    // Only update speed if a reasonable time has passed to avoid division by zero
    // or unrealistically high values when pulses are very close together
    if (now - lastPulseTime > 100) { // Minimum 100 microseconds between readings
        motorSpeed = 60000000.0 / (12 * (now - lastPulseTime));
        lastPulseTime = now;
    }
}

void loop() {
    unsigned long currentMillis = millis();
    
    if (commandReady) {
        commandReady = false;
        processCommand();
    }
    
    // Process sensor readings using the windowing approach
    if (sendSensorData && currentMillis - previousMillis >= samplingInterval) {
        previousMillis = currentMillis;
        
        // Read current sensor
        float current = analogRead(A0) * (5.0 / 1023.0); // Convert to voltage
        
        // Store readings in circular buffers
        speedBuffer[windowBufferIndex] = motorSpeed;
        currentBuffer[windowBufferIndex] = current;
        windowBufferIndex = (windowBufferIndex + 1) % windowSize;
        
        loopCount++;
        
        // Only send data every shiftStep iterations (like in TCPIP code)
        if (loopCount % shiftStep == 0) {
            // Calculate max values in window (or average if preferred)
            float maxSpeed = 0.0;
            float maxCurrent = 0.0;
            
            for (int j = 0; j < windowSize; j++) {
                if (speedBuffer[j] > maxSpeed) maxSpeed = speedBuffer[j];
                if (currentBuffer[j] > maxCurrent) maxCurrent = currentBuffer[j];
            }
            
            // Send the processed data to the Python app
            sendSensorValues(maxSpeed, maxCurrent);
        }
    }
}

void processCommand() {
    char command = serialBuffer[0];
    int value = atoi(&serialBuffer[2]);
    
    switch (command) {
        case 'a':
            sendSensorData = (value == 1);
            Serial.println("Sensor data streaming " + String(sendSensorData ? "enabled" : "disabled"));
            break;
        case 's':
            analogWrite(MOTOR_PWM_PIN, constrain(value, 0, 255));
            Serial.println("Motor speed set to " + String(value));
            break;
        case 'i':
            samplingInterval = value;
            Serial.println("Sampling interval set to " + String(value) + " ms");
            break;
        case 'd':
            digitalWrite(MOTOR_DIR_PIN, value);
            Serial.println("Motor direction set to " + String(value));
            break;
        case 'r':
            encoderCount = 0;
            Serial.println("Encoder count reset");
            break;
        default:
            Serial.println("Unknown command");
            break;
    }
}

void sendSensorValues(float speed, float current) {
    Serial.print(motorDirection ? 1 : 0);
    Serial.print(",");
    Serial.print(speed);
    Serial.print(",");
    Serial.println(current);
}