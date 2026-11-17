// Spec 005, plan DT-2: the dates of the test cases (CV-18 to CV-21) are in Madrid time,
// whatever the time zone of the machine that runs the tests.
vi.stubEnv('TZ', 'Europe/Madrid');
