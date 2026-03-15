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
  return `${lastName}${year}`
}
