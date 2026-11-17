import { initials } from './initials';

// Spec 006 §6.1 (IN-1 to IN-7): CA-3.3.
describe('initials (spec 006 §6.1)', () => {
  it.each([
    ['IN-1', 'Acme Telecom S.L.', 'AT'],
    ['IN-2', 'Estudio Lucía Ferrer', 'EL'],
    ['IN-3', 'pepeviyuela', 'PE'],
    ['IN-4', 'Ñandú Redes', 'ÑR'],
    ['IN-5', '3M España', 'ME'],
    ['IN-6', '123 456', '#'],
    ['IN-6', '', '#'],
    ['IN-7', '<b>Acme</b>', 'BA'],
  ])('%s: %j gives %j (CA-3.3)', (_id, name, expected) => {
    expect(initials(name)).toBe(expected);
  });

  it('a single letter is enough', () => {
    expect(initials('X')).toBe('X');
    expect(initials('  muchos   espacios  ')).toBe('ME');
  });
});
