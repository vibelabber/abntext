import { describe, it, expect } from 'vitest'
import { generateCiteKey, serializeEntry } from '../../web/bibtex.js'

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

  it('trims whitespace from year', () => {
    expect(generateCiteKey('Silva, João', '  2023  ')).toBe('Silva2023')
  })
})

describe('serializeEntry', () => {
  it('serializes a @book entry with correct field order and braces', () => {
    const entry = {
      type: 'book',
      author: 'Silva, João',
      title: 'Título do Livro',
      publisher: 'Editora Exemplo',
      address: 'São Paulo',
      year: '2023',
    }
    const expected = [
      '@book{Silva2023,',
      '  author    = {Silva, João},',
      '  title     = {Título do Livro},',
      '  publisher = {Editora Exemplo},',
      '  address   = {São Paulo},',
      '  year      = {2023},',
      '}',
    ].join('\n')
    expect(serializeEntry(entry)).toBe(expected)
  })

  it('serializes an @online entry with correct field order and braces', () => {
    const entry = {
      type: 'online',
      author: 'Souza, Maria',
      title: 'Título do Artigo Online',
      url: 'https://exemplo.com',
      urldate: '2022-05-10',
      year: '2022',
    }
    const expected = [
      '@online{Souza2022,',
      '  author  = {Souza, Maria},',
      '  title   = {Título do Artigo Online},',
      '  url     = {https://exemplo.com},',
      '  urldate = {2022-05-10},',
      '  year    = {2022},',
      '}',
    ].join('\n')
    expect(serializeEntry(entry)).toBe(expected)
  })

  it('throws for unknown entry types', () => {
    expect(() => serializeEntry({ type: 'unknown' })).toThrow('Unknown entry type: unknown')
  })
})
