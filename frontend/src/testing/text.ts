/**
 * Spec 005 §6: texts are compared with their spaces normalized, because the space before
 * «€», «US$» or «%» may be a non-breaking one.
 */
export function norm(text: string | null | undefined): string {
  return (text ?? '').replace(/\s+/g, ' ').trim();
}
