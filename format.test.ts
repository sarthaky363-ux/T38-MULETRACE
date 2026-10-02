// frontend/src/lib/format.test.ts
import test from 'node:test';
import assert from 'node:assert';
import { fmtPct, fmtINR, fmtINRCompact, fmtMin } from './format.ts';

test('fmtPct never emits two percent signs (%%)', () => {
  const inputs = [
    50,
    0,
    100,
    99.3,
    99.99,
    0.5,
    '50%',
    '99.3%',
    '100%%',
    '75.4%%',
    fmtPct(42),
    fmtPct('42%'),
    fmtPct(fmtPct(88.8)),
  ];

  for (const input of inputs) {
    const result = fmtPct(input as any);
    assert.strictEqual(
      result.includes('%%'),
      false,
      `Failed for input: ${input}. Output "${result}" contains "%%"`
    );
    assert.ok(
      result.endsWith('%'),
      `Output "${result}" should end with a single "%"`
    );
  }
});

test('fmtPct handles ratio conversion correctly', () => {
  assert.strictEqual(fmtPct(0.993, 1, true), '99.3%');
  assert.strictEqual(fmtPct(1.0, 0, true), '100%');
  assert.strictEqual(fmtPct(0.441, 1, true), '44.1%');
});

test('fmtINR formats Indian Rupees properly', () => {
  assert.strictEqual(fmtINR(795000), '₹7,95,000');
  assert.strictEqual(fmtINR(350000), '₹3,50,000');
  assert.strictEqual(fmtINR(0), '₹0');
});

test('fmtINRCompact formats Cr and Lakh properly for KPI tiles', () => {
  assert.strictEqual(fmtINRCompact(2864000), '₹28.64 Lakh');
  assert.strictEqual(fmtINRCompact(15000000), '₹1.50 Cr');
  assert.strictEqual(fmtINRCompact(45000), '₹45,000');
});

test('fmtMin formats minutes properly', () => {
  assert.strictEqual(fmtMin(5.0), '5.0 min');
  assert.strictEqual(fmtMin(18.25), '18.3 min');
});
