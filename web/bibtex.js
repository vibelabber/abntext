/**
 * Extracts the last name of the first listed author and appends the year.
 * Author string: last-name-first, comma-separated. Multiple authors separated by " and ".
 * Examples:
 *   generateCiteKey("Silva, João", "2023")              → "Silva2023"
 *   generateCiteKey("Souza, Maria and Silva, João", "2020") → "Souza2020"
 *   generateCiteKey("João Silva", "2021")               → "Silva2021"
 *
 * @param {string} author
 * @param {string} year
 * @returns {string}
 */
export function generateCiteKey(author, year) {
  const firstAuthor = author.split(' and ')[0].trim()
  const lastName = firstAuthor.includes(',')
    ? firstAuthor.split(',')[0].trim()
    : firstAuthor.split(' ').pop()
  return `${lastName}${year.trim()}`
}

/**
 * Serializes a single BibTeX entry object to a BibTeX string block.
 * Supported types: 'book', 'online'.
 *
 * @param {{ type: string, author: string, title: string, year: string, [key: string]: string }} entry
 * @returns {string}
 */
export function serializeEntry(entry) {
  if (entry.type !== 'book' && entry.type !== 'online') {
    throw new Error(`Unknown entry type: ${entry.type}`)
  }

  const key = generateCiteKey(entry.author, entry.year)

  if (entry.type === 'book') {
    return [
      `@book{${key},`,
      `  author    = {${entry.author}},`,
      `  title     = {${entry.title}},`,
      `  publisher = {${entry.publisher}},`,
      `  address   = {${entry.address}},`,
      `  year      = {${entry.year}},`,
      `}`,
    ].join('\n')
  }

  if (entry.type === 'online') {
    return [
      `@online{${key},`,
      `  author  = {${entry.author}},`,
      `  title   = {${entry.title}},`,
      `  url     = {${entry.url}},`,
      `  urldate = {${entry.urldate}},`,
      `  year    = {${entry.year}},`,
      `}`,
    ].join('\n')
  }
}

/**
 * Serializes an array of entry objects to a full .bib file string.
 * Entries are separated by a blank line.
 *
 * @param {object[]} entries
 * @returns {string}
 */
export function serializeBibFile(entries) {
  return entries.map(serializeEntry).join('\n\n')
}
