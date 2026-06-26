export interface Board {
  name: string
  fqbn: string
  shortName: string
}

export const BOARDS: Board[] = [
  { name: 'Arduino Uno',    fqbn: 'arduino:avr:uno',       shortName: 'Uno'    },
  { name: 'Arduino Nano',   fqbn: 'arduino:avr:nano',      shortName: 'Nano'   },
  { name: 'Arduino Mega',   fqbn: 'arduino:avr:mega',      shortName: 'Mega'   },
]

export function getBoardByName(name: string): Board | undefined {
  return BOARDS.find(b => b.name === name)
}
