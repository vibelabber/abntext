import { describe, it, expect } from 'vitest'
import { generateCiteKey } from '../../web/bibtex.js'

describe('generateCiteKey', () => {
  it('extracts last name before comma and appends year', () => {
    expect(generateCiteKey('Silva, João', '2023')).toBe('Silva2023')
  })

  it('uses last word when no comma present', () => {
    expect(generateCiteKey('João Silva', '2021')).toBe('Silva2021')
  })

  it('uses single token as-is when no comma or space', () => {
    expect(generateCiteKey('Silva', '2019')).toBe('Silva2019')
  })

  it('uses first listed author when multiple authors separated by " and "', () => {
    expect(generateCiteKey('Souza, Maria and Silva, João', '2020')).toBe('Souza2020')
  })

  it('trims whitespace from author name', () => {
    expect(generateCiteKey('  Silva, João  ', '2023')).toBe('Silva2023')
  })
})
