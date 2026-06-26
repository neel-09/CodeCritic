// lib/supportedComponents.ts
//
// Single source of truth for components CodeCritic can generate + verify.
// This list MUST stay in sync with the Planner prompt's
// "=== SUPPORTED COMPONENTS ===" section. If you add a component to the
// planner prompt, add it here too — and vice versa.

export type ComponentCategory =
  | "Sensors"
  | "Input Devices"
  | "LEDs"
  | "Displays"
  | "Motors"
  | "Communication"
  | "Logic & Shift Registers"
  | "Passives & Other";

export interface SupportedComponent {
  name: string;
  note?: string; // optional caveat, e.g. simulation limitation
}

export const SUPPORTED_COMPONENTS: Record<ComponentCategory, SupportedComponent[]> = {
  Sensors: [
    { name: "DHT22" },
    { name: "DHT11" },
    { name: "HC-SR04 (Ultrasonic)" },
    { name: "PIR Motion Sensor" },
    { name: "NTC Temperature Sensor" },
    { name: "DS18B20" },
    { name: "MPU6050 (IMU)" },
    { name: "Photoresistor (LDR)" },
    { name: "Soil Moisture Sensor" },
    { name: "MQ2 Gas Sensor" },
    { name: "HX711 Load Cell Amplifier" },
    { name: "DS1307 RTC" },
    { name: "RFID-RC522" },
    { name: "BMP180 Pressure Sensor" },
  ],
  "Input Devices": [
    { name: "Pushbutton", note: "compiles, simulation not supported" },
    { name: "Slide Switch", note: "compiles, simulation not supported" },
    { name: "DIP Switch", note: "compiles, simulation not supported" },
    { name: "Membrane Keypad (4x4)", note: "compiles, simulation not supported" },
    { name: "Analog Joystick", note: "compiles, simulation not supported" },
    { name: "Potentiometer", note: "compiles, simulation not supported" },
    { name: "Slide Potentiometer", note: "compiles, simulation not supported" },
    { name: "Rotary Encoder (KY-040)", note: "compiles, simulation not supported" },
  ],
  LEDs: [
    { name: "Standard LED" },
    { name: "RGB LED" },
    { name: "LED Bar Graph" },
    { name: "NeoPixel (WS2812)" },
    { name: "NeoPixel Ring" },
    { name: "NeoPixel Strip" },
    { name: "NeoPixel Matrix" },
  ],
  Displays: [
    { name: "LCD 16x2 (I2C)" },
    { name: "LCD 20x4 (I2C)" },
    { name: "OLED SSD1306 (I2C)" },
    { name: "ILI9341 TFT (SPI)" },
    { name: "Nokia 5110 Screen (SPI)" },
    { name: "MAX7219 Dot Matrix" },
    { name: "7-Segment Display" },
    { name: "TM1637 7-Segment" },
  ],
  Motors: [
    { name: "Servo Motor" },
    { name: "Stepper Motor (Bipolar)" },
    { name: "A4988 Stepper Driver" },
  ],
  Communication: [
    { name: "IR Receiver" },
    { name: "IR Remote" },
  ],
  "Logic & Shift Registers": [
    { name: "74HC595 Shift Register" },
    { name: "74HC165 Shift Register" },
    { name: "Logic Gates (NOT/AND/OR/XOR/NAND)" },
  ],
  "Passives & Other": [
    { name: "Resistor" },
    { name: "Capacitor" },
    { name: "Buzzer" },
    { name: "Relay Module" },
    { name: "Tilt Switch" },
    { name: "NPN Transistor" },
    { name: "PNP Transistor" },
    { name: "MicroSD Card" },
  ],
};

export const SUPPORTED_BOARDS = ["Arduino Uno", "Arduino Nano", "Arduino Mega"] as const;