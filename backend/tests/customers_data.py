"""Customer data shared by the level D and level I tests of spec 003."""

# The six customers of spec table 6.6, in creation order (ids 1 to 6): company name, tax id
# and country.
TABLE_6_6_CUSTOMERS: list[tuple[str, str, str]] = [
    ("Zeta Redes S.A.", "A00000000", "ES"),
    ("acme telecom s.l.", "B12345674", "ES"),
    ("COMPAÑÍA Ñandú", "12345678Z", "ES"),
    ("Telefónica Demo", "PT123456789", "PT"),
    ("100% Fibra GmbH", "DE1234567", "DE"),
    ("Acme Cloud Ltd", "GB7654321", "GB"),
]
# Their ids ordered by company name ignoring case, as the list returns them (LI-1).
ALL_BY_NAME = [5, 6, 2, 3, 4, 1]
