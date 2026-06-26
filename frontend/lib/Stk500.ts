// ─── Intel HEX Parser ────────────────────────────────────────────────────────

export function parseHex(hexText: string): Uint8Array {
  const lines = hexText.trim().split('\n')
  let baseAddress = 0
  const segments: { addr: number; data: Uint8Array }[] = []
  let maxAddr = 0

  for (const line of lines) {
    const l = line.trim()
    if (!l.startsWith(':')) continue
    const bytes = new Uint8Array(l.slice(1).match(/.{2}/g)!.map(b => parseInt(b, 16)))
    const byteCount = bytes[0]
    const address   = (bytes[1] << 8) | bytes[2]
    const recordType = bytes[3]

    if (recordType === 0x01) break                                      // EOF
    if (recordType === 0x04) { baseAddress = ((bytes[4] << 8) | bytes[5]) << 16; continue } // extended linear
    if (recordType === 0x02) { baseAddress = ((bytes[4] << 8) | bytes[5]) << 4;  continue } // extended segment
    if (recordType === 0x00) {
      const absAddr = baseAddress + address
      const data = bytes.slice(4, 4 + byteCount)
      segments.push({ addr: absAddr, data })
      maxAddr = Math.max(maxAddr, absAddr + byteCount)
    }
  }

  const result = new Uint8Array(maxAddr).fill(0xFF)
  for (const seg of segments) result.set(seg.data, seg.addr)
  return result
}

// ─── Serial helpers ───────────────────────────────────────────────────────────

async function readBytes(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  count: number,
  timeout = 5000
): Promise<Uint8Array> {
  const buf: number[] = []
  const deadline = Date.now() + timeout
  while (buf.length < count) {
    if (Date.now() > deadline) throw new Error('Read timeout')
    const { value, done } = await reader.read()
    if (done) throw new Error('Stream closed')
    if (value) buf.push(...value)
  }
  return new Uint8Array(buf.slice(0, count))
}

async function writeBytes(
  writer: WritableStreamDefaultWriter<Uint8Array>,
  data: Uint8Array
): Promise<void> {
  await writer.write(data)
}

// ─── DTR Reset ───────────────────────────────────────────────────────────────

async function dtrReset(port: SerialPort): Promise<void> {
  await port.setSignals({ dataTerminalReady: false })
  await new Promise(r => setTimeout(r, 250))
  await port.setSignals({ dataTerminalReady: true })
  await new Promise(r => setTimeout(r, 50))
}

// ─── STK500v1 — Uno / Nano (ATmega328P, page size 128 bytes) ─────────────────

const STK = {
  OK:             0x10,
  INSYNC:         0x14,
  CRC_EOP:        0x20,
  GET_SYNC:       0x30,
  ENTER_PROGMODE: 0x50,
  LEAVE_PROGMODE: 0x51,
  LOAD_ADDRESS:   0x55,
  PROG_PAGE:      0x64,
} as const

const PAGE_SIZE_V1 = 128

async function stk500v1Flash(
  port: SerialPort,
  binary: Uint8Array,
  onProgress: (pct: number) => void
): Promise<void> {
  const reader = port.readable!.getReader()
  const writer = port.writable!.getWriter()

  try {
    // Sync — retry up to 10 times
    let synced = false
    for (let i = 0; i < 10; i++) {
      await writeBytes(writer, new Uint8Array([STK.GET_SYNC, STK.CRC_EOP]))
      try {
        const resp = await readBytes(reader, 2, 400)
        if (resp[0] === STK.INSYNC && resp[1] === STK.OK) { synced = true; break }
      } catch { /* retry */ }
    }
    if (!synced) throw new Error('STK500v1: failed to sync with board')

    // Enter programming mode
    await writeBytes(writer, new Uint8Array([STK.ENTER_PROGMODE, STK.CRC_EOP]))
    const enterResp = await readBytes(reader, 2, 2000)
    if (enterResp[0] !== STK.INSYNC || enterResp[1] !== STK.OK)
      throw new Error('STK500v1: enter progmode failed')

    // Flash pages
    const totalPages = Math.ceil(binary.length / PAGE_SIZE_V1)
    for (let page = 0; page < totalPages; page++) {
      const wordAddr = (page * PAGE_SIZE_V1) / 2
      const pageData = binary.slice(page * PAGE_SIZE_V1, (page + 1) * PAGE_SIZE_V1)
      const padded = new Uint8Array(PAGE_SIZE_V1).fill(0xFF)
      padded.set(pageData)

      // Load address (word address)
      await writeBytes(writer, new Uint8Array([
        STK.LOAD_ADDRESS,
        wordAddr & 0xFF,
        (wordAddr >> 8) & 0xFF,
        STK.CRC_EOP,
      ]))
      const addrResp = await readBytes(reader, 2, 2000)
      if (addrResp[0] !== STK.INSYNC || addrResp[1] !== STK.OK)
        throw new Error(`STK500v1: load address failed at page ${page}`)

      // Program page
      await writeBytes(writer, new Uint8Array([
        STK.PROG_PAGE,
        (PAGE_SIZE_V1 >> 8) & 0xFF,
        PAGE_SIZE_V1 & 0xFF,
        0x46, // 'F' = flash
        ...padded,
        STK.CRC_EOP,
      ]))
      const progResp = await readBytes(reader, 2, 5000)
      if (progResp[0] !== STK.INSYNC || progResp[1] !== STK.OK)
        throw new Error(`STK500v1: prog page failed at page ${page}`)

      onProgress(Math.round(((page + 1) / totalPages) * 100))
    }

    // Leave programming mode
    await writeBytes(writer, new Uint8Array([STK.LEAVE_PROGMODE, STK.CRC_EOP]))
    await readBytes(reader, 2, 2000)

  } finally {
    reader.releaseLock()
    writer.releaseLock()
  }
}

// ─── STK500v2 — Mega (ATmega2560, page size 256 bytes) ───────────────────────

const STK2 = {
  MESSAGE_START:          0x1B,
  TOKEN:                  0x0E,
  CMD_SIGN_ON:            0x01,
  CMD_ENTER_PROGMODE_ISP: 0x10,
  CMD_LEAVE_PROGMODE_ISP: 0x11,
  CMD_LOAD_ADDRESS:       0x06,
  CMD_PROGRAM_FLASH_ISP:  0x13,
  STATUS_CMD_OK:          0x00,
} as const

const PAGE_SIZE_V2 = 256

function stk2Checksum(data: Uint8Array): number {
  return data.reduce((acc, b) => acc ^ b, 0)
}

function stk2BuildMessage(seqNum: number, body: Uint8Array): Uint8Array {
  const header = new Uint8Array([
    STK2.MESSAGE_START,
    seqNum,
    (body.length >> 8) & 0xFF,
    body.length & 0xFF,
    STK2.TOKEN,
  ])
  const msg = new Uint8Array(header.length + body.length + 1)
  msg.set(header, 0)
  msg.set(body, header.length)
  msg[msg.length - 1] = stk2Checksum(msg.slice(0, -1))
  return msg
}

async function stk2ReadMessage(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  timeout = 5000
): Promise<Uint8Array> {
  // Scan for MESSAGE_START
  while (true) {
    const b = await readBytes(reader, 1, timeout)
    if (b[0] === STK2.MESSAGE_START) break
  }
  // seqNum(1) + size(2) + token(1)
  const header = await readBytes(reader, 4, timeout)
  const bodyLen = (header[1] << 8) | header[2]
  // body + checksum
  const body = await readBytes(reader, bodyLen + 1, timeout)
  return body.slice(0, bodyLen)
}

async function stk500v2Flash(
  port: SerialPort,
  binary: Uint8Array,
  onProgress: (pct: number) => void
): Promise<void> {
  const reader = port.readable!.getReader()
  const writer = port.writable!.getWriter()
  let seq = 1

  const send = async (body: Uint8Array): Promise<Uint8Array> => {
    await writeBytes(writer, stk2BuildMessage(seq++ & 0xFF, body))
    return stk2ReadMessage(reader)
  }

  try {
    // Sign on
    await send(new Uint8Array([STK2.CMD_SIGN_ON]))

    // Enter programming mode
    await send(new Uint8Array([
      STK2.CMD_ENTER_PROGMODE_ISP,
      200,  // timeout
      200,  // stabDelay
      0,    // cmdexeDelay
      19,   // synchLoops
      0,    // byteDelay
      0x53, // pollValue
      0,    // pollIndex
      0xAC, 0x53, 0x00, 0x00, // SPI enter prog mode command
    ]))

    // Flash pages
    const totalPages = Math.ceil(binary.length / PAGE_SIZE_V2)
    for (let page = 0; page < totalPages; page++) {
      const byteAddr = page * PAGE_SIZE_V2
      const pageData = binary.slice(byteAddr, byteAddr + PAGE_SIZE_V2)
      const padded = new Uint8Array(PAGE_SIZE_V2).fill(0xFF)
      padded.set(pageData)

      // Load address — set bit 31 for extended (>64KB) addresses on Mega
      const useExtended = byteAddr > 0xFFFF
      await send(new Uint8Array([
        STK2.CMD_LOAD_ADDRESS,
        ((byteAddr >> 24) & 0xFF) | (useExtended ? 0x80 : 0x00),
        (byteAddr >> 16) & 0xFF,
        (byteAddr >> 8)  & 0xFF,
        byteAddr         & 0xFF,
      ]))

      // Program flash page
      await send(new Uint8Array([
        STK2.CMD_PROGRAM_FLASH_ISP,
        (PAGE_SIZE_V2 >> 8) & 0xFF,
        PAGE_SIZE_V2 & 0xFF,
        0x40, // mode: page write + erase before write
        0x09, // delay
        0x4C, // cmd1 — page write
        0x2C, // cmd2
        0x6D, // cmd3
        0x7A, // poll1
        0x7A, // poll2
        ...padded,
      ]))

      onProgress(Math.round(((page + 1) / totalPages) * 100))
    }

    // Leave programming mode
    await send(new Uint8Array([
      STK2.CMD_LEAVE_PROGMODE_ISP,
      1, // preDelay
      1, // postDelay
    ]))

  } finally {
    reader.releaseLock()
    writer.releaseLock()
  }
}

// ─── Public API ───────────────────────────────────────────────────────────────

export type FlashStatus = 'idle' | 'connecting' | 'resetting' | 'flashing' | 'done' | 'error'

const BOARD_BAUD: Record<string, number> = {
  'Arduino Uno':  115200,
  'Arduino Nano': 115200,
  'Arduino Mega': 115200,
}

export async function flashHex(
  hexText: string,
  board: string,
  onStatus: (status: FlashStatus) => void,
  onProgress: (pct: number) => void
): Promise<void> {
  onStatus('connecting')

  const port = await navigator.serial.requestPort()
  const baud = BOARD_BAUD[board] ?? 115200

  await port.open({ baudRate: baud })

  try {
    onStatus('resetting')
    await dtrReset(port)
    await new Promise(r => setTimeout(r, 250))

    onStatus('flashing')
    const binary = parseHex(hexText)

    if (board === 'Arduino Mega') {
      await stk500v2Flash(port, binary, onProgress)
    } else {
      await stk500v1Flash(port, binary, onProgress)
    }

    onStatus('done')
  } catch (err) {
    onStatus('error')
    throw err
  } finally {
    await port.close()
  }
}