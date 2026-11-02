/** Read a File as raw base64 (no data-URL prefix). */
export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const result = reader.result
      if (typeof result !== 'string') {
        reject(new Error('Could not read file'))
        return
      }
      const comma = result.indexOf(',')
      resolve(comma >= 0 ? result.slice(comma + 1) : result)
    }
    reader.onerror = () => reject(reader.error ?? new Error('Could not read file'))
    reader.readAsDataURL(file)
  })
}

export function scanMediaType(file: File): 'image/png' | 'image/jpeg' | null {
  if (file.type === 'image/png') {
    return 'image/png'
  }
  if (file.type === 'image/jpeg' || file.type === 'image/jpg') {
    return 'image/jpeg'
  }
  return null
}

export function isWavFile(file: File): boolean {
  return file.type === 'audio/wav' || file.type === 'audio/wave' || file.name.toLowerCase().endsWith('.wav')
}
