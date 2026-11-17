const LETTER = /\p{L}/u;

function lettersOf(word: string): string[] {
  return [...word].filter((character) => LETTER.test(character));
}

/**
 * Spec 006 CA-3.3: the first letter of each of the first two words with letters; with a single
 * such word, its first two letters; with none, «#». Always in capitals.
 */
export function initials(name: string): string {
  const words = name.split(/\s+/).filter((word) => LETTER.test(word));
  if (words.length === 0) {
    return '#';
  }
  const picked =
    words.length === 1
      ? lettersOf(words[0]).slice(0, 2)
      : words.slice(0, 2).map((w) => lettersOf(w)[0]);
  return picked.join('').toUpperCase();
}
