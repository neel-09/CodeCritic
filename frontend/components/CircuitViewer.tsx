"use client";

import { useMemo, useState, useRef, forwardRef, useImperativeHandle } from "react";

// ─── Types ──────────────────────────────────────────────────────────────────

type Side = "L" | "R" | "T" | "B";

interface PinDef {
  name: string;
  side: Side;
  pos: number; // 0–1 along the side
}

interface ComponentDef {
  label: string;
  w: number;
  h: number;
  fill: string;
  pins: PinDef[];
}

// ─── Helpers ────────────────────────────────────────────────────────────────

/** Evenly distribute pins along a side */
function ep(names: string[], side: Side): PinDef[] {
  return names.map((name, i) => ({
    name,
    side,
    pos: (i + 1) / (names.length + 1),
  }));
}

/** Pixel position of a pin relative to the component's (0,0) */
function pinPos(pin: PinDef, w: number, h: number) {
  switch (pin.side) {
    case "L": return { px: 0,     py: pin.pos * h };
    case "R": return { px: w,     py: pin.pos * h };
    case "T": return { px: pin.pos * w, py: 0 };
    case "B": return { px: pin.pos * w, py: h };
  }
}

/** Where to draw the pin label (always inside the box) */
function pinLabel(pin: PinDef, px: number, py: number) {
  const OFF = 7;
  switch (pin.side) {
    case "L": return { x: px + OFF, y: py + 3.5, anchor: "start"  as const };
    case "R": return { x: px - OFF, y: py + 3.5, anchor: "end"    as const };
    case "T": return { x: px,       y: py + 10,  anchor: "middle" as const };
    case "B": return { x: px,       y: py - 4,   anchor: "middle" as const };
  }
}

// ─── Component catalogue ────────────────────────────────────────────────────

const DEFS: Record<string, ComponentDef> = {

  // ── Microcontrollers ──────────────────────────────────────────────────────
  "wokwi-arduino-uno": {
    label: "Arduino Uno", w: 220, h: 300, fill: "#0d3a6e",
    pins: [
      ...ep(["5V","3.3V","GND.1","GND.2","VIN","RESET","AREF"], "L"),
      ...ep(["0","1","2","3","4","5","6","7","8","9","10","11","12","13"], "R"),
      ...ep(["A0","A1","A2","A3","A4","A5"], "B"),
    ],
  },
  "wokwi-arduino-nano": {
    label: "Arduino Nano", w: 140, h: 300, fill: "#0d3a6e",
    pins: [
      ...ep(["5V","3.3V","GND.1","GND.2","VIN","RESET","AREF"], "L"),
      ...ep(["0","1","2","3","4","5","6","7","8","9","10","11","12","13"], "R"),
      ...ep(["A0","A1","A2","A3","A4","A5","A6","A7"], "B"),
    ],
  },
  "wokwi-arduino-mega": {
    label: "Arduino Mega", w: 260, h: 400, fill: "#0d3a6e",
    pins: [
      ...ep(["5V","3.3V","GND.1","GND.2","VIN","RESET"], "L"),
      ...ep(["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19"], "R"),
      ...ep(["20","21","22","23","24","25","26","27","28","29","30","31"], "T"),
      ...ep(["A0","A1","A2","A3","A4","A5","A6","A7","A8","A9","A10","A11","A12","A13","A14","A15"], "B"),
    ],
  },
  "wokwi-attiny85": {
    label: "ATtiny85", w: 90, h: 80, fill: "#1a3a5c",
    pins: [
      ...ep(["RESET","3","4"], "L"),
      ...ep(["VCC","1","2","0"], "R"),
    ],
  },
  "wokwi-esp32-devkit-v1": {
    label: "ESP32 DevKit v1", w: 170, h: 340, fill: "#0f2a1a",
    pins: [
      ...ep(["3V3","GND.1","GND.2","VIN","EN","SVP","SVN"], "L"),
      ...ep(["23","22","TX","RX","21","19","18","5","17","16","4","0","2","15","8","7","6"], "R"),
      ...ep(["13","12","14","27","26","25","33","32","35","34","39","36"], "B"),
    ],
  },
  "wokwi-esp32-s2-devkit": {
    label: "ESP32-S2 DevKit", w: 160, h: 300, fill: "#0f2a1a",
    pins: [
      ...ep(["3V3","GND.1","VIN","EN"], "L"),
      ...ep(["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18"], "R"),
      ...ep(["33","34","35","36","37","38","39","40","41","42","43","44","45"], "B"),
    ],
  },
  "wokwi-esp32-s3-devkit": {
    label: "ESP32-S3 DevKit", w: 160, h: 300, fill: "#0f2a1a",
    pins: [
      ...ep(["3V3","GND.1","VIN","EN"], "L"),
      ...ep(["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18"], "R"),
      ...ep(["33","34","35","36","37","38","39","40","41","42","43","44","45"], "B"),
    ],
  },
  "wokwi-esp32-c3-devkit": {
    label: "ESP32-C3 DevKit", w: 150, h: 240, fill: "#0f2a1a",
    pins: [
      ...ep(["3V3","GND.1","VIN","EN"], "L"),
      ...ep(["0","1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16","17","18","19","20","21"], "R"),
    ],
  },
  "wokwi-pi-pico": {
    label: "Raspberry Pi Pico", w: 160, h: 320, fill: "#2a0f3a",
    pins: [
      ...ep(["GP0","GP1","GND.1","GP2","GP3","GND.2","GP4","GP5","GND.3","GP6","GP7","GND.4","GP8","GP9","GND.5","GP10","GP11","GND.6","GP12","GP13"], "L"),
      ...ep(["VBUS","VSYS","GND.7","3V3_EN","3V3","ADC_REF","GP26","GP27","AGND","GP28","ADC_EN","GND.8","GP22","GP21","GP20","GP19","GP18","GND.9","GP17","GP16"], "R"),
    ],
  },
  "board-st-nucleo-c031c6": {
    label: "Nucleo C031C6", w: 160, h: 200, fill: "#1a4a2a",
    pins: [
      ...ep(["3V3","GND.1","VIN","RESET"], "L"),
      ...ep(["PA0","PA1","PA2","PA3","PA4","PA5","PA6","PA7","PB0","PB1"], "R"),
      ...ep(["PA8","PA9","PA10","PA11","PA12"], "B"),
    ],
  },
  "board-st-nucleo-l031k6": {
    label: "Nucleo L031K6", w: 160, h: 180, fill: "#1a4a2a",
    pins: [
      ...ep(["3V3","GND.1","VIN","RESET"], "L"),
      ...ep(["PA0","PA1","PA2","PA3","PA4","PA5","PA6","PA7","PB0","PB1"], "R"),
    ],
  },
  "board-stm32-bluepill": {
    label: "STM32 Blue Pill", w: 160, h: 220, fill: "#0d2a4a",
    pins: [
      ...ep(["GND.1","GND.2","3V3","VIN","NRST"], "L"),
      ...ep(["PA0","PA1","PA2","PA3","PA4","PA5","PA6","PA7","PB0","PB1","PA8","PA9","PA10","PA15"], "R"),
      ...ep(["PB3","PB4","PB5","PB6","PB7","PB8","PB9"], "B"),
    ],
  },

  // ── Sensors ───────────────────────────────────────────────────────────────
  "wokwi-dht22": {
    label: "DHT22", w: 80, h: 80, fill: "#145214",
    pins: ep(["VCC","SDA","GND"], "L"),
  },
  "wokwi-dht11": {
    label: "DHT11", w: 80, h: 80, fill: "#145214",
    pins: ep(["VCC","SDA","GND"], "L"),
  },
  "wokwi-hc-sr04": {
    label: "HC-SR04", w: 100, h: 80, fill: "#145214",
    pins: ep(["VCC","TRIG","ECHO","GND"], "L"),
  },
  "wokwi-pir-motion-sensor": {
    label: "PIR Sensor", w: 90, h: 70, fill: "#145214",
    pins: ep(["GND","OUT","VCC"], "L"),
  },
  "wokwi-ntc-temperature-sensor": {
    label: "NTC Thermistor", w: 100, h: 70, fill: "#145214",
    pins: ep(["VCC","GND","OUT"], "L"),
  },
  "wokwi-ds18b20": {
    label: "DS18B20", w: 90, h: 70, fill: "#145214",
    pins: ep(["VCC","GND","DQ"], "L"),
  },
  "wokwi-mpu6050": {
    label: "MPU6050", w: 90, h: 100, fill: "#145214",
    pins: ep(["VCC","GND","SCL","SDA","INT"], "L"),
  },
  "wokwi-photoresistor-sensor": {
    label: "Photoresistor", w: 100, h: 80, fill: "#145214",
    pins: ep(["VCC","GND","DO","AO"], "L"),
  },
  "wokwi-soil-moisture-sensor": {
    label: "Soil Moisture", w: 100, h: 80, fill: "#145214",
    pins: ep(["VCC","GND","DO","AO"], "L"),
  },
  "wokwi-gas-sensor": {
    label: "Gas Sensor MQ2", w: 110, h: 80, fill: "#145214",
    pins: ep(["VCC","GND","DO","AO"], "L"),
  },
  "wokwi-hx711": {
    label: "HX711", w: 90, h: 80, fill: "#145214",
    pins: [
      ...ep(["VCC","GND"], "L"),
      ...ep(["DT","SCK"], "R"),
    ],
  },
  "wokwi-ds1307": {
    label: "DS1307 RTC", w: 100, h: 90, fill: "#145214",
    pins: ep(["GND","VCC","SDA","SCL","SQW"], "L"),
  },
  "board-mfrc522": {
    label: "MFRC522 RFID", w: 110, h: 130, fill: "#145214",
    pins: ep(["VCC","GND","SCK","MOSI","MISO","SDA","RST"], "L"),
  },
  "board-bmp180": {
    label: "BMP180", w: 90, h: 80, fill: "#145214",
    pins: ep(["VCC","GND","SCL","SDA"], "L"),
  },

  // ── Input Devices ─────────────────────────────────────────────────────────
  "wokwi-pushbutton": {
    label: "Button", w: 60, h: 60, fill: "#3d2a00",
    pins: [
      ...ep(["1.l","2.l"], "L"),
      ...ep(["1.r","2.r"], "R"),
    ],
  },
  "wokwi-pushbutton-6mm": {
    label: "Button 6mm", w: 60, h: 60, fill: "#3d2a00",
    pins: [
      ...ep(["1.l","2.l"], "L"),
      ...ep(["1.r","2.r"], "R"),
    ],
  },
  "wokwi-slide-switch": {
    label: "Slide Switch", w: 80, h: 60, fill: "#3d2a00",
    pins: ep(["1","2","3"], "L"),
  },
  "wokwi-dip-switch-8": {
    label: "DIP Switch ×8", w: 100, h: 160, fill: "#3d2a00",
    pins: [
      ...ep(["1A","2A","3A","4A","5A","6A","7A","8A"], "L"),
      ...ep(["1B","2B","3B","4B","5B","6B","7B","8B"], "R"),
    ],
  },
  "wokwi-membrane-keypad": {
    label: "4×4 Keypad", w: 100, h: 120, fill: "#3d2a00",
    pins: [
      ...ep(["R1","R2","R3","R4"], "L"),
      ...ep(["C1","C2","C3","C4"], "R"),
    ],
  },
  "wokwi-analog-joystick": {
    label: "Joystick", w: 100, h: 90, fill: "#3d2a00",
    pins: ep(["GND","VCC","VERT","HORIZ","SEL"], "L"),
  },
  "wokwi-potentiometer": {
    label: "Potentiometer", w: 90, h: 70, fill: "#3d2a00",
    pins: ep(["GND","SIG","VCC"], "L"),
  },
  "wokwi-slide-potentiometer": {
    label: "Slide Pot", w: 90, h: 70, fill: "#3d2a00",
    pins: ep(["GND","SIG","VCC"], "L"),
  },
  "wokwi-ky-040": {
    label: "Rotary Enc KY-040", w: 110, h: 90, fill: "#3d2a00",
    pins: ep(["GND","VCC","SW","DT","CLK"], "L"),
  },

  // ── LEDs ──────────────────────────────────────────────────────────────────
  "wokwi-led": {
    label: "LED", w: 60, h: 50, fill: "#4a2d00",
    pins: [
      ...ep(["A"], "L"),
      ...ep(["C"], "R"),
    ],
  },
  "wokwi-rgb-led": {
    label: "RGB LED", w: 70, h: 70, fill: "#4a2d00",
    pins: [
      ...ep(["R","G","B"], "L"),
      ...ep(["COM"], "R"),
    ],
  },
  "wokwi-led-bar-graph": {
    label: "LED Bar ×10", w: 100, h: 200, fill: "#4a2d00",
    pins: [
      ...ep(["A1","A2","A3","A4","A5","A6","A7","A8","A9","A10"], "L"),
      ...ep(["B1","B2","B3","B4","B5","B6","B7","B8","B9","B10"], "R"),
    ],
  },
  "wokwi-neopixel": {
    label: "NeoPixel", w: 80, h: 60, fill: "#4a2d00",
    pins: ep(["GND","VCC","DIN"], "L"),
  },
  "wokwi-led-ring": {
    label: "LED Ring", w: 80, h: 60, fill: "#4a2d00",
    pins: ep(["GND","VCC","DIN"], "L"),
  },
  "wokwi-led-strip": {
    label: "LED Strip", w: 80, h: 60, fill: "#4a2d00",
    pins: ep(["GND","VCC","DIN"], "L"),
  },
  "wokwi-led-matrix": {
    label: "LED Matrix", w: 80, h: 60, fill: "#4a2d00",
    pins: ep(["GND","VCC","DIN"], "L"),
  },
  "wokwi-nlsf595": {
    label: "NLSF595", w: 100, h: 130, fill: "#4a2d00",
    pins: [
      ...ep(["VCC","GND","SER","SRCLK","RCLK","OE","SRCLR"], "L"),
      ...ep(["QA","QB","QC","QD","QE","QF","QG","QH"], "R"),
    ],
  },

  // ── Displays ──────────────────────────────────────────────────────────────
  "wokwi-lcd1602": {
    label: "LCD 16×2", w: 130, h: 80, fill: "#1a0f4a",
    pins: ep(["GND","VCC","SDA","SCL"], "B"),
  },
  "wokwi-lcd2004": {
    label: "LCD 20×4", w: 150, h: 90, fill: "#1a0f4a",
    pins: ep(["GND","VCC","SDA","SCL"], "B"),
  },
  "wokwi-ssd1306": {
    label: "OLED SSD1306", w: 110, h: 80, fill: "#1a0f4a",
    pins: ep(["GND","VCC","SCL","SDA"], "B"),
  },
  "board-ssd1306": {
    label: "OLED SSD1306", w: 110, h: 80, fill: "#1a0f4a",
    pins: ep(["GND","VCC","SCL","SDA"], "B"),
  },
  "board-grove-oled-sh1107": {
    label: "Grove OLED", w: 110, h: 80, fill: "#1a0f4a",
    pins: ep(["GND","VCC","SCL","SDA"], "B"),
  },
  "wokwi-ili9341": {
    label: "ILI9341 TFT", w: 120, h: 100, fill: "#1a0f4a",
    pins: ep(["VCC","GND","SCL","SDA","CS","DC","RST"], "B"),
  },
  "wokwi-nokia-5110-screen": {
    label: "Nokia 5110", w: 130, h: 90, fill: "#1a0f4a",
    pins: ep(["RST","CE","DC","DIN","CLK","VCC","BL","GND"], "B"),
  },
  "wokwi-max7219-matrix": {
    label: "MAX7219 Matrix", w: 120, h: 80, fill: "#1a0f4a",
    pins: ep(["VCC","GND","DIN","CS","CLK"], "B"),
  },
  "wokwi-7segment": {
    label: "7-Segment", w: 100, h: 100, fill: "#1a0f4a",
    pins: [
      ...ep(["A","B","C","D","E","F"], "L"),
      ...ep(["G","DP","COM1","COM2"], "R"),
    ],
  },
  "wokwi-tm1637-7segment": {
    label: "TM1637", w: 100, h: 70, fill: "#1a0f4a",
    pins: ep(["VCC","GND","CLK","DIO"], "B"),
  },

  // ── Motors ────────────────────────────────────────────────────────────────
  "wokwi-servo": {
    label: "Servo", w: 90, h: 70, fill: "#4a0f0f",
    pins: ep(["GND","V+","PWM"], "L"),
  },
  "wokwi-stepper-motor": {
    label: "Stepper Motor", w: 100, h: 70, fill: "#4a0f0f",
    pins: ep(["A-","A+","B+","B-"], "L"),
  },
  "wokwi-biaxial-stepper": {
    label: "Biaxial Stepper", w: 110, h: 90, fill: "#4a0f0f",
    pins: [
      ...ep(["A1-","A1+","B1+","B1-"], "L"),
      ...ep(["A2-","A2+","B2+","B2-"], "R"),
    ],
  },
  "wokwi-a4988": {
    label: "A4988 Driver", w: 100, h: 130, fill: "#4a0f0f",
    pins: [
      ...ep(["VMOT","GND.1","2B","2A","1A","1B"], "L"),
      ...ep(["VDD","GND.2","STEP","DIR","SLEEP","RESET","MS3","MS2","MS1","EN"], "R"),
    ],
  },

  // ── Communication ─────────────────────────────────────────────────────────
  "wokwi-ir-receiver": {
    label: "IR Receiver", w: 90, h: 60, fill: "#0f2a3a",
    pins: ep(["GND","VCC","OUT"], "L"),
  },
  "wokwi-ir-remote": {
    label: "IR Remote", w: 90, h: 60, fill: "#0f2a3a",
    pins: [],
  },

  // ── Logic Gates & Shift Registers ─────────────────────────────────────────
  "wokwi-74hc595": {
    label: "74HC595", w: 110, h: 160, fill: "#0f3a3a",
    pins: [
      ...ep(["QB","QC","QD","QE","QF","QG","QH","GND"], "L"),
      ...ep(["VCC","QA","SER","OE","RCLK","SRCLK","SRCLR","QH'"], "R"),
    ],
  },
  "wokwi-74hc165": {
    label: "74HC165", w: 110, h: 160, fill: "#0f3a3a",
    pins: [
      ...ep(["SH/LD","CLK","E","F","G","H","QH'","GND"], "L"),
      ...ep(["VCC","QH","SER","A","B","C","D","CLK_INH"], "R"),
    ],
  },
  "wokwi-not-gate": {
    label: "NOT", w: 70, h: 50, fill: "#0f3a3a",
    pins: [...ep(["IN"], "L"), ...ep(["OUT"], "R")],
  },
  "wokwi-and-gate": {
    label: "AND", w: 70, h: 60, fill: "#0f3a3a",
    pins: [...ep(["IN1","IN2"], "L"), ...ep(["OUT"], "R")],
  },
  "wokwi-or-gate": {
    label: "OR", w: 70, h: 60, fill: "#0f3a3a",
    pins: [...ep(["IN1","IN2"], "L"), ...ep(["OUT"], "R")],
  },
  "wokwi-xor-gate": {
    label: "XOR", w: 70, h: 60, fill: "#0f3a3a",
    pins: [...ep(["IN1","IN2"], "L"), ...ep(["OUT"], "R")],
  },
  "wokwi-nand-gate": {
    label: "NAND", w: 70, h: 60, fill: "#0f3a3a",
    pins: [...ep(["IN1","IN2"], "L"), ...ep(["OUT"], "R")],
  },
  "wokwi-mux": {
    label: "Multiplexer", w: 100, h: 110, fill: "#0f3a3a",
    pins: [
      ...ep(["I0","I1","I2","I3","S0","S1"], "L"),
      ...ep(["OUT","EN"], "R"),
    ],
  },
  "wokwi-flipflop-d": {
    label: "D Flip-Flop", w: 100, h: 90, fill: "#0f3a3a",
    pins: [
      ...ep(["D","CLK","RESET"], "L"),
      ...ep(["Q","Q'"], "R"),
    ],
  },
  "wokwi-flipflop-dsr": {
    label: "D-SR Flip-Flop", w: 100, h: 100, fill: "#0f3a3a",
    pins: [
      ...ep(["D","CLK","SET","RESET"], "L"),
      ...ep(["Q","Q'"], "R"),
    ],
  },

  // ── Passives & Other ──────────────────────────────────────────────────────
  "wokwi-resistor": {
    label: "R", w: 70, h: 40, fill: "#2a2a2a",
    pins: [...ep(["1"], "L"), ...ep(["2"], "R")],
  },
  "wokwi-capacitor": {
    label: "C", w: 70, h: 40, fill: "#2a2a2a",
    pins: [...ep(["1"], "L"), ...ep(["2"], "R")],
  },
  "wokwi-buzzer": {
    label: "Buzzer", w: 70, h: 50, fill: "#2a2a2a",
    pins: [...ep(["1"], "L"), ...ep(["2"], "R")],
  },
  "wokwi-relay-module": {
    label: "Relay", w: 100, h: 100, fill: "#2a2a2a",
    pins: [
      ...ep(["VCC","GND","IN"], "L"),
      ...ep(["COM","NO","NC"], "R"),
    ],
  },
  "wokwi-ks2e-m-dc5": {
    label: "DPDT Relay", w: 100, h: 100, fill: "#2a2a2a",
    pins: [
      ...ep(["A1","A2"], "L"),
      ...ep(["11","12","14","21","22","24"], "R"),
    ],
  },
  "wokwi-tilt-switch": {
    label: "Tilt Switch", w: 70, h: 50, fill: "#2a2a2a",
    pins: [...ep(["1"], "L"), ...ep(["2"], "R")],
  },
  "wokwi-npn-transistor": {
    label: "NPN", w: 80, h: 70, fill: "#2a2a2a",
    pins: [...ep(["B"], "L"), ...ep(["C","E"], "R")],
  },
  "wokwi-pnp-transistor": {
    label: "PNP", w: 80, h: 70, fill: "#2a2a2a",
    pins: [...ep(["B"], "L"), ...ep(["C","E"], "R")],
  },
  "wokwi-microsd-card": {
    label: "MicroSD", w: 100, h: 100, fill: "#2a2a2a",
    pins: ep(["VCC","GND","SCK","MOSI","MISO","CS"], "L"),
  },
  "wokwi-logic-analyzer": {
    label: "Logic Analyzer", w: 110, h: 140, fill: "#1a1a1a",
    pins: ep(["D0","D1","D2","D3","D4","D5","D6","D7","GND"], "L"),
  },
  "wokwi-clock-generator": {
    label: "Clock Gen", w: 90, h: 60, fill: "#2a2a2a",
    pins: [...ep(["VCC","GND"], "L"), ...ep(["OUT"], "R")],
  },
  "wokwi-breadboard": {
    label: "Breadboard", w: 180, h: 100, fill: "#1e1e1e",
    pins: [],
  },
  "wokwi-breadboard-half": {
    label: "Breadboard Half", w: 130, h: 80, fill: "#1e1e1e",
    pins: [],
  },
  "wokwi-breadboard-mini": {
    label: "Breadboard Mini", w: 100, h: 60, fill: "#1e1e1e",
    pins: [],
  },
  "wokwi-text": {
    label: "Text", w: 80, h: 40, fill: "#111",
    pins: [],
  },
};

// ─── Wire color map ─────────────────────────────────────────────────────────

const WIRE_COLOR: Record<string, string> = {
  red:    "#ef4444",
  black:  "#6b7280",
  green:  "#22c55e",
  blue:   "#3b82f6",
  yellow: "#eab308",
  orange: "#f97316",
  purple: "#a855f7",
  white:  "#e5e7eb",
  gray:   "#9ca3af",
  grey:   "#9ca3af",
};

// ─── CircuitViewer ──────────────────────────────────────────────────────────

interface Props { diag_json: string; }

export interface CircuitViewerHandle {
  downloadSVG: () => void;
}

interface Box { id: string; x: number; y: number; w: number; h: number; }

const CircuitViewer = forwardRef<CircuitViewerHandle, Props>(function CircuitViewer({ diag_json }, ref) {
  const [zoom, setZoom] = useState(1);
  const svgRef = useRef<SVGSVGElement>(null);

  const diagram = useMemo(() => {
    try { return JSON.parse(diag_json); } catch { return null; }
  }, [diag_json]);

  useImperativeHandle(ref, () => ({
    downloadSVG() {
      if (!svgRef.current) return;
      const svgStr = new XMLSerializer().serializeToString(svgRef.current);
      const blob = new Blob([svgStr], { type: "image/svg+xml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "circuit-diagram.svg";
      a.click();
      URL.revokeObjectURL(url);
    },
  }));

  if (!diagram) return (
    <div className="flex items-center justify-center h-48 text-gray-500 text-sm rounded-lg bg-[#0a0a0a]">
      No circuit diagram available
    </div>
  );

  const allParts: any[]       = diagram.parts       ?? [];
  const allConnections: any[] = diagram.connections ?? [];

  const parts = allParts.filter((p: any) => p.type !== "wokwi-logic-analyzer");
  const partIds = new Set(parts.map((p: any) => p.id));

  const connections = allConnections.filter(([from, to]: [string, string]) => {
    const fromId = from.split(":")[0];
    const toId = to.split(":")[0];
    return partIds.has(fromId) && partIds.has(toId);
  });

  // ── Resolve part → def ──
  const defFor: Record<string, ComponentDef> = {};
  for (const p of parts) {
    defFor[p.id] = DEFS[p.type] ?? {
      label: (p.type ?? "?").replace(/^wokwi-|^board-/, ""),
      w: 100, h: 80, fill: "#2a2a2a", pins: [],
    };
  }

  // ── AUTO-LAYOUT: re-space components so none overlap and every
  //    component has breathing room, regardless of what top/left the
  //    LLM originally assigned. We keep relative left→right / top→bottom
  //    ORDER from the source diagram (so the layout still "reads" the
  //    way it was intended) but enforce real minimum gaps.
  // ──────────────────────────────────────────────────────────────────
  const MIN_GAP_X = 130;   // min horizontal gap between component edges
  const MIN_GAP_Y = 110;   // min vertical gap between component edges
  const COLS = Math.max(1, Math.ceil(Math.sqrt(parts.length)));

  // Sort by original position (reading order: top-to-bottom, left-to-right)
  const ordered = [...parts].sort((a, b) => {
    const ay = a.top ?? 0, by = b.top ?? 0;
    if (Math.abs(ay - by) > 40) return ay - by;
    return (a.left ?? 0) - (b.left ?? 0);
  });

  // Identify the "main" board (microcontroller) — keep it anchored at origin,
  // arrange everything else in a grid around it with generous spacing.
  const isBoard = (p: any) => /arduino|esp32|pico|nucleo|bluepill|attiny/i.test(p.type);
  const board = ordered.find(isBoard);
  const others = ordered.filter((p) => p !== board);

  const laidOut: Record<string, { x: number; y: number }> = {};

  if (board) {
    const bd = defFor[board.id];
    laidOut[board.id] = { x: 0, y: 0 };

    // Place remaining components in a column to the right of the board,
    // each spaced by the previous component's height + MIN_GAP_Y, and
    // far enough right of the board (MIN_GAP_X) to leave room for wires.
    const colX = bd.w + MIN_GAP_X;
    let cursorY = 0;
    let col = 0;
    let colHeights: number[] = [0];
    const maxPerCol = Math.max(2, Math.ceil(others.length / 2));

    others.forEach((p, i) => {
      const def = defFor[p.id];
      if (i > 0 && i % maxPerCol === 0) {
        col += 1;
        cursorY = 0;
        colHeights.push(0);
      }
      const x = colX + col * (220 + MIN_GAP_X);
      const y = cursorY;
      laidOut[p.id] = { x, y };
      cursorY += def.h + MIN_GAP_Y;
    });
  } else {
    // No board found — simple grid fallback
    let cursorX = 0, cursorY = 0, rowH = 0, colCount = 0;
    ordered.forEach((p) => {
      const def = defFor[p.id];
      laidOut[p.id] = { x: cursorX, y: cursorY };
      cursorX += def.w + MIN_GAP_X;
      rowH = Math.max(rowH, def.h);
      colCount += 1;
      if (colCount >= COLS) {
        colCount = 0;
        cursorX = 0;
        cursorY += rowH + MIN_GAP_Y;
        rowH = 0;
      }
    });
  }

  const partMap: Record<string, { x: number; y: number; def: ComponentDef }> = {};
  for (const p of parts) {
    const pos = laidOut[p.id] ?? { x: p.left ?? 0, y: p.top ?? 0 };
    partMap[p.id] = { x: pos.x, y: pos.y, def: defFor[p.id] };
  }

  const boxes: Box[] = parts.map((p: any) => {
    const e = partMap[p.id];
    return { id: p.id, x: e.x, y: e.y, w: e.def.w, h: e.def.h };
  });

  // ── Resolve "partId:pinName" → absolute pixel coords ──
  function resolvePin(ref: string): { px: number; py: number; side?: Side; partId: string } | null {
    const sep = ref.indexOf(":");
    if (sep < 0) return null;
    const partId  = ref.slice(0, sep);
    const pinName = ref.slice(sep + 1);
    const entry   = partMap[partId];
    if (!entry) return null;
    const { x, y, def } = entry;
    const pin = def.pins.find((p) => p.name === pinName);
    if (!pin) return { px: x + def.w / 2, py: y + def.h / 2, partId };
    const { px, py } = pinPos(pin, def.w, def.h);
    return { px: x + px, py: y + py, side: pin.side, partId };
  }

  // ── Collision-aware Manhattan routing ──
  // Exits perpendicular from the pin (stub), then routes via a midpoint
  // chosen to avoid passing directly through any other component's box.
  const STUB = 26;

  // Tracks which vertical "lanes" (mx rounded to nearest 10px) are already
  // occupied by a wire over which Y range, so unrelated wires don't share
  // the same lane and visually overlap each other.
  const usedLanes = new Map<number, Array<[number, number]>>();

  function stubPoint(p: { px: number; py: number; side?: Side }) {
    switch (p.side) {
      case "T": return { x: p.px, y: p.py - STUB };
      case "B": return { x: p.px, y: p.py + STUB };
      case "L": return { x: p.px - STUB, y: p.py };
      case "R": return { x: p.px + STUB, y: p.py };
      default:  return { x: p.px, y: p.py };
    }
  }

  /** Does a vertical line at x=vx between y1 and y2 cross any box
   *  (other than the two endpoints' own parts)? */
  function verticalCrossesBox(vx: number, y1: number, y2: number, excludeIds: string[]): boolean {
    const lo = Math.min(y1, y2), hi = Math.max(y1, y2);
    for (const b of boxes) {
      if (excludeIds.includes(b.id)) continue;
      const withinX = vx > b.x && vx < b.x + b.w;
      const overlapsY = hi > b.y && lo < b.y + b.h;
      if (withinX && overlapsY) return true;
    }
    return false;
  }

  function route(
    from: { px: number; py: number; side?: Side; partId: string },
    to:   { px: number; py: number; side?: Side; partId: string },
    offset = 0
  ): string {
    const a = stubPoint(from);
    const b = stubPoint(to);
    const exclude = [from.partId, to.partId];

    let mx = (a.x + b.x) / 2 + offset;

    // If the chosen midpoint's vertical run would cut through another
    // component, push it outward step by step until it's clear (max 6 tries).
    let attempts = 0;
    const step = 40;
    while (verticalCrossesBox(mx, a.y, b.y, exclude) && attempts < 6) {
      mx += (offset >= 0 ? step : -step);
      attempts += 1;
    }

    // If this lane (mx, rounded to nearest 10px) is already used by a
    // DIFFERENT component pair's wire whose Y range overlaps ours, nudge
    // further until we find a free lane — this is what stops a green wire
    // from one pair visually crossing a grey wire from a different pair.
    const lo = Math.min(a.y, b.y), hi = Math.max(a.y, b.y);
    let laneAttempts = 0;
    while (laneAttempts < 8) {
      const laneKey = Math.round(mx / 10);
      const used = usedLanes.get(laneKey);
      const overlaps = used && used.some(([ulo, uhi]) => hi > ulo && lo < uhi);
      if (!overlaps) break;
      mx += (offset >= 0 ? 18 : -18) || 18;
      laneAttempts += 1;
    }
    const laneKey = Math.round(mx / 10);
    const existing = usedLanes.get(laneKey) ?? [];
    existing.push([lo, hi]);
    usedLanes.set(laneKey, existing);

    return `${from.px},${from.py} ${a.x},${a.y} ${mx},${a.y} ${mx},${b.y} ${b.x},${b.y} ${to.px},${to.py}`;
  }

  // Stagger wires between the same component pair so they fan out
  // instead of stacking on the same vertical line.
  const pairCounts: Record<string, number> = {};
  function offsetForConn(conn: any): number {
    const a = String(conn[0]).split(":")[0];
    const b = String(conn[1]).split(":")[0];
    const key = [a, b].sort().join("|");
    const n = pairCounts[key] ?? 0;
    pairCounts[key] = n + 1;
    if (n === 0) return 0;
    const mag = Math.ceil(n / 2) * 16;
    return n % 2 === 1 ? mag : -mag;
  }

  // ── ViewBox — computed from the LAID-OUT positions, not source coords ──
  // Extra left/top padding so pin labels on the L/T sides (which extend
  // OUTWARD from the box, not inward) never clip against the viewBox edge.
  const PAD = 90;
  const LABEL_PAD = 60;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const b of boxes) {
    // Left/top get extra LABEL_PAD on top of PAD since "L" and "T" side
    // pin labels extend outward from the box past the wire stub itself.
    x0 = Math.min(x0, b.x - PAD - LABEL_PAD);
    y0 = Math.min(y0, b.y - PAD - LABEL_PAD);
    x1 = Math.max(x1, b.x + b.w + PAD);
    y1 = Math.max(y1, b.y + b.h + PAD);
  }
  if (!parts.length) { x0 = 0; y0 = 0; x1 = 400; y1 = 300; }
  const vbW = x1 - x0, vbH = y1 - y0;

  return (
    <div className="relative w-full rounded-xl overflow-hidden bg-[#0a0a0a] border border-gray-800"
         style={{ height: "520px" }}>

      {/* ── Zoom bar ── */}
      <div className="absolute top-3 right-3 z-10 flex gap-1 bg-[#111] rounded-lg p-1 border border-gray-800">
        {[0.5, 0.75, 1, 1.5, 2].map((z) => (
          <button
            key={z}
            onClick={() => setZoom(z)}
            className={`px-2 py-0.5 rounded text-xs font-mono transition-colors
              ${zoom === z
                ? "bg-teal-700 text-white"
                : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"}`}
          >
            {z}×
          </button>
        ))}
      </div>

      {/* ── Legend ── */}
      <div className="absolute bottom-3 left-3 z-10 flex gap-3 flex-wrap">
        {[
          { color: "#ef4444", label: "Power" },
          { color: "#6b7280", label: "GND" },
          { color: "#22c55e", label: "Signal" },
          { color: "#3b82f6", label: "SDA/Data" },
          { color: "#eab308", label: "SCL/Clock" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1">
            <div className="w-3 h-0.5 rounded" style={{ backgroundColor: color }} />
            <span className="text-gray-500 text-xs font-mono">{label}</span>
          </div>
        ))}
      </div>

      {/* ── SVG Canvas ── */}
      <svg
        ref={svgRef}
        width="100%"
        height="100%"
        viewBox={`${x0} ${y0} ${vbW} ${vbH}`}
        style={{
          transform: `scale(${zoom})`,
          transformOrigin: "center center",
          transition: "transform 0.15s ease",
        }}
      >
        {/* Dot grid */}
        <defs>
          <pattern id="cc-grid" width="20" height="20" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="0.6" fill="#252525" />
          </pattern>
        </defs>
        <rect x={x0} y={y0} width={vbW} height={vbH} fill="url(#cc-grid)" />

        {/* ── Pass 1: Component boxes + labels ── */}
        {parts.map((part: any) => {
          const entry = partMap[part.id];
          if (!entry) return null;
          const { x, y, def } = entry;

          return (
            <g key={`box-${part.id}`} transform={`translate(${x},${y})`}>
              <rect
                width={def.w} height={def.h}
                rx={5} ry={5}
                fill={def.fill}
                stroke="#3a3a3a"
                strokeWidth={1.5}
              />
              <text
                x={def.w / 2} y={def.h / 2 - 5}
                textAnchor="middle"
                fill="#f0f0f0"
                fontSize={11}
                fontFamily="ui-monospace, monospace"
                fontWeight="600"
              >
                {def.label}
              </text>
              <text
                x={def.w / 2} y={def.h / 2 + 9}
                textAnchor="middle"
                fill="#6b7280"
                fontSize={8.5}
                fontFamily="ui-monospace, monospace"
              >
                {part.id}
                {part.attrs?.value ? ` · ${part.attrs.value}` : ""}
                {part.attrs?.color ? ` · ${part.attrs.color}` : ""}
              </text>
            </g>
          );
        })}

        {/* ── Pass 2: Wires ── */}
        {connections.map((conn: any, i: number) => {
          if (!Array.isArray(conn) || conn.length < 2) return null;
          const from = resolvePin(conn[0]);
          const to   = resolvePin(conn[1]);
          if (!from || !to) return null;
          const stroke = WIRE_COLOR[conn[2]] ?? "#9ca3af";
          const offset = offsetForConn(conn);
          return (
            <polyline
              key={`w${i}`}
              points={route(from, to, offset)}
              fill="none"
              stroke={stroke}
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
              opacity={0.9}
            />
          );
        })}

        {/* ── Pass 3: Pin dots + labels (always on top) ── */}
        {parts.map((part: any) => {
          const entry = partMap[part.id];
          if (!entry) return null;
          const { x, y, def } = entry;

          return (
            <g key={`pins-${part.id}`} transform={`translate(${x},${y})`}>
              {def.pins.map((pin) => {
                const { px: ppx, py: ppy } = pinPos(pin, def.w, def.h);
                const lp = pinLabel(pin, ppx, ppy);
                const labelW = pin.name.length * 4.5 + 2;
                let bgX: number;
                if (lp.anchor === "start") bgX = lp.x - 1;
                else if (lp.anchor === "end") bgX = lp.x - labelW + 1;
                else bgX = lp.x - labelW / 2;
                return (
                  <g key={pin.name}>
                    <rect
                      x={bgX}
                      y={lp.y - 7}
                      width={labelW}
                      height={9}
                      fill={def.fill}
                      opacity={0.85}
                    />
                    <text
                      x={lp.x} y={lp.y}
                      textAnchor={lp.anchor}
                      fill="#94a3b8"
                      fontSize={7.5}
                      fontFamily="ui-monospace, monospace"
                    >
                      {pin.name}
                    </text>
                    <circle
                      cx={ppx} cy={ppy} r={3.5}
                      fill="#f59e0b"
                      stroke="#0a0a0a"
                      strokeWidth={1}
                    />
                  </g>
                );
              })}
            </g>
          );
        })}
      </svg>
    </div>
  );
});

export default CircuitViewer;