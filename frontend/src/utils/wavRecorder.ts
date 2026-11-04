/**
 * Microphone capture to a 24 kHz mono WAV (base64), the format the
 * transcription endpoint accepts. Uses WebAudio only — no dependency.
 */

export type WavRecorder = {
  stop: () => Promise<string>
}

function downsample(samples: Float32Array, from: number, to: number): Float32Array {
  if (from === to) {
    return samples
  }
  const ratio = from / to
  const out = new Float32Array(Math.floor(samples.length / ratio))
  for (let i = 0; i < out.length; i += 1) {
    out[i] = samples[Math.floor(i * ratio)] ?? 0
  }
  return out
}

function encodeWavBase64(samples: Float32Array, sampleRate: number): string {
  const buffer = new ArrayBuffer(44 + samples.length * 2)
  const view = new DataView(buffer)
  const writeText = (offset: number, text: string) => {
    for (let i = 0; i < text.length; i += 1) {
      view.setUint8(offset + i, text.charCodeAt(i))
    }
  }
  writeText(0, 'RIFF')
  view.setUint32(4, 36 + samples.length * 2, true)
  writeText(8, 'WAVEfmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeText(36, 'data')
  view.setUint32(40, samples.length * 2, true)
  for (let i = 0; i < samples.length; i += 1) {
    const clamped = Math.max(-1, Math.min(1, samples[i] ?? 0))
    view.setInt16(44 + i * 2, clamped * 0x7fff, true)
  }
  let binary = ''
  const bytes = new Uint8Array(buffer)
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i] ?? 0)
  }
  return window.btoa(binary)
}

function mergeChunks(chunks: Float32Array[]): Float32Array {
  const total = chunks.reduce((sum, chunk) => sum + chunk.length, 0)
  const merged = new Float32Array(total)
  let offset = 0
  for (const chunk of chunks) {
    merged.set(chunk, offset)
    offset += chunk.length
  }
  return merged
}

function encodeChunks(chunks: Float32Array[], rate: number): string {
  return encodeWavBase64(downsample(mergeChunks(chunks), rate, 24000), 24000)
}

export async function startWavRecording(): Promise<WavRecorder> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  const context = new AudioContext()
  const source = context.createMediaStreamSource(stream)
  const processor = context.createScriptProcessor(4096, 1, 1)
  const chunks: Float32Array[] = []
  processor.onaudioprocess = (event) => {
    chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)))
  }
  source.connect(processor)
  processor.connect(context.destination)
  return {
    stop: async () => {
      processor.disconnect()
      source.disconnect()
      stream.getTracks().forEach((track) => track.stop())
      const rate = context.sampleRate
      await context.close()
      return encodeChunks(chunks, rate)
    },
  }
}

/**
 * Live variant of `startWavRecording`: same capture and encoder, but every
 * `intervalMs` the cumulative buffer is encoded and handed to `onPartial`.
 * `stop()` returns the final base64, byte-identical to the one-shot path
 * for the same audio.
 */
export async function startLiveWavRecording(
  onPartial: (wavBase64SoFar: string) => void,
  intervalMs = 1500,
): Promise<WavRecorder> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  const context = new AudioContext()
  const source = context.createMediaStreamSource(stream)
  const processor = context.createScriptProcessor(4096, 1, 1)
  const chunks: Float32Array[] = []
  processor.onaudioprocess = (event) => {
    chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)))
  }
  source.connect(processor)
  processor.connect(context.destination)
  const timer = window.setInterval(() => {
    onPartial(encodeChunks(chunks, context.sampleRate))
  }, intervalMs)
  return {
    stop: async () => {
      window.clearInterval(timer)
      processor.disconnect()
      source.disconnect()
      stream.getTracks().forEach((track) => track.stop())
      const rate = context.sampleRate
      await context.close()
      return encodeChunks(chunks, rate)
    },
  }
}
