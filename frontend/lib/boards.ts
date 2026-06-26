export interface Board {
  name: string
  fqbn: string
  shortName: string
}

export const BOARDS: Board[] = [
  { name: 'Arduino Uno',    fqbn: 'arduino:avr:uno',       shortName: 'Uno'    },
  { name: 'Arduino Nano',   fqbn: 'arduino:avr:nano',      shortName: 'Nano'   },
  { name: 'Arduino Mega',   fqbn: 'arduino:avr:mega',      shortName: 'Mega'   },
  { name: 'ESP32 DevKit v1',fqbn: 'esp32:esp32:esp32',     shortName: 'ESP32'  },
]

export function getBoardByName(name: string): Board | undefined {
  return BOARDS.find(b => b.name === name)
}
